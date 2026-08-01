from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationException
from app.database.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api", tags=["Authentication"])


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        service = AuthService(db)
        token_response = await service.authenticate(request.username, request.password)
        # Set cookie for dashboard
        response.set_cookie(
            key="access_token",
            value=token_response.access_token,
            httponly=True,
            max_age=86400,
            samesite="lax",
            secure=False,  # Set True in production with HTTPS
        )
        return token_response
    except AuthenticationException as e:
        raise HTTPException(status_code=401, detail=e.message)


@router.post("/auth/logout")
async def logout(response: Response) -> dict:
    response.delete_cookie("access_token")
    return {"message": "تم تسجيل الخروج بنجاح"}
