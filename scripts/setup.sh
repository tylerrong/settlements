#!/bin/bash
set -e

echo "=== Settlement Monitor Setup ==="

# Check Python
python3 --version || { echo "Python 3 required"; exit 1; }

# Create venv
if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "Created virtual environment"
fi

source venv/bin/activate

# Install deps
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Copy env file
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo "⚠️  Created .env — please edit it and add your API keys:"
  echo "   ANTHROPIC_API_KEY=..."
  echo "   DISCORD_WEBHOOK_URL=..."
  echo ""
fi

echo "=== Setup complete ==="
echo ""
echo "Activate the venv:  source venv/bin/activate"
echo "Run one crawl:      python main.py crawl"
echo "Start dashboard:    python main.py serve"
echo "Add a site:         python main.py add-site https://example-settlement.com"
