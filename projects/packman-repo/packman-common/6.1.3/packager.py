import os
import logging
import utils
import time
import re
import errno
import shutil
import stat
from typing import Iterable, Tuple

import archive7z
import archivezip
import checksum

__author__ = "hfannar"

logger = logging.getLogger("packman.packager")


def create_package(
    package_input_dir: str, output_dir: str, output_package_name: str = None, container: str = "7z"
) -> str:
    """
    :param str package_input_dir: Path to top-level folder for the unpacked package (usually version number folder)
    :param str output_dir: The directory where the resulting package will be place
    :param str output_package_name: Optionally specify package name (otherwise derived from package_input_dir and
                                    parent folder)
    :param str container: Select between '7z' and 'zip'. This controls file format used for package and
        the compression (LZMA2 vs DEFLATE).
    :return: The full path name of the output package
    :rtype: str
    """
    if container == "7z":
        ext = ".7z"
    else:
        ext = ".zip"

    # First construct the base name
    if output_package_name:
        base_name = output_package_name
        # add extension if not provided
        if not base_name.lower().endswith(ext):
            base_name += ext
    else:
        head, version_name = os.path.split(os.path.abspath(package_input_dir))
        head, package_name = os.path.split(head)
        base_name = package_name + "@" + version_name + ext

    # Now construct full path:
    package_path = os.path.join(output_dir, base_name)

    if os.path.exists(package_path):
        print("Old package found with the same name, removing...")
        os.remove(package_path)

    logger.info("Creating package %s ..." % base_name)
    if container == "7z":
        return archive7z.make_archive_from_folder(package_input_dir, package_path)
    else:
        return archivezip.make_archive_from_folder(package_input_dir, package_path)


def create_package_from_file_list(
    iterable_file_list: Iterable[Tuple[str, str]], package_path: str
) -> str:
    """
    Creates a package at 'package_path' containing the files specified in 'file_list' according to the relative path
    structure specified in 'file_list'.
    NOTE: use create_file_list_from_pattern to generate the 'file_list' from unix style glob pattern
    :param iterable iterable_file_list: An iterable where each entry is a tuple of (full_path, relative_path) where
      full_path is the location on the file system and relative_path is the location in the resulting package file
    :param package_path: Full path to the resulting package (preferably without .zip extension)
    :return: The full path name of the output package
    :rtype: str
    """
    head, base_name = os.path.split(os.path.abspath(package_path))
    if os.path.exists(package_path):
        print("Old package found with the same name, removing...")
        os.remove(package_path)

    logger.info("Creating package %s ..." % base_name)
    archivezip.make_archive_from_file_list(package_path, iterable_file_list)
    return package_path


STATUS_INSTALLED = 0
STATUS_CORRUPT = 1
STATUS_MISSING = 2

__PACKMAN_SHA1_FILE_NAME = ".packman.sha1"


def get_package_install_info(cache_path, base_name, version):
    """
    Returns Status of package and install path
    :param str base_name: package base name
    :param str version: package version
    :param str cache_path: path to packages root location
    :return (int, str): A STATUS_INSTALLED if package is installed, a STATUS_CORRUPT is returned if determined to be
        corrupt, and a STATUS_MISSING is returned if the package is missing. Secondly the install path is returned
    """
    package_rel_path = os.path.join(base_name, version)
    cache_sha1_path = os.path.join(cache_path, "chk")
    package_sha1_path = os.path.join(cache_sha1_path, package_rel_path)
    if os.path.exists(package_sha1_path):
        status = STATUS_INSTALLED
        if not os.path.exists(os.path.join(package_sha1_path, __PACKMAN_SHA1_FILE_NAME)):
            logger.info("Package at '%s' is corrupt (missing sha1 file)", package_sha1_path)
            status = STATUS_CORRUPT
        return status, package_sha1_path
    else:
        # for compatibility with previously fetched packages (prior to packman 5.0)
        package_path = os.path.join(cache_path, package_rel_path)
        if os.path.exists(package_path) and os.listdir(package_path):
            return STATUS_INSTALLED, package_path
        else:
            return STATUS_MISSING, package_sha1_path


def get_basename_and_version_from_package_name(package_name):
    """
    Returns basename and version for the package name provided.
    :param str package_name: Name of package file name, with our without extension
    :return (str, str): The base name of the package and the version component
    """
    # lets strip off the extension if the extension is a known type. otherwise we leave it.
    # This is to address - https://gitlab-master.nvidia.com/hfannar/packman/issues/100
    filename, ext = os.path.splitext(package_name)
    if ext.lower() in [".7z", ".zip", ".tar"]:
        package_name = filename
    return package_name.split("@", 1)


def __get_packages_map(top_level_path):
    top_level = os.listdir(top_level_path)
    package_paths = {}
    for top_folder in sorted(top_level):
        if top_folder == "chk":
            continue
        path = os.path.join(top_level_path, top_folder)
        if os.path.isdir(path):
            sub_level = os.listdir(path)
            for sub_folder in sorted(sub_level):
                sub_path = os.path.join(path, sub_folder)
                if os.path.isdir(sub_path):
                    package_paths[top_folder + "@" + sub_folder] = (top_folder, sub_folder)
    return package_paths


def get_packages_installed(cache_path):
    """
    Returns a list of tuples (base_name, version) of packages installed in 'cache_path'. Use get_package_install_info
        to learn about the status of each package
    :param str cache_path: Path to where packages are stored
    :return list: A list of tuples (base_name, version)
    """
    packages = __get_packages_map(cache_path)
    checked_packages_path = os.path.join(cache_path, "chk")
    if os.path.exists(checked_packages_path):
        checked_packages = __get_packages_map(checked_packages_path)
        packages.update(checked_packages)

    # return as sorted list:
    sorted_packages = list(packages.values())
    sorted_packages.sort()
    return sorted_packages


def remove_package(install_path):
    def onerror(func, path, exc_info):
        """
        Error handler for ``shutil.rmtree``.

        If the error is due to an access error (read only file)
        it attempts to add write permission and then retries.

        If the error is for another reason it re-raises the error.

        Usage : ``shutil.rmtree(path, onerror=onerror)``
        """
        import stat

        if not os.access(path, os.W_OK):
            # Is the error an access error ?
            os.chmod(path, stat.S_IWUSR)
            func(path)
        else:
            raise

    logger.info("Removing package at '%s'", install_path)
    shutil.rmtree(install_path, onerror=onerror)


def verify_package(install_path):
    sha1_path = os.path.join(install_path, __PACKMAN_SHA1_FILE_NAME)
    with open(sha1_path) as f:
        sha1_from_file = f.read()
    sha1_from_package = checksum.generate_sha1_for_folder_with_exclusion(
        install_path, __PACKMAN_SHA1_FILE_NAME
    )
    return sha1_from_file == sha1_from_package


def generate_empty_sha1_file(folder_path):
    sha1_file_name = __PACKMAN_SHA1_FILE_NAME
    file_path = os.path.join(folder_path, sha1_file_name)
    with open(file_path, "w") as out_file:
        pass


def generate_sha1_file(folder_path):
    sha1_file_name = __PACKMAN_SHA1_FILE_NAME
    sha1 = checksum.generate_sha1_for_folder_with_exclusion(folder_path, sha1_file_name)
    file_path = os.path.join(folder_path, sha1_file_name)
    with open(file_path, "w") as out_file:
        out_file.write(sha1)


# Both GitLab and GitHub practice this annoying shell game where their zips contain a redundant top
# level folder, which is named the same as the zip downloaded (without '.zip' extension)
def _remove_redundant_top_level_folder(package_path, output_folder):
    top_level_items = os.listdir(output_folder)
    if len(top_level_items) == 1:
        folder_name = top_level_items[0]
        package_name, package_version = os.path.basename(package_path).split("@")
        package_version, ext = os.path.splitext(package_version)
        if folder_name.startswith(package_name) and folder_name[len(package_name) + 1:].startswith(package_version):
            folder_path = os.path.join(output_folder, folder_name)
            folder_items = os.listdir(folder_path)
            for item in folder_items:
                src_path = os.path.join(folder_path, item)
                shutil.move(src_path, output_folder)
            try:
                os.chmod(folder_path, stat.S_IWUSR)
                os.rmdir(folder_path)
            except OSError:
                pass


def install_package(package_path, install_path):
    staging_path, version = os.path.split(install_path)
    with utils.StagingDirectory(staging_path) as staging_dir:
        output_folder = staging_dir.get_temp_folder_path()
        if package_path.endswith(".7z"):
            archive7z.extract_archive_to_folder(package_path, output_folder)
        else:
            archivezip.extract_archive_to_folder(package_path, output_folder)
            _remove_redundant_top_level_folder(package_path, output_folder)

        # Generate hash for the package contents - we are disabling this to optimize (see issue #109)
        # Another checksum approach is needed.
        generate_empty_sha1_file(output_folder)

        # attempt the rename operation
        start_time = time.time()
        try:
            staging_dir.promote_and_rename(version)
            logger.info("Package rename took %f seconds" % (time.time() - start_time))
        except OSError as exc:
            # if we failed to rename because the folder now exists we can assume that another packman process
            # has managed to update the package before us - in all other cases we re-raise the exception
            if exc.errno == errno.EEXIST or exc.errno == errno.ENOTEMPTY:
                logger.warning(
                    "Directory %s already present, packaged installation aborted" % install_path
                )
            else:
                raise

    print("Package successfully installed to %s" % install_path)


def get_package_zip_filename(base_name: str, version: str) -> str:
    """
    :param str base_name: Base name of package
    :param str version: Version string for package
    :return: Full name of package in zip container
    :rtype: str
    """
    return base_name + "@" + version + ".zip"


def get_package_7z_filename(base_name, version):
    """
    :param str base_name: Base name of package
    :param str version: Version string for package
    :return: Full name of package in 7z container
    :rtype: str
    """
    return base_name + "@" + version + ".7z"


def list_package_versions(package_name, package_list):
    """
    Returns a list of published package versions.  It is assumed that packages always take this form:
        'package_name@package_version.{7z,zip}'. The match on 'package_name' is case-insensitive.
        This function assumes the characters between the '@' and the extension are the package version.
    :param str package_name:
    :param iterable package_list: A list of package titles returned from the storage search
    :return: A list of package version strings
    """
    package_versions = []
    for package in package_list:
        at = re.search("@", package)
        if at:
            name_ends = at.start()
            version_begins = name_ends + 1
            version_ends = None
            if package.endswith(".7z"):
                version_ends = len(package) - 3
            elif package.endswith(".zip"):
                version_ends = len(package) - 4
            if version_ends is not None:
                this_package_name = package[:name_ends]
                if package_name == this_package_name:
                    version = package[version_begins:version_ends]
                    if version not in package_versions:
                        package_versions.append(version)

    return package_versions


def copy_package_if_version_differs(install_path, target_path):
    """Copies a package if the version differs at target path, or doesn't exist.

    :param str install_path: Full path to the package in packman cache
    :param str target_path: Path to where the package should be copied.
    """
    prefix, version = os.path.split(install_path)
    prefix, name = os.path.split(prefix)
    version_target_file = os.path.join(target_path, "." + name + "@" + version)
    if os.path.exists(version_target_file):
        return

    if os.path.exists(target_path):
        remove_package(target_path)

    print("Copying package '%s' at version '%s' to '%s' ..." % (name, version, target_path))
    shutil.copytree(install_path, target_path)
    open(version_target_file, "w").close()
