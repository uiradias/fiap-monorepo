"""Add corpus_documents, corpus_chunks tables and pgvector index.

Revision ID: 0002_pgvector_corpus
Revises: 0001
Create Date: 2026-05-11
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "0002_pgvector_corpus"
down_revision = "0001"
branch_labels = None
depends_on = None

EMBEDDING_DIM = 1024  # voyage-3 default


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "corpus_documents",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("doc_id", sa.Text(), nullable=False, unique=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
    )

    op.create_table(
        "corpus_chunks",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "document_id", sa.BigInteger(),
            sa.ForeignKey("corpus_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "applies_to", sa.ARRAY(sa.Text()), nullable=False, server_default="{}",
        ),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.UniqueConstraint(
            "document_id", "chunk_index", name="uq_corpus_chunks_doc_idx",
        ),
    )

    op.execute(
        "CREATE INDEX corpus_chunks_embedding_hnsw "
        "ON corpus_chunks USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX corpus_chunks_applies_to_gin "
        "ON corpus_chunks USING gin (applies_to)"
    )


def downgrade() -> None:
    op.drop_index("corpus_chunks_applies_to_gin", table_name="corpus_chunks")
    op.drop_index("corpus_chunks_embedding_hnsw", table_name="corpus_chunks")
    op.drop_table("corpus_chunks")
    op.drop_table("corpus_documents")
    # leave the vector extension installed
