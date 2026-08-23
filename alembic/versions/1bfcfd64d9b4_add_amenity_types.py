"""Add amenity types

Revision ID: 1bfcfd64d9b4
Revises: d78901deaf11
Create Date: 2026-08-23 14:11:51.483155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1bfcfd64d9b4'
down_revision: Union[str, Sequence[str], None] = 'd78901deaf11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    amenity_enum = sa.Enum('PROPERTY', 'ROOM', 'BOTH', name='amenitytype')
    amenity_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('amenities', sa.Column('type', amenity_enum, server_default='BOTH', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('amenities', 'type')

    amenity_enum = sa.Enum('PROPERTY', 'ROOM', 'BOTH', name='amenitytype')
    amenity_enum.drop(op.get_bind(), checkfirst=True)
