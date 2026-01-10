#!/bin/bash

echo "==================================="
echo "Atlas Dashboard - Verification"
echo "==================================="
echo ""

# Check Node.js version
echo "✓ Checking Node.js version..."
NODE_VERSION=$(node --version)
echo "  Node: $NODE_VERSION"

# Check if node_modules exists
if [ -d "node_modules" ]; then
  echo "✓ Dependencies installed"
else
  echo "✗ Dependencies not installed. Run: npm install"
  exit 1
fi

# Count files
COMPONENT_COUNT=$(find src/components -name "*.tsx" | wc -l)
PAGE_COUNT=$(find src/pages -name "*.tsx" | wc -l)
TYPE_COUNT=$(find src/types -name "*.ts" | wc -l)

echo "✓ Project structure:"
echo "  - Components: $COMPONENT_COUNT files"
echo "  - Pages: $PAGE_COUNT files"
echo "  - Types: $TYPE_COUNT files"

# Check key files
echo ""
echo "✓ Checking key files..."
files=(
  "src/App.tsx"
  "src/main.tsx"
  "src/api/client.ts"
  "src/types/index.ts"
  "vite.config.ts"
  "tailwind.config.js"
  "package.json"
)

for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    echo "  ✓ $file"
  else
    echo "  ✗ $file (MISSING)"
  fi
done

# Check if dev server is running
echo ""
echo "✓ Checking dev server..."
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null ; then
  echo "  ✓ Dev server is running on http://localhost:5173"
else
  echo "  ✗ Dev server not running. Start with: npm run dev"
fi

# Check if API is accessible
echo ""
echo "✓ Checking Atlas API..."
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
  echo "  ✓ API is accessible at http://localhost:8000"
else
  echo "  ✗ API not accessible. Start with:"
  echo "    cd /Users/sven/Desktop/MCP/.worktrees/atlas-api"
  echo "    python3 simple_main.py"
fi

echo ""
echo "==================================="
echo "Verification Complete!"
echo "==================================="
echo ""
echo "To start the dashboard:"
echo "  npm run dev"
echo ""
echo "Then open: http://localhost:5173"
echo ""
