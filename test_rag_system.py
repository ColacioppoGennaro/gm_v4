#!/usr/bin/env python3
"""
Test script for RAG (Retrieval Augmented Generation) system
Tests embedding service and vector search
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from modules.services.embedding_service import EmbeddingService
from modules.utils.database import db
import json

def test_embeddings():
    """Test embedding creation and search"""

    print("🧪 Testing RAG System...\n")

    # Test 1: Create embeddings for sample documents
    print("1️⃣ Creating sample document embeddings...")

    sample_docs = [
        {
            'id': 'test_doc_1',
            'text': 'Il paziente presenta valori di colesterolo totale 220 mg/dL, HDL 45 mg/dL, LDL 150 mg/dL.'
        },
        {
            'id': 'test_doc_2',
            'text': 'La piscina è aperta dal lunedì al venerdì dalle 9:00 alle 20:00, sabato dalle 9:00 alle 18:00.'
        },
        {
            'id': 'test_doc_3',
            'text': 'Appuntamento dal dentista il 25 ottobre 2025 alle ore 15:30 per controllo e pulizia.'
        }
    ]

    for doc in sample_docs:
        try:
            embedding_id = EmbeddingService.save_embedding(
                source_type='document',
                source_id=doc['id'],
                text=doc['text'],
                chunk_index=0
            )
            print(f"   ✅ Created embedding {embedding_id[:8]}... for {doc['id']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Test 2: Search with query
    print("\n2️⃣ Testing vector search...")

    queries = [
        "Quanto ho di colesterolo?",
        "Quando posso andare in piscina?",
        "Ho appuntamenti dal dentista?"
    ]

    for query in queries:
        print(f"\n   Query: '{query}'")
        try:
            results = EmbeddingService.search(query=query, top_k=2)

            if results:
                print(f"   Found {len(results)} matches:")
                for i, match in enumerate(results):
                    print(f"      [{i}] Score: {match['score']:.3f}")
                    print(f"          Text: {match['text'][:80]}...")
            else:
                print("   No results found")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Test 3: Test event vectorization
    print("\n3️⃣ Testing event vectorization...")

    sample_event = {
        'id': 'test_event_1',
        'data': {
            'title': 'Piscina',
            'description': 'Nuoto libero',
            'start_datetime': '2025-10-24 18:00:00',
            'location': 'Centro sportivo',
            'category_name': 'Sport'
        }
    }

    try:
        embedding_id = EmbeddingService.vectorize_event(
            event_id=sample_event['id'],
            event_data=sample_event['data']
        )
        print(f"   ✅ Created event embedding {embedding_id[:8]}...")

        # Search for it
        results = EmbeddingService.search("quando devo andare in piscina?", top_k=1)
        if results:
            print(f"   ✅ Found event with score {results[0]['score']:.3f}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Cleanup
    print("\n🧹 Cleaning up test data...")
    try:
        for doc in sample_docs:
            db.execute_query("DELETE FROM embeddings WHERE source_id = %s", (doc['id'],), fetch_all=False)
        db.execute_query("DELETE FROM embeddings WHERE source_id = %s", (sample_event['id'],), fetch_all=False)
        print("   ✅ Test data removed")
    except Exception as e:
        print(f"   ⚠️  Cleanup warning: {e}")

    print("\n✨ RAG System test completed!\n")

if __name__ == '__main__':
    try:
        test_embeddings()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
