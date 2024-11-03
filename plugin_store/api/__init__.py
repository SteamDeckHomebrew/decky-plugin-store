from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.utils import is_body_allowed_for_status_code

from .endpoints import announcements, index, plugins

app = FastAPI()

cors_origins = [
    "https://steamloopback.host",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: "Request", exc: "HTTPException") -> "Response":
    headers = getattr(exc, "headers", None)
    if not is_body_allowed_for_status_code(exc.status_code):
        return Response(status_code=exc.status_code, headers=headers)
    return JSONResponse(
        {"detail": exc.detail, "message": exc.detail},
        status_code=exc.status_code,
        headers=headers,
    )


app.include_router(index.router)
app.include_router(announcements.router)
app.include_router(plugins.router)
