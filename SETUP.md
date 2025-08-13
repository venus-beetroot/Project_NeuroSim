# ⚙️ Project NeuroSim — Setup Guide

Welcome! This guide will walk you through setting up the **Project NeuroSim** simulation game on your local machine.

---

## 🔧 1. Prerequisites

Before running the setup, make sure the following tools are installed on your system:

| Tool         | Purpose                                      | Download Link |
|--------------|----------------------------------------------|----------------|
| **Ollama**   | Runs the local LLM `llama3.2`                | [ollama.com](https://ollama.com/download) |
| **Python 3.10+** | Core runtime (alternative to Miniconda)  | [python.org](https://python.org/downloads) |
| **Miniconda** | Manages Python and virtual environments     | [docs.conda.io](https://docs.conda.io/en/latest/miniconda.html) |
| **Git**      | Clones this repository                       | [git-scm.com](https://git-scm.com/) |

**Note:** You can use either Miniconda OR Python 3.10+ with pip. Choose the approach you're more comfortable with.

Also recommended:
- [Visual Studio Code](https://code.visualstudio.com/)
- Terminal: Git Bash, iTerm2, Windows Terminal, or WSL

After installation, verify tools with:

```bash
ollama --version
# For conda users:
conda --version
# For pip users:
python3 --version
pip --version
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

### Option A: Conda Environment (Recommended)
```bash
bash setup.sh
```
### Option B: Python Virtual Environment (If Conda has SSL issues)
```bash
bash setup_pip.sh
```


Both scripts will:
- [x] Create a new Conda environment called neurosim
- [x] Install required Python packages (pygame, requests, ollama)
- [x] Confirm the llama3.2 model is available

---

## 🔒 SSL Issues with Conda?

If you encounter SSL errors with conda, try these fixes: 

1. Quick fix (temporary): 
```bash
conda config --set ssl_verify false
```

2. Update certificates (recommended):
```bash
conda update ca-certificates
conda update certifi
```

3. Use the pip version instead:
```bash
bash setup_pip.sh
```

---

## 🧪 5. Run the Game
After setup is complete, activate the environment and run the game:

### If using Conda setup: 
```bash
conda activate neurosim
python main.py
```

### If using pip setup: 

1. Linux/Mac
```bash
source neurosim_venv/bin/activate  
```

2. Windows
```bash
neurosim_venv\Scripts\activate
python main.py
```


## 🧹 Cleanup / Reinstall
To delete the environment and start fresh:

### For Conda environment: 
```bash
conda deactivate
conda remove --name neurosim --all
```

### For pip environment: 
```bash
deactivate
rm -rf neurosim_venv
```

Then rerun your preferred setup script.

--- 

# ❓ Having Issues?

## Common Solutions:

- [ ] Ollama not responding: Ensure Ollama is running with ```ollama serve```

- [ ] Python package errors: Make sure you've activated your environment first

- [ ] SSL/Certificate errors: Try the SSL fixes above or use the pip version

- [ ] Permission errors: On Linux/Mac, you might need sudo for some installations

## Environment Activation: 

Make sure to activate your environment before running the game: 

### Conda users:
```bash
conda activate neurosim
```

### Pip users:

1. Linux/Mac
```bash
source neurosim_venv/bin/activate
```

2. Windows
```bash
neurosim_venv\Scripts\activate
```

## Still Having Problems?

- [ ] Verify all prerequisites are installed correctly

- [ ] Check that Ollama is running: ollama list should show llama3.2

- [ ] Open an issue on the GitHub repository with your error message


---

Happy simulating! 🧠✨

