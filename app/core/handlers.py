from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import APIException
from fastapi.responses import JSONResponse

def _error_body(code:str, message:str, details:list):
    return {"error":
    {"code": code,
    "message": message,
    "details": details}}

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        return JSONResponse(
            status_code=exc.http_status,
            content=_error_body(exc.code, exc.message, exc.details))


    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        detalles = [
            {"campo": ".".join(str(x) for x in e["loc"]), "error": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_error_body("VALIDATION_ERROR", "Los datos enviados no son válidos", detalles),
        )


    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body("HTTP_ERROR", exc.detail, []),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=_error_body("INTERNAL_SERVER_ERROR", "Ocurrió un error interno en el servidor", []),
        )