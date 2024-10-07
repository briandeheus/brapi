class APIException(Exception):
    def __init__(self, code, message=None, status_code=None):
        self.code = code
        self.message = message
        self.status_code = status_code
