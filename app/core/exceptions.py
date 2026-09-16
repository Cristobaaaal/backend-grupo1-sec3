class APIException(Exception):
    def __init__(self, message: str, code: str, http_status: int, details: list | None = None):
        self.message = message
        self.code = code
        self.http_status = http_status
        self.details = details or []
        super().__init__(self.message)

class NotFoundException(APIException):
    def __init__(self, entity:str, entity_id):
        super().__init__(
        message= f"No existe un {entity} con el ID {entity_id}",
        code= "RESOURCE_NOT_FOUND",
        http_status= 404)

class ConflictError(APIException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="RESOURCE_CONFLICT",
            http_status=409)

class BusinessRuleError(APIException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="BUSINESS_RULE_VIOLATION",
            http_status=400)