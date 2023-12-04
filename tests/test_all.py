import pytest
from httpx import AsyncClient
from starlette.status import HTTP_200_OK, HTTP_422_UNPROCESSABLE_ENTITY, HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR
from unittest.mock import patch,  AsyncMock

from sqlalchemy import select

from conftest import async_session_maker
from src.ftp_client import FTPException
from src.models import Logs
from src.schemas import LogSchema, PokemonSchema


@pytest.mark.parametrize("mail, winner_id, loser_id, total_rounds, expected_status", [
    ("thenorthlord@yandex.ru", 1, 2, 3, HTTP_200_OK),  # Valid data
    ("test@example.com", 0, 2, 3, HTTP_422_UNPROCESSABLE_ENTITY),  # Invalid winner_id
    ("test@example.com", 1, 0, 3, HTTP_422_UNPROCESSABLE_ENTITY),  # Invalid loser_id
    ("test@example.com", 1, 2, 0, HTTP_422_UNPROCESSABLE_ENTITY),  # Invalid total_rounds
    ("invalidemail", 1, 2, 3, HTTP_422_UNPROCESSABLE_ENTITY),  # Invalid email
])
@patch('src.main.send_logs_mail')
async def test_send_mail(mock_send_logs_mail, ac: AsyncClient, mail, winner_id, loser_id, total_rounds,
                         expected_status):
    log_data = {"winner_id": winner_id, "loser_id": loser_id, "total_rounds": total_rounds}
    response = await ac.post("/send_mail", params={"mail": mail}, json=log_data)

    assert response.status_code == expected_status, f"Expected status code {expected_status}, but got {response.status_code}"
    if expected_status == HTTP_200_OK:
        log_data = LogSchema(winner_id=winner_id, loser_id=loser_id, total_rounds=total_rounds)
        call_args = mock_send_logs_mail.call_args
        assert call_args[0][0] == mail, f"Expected mail {mail}, but got {call_args[0][0]}"
        assert call_args[0][1].winner_id == log_data.winner_id, f"Expected winner_id {log_data.winner_id}, but got {call_args[0][1].winner_id}"
        assert call_args[0][1].loser_id == log_data.loser_id, f"Expected loser_id {log_data.loser_id}, but got {call_args[0][1].loser_id}"
        assert call_args[0][1].total_rounds == log_data.total_rounds, f"Expected total_rounds {log_data.total_rounds}, but got {call_args[0][1].total_rounds}"
    else:
        mock_send_logs_mail.assert_not_called()


@pytest.mark.parametrize("winner_id, loser_id, total_rounds, expected_status", [
    (1, 2, 5, HTTP_201_CREATED),  # valid case
    (0, 2, 5, HTTP_422_UNPROCESSABLE_ENTITY),  # invalid winner_id
    (1, 0, 5, HTTP_422_UNPROCESSABLE_ENTITY),  # invalid loser_id
    (1, 2, 0, HTTP_422_UNPROCESSABLE_ENTITY),  # invalid total_rounds
])
async def test_add_to_db(ac: AsyncClient, winner_id, loser_id, total_rounds, expected_status):
    log_data = {"winner_id": winner_id, "loser_id": loser_id, "total_rounds": total_rounds}
    response = await ac.post("/add_to_db", json=log_data)

    assert response.status_code == expected_status, f"Expected status code {expected_status}, but got {response.status_code}"
    if expected_status == HTTP_201_CREATED:
        assert response.json() == log_data
        async with async_session_maker() as session:
            stmt = select(Logs).where(Logs.winner_id == winner_id, Logs.loser_id == loser_id, Logs.total_rounds == total_rounds)
            result = await session.execute(stmt)
            record = result.fetchone()
            assert record is not None, "Record not found in the database"
    else:
        async with async_session_maker() as session:
            stmt = select(Logs).where(Logs.winner_id == winner_id, Logs.loser_id == loser_id, Logs.total_rounds == total_rounds)
            result = await session.execute(stmt)
            record = result.fetchone()
            assert record is None, "Record found in the database"


@pytest.mark.parametrize("mock_return_value, expected_status", [
    (None, HTTP_201_CREATED),
    (FTPException(), HTTP_500_INTERNAL_SERVER_ERROR),
    (Exception(), HTTP_500_INTERNAL_SERVER_ERROR),
])
@patch("src.main.save_pokemon_md", new_callable=AsyncMock)
async def test_save_pokemon(mock_save_pokemon_md, ac: AsyncClient, mock_return_value, expected_status: int):
    pokemon_data = {
        "abilities": [{"ability": {"name": "test", "url": "test"}, "is_hidden": False, "slot": 1}],
        "forms": [{"name": "test", "url": "test"}],
        "game_indices": [{"game_index": 1, "version": {"name": "test", "url": "test"}}],
        "height": 7,
        "id": 1,
        "moves": [{"move": {"name": "test", "url": "test"}, "version_group_details": [{"level_learned_at": 1, "move_learn_method": {"name": "test", "url": "test"}, "version_group": {"name": "test", "url": "test"}}]}],
        "name": "pikachu",
        "order": 1,
        "species": {"name": "pikachu", "url": "http://example.com"},
        "sprites": {"front_default": "test", "front_shiny": "test"},
        "stats": [{"base_stat": 1, "effort": 1, "stat": {"name": "test", "url": "test"}}],
        "types": [{"slot": 1, "type": {"name": "test", "url": "test"}}],
        "weight": 6
    }

    if mock_return_value is not None:
        pokemon_data["name"] = "invalid#pokemon"

    mock_save_pokemon_md.side_effect = mock_return_value

    response = await ac.post(
        "/save_pokemon",
        json=pokemon_data,
        auth=("username", "password")
    )
    assert response.status_code == expected_status

    if expected_status == HTTP_201_CREATED:
        pokemon = PokemonSchema(**response.json())
        assert pokemon.name == pokemon_data["name"]

    mock_save_pokemon_md.assert_called_once()
    args, _ = mock_save_pokemon_md.call_args
    assert args[0].model_dump() == pokemon_data
    assert args[1] == "username"
    assert args[2] == "password"

    if expected_status != HTTP_201_CREATED:
        assert isinstance(mock_save_pokemon_md.side_effect, Exception)


@pytest.mark.parametrize("poke_name, expected_status", [
    ("pikachu", HTTP_200_OK),
    ("charizard", HTTP_200_OK),
    ("nonexistentpokemon", HTTP_404_NOT_FOUND)
])
async def test_get_single_pokemon(ac: AsyncClient, poke_name: str, expected_status: int):
    response = await ac.get(f"/pokemon/{poke_name}")
    assert response.status_code == expected_status

    if expected_status == HTTP_200_OK:
        assert "name" in response.json()
        assert response.json()["name"] == poke_name


@pytest.mark.parametrize("limit, expected_status", [
    (5, HTTP_200_OK),
    (10, HTTP_200_OK),
    (15, HTTP_200_OK),
    (-1, HTTP_422_UNPROCESSABLE_ENTITY),
    ("invalid", HTTP_422_UNPROCESSABLE_ENTITY),
])
async def test_get_multiple_pokemons(ac: AsyncClient, limit: str, expected_status: int):
    response = await ac.get(f"/pokemons/?limit={limit}")
    assert response.status_code == expected_status

    if expected_status == HTTP_200_OK:
        assert len(response.json()["results"]) <= int(limit)
