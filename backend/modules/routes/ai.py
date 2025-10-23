"""
AI Service Routes - Gemini Integration
Handles AI-powered features using server-side Gemini API key
"""

from flask import Blueprint, request, jsonify
from modules.utils.auth import require_auth
from modules.services.embedding_service import EmbeddingService
import os
import base64
import json
import logging

ai_bp = Blueprint('ai', __name__)
logger = logging.getLogger(__name__)

# Gemini API key from environment (server-side only)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

@ai_bp.route('/analyze-document', methods=['POST'])
@require_auth
def analyze_document(current_user):
    """
    Analyze uploaded document using Gemini AI
    Extracts: document_type, reason, due_date, amount
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Read file content
        file_content = file.read()
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Determine MIME type
        mime_type = file.content_type or 'application/octet-stream'
        
        # Call Gemini API
        import requests
        
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"
        
        prompt = """Analizza questo documento e estrai le informazioni in formato JSON.
Schema richiesto:
{
  "document_type": "bolletta" | "fattura" | "multa" | "ricevuta" | "altro",
  "reason": "descrizione breve (es. 'Bolletta Enel Energia' o 'Multa ZTL')",
  "due_date": "data scadenza in formato ISO 8601 YYYY-MM-DD (null se non presente)",
  "amount": numero decimale importo in euro (null se non presente)
}

Rispondi SOLO con il JSON, senza markdown o spiegazioni."""

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": file_base64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }
        
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(gemini_url, json=payload, timeout=30)
                response.raise_for_status()
                result = response.json()
                # Extract JSON from response
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    analysis = json.loads(content)
                    return jsonify({
                        'success': True,
                        'analysis': analysis
                    }), 200
                else:
                    return jsonify({'error': 'No analysis returned from AI'}), 500
            except requests.exceptions.RequestException as e:
                print(f"Gemini API error (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    raise
            
    except Exception as e:
        print(f"AI analyze error: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/chat', methods=['POST'])
@require_auth
def ai_chat(current_user):
    """
    AI chat endpoint for event creation via text
    Uses Gemini with function calling
    """
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        
        if not messages:
            return jsonify({'error': 'No messages provided'}), 400
        
        # Transform messages to Gemini format
        contents = []
        for msg in messages:
            role = 'model' if msg['role'] == 'ai' else 'user'
            contents.append({
                'role': role,
                'parts': [{'text': msg['content']}]
            })
        
        # System instruction
        system_instruction = """Sei un assistente per la creazione di eventi. 
Aiuta l'utente a compilare i dettagli di un evento (titolo, data, importo, categoria, ecc.).
Fai domande brevi e chiare. Quando hai tutte le informazioni necessarie, chiedi conferma.
Usa le funzioni fornite per aggiornare i dati dell'evento."""
        
        # Function declarations
        tools = [{
            "function_declarations": [{
                "name": "update_event_details",
                "description": "Aggiorna i dettagli dell'evento nel form",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING", "description": "Titolo evento"},
                        "start_datetime": {"type": "STRING", "description": "Data/ora inizio ISO 8601"},
                        "end_datetime": {"type": "STRING", "description": "Data/ora fine ISO 8601"},
                        "amount": {"type": "NUMBER", "description": "Importo in euro"},
                        "category_id": {"type": "STRING", "description": "ID categoria"},
                        "description": {"type": "STRING", "description": "Descrizione"}
                    }
                }
            }, {
                "name": "save_and_close_event",
                "description": "Salva l'evento dopo conferma dell'utente",
                "parameters": {"type": "OBJECT", "properties": {}}
            }]
        }]
        
        import requests
        
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "tools": tools
        }
        
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(gemini_url, json=payload, timeout=30)
                response.raise_for_status()
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    # Check for function calls
                    function_calls = []
                    if 'content' in candidate and 'parts' in candidate['content']:
                        for part in candidate['content']['parts']:
                            if 'functionCall' in part:
                                function_calls.append(part['functionCall'])
                    # Get text response
                    text_response = ''
                    if 'content' in candidate and 'parts' in candidate['content']:
                        for part in candidate['content']['parts']:
                            if 'text' in part:
                                text_response = part['text']
                                break
                    return jsonify({
                        'success': True,
                        'text': text_response,
                        'function_calls': function_calls
                    }), 200
                else:
                    return jsonify({'error': 'No response from AI'}), 500
            except requests.exceptions.RequestException as e:
                print(f"Gemini API error (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    raise
            
    except Exception as e:
        print(f"AI chat error: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/search', methods=['POST'])
@require_auth
def rag_search(current_user):
    """
    RAG Search endpoint - Search across all vectorized documents and events

    POST /api/ai/search
    {
        "query": "quanto avevo di colesterolo?",
        "source_types": ["document", "event"],  // optional
        "top_k": 5  // optional
    }
    """
    try:
        data = request.get_json()
        query = data.get('query', '').strip()

        if not query:
            return jsonify({'error': 'Query parameter required'}), 400

        source_types = data.get('source_types')  # None = search all
        top_k = data.get('top_k', 5)

        # Search embeddings
        results = EmbeddingService.search(
            query=query,
            source_types=source_types,
            top_k=top_k
        )

        # Build context for LLM
        context_parts = []
        for i, match in enumerate(results):
            context_parts.append(f"[{i}] {match['text']}")

        context = "\n\n".join(context_parts)

        # Generate answer using Gemini Flash
        import requests

        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"

        system_prompt = """Sei un assistente che risponde SOLO usando i passaggi forniti tra parentesi quadre [i].
Cita sempre i riferimenti numerici quando possibile.
Se la risposta non è nei passaggi, dì chiaramente che l'informazione non è disponibile.
Rispondi in modo naturale e conversazionale."""

        prompt = f"{system_prompt}\n\nPassaggi:\n{context}\n\nDomanda: {query}\n\nRisposta:"

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": 800,
                "temperature": 0.3
            }
        }

        response = requests.post(gemini_url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        answer = ""
        if 'candidates' in result and len(result['candidates']) > 0:
            parts = result['candidates'][0]['content']['parts']
            if parts:
                answer = parts[0]['text']

        logger.info(f"RAG search for user {current_user['id']}: '{query}' - {len(results)} matches")

        return jsonify({
            'success': True,
            'query': query,
            'answer': answer,
            'sources': results,
            'total_matches': len(results)
        }), 200

    except Exception as e:
        logger.error(f"RAG search error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/vectorize-document', methods=['POST'])
@require_auth
def vectorize_document_endpoint(current_user):
    """
    Vectorize a document for RAG search

    POST /api/ai/vectorize-document
    {
        "document_id": "uuid",
        "text": "full document text",
        "metadata": {}  // optional
    }
    """
    try:
        data = request.get_json()

        document_id = data.get('document_id')
        text = data.get('text', '').strip()
        metadata = data.get('metadata', {})

        if not document_id or not text:
            return jsonify({'error': 'document_id and text required'}), 400

        # Vectorize document
        chunks_count = EmbeddingService.vectorize_document(
            document_id=document_id,
            full_text=text,
            metadata=metadata
        )

        logger.info(f"Vectorized document {document_id} into {chunks_count} chunks")

        return jsonify({
            'success': True,
            'document_id': document_id,
            'chunks_created': chunks_count
        }), 200

    except Exception as e:
        logger.error(f"Vectorize document error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/vectorize-event', methods=['POST'])
@require_auth
def vectorize_event_endpoint(current_user):
    """
    Vectorize an event for RAG search

    POST /api/ai/vectorize-event
    {
        "event_id": "uuid",
        "event_data": {
            "title": "...",
            "description": "...",
            "start_datetime": "...",
            "location": "...",
            "category_name": "..."
        }
    }
    """
    try:
        data = request.get_json()

        event_id = data.get('event_id')
        event_data = data.get('event_data', {})

        if not event_id or not event_data:
            return jsonify({'error': 'event_id and event_data required'}), 400

        # Vectorize event
        embedding_id = EmbeddingService.vectorize_event(
            event_id=event_id,
            event_data=event_data
        )

        logger.info(f"Vectorized event {event_id}")

        return jsonify({
            'success': True,
            'event_id': event_id,
            'embedding_id': embedding_id
        }), 200

    except Exception as e:
        logger.error(f"Vectorize event error: {str(e)}")
        return jsonify({'error': str(e)}), 500
