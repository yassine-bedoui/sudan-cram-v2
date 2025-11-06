# Sudan CRAM v2 - Conflict Risk Analysis & Monitoring

A comprehensive conflict risk analysis and monitoring system for Sudan, providing real-time analytics, visualizations, and predictive insights based on ACLED data.

## 🌟 Features

### ✅ Implemented (V1)
- **Analytics Dashboard** - Interactive charts and visualizations
  - Monthly conflict trend analysis (12-month view with real ACLED data)
  - Regional comparison bar charts
  - Risk level distribution (pie chart)
  - Top 10 high-risk regions ranking
  - Summary KPI cards (events, fatalities, risk scores)
- **Backend API** - FastAPI REST endpoints
  - `/api/analytics` - Comprehensive analytics data
  - `/api/monthly-trend` - Monthly aggregated conflict trends
  - Real ACLED data processing
  - Risk scoring algorithm
- **Frontend** - Next.js 14 + TypeScript
  - Responsive design (mobile-first)
  - Dark theme UI
  - Recharts visualization library
  - Real-time data fetching

### 🚧 Planned (Future Iterations)
- Export functionality (CSV, JSON, PDF)
- Interactive map with region selection
- Date range filtering and comparison
- Real-time data updates
- Advanced visualizations (Sankey, heatmaps)
- User authentication
- Historical trend predictions

## 📊 Data Sources

- **ACLED** (Armed Conflict Location & Event Data Project)
  - `acled_with_causes.csv` - Processed conflict events with classifications
  - Coverage: November 2024 - October 2025
  - 2,451 events | 18,489 fatalities | 19 regions

## 🏗️ Architecture

sudan-cram-v2/
├── backend/ # FastAPI backend
│ ├── app/
│ │ ├── main.py # FastAPI app entry point
│ │ ├── routers/
│ │ │ └── analytics.py # Analytics endpoints
│ │ └── data/
│ │ └── processed/
│ │ └── acled_with_causes.csv
│ ├── requirements.txt
│ └── venv/
│
└── frontend/ # Next.js frontend
├── src/
│ ├── app/
│ │ ├── page.tsx # Home page
│ │ ├── dashboard/ # Dashboard page
│ │ └── analytics/ # Analytics page
│ └── components/
│ └── analytics/
│ ├── TrendChart.tsx
│ ├── RegionalChart.tsx
│ └── RiskDistributionChart.tsx
├── package.json
└── node_modules/


## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.9 or higher
- Node.js 18 or higher
- npm or yarn
- Git

### Step 1: Clone the Repository

git clone https://github.com/your-org/sudan-cram-v2.git
cd sudan-cram-v2

### Step 2: Backend Setup
cd backend

Create virtual environment
python -m venv venv

Activate virtual environment
On macOS/Linux:
source venv/bin/activate

On Windows:
venv\Scripts\activate

Install dependencies
pip install -r requirements.txt

Start the backend server (runs on port 8000)
uvicorn app.main:app --reload --port 8000

**Expected output:**

INFO: Uvicorn running on http://127.0.0.1:8000
INFO: Application startup complete

### Step 3: Frontend Setup (New Terminal)

cd frontend

Install dependencies
npm install

Set backend URL environment variable
On macOS/Linux:
export NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

On Windows (CMD):
set NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

Start the frontend dev server (runs on port 3000)
npm run dev

**Expected output:**

▲ Next.js 14.0.0

Local: http://localhost:3000


### Step 4: Access the Application

- **Frontend Dashboard:** http://localhost:3000
- **Analytics Page:** http://localhost:3000/analytics
- **API Endpoint:** http://localhost:8000/api/analytics

---

## 📡 API Endpoints

### GET `/api/analytics`
Comprehensive analytics data for dashboard

**cURL Example:**
curl http://localhost:8000/api/analytics | python -m json.tool


**Response Fields:**
- `summary` - Key metrics (total_events, total_fatalities, avg_risk_score)
- `monthly_trend` - Monthly aggregated data
- `regional_data` - Per-region statistics
- `risk_distribution` - Risk level breakdown
- `top_regions` - Top 10 high-risk regions

### GET `/api/monthly-trend`
Monthly conflict trend data (events and fatalities)

**cURL Example:**
curl http://localhost:8000/api/monthly-trend | python -m json.tool

**Response:**

{
"data": [
{
"month": "2024-11",
"events": 834,
"fatalities": 2009
}
],
"summary": {
"avg_monthly_events": 491.75,
"avg_monthly_fatalities": 1540.75,
"trend": "decreasing"
}
}


---

## 🎨 Pages Overview

### Dashboard (`/`)
Home page with quick summary cards

### Analytics (`/analytics`)
- Monthly trend chart (line graph)
- Regional comparison (bar chart)
- Risk distribution (pie charts)
- Top 10 regions table

---

## 🛠️ Development

### Project Structure

**Backend:**
- Uses FastAPI for REST API
- Pandas for data processing
- CSV data source (ACLED)

**Frontend:**
- Next.js 14 App Router
- TypeScript for type safety
- Tailwind CSS for styling
- Recharts for visualizations

### Running Both Services

**Terminal 1 (Backend):**

cd backend
source venv/bin/activate # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --port 8000

**Terminal 2 (Frontend):**

cd frontend
export NEXT_PUBLIC_BACKEND_URL=http://localhost:8000 # macOS/Linux
npm run dev


---

## 🔧 Troubleshooting

### Backend won't start
**Error:** `ModuleNotFoundError: No module named 'fastapi'`
**Solution:**

cd backend
source venv/bin/activate
pip install -r requirements.txt


### Frontend can't connect to API
**Error:** `Failed to fetch analytics` or `CORS error`
**Solution:** Ensure `NEXT_PUBLIC_BACKEND_URL` is set correctly

export NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
npm run dev


### Port already in use
**Backend (8000):**

Find process using port 8000
lsof -i :8000

Kill process: kill -9 <PID>
**Frontend (3000):**

Find process using port 3000
lsof -i :3000

Kill process: kill -9 <PID>

---

## 📊 Data Processing

### Risk Scoring Algorithm

Normalized scoring (0-10 scale):
risk_score = (events / max_events) * 5 + (fatalities / max_fatalities) * 5


Risk Categories:
- **SEVERE**: ≥ 7.5
- **HIGH**: ≥ 5.0
- **MEDIUM**: ≥ 2.5
- **LOW**: < 2.5

---

## 📝 Development Workflow

### Creating a Feature Branch

git checkout -b feat/your-feature-name

Make changes and commit
git add .
git commit -m "feat: description of changes"

Push to remote
git push origin feat/your-feature-name

### Pull Request Process

1. Push your branch to GitHub
2. Create a Pull Request on GitHub
3. Ensure tests pass and code review approved
4. Merge to `main` branch

---

## 📦 Production Deployment

### Environment Variables

Create `.env.local` in frontend:
NEXT_PUBLIC_BACKEND_URL=https://your-api-domain.com



### Build for Production

**Backend:**
cd backend
pip install -r requirements.txt
gunicorn app.main:app --workers 4 --bind 0.0.0.0:8000
**Frontend:**

cd frontend
npm install
npm run build
npm start

---

## 📈 Version History

### V1.0 - Analytics Dashboard (November 6, 2025)
- ✅ Backend API with analytics endpoint
- ✅ Monthly trend analysis endpoint
- ✅ Frontend dashboard with Recharts
- ✅ Risk scoring and classification
- ✅ Regional comparison visualizations
- ✅ Real ACLED data integration

---

## 🤝 Contributing

### Code Standards
- Use TypeScript for frontend
- Follow PEP 8 for Python
- Write descriptive commit messages
- Create feature branches for new work

### Testing
Before pushing, verify:
- Backend API returns valid JSON
- Frontend builds without errors
- No console errors in browser DevTools

---

## 📝 License

Proprietary - Internal Use Only

## 📧 Support

For questions or issues, contact the CRAM development team.

---

**Last Updated:** November 6, 2025  
**Version:** 1.0.0  
**Status:** Production-Ready V1  
**Next Iteration:** Export Functionality & Map Integration
