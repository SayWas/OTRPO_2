"""add_user_in_logs

Revision ID: 4939ee17c4eb
Revises: 6a84f5450941
Create Date: 2023-12-04 23:16:40.940878

"""
from typing import Sequence, Union

import fastapi_users_db_sqlalchemy
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4939ee17c4eb'
down_revision: Union[str, None] = '6a84f5450941'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('logs', sa.Column('user_id', fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False))
    op.create_foreign_key(None, 'logs', 'user', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'logs', type_='foreignkey')
    op.drop_column('logs', 'user_id')
    # ### end Alembic commands ###
