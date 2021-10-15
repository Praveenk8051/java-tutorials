import logging
import xml.parsers.expat
import os

from errors import PackmanError


__author__ = "hfannar"
logger = logging.getLogger("packman.xmlparser")


class Element(object):
    TAG = "undefined"

    def __init__(self):
        self.attributes_required = list()
        self.attributes_optional = list()
        self._init()

    def _init(self):
        pass

    def start_handler(self, parse_helper, attribute_dict):
        pass

    def end_handler(self, parse_helper):
        pass

    def get_attribute_error(self, attribute_dict, error_on_unhandled_attributes=True):
        for required in self.attributes_required:
            if required not in attribute_dict:
                return "Attribute '%s' (required) on element '%s' is missing." % (
                    required,
                    self.TAG,
                )
            if not attribute_dict[required]:
                return "Attribute '%s' on element '%s' cannot be set to empty string." % (
                    required,
                    self.TAG,
                )

        if error_on_unhandled_attributes:
            for key in list(attribute_dict.keys()):
                if key not in self.attributes_required and key not in self.attributes_optional:
                    msg = "Attribute '%s' on element '%s' is not supported." % (key, self.TAG)
                    required_str = " ".join(self.attributes_required)
                    optional_str = " ".join(self.attributes_optional)
                    msg += " Supported attributes are: %s %s" % (required_str, optional_str)
                    return msg
        return None


class ParseHelper:
    def __init__(self, xml_parser, elements, namespace, fail_on_unhandled_data=True, filename=None):
        self.xml_parser = xml_parser
        self.elements = elements
        self.namespace = namespace
        self.fail_on_unhandled_data = fail_on_unhandled_data
        self.filename = filename
        cwd = os.getcwd()
        path = filename if filename else ""
        self.base_dir = os.path.dirname(os.path.abspath(os.path.join(cwd, path)))
        self.ignore_stack = (
            0
        )  # When non-zero we ignore elements until parsing brings this back to zero
        self.root_element = None
        self.element_name_stack = []

    def _skip_element(self, element_name):
        self._log_info(
            "Ignoring unrecognized element '%s' and everything it contains.", element_name
        )
        self.ignore_stack = 1

    def _create_log_message(self, msg, *args):
        line = "(line %d): " % self.xml_parser.CurrentLineNumber
        if self.filename:
            line = self.filename + line
        return line + (msg % args)

    def raise_error(self, msg, *args):
        raise PackmanError(self._create_log_message(msg, *args))

    def _log_info(self, msg, *args):
        logger.info(self._create_log_message(msg, *args))

    def resolve_env_vars(self, attributes):
        for key, value in list(attributes.items()):
            if value.startswith("$"):
                os_env_var = value[1:]
                try:
                    env_var_value = os.environ[os_env_var]
                except KeyError:
                    self.raise_error(
                        "Environment variable '%s' in project file not found in environment.",
                        os_env_var,
                    )
                else:
                    attributes[key] = env_var_value

    def resolve_path(self, path):
        if not os.path.isabs(path):
            abs_path = os.path.abspath(os.path.join(self.base_dir, path))
            logger.info("Resolving relative path '%s' => '%s'", path, abs_path)
            return abs_path
        else:
            return path

    def start_element(self, name, attributes):
        """
        :type name: unicode
        :type attributes: dict
        :rtype: None
        """
        self.element_name_stack.append(name)
        if self.ignore_stack:
            # We are in skip mode because of errors or future element this parser doesn't know what to do with
            self.ignore_stack += 1
            return

        try:
            element, schema_parent_name = self.elements[name]
        except KeyError:
            if self.fail_on_unhandled_data:
                self.raise_error("Unknown element '%s'", name)
            else:
                self._skip_element(name)
                return

        if schema_parent_name:
            self.ensure_element_inside_parent_element(name, schema_parent_name)
        else:
            parent_name = self.get_parent_element_name()
            if parent_name:
                self.raise_error("Element '%s' must be defined at the root of the document", name)

        error_msg = element.get_attribute_error(
            attributes, error_on_unhandled_attributes=self.fail_on_unhandled_data
        )
        if error_msg:
            self.raise_error(error_msg)
        element.start_handler(self, attributes)

    def end_element(self, name):
        self.element_name_stack.pop()
        if self.ignore_stack:
            self.ignore_stack -= 1
            return
        element = self.elements[name][0]
        element.end_handler(self)

    def get_parent_element_name(self):
        try:
            return self.element_name_stack[-2]
        except IndexError:
            return None

    def ensure_element_inside_parent_element(self, element_name, parent_element_name):
        if self.get_parent_element_name() != parent_element_name:
            self.raise_error(
                "Element '%s' defined outside '%s' element!", element_name, parent_element_name
            )


class BaseParser(object):
    def __init__(self, elements, namespace, fail_on_unhandled_data=True):
        self.elements = elements
        self.fail_on_unhandled_data = fail_on_unhandled_data
        self.namespace = namespace

    def parse_file(self, filename):
        """
        :type filename: str
        :rtype: Project
        """
        # Create handlers for the parser
        p = xml.parsers.expat.ParserCreate()
        handler = ParseHelper(
            p, self.elements, self.namespace, self.fail_on_unhandled_data, filename=filename
        )
        p.StartElementHandler = handler.start_element
        p.EndElementHandler = handler.end_element
        with open(filename, "rb") as fileobject:
            try:
                p.ParseFile(fileobject)
            except xml.parsers.expat.ExpatError as e:
                message = "%s: %s" % (filename, str(e))
                raise PackmanError(message)
        return handler.root_element

    def parse_data(self, data):
        """
        :type data: str
        :rtype: Project
        """
        # Create handlers for the parser
        p = xml.parsers.expat.ParserCreate()
        handler = ParseHelper(p, self.elements, self.namespace)
        p.StartElementHandler = handler.start_element
        p.EndElementHandler = handler.end_element
        p.Parse(data, True)
        return handler.root_element
