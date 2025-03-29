"""Initial migration

Revision ID: 1a2b3c4d5e6f
Revises:
Create Date: 2023-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create pdf_documents table
    op.create_table(
        'pdf_documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create text_contents table
    op.create_table(
        'text_contents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['pdf_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create images table
    op.create_table(
        'images',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('image_index', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['pdf_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create tables table
    op.create_table(
        'tables',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('table_index', sa.Integer(), nullable=False),
        sa.Column('table_data', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['pdf_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Add indexes
    op.create_index(op.f('ix_pdf_documents_created_at'), 'pdf_documents', ['created_at'], unique=False)
    op.create_index(op.f('ix_text_contents_document_id'), 'text_contents', ['document_id'], unique=False)
    op.create_index(op.f('ix_images_document_id'), 'images', ['document_id'], unique=False)
    op.create_index(op.f('ix_tables_document_id'), 'tables', ['document_id'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_tables_document_id'), table_name='tables')
    op.drop_index(op.f('ix_images_document_id'), table_name='images')
    op.drop_index(op.f('ix_text_contents_document_id'), table_name='text_contents')
    op.drop_index(op.f('ix_pdf_documents_created_at'), table_name='pdf_documents')

    # Drop tables
    op.drop_table('tables')
    op.drop_table('images')
    op.drop_table('text_contents')
    op.drop_table('pdf_documents')