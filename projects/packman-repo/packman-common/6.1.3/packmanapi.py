# This file contains the interfaces that external Python scripts can use.
# Import this file and use the APIs exposed below.  For example:
#
# import sys
# import os
# sys.path.insert(0, os.environ['PM_packman_common_PATH']
# import packmanapi
# packmanapi.pack(version_path)
#
# The above example assumes that the environment variable has been set in the process, which is true
# if the appropriate packman common module was installed/pulled prior to running the script.

# To get documentation on these methods import this file into a Python interpreter and run help on them, like this:
# help(packmanapi.pack)
from packman import pack

from schemaparser import Remote

from packman import list_remote

from packman import push
from packman import push_to_remote

from packman import publish
from packman import publish_to_remote

from packman import pull

from packman import install

from packman import hash

from packman import link
from packman import unlink

from packman import VERBOSITY_LOW
from packman import VERBOSITY_NORMAL
from packman import VERBOSITY_HIGH
from packman import set_verbosity_level

from packman import CONSOLE_ENCODING

from project import create_project
from project import add_dependency
from project import remove_dependency
from project import add_package

from packager import create_package
from packager import get_package_zip_filename
from packager import create_package_from_file_list
from utils import create_file_list_from_pattern

# Get the version to allow people to check what version of packman they are using.
from version import PRODUCT_VERSION

# Expose the exception types via the packmanapi so that users of the above functions can catch them and take appropriate
# action
from errors import *

from packman import read_configuration as _read_configuration

_read_configuration()
