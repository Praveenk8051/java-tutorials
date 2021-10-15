import hashlib
import os


def generate_sha1_for_file(file_path) -> str:
    sha1 = hashlib.sha1()
    with open(file_path, "rb") as f:
        while True:
            buf = f.read(64 * 1024)
            if not buf:
                break
            sha1.update(buf)
    return sha1.hexdigest()


def __update_hash_for_folder_recursively(
    hasher, root_path: bytes, rel_path: bytes = "", rel_exclude_path: bytes = None
):
    # lets just make sure we are working with bytes objects
    if type(root_path) == str:
        root_path = root_path.encode("utf8")
    if type(rel_path) == str:
        rel_path = rel_path.encode("utf8")
    if type(rel_exclude_path) == str:
        rel_exclude_path = rel_exclude_path.encode("utf8")
    path = os.path.join(root_path, rel_path)
    for entry in sorted(os.listdir(path)):
        rel_entry_path = os.path.join(rel_path, entry)
        if rel_entry_path == rel_exclude_path:
            continue
        entry_path = os.path.join(path, entry)
        if os.path.isdir(entry_path):
            hasher.update(b"dir '" + rel_entry_path + b"'\0")
            # Only recurse into regular folders (not symbolic links)
            if not os.path.islink(entry_path):
                __update_hash_for_folder_recursively(
                    hasher, root_path, rel_entry_path, rel_exclude_path
                )
        elif os.path.isfile(entry_path):
            hasher.update(b"file '" + rel_entry_path + b"' ")
            hasher.update(str(os.path.getsize(entry_path)).encode("utf-8") + b" ")
            hasher.update(generate_sha1_for_file(entry_path).encode("utf-8") + b"\0")


def generate_sha1_for_folder(folder_path) -> str:
    hasher = hashlib.sha1()
    __update_hash_for_folder_recursively(hasher, folder_path)
    return hasher.hexdigest()


def generate_sha1_for_folder_with_exclusion(
    folder_path: bytes, relative_path_to_exclusion: bytes
) -> str:
    hasher = hashlib.sha1()
    relative_path_to_exclusion_native = relative_path_to_exclusion.replace("/", os.path.sep)
    __update_hash_for_folder_recursively(
        hasher, folder_path, rel_exclude_path=relative_path_to_exclusion_native
    )
    return hasher.hexdigest()
