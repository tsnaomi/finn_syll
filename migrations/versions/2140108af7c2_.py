"""empty message

Revision ID: 2140108af7c2
Revises: 2d0c74a4c04c
Create Date: 2015-05-03 18:45:22.072672

"""

# revision identifiers, used by Alembic.
revision = '2140108af7c2'
down_revision = '2d0c74a4c04c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Token', sa.Column('rules', sa.String(length=80, convert_unicode=True), nullable=True))
    op.drop_column('Token', 'applied_rules')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Token', sa.Column('applied_rules', sa.VARCHAR(length=80), autoincrement=False, nullable=True))
    op.drop_column('Token', 'rules')
    ### end Alembic commands ###
