Sudan CRAM v2 - Conflict Risk Analysis & Monitoring
A comprehensive conflict risk analysis and monitoring system for Sudan providing real-time analytics, visualizations, and predictive insights based on ACLED data.

Features
Implemented (V1)
Analytics Dashboard with interactive charts

Monthly conflict trends

Regional comparison

Risk distribution

Top 10 high-risk regions

Summary KPIs (events, fatalities, risk scores)

Backend API (FastAPI)

/api/analytics for comprehensive data

/api/monthly-trend for monthly aggregated trends

Processes real ACLED data with risk scoring

Frontend (Next.js 14 + TypeScript)

Responsive, mobile-first design

Dark theme UI

Visualizations with Recharts

Real-time data fetching

Planned Enhancements
Export options (CSV, JSON, PDF)

Interactive maps and date filters

Real-time updates and advanced visuals

User authentication

Historical trend predictions

Data
ACLED dataset: acled_with_causes.csv covering Nov 2024 - Oct 2025

Includes 2,451 events, 18,489 fatalities across 19 regions

Architecture Overview
text
sudan-cram-v2/
├── backend/          # FastAPI backend & data processing
└── frontend/         # Next.js frontend UI with visualizations
Quick Start
Clone repo:
git clone https://github.com/your-org/sudan-cram-v2.git && cd sudan-cram-v2

Backend:

text
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
Frontend (new terminal):

text
cd frontend
npm install
export NEXT_PUBLIC_BACKEND_URL=http://localhost:8000  # Windows CMD: set NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
npm run dev
Access frontend dashboard at http://localhost:3000.

API Examples
/api/analytics returns dashboard data

/api/monthly-trend returns monthly event and fatality trends

Development Notes
Backend uses FastAPI and Pandas.

Frontend built with Next.js, TypeScript, Tailwind CSS, and Recharts.

Troubleshooting
Backend module errors: Confirm virtual env active and dependencies installed.

Frontend API access errors: Ensure NEXT_PUBLIC_BACKEND_URL is correctly set.

Port conflicts: Kill existing processes using ports 8000 (backend) or 3000 (frontend).

Planned for V2
Export functionality (CSV, JSON, PDF).

Interactive maps and date-based filtering.

Real-time data updates and advanced visualizations.

User authentication.

Historical trend predictions using multi-agent AI.