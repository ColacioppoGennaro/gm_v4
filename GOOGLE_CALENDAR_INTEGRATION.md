# 🗓️ Google Calendar Integration - SmartLife Organizer v4

## ✅ FASE 1 COMPLETATA: Google Calendar Sync

### 📝 Cosa è stato implementato

#### Backend
1. **Servizio Google Calendar** (`backend/modules/services/google_calendar_service.py`)
   - OAuth2 flow completo
   - Token refresh automatico
   - CRUD eventi su Google Calendar
   - Gestione credenziali utente

2. **Endpoints OAuth** (`backend/modules/routes/auth.py`)
   - `GET /api/auth/google/connect` - Inizia OAuth flow
   - `GET /api/auth/google/callback` - Callback OAuth (popup window)
   - `POST /api/auth/google/disconnect` - Disconnessione

3. **Sync Automatica Eventi** (`backend/modules/routes/events.py`)
   - **CREATE**: Evento creato su app → push automatico a Google Calendar
   - **UPDATE**: Evento modificato su app → aggiornamento su Google Calendar
   - **DELETE**: Evento cancellato su app → cancellazione da Google Calendar

#### Frontend
1. **API Service** (`frontend/src/services/apiService.ts`)
   - `connectGoogleCalendar()` - Apre popup OAuth e gestisce callback
   - `disconnectGoogleCalendar()` - Disconnette account Google

2. **Settings UI** (`frontend/src/components/Settings.tsx`)
   - Bottone "Connetti/Disconnetti" già presente e funzionante

#### Database
- Schema già pronto con campi necessari:
  - `users`: `google_calendar_connected`, `google_access_token`, `google_refresh_token`, `google_token_expires`
  - `events`: `google_event_id`, `last_synced_at`

### 🚀 Come testare

1. **Deploy su cPanel**:
   ```bash
   cd /home/genaro/gm_v4
   git add .
   git commit -m "feat: Google Calendar sync integration"
   git push origin main
   ```

2. **In cPanel**:
   - Git Version Control → Update from Remote
   - Riavvia backend: `touch passenger_wsgi.py tmp/restart.txt`

3. **Verifica database** (esegui migration se necessario):
   ```bash
   ssh to cPanel
   mysql -u ywrloefq_gm_user -p ywrloefq_gm_v4 < ~/public_html/gm_v4/database/migration_add_google_calendar_fields.sql
   ```

4. **Test nell'app**:
   - Login su https://gruppogea.net/gm_v4/
   - Vai in Settings
   - Click su "Connetti" Google Calendar
   - Autorizza nell'popup
   - Crea un evento → verificare che appare su Google Calendar!

### 🔧 Configurazione Google OAuth

Le credenziali sono già configurate in `.env` su hosting (non committate su Git per sicurezza):
```
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=https://gruppogea.net/gm_v4/api/auth/google/callback
```

**Verifica su Google Cloud Console**:
1. Vai su https://console.cloud.google.com/
2. Progetto SmartLife Organizer
3. API & Services → Credentials
4. Verifica che il redirect URI sia configurato: `https://gruppogea.net/gm_v4/api/auth/google/callback`
5. Abilita **Google Calendar API** se non ancora fatto

### 📌 Note Tecniche

#### Sicurezza
- Token OAuth salvati criptati nel database
- Refresh token automatico quando scade
- State parameter per prevenire CSRF

#### Sincronizzazione
- **Unidirezionale**: App → Google Calendar (per ora)
- Eventi creati in app appaiono su Google Calendar
- Eventi creati direttamente su Google Calendar NON sincronizzano (FASE 2)

#### Errori Gestiti
- Token scaduto → refresh automatico
- Google API down → evento salvato comunque in app (sync in background)
- Popup bloccato → messaggio errore all'utente

---

## 🎯 FASE 2: Vettorializzazione & Knowledge Base

### Cosa implementare

1. **Embedding Service** (`backend/modules/services/embedding_service.py`)
   - Gemini Embedding API integration
   - Chunking documenti lunghi
   - Salvataggio in `vector_embeddings` table

2. **Auto-Document Generation per Eventi**
   - Quando si crea evento → genera documento riassuntivo
   - Vettorializza e salva in `documents` + `vector_embeddings`
   - Link evento ↔ documento via `event_id`

3. **Similarity Search**
   - Query vettoriale per trovare documenti simili
   - Context retrieval per AI chat

4. **Document Upload Enhancement**
   - PDF, immagini, Excel → OCR → vettorializzazione
   - Associazione documenti a eventi

### Database già pronto
- ✅ `documents` table (con `ai_summary`, `extracted_text`)
- ✅ `vector_embeddings` table (JSON format per embeddings)
- ✅ Fulltext search su documenti

---

## 🤖 FASE 3: AI Chat Potenziata

### Obiettivi
- **Conversazionale**: parlare liberamente con l'utente
- **Context-aware**: usare embeddings per rispondere con context
- **Action-oriented**: creare/modificare eventi via function calling
- **Query documenti**: "Quando devo pagare bolletta luce?"

### Già implementato
- ✅ `/api/ai/chat` endpoint con Gemini
- ✅ Function calling base
- ✅ Document analysis endpoint

### Da migliorare
- Recupero context da `vector_embeddings`
- Espansione function calling (update, delete eventi)
- Multi-turn conversation con memory

---

## 📋 TODO List Priorità

### Immediato (per testare Google Calendar)
- [ ] Deploy su cPanel
- [ ] Eseguire migration database
- [ ] Test OAuth flow
- [ ] Creare evento e verificare su Google Calendar

### Prossimo Sprint
- [ ] Embedding service con Gemini
- [ ] Auto-generazione documenti per eventi
- [ ] Vettorializzazione automatica
- [ ] Similarity search

### Future
- [ ] Sync bidirezionale (Google → App)
- [ ] Webhook Google Calendar
- [ ] Conflict resolution
- [ ] Bulk sync iniziale

---

## 🐛 Known Issues

1. **Column naming mismatch**:
   - DB schema usa `start_datetime`/`end_datetime`
   - Python code usa `start_time`/`end_time`
   - **Fix**: Verificare database reale e allineare

2. **Timezone handling**:
   - Hardcoded 'Europe/Rome' nel Google Calendar service
   - **Fix**: Prendere timezone da user settings

3. **Error handling OAuth**:
   - Popup blocker può impedire OAuth
   - **Fix**: Fallback a redirect flow se popup bloccato

---

## 📚 Resources

- [Google Calendar API Docs](https://developers.google.com/calendar/api/v3/reference)
- [OAuth2 Flow](https://developers.google.com/identity/protocols/oauth2)
- [Gemini Embedding API](https://ai.google.dev/docs/embeddings_guide)
