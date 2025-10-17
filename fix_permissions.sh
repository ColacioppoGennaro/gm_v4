#!/bin/bash
# Fix permissions script for gm_v4

echo "🔧 Fixing permissions..."

cd /home/ywrloefq/public_html/gm_v4

# Make Python entry points executable
chmod 755 test.py
chmod 755 index.py
chmod 755 passenger_wsgi.py

# Fix backend permissions
chmod 755 backend
chmod 644 backend/*.py
chmod 755 backend/app
chmod 644 backend/app/*.py 2>/dev/null
chmod 755 backend/app/routes 2>/dev/null
chmod 644 backend/app/routes/*.py 2>/dev/null
chmod 755 backend/app/services 2>/dev/null
chmod 644 backend/app/services/*.py 2>/dev/null
chmod 755 backend/app/utils 2>/dev/null
chmod 644 backend/app/utils/*.py 2>/dev/null

# Secure .env
chmod 600 .env 2>/dev/null

# Make uploads writable
chmod 755 uploads 2>/dev/null

echo "✅ Permissions fixed!"
echo ""
echo "Now run: git config core.fileMode false"
echo "This will prevent Git from tracking permission changes"
