"""Add shipping fields to orders table

Revision ID: add_shipping_fields
Revises:
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_shipping_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add shipping fields to orders table
    op.add_column('orders', sa.Column('shipping_method', sa.String(100), default='Giao hàng tiêu chuẩn'))
    op.add_column('orders', sa.Column('shipping_fee', sa.Numeric(10, 2), default=30000))
    op.add_column('orders', sa.Column('estimated_delivery', sa.DateTime()))
    op.add_column('orders', sa.Column('shipped_at', sa.DateTime()))
    op.add_column('orders', sa.Column('delivered_at', sa.DateTime()))
    op.add_column('orders', sa.Column('tracking_number', sa.String(100)))
    op.add_column('orders', sa.Column('shipping_notes', sa.Text()))


def downgrade():
    # Remove shipping fields from orders table
    op.drop_column('orders', 'shipping_notes')
    op.drop_column('orders', 'tracking_number')
    op.drop_column('orders', 'delivered_at')
    op.drop_column('orders', 'shipped_at')
    op.drop_column('orders', 'estimated_delivery')
    op.add_column('orders', sa.Column('shipping_fee', sa.Numeric(10, 2)))
    op.drop_column('orders', 'shipping_method')
