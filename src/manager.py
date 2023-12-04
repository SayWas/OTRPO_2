import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .adapter import SQLAlchemyLogsAdapter


class LogsManager:
    def __init__(self,
                 session: AsyncSession
                 ):
        self.db_adapter = SQLAlchemyLogsAdapter(session=session)

    async def create_log(
            self,
            user_id: uuid.UUID,
            winner_id: int,
            loser_id: int,
            total_rounds: int
    ):
        return await self.db_adapter.create_logs(user_id, winner_id, loser_id, total_rounds)