from pydantic import BaseModel, Field
from typing import List, Optional


class Ability(BaseModel):
    name: str
    url: str


class AbilityItem(BaseModel):
    ability: Ability
    is_hidden: bool
    slot: int


class Form(BaseModel):
    name: str
    url: str


class Version(BaseModel):
    name: str
    url: str


class GameIndex(BaseModel):
    game_index: int
    version: Version


class Move(BaseModel):
    name: str
    url: str


class VersionGroup(BaseModel):
    name: str
    url: str


class MoveLearnMethod(BaseModel):
    name: str
    url: str


class VersionGroupDetail(BaseModel):
    level_learned_at: int
    move_learn_method: MoveLearnMethod
    version_group: VersionGroup


class Moves(BaseModel):
    move: Move
    version_group_details: List[VersionGroupDetail]


class Species(BaseModel):
    name: str
    url: str


class Sprites(BaseModel):
    front_default: Optional[str]
    front_shiny: Optional[str]


class Stat(BaseModel):
    name: str
    url: str


class Stats(BaseModel):
    base_stat: int
    effort: int
    stat: Stat


class Type(BaseModel):
    name: str
    url: str


class Types(BaseModel):
    slot: int
    type: Type


class PokemonSchema(BaseModel):
    abilities: List[AbilityItem]
    forms: List[Form]
    game_indices: List[GameIndex]
    height: int
    id: int
    moves: List[Moves]
    name: str
    order: int
    species: Species
    sprites: Sprites
    stats: List[Stats]
    types: List[Types]
    weight: int


class LogSchema(BaseModel):
    winner_id: int = Field(gt=0, description="The ID of the winner")
    loser_id: int = Field(gt=0, description="The ID of the loser")
    total_rounds: int = Field(gt=0, description="The total number of rounds")
