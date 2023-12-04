import os
import re
from datetime import datetime
import aiofiles
import aioftp
from .config import FTP_HOST, FTP_PORT
from .schemas import PokemonSchema


class FTPException(Exception):
    pass


async def save_pokemon_md(pokemon: PokemonSchema, ftp_username: str, ftp_password: str):
    markdown = f"# {pokemon.name}\n\n- Height: {pokemon.height}\n- Weight: {pokemon.weight}\n- Abilities: {', '.join([ability.ability.name for ability in pokemon.abilities])}"
    safe_name = re.sub(r'\W+', '_', pokemon.name)
    filename = f"{safe_name}.md"
    local_filepath = filename

    async with aiofiles.open(local_filepath, 'w') as f:
        await f.write(markdown)

    try:
        client = aioftp.Client()
        await client.connect(FTP_HOST, port=FTP_PORT)
        await client.login(ftp_username, ftp_password)
        date_dir = datetime.now().strftime('%Y%m%d')
        await client.make_directory(date_dir)

        remote_filepath = os.path.join(date_dir, filename)
        await client.upload(local_filepath, remote_filepath)
        await client.quit()
    except Exception as e:
        raise FTPException(f"Failed to store file on FTP server: {e}")
    finally:
        if os.path.isfile(local_filepath):
            os.remove(local_filepath)