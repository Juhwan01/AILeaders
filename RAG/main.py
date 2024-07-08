import logging
import traceback
from urllib.request import Request

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from dependencies.database import init_db
from dependencies.config import get_config

from routers import router as main_router

init_db(config=get_config())

app = FastAPI(
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)


app.include_router(router=main_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)


async def add_cors_to_response(
    request: Request, response: JSONResponse
) -> JSONResponse:
    origin = request.headers.get("origin")

    # Set CORS CORS header.
    if origin:
        cors = CORSMiddleware(
            app=app,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        response.headers.update(cors.simple_headers)
        has_cookie = "cookie" in request.headers

        # Allow Origin header if CORS is allowed.
        if cors.allow_all_origins and has_cookie:
            response.headers["Access-Control-Allow-Origin"] = origin
        elif not cors.allow_all_origins and cors.is_allowed_origin(
            origin=origin,
        ):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers.add_vary_header("Origin")
    return response


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logging.error(traceback.format_exc())
    response = JSONResponse(status_code=500, content={"context": exc})
    return await add_cors_to_response(request=request, response=response)
