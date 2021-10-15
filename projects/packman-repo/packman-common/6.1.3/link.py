import subprocess
import os
from packman import CONSOLE_ENCODING


def _call_command(args):
    p = subprocess.Popen(
        args, bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    out, err = p.communicate()
    # we need to return out and err as str, not bytes
    return p.returncode, out.decode(CONSOLE_ENCODING), err.decode(CONSOLE_ENCODING)


def _sanitize_path(path):
    # Adjust paths so they match native format
    ret = path.replace("/", os.path.sep)  # posix fix
    ret = ret.rstrip(os.path.sep)  # chop of any trailing slashes
    return ret


def _get_link_target_win(link_folder_path):
    # fsutil would be the clean way to do this but it requires ADMIN privileges. Windows, oh why?  So
    # we must resort to a very roundabout way.
    # 1. list the parent directory contents looking for link folders
    # 2. parse out the entry we are looking for
    # 3. parse out the link
    # NOTE: we must be careful to normalize the path because otherwise we go through the link!!
    parent_path = os.path.normpath(os.path.join(link_folder_path, os.pardir))
    args = ("dir", "/A:L", parent_path)
    ret_code, out, err = _call_command(args)
    if ret_code == 0:
        lines = out.splitlines()
        keys = ["<JUNCTION>", "<SYMLINKD>"]
        for line in lines:
            for key in keys:
                start = line.find(key)
                if start != -1:
                    end = start + len(key)
                    terms = line[end:].split("[")
                    if len(terms) > 1:
                        link_name = os.path.normcase(terms[0].strip())
                        link_target = terms[1].strip("]")
                        link_name_to_find = os.path.normcase(os.path.basename(link_folder_path))
                        if link_name == link_name_to_find:
                            return link_target
    raise RuntimeError("Failed to get link target for '%s'" % link_folder_path)


def _create_junction_link(link_folder_path, target_folder_path):
    # target folder path can be relative but mklink interprets it as relative to CWD rather than relative to link
    # - we want the latter so must do the lifting ourselves:
    path = target_folder_path
    path = os.path.join(os.path.dirname(link_folder_path), path)
    path = os.path.normpath(path)

    args = ("mklink", "/j", link_folder_path, path)
    ret_code, out, err = _call_command(args)
    if ret_code:
        msg = err.strip() + " (%s ==> %s)" % (link_folder_path, path)
        raise RuntimeError(msg)


def _destroy_link_win(link_folder_path):
    args = ("rmdir", link_folder_path)
    ret_code, out, err = _call_command(args)
    if ret_code:
        msg = err.strip() + " (%s)" % link_folder_path
        raise RuntimeError(msg)


def get_link_target(link_folder_path):
    # reordered this check. it was hasattr(os, 'readlink'), if 'nt', else
    # a better fix might be available, but i've not looked into it yet - Petert
    link_folder_path = _sanitize_path(link_folder_path)
    if os.name == "nt":
        path = _get_link_target_win(link_folder_path)
    elif hasattr(os, "readlink"):
        try:
            path = os.readlink(link_folder_path)
        except OSError as exc:
            raise RuntimeError(str(exc))
    else:
        raise NotImplementedError("get_link_target not implemented for this platform")
    # path can be relative to link path so we convert to absolute path:
    path = os.path.join(os.path.dirname(link_folder_path), path)
    path = os.path.normpath(path)
    return path


def create_link(link_folder_path, target_folder_path):
    """
    Creates a file system link from 'link_folder_path' to 'target_folder_path'
    :param link_folder_path: Absolute or relative path to link folder to create
    :param target_folder_path: Absolute or relative path to target folder; if relative then it is
     relative to 'link_folder_path'
    :return: None
    """
    link_folder_path = _sanitize_path(link_folder_path)
    target_folder_path = _sanitize_path(target_folder_path)
    # We always try first using symlink, this can fail on Windows if admin privileges are not
    # present - we then fall back to junction point.
    try:
        os.symlink(target_folder_path, link_folder_path, target_is_directory=True)
    except OSError as exc:
        message = str(exc)
        if os.name == "nt" and "privilege not held" in message:
            _create_junction_link(link_folder_path, target_folder_path)
        else:
            raise RuntimeError(message)


def destroy_link(link_folder_path):
    """
    Destroys an existing file system link
    :param link_folder_path: Path to linked folder to destroy.
    :return: None
    """
    link_folder_path = _sanitize_path(link_folder_path)
    if os.name == "nt":
        _destroy_link_win(link_folder_path)
    else:
        try:
            os.unlink(link_folder_path)
        except OSError as exc:
            raise RuntimeError(str(exc))
