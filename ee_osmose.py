# Errors and Exceptions Osmate


class ParseError(Exception):
    def __init__(self, message):
        self.message = message


class ConflictError(Exception):
    def __init__(self, message):
        self.message = message


class MethodError(LookupError):
    def __init__(self, message):
        self.message = message


class NoneFoundError(ValueError):
    def __init__(self, message):
        self.message = message
