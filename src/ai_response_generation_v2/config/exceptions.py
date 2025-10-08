# app/common/exceptions.py
from __future__ import annotations
import structlog
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger("api")

def install_exception_middleware(app) -> None:
    @app.middleware("http")
    async def _exceptions_mw(request: Request, call_next):
        try:
            return await call_next(request)

        # Let explicit HTTPException bubble to FastAPI's handler
        except HTTPException:
            raise

        # Map common app exceptions to HTTP responses
        except PermissionError as exc:
            return JSONResponse(
                status_code=401,
                content={"detail": str(exc) or "Unauthorized"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"detail": str(exc) or "Bad Request"})

        # Fallback: log and hide details
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Unhandled server error",
                path=str(request.url),
                error=str(exc),
                exc_info=True,
            )
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
