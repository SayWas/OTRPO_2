from threading import Thread
from typing import Tuple

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm

from fastapi_users import models
from fastapi_users.authentication import AuthenticationBackend, Authenticator, Strategy
from fastapi_users.manager import BaseUserManager, UserManagerDependency
from fastapi_users.openapi import OpenAPIResponseType
from fastapi_users.router.common import ErrorCode, ErrorModel
from starlette.responses import JSONResponse

from .two_f_a import generate_otp, set_otp_to_redis, verify_otp_from_redis
from .common import ErrorCode as AuthErrorCode

from ..mail_service import send_otp_mail


def get_auth_router(
        backend: AuthenticationBackend,
        get_user_manager: UserManagerDependency[models.UP, models.ID],
        authenticator: Authenticator,
        redis,
        requires_verification: bool = False,
) -> APIRouter:
    """Generate a router with login/logout routes for an authentication backend."""
    router = APIRouter()
    get_current_user_token = authenticator.current_user_token(
        active=True, verified=requires_verification
    )

    login_responses: OpenAPIResponseType = {
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        ErrorCode.LOGIN_BAD_CREDENTIALS: {
                            "summary": "Bad credentials or the user is inactive.",
                            "value": {"detail": ErrorCode.LOGIN_BAD_CREDENTIALS},
                        },
                        ErrorCode.LOGIN_USER_NOT_VERIFIED: {
                            "summary": "The user is not verified.",
                            "value": {"detail": ErrorCode.LOGIN_USER_NOT_VERIFIED},
                        },
                    }
                }
            },
        },
        status.HTTP_202_ACCEPTED: {
            "model": ErrorModel,
            "description": "2FA verification required.",
            "content": {
                "application/json": {
                    "examples": {
                        "2fa_required": {
                            "summary": "2FA verification required.",
                            "value": {"message": "2FA verification required", "user_id": "UUID пользователя"},
                        }
                    }
                }
            },
        },
        **backend.transport.get_openapi_login_responses_success(),
    }

    @router.post(
        "/login",
        name=f"auth:{backend.name}.login",
        responses=login_responses,
    )
    async def login(
            # request: Request,
            credentials: OAuth2PasswordRequestForm = Depends(),
            user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
            # strategy: Strategy[models.UP, models.ID] = Depends(backend.get_strategy),
    ):
        user = await user_manager.authenticate(credentials)

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
            )
        if requires_verification and not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.LOGIN_USER_NOT_VERIFIED,
            )
        otp = generate_otp()
        Thread(target=send_otp_mail, args=(user.email, otp)).start()
        await set_otp_to_redis(user.id, otp, redis)

        return JSONResponse(content={"message": "2FA verification required"}, status_code=status.HTTP_202_ACCEPTED)

    verify_otp_responses: OpenAPIResponseType = {
        status.HTTP_204_NO_CONTENT: {
            "description": "Successful 2FA Verification."
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorModel,
            "description": "Invalid OTP or User Details.",
            "content": {
                "application/json": {
                    "examples": {
                        AuthErrorCode.VERIFY_OTP_BAD_CREDENTIALS: {
                            "summary": "Invalid OTP.",
                            "value": {"detail": AuthErrorCode.VERIFY_OTP_BAD_CREDENTIALS},
                        },
                        AuthErrorCode.VERIFY_OTP_USER_NOT_FOUND: {
                            "summary": "User not found or not active.",
                            "value": {"detail": AuthErrorCode.VERIFY_OTP_USER_NOT_FOUND},
                        },
                    }
                }
            },
        },
    }

    @router.post("/verify-otp", responses=verify_otp_responses)
    async def verify_otp(
            otp: str = Form(...),
            credentials: OAuth2PasswordRequestForm = Depends(),
            user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
            strategy: Strategy[models.UP, models.ID] = Depends(backend.get_strategy),
    ):
        user = await user_manager.authenticate(credentials)
        if not await verify_otp_from_redis(user.id, otp, redis):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found or not active")

        response = await backend.login(strategy, user)
        await user_manager.on_after_login(user, None, response)
        return response

    logout_responses: OpenAPIResponseType = {
        **{
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user."
            }
        },
        **backend.transport.get_openapi_logout_responses_success(),
    }

    @router.post(
        "/logout", name=f"auth:{backend.name}.logout", responses=logout_responses
    )
    async def logout(
            user_token: Tuple[models.UP, str] = Depends(get_current_user_token),
            strategy: Strategy[models.UP, models.ID] = Depends(backend.get_strategy),
    ):
        user, token = user_token
        return await backend.logout(strategy, user, token)

    return router
