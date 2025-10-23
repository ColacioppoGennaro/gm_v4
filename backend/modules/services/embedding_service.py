"""
Embedding Service for Vector Search (RAG)
Handles document/event vectorization using Gemini Embedding API
"""

import google.generativeai as genai
import json
import numpy as np
from typing import List, Dict, Optional, Tuple
from config import Config
from modules.utils.database import db, generate_uuid
import logging

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=Config.GEMINI_API_KEY)

class EmbeddingService:
    """Service for creating and managing embeddings"""

    MODEL_NAME = "models/gemini-embedding-001"
    DIMENSION = 768  # Good balance between quality and performance

    @staticmethod
    def create_embedding(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """
        Create embedding vector for text

        Args:
            text: Input text to embed
            task_type: 'RETRIEVAL_DOCUMENT' or 'RETRIEVAL_QUERY'

        Returns:
            List of floats representing the embedding vector
        """
        try:
            result = genai.embed_content(
                model=EmbeddingService.MODEL_NAME,
                content=text,
                task_type=task_type,
                output_dimensionality=EmbeddingService.DIMENSION
            )

            # Normalize L2 for cosine similarity
            vector = np.array(result['embedding'])
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm

            return vector.tolist()

        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            raise

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity between two vectors (already normalized)"""
        return float(np.dot(vec_a, vec_b))

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Text to chunk
            chunk_size: Target words per chunk
            overlap: Overlapping words between chunks
        """
        words = text.split()
        chunks = []

        if len(words) <= chunk_size:
            return [text]

        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            if len(chunk_words) > 20:  # Minimum chunk size
                chunks.append(' '.join(chunk_words))

        return chunks

    @staticmethod
    def save_embedding(
        source_type: str,
        source_id: str,
        text: str,
        chunk_index: int = 0,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Save embedding to database

        Args:
            source_type: 'document', 'event', or 'conversation'
            source_id: ID of the source object
            text: Text content
            chunk_index: Index for chunked documents (0 for single embeddings)
            metadata: Additional metadata

        Returns:
            Embedding ID
        """
        try:
            # Create embedding
            vector = EmbeddingService.create_embedding(text, "RETRIEVAL_DOCUMENT")

            # Generate ID
            embedding_id = generate_uuid()

            # Prepare metadata
            if metadata is None:
                metadata = {}
            metadata['dimension'] = EmbeddingService.DIMENSION
            metadata['model'] = EmbeddingService.MODEL_NAME

            # Save to DB
            query = """
                INSERT INTO embeddings
                (id, source_type, source_id, chunk_index, text_content, embedding_vector, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            db.execute_query(
                query,
                (
                    embedding_id,
                    source_type,
                    source_id,
                    chunk_index,
                    text,
                    json.dumps(vector),
                    json.dumps(metadata)
                ),
                fetch_all=False
            )

            logger.info(f"Saved embedding {embedding_id} for {source_type}:{source_id}")
            return embedding_id

        except Exception as e:
            logger.error(f"Error saving embedding: {str(e)}")
            raise

    @staticmethod
    def vectorize_document(document_id: str, full_text: str, metadata: Optional[Dict] = None) -> int:
        """
        Vectorize entire document with chunking

        Returns:
            Number of chunks created
        """
        try:
            # Split into chunks
            chunks = EmbeddingService.chunk_text(full_text)

            # Save each chunk
            for i, chunk in enumerate(chunks):
                EmbeddingService.save_embedding(
                    source_type='document',
                    source_id=document_id,
                    text=chunk,
                    chunk_index=i,
                    metadata=metadata
                )

            logger.info(f"Vectorized document {document_id} into {len(chunks)} chunks")
            return len(chunks)

        except Exception as e:
            logger.error(f"Error vectorizing document: {str(e)}")
            raise

    @staticmethod
    def vectorize_event(event_id: str, event_data: Dict) -> str:
        """
        Vectorize event as single embedding
        Creates a summary text from event data

        Returns:
            Embedding ID
        """
        try:
            # Create searchable text from event
            parts = []

            if event_data.get('title'):
                parts.append(f"Titolo: {event_data['title']}")

            if event_data.get('description'):
                parts.append(f"Descrizione: {event_data['description']}")

            if event_data.get('location'):
                parts.append(f"Luogo: {event_data['location']}")

            if event_data.get('start_datetime'):
                parts.append(f"Data: {event_data['start_datetime']}")

            if event_data.get('category_name'):
                parts.append(f"Categoria: {event_data['category_name']}")

            text = ". ".join(parts)

            metadata = {
                'event_type': event_data.get('category_name'),
                'has_location': bool(event_data.get('location')),
                'has_amount': bool(event_data.get('amount'))
            }

            embedding_id = EmbeddingService.save_embedding(
                source_type='event',
                source_id=event_id,
                text=text,
                chunk_index=0,
                metadata=metadata
            )

            logger.info(f"Vectorized event {event_id}")
            return embedding_id

        except Exception as e:
            logger.error(f"Error vectorizing event: {str(e)}")
            raise

    @staticmethod
    def search(
        query: str,
        source_types: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search embeddings by query

        Args:
            query: Search query text
            source_types: Filter by source types (None = all)
            top_k: Number of results to return

        Returns:
            List of matches with scores
        """
        try:
            # Create query embedding
            query_vector = EmbeddingService.create_embedding(query, "RETRIEVAL_QUERY")

            # Get all embeddings (filter by type if specified)
            if source_types:
                placeholders = ','.join(['%s'] * len(source_types))
                where_clause = f"WHERE source_type IN ({placeholders})"
                params = source_types
            else:
                where_clause = ""
                params = []

            query_sql = f"""
                SELECT id, source_type, source_id, chunk_index, text_content,
                       embedding_vector, metadata
                FROM embeddings
                {where_clause}
            """

            results = db.execute_query(query_sql, params, fetch_all=True)

            # Calculate similarities
            matches = []
            for row in results:
                stored_vector = json.loads(row['embedding_vector'])
                similarity = EmbeddingService.cosine_similarity(query_vector, stored_vector)

                matches.append({
                    'id': row['id'],
                    'source_type': row['source_type'],
                    'source_id': row['source_id'],
                    'chunk_index': row['chunk_index'],
                    'text': row['text_content'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'score': similarity
                })

            # Sort by similarity and return top-k
            matches.sort(key=lambda x: x['score'], reverse=True)

            logger.info(f"Search query '{query}' returned {len(matches[:top_k])} results")
            return matches[:top_k]

        except Exception as e:
            logger.error(f"Error searching embeddings: {str(e)}")
            raise

    @staticmethod
    def delete_embeddings_for_source(source_id: str) -> int:
        """
        Delete all embeddings for a source

        Returns:
            Number of embeddings deleted
        """
        try:
            query = "DELETE FROM embeddings WHERE source_id = %s"
            count = db.execute_query(query, (source_id,), fetch_all=False)
            logger.info(f"Deleted {count} embeddings for source {source_id}")
            return count

        except Exception as e:
            logger.error(f"Error deleting embeddings: {str(e)}")
            raise
