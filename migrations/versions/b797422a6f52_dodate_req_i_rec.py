"""dodate req i rec.

Revision ID: b797422a6f52
Revises: d36b1abe990b
Create Date: 2023-06-05 18:14:26.899924

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b797422a6f52'
down_revision = 'd36b1abe990b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('productord', sa.Column('price', sa.Float(), nullable=False))
    op.add_column('productord', sa.Column('received', sa.Integer(), nullable=False))
    op.add_column('productord', sa.Column('requested', sa.Integer(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('productord', 'requested')
    op.drop_column('productord', 'received')
    op.drop_column('productord', 'price')
    # ### end Alembic commands ###
