#!/bin/bash
# Script per build e deploy automatico del frontend

echo "🔨 Building frontend..."
cd frontend
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "📦 Adding dist files to git..."
cd ..
git add -f frontend/dist/

echo "💾 Committing..."
git commit -m "build: Update frontend bundle [auto-deploy]"

if [ $? -eq 0 ]; then
    echo "🚀 Pushing to GitHub..."
    git push origin main
    echo "✅ Deploy completato! Ora fai 'Update from remote' su cPanel."
else
    echo "ℹ️ Nessuna modifica da committare"
fi
