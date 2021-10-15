import logging
import string
import re

from errors import PackmanError
import xmlparser
import version
import utils

logger = logging.getLogger("packman.schemaparser")


def _get_tools_version(product_version):
    ver = product_version
    # chop off any release candidate versioning
    pos = ver.find("-rc")
    if pos != -1:
        ver = ver[:pos]
    return ver


SUPPORTED_TOOLSVERSION = _get_tools_version(version.PRODUCT_VERSION)


class Remote(object):
    def __init__(self, name: str, type: str):
        self.name = name
        self.type = type
        self.package_location = None
        self.id = None
        self.key = None
        self.error_url = None

    def __str__(self):
        ret = "name=%s type=%s" % (self.name, self.type)
        if self.package_location:
            ret += " packageLocation=%s" % self.package_location
        if self.id:
            ret += " id=%s" % self.id
        if self.key:
            ret += " key=%s" % self.key
        if self.error_url:
            ret += " errorUrl=%s" % self.error_url
        return ret


class PlatformNode:
    def __init__(self, name):
        self.name = name
        self.children = []
        self.parent = None
        self.marked = False

    def __str__(self):
        ret = "[name=%s, inheriting=%s, parent=%s, children=%s]" % (
            self.name,
            self.marked,
            self.parent,
            self.children,
        )
        return ret

    def is_branch_marked(self):
        if self.marked:
            return True
        else:
            if self.parent:
                return self.parent.is_branch_marked()
            else:
                return False

    def delete_descendants(self, nodes):
        for child in self.children:
            del nodes[child.name]
            child.delete_descendants(nodes)
        self.children = []


class Project:
    def __init__(self):
        self.dependency_map = {}
        self.remotes = ()
        self.remotes_map = {}
        self.remotes_referenced = set()

    def __str__(self):
        msg = "Project\nDependency map:\n"
        for k, v in list(self.dependency_map.items()):
            dep_msg = str(v)
            msg += dep_msg
        return msg

    def add_dependency(self, dependency):
        """
        :param Dependency dependency: Dependency to add
        :rtype: None
        """
        dep_name = dependency.name
        if dep_name in self.dependency_map:
            raise PackmanError("Dependency '%s' can only be defined once in a project!" % dep_name)
        self.dependency_map[dep_name] = dependency
        for child in dependency.children:
            if hasattr(child, "remotes"):
                if child.remotes:
                    self.remotes_referenced.update(child.remotes)

    def add_remote(self, remote):
        """
        :type remote: Remote
        :rtype: None
        """
        self.remotes_map[remote.name] = remote

    def get_remote_configs(self):
        return self.remotes_map

    def get_remote_names(self):
        return self.remotes

    def get_dependencies(self, platform_name=None, include_tags=None, exclude_tags=None):
        """
        :param str platform_name: Name of platform
        :param list of str include_tags: List of tag strings
        :param list of str exclude_tags: List of tag strings
        :rtype: dict of Dependency objects
        """
        deps = {}
        for dep in list(self.dependency_map.values()):
            candidate = dep.as_resolved(platform_name, include_tags, exclude_tags)
            if candidate:
                deps[candidate.name] = candidate
        return deps


class ProjectElement(xmlparser.Element):
    TAG = "project"
    TOOLSVERSION = "toolsVersion"
    REMOTES = "remotes"

    def _init(self):
        self.attributes_required = (self.TOOLSVERSION,)
        self.attributes_optional = (self.REMOTES,)

    def start_handler(self, parse_helper, attributes):
        if hasattr(parse_helper, self.TAG):
            parse_helper.raise_error(
                "New '%s' element cannot be defined when one has already been defined!", self.TAG
            )
        root_element = Project()
        parse_helper.project = root_element
        parse_helper.root_element = root_element
        file_version = attributes[self.TOOLSVERSION]
        supported_version = SUPPORTED_TOOLSVERSION
        if self.is_file_version_newer(file_version, supported_version):
            logger.warning(
                "!!! This parser supports %s %s but file requests %s. Parsing may produce unexpected"
                " results. !!!" % (self.TOOLSVERSION, supported_version, file_version)
            )
        if self.REMOTES in attributes:
            qualified_remotes = []
            remote_names = attributes[self.REMOTES].split()
            for name in remote_names:
                qualified_remotes.append(parse_helper.namespace + ":" + name)
            root_element.remotes = qualified_remotes

    def end_handler(self, parse_helper):
        # verify that remotes referred to actually are defined in the file:
        root = parse_helper.root_element
        for name in root.remotes_referenced:
            if name not in root.remotes_map:
                head, tail = name.split(":")
                parse_helper.raise_error(
                    "Remote named '%s' is listed in attribute '%s' to but not defined!",
                    tail,
                    ProjectElement.REMOTES,
                )

    @classmethod
    def is_file_version_newer(cls, project_file_version, supported_version):
        version_numbers = project_file_version.split(".")
        major = version_numbers[0]
        minor = version_numbers[1]
        supported_version_numbers = supported_version.split(".")
        s_major = supported_version_numbers[0]
        s_minor = supported_version_numbers[1]
        project_is_newer = False
        if int(major) > int(s_major):
            project_is_newer = True
        if int(minor) > int(s_minor) and int(major) == int(s_major):
            project_is_newer = True
        return project_is_newer


class PlatformElement(xmlparser.Element):
    TAG = "platform"
    NAME = "name"
    INHERIT = "inherit"

    def _init(self):
        self.attributes_optional = (self.NAME, self.INHERIT)

    def start_handler(self, parse_helper, attributes):
        # remove this to support generic platform
        try:
            platform_name = attributes[self.NAME]
        except KeyError:
            parse_helper.raise_error("%s element must specify name attribute!", self.TAG)

        if parse_helper.project.has_platform(platform_name):
            parse_helper.raise_error("Platform %s already defined!", platform_name)
        platform = Platform(platform_name)
        if self.INHERIT in attributes:
            platform.inherit = attributes[self.INHERIT]
        parse_helper.current_platform = platform

    def end_handler(self, parse_helper):
        parse_helper.project.add_platform(parse_helper.current_platform)
        parse_helper.current_platform = None


class Package:
    def __init__(self, name, version):
        self.name = name
        self.version = version
        self.platforms = None
        self.remotes = None

    def __str__(self):
        msg = "Package '%s' @ '%s' (" % (self.name, self.version)
        if self.platforms:
            msg += "platforms='%s' " % " ".join(self.platforms)
        if self.remotes:
            msg += "remotes='%s' " % " ".join(self.remotes)
        msg += ")\n"
        return msg

    def as_resolved(self, platform):
        name_template = string.Template(self.name)
        version_template = string.Template(self.version)
        platform_str = platform if platform else ""
        try:
            name_resolved = name_template.substitute(platform=platform_str)
            version_resolved = version_template.substitute(platform=platform_str)
        except KeyError as exc:
            raise PackmanError(
                "Variable substitution for 'package' element failed (keyword '%s' not supported)"
                % str(exc)
            )
        p = Package(name_resolved, version_resolved)
        p.remotes = self.remotes
        return p


class Label:
    def __init__(self, name):
        self.name = name
        self.cache_expiration = 300
        self.platforms = None
        self.remotes = None
        self.version = None
        self.label = (
            name
        )  # storing this here because its the true label name and we might rename name later.

    def __str__(self):
        msg = "Label %s (" % self.name
        if self.platforms:
            msg += "platforms='%s' " % " ".join(self.platforms)
        if self.remotes:
            msg += "remotes='%s' " % " ".join(self.remotes)
        msg += ")\n"
        return msg

    def as_resolved(self, platform):
        name_template = string.Template(self.name)
        platform_str = platform if platform else ""
        try:
            name_resolved = name_template.substitute(platform=platform_str)
        except KeyError as exc:
            raise PackmanError(
                "Variable substitution for 'label' element failed (keyword '%s' not supported)"
                % str(exc)
            )
        l = Label(name_resolved)
        l.cache_expiration = self.cache_expiration
        l.remotes = self.remotes
        return l


class PackageElement(xmlparser.Element):
    TAG = "package"
    NAME = "name"
    VERSION = "version"
    PLATFORMS = "platforms"
    REMOTES = "remotes"

    def _init(self):
        self.attributes_required = (self.NAME, self.VERSION)
        self.attributes_optional = (self.REMOTES, self.PLATFORMS)

    def start_handler(self, parse_helper, attributes):
        package = Package(attributes[self.NAME], attributes[self.VERSION])
        parse_helper.current_dependency.add_child(package)
        try:
            package.platforms = attributes[self.PLATFORMS].split()
        except KeyError:
            pass
        try:
            remote_names = attributes[self.REMOTES].split()
        except KeyError:
            package.remotes = parse_helper.project.remotes
        else:
            qualified_remotes = []
            for name in remote_names:
                qualified_remotes.append(parse_helper.namespace + ":" + name)
            package.remotes = qualified_remotes


class LabelElement(xmlparser.Element):
    TAG = "label"
    NAME = "name"
    PLATFORMS = "platforms"
    REMOTES = "remotes"
    CACHEEXPIRATION = "cacheExpiration"

    def __init__(self):
        self.attributes_required = [
            self.NAME
        ]  # because there is a forloop on this we cant pass in a string.
        self.attributes_optional = (self.REMOTES, self.PLATFORMS, self.CACHEEXPIRATION)

    def start_handler(self, parse_helper, attributes):
        label = Label(attributes[self.NAME])
        parse_helper.current_dependency.add_child(label)
        try:
            label.platforms = attributes[self.PLATFORMS].split()
        except KeyError:
            pass
        try:
            remote_names = attributes[self.REMOTES].split()
        except KeyError:
            label.remotes = parse_helper.project.remotes
        else:
            qualified_remotes = []
            for name in remote_names:
                qualified_remotes.append(parse_helper.namespace + ":" + name)
            label.remotes = qualified_remotes
        if self.CACHEEXPIRATION in attributes:
            if attributes[self.CACHEEXPIRATION].isdigit():
                label.cache_expiration = int(attributes[self.CACHEEXPIRATION])


class Source:
    def __init__(self, path):
        self.path = path
        self.platforms = None

    def __str__(self):
        msg = "Source path '%s' (" % self.path
        if self.platforms:
            msg += "platforms='%s'" % " ".join(self.platforms)
        msg += ")\n"
        return msg

    def as_resolved(self, platform):
        path_template = string.Template(self.path)
        if platform:
            platform_str = platform
        else:
            platform_str = ""
        try:
            path_resolved = path_template.substitute(platform=platform_str)
        except KeyError as exc:
            raise PackmanError(
                "Variable substitution for 'source' element failed (keyword '%s' not supported)"
                % str(exc)
            )
        return Source(path_resolved)


class SourceElement(xmlparser.Element):
    TAG = "source"
    PATH = "path"
    PLATFORMS = "platforms"

    def _init(self):
        self.attributes_required = (self.PATH,)
        self.attributes_optional = (self.PLATFORMS,)

    def start_handler(self, parse_helper, attributes):
        path = attributes[self.PATH]
        # resolve to absolute path if relative:
        path = parse_helper.resolve_path(path)
        source = Source(path)
        parse_helper.current_dependency.add_child(source)
        try:
            source.platforms = attributes[self.PLATFORMS].split()
        except KeyError:
            pass


def create_re_pattern_from_platform_wildcard(wildcard):
    i, n = 0, len(wildcard)
    res = ""
    while i < n:
        c = wildcard[i]
        i += 1
        if c == "*":
            res += ".*"
        elif c == "?":
            res += "."
        else:
            res = res + re.escape(c)
    return "(?ms)" + res + r"\Z"


class Dependency:
    def __init__(self, name):
        self.name = name
        self.link_path = None
        self.copy_path = None
        self.tags = None
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def __str__(self):
        msg = "Dependency '%s' (" % self.name
        if self.link_path:
            msg += "linkPath='%s'" % self.link_path
        if self.copy_path:
            msg += "copyPath='%s'" % self.copy_path
        if self.tags:
            msg += "tags='%s'" % " ".join(self.tags)
        msg += ")\n"
        for child in self.children:
            msg += str(child)
        return msg

    def as_resolved(self, platform=None, include_tags=None, exclude_tags=None):
        # first filter on tags:
        is_in = self.is_filtered_in(include_tags, exclude_tags)
        if is_in:
            # now see if platform matches:
            candidate = self.get_best_match_for_platform(platform)

            if candidate:
                resolved = candidate.as_resolved(platform)
                dep = Dependency(self.name)
                dep.link_path = self.link_path
                dep.copy_path = self.copy_path
                dep.children = [resolved]
                return dep
        return None

    def is_filtered_in(self, include_tags, exclude_tags):
        """
        :param iterable include_tags: List of tags to include
        :param iterable exclude_tags: List of tags to exclude
        :return: True iff dependency contains only elements with tag from 'include_tags' and no
            tags from 'exclude_tags'
        :rtype: bool
        """
        # We have to check for None explicitly on include tags because empty list is a special inclusion case where
        # nothing gets through so we must run the processing in that case
        include_tags_arg = include_tags is not None
        add = True
        if include_tags_arg or exclude_tags:
            add = False if include_tags_arg else True
            if self.tags:
                if include_tags:
                    for tag in include_tags:
                        if tag in self.tags:
                            logging.info(
                                "Including dependency '%s' because of tag '%s'" % (self.name, tag)
                            )
                            add = True
                            break
                if exclude_tags:
                    for tag in exclude_tags:
                        if tag in self.tags:
                            logging.info(
                                "Excluding dependency '%s' because of tag '%s'" % (self.name, tag)
                            )
                            add = False
                            break
        return add

    def get_best_match_for_platform(self, platform):
        """
        Returns the child source or package object that best matches the platform, if none does then None is returned.
        :param str platform: Name of platform to match or None.
        :return None or child object:
        """
        candidate = None
        candidate_match_location = 0
        for child in self.children:
            if child.platforms is None:
                # no platform specified makes this the exact match if no platform was specified on command line:
                if platform is None:
                    candidate = child
                    break  # exit because this is an exact match
                # otherwise this becomes the best match if no more specific match has already been made:
                if candidate_match_location > 0:
                    continue  # we have already found a more specific match
                else:
                    candidate = child
            elif platform:
                if platform in child.platforms:
                    candidate = child
                    break  # exit because this is an exact match
                else:
                    # we must iterate through the platforms specified and see if there is a wildcard match
                    for child_platform in child.platforms:
                        pos = child_platform.find("*")
                        # the below requires explanation. pos will be -1 if * is not found and this will always
                        # be less than candidate_match_location so we manage to check two things at once; i.e.
                        # whether there is a wildcard *and* whether this would be a stronger match
                        if pos > candidate_match_location:
                            re_pattern = create_re_pattern_from_platform_wildcard(child_platform)
                            if re.match(re_pattern, platform):
                                logger.info(
                                    "Platform '%s' is now the strongest match for dependency '%s'",
                                    child_platform,
                                    self.name,
                                )
                                candidate = child
                                candidate_match_location = pos
                        else:
                            logger.info(
                                "Platform '%s' ignored for dependency '%s' because stronger match has already "
                                "been made",
                                child_platform,
                                self.name,
                            )
        return candidate


class DependencyElement(xmlparser.Element):
    TAG = "dependency"
    NAME = "name"
    LINKPATH = "linkPath"
    COPYPATH = "copyPath"
    TAGS = "tags"

    def _init(self):
        self.attributes_required = (self.NAME,)
        self.attributes_optional = (self.LINKPATH, self.TAGS, self.COPYPATH)

    def start_handler(self, parse_helper, attributes):
        name = attributes[self.NAME]
        if not utils.is_valid_shell_variable_name(name):
            parse_helper.raise_error(
                "Value for attribute '%s' on element '%s' must be a valid Unix shell variable "
                "name (alphanumeric and underscore)",
                self.NAME,
                self.TAG,
            )
        dep = Dependency(attributes[self.NAME])
        parse_helper.current_dependency = dep
        parse_helper.project.add_dependency(dep)
        # Check for link path and resolve if needed:
        try:
            path = attributes[self.LINKPATH]
        except KeyError:
            pass
        else:
            dep.link_path = parse_helper.resolve_path(path)

        # Check for copy path and resolve if needed:
        try:
            path = attributes[self.COPYPATH]
        except KeyError:
            pass
        else:
            dep.copy_path = parse_helper.resolve_path(path)

        try:
            dep.tags = attributes[self.TAGS].split()
        except KeyError:
            pass


class RemoteElement(xmlparser.Element):
    TAG = "remote"
    NAME = "name"
    TYPE = "type"
    LOCATION = "packageLocation"

    def _init(self):
        self.attributes_required = (self.NAME, self.TYPE)
        self.attributes_optional = (self.LOCATION,)

    def start_handler(self, parse_helper, attribute_dict):
        name_value = attribute_dict[self.NAME]
        namespaced_name = parse_helper.namespace + ":" + name_value
        attribute_dict[self.NAME] = namespaced_name
        type_value = attribute_dict[self.TYPE]
        remote = Remote(namespaced_name, type_value)
        parse_helper.current_remote = remote
        supported_types = ("gtl", "s3", "http", "https")
        if type_value not in supported_types:
            parse_helper.raise_error(
                "Attribute '%s' needs to contain one of the following: %s",
                self.TYPE,
                " ".join(supported_types),
            )
        if type_value != "gtl":
            try:
                package_location = attribute_dict[self.LOCATION]
            except KeyError:
                parse_helper.raise_error(
                    "Attribute '%s' is missing but required for remote type '%s'",
                    self.LOCATION,
                    type_value,
                )
            remote.package_location = package_location
        parse_helper.root_element.add_remote(remote)

    def end_handler(self, parse_helper):
        parse_helper.current_remote = None


class CredentialsElement(xmlparser.Element):
    TAG = "credentials"
    ATTRIBUTE_ID = "id"
    ATTRIBUTE_KEY = "key"
    ATTRIBUTE_URL = "errorUrl"

    def _init(self):
        self.attributes_required = (self.ATTRIBUTE_ID, self.ATTRIBUTE_KEY)
        self.attributes_optional = (self.ATTRIBUTE_URL,)

    def start_handler(self, parse_helper, attribute_dict):
        remote = parse_helper.current_remote
        remote.id = attribute_dict[self.ATTRIBUTE_ID]
        remote.key = attribute_dict[self.ATTRIBUTE_KEY]
        try:
            remote.error_url = attribute_dict[self.ATTRIBUTE_URL]
        except KeyError:
            pass


class Cache:
    def __init__(self):
        self.remove_previous_package_on_label_update = None

    def merge(self, cache_lower_priority):
        if (
            self.remove_previous_package_on_label_update is None
            and cache_lower_priority is not None
        ):
            self.remove_previous_package_on_label_update = (
                cache_lower_priority.remove_previous_package_on_label_update
            )


class CacheElement(xmlparser.Element):
    TAG = "cache"
    REMOVE_OLD_PACKAGE_ON_LABEL_UPDATE = "removePreviousPackageOnLabelUpdate"

    def _init(self):
        self.attributes_required = tuple()
        self.attributes_optional = (self.REMOVE_OLD_PACKAGE_ON_LABEL_UPDATE,)

    def start_handler(self, parse_helper, attribute_dict):
        if parse_helper.root_element.cache:
            parse_helper.raise_error(
                "New '%s' element cannot be defined when one has already been defined!", self.TAG
            )
        cache = Cache()
        parse_helper.root_element.cache = cache
        try:
            value = attribute_dict[self.REMOVE_OLD_PACKAGE_ON_LABEL_UPDATE]
            cache.remove_previous_package_on_label_update = True if value == "true" else False
        except KeyError:
            pass


class Config:
    def __init__(self):
        self.remotes = ()
        self.remotes_map = {}
        self.cache = None

    def add_remote(self, remote):
        """
        :type remote: Remote
        :rtype: None
        """
        self.remotes_map[remote.name] = remote

    def get_remote_configs(self):
        return self.remotes_map


class ConfigElement(xmlparser.Element):
    TAG = "config"
    REMOTES = "remotes"

    def _init(self):
        self.attributes_required = tuple()
        self.attributes_optional = (self.REMOTES,)

    def start_handler(self, parse_helper, attributes):
        if hasattr(parse_helper, self.TAG):
            parse_helper.raise_error(
                "New '%s' element cannot be defined when one has already been defined!", self.TAG
            )
        root_element = Config()
        parse_helper.root_element = root_element
        if self.REMOTES in attributes:
            qualified_remotes = []
            remote_names = attributes[self.REMOTES].split()
            for name in remote_names:
                qualified_remotes.append(parse_helper.namespace + ":" + name)
            root_element.remotes = qualified_remotes

    def end_handler(self, parse_helper):
        # verify that remotes referred to actually are defined in the file:
        root = parse_helper.root_element
        if root.remotes:
            for name in root.remotes:
                if name not in root.remotes_map:
                    head, tail = name.split(":")
                    parse_helper.raise_error(
                        "Remote named '%s' is listed in attribute '%s' to but not defined!",
                        tail,
                        ConfigElement.REMOTES,
                    )


class ProjectParser(xmlparser.BaseParser):
    def __init__(self):
        element_map = {
            ProjectElement.TAG: (ProjectElement(), None),
            RemoteElement.TAG: (RemoteElement(), ProjectElement.TAG),
            CredentialsElement.TAG: (CredentialsElement(), RemoteElement.TAG),
            DependencyElement.TAG: (DependencyElement(), ProjectElement.TAG),
            PackageElement.TAG: (PackageElement(), DependencyElement.TAG),
            LabelElement.TAG: (LabelElement(), DependencyElement.TAG),
            SourceElement.TAG: (SourceElement(), DependencyElement.TAG),
        }
        super(ProjectParser, self).__init__(element_map, "project")


class ConfigParser(xmlparser.BaseParser):
    def __init__(self, namespace):
        element_map = {
            ConfigElement.TAG: (ConfigElement(), None),
            RemoteElement.TAG: (RemoteElement(), ConfigElement.TAG),
            CredentialsElement.TAG: (CredentialsElement(), RemoteElement.TAG),
            CacheElement.TAG: (CacheElement(), ConfigElement.TAG),
        }
        super(ConfigParser, self).__init__(element_map, namespace, fail_on_unhandled_data=False)
