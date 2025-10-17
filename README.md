# SmartLife Organizer v4

## Istruzioni Database Setup

### 1. Accedi a cPanel → phpMyAdmin

### 2. Seleziona il database `ywrloefq_gm_v4`

### 3. Vai su "SQL" ed esegui prima questo:

```sql
-- Setup iniziale database
CREATE DATABASE IF NOT EXISTS `ywrloefq_gm_v4` 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

USE `ywrloefq_gm_v4`;

SET SQL_MODE = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION';
SET GLOBAL event_scheduler = ON;
```

### 4. Poi copia e incolla tutto il contenuto del file `database/schema.sql`

### 5. Verifica che le tabelle siano state create:

```sql
SHOW TABLES;
```

Dovresti vedere tutte queste tabelle:
- users
- categories  
- events
- documents
- reminders
- ai_queries_log
- document_uploads_log
- vector_embeddings
- subscriptions
- stripe_webhooks_log
- admin_stats

### 6. Test del sistema:

Il backend Flask sarà disponibile all'indirizzo: `https://gruppogea.net/gm_v4/api/`

### Endpoints disponibili:

- `GET /api/health` - Health check
- `POST /api/auth/register` - Registrazione utente
- `POST /api/auth/login` - Login
- `GET /api/auth/verify-email?token=XXX` - Verifica email
- `POST /api/auth/forgot-password` - Reset password
- `POST /api/auth/reset-password` - Conferma reset password
- `GET /api/auth/me` - Profilo utente (richiede auth)

### Test registrazione:

```bash
curl -X POST https://gruppogea.net/gm_v4/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Password123!",
    "password_confirm": "Password123!"
  }'
```

## Struttura Progetto

```
gm_v4/
├── .env                    # Configurazione ambiente
├── .gitignore             # File Git ignore
├── requirements.txt       # Dipendenze Python
├── database/
│   ├── schema.sql         # Schema completo database
│   └── setup.sql          # Script setup iniziale
└── backend/
    ├── config.py          # Configurazione app
    ├── app.py             # App Flask principale
    ├── wsgi.py            # Entry point per hosting
    └── app/
        ├── routes/
        │   └── auth.py    # Routes autenticazione
        ├── services/
        │   └── email_service.py  # Servizio email
        └── utils/
            ├── database.py # Utility database
            └── auth.py     # Utility autenticazione
```

## Prossimi step:

1. ✅ Schema database MySQL creato
2. ✅ Sistema autenticazione completo 
3. 🔄 API eventi e categorie
4. 🔄 Integrazione Gemini AI
5. 🔄 Frontend React PWA
6. 🔄 Google Calendar sync
7. 🔄 Sistema notifiche
8. 🔄 Pagamenti Stripe

## Note tecniche:

- **Database**: MySQL/MariaDB (non PostgreSQL)
- **Embeddings**: JSON arrays invece di pgvector
- **Python**: 3.6.8 compatible
- **Hosting**: cPanel con supporto Python
- **CORS**: Abilitato per sviluppo
