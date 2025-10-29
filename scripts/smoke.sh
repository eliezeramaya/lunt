#!/bin/bash
# Smoke test script to verify basic API functionality
# Run after starting services with docker-compose

set -e

API_URL="${API_URL:-http://localhost:8000}"

echo "=== Lunt API Smoke Test ==="
echo "API URL: $API_URL"
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
curl -s "$API_URL/health" | jq .
echo ""

# Test 2: Root Endpoint
echo "Test 2: Root Endpoint"
curl -s "$API_URL/" | jq .
echo ""

# Test 3: API Docs Available
echo "Test 3: Check API Docs"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/docs")
if [ $STATUS -eq 200 ]; then
    echo "API docs available at $API_URL/docs"
else
    echo "ERROR: API docs not available (status: $STATUS)"
    exit 1
fi
echo ""

# Test 4: Preview Endpoint (expect 404 for non-existent concept)
echo "Test 4: Preview Endpoint (expect 404)"
curl -s -X POST "$API_URL/v1/preview" \
    -H "Content-Type: application/json" \
    -d '{"concept_code": "NONEXISTENT"}' | jq .
echo ""

echo "=== Smoke Test Complete ==="
echo "All basic checks passed"
