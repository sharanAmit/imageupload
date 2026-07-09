from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger("trip_memories")
logging.basicConfig(level=logging.INFO)

async def error_handling_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except RequestValidationError as exc:
        logger.error(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(), "message": "Validation failed"}
        )
    except SQLAlchemyError as exc:
        logger.error(f"Database error: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"message": "A database error occurred. Please try again."}
        )
    except Exception as exc:
        logger.error(f"Unhandled server error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"message": "An unexpected server error occurred."}
        )
