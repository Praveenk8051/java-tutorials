import os
import shutil
import tempfile
import uuid
import threading
import sys
import time
import math
import glob2
import re
from typing import List, Tuple


SHELL_VARIABLE_MATCH_OBJECT = re.compile("^[a-zA-Z0-9_]*$")


def get_pretty_size(size_bytes):
    # We use 4-character maximum width for number string
    if size_bytes < 1024:
        return "%d bytes" % size_bytes
    size_name = ("bytes", "KiB", "MiB", "GiB", "TiB", "PiB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    number_str = "%.2f" % s
    l = len(number_str)
    max_len = 4
    if l > max_len:
        # chop of dangling decimal separator:
        if number_str[max_len - 1] == ".":
            max_len -= 1
        excess = l - max_len
        number_str = number_str[: l - excess]

    return "%s %s" % (number_str, size_name[i])


def get_pretty_speed(size_bytes, time_seconds):
    try:
        pretty_speed = "%s/s" % get_pretty_size(size_bytes / time_seconds)
    except ZeroDivisionError:
        pretty_speed = "fast"
    return pretty_speed


class TemporaryDirectory:
    def __init__(self):
        self.path = None

    def __enter__(self):
        self.path = tempfile.mkdtemp()
        return self.path

    def __exit__(self, type, value, traceback):
        # Remove temporary data created
        shutil.rmtree(self.path)


class SwapWorkingDirectory:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        cwd = os.getcwd()
        os.chdir(self.path)
        self.path = cwd

    def __exit__(self, type, value, traceback):
        os.chdir(self.path)


class StagingDirectory:
    def __init__(self, staging_path):
        self.staging_path = staging_path
        self.temp_folder_path = os.path.join(staging_path, str(uuid.uuid4()))

    def __enter__(self):
        os.makedirs(self.temp_folder_path)
        return self

    def get_temp_folder_path(self):
        return self.temp_folder_path

    # this function renames the temp staging folder to folder_name, it is required that the parent path exists!
    def promote_and_rename(self, folder_name):
        abs_dst_folder_name = os.path.join(self.staging_path, folder_name)
        os.rename(self.temp_folder_path, abs_dst_folder_name)

    def __exit__(self, type, value, traceback):
        # Remove temp staging folder if it's still there (something went wrong):
        path = self.temp_folder_path
        if os.path.isdir(path):
            shutil.rmtree(path)


class NoLock(object):
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


def is_stdout_a_terminal():
    return sys.stdout.isatty()


def is_stderr_a_terminal():
    return sys.stderr.isatty()


class ProgressPercentage(object):
    def __init__(self, message_head, size, is_lock_required=False, eta_delay=20):
        self._message_head = message_head
        self._size = size
        self._seen_so_far = 0
        self._speed = 0
        self._is_eta_reported = False
        self._eta_delay = eta_delay
        self._lock = threading.Lock() if is_lock_required else NoLock()

    def __enter__(self):
        # write out short header:
        print("%s (%s)" % (self._message_head, get_pretty_size(self._size)))
        if not is_stdout_a_terminal():
            print(
                "No continuous progress report because this is not a proper terminal. Be patient ..."
            )
        self._start_time = time.time()
        return self

    def __call__(self, bytes_amount, threads_amount=None):
        # shared state change requires lock:
        with self._lock:
            self._seen_so_far += bytes_amount

        if self._size:
            percentage = (self._seen_so_far / float(self._size)) * 100
        else:
            percentage = 100
        if percentage < 0:
            raise Exception("Invalid number of bytes provided - percentage at %d" % percentage)

        seconds_elapsed = time.time() - self._start_time
        # We have seen seconds_elapsed come back as 0.0 on some VMs!  Need to guard against this
        if seconds_elapsed:
            speed = self._seen_so_far / seconds_elapsed
        else:
            speed = 1024 * 1024 * 1024

        self._speed = speed

        if is_stdout_a_terminal():
            # we are changing shared state so need the lock (the state of the output console)
            with self._lock:
                sys.stdout.write("\r")
                if percentage < 10:
                    sys.stdout.write("  ")
                elif percentage < 100:
                    sys.stdout.write(" ")
                sys.stdout.write("%.2f%% (speed %s/s" % (percentage, get_pretty_size(speed)))
                if threads_amount:
                    msg = " | threads %d)    \b\b\b\b" % threads_amount
                else:
                    msg = ")   \b\b\b"
                sys.stdout.write(msg)
                sys.stdout.flush()
        elif seconds_elapsed > self._eta_delay and not self._is_eta_reported:
            if speed:
                seconds_left = (self._size - self._seen_so_far) / self._speed
                print(
                    "This is taking a while. Estimated time of arrival is %d seconds from now ..."
                    % seconds_left
                )
            else:
                print(
                    "This is taking a while. Estimated time of arrival is never because current speed is zero!"
                )
            self._is_eta_reported = True

    def __exit__(self, exc_type, exc_value, traceback):
        if self._size != self._seen_so_far:
            sys.stdout.write("ERROR (expected: %d, actual: %d)\n" % (self._size, self._seen_so_far))
        else:
            if is_stdout_a_terminal():
                sys.stdout.write("\n")
            else:
                sys.stdout.write("100%% (speed %s/s)\n" % get_pretty_size(self._speed))
            seconds_elapsed = time.time() - self._start_time
            sys.stdout.write("Total of %.2f seconds\n" % seconds_elapsed)


def create_valid_shell_variable_name(name):
    # Linux/macOS has severe limitations on shell variable names. Only letters, numbers and underscores are allowed.
    ret = ""
    for char in name:
        if "a" <= char <= "z" or "A" <= char <= "Z" or "0" <= char <= "9":
            ret += char
        else:
            # in all other cases it's an underscore
            ret += "_"
    return ret


def is_valid_shell_variable_name(name):
    if SHELL_VARIABLE_MATCH_OBJECT.match(name):
        return True
    else:
        return False


def replace_with_native_path_separator(path):
    native_path_sep = os.path.sep
    if native_path_sep == "/":
        alt_path_sep = "\\"
    else:
        alt_path_sep = "/"
    return path.replace(alt_path_sep, native_path_sep)


def create_file_list_from_pattern(
    search_pattern: str, folder_rebase: str = None
) -> List[Tuple[str, str]]:
    """
     Creates a list of tuples where each entry is (full_path, package_path). full_path is the path to the
     file on the current filesystem and package_path is the location for the file in the package.
     NOTE: This helper function is typically used with the create_package_from_file_list.
     :param str search_pattern: A string following the Unix glob syntax, recursive paths are specified using '**'. The
       path can be relative to the current working directory or absolute.
     :param str folder_rebase: Optional path to rebase the folders to. The package_path will use 'folder_rebase' as
       its root if specified
     :return: The list of (full_path, package_path) entries
     :rtype: list
    """
    # simplify things by always using native separator:
    search_pattern = replace_with_native_path_separator(search_pattern)
    files = glob2.glob(search_pattern, include_hidden=True)
    ret = []

    chars = "*[?"
    folder_rebase_ix = -1
    if folder_rebase:
        folder_rebase = replace_with_native_path_separator(folder_rebase)
        folder_rebase_ix = search_pattern.rfind(os.path.sep)
        for char in chars:
            ix = search_pattern.find(char)
            if ix != -1:
                ix = search_pattern.rfind(os.path.sep, 0, ix)
            if ix != -1 and ix < folder_rebase_ix:
                folder_rebase_ix = ix

    for rel_path in files:
        if folder_rebase_ix != -1:
            target_path = folder_rebase + rel_path[folder_rebase_ix:]
        else:
            target_path = rel_path
        ret.append((os.path.abspath(rel_path), target_path))

    return ret


def add_site_packages(package_names):
    """
    Adds the packages 'package_names' from folder 'site-packages' to the search list so they can be imported
    :param iterable or str package_names: List of package names
    :return: None
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.join(dir_path, "site-packages")
    if isinstance(package_names, str):
        package_names = (package_names,)
    for item in package_names:
        sys.path.append(os.path.join(dir_path, item))


class ProgressSpeed(object):
    def __init__(self, message_head, is_lock_required=False):
        self._message_head = message_head
        self._seen_so_far = 0
        self._speed = 0
        self._stage = 0
        self._stage_count = 7
        self._lock = threading.Lock() if is_lock_required else NoLock()

    def __enter__(self):
        # write out short header:
        print(self._message_head)
        if not is_stdout_a_terminal():
            print(
                "No continuous progress report because this is not a proper terminal. Be patient ..."
            )
        self._start_time = time.time()
        return self

    def __call__(self, bytes_amount, threads_amount=None):
        # shared state change requires lock:
        with self._lock:
            self._seen_so_far += bytes_amount

        seconds_elapsed = time.time() - self._start_time
        # We have seen seconds_elapsed come back as 0.0 on some VMs!  Need to guard against this
        if seconds_elapsed:
            speed = self._seen_so_far / seconds_elapsed
        else:
            speed = 1024 * 1024 * 1024

        self._speed = speed

        if is_stdout_a_terminal():
            # we are changing shared state so need the lock (the state of the output console)
            self._stage = self._stage % self._stage_count + 1
            with self._lock:
                sys.stdout.write("\r")
                sys.stdout.write("." * self._stage)
                sys.stdout.write(" " * (self._stage_count - self._stage))
                sys.stdout.write(" (speed %s/s" % get_pretty_size(speed))

                if threads_amount:
                    msg = " | threads %d)    \b\b\b\b" % threads_amount
                else:
                    msg = ")   \b\b\b"
                sys.stdout.write(msg)
                sys.stdout.flush()

    def __exit__(self, exc_type, exc_value, traceback):
            if is_stdout_a_terminal():
                sys.stdout.write("\n")
            else:
                sys.stdout.write("... (speed %s/s)\n" % get_pretty_size(self._speed))
            seconds_elapsed = time.time() - self._start_time
            sys.stdout.write("Total of %.2f seconds\n" % seconds_elapsed)
