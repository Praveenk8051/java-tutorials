import socket
import os.path
import time
import string
import mimetypes
import random
import logging
import threading
import collections
import sys
import base64
from urllib import parse as urlparse
from http import client as httplib
from xmlrpc import client as xmlrpclib
from urllib.request import urlopen

import utils

# This is required for the closed embedded python int
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .s3transport import S3Transport
from .httptransport import HttpTransport
import errors
from . import basetransport

utils.add_site_packages("boto3-1.9.214")
from botocore.vendored import requests

__author__ = "hfannar"
__all__ = ["GtlTransport", "GTL_API"]

logger = logging.getLogger("packman.transport")
GTL_API = "gtl-api.nvidia.com:8080"
GTL_RETRY_COUNT = 2
GTL_RETRY_DELAY = 20  # seconds until web request retry is attempted
GTL_TIMEOUT = 120  # seconds for web request timeout

_BOUNDARY_CHARS = string.digits + string.ascii_letters


def create_transport(type_name, credentials=None, location=None, error_url=None):
    """
    :param str type_name: Valid inputs are 'gtl' and 's3'. They can be followed by a colon to specify
        account (gtl) or bucket (s3)
    :param tuple credentials: A tuple containing transport credentials.
    :param str location: Some transport types require a location specifier, like bucket for S3.
    :return: Returns a new transport object, supporting upload_file, download_file and list_files.
    """
    if type_name == "gtl":
        return GtlTransport(username=credentials[0], key=credentials[1])
    elif type_name == "s3":
        if not location:
            raise errors.PackmanError("Bucket must be specified for S3 transport type")
        return S3Transport(access_key_pair=credentials, bucket_name=location, error_url=error_url)
    elif type_name == "http":
        if not location:
            raise errors.PackmanError(
                "Package location URL must be specified for HTTP transport type"
            )
        return HttpTransport(location)
    elif type_name == "https":
        if not location:
            raise errors.PackmanError(
                "Package location URL must be specified for HTTPS transport type"
            )
        return HttpTransport(location, use_secure_http=True)
    else:
        raise errors.PackmanError("Transport type %r not supported!" % type_name)


def _retry():
    """Retry calling the decorated function GTL_RETRY_COUNT times (if it fails due to connection error). The delay
    between retries is GTL_RETRY_DELAY seconds.
    :return: Returns the values from the decorated functions if it succeeds within GTL_RETRY_COUNT+1 attempts, otherwise
    passes the exception along.
    """

    def deco_retry(func):
        def func_retry(*args, **kwargs):
            retries_left = GTL_RETRY_COUNT
            while True:
                try:
                    return func(*args, **kwargs)
                except (xmlrpclib.Error, IOError) as exc:
                    if retries_left:
                        retry_delay = GTL_RETRY_DELAY
                        retry_str = str(retries_left) + (
                            " retry left" if retries_left == 1 else " retries left"
                        )
                        logger.error(
                            "NVGTL is unreachable or returned HTTP error. Retrying after "
                            "%d seconds (%s) ..." % (retry_delay, retry_str)
                        )
                        time.sleep(retry_delay)
                        retries_left -= 1
                    else:
                        raise errors.PackmanError(
                            "NVGTL is unreachable. Retries exhausted. Is VPN disconnected or "
                            "network down? (%s)" % exc
                        )

        return func_retry

    return deco_retry


def encode_multipart(file_form, boundary=None):
    r"""Encode a file form as multipart/form-data. The file_form is a tuple of
    the field name and a dict that maps 'filename' to a full path to filename.
    The dict can optionally contain a 'mimetype' key (if not specified, tries
    to guess mime type or uses 'application/octet-stream').
    Returns a tuple of (headers, data_begin, data_end).

    >>> body, headers = encode_multipart(
    ...                                  ('FILE': {'filename': 'F.TXT'}),
    ...                                  boundary='BOUNDARY')
    >>> print('\n'.join(repr(l) for l in body.split('\r\n')))
    '--BOUNDARY'
    'Content-Disposition: form-data; name="FILE"; filename="F.TXT"'
    'Content-Type: text/plain'
    ''
    'CONTENT'
    '--BOUNDARY--'
    ''
    """

    def escape_quote(s):
        return s.replace('"', '\\"')

    if boundary is None:
        boundary = "".join(random.choice(_BOUNDARY_CHARS) for i in range(30))
    lines = []

    name, value = file_form
    filename = value["filename"]
    mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    lines.extend(
        (
            "--{0}".format(boundary),
            'Content-Disposition: form-data; name="{0}"; filename="{1}"'.format(
                escape_quote(name), escape_quote(filename)
            ),
            "Content-Type: {0}".format(mimetype),
            "",
        )
    )

    data_end = "\r\n--{0}--\r\n".format(boundary).encode("utf-8")
    data_begin = "\r\n".join(lines).encode("utf-8")
    data_begin += "\r\n".encode("utf-8")

    headers = {
        "Content-Type": "multipart/form-data; boundary={0}".format(boundary),
        "Content-Length": str(len(data_begin) + os.path.getsize(filename) + len(data_end)),
    }

    return headers, data_begin, data_end


THREAD_BLOCK_SIZE = 8 * 1024 * 1024


class ThreadedTransport:
    def _set_block_size(self, size):
        self.block_size = size
        self.chunk_size = size / 16

    def __init__(self, smart_threading=True):
        self.lock = threading.Lock()

        self.source_url = ""
        self.source_size = 0
        self.target_file = None
        self._set_block_size(THREAD_BLOCK_SIZE)
        self.smart_threading = smart_threading

        self.exception = None

        self.download_threads = []
        self.progress = 0
        self.max_download_threads = 10
        self.chunks_to_write = {}
        self.ranges_to_fetch = []
        self.num_download_threads = 0

        self.download_times = collections.deque(maxlen=5)
        self.download_speed = 0
        self.previous_speed = 0

    def track_speed(self, time_elapsed):
        self.download_times.append(time_elapsed)
        time_elapsed = sum(self.download_times) / self.download_times.maxlen
        self.download_speed = round((self.block_size / time_elapsed), 2)

    def get_chunks(self, byte_from, byte_to):
        # Get a chunk from the server
        start = time.time()
        retries_left = GTL_RETRY_COUNT
        while True:
            if self.exception:
                self.num_download_threads -= 1
                return 0  # terminate thread
            try:
                r = requests.get(
                    self.source_url,
                    stream=True,
                    headers={"Range": "bytes=%s-%s" % (byte_from, byte_to)},
                    timeout=GTL_TIMEOUT,
                )
                if r.status_code == requests.codes.ok or r.status_code == 206:
                    # success
                    break
                else:
                    raise IOError("HTTP Error - status code: " + str(r.status_code))

            except IOError as exc:
                if retries_left:
                    retry_delay = GTL_RETRY_DELAY
                    retry_str = str(retries_left) + (
                        " retry left" if retries_left == 1 else " retries left"
                    )
                    logger.error(
                        "NVGTL is unreachable or returned HTTP error. Retrying after %d seconds for chunk %d "
                        "(%s) [%s] ..." % (retry_delay, byte_from, retry_str, exc)
                    )
                    time.sleep(retry_delay)
                    retries_left -= 1
                else:
                    self.exception = errors.PackmanError(
                        "NVGTL is unreachable. Retries exhausted. Is VPN disconnected or network down? (%s)"
                        % exc
                    )
                    self.num_download_threads -= 1
                    return  # terminate thread
            except BaseException as exc:
                self.exception = exc

        location = byte_from
        try:
            for chunk in r.iter_content(int(self.chunk_size)):
                self.chunks_to_write[location] = chunk
                location += len(chunk)
        except IOError:
            # we need to return the remaining range to the beginning of the fetch list:
            self.ranges_to_fetch.insert(0, (location, byte_to))
            # we swallow the exception here on purpose - we kill the thread and another attempt will be made to get
            # this range
            self.num_download_threads -= 1
            return
        except Exception as exc:
            self.exception = exc
            return
        end = time.time()
        self.track_speed(end - start)
        self.num_download_threads -= 1

    def generate_new_thread(self):
        # Generate a new thread complete with specified range of bytes
        if self.exception:
            return None

        if len(self.ranges_to_fetch) == 0:
            return None

        with self.lock:
            byte_from, byte_to = self.ranges_to_fetch.pop()
            self.num_download_threads += 1

        new_thread = threading.Thread(target=self.get_chunks, args=(byte_from, byte_to))
        new_thread.name = byte_from
        new_thread.daemon = True
        new_thread.start()
        return new_thread

    def write_chunks(self, target_file, source_size, progress):
        # First try to fill out the file to final size, this can raise so need to handle that:
        try:
            target_file.seek(source_size - 1)
            target_file.write(b"\0")
        except BaseException as exc:
            # propagate exception to all threads so they terminate
            self.exception = exc
            return  # terminate thread

        # Begin the loop to check for newly acquired chunks
        while self.progress < source_size - 1:
            if self.exception:
                return  # terminate thread
            if target_file.closed:
                return  # terminate thread; file has been closed outside thread (main thread most likely)
            if len(self.chunks_to_write) > 0:
                for x in list(self.chunks_to_write.keys()):
                    target_file.seek(x)
                    target_file.write(self.chunks_to_write[x])
                    target_file.flush()
                    os.fsync(target_file)

                    # Update the progress
                    progress(len(self.chunks_to_write[x]), self.max_download_threads)

                    self.progress += len(self.chunks_to_write[x])
                    self.chunks_to_write.pop(x)

            # Wait for a small bit for new chunks to be acquired
            time.sleep(0.5)

    def download(self, source_url, source_size, target_file, block_size=THREAD_BLOCK_SIZE):
        self.source_url = source_url
        self.source_size = source_size
        self.target_file = target_file
        self._set_block_size(block_size)

        self.exception = None
        self.num_download_threads = 0

        self.download_times.clear()

        # Setup a list of ranges to download
        self.ranges_to_fetch = []
        num_bytes_left = source_size
        while num_bytes_left:
            byte_end = num_bytes_left - 1  # because range is inclusive of both begin and end
            num_bytes_left -= self.block_size
            if num_bytes_left < 0:
                num_bytes_left = 0
            byte_begin = num_bytes_left
            self.ranges_to_fetch.append((byte_begin, byte_end))

        # Generate the initial download threads
        for x in range(self.max_download_threads):
            t = self.generate_new_thread()
            if not t:
                break

        msg_head = "Downloading from GTL: " + os.path.basename(target_file.name)
        with utils.ProgressPercentage(msg_head, source_size) as progress:
            try:
                # Startup the chunk writing thread
                writer = threading.Thread(
                    target=self.write_chunks,
                    args=(target_file, source_size, progress),
                    name="writer",
                )
                writer.daemon = True
                writer.start()

                while writer.is_alive():
                    add_threads = 0
                    available_chunks = len(self.ranges_to_fetch)
                    if available_chunks > 0:
                        available_threads = self.max_download_threads - self.num_download_threads
                        if available_chunks < available_threads:
                            add_threads = available_chunks
                        else:
                            add_threads = available_threads
                    while add_threads > 0:
                        self.generate_new_thread()
                        add_threads -= 1

                    time.sleep(0.1)

                    if self.smart_threading:
                        if (
                            self.previous_speed > self.download_speed * 1.25
                            and self.max_download_threads > 1
                        ):
                            self.max_download_threads -= 1
                        elif (
                            self.previous_speed * 0.95 < self.download_speed
                            and self.max_download_threads < 20
                        ):
                            self.max_download_threads += 1
                    self.previous_speed = self.download_speed
            except BaseException as exc:
                self.exception = exc

        if self.exception:
            logging.error("Terminating download threads ...")
            raise self.exception


class GtlTransport(basetransport.Transport):
    """
    A class to handle uploading and downloading of files to GTLFS.

    Note that any method, including instance construction can throw networking exceptions if problems arise during
    communication (no VPN connection, etc). It is the responsibility of the user to catch these exceptions, especially
    the socket.gaierror that indicates that the gtl_api is unreachable.
    """

    FILE_TYPE_ZIP = (
        8
    )  # This is taken from http://gtl-idl:8080/doc/namespace_n_v_i_d_i_a_1_1_g_t_l_1_1_file.html

    def __init__(self, username, key, gtl_api=GTL_API):
        self.netloc = "http://%s:%s@%s/GTLAPI" % (
            username,
            base64.b64decode(key).decode("utf8"),
            gtl_api,
        )
        self.debug = logger.isEnabledFor(logging.DEBUG)
        self.username = username
        self.user_id = None  # delay this so that init doesn't throw exceptions

    @_retry()
    def get_file_url_and_size(self, filename):
        """
        Returns a URL for anonymous download of 'filename' (valid for one hour)
        :param filename: The filename to search for (must be created by the user account associated with transport)
        :return: The URL of the filename in GTLFS if found, otherwise None.
        :rtype: str, long
        """
        logger.info("Resolving file '%s' to URL", filename)
        # initialize user_id if needed
        if self.user_id is None:
            self._get_user_id(self.username)
        logger.debug("Retrieving GUID for %s", filename)
        xml1 = """<Search type="file"><And><Like><Field name="Title"/><Value>"""
        xml2 = """</Value></Like><Equals><Field name="CreateUserId"/><Value>"""
        xml3 = """</Value></Equals></And></Search>"""
        command = xml1 + filename + xml2 + str(self.user_id) + xml3
        with xmlrpclib.ServerProxy(self.netloc + "/File_cgi.pl", verbose=self.debug) as server:
            guid = server.SearchFileIds(command)
            if not guid:
                logger.debug("GUID not found!")
                return None, None
            logger.debug("Retrieving URL for GUID %s", guid)
            link = server.GetFile(guid[0])
        url = link["URL"]
        size = int(link["Size"])
        logger.info("File '%s' of size %d bytes can be downloaded from %s", filename, size, url)
        return url, size

    @_retry()
    def is_file_found(self, filename):
        """
        Returns True if file with 'filename' is found on the remote server, otherwise False
        :param filename: The filename to search for (must be created by the user account associated with transport)
        :return: True or False
        :rtype: bool
        """
        logger.info("Searching on GTL for files with substring: '%s'", filename)
        # initialize user_id if needed
        if self.user_id is None:
            self._get_user_id(self.username)
        logger.debug("Retrieving GUID for %s", filename)
        xml1 = """<Search type="file"><And><Like><Field name="Title"/><Value>"""
        xml2 = """</Value></Like><Equals><Field name="CreateUserId"/><Value>"""
        xml3 = """</Value></Equals></And></Search>"""
        command = xml1 + filename + xml2 + str(self.user_id) + xml3
        with xmlrpclib.ServerProxy(self.netloc + "/File_cgi.pl", verbose=self.debug) as server:
            guid_list = server.SearchFileIds(command)
        if guid_list:
            logger.info("File(s) found")
            return True
        else:
            logger.debug('File "%s" not found', filename)
            return False

    @_retry()
    def list_files_starting_with(self, filename):
        """
        Returns a list of filenames that match the filename
        :param filename: The substring to search for (must be created by the user account associated with transport)
        :return: list of strings
        """
        logger.info("Searching on GTL for files starting with: '%s'", filename)
        # initialize user_id if needed
        if self.user_id is None:
            self._get_user_id(self.username)
        logger.debug("Retrieving GUID for %s", filename)
        xml1 = """<Search type="file"><And><Like><Field name="Title"/><Value>"""
        xml2 = """</Value></Like><Equals><Field name="CreateUserId"/><Value>"""
        xml3 = """</Value></Equals></And></Search>"""
        # Note: '%' is a wildcard in GTL search-speak
        command = xml1 + filename + "%" + xml2 + str(self.user_id) + xml3
        with xmlrpclib.ServerProxy(self.netloc + "/File_cgi.pl", verbose=self.debug) as server:
            guid_list = server.SearchFileIds(command)
            if not guid_list:
                logger.debug('File starting with "%s" not found on NVGTL!', filename)
                return None

            filename_list = []
            for guid in guid_list:
                file_info = server.GetFile(guid)
                filename_list.append(file_info["Title"])

        return filename_list

    @_retry()
    def create_file(self, filename):
        logger.info("Creating upload URL and GUID for file '%s'", filename)
        with xmlrpclib.ServerProxy(self.netloc + "/File_cgi.pl", verbose=self.debug) as server:
            response = server.CreatePermanentFile(
                {
                    "Type": GtlTransport.FILE_TYPE_ZIP,
                    "Title": filename,
                    "Description": "Package for packman",
                    "OriginalHost": socket.gethostname(),
                }
            )
        url = response["URL"]
        guid = response["Id"]
        logger.info('File "%s" can be uploaded to %s', filename, url)
        return url, guid

    @staticmethod
    @_retry()
    def upload_to_url(source_file_path, target_url, block_size=8192):
        """
        :type source_file_path: str
        :type target_url: str
        :type block_size: int
        """
        logger.info(
            "Uploading '%s' in blocks of %d bytes to %s", source_file_path, block_size, target_url
        )
        res = urlparse.urlparse(target_url)
        conn = httplib.HTTPConnection(res.netloc)
        conn.connect()
        conn.putrequest("POST", res.path + "?" + res.query)
        form = ("fname", {"filename": source_file_path})
        headers, data_begin, data_end = encode_multipart(form)
        if logger.isEnabledFor(logging.DEBUG):
            for k, v in list(headers.items()):
                logger.debug("%s : %s", k, v)
            logger.debug("Data begin section %s", data_begin)
            logger.debug("Data end section %s", data_end)
        conn.putheader("Connection", "close")
        for header, argument in list(headers.items()):
            conn.putheader(header, argument)
        conn.endheaders()
        conn.send(data_begin)
        file_size = os.path.getsize(source_file_path)
        msg_head = "Uploading to GTL: " + os.path.basename(source_file_path)
        with open(source_file_path, "rb") as source_file, utils.ProgressPercentage(
            msg_head, file_size
        ) as bar:
            while True:
                chunk = source_file.read(block_size)
                if not chunk:
                    break
                conn.send(chunk)
                bar(len(chunk))
            conn.send(data_end)
            response = conn.getresponse()
            if response.status != 200:
                raise Exception(
                    "HTTP status %d (%s). Error occurred during upload of '%s'"
                    % (response.status, response.msg, source_file_path)
                )

    @staticmethod
    @_retry()
    def download_from_url(source_url, source_size, target_file, block_size=8192):
        """
        :type source_url: str
        :type source_size: int
        :type target_file: file
        :type block_size: int
        """
        with urlopen(source_url, timeout=GTL_TIMEOUT) as result:
            msg_head = "Downloading from GTL: " + os.path.basename(target_file.name)
            with utils.ProgressPercentage(msg_head, source_size) as bar:
                while True:
                    chunk = result.read(block_size)
                    if not chunk:
                        break
                    target_file.write(chunk)
                    bar(len(chunk))

    @staticmethod
    def download_from_url_multithreaded(source_url, source_size, target_file):
        """
        :type source_url: str
        :type source_size: int
        :type target_file: file
        """
        acquire = ThreadedTransport(smart_threading=True)
        acquire.download(source_url, int(source_size), target_file)

    # Don't wrap high-level methods with retry decorator
    def upload_file(self, source_path, target_name, make_public=False):
        # GTL does not serve the public - it always requires authenticated access so we need to raise if people try it:
        if make_public:
            raise errors.PackmanError(
                "Files cannot be made public on GTL service - authenticated access is always "
                "required"
            )
        url, guid = self.create_file(target_name)
        self.upload_to_url(source_path, url)
        return guid

    def download_file(self, source_name, target_path):
        url, size = self.get_file_url_and_size(source_name)
        if url:
            with open(target_path, "wb") as target_file:
                if size > THREAD_BLOCK_SIZE:
                    download_method = self.download_from_url_multithreaded
                else:
                    download_method = self.download_from_url
                download_method(url, size, target_file)
        else:
            raise errors.PackmanError("File '%s' not found on GTL server!" % source_name)

    # Don't wrap internally called methods with retry decorator
    def _get_user_id(self, username):
        with xmlrpclib.ServerProxy(self.netloc + "/User_cgi.pl", verbose=self.debug) as server:
            self.user_id = server.GetUserIdFromLogin(username)
