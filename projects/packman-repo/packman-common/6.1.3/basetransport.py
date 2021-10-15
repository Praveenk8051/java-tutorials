import packager


class Transport(object):
    def is_file_found(self, path):
        raise NotImplementedError

    def get_package_path(self, package_name, package_version):
        package_filename = packager.get_package_7z_filename(package_name, package_version)
        if self.is_file_found(package_filename):
            return package_filename
        # fall back to older zip container if 7z not found on remote server:
        package_filename = packager.get_package_zip_filename(package_name, package_version)
        if self.is_file_found(package_filename):
            return package_filename
        return None  # package doesn't exist on this server
