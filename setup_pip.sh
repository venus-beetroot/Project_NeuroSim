#!/usr/bin/env bash
# Setup script for Project_NeuroSim (pip version)

set -euo pipefail

echo "🔧 Starting Project_NeuroSim setup..."

# Ensure ollama is installed
if ! command -v ollama &> /dev/null; then
  echo "❌ Ollama not found."
  echo "👉 Please install Ollama manually from https://ollama.com/download"
  exit 1
fi

# Pull the LLM model
echo "📦 Pulling llama3.2..."
ollama pull llama3.2

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
  echo "❌ Python3 not found."
  echo "👉 Please install Python 3.10+ from https://python.org/downloads"
  exit 1
fi

# Create virtual environment
ENV_NAME="neurosim_venv"
if [ ! -d "$ENV_NAME" ]; then
  echo "🐍 Creating Python virtual environment '$ENV_NAME'..."
  python3 -m venv "$ENV_NAME"
fi

echo "✅ Activating virtual environment..."
source "$ENV_NAME/bin/activate"

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install pygame requests ollama

echo ""
echo "🎉 Setup complete!"
echo "👉 To start:"
echo "   source $ENV_NAME/bin/activate"
echo "   python main.py"
echo ""
echo "👉 To deactivate when done:"
echo "   deactivate"