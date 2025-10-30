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
        
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        prompt = """IMPORTANTE: Leggi TUTTO il CONTENUTO del documento (non il nome file!). Analizza il testo e le informazioni scritte nel documento.

Cerca nel documento:
- Tipo documento (bolletta/fattura/ordine/multa/ricevuta/contratto/altro)
- Descrizione/oggetto (es. "Ordine Caparol materiali edili", "Bolletta Enel luce")
- Data scadenza/pagamento/emissione (cerca parole: scadenza, pagamento, data emissione, valuta fino al)
- Importo totale in euro (cerca: totale, importo, da pagare, totale fattura, IVA inclusa)

Schema JSON richiesto:
{
  "document_type": "bolletta" | "fattura" | "ordine" | "multa" | "ricevuta" | "contratto" | "altro",
  "reason": "descrizione dettagliata dell'oggetto del documento (es. 'Ordine Caparol materiali edili num. 3000123284' o 'Bolletta Enel energia elettrica')",
  "due_date": "data scadenza/pagamento in formato ISO 8601 YYYY-MM-DD (null se non trovata nel testo)",
  "amount": numero decimale importo totale in euro (null se non trovato nel testo)
}

Rispondi SOLO con il JSON valido, senza markdown o spiegazioni."""

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
        categories = data.get('categories', []) or []  # Categories from frontend (handle None)
        form_state = data.get('form_state', {})  # Current form state so AI can see what's filled

        if not messages:
            return jsonify({'error': 'No messages provided'}), 400

        # Constants for AI context
        COLORS = ['#3B82F6', '#10B981', '#EF4444', '#F97316', '#8B5CF6', '#F59E0B', '#EC4899']
        RECURRENCE_OPTIONS = ['none', 'daily', 'weekly', 'monthly', 'yearly']
        REMINDER_OPTIONS = [0, 5, 10, 15, 30, 60, 120, 1440]  # minutes
        
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

        # Build form state description for AI to see
        form_state_desc = "📝 STATO FORM CORRENTE:\n"
        form_state_desc += f"- Titolo: {form_state.get('title') or '❌ MANCANTE'}\n"
        form_state_desc += f"- Data inizio: {form_state.get('start_datetime') or '❌ MANCANTE'}\n"
        form_state_desc += f"- Categoria: {form_state.get('category_id') or '❌ MANCANTE'}\n"
        form_state_desc += f"- Importo: {form_state.get('amount') or 'non specificato'}\n"
        form_state_desc += f"- Colore: {form_state.get('color') or 'non specificato'}\n"
        form_state_desc += f"- Promemoria: {form_state.get('reminders') or 'nessuno'}\n"
        form_state_desc += f"- Ricorrenza: {form_state.get('recurrence') or 'none'}\n"

        # Build categories description for AI
        categories_desc = ""
        if categories and len(categories) > 0:
            categories_desc = "\n📋 CATEGORIE DISPONIBILI:\n"
            for cat in categories:
                cat_name = cat.get('name', '')
                cat_id = cat.get('id', '')
                cat_icon = cat.get('icon', '')
                categories_desc += f"- {cat_icon} {cat_name} (id: {cat_id})\n"
        else:
            categories_desc = "\n📋 CATEGORIE DISPONIBILI: Nessuna categoria disponibile\n"

        # Get category names for safe join
        category_names = ', '.join([c.get('name', '') for c in categories]) if categories else "nessuna"

        # System instruction - VERSIONE MIGLIORATA (linguaggio naturale)
        system_instruction = f"""🎯 RUOLO E REGOLE FONDAMENTALI

Tu sei un assistente per gestire eventi e interrogare il database.

HAI SOLO 2 COMPITI:
1. CREARE EVENTO → usa update_event_details, poi save_and_close_event
2. CERCARE NEL DB → usa search_documents

REGOLE CRITICHE:
❌ MAI scrivere il codice delle funzioni (tipo "update_event_details(title=...")") nel testo della risposta
❌ MAI chiedere "che tipo di evento vuoi creare?" - CREA SUBITO
❌ MAI dire "ti aiuto" o "nessun problema" - VAI DRITTO AL PUNTO
✅ CHIAMA le funzioni silenziosamente (l'utente NON deve vedere il codice!)
✅ Rispondi SOLO con conferme brevi tipo "Ok!" o "Fatto!"

{form_state_desc}
{categories_desc}
{events_context}

⚙️ FUNZIONI DISPONIBILI

update_event_details       = compila/aggiorna campi modulo (apre il form automaticamente!)
save_and_close_event      = salva l'evento e chiude
search_documents          = cerca eventi/documenti nel database vettorizzato
highlight_upload_buttons   = evidenzia pulsanti caricamento file
create_document           = salva nota semplice (senza data/ora)

🧩 CAMPI (PARAMETRI) CHE PUOI LEGGERE O SCRIVERE

title            = titolo dell'evento
start_datetime   = data/ora di inizio (ISO 8601, es. 2025-06-30T15:00)
end_datetime     = data/ora di fine (ISO 8601)
description      = descrizione o note
amount           = importo economico (€)
category_id      = ID categoria (vedi lista sopra)
recurrence       = regola di ricorrenza (none, daily, weekly, monthly, yearly)
reminders        = minuti prima della notifica (es. [60, 1440])
color            = colore esadecimale (es. #3B82F6)

📅 CREARE EVENTO (logica intelligente con feedback)

QUANDO l'utente dice qualcosa tipo:
- "pagare fattura mario"
- "palestra domani"
- "riunione venerdì"
- "ho un ddt"
- "appunto: comprare pane"

PROCESSO:
1. Estrai: titolo dalla frase dell'utente
2. Inferisci: data/ora
   - Se chiara ("domani", "lunedì", "15:30") → usa quella
   - Se vaga ("prossima settimana") → chiedi "Che giorno preciso?"
   - Se manca del tutto → OGGI ora corrente
3. Inferisci: categoria (palestra→Personale, riunione→Lavoro, fattura/ddt→prima disponibile)
4. Reminders: NESSUNO di default (solo se utente dice "ricordamelo" o "promemoria")
5. CHIAMA update_event_details(title="...", start_datetime="...", category_id="...")
6. CONFERMA con messaggio tipo:
   - "Ok! Ho inserito '[titolo]' per [data/ora]. Va bene?"
   - "Fatto! Vedi '[titolo]' qui sotto per [data]. Tutto ok?"

QUANDO CHIEDERE:
✅ Chiedi se data VERAMENTE ambigua: "venerdì" (quale venerdì? questo o prossimo?)
✅ Chiedi se manca info critica per eventi specifici: "scadenza bolletta" senza importo
❌ NON chiedere "che tipo di evento?" - crea subito
❌ NON chiedere conferma per ogni campo - compila e poi chiedi conferma finale

ESEMPI INFERENZA DATE:
- Nessuna data → OGGI ora corrente
- "domani" → +1 giorno ore 09:00
- "domani pomeriggio" → +1 giorno ore 15:00
- "lunedì prossimo" → prossimo lunedì ore 09:00
- "15:30" → oggi alle 15:30

ESEMPI INFERENZA CATEGORIA:
- "palestra", "sport", "corso" → Personale
- "riunione", "meeting", "call", "progetto" → Lavoro
- "compleanno", "anniversario", "cena famiglia" → Famiglia
- "ddt", "fattura", "bolletta", "pagamento" → prima categoria disponibile

SALVATAGGIO:
- Dopo aver mostrato il riepilogo, chiedi: "Va bene? Di' 'salva' per confermare"
- SOLO se utente dice "salva", "conferma", "va bene così" → save_and_close_event()
- Se dice "ok" o "bene" → chiedi "Salvo? Scrivi 'salva'"

🔍 CERCARE NEL DATABASE

Se l'utente fa DOMANDE tipo:
- "quando devo pagare la luce?"
- "quando ho il dentista?"
- "ho pagato la bolletta?"

FAI SUBITO:
1. CHIAMA search_documents(query="testo domanda", source_types=["event", "document"])
2. NON dire "cerco" o "aspetta" - chiama DIRETTAMENTE la funzione
3. La risposta arriverà automaticamente dal sistema

💬 ESEMPI (IMPORTANTE - segui ESATTAMENTE questo pattern):

User: "ho un ddt"
AI chiama: update_event_details({{title: "DDT", start_datetime: "2025-10-30T14:30", category_id: "prima_categoria_id"}})
AI risponde: "Ok! Ho inserito 'DDT' per oggi alle 14:30. Va bene?"

User: "pagare fattura mario domani"
AI chiama: update_event_details({{title: "Pagare fattura mario", start_datetime: "2025-10-31T09:00", category_id: "prima_categoria_id"}})
AI risponde: "Fatto! 'Pagare fattura mario' inserito per domani mattina. Tutto ok?"

User: "palestra domani pomeriggio"
AI chiama: update_event_details({{title: "Palestra", start_datetime: "2025-10-31T15:00", category_id: "personale_id"}})
AI risponde: "Ok! Palestra domani alle 15:00. Confermi?"

User: "riunione venerdì"
AI risponde: "Quale venerdì? Questo venerdì 1 novembre o il prossimo?"
(aspetta risposta prima di chiamare update_event_details)

User: "quando devo pagare la luce?"
AI chiama: search_documents({{query: "quando devo pagare la luce scadenza bolletta", source_types: ["event", "document"]}})
(la risposta arriva automaticamente dal sistema - NON scrivere nulla tu)

User: "salva"
AI chiama: save_and_close_event()
AI risponde: "Salvato!"

REGOLE CRITICHE:
- MAI scrivere "update_event_details(...)" nel testo visibile all'utente
- CHIAMA la funzione silenziosamente (in background)
- DOPO la chiamata, conferma con messaggio breve e descrittivo
- Includi sempre nel messaggio: cosa hai inserito, quando, e chiedi "Va bene?"
"""
        
        # Build category IDs description for function
        category_ids_desc = ', '.join([f"{c.get('name')} (id: {c.get('id')})" for c in categories]) if categories else "Nessuna categoria disponibile"

        # Function declarations - COMPLETE con RAG
        tools = [{
            "function_declarations": [
                {
                    "name": "update_event_details",
                    "description": "Aggiorna i dettagli di un evento nel form. Usa questa funzione per riempire i campi man mano che ottieni le informazioni dall'utente.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "title": {"type": "STRING", "description": "Il titolo dell'evento."},
                            "start_datetime": {"type": "STRING", "description": "La data e ora di inizio in formato ISO 8601. Inferisci l'anno se non specificato."},
                            "end_datetime": {"type": "STRING", "description": "La data e ora di fine in formato ISO 8601. Se non specificato, imposta la durata a 1 ora dall'inizio."},
                            "description": {"type": "STRING", "description": "Una breve descrizione o nota per l'evento."},
                            "amount": {"type": "NUMBER", "description": "L'importo monetario, se applicabile."},
                            "category_id": {"type": "STRING", "description": f"L'ID della categoria. Scegli tra questi: {category_ids_desc}"},
                            "recurrence": {"type": "STRING", "description": f"La ricorrenza. Scegli tra: {', '.join(RECURRENCE_OPTIONS)}"},
                            "reminders": {"type": "ARRAY", "items": {"type": "NUMBER"}, "description": f"Promemoria in minuti prima dell'evento. Scegli tra: {', '.join(map(str, REMINDER_OPTIONS))}"},
                            "color": {"type": "STRING", "description": f"Colore esadecimale per l'evento. Scegli tra: {', '.join(COLORS)}"}
                        }
                    }
                },
                {
                    "name": "save_and_close_event",
                    "description": "Salva l'evento con i dettagli correnti nel modulo e chiude la finestra. Da usare SOLO dopo che l'utente ha dato la conferma finale che i dettagli sono corretti.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "search_documents",
                    "description": "Cerca nei documenti vettorizzati usando ricerca semantica (RAG). Usa quando l'utente fa domande tipo 'ho pagato...?', 'quando...?', 'quanto ho speso...?'",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "query": {"type": "STRING", "description": "La query di ricerca in linguaggio naturale"},
                            "top_k": {"type": "NUMBER", "description": "Numero massimo di risultati (default 5)"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "create_document",
                    "description": "Crea un nuovo documento nell'archivio vettorizzato. Usa quando l'utente vuole archiviare informazioni senza creare evento calendario.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "title": {"type": "STRING", "description": "Titolo del documento"},
                            "content": {"type": "STRING", "description": "Contenuto testuale del documento"},
                            "date": {"type": "STRING", "description": "Data associata al documento (ISO 8601)"},
                            "category_id": {"type": "STRING", "description": f"Categoria documento. Scegli tra: {category_ids_desc}"}
                        },
                        "required": ["title", "content"]
                    }
                },
                {
                    "name": "highlight_upload_buttons",
                    "description": "Evidenzia i pulsanti di caricamento documento (📷 Foto e 📁 File) con un'animazione per attirare l'attenzione dell'utente. Usa quando suggerisci di caricare un documento.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {},
                        "required": []
                    }
                }
            ]
        }]
        
        import requests
        
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
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

                # Handle rate limiting (429) with exponential backoff
                if response.status_code == 429:
                    wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s
                    logger.warning(f"Rate limit hit (429), waiting {wait_time}s before retry {attempt+1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        return jsonify({
                            'error': 'Troppe richieste. Aspetta 30 secondi e riprova.',
                            'details': 'Rate limit Gemini API raggiunto.'
                        }), 429

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

        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

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
