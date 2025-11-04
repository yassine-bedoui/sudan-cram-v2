# Sudan CRAM v2 - Conflict Risk Analysis & Monitoring

A comprehensive conflict risk analysis and monitoring system for Sudan, providing real-time analytics, visualizations, and predictive insights based on ACLED data.

## 🌟 Features

### ✅ Implemented (V1)
- **Analytics Dashboard** - Interactive charts and visualizations
  - Monthly conflict trend analysis (12-month view)
  - Regional comparison bar charts
  - Risk level distribution (pie chart)
  - Top 10 high-risk regions ranking
  - Summary KPI cards (events, fatalities, risk scores)
- **Backend API** - FastAPI REST endpoints
  - `/api/analytics` - Comprehensive analytics data
  - Real ACLED data processing
  - Risk scoring algorithm
- **Frontend** - Next.js 14 + TypeScript
  - Responsive design (mobile-first)
  - Dark theme UI
  - Recharts visualization library
  - Real-time data fetching

### 🚧 Planned (Future Iterations)
- Interactive map with region selection
- Date range filtering and comparison
- Export functionality (PNG, CSV, PDF)
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
│ │ ├── main.py # FastAPI app entry
│ │ ├── routers/
│ │ │ └── analytics.py # Analytics endpoint
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


## 🚀 Setup & Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm/yarn

### Backend Setup

cd backend

Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

Install dependencies
pip install -r requirements.txt

Run server
uvicorn app.main:app --reload --port 8000

### Frontend Setup
cd frontend

Install dependencies
npm install

Run development server
npm run dev


## 📡 API Endpoints

### GET `/api/analytics`

Returns comprehensive analytics data.

**Response:**

{
"summary": {
"total_events": 2451,
"total_fatalities": 18489,
"avg_risk_score": 2.45,
"highest_risk_region": "North Darfur",
"regions_monitored": 19
},
"monthly_trend": [
{
"month": "Nov 2024",
"events": 282,
"fatalities": 2009,
"avg_risk": 4.67
}
],
"regional_data": [
{
"region": "North Darfur",
"events": 349,
"fatalities": 8116,
"risk_score": 10.0
}
],
"risk_distribution": {
"LOW": 12,
"MEDIUM": 5,
"HIGH": 1,
"SEVERE": 1
},
"top_regions": [...]
}


## 🎨 UI Components

### Analytics Dashboard
- **Summary Cards** - Key metrics at a glance
- **Monthly Trend Chart** - Line chart showing events/fatalities over time
- **Regional Comparison** - Bar chart of top 15 regions
- **Risk Distribution** - Pie chart of risk levels
- **Top 10 List** - Ranked regions with detailed stats

### Technology Stack
- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, Recharts
- **Backend:** FastAPI, Pandas, Python 3.9+
- **Data:** ACLED CSV files

## 📈 Risk Scoring Algorithm

Normalized scoring (0-10 scale)
risk_score = (
(events / max_events) * 5 +
(fatalities / max_fatalities) * 5
)

Categories:
SEVERE: >= 7.5
HIGH: >= 5.0
MEDIUM: >= 2.5
LOW: < 2.5


## 🔧 Development

### Running Both Services

**Terminal 1 (Backend):**

cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000


**Terminal 2 (Frontend):**
cd frontend
npm run dev

Access at: `http://localhost:3000`

### Testing the API
Get analytics data
curl http://localhost:8000/api/analytics | python -m json.tool


## 📝 Version History

### V1.0 - Analytics Dashboard (November 4, 2025)
- ✅ Backend API with analytics endpoint
- ✅ Frontend dashboard with Recharts
- ✅ Risk scoring and classification
- ✅ Monthly trend analysis
- ✅ Regional comparison visualizations
- ✅ Real ACLED data integration

## 🤝 Contributing

This is an internal project. For questions or suggestions, contact the development team.

## 📄 License

Proprietary - Internal Use Only

## 📧 Contact

For support or inquiries, please contact the CRAM development team.

---

**Last Updated:** November 4, 2025  
**Version:** 1.0.0  
**Status:** Production-Ready V1
