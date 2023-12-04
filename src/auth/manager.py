import re
import uuid
from threading import Thread
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin, exceptions, models, schemas
from httpx_oauth.clients.google import GoogleOAuth2

from ..mail_service import send_reset_password_mail
from .utils import get_user_db
from ..config import RESET_SECRET, VERIFICATION_SECRET, CLIENT_ID, CLIENT_SECRET
from ..models import User

google_oauth_client = GoogleOAuth2(CLIENT_ID, CLIENT_SECRET)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = RESET_SECRET
    verification_token_secret = VERIFICATION_SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(self, user: User, token: str, request: Optional[Request] = None):
        print(f"User {user.id} has forgot their password. Reset token: {token}")
        Thread(target=send_reset_password_mail, args=(user.email, token)).start()

    async def on_after_reset_password(
            self, user: models.UP, request: Optional[Request] = None
    ) -> None:
        print("reset")

    async def validate_password(self, password: str, user: models.UP):
        if len(password) < 8:
            raise exceptions.InvalidPasswordException(
                reason="Password should be at least 8 characters"
            )
        if len(password) > 1024:
            raise exceptions.InvalidPasswordException(
                reason="Password is too long"
            )
        if re.match("^.*(?=.*[a-zA-Z])(?=.*\d)(?=.*[!#$%&?]).*$", password) is None:
            raise exceptions.InvalidPasswordException(
                reason="Password should contain at least one letter, one number and one special character"
            )

    async def create(
            self,
            user_create: schemas.UC,
            safe: bool = False,
            request: Optional[Request] = None,
    ) -> models.UP:
        await self.validate_password(user_create.password, user_create)

        existing_user = await self.user_db.get_by_email(user_create.email)
        if existing_user is not None:
            raise exceptions.UserAlreadyExists()

        user_dict = (
            user_create.create_update_dict()
            if safe
            else user_create.create_update_dict_superuser()
        )
        password = user_dict.pop("password")
        user_dict["hashed_password"] = self.password_helper.hash(password)
        user_dict["role_id"] = 1

        created_user = await self.user_db.create(user_dict)

        await self.on_after_register(created_user, request)

        return created_user

    async def oauth_callback(
            self: "BaseUserManager[models.UOAP, models.ID]",
            oauth_name: str,
            access_token: str,
            account_id: str,
            account_email: str,
            expires_at: Optional[int] = None,
            refresh_token: Optional[str] = None,
            request: Optional[Request] = None,
            *,
            associate_by_email: bool = False,
            is_verified_by_default: bool = False,
    ) -> models.UOAP:
        oauth_account_dict = {
            "oauth_name": oauth_name,
            "access_token": access_token,
            "account_id": account_id,
            "account_email": account_email,
            "expires_at": expires_at,
            "refresh_token": refresh_token,
        }

        try:
            user = await self.get_by_oauth_account(oauth_name, account_id)
        except exceptions.UserNotExists:
            try:
                # Associate account
                user = await self.get_by_email(account_email)
                if not associate_by_email:
                    raise exceptions.UserAlreadyExists()
                user = await self.user_db.add_oauth_account(user, oauth_account_dict)
            except exceptions.UserNotExists:
                # Create account
                password = self.password_helper.generate()
                user_dict = {
                    "email": account_email,
                    "hashed_password": self.password_helper.hash(password),
                    "is_verified": is_verified_by_default,
                    "role_id": 1,
                }
                user = await self.user_db.create(user_dict)
                user = await self.user_db.add_oauth_account(user, oauth_account_dict)
                await self.on_after_register(user, request)
        else:
            # Update oauth
            for existing_oauth_account in user.oauth_accounts:
                if (
                        existing_oauth_account.account_id == account_id
                        and existing_oauth_account.oauth_name == oauth_name
                ):
                    user = await self.user_db.update_oauth_account(
                        user, existing_oauth_account, oauth_account_dict
                    )

        return user


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
