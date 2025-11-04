# Sudan CRAM v2 - React + FastAPI

## Project Structure

sudan-cram-v2/
├── backend/ # FastAPI backend
│ └── app/
│ ├── api/ # API routes
│ ├── core/ # Core logic & data loaders
│ └── data/ # CSV/Excel datasets
└── frontend/ # React (Next.js) frontend
└── src/
├── app/ # Next.js pages
├── components/ # Reusable components
└── lib/ # Utilities & API client
## Setup

### Backend

cd backend
python -m venv venv 
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

### Frontend
cd frontend
npm install
npm run dev


## Development Plan
See planning document for 15-day migration roadmap.
