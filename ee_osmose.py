# Errors and Exceptions Osmate


class ParseError(Exception):
    def __init__(self, message):
        super(message)


class ConflictError(Exception):
    def __init__(self, message):
        super(message)


class MethodError(LookupError):
    def __init__(self, message):
        super(message)


class NoneFoundError(ValueError):
    def __init__(self, message):
        super(message)
