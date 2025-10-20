# File da Uploadare su cPanel per Deployment

## 📁 Backend - File Modificati/Nuovi

### 1. `/modules/routes/ai.py` (NUOVO)
Path completo: `public_html/gm_v4/backend/modules/routes/ai.py`
**Contenuto:** Gestisce endpoint `/api/ai/analyze-document` e `/api/ai/chat`

### 2. `/backend/app.py` (MODIFICATO)
Path completo: `public_html/gm_v4/backend/app.py`
**Modifiche:** 
- Aggiunto import: `from modules.routes.ai import ai_bp`
- Aggiunto blueprint: `app.register_blueprint(ai_bp, url_prefix='/api/ai')`

### 3. Dipendenze Python
Aggiungi al `requirements.txt` (se non presente):
```
requests==2.31.0
```

Installa con:
```bash
cd ~/public_html/gm_v4/backend
source ~/virtualenv/public_html/gm_v4/backend/3.9/bin/activate
pip install requests
```

## 🔄 Restart App

Dopo aver uploadato i file:
```bash
cd ~/public_html/gm_v4
touch passenger_wsgi.py
```

Oppure via cPanel: **Application Manager → Restart**

## ✅ Verifica Deployment

### 1. Health Check
```bash
curl https://gruppogea.net/gm_v4/api/health
```

Risposta attesa:
```json
{
  "status": "healthy",
  "version": "4.0.0",
  "service": "SmartLife Organizer API"
}
```

### 2. Test AI Endpoint (richiede JWT token)

Prima ottieni un token:
```bash
curl -X POST https://gruppogea.net/gm_v4/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "yourpassword"}'
```

Poi testa AI chat:
```bash
curl -X POST https://gruppogea.net/gm_v4/api/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "messages": [
      {"role": "ai", "content": "Ciao!"},
      {"role": "user", "content": "Bolletta 150 euro"}
    ]
  }'
```

## 📝 Note Importanti

1. ✅ Il file `.env` in `public_html/gm_v4/.env` contiene già `GEMINI_API_KEY=AIzaSyBiuRPm59rcfz49vXqpb27RjVdJZHUBkhg`
2. ✅ La chiave viene letta automaticamente da `os.getenv('GEMINI_API_KEY')`
3. ⚠️  Assicurati che la cartella `modules/routes/` sia writable
4. 🔒 Il file `.env` NON deve essere accessibile via web (già protetto da `.htaccess`)

## 🎯 Prossimi Step Dopo Deployment Backend

1. Testare endpoint `/api/ai/analyze-document` con un PDF di prova
2. Testare endpoint `/api/ai/chat` con conversazione test
3. Verificare che GEMINI_API_KEY venga letta correttamente dal .env
4. Fixare schema database (colonne events)
5. Collegare frontend agli endpoint reali
6. Build frontend React (`npm run build`)
7. Deploy frontend su cPanel
