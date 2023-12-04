import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .models import Logs


class SQLAlchemyLogsAdapter:
    session: AsyncSession

    def __init__(self,
                 session: AsyncSession,
                 ):
        self.session = session

    async def create_logs(self, user_id: uuid.UUID, winner_id: int, loser_id: int, total_rounds: int):
        logs = Logs(user_id=user_id, winner_id=winner_id, loser_id=loser_id, total_rounds=total_rounds)
        self.session.add(logs)
        await self.session.commit()
