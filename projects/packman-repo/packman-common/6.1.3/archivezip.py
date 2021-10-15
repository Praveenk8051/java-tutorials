import os
import zipfile
import logging

import utils

logger = logging.getLogger("packman.archivezip")


def _get_files_in_folder(folder_path, parent_path=""):
    f = []
    for (dirpath, dirnames, filenames) in os.walk(folder_path):
        for filename in filenames:
            f.append((os.path.join(dirpath, filename), os.path.join(parent_path, filename)))
        for dir in dirnames:
            new_parent_path = os.path.join(parent_path, dir)
            f.extend(_get_files_in_folder(os.path.join(dirpath, dir), new_parent_path))
        break
    return f


def make_archive_from_folder(input_folder, archive_path):
    """Creates zip archive at 'archive_path' from all the files and folders inside 'input_folder'.
    :type archive_path: str
    :type input_folder: str"""
    # Generate file list:
    file_list = _get_files_in_folder(input_folder)
    return make_archive_from_file_list(archive_path, file_list)


def make_archive_from_file_list(package_path, iterable_file_list):
    """Create a zip file from all the files in 'iterable_file_list' according to the relative paths in
    iterable 'file_list'.

    Uses either the "zipfile" Python module (if available) or the InfoZIP "zip" utility
    (if installed and found on the default search path).  If neither tool is
    available, raises ExecError.  Returns the name of the output zip
    file.
    """
    # Build list of file sizes:
    manifest = []
    file_sizes_total = 0
    for full_path, rel_path in iterable_file_list:
        file_size = os.path.getsize(full_path)
        manifest.append((full_path, rel_path, file_size))
        file_sizes_total += file_size

    zip_filename = package_path
    archive_dir = os.path.dirname(package_path)

    if not os.path.exists(archive_dir):
        if logger is not None:
            logger.info("creating %s", archive_dir)
        os.makedirs(archive_dir)

    if logger is not None:
        logger.info("creating file '%s'" % zip_filename)

    # allow 64-bit so we can have huge zips
    zip = zipfile.ZipFile(zip_filename, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True)

    total_size = file_sizes_total
    with utils.ProgressPercentage(
        "Compressing: %s " % os.path.basename(zip_filename), total_size
    ) as bar:
        for full_path, rel_path, size in manifest:
            zip.write(full_path, rel_path)
            bar(size)
            if logger is not None:
                logger.info("\nadding '%s'", full_path)
    zip.close()
    output_size = os.path.getsize(zip_filename)
    percentage = float(output_size * 100) / file_sizes_total
    print(
        "Output size: %s (Compressed to %.1f%% of input size)"
        % (utils.get_pretty_size(output_size), percentage)
    )
    return zip_filename


def _extract_file(zip_file, file_info, extract_dir):
    """
    Extracts the file in 'file_info' from zip 'zip_file' to directory 'extract_dir' and preserves
    file permissions on the resulting file (using chmod).
    :type zip_file: ZipFile
    :type file_info: ZipInfo
    :rtype: None
    """
    zip_file.extract(file_info, path=extract_dir)
    out_path = os.path.join(extract_dir, file_info.filename)

    perm = file_info.external_attr >> 16
    # the permission info is sometimes missing from funky zip files so then we must skip it:
    if perm:
        os.chmod(out_path, perm)


def extract_archive_to_folder(archive_path, output_folder):
    with zipfile.ZipFile(archive_path, allowZip64=True) as zip_file:
        # display an unzip progress bar for the user
        uncompress_size = sum(file.file_size for file in zip_file.infolist())
        package_name = os.path.basename(archive_path)
        with utils.ProgressPercentage("Unzipping: %s" % package_name, uncompress_size) as bar:
            for file_info in zip_file.infolist():
                _extract_file(zip_file, file_info, output_folder)
                bar(file_info.file_size)
