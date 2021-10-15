# With Python 3.2 a lot of resource warnings have been introduced. Most of these are just noise
# and don't improve the code. We have addressed most but some are in libraries and they are not
# actual problems so we are disabling the warnings here.
import warnings

warnings.simplefilter("ignore")
import logging
import os
import argparse
import subprocess
import multiprocessing
import sys
import webbrowser
import posixpath
import re
import time
from typing import Dict, Iterable, List
import uuid
import shlex
from io import StringIO

# Alias the silly Windows cp65001 codepage to utf-8
import codecs

codecs.register(lambda name: codecs.lookup("utf-8") if name == "cp65001" else None)

import locale

CONSOLE_ENCODING = locale.getdefaultlocale()[1]  # cp1252 for windows, utf8 for linux and mac
if not CONSOLE_ENCODING:
    CONSOLE_ENCODING = "utf8"

# This is required for the closed embedded python int
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import utils
import schemaparser
import packager
import transport
import version
import errors
import link as linkmodule
import project
import cache
import checksum
import updater
import mirror


__author__ = "hfannar"
ENVIRONMENT_VARIABLE_FOR_EXTERNAL_DEPENDENCIES = "PM_PACKAGES_ROOT"
ENVIRONMENT_VARIABLE_FOR_S3_KEY_ID = "PM_S3_ID"
ENVIRONMENT_VARIABLE_FOR_S3_SECRET_KEY = "PM_S3_KEY"
ENVIRONMENT_VARIABLE_FOR_PACKAGE_SOURCE = "PM_PACKAGES_SOURCE"
ENVIRONMENT_VARIABLE_FOR_GTL_USER = "PM_GTL_ID"
ENVIRONMENT_VARIABLE_FOR_GTL_KEY = "PM_GTL_KEY"
ENVIRONMENT_VARIABLE_FOR_INSTALL_PATH = "PM_INSTALL_PATH"
ENVIRONMENT_VARIABLE_FOR_VERBOSITY = "PM_VERBOSITY"
PACKMAN_VERSION = version.PRODUCT_VERSION
REMOTES_MAP = {}
REMOTES_CASCADE_DEFAULT = ()
CACHE_CONFIG = schemaparser.Cache()

logging.basicConfig(level=logging.WARNING, format="packman(%(levelname)s): %(message)s")
logger = logging.getLogger("packman")


def get_cache_settings_from_config_files():
    return CACHE_CONFIG


def get_remote_names_from_config_files():
    """
    Returns the list of remotes names configured in user and packman config files. Returns None if nothing is
    configured.
    :return list:
    """
    return REMOTES_CASCADE_DEFAULT


def get_remote_configs_from_config_files():
    return REMOTES_MAP


def get_remote_names_and_configs(remotes_arg, project_path_arg):
    if project_path_arg:
        if not os.path.exists(project_path_arg):
            raise errors.PackmanError("Project file path '%s' does not exist!" % project_path_arg)
        project = schemaparser.ProjectParser().parse_file(project_path_arg)
    else:
        project = None
    return get_remote_names_and_configs_with_parsed_project(remotes_arg, project)


def get_remote_config_with_parsed_project(remote_name, project):
    remote_configs = get_remote_configs_from_config_files()
    remote_configs.update(project.get_remote_configs())
    name = remote_name
    if name in remote_configs:
        # fully qualified, namespace name is used - we can just use it:
        return remote_configs[name]
    else:
        matched_config = None
        matched_name = None
        for namespace_name, config in list(remote_configs.items()):
            namespace, tail = namespace_name.split(":")
            if tail == name:
                if matched_config:
                    msg = (
                        "Argument remote with value '%s' matches both '%s' and '%s'. Please use fully "
                        "qualified name to disambiguate." % (name, matched_name, namespace_name)
                    )
                    raise errors.PackmanError(msg)
                else:
                    matched_config = config
                    matched_name = namespace_name
        if matched_config:
            return matched_config
        else:
            msg = (
                "Argument remote with value '%s' does not match the name of any configured remote."
                % name
            )
            msg += " Use 'remotes' command to see list of configured remotes."
            raise errors.PackmanError(msg)


def get_remote_names_and_configs_with_parsed_project(remotes_arg, project):
    remote_names = []
    remote_names.extend(get_remote_names_from_config_files())
    remote_configs = {}
    remote_configs.update(get_remote_configs_from_config_files())

    if project:
        # we don't extend remote_names with project value because this will come from individual packages
        remote_configs.update(project.get_remote_configs())

    if remotes_arg:
        # Command line overrules the whole cascade. We must first make sure it addresses named remote(s)
        remotes_arg_with_namespace = []
        for name in remotes_arg:
            if name in remote_configs:
                # fully qualified, namespace name is used - we can just use it:
                remotes_arg_with_namespace.append(name)
            else:
                matched = 0
                for namespace_name in remote_configs:
                    namespace, tail = namespace_name.split(":")
                    if tail == name:
                        matched += 1
                        if matched > 1:
                            msg = (
                                "Argument remote with value '%s' matches both '%s' and '%s'. Please use fully "
                                "qualified name to disambiguate."
                                % (name, remotes_arg_with_namespace[-1], namespace_name)
                            )
                            raise errors.PackmanError(msg)
                        else:
                            remotes_arg_with_namespace.append(namespace_name)
                if not matched:
                    msg = (
                        "Argument remote with value '%s' does not match the name of any configured remote."
                        % name
                    )
                    msg += " Use 'remotes' command to see list of configured remotes."
                    raise errors.PackmanError(msg)

        remote_names = remotes_arg_with_namespace

    return remote_names, remote_configs


def raise_if_remote_names_empty(remote_names):
    if not remote_names:
        msg = "No remotes specified in config files (neither packman nor user level)."
        msg += " If project file was provided then no remotes were found at project level."
        msg += (
            " You must specify at least one remote in one of these files or use 'remote' argument."
        )
        msg += " Use 'remotes' command to get list of currently configured remotes."
        raise errors.PackmanError(msg)


def get_remote_config_from_name(remote_name, remote_configs):
    try:
        remote_config = remote_configs[remote_name]
    except KeyError:
        raise errors.PackmanError("No configuration found for remote named '%s'" % remote_name)
    if remote_config.type in ["s3", "gtl"]:
        if not remote_config.id or not remote_config.key:
            remote_config.id, remote_config.key = get_credentials(remote_config.type)
    return remote_config


def get_dependencies_remote_names_and_configs(
    remotes_arg, project_path_arg, platform, include_tags, exclude_tags
):
    project = parse_project_file(project_path_arg)
    remote_names, remote_configs = get_remote_names_and_configs_with_parsed_project(
        remotes_arg, project
    )
    deps = project.get_dependencies(platform, include_tags, exclude_tags)
    return deps, remote_names, remote_configs


def get_repo_dir():
    msg = (
        "Environment variable %r not defined! Please set it to the path where external dependencies should be "
        "stored." % ENVIRONMENT_VARIABLE_FOR_EXTERNAL_DEPENDENCIES
    )
    package_repo_dir = get_environment_variable(ENVIRONMENT_VARIABLE_FOR_EXTERNAL_DEPENDENCIES, msg)
    return package_repo_dir


def get_environment_variable(variable_name, error_msg):
    try:
        value = os.environ[variable_name]
    except KeyError:
        logger.error(error_msg)
        raise errors.PackmanError("Environment variable %r not defined." % variable_name)
    return value


def get_s3_credentials():
    msg = "Full access credentials are required to publish/push/list packages with S3."
    key_id = get_environment_variable(ENVIRONMENT_VARIABLE_FOR_S3_KEY_ID, msg)
    secret_key = get_environment_variable(ENVIRONMENT_VARIABLE_FOR_S3_SECRET_KEY, msg)
    return key_id, secret_key


def get_gtl_credentials():
    msg = "GTL credentials are required to process packages with GTL"
    user = get_environment_variable(ENVIRONMENT_VARIABLE_FOR_GTL_USER, msg)
    key = get_environment_variable(ENVIRONMENT_VARIABLE_FOR_GTL_KEY, msg)
    return user, key


def get_credentials(source):
    if source.startswith("gtl"):
        return get_gtl_credentials()
    elif source.startswith("s3"):
        return get_s3_credentials()
    else:
        raise errors.PackmanError("Package source %r not supported" % source)


def create_transport(remote):
    return transport.create_transport(
        remote.type, (remote.id, remote.key), remote.package_location, error_url=remote.error_url
    )


def get_labels_dir():
    labels_dir = os.path.join(get_repo_dir(), "labels")
    if not os.path.exists(labels_dir):
        os.makedirs(labels_dir)
    return labels_dir


def is_local_label_still_valid(filename, label_name, cache_expiration=300):
    if type(cache_expiration) == str:
        if cache_expiration.isdigit():
            cache_expiration = int(cache_expiration)
        else:
            return False
    diff = int(time.time() - os.path.getmtime(filename))
    if cache_expiration > diff:
        print(
            "Using a local label for '%s' created %s seconds ago. Max age is %s seconds."
            % (label_name, diff, cache_expiration)
        )
        return True
    else:
        print(
            "A local label was found for '%s' but is older than the set cache limit. Label: %s | Cache: %s"
            % (label_name, diff, cache_expiration)
        )
    return False


def get_local_label_path(name):
    if not name.endswith(".txt"):
        name += ".txt"
    local_labels_dir = get_labels_dir()
    local_label_path = os.path.join(local_labels_dir, name)
    return local_label_path


def process_label(name, cache_expiration=300, remote_names=None, remotes=None):
    possible_package = None
    local_label_found = False
    local_label_file = get_local_label_path(name)
    file_name = os.path.basename(local_label_file)
    if os.path.exists(local_label_file):
        local_label_found = True
        if is_local_label_still_valid(
            local_label_file, file_name, cache_expiration=cache_expiration
        ):
            with open(local_label_file, "r") as local_label:
                possible_package = local_label.read().strip()
    remove_previous_package = (
        get_cache_settings_from_config_files().remove_previous_package_on_label_update
    )
    if not possible_package:
        tp = {}
        if remotes:
            for remote_name in remote_names:
                if remote_name not in tp:
                    remote_config = get_remote_config_from_name(remote_name, remotes)
                    tp[remote_name] = create_transport(remote_config)
                    label_url = tp[remote_name].get_package_path(file_name, "")
                    if not label_url:
                        continue  # the label doesnt exist on the remote server.
                    temp_possible_package = None
                    temp_label = os.path.join(get_labels_dir(), "%s.txt" % str(uuid.uuid4()))
                    tp[remote_name].download_file(label_url, temp_label)
                    with open(temp_label, "r") as tlabel:
                        temp_possible_package = tlabel.read()
                    if temp_possible_package:
                        possible_package = temp_possible_package.strip()
                        try:
                            # lets remove the old label and rename the new label
                            old_label = os.path.join(os.path.split(temp_label)[0], file_name)
                            if os.path.exists(old_label):
                                if remove_previous_package:
                                    # also remove the package the old label pointed at
                                    with open(old_label, "r") as f:
                                        old_package = f.read().strip()
                                        old_basename, old_version = packager.get_basename_and_version_from_package_name(
                                            old_package
                                        )
                                        old_package_status, old_package_path = packager.get_package_install_info(
                                            get_repo_dir(), old_basename, old_version
                                        )
                                        if old_package_status == packager.STATUS_INSTALLED:
                                            packager.remove_package(old_package_path)
                                os.remove(old_label)
                            os.rename(temp_label, old_label)
                        except OSError:
                            # Something else might have already done the rename, so lets delete the temp label and move on.
                            os.remove(temp_label)
                        # we have our package so lets break out.
                        break
    # if we have internet problems or cant find a label on a remote server, lets use the local copy if there is one.
    if not possible_package:
        if local_label_found is True:
            print(
                "No label was found on a remote server or we have connection problems. Using an older local label."
            )
            with open(local_label_file, "r") as local_label:
                possible_package = local_label.read().strip()
        else:
            raise errors.PackmanError(
                "No label called '%s' found on a remote server or cached locally." % file_name
            )
    if "@" not in possible_package:
        return file_name, None

    return packager.get_basename_and_version_from_package_name(possible_package)


def postscript_args_parse(value):
    new_value = []
    if value:
        value_split = shlex.split(value, posix=False)
        for v in value_split:
            new_value.append(v.strip('"'))
        return new_value[0], new_value[1:]
    return None, None


def install_cmd(
    name,
    package_version=None,
    postscript=None,
    remotes=None,
    project_path=None,
    link_path=None,
    cache_expiration=300,
    var_path=None,
    **kwargs,
):
    with open(var_path, "w") if var_path else DummyContextMgr() as variable_file:
        install_with_variable_file(
            name,
            package_version,
            postscript,
            remotes,
            project_path,
            link_path,
            cache_expiration,
            variable_file,
        )


def install_with_variable_file(
    name,
    package_version,
    postscript,
    remotes,
    project_path,
    link_path,
    cache_expiration,
    variable_file,
):
    remote_names, remote_configs = get_remote_names_and_configs(remotes, project_path)
    raise_if_remote_names_empty(remote_names)
    if (
        package_version is None
    ):  # if the package version is None lets assume its a label and proccess it as such.
        name, package_version = process_label(
            name,
            remote_names=remote_names,
            remotes=remote_configs,
            cache_expiration=cache_expiration,
        )
        if not name or not package_version:
            return
    package = schemaparser.Package(name, package_version)
    dep_name = utils.create_valid_shell_variable_name(name)
    dep = schemaparser.Dependency(dep_name)
    dep.add_child(package)
    # sort out the postscript and args before we continue.
    args = []
    if postscript:
        postscript, args = postscript_args_parse(postscript)
    if link_path:
        # make absolute from current working directory if needed:
        path = os.path.abspath(link_path)
        dep.link_path = path

    dep_map = {"dep_name": dep}
    return pull_dependencies(
        dep_map,
        remote_configs,
        remote_names=remote_names,
        platform=None,
        postscript=postscript,
        variable_file=variable_file,
        args=args,
    )


def install(
    name: str,
    package_version: str = None,
    postscript: str = None,
    remotes: Iterable[str] = None,
    project_path: str = None,
    link_path: str = None,
    cache_expiration: int = 300,
) -> Dict[str, str]:
    """
     :param str name: name for label or package to install
     :param str version: version of package to install
     :param str postscript: path to script (.py or native shell script) to execute after successful processing of
       dependencies - execution has access to environment variables for packages installed.
     :param list remotes: name(s) of remote server(s) to use by default for packages (overrides environment setting)
     :param str project_path: path to project file for remotes lookup
     :param str link_path: link path (can be relative to current working directory) to link the dependency to
     :return: a map of 1 entry with dependency name as the key and the absolute link path as value, or packman cache
        path if no 'link_path' was provided.
     :rtype: dict
     """
    return install_with_variable_file(
        name, package_version, postscript, remotes, project_path, link_path, cache_expiration, None
    )


def pack(input_folder: str, output_folder: str = None, name: str = None, **kwargs) -> str:
    """
    :param str input_folder: path to the folder to package
    :param str output_folder: path to output directory where package will be placed (default is next to input folder)
    :param str name: name for resulting package (without extension). If not provide the name will be generated from the name
        of the input_folder and the parent folder of the input folder, like this:
        <input_folder parent name>@<input_folder name>
    :param kwargs: for additional arguments when argparse is used
    :return: path to package created
    :rtype: str
    """
    file_path = input_folder
    if not os.path.exists(file_path):
        raise errors.PackmanError("Specified file path '%s' not found!" % file_path)
    if output_folder:
        out_dir = output_folder
        if not os.path.exists(out_dir):
            raise errors.PackmanError("Specified output directory path '%s' not found!" % out_dir)
    else:
        out_dir = os.path.abspath(os.path.join(file_path, ".."))

    package_path = packager.create_package(file_path, out_dir, name, container="7z")
    print("Package created:", package_path)
    return package_path


def push_to_remote(
    path: str,
    remote_config: schemaparser.Remote,
    force: bool = False,
    make_public: bool = False,
    remote_path: str = None,
):
    """
    Pushes file at 'path' to remote storage with config 'remote_config'.
    :param str path:  Path to file to upload.
    :param Remote remote_config: Remote configuration to push to. Must include credentials that allow writing.
    :param bool force: Overwrite file on remote storage if it already exists - otherwise a PackmanErrorFileExists
        exception will be raised.
    :param bool make_public: This flag only works for remote storage locations that can be publicly accessed. In that
        case the file will be downloadable without credentials.
    :param str remote_path: Folder to store the file in on the remote server.
    :return: None
    """
    if not os.path.isfile(path):
        raise errors.PackmanError("File not found at path '%s'" % path)

    tp = create_transport(remote_config)
    if not hasattr(tp, "upload_file"):
        raise errors.PackmanError(
            "Cannot upload to remotes of type '%s' with packman" % remote_config.type
        )

    basename = os.path.basename(path)
    if remote_path:
        basename = posixpath.join(remote_path, basename)
    if not force:
        try:
            package_already_exists = tp.is_file_found(basename)
        except errors.PackmanError:
            raise errors.PackmanError("Failure to query remote server. Unable to upload file.")
        if package_already_exists:
            raise errors.PackmanErrorFileExists(
                "Package '%s' already exists on remote '%s'. Use force option to overwrite."
                % (basename, remote_config.name)
            )
    res = tp.upload_file(path, basename, make_public)
    print("Package %s uploaded to %s" % (basename, res))


def push(
    path: str,
    remotes: Iterable[str] = None,
    project_path: str = None,
    force: bool = False,
    make_public: bool = False,
    remote_path: str = None,
    **kwargs,
):
    """
    Pushes file at 'path' to remote storage.
    :param str path:  Path to file to upload.
    :param iterable or None remotes: List of remote names to push to. If none provided will use remotes setting
        from project file, packman config and user config.
    :param str project_path: Path to project file to use as default remotes setting.
    :param bool force: Overwrite file on remote storage if it already exists - otherwise a PackmanErrorFileExists
        exception will be raised.
    :param bool make_public: This flag only works for remote storage locations that can be publicly accessed. In that
        case the file will be downloadable without credentials.
    :param str remote_path: Folder to store the file in on the remote server.
    :param kwargs:
    :return: None
    """
    remote_names, remote_configs = get_remote_names_and_configs(remotes, project_path)
    raise_if_remote_names_empty(remote_names)
    for remote_name in remote_names:
        remote_config = get_remote_config_from_name(remote_name, remote_configs)
        push_to_remote(path, remote_config, force, make_public, remote_path)


def publish_to_remote(
    input_folder: str,
    remote_object: schemaparser.Remote,
    name: str = None,
    project_path: str = None,
    force: bool = False,
    make_public: bool = False,
):
    """
    :param str input_folder: path to the folder to pack and push (publish)
    :param Remote remote_object: The remote configured for upload (including credentials)
    :param str name: name for resulting package (without extension). If not provide the name will be generated from the
        name of the input_folder and the parent folder of the input folder, like this:
        <input_folder parent name>@<input_folder name>
    :param str project_path: Path to project file to use as default remotes setting.
    :param bool force: Overwrite file on remote storage if it already exists - otherwise a PackmanErrorFileExists
        exception will be raised.
    :param bool make_public: This flag only works for remote storage locations that can be publicly accessed. In that
        case the file will be downloadable without credentials.
    :param str remote_path: Folder to store the file in on the remote server.
    :param kwargs: for additional arguments when argparse is used
    :return: None
    """
    file_path = input_folder
    if not os.path.exists(file_path):
        raise errors.PackmanError(
            "Specified file path '%s' for publish command was not found!" % file_path
        )

    with utils.TemporaryDirectory() as temp_dir:
        package_path = packager.create_package(
            file_path, temp_dir, output_package_name=name, container="7z"
        )
        push_to_remote(package_path, remote_object, force=force, make_public=make_public)


def publish(
    input_folder: str,
    remotes: Iterable[str] = None,
    name: str = None,
    project_path: str = None,
    force: bool = False,
    make_public: bool = False,
    **kwargs,
):
    """
    :param str input_folder: path to the folder to pack and push (publish)
    :param iterable or None remotes: List of remote names to push to. If none provided will use remotes setting
        from project file, packman config and user config.
    :param str name: name for resulting package (without extension). If not provide the name will be generated from the
        name of the input_folder and the parent folder of the input folder, like this:
        <input_folder parent name>@<input_folder name>
    :param str project_path: Path to project file to use as default remotes setting.
    :param bool force: Overwrite file on remote storage if it already exists - otherwise a PackmanErrorFileExists
        exception will be raised.
    :param bool make_public: This flag only works for remote storage locations that can be publicly accessed. In that
        case the file will be downloadable without credentials.
    :param str remote_path: Folder to store the file in on the remote server.
    :param kwargs: for additional arguments when argparse is used
    :return: None
    """
    file_path = input_folder
    if not os.path.exists(file_path):
        raise errors.PackmanError(
            "Specified file path '%s' for publish command was not found!" % file_path
        )
    # it is annoying if we only find out about incorrect remote specification after creating the package so we
    # verify here that the config makes sense:
    remote_names, remote_configs = get_remote_names_and_configs(remotes, project_path)
    raise_if_remote_names_empty(remote_names)

    with utils.TemporaryDirectory() as temp_dir:
        package_path = packager.create_package(
            file_path, temp_dir, output_package_name=name, container="7z"
        )
        for remote_name in remote_names:
            remote_config = get_remote_config_from_name(remote_name, remote_configs)
            push_to_remote(package_path, remote_config, force=force, make_public=make_public)


def remotes(**kwargs):
    print("The following remotes have been configured:\n")
    header = "NAME" + " " * 16 + "TYPE" + " " * 3 + "PACKAGELOCATION"
    underline = "=" * len(header)
    print(header)
    print(underline)
    for name, remote in list(REMOTES_MAP.items()):
        line = name.ljust(19) + " "
        line += remote.type.ljust(7)
        if remote.package_location:
            line += remote.package_location
        print(line)
    print()
    if REMOTES_CASCADE_DEFAULT:
        print("The default search order for remotes is:")
        print(" ".join(REMOTES_CASCADE_DEFAULT))
    else:
        print("No default search order has been configured for remotes.")


def list_remote(
    package_name: str, remotes: Iterable[str] = None, project_path: str = None, **kwargs
) -> Dict[str, List[str]]:
    remote_names, remote_configs = get_remote_names_and_configs(remotes, project_path)
    raise_if_remote_names_empty(remote_names)
    result = {}
    for remote_name in remote_names:
        config = get_remote_config_from_name(remote_name, remote_configs)
        print("\nRemote server '%s':" % config.name)
        tp = create_transport(config)
        if hasattr(tp, "list_files_starting_with"):
            search_results = tp.list_files_starting_with(package_name)
            if search_results:
                result[config.name] = search_results
                for item in search_results:
                    print(item)
            else:
                print("No package found that starts with '%s'" % package_name)
        else:
            print("Cannot list packages on server of type '%s'" % config.type)
    return result


def filter_dependencies(dependencies, include_tags=None, exclude_tags=None):
    """
    :param iterable dependencies: List of dependencies, each dependency is a dict which can possibly contain a 'tags'
        attribute.
    :param iterable include_tags: List of tags to include
    :param iterable exclude_tags: List of tags to exclude
    :return: Filtered list of dependencies that contains only elements with tag from 'include_tags' and no
        tags from 'exclude_tags'
    :rtype: list
    """
    # We have to check for None explicitly on include tags because empty list is a special inclusion case where nothing
    # gets through so we must run the processing in that case
    include_tags_arg = include_tags is not None
    if include_tags_arg or exclude_tags:
        deps_filtered = []
        for dep in dependencies:
            add = False if include_tags_arg else True
            if "tags" in dep:
                tags_listed = dep["tags"].split()
                if include_tags:
                    for tag in include_tags:
                        if tag in tags_listed:
                            logging.info(
                                "Including dependency %r{name} %r{version} because of tag %r"
                                % (dep, dep, tag)
                            )
                            add = True
                            break
                if exclude_tags:
                    for tag in exclude_tags:
                        if tag in tags_listed:
                            logging.info(
                                "Excluding dependency %r{name} %r{version} because of tag %r"
                                % (dep, dep, tag)
                            )
                            add = False
                            break
            if add:
                deps_filtered.append(dep)

        return deps_filtered
    else:
        return dependencies


def parse_project_file(project_file_path):
    print("Processing project file '%s'" % project_file_path)

    proj_parser = schemaparser.ProjectParser()
    return proj_parser.parse_file(project_file_path)


def replace_environment(new_env_dict):
    if not (new_env_dict is os.environ):
        encoded_dict = {}
        for k, v in new_env_dict.items():
            encoded_dict[os.environ.encodekey(k)] = os.environ.encodevalue(v)

        def fake_putenv(key, value):
            pass

        def fake_unsetenv(key):
            pass

        # This code is interpreter-specific, and if interpreter will be changed to some other one,
        # re-implementing `_Environ` class from os.py of CPython will be required
        os.environ = os._Environ(
            encoded_dict,
            os.environ.encodekey,
            os.environ.decodekey,
            os.environ.encodevalue,
            os.environ.decodevalue,
            fake_putenv,
            fake_unsetenv,
        )


def run_py_script(path, env=None):
    script_dir = os.path.dirname(path)
    if script_dir:
        sys.path.append(script_dir)
    if env:
        replace_environment(env)
    my_globals = dict.copy(globals())
    my_globals["__file__"] = path
    with open(path, "rb") as path_input:
        exec(compile(path_input.read(), path, "exec"), my_globals)
    if script_dir:
        sys.path.remove(script_dir)


def hash(path: str) -> str:
    if not os.path.exists(path):
        raise errors.PackmanError("Specified file path '%s' not found!" % path)
    if os.path.isdir(path):
        return checksum.generate_sha1_for_folder(path)
    else:
        return checksum.generate_sha1_for_file(path)


def hash_cmd(path, **kwargs):
    ret = hash(path)
    print(ret)


def install_package_deps(install_path, platform, variable_file):
    deps_path = os.path.join(install_path, "deps.packman.xml")
    if os.path.exists(deps_path):
        logger.info("Found additional dependencies to process for package at '%s'", install_path)
        pull_with_variable_file(deps_path, platform, variable_file=variable_file)


def process_labels_in_dependencies(deps, remote_names, remote_configs):
    deps_removes = []
    for dep in list(deps.values()):
        child = dep.children[0]
        if isinstance(child, schemaparser.Label):
            label_remote_names = []
            if child.remotes:
                label_remote_names.extend(child.remotes)
            if remote_names:
                label_remote_names.extend(remote_names)
            name, version = process_label(
                child.name,
                cache_expiration=child.cache_expiration,
                remotes=remote_configs,
                remote_names=label_remote_names,
            )
            package = schemaparser.Package(name, version)
            package.remotes = child.remotes
            deps[dep.name].children[0] = package


def pull_cmd(
    project_path,
    platform=None,
    postscript=None,
    remotes=None,
    include_tags=None,
    exclude_tags=None,
    var_path=None,
    **kwargs,
):
    """
    :param str project_path: path to project file to process
    :param str platform: a platform name to process from the 'project_path' project file (default of None means
      that only dependencies that match any platform will be processed)
    :param str postscript: path to script (.py or native shell script) to execute after successful processing of
      dependencies - execution has access to environment variables for packages installed.
    :param list remotes: name(s) of remote server(s) to use by default for packages (overrides environment setting)
    :param list include_tags: sequence of strings that determine which dependencies will be processed. They need to
      have at least one of the tags from the 'include_tags' list.
    :param list exclude_tags: sequence of strings that are used to filter out dependencies from processing. A
      dependency that has one (or more) of the tags from 'exclude_tags' list will be excluded.
    :param str var_path: path to file where variables will be stored - so they can escape into the calling process
    :param kwargs: for additional arguments when argparse is used
    :return: None
    """
    with open(var_path, "w") if var_path else DummyContextMgr() as variable_file:
        pull_with_variable_file(
            project_path, platform, postscript, remotes, include_tags, exclude_tags, variable_file
        )


def pull(
    project_path: str,
    platform: str = None,
    postscript: str = None,
    remotes: Iterable[str] = None,
    include_tags: Iterable[str] = None,
    exclude_tags: Iterable[str] = None,
) -> Dict[str, str]:
    """
    :param str project_path: path to project file to process
    :param str platform: a platform name to process from the 'project_path' project file (default of None means
      that only dependencies that match any platform will be processed)
    :param str postscript: path to script (.py or native shell script) to execute after successful processing of
      dependencies - execution has access to environment variables for packages installed.
    :param list remotes: name(s) of remote server(s) to use by default for packages (overrides environment setting)
    :param list include_tags: sequence of strings that determine which dependencies will be processed. They need to
      have at least one of the tags from the 'include_tags' list.
    :param list exclude_tags: sequence of strings that are used to filter out dependencies from processing. A
      dependency that has one (or more) of the tags from 'exclude_tags' list will be excluded.
    :param kwargs: for additional arguments when argparse is used
    :return: a map of dependency names as keys and the absolute link path as value, or absolute packman cache
        path if no link path was provided for the dependency.
    :rtype: dict
    """
    return pull_with_variable_file(
        project_path, platform, postscript, remotes, include_tags, exclude_tags, None
    )


def pull_with_variable_file(
    project_file_path,
    platform=None,
    postscript=None,
    remotes_arg=None,
    include_tags=None,
    exclude_tags=None,
    variable_file=None,
):
    deps, remote_names, remote_configs = get_dependencies_remote_names_and_configs(
        remotes_arg, project_file_path, platform, include_tags, exclude_tags
    )
    # we need to check for any labels and if found process them.
    process_labels_in_dependencies(deps, remote_names, remote_configs)
    user_path = project_file_path + ".user"
    # sort out the postscript and args before we continue.
    args = []
    path_map = {}
    if postscript:
        postscript, args = postscript_args_parse(postscript)
    if os.path.exists(user_path):
        user_deps, user_remote_names, user_remote_configs = get_dependencies_remote_names_and_configs(
            remotes_arg, user_path, platform, include_tags, exclude_tags
        )
        # we need to check for any labels and if found process them.
        process_labels_in_dependencies(user_deps, user_remote_names, user_remote_configs)
        for dep_name in list(user_deps.keys()):
            if dep_name in deps:
                del deps[dep_name]
        pull_map = pull_dependencies(
            user_deps,
            user_remote_configs,
            remote_names=user_remote_names,
            platform=platform,
            postscript=None,
            variable_file=variable_file,
            args=args,
        )
        path_map.update(pull_map)
    pull_map = pull_dependencies(
        deps,
        remote_configs,
        remote_names=remote_names,
        platform=platform,
        postscript=postscript,
        variable_file=variable_file,
        args=args,
    )
    path_map.update(pull_map)
    return path_map


def store_variable(name, value, outfile):
    os.environ[name] = value
    if outfile:
        logger.info("Setting env var %s=%s", name, value)
        outfile.write("%s=%s\n" % (name, value))


# This one is used for conditional with context
class DummyContextMgr(object):
    def __init__(self):
        pass

    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def find_env_variable(item):
    # opted to keep the search simple because there should be nothing other than these few characters in
    # file/path/variables.
    find_env = re.compile("ENV{([a-zA-Z0-9_.-]+)}")
    return find_env.search(item)


def run(name, args=[], **kwargs):
    # we have to add the current working directory to the path else we cant import or find items from there.
    sys.path.append(os.getcwd())
    if not args:
        # we have to go through the name because it might have args inside.
        name, args = postscript_args_parse(name)
    command_line = [name]
    command_line.extend(args)
    # then we add the directory the script or application lives in to the path if its not in sys.path.
    name_abspath = os.path.dirname(os.path.abspath(name))
    if name_abspath not in sys.path:
        sys.path.append(name_abspath)
    if name.endswith(".py"):
        if not os.path.exists(name):
            raise errors.PackmanError("Specified file path '%s' not found!" % name)
        # if there are args lets rewrite sys.argv because we cant pass args to execfile, but we can process sys.argv.
        sys.argv = command_line
        p = multiprocessing.Process(target=run_py_script, args=(name, dict(os.environ)))
        try:
            p.start()
            p.join()
            return_code = p.exitcode
        except multiprocessing.ProcessError:
            raise errors.PackmanError("Python process execution of '%s' failed!" % name)
    else:
        return_code = subprocess.call(command_line, shell=True)

    if return_code:
        raise errors.PackmanErrorScriptFailure(name, return_code)


def pull_dependencies(
    dependency_map,
    remote_configs,
    remote_names=None,
    platform=None,
    postscript=None,
    variable_file=None,
    args=[],
):
    path_map = {}
    if len(dependency_map) == 0:
        logger.info("No dependencies to process.")

    # iterate over dependencies and get the ones that are missing (we could possibly run 8 concurrently):
    tp = {}  # we delay creation of transport until it's actually needed
    package_repo_dir = None  # we delay look up of this until it's actually needed
    all_paths = ""
    dependencies_processed = []
    with utils.TemporaryDirectory() as temp_dir:
        for dep in list(dependency_map.values()):
            dep_name = dep.name
            env_base_name = dep_name
            if dep_name not in dependencies_processed:
                dependencies_processed.append(dep_name)
                child = dep.children[0]
                if isinstance(child, schemaparser.Source):
                    logger.info(
                        "Dependency '%s' is fulfilled by source at '%s'", dep_name, child.path
                    )
                    install_path = child.path
                else:
                    package_name = child.name
                    package_version = child.version
                    if package_repo_dir is None:
                        package_repo_dir = get_repo_dir()
                    status, install_path = packager.get_package_install_info(
                        package_repo_dir, package_name, package_version
                    )
                    if status == packager.STATUS_CORRUPT:
                        packager.remove_package(install_path)
                    if status != packager.STATUS_INSTALLED:
                        print(
                            "Package '%s' at version '%s' is missing from local storage."
                            % (package_name, package_version)
                        )
                        package_found = False
                        if child.remotes:
                            package_remotes = child.remotes[:]
                            package_remotes.extend(remote_names)
                        else:
                            package_remotes = remote_names
                        if not package_remotes:
                            raise errors.PackmanError(
                                "No remote configured for package '%s' at version '%s'"
                                % (package_name, package_version)
                            )
                        for remote_name in package_remotes:
                            if remote_name not in tp:
                                remote_config = get_remote_config_from_name(
                                    remote_name, remote_configs
                                )
                                tp[remote_name] = create_transport(remote_config)
                            # see if package exists on remote
                            package_path = tp[remote_name].get_package_path(
                                package_name, package_version
                            )
                            if not package_path:
                                continue  # package doesn't exist on this server
                            package_found = True
                            head, ext = os.path.splitext(package_path)
                            if ext.startswith(".zip"):
                                ext = ".zip"
                            target_filename = os.path.join(
                                temp_dir, package_name + "@" + package_version + ext
                            )
                            tp[remote_name].download_file(package_path, target_filename)
                            packager.install_package(target_filename, install_path)
                            break
                        if not package_found:
                            raise errors.PackmanError(
                                "Package not found on specified remote servers!"
                            )
                    store_variable(
                        "PM_" + env_base_name + "_VERSION", package_version, variable_file
                    )

                install_path_unix_style = install_path.replace(os.path.sep, "/")
                all_paths += install_path_unix_style + ";"
                store_variable(
                    "PM_" + env_base_name + "_PATH", install_path_unix_style, variable_file
                )
                if dep.link_path:
                    path_map[dep.name] = dep.link_path
                    link_path = dep.link_path
                    link(link_path, install_path)
                elif dep.copy_path:
                    path_map[dep.name] = dep.copy_path
                    packager.copy_package_if_version_differs(install_path, dep.copy_path)
                else:
                    path_map[dep.name] = install_path_unix_style
                # install dependencies of the package if needed
                install_package_deps(install_path, platform, variable_file)

    store_variable("PM_PATHS", all_paths, variable_file)

    if postscript:
        if not os.path.exists(postscript):
            postscript_env = find_env_variable(postscript)
            if postscript_env:
                postscript = postscript.replace(
                    "ENV{%s}" % postscript_env.group(1), os.getenv(postscript_env.group(1))
                )
        if not os.path.exists(postscript):
            raise errors.PackmanError("Postscript file '%s' not found" % postscript)

        run(postscript, args=args)

    return path_map


def verify(project_path, platform=None, remotes=None, **kwargs):
    logger.info("Verifying packages for project file " + project_path)

    deps_map, remote_names, remotes_map = get_dependencies_remote_names_and_configs(
        remotes, project_path, platform, None, None
    )
    tp = {}
    remote_packages_present_and_total = {}
    for key in list(remotes_map.keys()):
        remote_packages_present_and_total[key] = [0, 0]

    package_repo_dir = get_repo_dir()
    # iterate over dependencies and verify they exist locally and remotely
    missing_locally = 0
    package_count = 0
    for dep in list(deps_map.values()):
        child = dep.children[0]
        # source dependencies are not counted
        if isinstance(child, schemaparser.Source):
            continue
        # labels need to be handled differently
        if isinstance(child, schemaparser.Label):
            local_path = get_local_label_path(child.name)
            if not os.path.exists(local_path):
                logger.error("Label '%s' is missing from local storage.", child.name)
                missing_locally += 1
            else:
                with open(local_path, "r") as local_label:
                    possible_package = local_label.read().strip()
                head, file_extension = os.path.splitext(possible_package)
                if file_extension.lower() in [".7z", ".zip", ".tar"]:
                    possible_package = head
                package_name, package_version = possible_package.split("@", 1)
        else:
            package_name = child.name
            package_version = child.version

        package_count += 1
        status, install_path = packager.get_package_install_info(
            package_repo_dir, package_name, package_version
        )
        if status != packager.STATUS_INSTALLED:
            logger.error(
                "Package '%s' at version '%s' is missing from local storage (or corrupt).",
                package_name,
                package_version,
            )
            missing_locally += 1

        if child.remotes:
            package_remotes = remote_names[:]
            package_remotes.extend(child.remotes)
        else:
            package_remotes = remote_names
        if not package_remotes:
            raise errors.PackmanError(
                "No remotes configured for package '%s' at version '%s'"
                % (package_name, package_version)
            )
        for remote_name in package_remotes:
            if remote_name not in tp:
                try:
                    remote_config = remotes_map[remote_name]
                except KeyError:
                    raise errors.PackmanError(
                        "Referenced remote '%s' is not configured!" % remote_name
                    )
                tp[remote_name] = create_transport(remote_config)
            # see if package exists on remote
            package_path = tp[remote_name].get_package_path(package_name, package_version)
            present_and_total = remote_packages_present_and_total[remote_name]
            present_and_total[1] += 1
            if package_path:
                present_and_total[0] += 1
            else:
                msg = "Package '%s' at version '%s' is missing from remote storage '%s'" % (
                    child.name,
                    child.version,
                    remote_name,
                )
                logger.error(msg)

    print("%d/%d packages present locally" % (package_count - missing_locally, package_count))
    missing_remotely = 0
    for k, v in list(remote_packages_present_and_total.items()):
        present = v[0]
        total = v[1]
        if total:
            print("%d/%d packages present remotely on '%s'" % (present, total, k))
            missing_remotely += total - present
    if missing_locally or missing_remotely:
        raise errors.PackmanError(
            "One or more packages were found to be missing from local or remote storage."
        )


def project_create(project_file_path, **kwargs):
    project.create_project(project_file_path)


def project_dependency_add(
    project_file_path, dependency_name, link_path=None, tags=None, force=False, **kwargs
):
    project.add_dependency(
        project_file_path, dependency_name, link_path, tags, force_overwrite=force
    )


def project_dependency_remove(project_file_path, dependency_name, **kwargs):
    project.remove_dependency(project_file_path, dependency_name)


_help_topics = []
_help_usage = None


def populate_help_topics(help_parser):
    # populate help topics:
    _my_dir = os.path.dirname(os.path.realpath(__file__))
    folder = os.path.join(_my_dir, "help")

    contents = sorted(os.listdir(folder))
    for file_name in contents:
        if file_name.endswith(".html"):
            _help_topics.append(os.path.splitext(file_name)[0])

    string_buffer = StringIO()
    help_parser.print_usage(string_buffer)
    global _help_usage
    _help_usage = string_buffer.getvalue()
    string_buffer.close()


def cache_cmd(remove_corrupt=False, **kwargs):
    cache.report(remove_corrupt_packages=remove_corrupt)


def help(topic=None, **kwargs):
    if topic and topic in _help_topics:
        my_dir = os.path.dirname(os.path.realpath(__file__))
        filepath = os.path.join(my_dir, "help", topic + ".html")
        filepath.replace(os.path.sep, "/")
        webbrowser.open_new_tab("file:///" + filepath)
    else:
        print(_help_usage)
        print("Available TOPICs are:\n")
        for item in _help_topics:
            print(item)
        print("")


def link(link_path: str, target_path: str):
    is_link_creation_needed = True
    # We are forced to chop of any trailing slashes because a bug introduced in Python 3 around abspath made
    # the previous approach fail. It was fixed in Python 3.6.8 but we would rather not rely on that.
    native_link_path = link_path.replace("/", os.path.sep)  # ensure native format
    native_link_path = native_link_path.rstrip(os.path.sep)  # chop of any trailing slashes

    head, tail = os.path.split(native_link_path)
    if head and not os.path.exists(head):
        logger.info("Creating parent path '%s' for folder linking ...", head)
        os.makedirs(head)
    if os.path.exists(link_path) or os.path.islink(link_path):
        try:
            target = linkmodule.get_link_target(link_path)
        except RuntimeError as exc:
            raise errors.PackmanError(
                "Path '%s' already exists as a normal folder. Cannot create "
                "a link target at this location!" % link_path
            )
        if os.path.normcase(target) == os.path.normcase(target_path):
            is_link_creation_needed = False
            logger.info("Link path already set up '%s' => '%s'" % (link_path, target_path))
        else:
            linkmodule.destroy_link(link_path)
    if is_link_creation_needed:
        logger.info("Linking path '%s' => '%s'" % (link_path, target_path))
        linkmodule.create_link(link_path, target_path)


def link_cmd(link_path, target_path, **kwargs):
    link(link_path, target_path)


def unlink(path: str):
    linkmodule.destroy_link(path)


def unlink_cmd(path, **kwargs):
    unlink(path)


def update_cmd(version=None, force=False, auto_yes=False, **kwargs):
    install_path = os.environ[ENVIRONMENT_VARIABLE_FOR_INSTALL_PATH]
    install_path = os.path.normpath(install_path)
    if not version:
        version = updater.fetch_last_known_good_version()
        if not auto_yes:
            # does it make sense to loop here until we get an answer we support? the original way but something starting with 'n' would stop the update.
            res = ""
            while res.lower() not in ["n", "no", "y", "yes"]:
                res = input(
                    "Do you want to update packman at '%s' to version %s [Y/n]: "
                    % (install_path, version)
                )
                if res.lower() in ["n", "no"]:
                    return
    updater.update(version, install_path, force)


def mirror_cmd(project_path, target_remote, platforms=None, auto_yes=False, **kwargs):
    mirror.mirror(project_path, target_remote, platforms, auto_yes)


def read_configuration():
    file_name = "config.packman.xml"
    file_path = os.path.expanduser(os.path.join("~", file_name))
    configs = []
    if os.path.exists(file_path):
        parser = schemaparser.ConfigParser("user")
        configs.append(parser.parse_file(file_path))

    try:
        install_path = os.environ[ENVIRONMENT_VARIABLE_FOR_INSTALL_PATH]
    except KeyError:
        pass
    else:
        file_path = os.path.join(install_path, file_name)
        if os.path.exists(file_path):
            parser = schemaparser.ConfigParser("packman")
            configs.append(parser.parse_file(file_path))

    remote_configs = {}
    remote_order = []
    cache_config = schemaparser.Cache()
    for config in configs:
        cache_config.merge(config.cache)
        remote_order.extend(config.remotes)
        remote_map = config.get_remote_configs()
        remote_configs.update(remote_map)
    global CACHE_CONFIG
    CACHE_CONFIG = cache_config
    global REMOTES_MAP
    REMOTES_MAP = remote_configs
    global REMOTES_CASCADE_DEFAULT
    REMOTES_CASCADE_DEFAULT = remote_order


def main(argv=None):
    read_configuration()
    epilog = (
        "Get help on each command by executing the command with the help option. Like \n"
        "this for the publish command:\n"
        "  packman publish -h"
    )
    desc = (
        "packman %s Copyright (c) 2015-2019 NVIDIA is a utility for managing external\n"
        "dependencies in accordance with RfC 100." % PACKMAN_VERSION
    )

    # create global options parser
    global_option_parser = argparse.ArgumentParser(add_help=False)
    group = global_option_parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")
    group.add_argument(
        "-q", "--quiet", action="store_true", help="no output except for error messages"
    )
    group.add_argument("-s", "--silent", action="store_true", help="silence all output")
    # the following option is only used by wrapper shell scripts to marshall environment variables from packman so we
    # suppress help for it:
    global_option_parser.add_argument("--var-path", dest="var_path", help=argparse.SUPPRESS)

    # create remotes option parser
    remote_option_parser = argparse.ArgumentParser(add_help=False)

    remote_option_help = (
        "name of remote server for packages - repeat option to specify multiple remotes "
    )
    remotes_cascade = get_remote_names_from_config_files()
    if remotes_cascade:
        remote_option_help += (
            " (this option overrides default environment configuration of '%s' and project file "
            "setting, if provided)" % " ".join(remotes_cascade)
        )
    remote_option_parser.add_argument(
        "-r", "--remote", dest="remotes", metavar="REMOTE", action="append", help=remote_option_help
    )

    # create project-path option parser
    project_file_option_parser = argparse.ArgumentParser(add_help=False)
    project_file_option_parser.add_argument(
        "-pf",
        "--project-file",
        dest="project_path",
        metavar="PROJECT_FILE",
        help="Path to project file for list of remotes and remote configurations",
    )

    # create postscript option parser
    postscript_option_parser = argparse.ArgumentParser(add_help=False)
    postscript_option_help = (
        "script (.py or native shell script) to execute after successful processing of "
        "dependencies - execution has access to environment variables for packages "
        "installed (name, version, and path)"
    )
    postscript_option_parser.add_argument("-ps", "--postscript", help=postscript_option_help)

    # create force upload option parser
    force_option_parser = argparse.ArgumentParser(add_help=False)
    force_option_help = "force overwrite of package even if same named package already exists"
    force_option_parser.add_argument("-f", "--force", action="store_true", help=force_option_help)

    # create make-public option parser
    make_public_option_parser = argparse.ArgumentParser(add_help=False)
    make_public_option_help = (
        "make the file accessible publicly on the remote storage - if the remote storage "
        "doesn't support this feature an error will be raised."
    )
    make_public_option_parser.add_argument(
        "-mp", "--make-public", action="store_true", help=make_public_option_help
    )

    # create yes option parser
    yes_option_parser = argparse.ArgumentParser(add_help=False)
    yes_option_help = (
        "automatically answer yes to all interactive questions, making the command non-interactive"
    )
    yes_option_parser.add_argument(
        "-y", "--yes", dest="auto_yes", action="store_true", help=yes_option_help
    )

    # create top-level parser
    parser = argparse.ArgumentParser(
        prog="packman",
        description=desc,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument("--version", action="version", version="%(prog)s " + PACKMAN_VERSION)
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="show this help message and exit - use help *command* for " "detailed help",
    )

    subparsers = parser.add_subparsers(help="COMMAND FOR PACKMAN TO EXECUTE")

    # create parser for 'cache' command
    parser_cache = subparsers.add_parser(
        "cache", parents=[global_option_parser], help="analyze and manage packages cache"
    )
    parser_cache.add_argument(
        "-rc", "--remove-corrupt", action="store_true", help="remove corrupt packages"
    )
    parser_cache.set_defaults(func=cache_cmd)

    # create parser for 'help' command
    parser_help = subparsers.add_parser(
        "help", parents=[global_option_parser], help="display detailed help in web " "browser"
    )
    parser_help.add_argument(
        "topic",
        metavar="TOPIC",
        nargs="?",
        help="command or subject to display help on in default web browser - leave empty to get "
        "full list of all topics available",
    )
    parser_help.set_defaults(func=help)
    populate_help_topics(parser_help)

    # create parser for 'install' command
    parser_install = subparsers.add_parser(
        "install",
        parents=[
            global_option_parser,
            remote_option_parser,
            project_file_option_parser,
            postscript_option_parser,
        ],
        help="install a package if missing from local storage",
    )
    parser_install.add_argument(
        "name",
        metavar="NAME",
        help="name of package or label (case sensitive) - excluding path, " "version and extension",
    )
    parser_install.add_argument(
        "package_version",
        metavar="VERSION",
        help="version of package (case sensitive) if package name was provided",
        nargs="?",
        default=None,
    )
    parser_install.add_argument(
        "-l",
        "--link-path",
        dest="link_path",
        metavar="LINK_PATH",
        help="dependency will be linked from LINK_PATH in the file system (can be specified "
        "relative to current working directory)",
    )
    parser_install.add_argument(
        "--cacheExpiration",
        dest="cache_expiration",
        metavar="CACHEEXPIRATION",
        default=300,
        help="set the age limit (in seconds) for local labels before they are ignored ",
    )
    parser_install.set_defaults(func=install_cmd)

    # create parser for 'list' command
    parser_list = subparsers.add_parser(
        "list",
        parents=[global_option_parser, remote_option_parser, project_file_option_parser],
        help="if a name is specified show list of packages that start with provided name else show all packages on the remote server",
    )
    parser_list.add_argument(
        "package_name",
        metavar="packageName",
        nargs="?",
        default="",
        help="package name to search for (comparison is case insensitive)",
    )
    parser_list.set_defaults(func=list_remote)

    # create name option parser
    name_option_parser = argparse.ArgumentParser(add_help=False)
    name_option_parser.add_argument(
        "-n",
        "--name",
        help="package will be named NAME (do not provide file extension) - default is to "
        "use name of parent folder of INPUT_FOLDER combined with the name of the "
        "INPUT_FOLDER, separated by '@' symbol. Use this format of "
        "base_name@version_name if the package is to be used with packman",
    )
    # create parser for 'pack' command
    parser_pack = subparsers.add_parser(
        "pack",
        parents=[global_option_parser, name_option_parser],
        help="pack a folder into a package",
    )
    parser_pack.add_argument(
        "input_folder", metavar="INPUT_FOLDER", help="path to folder that will be packaged"
    )
    parser_pack.add_argument(
        "-o",
        "--output-folder",
        help="path to output folder for package - default is parent folder of INPUT_FOLDER",
    )
    parser_pack.set_defaults(func=pack)

    # create parser for 'publish' command
    parser_publish = subparsers.add_parser(
        "publish",
        parents=[
            global_option_parser,
            name_option_parser,
            remote_option_parser,
            project_file_option_parser,
            force_option_parser,
            make_public_option_parser,
        ],
        help="a convenience command that performs pack and then push",
    )
    parser_publish.add_argument(
        "input_folder",
        metavar="INPUT_FOLDER",
        help="path to folder that will packaged and then pushed",
    )
    parser_publish.set_defaults(func=publish)

    # create parser for 'push' command
    parser_push = subparsers.add_parser(
        "push",
        parents=[
            global_option_parser,
            remote_option_parser,
            project_file_option_parser,
            force_option_parser,
            make_public_option_parser,
        ],
        help="push package to remote storage",
    )
    parser_push.add_argument(
        "path", metavar="PATH", help="path to zipped package or label to push to remote " "storage"
    )
    parser_push.add_argument(
        "-rp",
        "--remote-path",
        help="path to folder where package will be stored on remote " "(default is root)",
    )
    parser_push.set_defaults(func=push)

    # create parser for 'pull' command
    parser_pull = subparsers.add_parser(
        "pull",
        parents=[global_option_parser, remote_option_parser, postscript_option_parser],
        help="process dependencies and pull them if needed",
    )
    parser_pull.add_argument(
        "project_path",
        metavar="PROJECT_FILE",
        help="path to a "
        "project file (xml) that describe dependencies to fetch if missing - if a "
        "PROJECT_PATH.user file is found it will be processed as well (use this to override "
        "dependencies locally)",
    )
    parser_pull.add_argument(
        "-p", "--platform", help="platform to pull dependencies for - default is no platform"
    )
    parser_pull.add_argument(
        "-e",
        "--exclude-tag",
        dest="exclude_tags",
        metavar="EXCLUDE_TAG",
        action="append",
        help="dependencies with EXCLUDE_TAG in 'tags' attribute will be excluded from processing "
        "- repeat option for multiple tags to exclude",
    )
    parser_pull.add_argument(
        "-i",
        "--include-tag",
        dest="include_tags",
        metavar="INCLUDE_TAG",
        action="append",
        help="dependencies with INCLUDE_TAG in 'tags' attribute will be included in processing "
        "- repeat option for multiple tags to include",
    )
    parser_pull.set_defaults(func=pull_cmd)

    # create parser for 'verify' command
    parser_verify = subparsers.add_parser(
        "verify",
        parents=[global_option_parser, remote_option_parser],
        help="verify that dependencies are available locally and remotely",
    )
    parser_verify.add_argument(
        "project_path",
        metavar="PROJECT_FILE",
        help="path to a project file (xml) that describe dependencies to verify",
    )
    parser_verify.add_argument(
        "-p", "--platform", help="platform to verify dependencies for - default is all"
    )
    parser_verify.set_defaults(func=verify)

    # create parser for 'run" command
    parser_run = subparsers.add_parser(
        "run",
        parents=[global_option_parser],
        help="run a script using packman to get access to the api and such.",
    )
    parser_run.add_argument("name", metavar="NAME", help="script or application to execute.")
    parser_run.add_argument(
        "args",
        metavar="ARGS",
        nargs="*",
        help="arguments to pass to script - deprecated, will be removed soon.",
    )
    parser_run.set_defaults(func=run)

    # create parser for 'remotes' command
    parser_remotes = subparsers.add_parser(
        "remotes",
        parents=[global_option_parser],
        help="List remote servers that have been configured in the environment",
    )
    parser_remotes.set_defaults(func=remotes)

    # create parser for 'hash' command
    parser_hash = subparsers.add_parser(
        "hash",
        parents=[global_option_parser],
        help="returns the SHA-1 hash of given folder or file",
    )
    parser_hash.add_argument(
        "path", metavar="PATH", help="path to filename or folder to generate SHA-1 for"
    )
    parser_hash.set_defaults(func=hash_cmd)

    # create parser for 'link' command
    parser_link = subparsers.add_parser(
        "link", parents=[global_option_parser], help="creates a folder that links to another folder"
    )
    parser_link.add_argument("link_path", metavar="LINK_PATH", help="path to link folder to create")
    parser_link.add_argument("target_path", metavar="TARGET_PATH", help="path to target folder")
    parser_link.set_defaults(func=link_cmd)

    # create parser for 'unlink' command
    parser_unlink = subparsers.add_parser(
        "unlink", parents=[global_option_parser], help="removes a linked folder"
    )
    parser_unlink.add_argument("path", metavar="PATH", help="path to linked folder")
    parser_unlink.set_defaults(func=unlink_cmd)

    # create parser for 'update' command
    parser_update = subparsers.add_parser(
        "update",
        parents=[global_option_parser, yes_option_parser],
        help="updates packman to a new version",
    )
    parser_update.add_argument(
        "-f", "--force", action="store_true", help="overwrite read-only files during update"
    )
    parser_update.add_argument(
        "version",
        metavar="VERSION",
        nargs="?",
        help="packman version number - leave out to upgrade to latest for current major version.",
    )
    parser_update.set_defaults(func=update_cmd)

    # create parser for 'mirror' command
    parser_mirror = subparsers.add_parser(
        "mirror",
        parents=[global_option_parser, yes_option_parser],
        help="mirrors packages to a remote",
    )
    parser_mirror.add_argument(
        "project_path",
        metavar="PROJECT_FILE",
        help="path to a project file (xml) with dependencies to mirror",
    )
    parser_mirror.add_argument(
        "target_remote",
        metavar="REMOTE_NAME",
        help="name of target remote for mirroring; must have write access to it",
    )
    parser_mirror.add_argument(
        "-p",
        "--platform",
        dest="platforms",
        metavar="PLATFORM",
        action="append",
        help="process the project file for PLATFORM "
        "- repeat option to process multiple platforms at once",
    )
    parser_mirror.set_defaults(func=mirror_cmd)

    # create parser for 'project' command
    parser_project = subparsers.add_parser("project", help="create and update project files")
    project_subparsers = parser_project.add_subparsers(help="COMMAND FOR PROJECT FILE MODIFICATION")

    project_file_parser = argparse.ArgumentParser(add_help=False)
    project_file_parser.add_argument(
        "project_file_path", metavar="PROJECT_FILE", help="path to project file (xml) " "to create"
    )
    dependency_name_parser = argparse.ArgumentParser(add_help=False)
    dependency_name_parser.add_argument(
        "dependency_name", metavar="DEPENDENCY_NAME", help="name of dependency"
    )

    # create parsers for subcommands of 'project'
    parser_create = project_subparsers.add_parser(
        "create",
        parents=[global_option_parser, project_file_parser],
        help="create project dependency file",
    )
    parser_create.set_defaults(func=project_create)

    platforms_parser = argparse.ArgumentParser(add_help=False)
    platforms_parser.add_argument(
        "-p",
        "--platform",
        dest="platforms",
        metavar="PLATFORM_NAME",
        action="append",
        help="platform to operate on - repeat option to specify multiple platforms "
        "(default is all platforms)",
    )

    parser_dependency_add = project_subparsers.add_parser(
        "dependency-add",
        parents=[global_option_parser, project_file_parser, dependency_name_parser],
        help="add dependency to project file",
    )
    parser_dependency_add.add_argument(
        "-l",
        "--link-path",
        dest="link_path",
        metavar="LINK_PATH",
        help="dependency will be linked from LINK_PATH in the file system (can be specified relative to "
        "PROJECT_FILE path)",
    )
    parser_dependency_add.add_argument(
        "-t",
        "--tag",
        dest="tags",
        metavar="TAG",
        action="append",
        help="dependency will include TAG in 'tags' attribute - repeat option to define multiple tags",
    )
    parser_dependency_add.add_argument(
        "-f", "--force", action="store_true", help="force overwrite of existing dependency element"
    )
    parser_dependency_add.set_defaults(func=project_dependency_add)
    parser_dependency_remove = project_subparsers.add_parser(
        "dependency-remove",
        parents=[global_option_parser, project_file_parser, dependency_name_parser],
        help="remove dependency from project file",
    )
    parser_dependency_remove.set_defaults(func=project_dependency_remove)

    args = parser.parse_args(argv)
    # Check for the case where no arguments are given and provide basic help and exit.
    # This is straight forward when argv is set but in the shell case we will always
    # have packman.py so if we have one we efffectively have zero.
    if not argv and len(sys.argv) == 1:
        parser.print_help()
        parser.exit()

    auto_yes = False
    if not args.verbose and not args.quiet and not args.silent:
        try:
            value = os.environ[ENVIRONMENT_VARIABLE_FOR_VERBOSITY]
        except KeyError:
            pass
        else:
            verbosity = value.lower()
            setattr(args, verbosity, True)

    my_stdout = None
    my_stderr = None
    if args.verbose:
        set_verbosity_level(VERBOSITY_HIGH)
    elif args.quiet:
        set_verbosity_level(VERBOSITY_LOW)
        sys.stdout = my_stdout = open(os.devnull, "w")
        auto_yes = True
    elif args.silent:
        set_verbosity_level(VERBOSITY_NONE)
        sys.stdout = my_stdout = open(os.devnull, "w")
        sys.stderr = my_stderr = open(os.devnull, "w")
        auto_yes = True

    if auto_yes and hasattr(args, "auto_yes"):
        args.auto_yes = True

    # execute the appropriate command via the subparser func attribute that they set,
    # while passing the agrparse arguments
    ret = args.func(**vars(args))

    if my_stdout:
        my_stdout.close()

    if my_stderr:
        my_stderr.close()

    return ret


VERBOSITY_NONE = logging.CRITICAL
VERBOSITY_LOW = logging.ERROR
VERBOSITY_NORMAL = logging.WARNING
VERBOSITY_HIGH = logging.INFO


def set_verbosity_level(verbosity_level: int):
    """
    Sets the verbosity level of stdout/stderr output from packman
    :param int verbosity_level: Select between the VERBOSITY_ constants
    :return: None
    """
    logger.setLevel(verbosity_level)


def main_with_exception_handler(argv=None):
    try:
        main(argv)
    except Exception as exc:
        exit_code = 1
        if isinstance(exc, errors.PackmanErrorScriptFailure):
            exit_code = exc.error_code
            # On purpose we don't emit a message when an external script returns error code
            # unless verbose level is selected:
            logger.info("Exit code %d from external script will be returned", exit_code)
        elif isinstance(exc, errors.PackmanError):
            logger.error(str(exc))
        elif isinstance(exc, RuntimeError):
            logger.error(str(exc))
        else:
            raise
        sys.exit(exit_code)


# Make sure configuration is read on module import (main reads it again for unit tests).
# This is put in place to deal with circular import of packman module (those need to be
# removed eventually but requires large refactor).
read_configuration()

if __name__ == "__main__":
    main_with_exception_handler()
