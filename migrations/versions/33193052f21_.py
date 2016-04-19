"""empty message

Revision ID: 33193052f21
Revises: 423081911c8e
Create Date: 2016-03-08 23:07:20.193665

"""

# revision identifiers, used by Alembic.
revision = '33193052f21'
down_revision = '423081911c8e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Token', sa.Column('is_loanword', sa.Boolean(), nullable=True))
    op.add_column('Token', sa.Column('fold', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Token', 'fold')
    op.drop_column('Token', 'is_loanword')
    ### end Alembic commands ###
