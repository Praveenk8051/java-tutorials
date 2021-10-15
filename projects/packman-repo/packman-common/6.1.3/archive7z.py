import subprocess
import os
import sys
import platform
import multiprocessing
import time
import logging

import utils
from errors import PackmanError


# This constant must be set to where 7z command is located
PATH_TO_7Z_COMMAND = None


def locate_7z_command():
    """Finds suitable 7z command or raises an exception if not found"""
    # This gets the bitness of the current Python interpreter which we use as a proxy for OS bitness
    is_64bits = sys.maxsize > 2 ** 32
    # We need to branch on OS because they have different flavors of 7z commands
    platform_name = platform.system()
    if platform_name == "Windows":
        # We can do better than above in detecting bitness of this OS:
        if platform.machine().endswith("64"):
            is_64bits = True
        name_of_exe = "7za.exe"
        architecture = "win-x86"
    elif platform_name == "Darwin":
        # macOS
        name_of_exe = "7za"
        architecture = "mac-x86"
    elif platform_name == "Linux":
        name_of_exe = "7za"
        if platform.processor() == "aarch64":
            architecture = "linux-arm"
        else:
            architecture = "linux-x86"
    else:
        raise PackmanError("Operating system %r not supported" % platform_name)

    if is_64bits:
        bitness = 64
    else:
        bitness = 32

    subfolder = os.path.join(architecture, str(bitness))
    try:
        path_to_7za_root = os.environ["PM_7za_PATH"]
    except KeyError:
        # fall back to local repo 7za for testing
        my_dir = os.path.dirname(os.path.realpath(__file__))
        path_to_7za_root = os.path.join(my_dir, "test_data", "7za")

    path_to_exe = os.path.join(path_to_7za_root, subfolder, name_of_exe)

    if os.path.exists(path_to_exe):
        return path_to_exe
    else:
        raise RuntimeError("7z command not found at '%s'" % path_to_exe)


def _call_command(command, switches, files, report_errors=True):
    global PATH_TO_7Z_COMMAND
    if PATH_TO_7Z_COMMAND is None:
        PATH_TO_7Z_COMMAND = locate_7z_command()

    params = [PATH_TO_7Z_COMMAND, command]
    params.extend(switches)
    try:
        cpu_count = multiprocessing.cpu_count()
        params.append("-mmt" + str(cpu_count))
    except NotImplementedError:
        pass

    if logging.getLogger("packman").isEnabledFor(logging.INFO):
        # stream out progress reports to error channel if TTY terminal
        if utils.is_stderr_a_terminal():
            params.append("-bsp2")
        else:
            print(
                "No continuous progress report because this is not a proper terminal. Patience is a virtue ..."
            )

    params.extend(files)
    if platform.system() == "Windows":
        create_shell = True
    else:
        create_shell = False
    return subprocess.check_output(params, shell=create_shell)


def make_archive_from_folder(input_folder, archive_path):
    """Creates 7z archive at 'archive_path' from all the files and folders inside 'input_folder'.
    An extension of 7z is added if it's not included in 'archive_path'
    :type archive_path: str
    :type input_folder: str"""
    if not archive_path.endswith(".7z"):
        archive_path += ".7z"
    # We want all the files inside the input_folder, not the folder itself
    # But first we check that folder exists and is a proper folder:
    if not os.path.exists(input_folder):
        raise PackmanError("'%s' is not a valid directory" % input_folder)

    with utils.SwapWorkingDirectory(input_folder):
        input_files = "*"
        switches = ["-mx=9"]
        files = [archive_path, input_files]

        print("Compressing:", os.path.basename(archive_path))
        try:
            start_time = time.time()
            out = _call_command("a", switches, files)
            seconds_elapsed = time.time() - start_time
        except subprocess.CalledProcessError:
            # Don't leave half-baked archive behind
            if os.path.exists(archive_path):
                os.remove(archive_path)
            raise PackmanError("Archive creation failed.")

    output_size = os.path.getsize(archive_path)
    # Process the output stream to get total input size:
    input_size = None
    start_ix = out.find(b"Scanning the drive:")
    if start_ix != -1:
        end_ix = out.find(b"bytes", start_ix)
        if end_ix != -1:
            words = out[start_ix:end_ix].split(b",")
            input_size = int(words[-1].strip())
    compression = ""
    speed = ""
    if input_size:
        speed = "(speed %s)" % utils.get_pretty_speed(input_size, seconds_elapsed)
        percentage = float(output_size * 100) / input_size
        compression = "(Compressed to %.1f%% of input size)" % percentage
    print("100%% %s" % speed)
    print("Total of %.2f seconds" % seconds_elapsed)
    print("Output size: %s %s" % (utils.get_pretty_size(output_size), compression))
    return archive_path


def extract_archive_to_folder(archive_path, output_folder):
    switches = ["-y", "-o" + output_folder]
    print(
        "Decompressing: %s (%s)"
        % (os.path.basename(archive_path), utils.get_pretty_size(os.path.getsize(archive_path)))
    )
    try:
        start_time = time.time()
        out = _call_command("x", switches, [archive_path])
        seconds_elapsed = time.time() - start_time
    except subprocess.CalledProcessError:
        raise PackmanError("Archive extraction failed.")

    # Process the output stream to get total input size:
    lines = out.splitlines()
    words = lines[-2].split()
    uncompressed_size = int(words[1])
    print("100%% (speed %s)" % utils.get_pretty_speed(uncompressed_size, seconds_elapsed))
    print("Total of %.2f seconds" % seconds_elapsed)
    print("Output size: %s" % utils.get_pretty_size(uncompressed_size))


def get_archive_uncompressed_size(archive_path):
    """
    Return the size that the archive would consume uncompressed
    :param str archive_path: Path to archive, including extension
    :return int: Size of archive when it has been uncompressed
    """
    try:
        out = _call_command("l", [], [archive_path])
        lines = out.splitlines()
        words = lines[-1].split()
        return int(words[2])
    except subprocess.CalledProcessError as exc:
        raise PackmanError("Unable to access archive '%s' (%s)" % (archive_path, exc))
