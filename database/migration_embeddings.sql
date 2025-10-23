-- Migration: Add embeddings table for vector search (RAG)
-- Created: 2025-10-23

CREATE TABLE IF NOT EXISTS embeddings (
    id CHAR(36) PRIMARY KEY,
    source_type ENUM('document', 'event', 'conversation') NOT NULL,
    source_id CHAR(36) NOT NULL,
    chunk_index INT DEFAULT 0,
    text_content TEXT NOT NULL,
    embedding_vector JSON NOT NULL,
    metadata JSON DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_source (source_type, source_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add vector dimension to metadata for faster filtering
-- Store as: {"dimension": 768, "model": "gemini-embedding-001", "custom": {...}}
