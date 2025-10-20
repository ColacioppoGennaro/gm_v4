#!/bin/bash
echo "==================================="
echo "Test Backend Produzione"
echo "==================================="
echo ""

echo "1. Health Check..."
curl -s https://gruppogea.net/gm_v4/api/health | python3 -m json.tool
echo ""
echo ""

echo "2. Provo a registrare utente test..."
curl -s -X POST https://gruppogea.net/gm_v4/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test_ai_'$(date +%s)'@example.com","password":"TestPass123!"}' | python3 -m json.tool
echo ""
echo ""

echo "==================================="
echo "Per testare AI endpoints:"
echo "1. Fai login e copia il token"
echo "2. Usa: curl -X POST https://gruppogea.net/gm_v4/api/ai/chat \\"
echo "   -H 'Authorization: Bearer TOKEN' \\"
echo "   -H 'Content-Type: application/json' \\"
echo "   -d '{\"messages\":[{\"role\":\"user\",\"content\":\"test\"}]}'"
echo "==================================="
