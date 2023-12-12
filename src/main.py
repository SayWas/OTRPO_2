from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import httpx
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from fastapi_cache.backends.redis import RedisBackend
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from redis import asyncio as aioredis

from .auth.base_config import fastapi_users, auth_backend, current_user
from .auth.manager import google_oauth_client
from .auth.router import get_auth_router
from .auth.schemas import UserRead, UserCreate, UserUpdate
from .database import get_async_session
from .mail_service import send_logs_mail
from .manager import LogsManager
from .ftp_client import save_pokemon_md, FTPException

from .schemas import LogSchema, PokemonSchema
from .config import REDIS_HOST, REDIS_PORT, STATE_SECRET

app = FastAPI()

origins = [
    "http://127.0.0.1:6459",
    "http://127.0.0.1:8000",
    "http://localhost:5173",
    "http://localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PATCH', 'DELETE'],
    allow_headers=['Content-Type', 'Set-Cookie', 'Authorization', 'Access-Control-Allow-Origin',
                   'Access-Control-Allow-Headers', 'Access-Control-Allow-Credentials']
)


@app.on_event("startup")
async def startup_event():
    app.state.redis = aioredis.from_url(
        f"redis://{REDIS_HOST}:{REDIS_PORT}",
        encoding="utf-8",
        decode_responses=True
    )
    FastAPICache.init(RedisBackend(app.state.redis), prefix="fastapi-cache")
    app.include_router(
        get_auth_router(auth_backend, fastapi_users.get_user_manager, fastapi_users.authenticator, app.state.redis),
        prefix="/auth",
        tags=["Auth"],
    )


app.include_router(
    fastapi_users.get_oauth_router(google_oauth_client, auth_backend, STATE_SECRET,
                                   redirect_url="http://localhost:5173/auth/callback", associate_by_email=True),
    prefix="/auth/google",
    tags=["Auth Google"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Auth"],
)

app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["Auth"],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["Users"],
)


@app.post(
    "/send_mail",
    status_code=status.HTTP_200_OK,
    response_model=LogSchema)
async def send_mail(
        mail: EmailStr,
        log: LogSchema
):
    try:
        send_logs_mail(mail, log)
        return log
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post(
    "/add_to_db",
    status_code=status.HTTP_201_CREATED,
    response_model=LogSchema,
    dependencies=[Depends(current_user)]
)
async def add_to_db(
        log: LogSchema,
        user=Depends(current_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        await LogsManager(session).create_log(user.id, log.winner_id, log.loser_id, log.total_rounds)
        return log
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


security = HTTPBasic()


@app.post(
    "/save_pokemon",
    status_code=status.HTTP_201_CREATED,
    response_model=PokemonSchema,
    dependencies=[Depends(current_user)]
)
async def save_pokemon(
        pokemon: PokemonSchema,
        credentials: HTTPBasicCredentials = Depends(security)
):
    username = credentials.username
    password = credentials.password
    try:
        await save_pokemon_md(pokemon, username, password)
        return pokemon
    except FTPException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get(
    "/pokemon/{poke_name}",
    status_code=status.HTTP_200_OK,
    response_model=PokemonSchema)
@cache(expire=6000)
async def get_single_pokemon(
        poke_name: str
):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://pokeapi.co/api/v2/pokemon/{poke_name}")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pokemon not found")
        elif response.status_code != status.HTTP_200_OK:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid pokemon name")

        return PokemonSchema(**response.json())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@app.get(
    "/pokemons/",
    status_code=status.HTTP_200_OK)
@cache(expire=6000)
async def get_multiple_pokemons(
        limit: int = 20
):
    if limit < 1 or not isinstance(limit, int):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid limit value")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://pokeapi.co/api/v2/pokemon?limit={limit}")
        return response.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
