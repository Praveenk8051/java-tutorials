import os
import logging
import webbrowser
from . import basetransport

import utils
from errors import PackmanError

__author__ = "hfannar"
__all__ = ["S3Transport", "AWS_REGION", "AWS_BUCKET"]


logger = logging.getLogger("packman.transport.s3")
AWS_REGION = "us-east-1"
AWS_BUCKET = "packman"


# S3 uses boto3 which has a bunch of dependencies - we add them here
utils.add_site_packages(
    (
        "boto3-1.9.214",
        "botocore-1.12.214",
        "six-1.12.0",
        "jmespath-0.9.4",
        "python_dateutil-2.8.0",
        "s3transfer-0.2.1",
        "urllib3-1.25.3",
    )
)
import boto3
import botocore


class S3Transport(basetransport.Transport):
    """
    :param access_key_pair: The AWS access key ID and secret access key pair as an iterable of 2
    """

    def __init__(self, access_key_pair, bucket_name=AWS_BUCKET, region=AWS_REGION, error_url=None):
        self.error_url = error_url
        self.bucket_name = bucket_name
        self.bucket = boto3.resource(
            "s3",
            region_name=region,
            aws_access_key_id=access_key_pair[0],
            aws_secret_access_key=access_key_pair[1],
        ).Bucket(self.bucket_name)

    def upload_file(self, source_file_path, target_name, make_public=False):
        try:
            msg = "Uploading to S3: " + target_name
            with utils.ProgressPercentage(
                msg, os.path.getsize(source_file_path), is_lock_required=True
            ) as progress:
                self.bucket.upload_file(source_file_path, target_name, Callback=progress)
        except botocore.exceptions.EndpointConnectionError:
            logger.error("S3 is unreachable! Is the network connection down?")
            raise PackmanError("Failed to upload file '%s'" % target_name)
        except boto3.exceptions.S3UploadFailedError as exc:
            if self.error_url:
                print("Redirecting to credentials error handling page:", self.error_url)
                webbrowser.open_new_tab(self.error_url)
            raise PackmanError(str(exc))

        if make_public:
            try:
                acl = self.bucket.Object(target_name).Acl()
                acl.put(ACL="public-read")
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as exc:
                raise PackmanError(
                    "Failed to make uploaded file '%s' public (%s)" % (target_name, exc)
                )

        return "s3:%s:%s" % (self.bucket_name, target_name)

    def download_file(self, source_name, target_file_path):
        try:
            size = self.bucket.Object(source_name).content_length
            with utils.ProgressPercentage(
                "Downloading from S3: " + source_name, size, is_lock_required=True
            ) as progress:
                self.bucket.download_file(source_name, target_file_path, Callback=progress)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as exc:
            if isinstance(exc, botocore.exceptions.ClientError):
                logger.error("Unable to access file on S3!")
            elif isinstance(exc, botocore.exceptions.EndpointConnectionError):
                logger.error("S3 is unreachable! Is the network connection down?")
            raise PackmanError("Failed to download file %s" % source_name)

    def list_files_starting_with(self, filename_part):
        # We must do this ourselves because search needs to be case insensitive (it is for GTL):
        filename_list = []
        filename_part_lower = filename_part.lower()
        try:
            if filename_part_lower:
                # if filename_part is specified we create a merged list of all items that start with
                # the first letter in upper and lower case, this massively reduces the keys to work with
                # and speeds up the query by order of magnitude
                items = self.bucket.objects.filter(Prefix=filename_part_lower[0].upper())
                for item in items:
                    if item.key.lower().startswith(filename_part_lower):
                        filename_list.append(item.key)
                items = self.bucket.objects.filter(Prefix=filename_part_lower[0])
                for item in items:
                    if item.key.lower().startswith(filename_part_lower):
                        filename_list.append(item.key)
            else:
                # no prefix specified so we list everything
                items = self.bucket.objects.all()
                for item in items:
                    filename_list.append(item.key)
        except botocore.exceptions.EndpointConnectionError:
            raise PackmanError("S3 is unreachable! Is the network connection down?")

        if not filename_list:
            logger.debug('File starting with "%s" not found on S3!', filename_part)
            return None

        return filename_list

    def is_file_found(self, filename):
        """
        Returns True if file with 'filename' is found on the remote server, otherwise False
        :param filename: The filename to search for
        :return: True or False
        :rtype: bool
        """
        logger.info('Searching on S3 for files with filename: "%s"', filename)
        try:
            object = self.bucket.Object(filename).content_length
            logger.info("File is found")
            return True
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as exc:
            if isinstance(exc, botocore.exceptions.EndpointConnectionError):
                logger.error("S3 is unreachable! Is network connection down?")
                raise PackmanError("Failed to check for presence of file %s" % filename)
            return False
