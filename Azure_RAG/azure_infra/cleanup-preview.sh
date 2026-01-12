#!/bin/bash
# Preview what would be deleted without actually deleting
set -e

echo "========================================="
echo "RAG Application - Cleanup Preview"
echo "========================================="
echo ""
echo "This will show what would be deleted WITHOUT actually deleting anything."
echo ""

terraform plan -destroy

echo ""
echo "========================================="
echo "Preview Complete"
echo "========================================="
echo ""
echo "No resources were deleted (this was a preview only)."
echo ""
echo "To actually delete resources, run:"
echo "  ./cleanup.sh"
echo ""
