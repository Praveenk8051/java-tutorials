import string
import os
import logging
import urllib.request, urllib.parse, urllib.error
import utils
import errors
import urllib.parse

from . import basetransport

utils.add_site_packages("boto3-1.4.7")
from botocore.vendored import requests


logger = logging.getLogger("packman.transport.httptransport")


class HttpTransport(basetransport.Transport):
    URL_ENCODE_EXCEPTIONS = "/%?="

    def __init__(self, url_pattern, use_secure_http=False):
        self.url_template = string.Template(url_pattern)
        self.protocol = "https://" if use_secure_http else "http://"

    def is_file_found(self, path):
        protocol_and_path = self.protocol + urllib.parse.quote(
            path, safe=self.URL_ENCODE_EXCEPTIONS
        )
        logger.info("Searching for file at: '%s'", protocol_and_path)
        r = requests.head(protocol_and_path)
        if r.status_code in (requests.codes.ok, requests.codes.found):
            logger.info("File is found")
            return True
        return False

    def get_package_path(self, package_name, package_version):
        url = self.url_template.substitute(name=package_name, version=package_version)
        # Crappy hack below. had to do this because we need it in the name else we cant find the file. this needs to be fixed - Pete.
        if url.endswith("@"):
            url = url[:-1]
        path_candidates = [url, url + ".7z", url + ".zip"]
        for path in path_candidates:
            if self.is_file_found(path):
                return path
        return None

    def download_file(self, source_file_path, target_file_path):
        url = self.protocol + urllib.parse.quote(source_file_path, safe=self.URL_ENCODE_EXCEPTIONS)
        r = requests.get(url, stream=True, timeout=60)
        if not r:
            raise errors.PackmanError(
                "Unable to download file from '%s' (server returned %s)" % (url, r.status_code)
            )
        try:
            size = int(r.headers["Content-length"])
            chunked_encoding = False
        except KeyError:
            chunked_encoding = True
            logger.info("Chunked encoding")

        domain = source_file_path.split("/")[0]
        msg_head = "Downloading from '%s': %s" % (domain, os.path.basename(source_file_path))
        with open(target_file_path, "wb") as out_file:
            if chunked_encoding:
                with utils.ProgressSpeed(msg_head) as progress:
                    for chunk in r.iter_content(chunk_size=None):
                        if chunk:
                            out_file.write(chunk)
                            progress(len(chunk))
            else:
                with utils.ProgressPercentage(msg_head, size) as progress:
                    for chunk in r.iter_content(chunk_size=8 * 1024):
                        if chunk:
                            out_file.write(chunk)
                            progress(len(chunk))
