# AI Bio-Security Threat Forecaster

Tracks emerging AI-enabled bio-security threats by monitoring AI-capabilities in publications.

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
