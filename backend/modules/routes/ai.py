"""
AI Service Routes - Gemini Integration
Handles AI-powered features using server-side Gemini API key
"""

from flask import Blueprint, request, jsonify
from modules.utils.auth import require_auth
import os
import base64
import json

ai_bp = Blueprint('ai', __name__)

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
            
    except Exception as e:
        print(f"AI chat error: {e}")
        return jsonify({'error': str(e)}), 500
