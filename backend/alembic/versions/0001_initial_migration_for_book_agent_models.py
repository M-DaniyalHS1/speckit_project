"""Initial migration for book agent models

Revision ID: 0001
Revises: 
Create Date: 2025-11-29 16:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=50), nullable=False),
        sa.Column('last_name', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('preferences', sa.Text(), nullable=True, default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create books table
    op.create_table(
        'books',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_format', sa.String(length=10), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('total_pages', sa.Integer(), nullable=True),
        sa.Column('is_processed', sa.Boolean(), nullable=True, default=False),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    
    # Create reading_sessions table
    op.create_table(
        'reading_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_location', sa.String(length=100), nullable=False),
        sa.Column('current_position_percent', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    
    # Create book_contents table
    op.create_table(
        'book_contents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_id', sa.String(length=100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section_title', sa.String(length=255), nullable=True),
        sa.Column('chapter', sa.String(length=100), nullable=True),
        sa.Column('embedding_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], )
    )
    
    # Create queries table
    op.create_table(
        'queries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_type', sa.String(length=50), nullable=False),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    
    # Create explanations table
    op.create_table(
        'explanations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('explanation_text', sa.Text(), nullable=False),
        sa.Column('complexity_level', sa.String(length=20), nullable=False),
        sa.Column('sources', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['content_id'], ['book_contents.id'], ),
        sa.ForeignKeyConstraint(['query_id'], ['queries.id'], )
    )
    
    # Create learning_materials table
    op.create_table(
        'learning_materials',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('additional_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    
    # Create indexes
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_index('ix_book_contents_embedding_id', 'book_contents', ['embedding_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_book_contents_embedding_id', table_name='book_contents')
    
    # Drop tables in reverse order to respect foreign key constraints
    op.drop_table('learning_materials')
    op.drop_table('explanations')
    op.drop_table('queries')
    op.drop_table('book_contents')
    op.drop_table('reading_sessions')
    op.drop_table('books')
    op.drop_table('users')