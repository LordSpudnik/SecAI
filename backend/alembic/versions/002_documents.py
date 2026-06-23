"""Add documents table

Revision ID: 002_documents
Revises: 001_initial
Create Date: 2025-01-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_documents"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


filetype_enum = postgresql.ENUM(
    "pdf",
    "docx",
    "xlsx",
    "txt",
    "csv",
    name="filetype",
    create_type=False,
)

processingstatus_enum = postgresql.ENUM(
    "queued",
    "processing",
    "ready",
    "failed",
    name="processingstatus",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type
                WHERE typname = 'filetype'
            ) THEN
                CREATE TYPE filetype AS ENUM (
                    'pdf',
                    'docx',
                    'xlsx',
                    'txt',
                    'csv'
                );
            END IF;
        END$$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type
                WHERE typname = 'processingstatus'
            ) THEN
                CREATE TYPE processingstatus AS ENUM (
                    'queued',
                    'processing',
                    'ready',
                    'failed'
                );
            END IF;
        END$$;
        """
    )

    op.create_table(
        "documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "filename",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "original_filename",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "file_type",
            filetype_enum,
            nullable=False,
        ),
        sa.Column(
            "file_size_mb",
            sa.Float,
            nullable=False,
        ),
        sa.Column(
            "file_path",
            sa.String(512),
            nullable=False,
        ),
        sa.Column(
            "chroma_collection",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "processing_status",
            processingstatus_enum,
            nullable=False,
            server_default=sa.text("'queued'"),
        ),
        sa.Column(
            "processing_error",
            sa.Text,
            nullable=True,
        ),
        sa.Column(
            "vector_count",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_documents_owner_id",
        "documents",
        ["owner_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_documents_owner_id",
        table_name="documents",
    )

    op.drop_table("documents")

    op.execute("DROP TYPE IF EXISTS processingstatus")

    op.execute("DROP TYPE IF EXISTS filetype")