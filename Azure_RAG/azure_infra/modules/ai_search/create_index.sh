#!/bin/bash
# Script to create Azure AI Search index with the schema
# Run this after Terraform provisions the search service

set -e

# Check required environment variables
if [ -z "$SEARCH_SERVICE_NAME" ] || [ -z "$SEARCH_ADMIN_KEY" ]; then
    echo "Error: SEARCH_SERVICE_NAME and SEARCH_ADMIN_KEY must be set"
    echo "Usage: SEARCH_SERVICE_NAME=<name> SEARCH_ADMIN_KEY=<key> ./create_index.sh"
    exit 1
fi

SEARCH_ENDPOINT="https://${SEARCH_SERVICE_NAME}.search.windows.net"
INDEX_NAME="rag-index"
API_VERSION="2023-11-01"

echo "Creating index '${INDEX_NAME}' in search service '${SEARCH_SERVICE_NAME}'..."

# Create the index
curl -X PUT "${SEARCH_ENDPOINT}/indexes/${INDEX_NAME}?api-version=${API_VERSION}" \
  -H "Content-Type: application/json" \
  -H "api-key: ${SEARCH_ADMIN_KEY}" \
  -d @index_schema.json

echo ""
echo "Index created successfully!"
echo ""
echo "You can verify the index at:"
echo "${SEARCH_ENDPOINT}/indexes/${INDEX_NAME}?api-version=${API_VERSION}"
