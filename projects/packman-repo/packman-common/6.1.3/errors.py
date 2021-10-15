# Use these for throwing exceptions that should be reported as errors to the user (when using command line version)
# or handled by the programmer (when using packmanapi)


class PackmanError(Exception):
    pass


class PackmanErrorFileExists(PackmanError):
    pass


class PackmanErrorScriptFailure(PackmanError):
    def __init__(self, script_name: str, error_code: int):
        PackmanError.__init__(
            self, "Script '%s' returned error code %d" % (script_name, error_code)
        )
        self.error_code = error_code
