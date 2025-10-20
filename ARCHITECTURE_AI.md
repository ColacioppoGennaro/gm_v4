# SmartLife Organizer v4 - Architettura AI

## 🔐 Gestione Chiavi API

### Backend (Server-Side) - File: `/public_html/gm_v4/.env`
```bash
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
DB_PASS=your_database_password
JWT_SECRET_KEY=your_jwt_secret_key
```

**✅ SICURE** - Non esposte al client, usate solo dal server Python

### Frontend (Client-Side) - File: `/frontend/.env`
```bash
VITE_API_BASE_URL=https://gruppogea.net/gm_v4/api
VITE_GEMINI_API_KEY=your_gemini_api_key_for_voice_realtime
```

**⚠️ VITE_GEMINI_API_KEY** - Temporaneamente esposta per **realtime voice** con LiveSession
- Usata SOLO da EventModal.tsx per audio streaming
- In produzione: considera proxy WebSocket server-side per nascondere anche questa

---

## 🤖 Flussi AI

### 1. Document Analysis (Analisi Documenti)
**Flusso:** Frontend → Backend → Gemini API

```
[Browser]
  ↓ File Upload (FormData)
  ↓ POST /api/ai/analyze-document
  ↓ Authorization: Bearer <JWT>
[Flask Backend - ai.py]
  ↓ Legge GEMINI_API_KEY dal .env
  ↓ Invia file a Gemini API
  ↓ Riceve JSON response
[Browser]
  ← JSON: {document_type, reason, due_date, amount}
```

**File coinvolti:**
- Frontend: `apiService.ts` → `aiAnalyzeDocument()`
- Backend: `modules/routes/ai.py` → `@ai_bp.route('/analyze-document')`

### 2. Text Chat (Chat AI per Eventi)
**Flusso:** Frontend → Backend → Gemini API (con Function Calling)

```
[Browser - EventModal.tsx]
  ↓ User message
  ↓ POST /api/ai/chat
  ↓ Body: {messages: [...conversation]}
[Flask Backend - ai.py]
  ↓ Legge GEMINI_API_KEY dal .env
  ↓ Chiama Gemini con function declarations:
       - update_event_details
       - save_and_close_event
  ↓ Processa function calls
[Browser]
  ← JSON: {text: "...", function_calls: [...]}
  → Esegue function calls (aggiorna form, salva evento)
```

**File coinvolti:**
- Frontend: `EventModal.tsx` → `handleTextPrompt()`
- Backend: `modules/routes/ai.py` → `@ai_bp.route('/chat')`

### 3. Voice Realtime (Audio Streaming)
**Flusso:** Frontend ↔ Gemini API (diretta, con chiave client-side)

```
[Browser - EventModal.tsx]
  ↓ User clicks microphone
  ↓ navigator.mediaDevices.getUserMedia()
  ↓ AudioContext (16kHz input)
  ↓
[Gemini LiveSession API]
  ↔ WebSocket connection
  ↔ Audio chunks (PCM base64)
  ↔ Transcription + Function Calls
  ↔ Audio response (24kHz output)
[Browser]
  → Riproduce audio
  → Aggiorna form con function calls
```

**File coinvolti:**
- Frontend: `EventModal.tsx` → `startListening()`
- API: Gemini 2.0 Flash Exp (gemini-2.0-flash-exp)

---

## 📝 Endpoint Backend AI

### `/api/ai/analyze-document` (POST)
**Headers:** `Authorization: Bearer <JWT>`
**Body:** `multipart/form-data` con campo `file`
**Response:**
```json
{
  "success": true,
  "analysis": {
    "document_type": "bolletta",
    "reason": "Bolletta Enel Energia",
    "due_date": "2025-10-30",
    "amount": 150.50
  }
}
```

### `/api/ai/chat` (POST)
**Headers:** 
- `Authorization: Bearer <JWT>`
- `Content-Type: application/json`

**Body:**
```json
{
  "messages": [
    {"role": "ai", "content": "Ciao! Come posso aiutarti?"},
    {"role": "user", "content": "Bolletta Enel 150 euro scadenza 30 ottobre"}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "text": "Ho capito. In quale categoria vuoi inserirlo?",
  "function_calls": [
    {
      "name": "update_event_details",
      "args": {
        "title": "Bolletta Enel",
        "amount": 150,
        "start_datetime": "2025-10-30T00:00:00Z"
      }
    }
  ]
}
```

---

## 🔄 Deployment Checklist

### Backend (cPanel)
1. ✅ File `.env` già presente in `/public_html/gm_v4/.env`
2. ⏳ Upload `modules/routes/ai.py`
3. ⏳ Aggiorna `app.py` con `ai_bp` blueprint
4. ⏳ Installa `requests` library: `pip install requests`
5. ⏳ Restart app via cPanel o `touch passenger_wsgi.py`

### Frontend (Build & Deploy)
1. ⏳ Verifica `.env` ha `VITE_API_BASE_URL=https://gruppogea.net/gm_v4/api`
2. ⏳ Build: `npm run build`
3. ⏳ Upload `dist/` folder su cPanel
4. ⏳ Configura routing (serve `index.html` per tutti i path)

### Test Produzione
1. ⏳ Health check: `curl https://gruppogea.net/gm_v4/api/health`
2. ⏳ Login e ottieni JWT token
3. ⏳ Test AI endpoints con script `test_ai_endpoints.py`

---

## 🚨 Note Sicurezza

### Chiavi Esposte al Client
- ⚠️ `VITE_GEMINI_API_KEY` è visibile nel browser (bundle JS)
- 💡 **Mitigazione:** Usata SOLO per realtime voice, rate limiting su Gemini API
- 🔒 **Migliore opzione futura:** Proxy WebSocket server-side anche per voice

### Chiavi Sicure Server-Side
- ✅ `GEMINI_API_KEY` (backend .env)
- ✅ `DB_PASS` (backend .env)
- ✅ `JWT_SECRET_KEY` (backend .env)
- ✅ `GOOGLE_CLIENT_SECRET` (backend .env)

---

## 📊 Vantaggi Architettura Attuale

1. **Document Analysis:** 100% server-side ✅
2. **Text Chat:** 100% server-side ✅
3. **Voice Realtime:** Client-side (necessario per bassa latenza) ⚠️
4. **Tutte le altre chiavi:** Server-side ✅

## 🎯 Prossimo Step

**Fix Database Schema** → Poi colleghiamo apiService.ts agli endpoint reali!
