# Project: NeuroSim

---

## Welcome!
Welcome to our STEAM day project, Project: NeuroSim! 
_This project is a ai-integrated NPC's town with interactive furniture, houses and environments. 
All the NPC's can talk with you and with each other, along with going in and out of buildings,
adapting to the environment and interacting with elements inside buildings and in the environment._ 

---

# Prerequisites

### 1. Ollama Llama3.2 model
_Llama3.2 is a local large language model that doesn't include reasoning, leading to the NPCs prone
to making mistakes, just like humans or characters in video games._

To install: 
1. Go to: https://ollama.com/download

2. Choose your OS (Linux/macOS), and download the standalone binary version.
    a. For Linux: `ollama-linux-amd64`
    b. For macOS: `ollama-darwin-arm64` or `ollama-darwin-amd64`

3. Go to your terminal (bash)

4. Make it executable: `chmod +x ollama-linux-amd64`

5. Run Ollama and install the model llama3.2
    a. `ollama run llama3.2`

### 2. Python

To Install: 

1. Download Miniconda installer (for your platform):
    Go to: *https://docs.conda.io/en/latest/miniconda.html*

2. Choose:
    a. Miniconda3-latest-Linux-x86_64.sh (Linux)
    b. Miniconda3-latest-MacOSX-x86_64.sh (macOS Intel)
    c. Miniconda3-latest-MacOSX-arm64.sh (macOS M1/M2)

3. Run the installer:
    `bash Miniconda3-latest-Linux-x86_64.sh` and Say **yes** to the license.

4. Install to a location like ~/miniconda3 and activate it.
    `source ~/miniconda3/bin/activate`

5. Confirm Python is installed:
    `python --version`

