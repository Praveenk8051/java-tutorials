import os
import sys

import packager
import packman


def get_package_paths_in_folder(top_level_path):
    top_level = os.listdir(top_level_path)
    package_paths = []
    for top_folder in sorted(top_level):
        if top_folder == "chk":
            continue
        path = os.path.join(top_level_path, top_folder)
        if os.path.isdir(path):
            sub_level = os.listdir(path)
            for sub_folder in sub_level:
                sub_path = os.path.join(path, sub_folder)
                if os.path.isdir(sub_path):
                    package_paths.append(sub_path)
    return package_paths


def report(remove_corrupt_packages=False):
    repo_path = packman.get_repo_dir()
    packages_installed = packager.get_packages_installed(repo_path)
    modified_count = 0
    total_count = len(packages_installed)
    for base_name, version in packages_installed:
        sys.stdout.write(base_name + " (" + version + ")")
        sys.stdout.write("...")
        status, path = packager.get_package_install_info(repo_path, base_name, version)
        if status == packager.STATUS_CORRUPT:
            sys.stdout.write("CORRUPT")
            modified_count += 1
        else:
            sys.stdout.write("OK\n")
            continue

        if remove_corrupt_packages:
            packager.remove_package(path)
            sys.stdout.write(" - REMOVED")

        sys.stdout.write("\n")

    print("\nSUMMARY:")
    print("%d corrupt of %d packages" % (modified_count, total_count))
    if modified_count and not remove_corrupt_packages:
        print("Use remove-corrupt option to remove corrupt packages.")
