# Excel Mock Interviewer - AI-Powered PoC

A complete AI-powered Excel interview system that simulates human interviewers, evaluates skills through deterministic checks and LLM judgement, and generates comprehensive feedback reports. Built to run entirely on free-tier services.

## 🚀 Quick Start

### Local Development

1. **Clone and Setup**
    git clone <repo-url>
    cd excel-mock-interviewer
    cp .env.example .env


2. **Start Services**
    docker-compose up --build



3. **Access Applications**
- Frontend (Streamlit): http://localhost:8501
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Free Cloud Deployment

See `infra/README_deploy_free.txt` for step-by-step instructions to deploy on:
- **Backend**: Render.com or Railway (free tier)
- **Frontend**: Streamlit Cloud
- **Database**: Render PostgreSQL (free tier)

## 🏗️ Architecture

┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Streamlit │───▶│ FastAPI │───▶│ Evaluation │
│ Frontend │ │ Backend │ │ Workers │
└─────────────────┘ └─────────────────┘ └─────────────────┘
│ │
▼ ▼
┌─────────────────┐ ┌─────────────────┐
│ PostgreSQL │ │ Redis Queue │
│ Database │ │ │
└─────────────────┘ └─────────────────┘


## 🎯 Features

- **Multi-turn Interviews**: 6 adaptive questions with follow-ups
- **Hybrid Evaluation**: Deterministic Excel checks + LLM judgment
- **File Processing**: Upload and analyze Excel workbooks
- **State Management**: Persistent interview sessions
- **Report Generation**: HTML + PDF feedback reports
- **Mock Mode**: Runs without API keys for testing
- **Free Hosting**: Designed for zero-cost deployment

## 🧪 Testing

Run deterministic evaluator tests
docker-compose run backend pytest tests/

Test with mock mode (no API keys needed)
MOCK_MODE=true docker-compose up


## 📊 Question Types

1. **Formula Questions**: VLOOKUP, INDEX/MATCH, array formulas
2. **Practical Exercises**: Pivot tables, data cleaning, dashboards
3. **Multiple Choice**: Excel features and best practices
4. **Explanations**: Methodology and troubleshooting

## 🔧 Configuration

Key environment variables:

- `MOCK_MODE=true`: Run without external API calls
- `GROQ_API_KEY`: Free tier LLM evaluation
- `DATABASE_URL`: PostgreSQL or SQLite
- `DETERMINISTIC_WEIGHT`: Balance between rule-based vs AI scoring

## 📁 Project Structure

excel-mock-interviewer/
├── backend/ # FastAPI application
├── frontend/ # Streamlit UI
├── docs/ # Questions & test data
├── tests/ # Unit tests
└── infra/ # Deployment guides


## 🤝 Contributing

1. Add questions to `docs/seed_questions.json`
2. Create test workbooks in `docs/golden_workbooks/`
3. Extend evaluators in `backend/app/evaluator/`
4. Test in mock mode first

## 📋 License

MIT License - see LICENSE file for details.

Free Deployment Guide (infra/README_deploy_free.txt)

