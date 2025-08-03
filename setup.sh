# setup.sh
#!/usr/bin/env bash
# Setup script for Project_NeuroSim

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

# Check if conda is installed
if ! command -v conda &> /dev/null; then
  echo "❌ Conda not found."
  echo "👉 Please install Miniconda from https://docs.conda.io/en/latest/miniconda.html"
  exit 1
fi

# Create and activate environment
ENV_NAME="neurosim"
if ! conda env list | grep -q "$ENV_NAME"; then
  echo "🐍 Creating conda environment '$ENV_NAME'..."
  conda create -y -n "$ENV_NAME" python=3.10 pip
fi

echo "✅ Activating environment..."
eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install pygame requests ollama

echo ""
echo "🎉 Setup complete!"
echo "👉 To start:"
echo "   conda activate $ENV_NAME"
echo "   python main.py"
