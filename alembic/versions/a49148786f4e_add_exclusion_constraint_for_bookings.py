"""Add exclusion constraint for bookings

Revision ID: a49148786f4e
Revises: e7db7c500609
Create Date: 2026-08-24 13:32:14.342196

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a49148786f4e'
down_revision: Union[str, Sequence[str], None] = 'e7db7c500609'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Вмикаємо розширення Postgres для роботи з діапазонами
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

    # 2. Додаємо саме обмеження через чистий SQL
    op.execute("""
        ALTER TABLE bookings 
        ADD CONSTRAINT exclude_overlapping_bookings 
        EXCLUDE USING gist (
            room_id WITH =, 
            daterange(check_in, check_out) WITH &&
        );
    """)


def downgrade() -> None:
    # Видаляємо обмеження, якщо доведеться відкочувати міграцію
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS exclude_overlapping_bookings;")