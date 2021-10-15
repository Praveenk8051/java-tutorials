import os
import tarfile
import posixpath
import shutil
import logging
import sys
import stat

import utils
import errors
from version import PRODUCT_VERSION
from transport import httptransport

logger = logging.getLogger("packman.updater")


def get_directory_entries_in_folder(folder_path):
    f = []
    for (dirpath, dirnames, filenames) in os.walk(folder_path):
        for filename in filenames:
            f.append(os.path.join(folder_path, filename))
        for dir in dirnames:
            sub_folder_path = os.path.join(folder_path, dir)
            f.append(sub_folder_path)
            f.extend(get_directory_entries_in_folder(sub_folder_path))
        break
    return f


def backup_and_remove_directory_entry(src_path_abs, dst_path_abs, force, undo_stack):
    mode = os.stat(src_path_abs).st_mode
    if not os.access(src_path_abs, os.W_OK):
        if force:
            os.chmod(src_path_abs, mode | stat.S_IWRITE)
        else:
            logger.error("Process does not have permission to remove '%s'", src_path_abs)
            logger.error("Run this command with 'force' option to remove/replace read-only files")
            raise errors.PackmanError()  # message is generated in outer except block

    try:
        if os.path.isdir(src_path_abs):
            if not os.path.exists(dst_path_abs):
                os.makedirs(dst_path_abs)
            # copy mode settings over
            os.chmod(dst_path_abs, mode)
            # create undo command:
            args = (src_path_abs, mode)
            undo_stack.append((os.chmod, args))
            # remove dir
            os.rmdir(src_path_abs)
            # create undo command:
            args = src_path_abs
            undo_stack.append((os.makedirs, args))
        else:
            target_dir = os.path.dirname(dst_path_abs)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            shutil.copy2(src_path_abs, dst_path_abs)
            os.remove(src_path_abs)
            args = (dst_path_abs, src_path_abs)
            undo_stack.append((shutil.copy2, args))
    except OSError as exc:
        logger.error("Failed to backup and remove path (%s)" % exc)
        raise


def update_from_build(build_path, installation_path, force=False):
    if not os.path.exists(build_path):
        raise errors.PackmanError("Path '%s' not found!" % build_path)
    with utils.TemporaryDirectory() as temp_dir:
        entries = get_directory_entries_in_folder(installation_path)
        try:
            sys.stdout.write("Making a backup .")
            # make a backup of each entry as we remove it
            backup_path = temp_dir
            undo_stack = []
            while entries:
                sys.stdout.write(".")
                sys.stdout.flush()
                src_path_abs = entries.pop()
                path_rel = os.path.relpath(src_path_abs, installation_path)
                if path_rel == "config.packman.xml":
                    # we leave this file alone
                    continue
                dst_path_abs = os.path.join(backup_path, path_rel)
                backup_and_remove_directory_entry(src_path_abs, dst_path_abs, force, undo_stack)
            sys.stdout.write(" done!\n")
            sys.stdout.write("Extracting build to install folder ...")
            sys.stdout.flush()
            # now add the files that are to be added or replaced by just extracting the tarfile:
            try:
                with tarfile.open(build_path) as tar:
                    tar.extractall(path=installation_path)
                sys.stdout.write(" done!\n")
            except Exception as exc:
                logger.error(
                    "Failed to extract build to installation location (%s)" % installation_path
                )
                raise

        except Exception as exc:
            sys.stdout.write("Rolling back the update ")
            while undo_stack:
                func, args = undo_stack.pop()
                func(*args)
                sys.stdout.write(".")
                sys.stdout.flush()
            sys.stdout.write(" done!\n")
            sys.stdout.flush()
            raise errors.PackmanError("Update operation failed")


def fetch_file(filename, target_path):
    tp = httptransport.HttpTransport(
        "packman-bootstrap.s3.amazonaws.com/${name}", use_secure_http=True
    )
    path = tp.get_package_path(filename, None)
    if not path:
        raise errors.PackmanError("File '%s' not found on bootstrap server!" % filename)
    tp.download_file(path, target_path)


def fetch_last_known_good_version():
    with utils.TemporaryDirectory() as temp_dir:
        # get version from label - for our current version
        major_version = PRODUCT_VERSION.split(".")[0]
        label_name = "packman-command@%s.last-known-good.txt" % major_version
        label_target_path = os.path.join(temp_dir, label_name)
        fetch_file(label_name, label_target_path)
        with open(label_target_path) as infile:
            build_filename = infile.read().strip()
        head = os.path.splitext(build_filename)[0]
        version = head.split("@")[1]
    return version


def update(version, install_path, force=False):
    with utils.TemporaryDirectory() as temp_dir:
        build_filename = "packman-command@%s.tar" % version
        target_path = os.path.join(temp_dir, build_filename)
        fetch_file(build_filename, target_path)
        update_from_build(target_path, install_path, force)
    print("packman (%s) updated successfully to version %s" % (install_path, version))
