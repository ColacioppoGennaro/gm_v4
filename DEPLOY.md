# 📦 DEPLOYMENT GUIDE - SmartLife Organizer v4

## 🚀 Deploy su Hosting Netsons (cPanel)

### **1. Upload Files**

**Opzione A - Git (se disponibile in cPanel):**
```bash
cd ~/public_html
git clone https://github.com/ColacioppoGennaro/gm_v4.git
cd gm_v4
```

**Opzione B - FTP/File Manager:**
1. Scarica ZIP da GitHub
2. Carica in `public_html/gm_v4/`
3. Estrai i file

---

### **2. Crea file `.env`**

In `public_html/gm_v4/.env` copia questo contenuto:

```env
APP_ENV=production
APP_URI=https://gruppogea.net/gm_v4
SECRET_KEY=gm_v4_secret_key_2025_secure_random_string

DB_HOST=127.0.0.1
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASS="your_database_password"

ADMIN_TOKEN=your_admin_token_here
JWT_SECRET_KEY=your_jwt_secret_key_here

GEMINI_API_KEY=your_gemini_api_key_here
DOCANALYZER_API_KEY=your_docanalyzer_api_key_here

GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=https://gruppogea.net/gm_v4/api/auth/google/callback

PWA_PUSH=true
VAPID_PUBLIC_KEY=your_vapid_public_key_here
VAPID_PRIVATE_KEY=your_vapid_private_key_here
PUSH_SUBJECT=mailto:admin@gruppogea.net

MAIL_ENABLED=false
MAIL_HOST=
MAIL_PORT=587
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=notifiche@gruppogea.net
MAIL_FROM_NAME="SmartLife Organizer"

STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_ID_MONTHLY=
STRIPE_PRICE_ID_ANNUAL=

MAX_FILE_SIZE=10485760
UPLOAD_FOLDER=uploads
ALLOWED_EXTENSIONS=pdf,jpg,jpeg,png

RATE_LIMIT_ENABLED=true
FREE_PLAN_AI_QUERIES_DAILY=20
FREE_PLAN_DOCUMENTS_DAILY=20
```

---

### **3. Setup Python App in cPanel**

**Metodo 1 - Python Selector (se disponibile):**

1. cPanel → **"Setup Python App"**
2. Click **"Create Application"**
3. Configurazione:
   - **Python version:** 3.6.8
   - **Application root:** `gm_v4`
   - **Application URL:** `gm_v4`
   - **Application startup file:** `passenger_wsgi.py`
   - **Application Entry point:** `application`

4. Salva e click **"Edit"**
5. In **"Configuration files"** → carica `requirements.txt`
6. Click **"Run pip install"**

**Metodo 2 - Manuale (se non hai Python Selector):**

Contatta supporto Netsons per attivare Python/WSGI oppure usa `.htaccess` con CGI:

```apache
# In .htaccess
AddHandler cgi-script .py
Options +ExecCGI
```

---

### **4. Permessi File**

```bash
chmod 755 passenger_wsgi.py
chmod 644 .env
chmod 755 backend/
chmod 755 uploads/
```

---

### **5. Test API**

Apri nel browser:

**Health Check:**
```
https://gruppogea.net/gm_v4/api/health
```

**Risposta attesa:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-17T...",
  "version": "4.0.0",
  "service": "SmartLife Organizer API"
}
```

---

### **6. Test Registrazione**

Con **Postman** o **cURL**:

```bash
curl -X POST https://gruppogea.net/gm_v4/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234!",
    "password_confirm": "Test1234!"
  }'
```

---

## 🐛 **Troubleshooting**

### **Errore 500 - Internal Server Error**

1. Verifica permessi file
2. Controlla log errori in cPanel → **Error Log**
3. Verifica che Python 3.6+ sia installato
4. Controlla che tutti i moduli in `requirements.txt` siano installati

### **Errore 404 - Not Found**

1. Verifica che `.htaccess` sia presente
2. Verifica che `passenger_wsgi.py` abbia permessi esecuzione
3. Controlla configurazione Python App in cPanel

### **Database Connection Error**

1. Verifica credenziali in `.env`
2. Test connessione database da phpMyAdmin
3. Verifica che tutte le tabelle siano create

### **CORS Errors**

Aggiungi in `.htaccess`:
```apache
Header set Access-Control-Allow-Origin "*"
```

---

## 📝 **Logs**

Controlla log per debug:

1. **cPanel → Error Log** - errori Apache/Python
2. **Application log** - output Flask app
3. **Database log** - query MySQL errors

---

## ✅ **Checklist Deploy**

- [ ] Repository clonato/uploadato
- [ ] File `.env` creato con variabili corrette
- [ ] Database schema eseguito in phpMyAdmin
- [ ] Python App configurata in cPanel
- [ ] Dipendenze installate (`requirements.txt`)
- [ ] Permessi file corretti
- [ ] Test `/api/health` = 200 OK
- [ ] Test registrazione utente = 201 Created

---

## 🔄 **Update App**

Per aggiornamenti futuri:

```bash
cd ~/public_html/gm_v4
git pull origin main
# Riavvia Python App da cPanel
```

Oppure ricarica i file via FTP/File Manager.