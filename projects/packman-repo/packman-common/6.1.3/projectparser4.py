import logging
import xml.parsers.expat
import os
import version
from errors import PackmanError


__author__ = "hfannar"
logger = logging.getLogger("packman.projectparser4")


def _get_tools_version(product_version):
    ver = product_version
    # chop off any release candidate versioning
    pos = ver.find("-rc")
    if pos != -1:
        ver = ver[:pos]
    return ver


SUPPORTED_TOOLSVERSION = (
    "4.3"
)  # we freeze this parser on last published packman version for 4 major
SUPPORTED_DEPENDENCY_ATTRIBUTES = (
    "name",
    "version",
    "path",
    "linkPath",
    "exportAs",
    "packageSource",
    "tags",
)
PROJECT_TAG = "project"
TOOLSVERSION_ATTRIB = "toolsVersion"
PLATFORM_TAG = "platform"
INHERIT_ATTRIB = "inherit"
DEPENDENCY_TAG = "dependency"
EXPORTAS_ATTRIB = "exportAs"
LINKPATH_ATTRIB = "linkPath"
TAGS_ATTRIB = "tags"
OVERRIDEPATH_ATTRIB = "path"


def is_project_file_newer(project_file_version, supported_version):
    version_numbers = project_file_version.split(".")
    major = version_numbers[0]
    minor = version_numbers[1]
    supported_version_numbers = SUPPORTED_TOOLSVERSION.split(".")
    s_major = supported_version_numbers[0]
    s_minor = supported_version_numbers[1]
    project_is_newer = False
    if int(major) > int(s_major):
        project_is_newer = True
    if int(minor) > int(s_minor) and int(major) == int(s_major):
        project_is_newer = True
    return project_is_newer


def compare_versions(project_file_version, supported_version):
    if is_project_file_newer(project_file_version, supported_version):
        logger.warning(
            "!!! This parser supports %s %s but project file requests %s. "
            "Parsing may produce unexpected results. !!!"
            % (TOOLSVERSION_ATTRIB, supported_version, project_file_version)
        )


class ParseHelper:
    def __init__(self, xml_parser, filename=None):
        self.xml_parser = xml_parser
        self.filename = filename
        cwd = os.getcwd()
        path = filename if filename else ""
        self.base_dir = os.path.dirname(os.path.abspath(os.path.join(cwd, path)))
        self.ignore_stack = (
            0
        )  # When non-zero we ignore elements until parsing brings this back to zero
        self.project = None
        self.current_platform = None

    def _skip_element(self, element_name):
        self._log_error("Ignoring element '%s' and everything it contains.", element_name)
        self.ignore_stack = 1

    def _verify_attributes(self, element_name, attributes, supported_attributes):
        for key in list(attributes.keys()):
            if key not in supported_attributes:
                self._log_error(
                    "Attribute '%s' on element '%s' is not supported.", key, element_name
                )
                supported_str = " ".join(supported_attributes)
                logger.error("Supported attributes are: %s", supported_str)

    def _log_error(self, msg, *args):
        line = "(line %d): " % self.xml_parser.CurrentLineNumber
        if self.filename:
            line = self.filename + line
        msg = line + msg
        logger.error(msg, *args)

    def _resolve_env_vars(self, attributes):
        for key, value in list(attributes.items()):
            if value.startswith("$"):
                os_env_var = value[1:]
                try:
                    env_var_value = os.environ[os_env_var]
                except KeyError:
                    self._log_error(
                        "Environment variable '%s' in project file not found in environment."
                        % os_env_var
                    )
                    return False
                else:
                    attributes[key] = env_var_value
        return True

    def start_element(self, name, attributes):
        """
        :type name: unicode
        :type attributes: dict
        :rtype: None
        """
        if self.ignore_stack:
            # We are in skip mode because of errors or future element this parser doesn't know what to do with
            self.ignore_stack += 1
            return
        elif name == PROJECT_TAG:
            if self.project:
                self._log_error(
                    "New project element cannot be defined when one has already been defined!"
                )
                self._skip_element(name)
                return
            self.project = Project()
            compare_versions(attributes[TOOLSVERSION_ATTRIB], SUPPORTED_TOOLSVERSION)

            if "packageSource" in attributes:
                self.project.package_source = attributes["packageSource"].lower()
        elif name == PLATFORM_TAG:
            if self.current_platform is not None:
                self._log_error(
                    "New %s cannot be defined inside another %s!" % (PLATFORM_TAG, PLATFORM_TAG)
                )
                self._skip_element(name)
                return
            if "name" not in attributes:
                self._log_error("%s element must specify name attribute!" % PLATFORM_TAG)
                self._skip_element(name)
                return
            platform_name = attributes["name"]
            if self.project.has_platform(platform_name):
                self._log_error("Platform %s already defined!" % platform_name)
                self._skip_element(name)
                return
            platform = Platform(platform_name)
            if INHERIT_ATTRIB in attributes:
                platform.inherit = attributes[INHERIT_ATTRIB]
            self.current_platform = platform
        elif name == "dependency":
            if self.current_platform:
                self._verify_attributes(name, attributes, SUPPORTED_DEPENDENCY_ATTRIBUTES)
                # Need to resolve environment variables if used:
                ok = self._resolve_env_vars(attributes)
                if ok:
                    # Check for override path:
                    if OVERRIDEPATH_ATTRIB in attributes:
                        # we support relative path specification:
                        path = attributes[OVERRIDEPATH_ATTRIB]
                        if not os.path.isabs(path):
                            abs_path = os.path.abspath(os.path.join(self.base_dir, path))
                            logger.info("Resolving relative path '%s' => '%s'", path, abs_path)
                            attributes[OVERRIDEPATH_ATTRIB] = abs_path
                        self.current_platform.overrides.append(attributes)
                    else:
                        self.current_platform.dependencies.append(attributes)
                    # Check for link path and resolve if needed:
                    if "linkPath" in attributes:
                        # we support relative path specification:
                        path = attributes["linkPath"]
                        abs_path = os.path.abspath(os.path.join(self.base_dir, path))
                        attributes["linkPath"] = abs_path
                else:
                    self._skip_element(name)
            else:
                self._log_error("Dependency defined outside platform!")
                self._skip_element(name)

        else:
            self._log_error("Unknown element %s", name)
            self._skip_element(name)

    def end_element(self, name):
        if self.ignore_stack:
            self.ignore_stack -= 1
            return
        if name == "platform":
            self.project.add_platform(self.current_platform)
            self.current_platform = None


class Platform:
    def __init__(self, name):
        self.name = name
        self.inherit = None
        self.dependencies = []
        self.overrides = []

    def __str__(self):
        ret = "%s=%s" % (PLATFORM_TAG, self.name)
        if self.inherit:
            ret += " %s=%s" % (INHERIT_ATTRIB, self.inherit)
        ret += "\ndependencies="
        ret += str(self.dependencies)
        ret += "\noverrides="
        ret += str(self.overrides)
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
        self.platforms = {}
        self.package_source = None

    def has_platform(self, name):
        """
        :type name: str
        :rtype: bool
        """
        if name.lower() in self.platforms:
            return True
        else:
            return False

    def add_platform(self, platform):
        """
        :type platform: Platform
        :rtype: None
        """
        self.platforms[platform.name.lower()] = platform

    def get_dependencies_and_overrides(self):
        """
        :rtype: list, list
        """
        deps = []
        overrides = []
        for platform in list(self.platforms.values()):
            self.get_dependencies_and_overrides_for_platform(platform.name, deps, overrides)
        return deps, overrides

    def get_dependencies_and_overrides_for_platform(self, name, dependencies, overrides):
        """
        :type name: str
        :type dependencies: list
        :type overrides: list
        """
        try:
            platform = self.platforms[name.lower()]
            logger.info("Getting dependencies for platform %s" % name)
            dependencies.extend(platform.dependencies)
            overrides.extend(platform.overrides)
            if platform.inherit:
                logger.info("Getting dependencies for inherited platform")
                self.get_dependencies_and_overrides_for_platform(
                    platform.inherit, dependencies, overrides
                )
        except KeyError:
            raise PackmanError("Platform %s not found in project!" % name)

    def _get_relations_on_branch(self, node, platform, nodes):
        if platform.inherit:
            parent = platform.inherit.lower()
            if parent in nodes:
                parent_node = nodes[parent]
            else:
                parent_node = PlatformNode(parent)
                nodes[parent] = parent_node

            node.parent = parent_node
            if node not in parent_node.children:
                parent_node.children.append(node)

            parent_platform = self.platforms[parent]
            self._get_relations_on_branch(parent_node, parent_platform, nodes)

    def get_platform_nodes(self):
        nodes = {}
        for name, platform in list(self.platforms.items()):
            if name in nodes:
                continue
            node = PlatformNode(name)
            nodes[name] = node
            self._get_relations_on_branch(node, platform, nodes)
        return nodes


class ProjectParser:
    def __init__(self):
        self.xml_parser = xml.parsers.expat.ParserCreate()

    def parse_file(self, filename):
        """
        :type filename: str
        :rtype: Project
        """
        # Create handlers for the parser
        p = self.xml_parser
        handler = ParseHelper(p, filename)
        p.StartElementHandler = handler.start_element
        p.EndElementHandler = handler.end_element
        with open(filename, "r") as fileobject:
            try:
                p.ParseFile(fileobject)
            except xml.parsers.expat.ExpatError as e:
                message = "%s: %s" % (filename, str(e))
                raise PackmanError(message)
        return handler.project

    def parse_data(self, data):
        """
        :type data: str
        :rtype: Project
        """
        # Create handlers for the parser
        p = self.xml_parser
        handler = ParseHelper(p)
        p.StartElementHandler = handler.start_element
        p.EndElementHandler = handler.end_element
        p.Parse(data, True)
        return handler.project
