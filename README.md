# AI Bio-Security Threat Forecaster

This project was completed during the Apart Research def/acc hackathon. Its function is to outline the bio-security threats that could potentially happen given advancing AI capabilities. The idea is that automating the analysis of AI capabilities in relation to bio-security threats will ensure us to stay up to date and aware of future threats, allowing us to sufficient time to develop and deploy safeguards.

Tracks emerging AI-enabled bio-security threats by monitoring AI-capabilities in publications.
1. Finds papers from given data sources that outline current AI capabilities
2. Finds AI-enabled Bio-security threats
3. Maps capabilities that will have an impact on threats & predicts feasibility


## Quick Start
### 1. Setup Environment

```
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create data directory
mkdir -p data
```
### 2. Configure API key
```
# Edit .env and add your OpenRouter API key
# Get one at: https://openrouter.ai/keys
```
### 3. Initialize Database
```
# Seed data sources

mkdir data
touch data/biosecurity.db

python scripts/seed_sources.py

# Edit scripts/seed_threats.py with YOUR threat categories, then:
python scripts/seed_threats.py
```
### 4. Run Application
```
# Terminal 1 - Backend API
uvicorn backend.main:app --reload --port 8000

# Terminal 2 - Streamlit Frontend
streamlit run frontend/app.py
```
### 5. Run ingestion cycle via script
```
# Via script
python scripts/run_ingestion.py
```
