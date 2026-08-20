from fastapi import Request, status
from fastapi.responses import JSONResponse
from supabase import AuthApiError

from database import supabase

PUBLIC_PATHS = {
    "/",
    "/health",
    "/public/info",
    "/auth/signup",
    "/auth/login",
    "/docs",
    "/redoc",
    "/openapi.json",
}


async def auth_middleware(request: Request, call_next):
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Access token required"},
        )

    token = auth_header.split(" ", 1)[1].strip()

    try:
        response = supabase.auth.get_user(token)
        request.state.user = response.user
    except AuthApiError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Invalid or expired token"},
        )

    return await call_next(request)
