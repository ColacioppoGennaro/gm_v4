"""
AI Service Routes - Gemini Integration
Handles AI-powered features using server-side Gemini API key
"""

from flask import Blueprint, request, jsonify
from modules.utils.auth import require_auth
# from modules.services.embedding_service import EmbeddingService  # TEMPORARY: Disabled until dependencies installed
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
    AI chat endpoint for event creation and search via text
    Uses Gemini with function calling
    """
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        user_events = data.get('events', [])  # Events from frontend

        if not messages:
            return jsonify({'error': 'No messages provided'}), 400
        
        # Build events context for AI
        events_context = ""
        if user_events and len(user_events) > 0:
            events_context = "\n\n📅 EVENTI DELL'UTENTE (per rispondere a domande):\n"
            for i, event in enumerate(user_events[:20], 1):  # Max 20 events
                title = event.get('title', 'Senza titolo')
                start = event.get('start_datetime', '')
                amount = event.get('amount')
                category = event.get('category', {})
                cat_name = category.get('name', '') if isinstance(category, dict) else ''

                events_context += f"{i}. {title}"
                if start:
                    events_context += f" - {start}"
                if cat_name:
                    events_context += f" ({cat_name})"
                if amount:
                    events_context += f" - €{amount}"
                events_context += "\n"

        # Transform messages to Gemini format
        contents = []
        for msg in messages:
            role = 'model' if msg['role'] == 'ai' else 'user'
            contents.append({
                'role': role,
                'parts': [{'text': msg['content']}]
            })

        # System instruction - ESTREMAMENTE ESPLICITO
        system_instruction = f"""Tu sei un assistente AI. Hai a disposizione la funzione update_event_details() per creare eventi.

{events_context}

REGOLE FERREE:
1. Se l'utente dice "inserisci", "crea", "aggiungi", "nuovo evento" → DEVI chiamare update_event_details()
2. Se l'utente fa una domanda → rispondi cercando negli eventi sopra
3. Dopo aver inserito i dati, NON dire "salva" ma di "cliccare il bottone per completare il salvataggio"

ESEMPI CON CHIAMATA FUNZIONE (SEGUI QUESTI):

Esempio 1:
Utente: "inserisci bolletta 50 euro"
Azione: CHIAMA update_event_details con {{"title": "Bolletta", "amount": 50}}
Risposta: "Ok! Bolletta da 50€. Per quando è la scadenza?"

Esempio 2:
Utente: "crea evento domani alle 10"
Azione: CHIAMA update_event_details con {{"start_datetime": "2025-10-24T10:00:00"}}
Risposta: "Ok! Evento per domani alle 10. Che titolo vuoi dargli?"

Esempio 3:
Utente: "aggiungi promemoria pagare affitto"
Azione: CHIAMA update_event_details con {{"title": "Pagare affitto"}}
Risposta: "Ok! Promemoria per pagare affitto. Quando?"

Esempio 4 (utente dice "ok" o "salva"):
Utente: "ok così va bene"
Azione: NESSUNA funzione
Risposta: "Perfetto! Clicca sul bottone 'Completa e Salva' sotto per salvare l'evento."

ESEMPI SENZA CHIAMATA (solo risposta):

Esempio 5:
Utente: "quando devo andare in palestra?"
Azione: Cerca negli eventi sopra
Risposta: "Hai palestra martedì 25 ottobre alle 18:00" oppure "Non ho trovato eventi sulla palestra"

ADESSO SEGUI QUESTE REGOLE ALLA LETTERA!"""
        
        # Function declarations - SOLO update_event_details (save è manuale con bottone)
        tools = [{
            "function_declarations": [{
                "name": "update_event_details",
                "description": "Aggiorna i dettagli dell'evento nel form di creazione",
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

                # DEBUG: Log full response
                logger.info(f"Gemini response: {json.dumps(result, indent=2)}")

                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]

                    # Check for function calls (solo update_event_details e save_and_close_event)
                    function_calls = []
                    if 'content' in candidate and 'parts' in candidate['content']:
                        for part in candidate['content']['parts']:
                            if 'functionCall' in part:
                                function_calls.append(part['functionCall'])
                                logger.info(f"Function call detected: {part['functionCall']}")

                    # Get text response
                    text_response = ''
                    if 'content' in candidate and 'parts' in candidate['content']:
                        for part in candidate['content']['parts']:
                            if 'text' in part:
                                text_response = part['text']
                                break

                    logger.info(f"AI response - text: '{text_response}', function_calls: {len(function_calls)}")

                    return jsonify({
                        'success': True,
                        'text': text_response,
                        'function_calls': function_calls
                    }), 200
                else:
                    return jsonify({'error': 'No response from AI'}), 500
            except requests.exceptions.RequestException as e:
                logger.error(f"Gemini API error (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    raise

    except Exception as e:
        logger.error(f"AI chat error: {e}", exc_info=True)
        return jsonify({'error': 'Si è verificato un errore. Riprova.', 'details': str(e)}), 500


# TEMP_DISABLED: @ai_bp.route('/search', methods=['POST'])
# TEMP_DISABLED: @require_auth
# TEMP_DISABLED: def rag_search(current_user):
# TEMP_DISABLED:     """
# TEMP_DISABLED:     RAG Search endpoint - Search across all vectorized documents and events
# TEMP_DISABLED: 
# TEMP_DISABLED:     POST /api/ai/search
# TEMP_DISABLED:     {
# TEMP_DISABLED:         "query": "quanto avevo di colesterolo?",
# TEMP_DISABLED:         "source_types": ["document", "event"],  // optional
# TEMP_DISABLED:         "top_k": 5  // optional
# TEMP_DISABLED:     }
# TEMP_DISABLED:     """
# TEMP_DISABLED:     try:
# TEMP_DISABLED:         data = request.get_json()
# TEMP_DISABLED:         query = data.get('query', '').strip()
# TEMP_DISABLED: 
# TEMP_DISABLED:         if not query:
# TEMP_DISABLED:             return jsonify({'error': 'Query parameter required'}), 400
# TEMP_DISABLED: 
# TEMP_DISABLED:         source_types = data.get('source_types')  # None = search all
# TEMP_DISABLED:         top_k = data.get('top_k', 5)
# TEMP_DISABLED: 
# TEMP_DISABLED:         # Search embeddings
# TEMP_DISABLED:         results = EmbeddingService.search(
# TEMP_DISABLED:             query=query,
# TEMP_DISABLED:             source_types=source_types,
# TEMP_DISABLED:             top_k=top_k
# TEMP_DISABLED:         )
# TEMP_DISABLED: 
# TEMP_DISABLED:         # Build context for LLM
# TEMP_DISABLED:         context_parts = []
# TEMP_DISABLED:         for i, match in enumerate(results):
# TEMP_DISABLED:             context_parts.append(f"[{i}] {match['text']}")
# TEMP_DISABLED: 
# TEMP_DISABLED:         context = "\n\n".join(context_parts)
# TEMP_DISABLED: 
# TEMP_DISABLED:         # Generate answer using Gemini Flash
# TEMP_DISABLED:         import requests
# TEMP_DISABLED: 
# TEMP_DISABLED:         gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"
# TEMP_DISABLED: 
# TEMP_DISABLED:         system_prompt = """Sei un assistente che risponde SOLO usando i passaggi forniti tra parentesi quadre [i].
# TEMP_DISABLED: Cita sempre i riferimenti numerici quando possibile.
# TEMP_DISABLED: Se la risposta non è nei passaggi, dì chiaramente che l'informazione non è disponibile.
# TEMP_DISABLED: Rispondi in modo naturale e conversazionale."""
# TEMP_DISABLED: 
# TEMP_DISABLED:         prompt = f"{system_prompt}\n\nPassaggi:\n{context}\n\nDomanda: {query}\n\nRisposta:"
# TEMP_DISABLED: 
# TEMP_DISABLED:         payload = {
# TEMP_DISABLED:             "contents": [{
# TEMP_DISABLED:                 "parts": [{"text": prompt}]
# TEMP_DISABLED:             }],
# TEMP_DISABLED:             "generationConfig": {
# TEMP_DISABLED:                 "maxOutputTokens": 800,
# TEMP_DISABLED:                 "temperature": 0.3
# TEMP_DISABLED:             }
# TEMP_DISABLED:         }
# TEMP_DISABLED: 
# TEMP_DISABLED:         response = requests.post(gemini_url, json=payload, timeout=30)
# TEMP_DISABLED:         response.raise_for_status()
# TEMP_DISABLED:         result = response.json()
# TEMP_DISABLED: 
# TEMP_DISABLED:         answer = ""
# TEMP_DISABLED:         if 'candidates' in result and len(result['candidates']) > 0:
# TEMP_DISABLED:             parts = result['candidates'][0]['content']['parts']
# TEMP_DISABLED:             if parts:
# TEMP_DISABLED:                 answer = parts[0]['text']
# TEMP_DISABLED: 
# TEMP_DISABLED:         logger.info(f"RAG search for user {current_user['id']}: '{query}' - {len(results)} matches")
# TEMP_DISABLED: 
# TEMP_DISABLED:         return jsonify({
# TEMP_DISABLED:             'success': True,
# TEMP_DISABLED:             'query': query,
# TEMP_DISABLED:             'answer': answer,
# TEMP_DISABLED:             'sources': results,
# TEMP_DISABLED:             'total_matches': len(results)
# TEMP_DISABLED:         }), 200
# TEMP_DISABLED: 
# TEMP_DISABLED:     except Exception as e:
# TEMP_DISABLED:         logger.error(f"RAG search error: {str(e)}")
# TEMP_DISABLED:         return jsonify({'error': str(e)}), 500
# TEMP_DISABLED: 
# TEMP_DISABLED: 
# TEMP_DISABLED: @ai_bp.route('/vectorize-document', methods=['POST'])
# TEMP_DISABLED: @require_auth
# TEMP_DISABLED: def vectorize_document_endpoint(current_user):
# TEMP_DISABLED:     """
# TEMP_DISABLED:     Vectorize a document for RAG search
# TEMP_DISABLED: 
# TEMP_DISABLED:     POST /api/ai/vectorize-document
# TEMP_DISABLED:     {
# TEMP_DISABLED:         "document_id": "uuid",
# TEMP_DISABLED:         "text": "full document text",
# TEMP_DISABLED:         "metadata": {}  // optional
# TEMP_DISABLED:     }
# TEMP_DISABLED:     """
# TEMP_DISABLED:     try:
# TEMP_DISABLED:         data = request.get_json()
# TEMP_DISABLED: 
# TEMP_DISABLED:         document_id = data.get('document_id')
# TEMP_DISABLED:         text = data.get('text', '').strip()
# TEMP_DISABLED:         metadata = data.get('metadata', {})
# TEMP_DISABLED: 
# TEMP_DISABLED:         if not document_id or not text:
# TEMP_DISABLED:             return jsonify({'error': 'document_id and text required'}), 400
# TEMP_DISABLED: 
# TEMP_DISABLED:         # Vectorize document
# TEMP_DISABLED:         chunks_count = EmbeddingService.vectorize_document(
# TEMP_DISABLED:             document_id=document_id,
# TEMP_DISABLED:             full_text=text,
# TEMP_DISABLED:             metadata=metadata
# TEMP_DISABLED:         )
# TEMP_DISABLED: 
# TEMP_DISABLED:         logger.info(f"Vectorized document {document_id} into {chunks_count} chunks")
# TEMP_DISABLED: 
# TEMP_DISABLED:         return jsonify({
# TEMP_DISABLED:             'success': True,
# TEMP_DISABLED:             'document_id': document_id,
# TEMP_DISABLED:             'chunks_created': chunks_count
# TEMP_DISABLED:         }), 200
# TEMP_DISABLED: 
# TEMP_DISABLED:     except Exception as e:
# TEMP_DISABLED:         logger.error(f"Vectorize document error: {str(e)}")
# TEMP_DISABLED:         return jsonify({'error': str(e)}), 500
# TEMP_DISABLED: 
# TEMP_DISABLED: 
# TEMP_DISABLED: @ai_bp.route('/vectorize-event', methods=['POST'])
# TEMP_DISABLED: @require_auth
# TEMP_DISABLED: def vectorize_event_endpoint(current_user):
# TEMP_DISABLED:     """
# TEMP_DISABLED:     Vectorize an event for RAG search
# TEMP_DISABLED: 
# TEMP_DISABLED:     POST /api/ai/vectorize-event
# TEMP_DISABLED:     {
# TEMP_DISABLED:         "event_id": "uuid",
# TEMP_DISABLED:         "event_data": {
# TEMP_DISABLED:             "title": "...",
# TEMP_DISABLED:             "description": "...",
# TEMP_DISABLED:             "start_datetime": "...",
# TEMP_DISABLED:             "location": "...",
# TEMP_DISABLED:             "category_name": "..."
# TEMP_DISABLED:         }
# TEMP_DISABLED:     }
# TEMP_DISABLED:     """
# TEMP_DISABLED:     try:
# TEMP_DISABLED:         data = request.get_json()
# TEMP_DISABLED: 
# TEMP_DISABLED:         event_id = data.get('event_id')
# TEMP_DISABLED:         event_data = data.get('event_data', {})
# TEMP_DISABLED: 
# TEMP_DISABLED:         if not event_id or not event_data:
# TEMP_DISABLED:             return jsonify({'error': 'event_id and event_data required'}), 400
# TEMP_DISABLED: 
# TEMP_DISABLED:         # Vectorize event
# TEMP_DISABLED:         embedding_id = EmbeddingService.vectorize_event(
# TEMP_DISABLED:             event_id=event_id,
# TEMP_DISABLED:             event_data=event_data
# TEMP_DISABLED:         )
# TEMP_DISABLED: 
# TEMP_DISABLED:         logger.info(f"Vectorized event {event_id}")
# TEMP_DISABLED: 
# TEMP_DISABLED:         return jsonify({
# TEMP_DISABLED:             'success': True,
# TEMP_DISABLED:             'event_id': event_id,
# TEMP_DISABLED:             'embedding_id': embedding_id
# TEMP_DISABLED:         }), 200
# TEMP_DISABLED: 
# TEMP_DISABLED:     except Exception as e:
# TEMP_DISABLED:         logger.error(f"Vectorize event error: {str(e)}")
# TEMP_DISABLED:         return jsonify({'error': str(e)}), 500
