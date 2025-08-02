# ⚙️ Project NeuroSim — Setup Guide

Welcome! This guide will walk you through setting up the **Project NeuroSim** simulation game on your local machine.

---

## 🔧 1. Prerequisites

Before running the setup, make sure the following tools are installed on your system:

| Tool         | Purpose                                      | Download Link |
|--------------|----------------------------------------------|----------------|
| **Ollama**   | Runs the local LLM `llama3.2`                | [ollama.com](https://ollama.com/download) |
| **Miniconda**| Manages Python and virtual environments      | [docs.conda.io](https://docs.conda.io/en/latest/miniconda.html) |
| **Git**      | Clones this repository                       | [git-scm.com](https://git-scm.com/) |

Also recommended:
- [Visual Studio Code](https://code.visualstudio.com/)
- Terminal: Git Bash, iTerm2, Windows Terminal, or WSL

After installation, verify tools with:

```bash
ollama --version
conda --version
git --version
```


## 📦 2. Clone the Repository

```bash
git clone https://github.com/venus-beetroot/Project_NeuroSim.git
cd Project_NeuroSim
```

## 🧠 3. Install the AI Model
Pull the required LLM from Ollama:

```bash
ollama pull llama3.2
```
This is necessary for NPCs to generate AI-powered dialogue locally.

## 🛠️ 4. Run the Setup Script
We’ve bundled all environment setup into one script.

```bash
bash setup.sh
```

This script will:
- [x] Create a new Conda environment called neurosim
- [x] Install required Python packages (pygame, requests, ollama)
- [x] Confirm the llama3.2 model is available


## 🧪 5. Run the Game
After setup is complete, activate the environment and run the game:

```bash
conda activate neurosim
python main.py
```


## 🧹 Cleanup / Reinstall
To delete the environment and start fresh:

```bash
conda deactivate
conda remove --name neurosim --all
```

Then rerun `bash setup.sh.`

--- 

# ❓ Having Issues?

- [ ] Ensure Ollama is running correctly (ollama serve)

- [ ] Make sure Python is being managed via Conda

- [ ] Try restarting your terminal and re-running conda activate neurosim

If problems persist, open an issue on the GitHub repository.


