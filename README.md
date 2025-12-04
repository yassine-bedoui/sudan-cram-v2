# MERLx – Conflict & Climate Risk Analytics API

MERLx exposes a FastAPI-based REST API that combines:

- **Conflict data** (ACLED, GDELT)
- **Climate & drought** (FAO WaPOR v3)
- **Humanitarian indicators** (IPC, DTM, IDMC, etc.)
- **Analytics & forecasting** (escalation risk, Goldstein trends)
- **Collaboration tooling** (analyst feedback, local actor inputs, belief state)

This README explains:

1. How to **set up and run** MERLx.
2. How to run **ETL / analysis scripts**.
3. How to **test every API endpoint** with `curl`.


---

## 1. Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **Vector Store**: Qdrant
- **ML / NLP**:
  - `sentence-transformers` (Alibaba-NLP/gte-multilingual-base)
  - `transformers`, `torch`
- **Geo / Climate**:
  - `geopandas`, `rasterio`, `shapely`, `pyproj`
  - WaPOR v3 via FAO GISMGR (no auth)
- **Other**:
  - `pandas`, `SQLAlchemy`, `alembic`
  - `python-dotenv` for `.env` loading

---

## 2. Project Layout (backend folder)

From the backend root (what you pasted):

```text
backend/
  app/
    config/
    models/
    services/
    utils/
  scripts/
    acled_backfill_last_year.py
    acled_sync_from_api.py
    add_country_iso3_to_analysis_runs.py
    gdelt_backfill_last_30_days.py
    gdelt_sync_from_api.py
    populate_vector_store.py
    wapor_drought_index.py
    compute_somalia_admin1_centroids.py
    gdelt/
      analyze_goldstein_trends.py
  create_tables.py
  populate_db.py
  requirements.txt
  ...
```

> All commands below assume you `cd` into the `backend/` directory.

---

## 3. Installation & Setup

### 3.1. Requirements

- Python 3.11+  
- PostgreSQL (with a database & user created)  
- (Optional) Qdrant running locally or hosted

### 3.2. Install dependencies

```bash
cd backend

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scriptsctivate

pip install -r requirements.txt
```



## 4. Database Setup

### 4.1. Create tables

```bash
cd backend
python create_tables.py
```

This initializes the core tables (GDELT, ACLED, analysis_runs, feedback, etc.)

### 4.2. (Optional) Populate DB from CSVs

If you have the CSVs referenced in `populate_db.py`:

```bash
python populate_db.py
```

> ⚠️ `populate_db.py` **TRUNCATES** `gdelt_events` and `acled_events` before inserting.

---

## 5. Running ETL & Analysis Scripts

All commands below are from `backend/`.

### 5.1. ACLED data – last year backfill

```bash
# Backfill last 365 days for default (from env or SDN)
python scripts/acled_backfill_last_year.py

# Backfill explicitly for Somalia
python scripts/acled_backfill_last_year.py --country SOM
```

### 5.2. ACLED incremental sync

```bash
# Sync for Sudan, using ACLED_BACKFILL_DAYS from `.env` for overlap
python scripts/acled_sync_from_api.py --country-iso3 SDN

# Sync for Somalia with custom backfill window
python scripts/acled_sync_from_api.py --country-iso3 SOM --backfill-days 3
```

### 5.3. GDELT – archive backfill last 30 days

```bash
# Sudan
python scripts/gdelt_backfill_last_30_days.py --country SDN

# Somalia
python scripts/gdelt_backfill_last_30_days.py --country SOM
```

### 5.4. GDELT – API incremental sync

```bash
# Sudan (default from env GDELT_COUNTRY_ISO3 if set)
python scripts/gdelt_sync_from_api.py --country SDN --days-back 7

# Somalia
python scripts/gdelt_sync_from_api.py --country SOM --days-back 7
```

### 5.5. Goldstein escalation analysis

Reads from DB (or CSV fallback) and writes processed files.

```bash
python scripts/gdelt/analyze_goldstein_trends.py
```

Outputs:

- `data/processed/goldstein_escalation_risk_SDN_YYYYMMDD.csv`
- `data/processed/goldstein_hourly_timeline_SDN_YYYYMMDD.csv`

### 5.6. Somalia admin1 centroids

Create `somalia_admin1_centroids.json` from a GeoJSON boundary file.

```bash
python scripts/compute_somalia_admin1_centroids.py
```

Outputs:

- `data/geo/somalia_admin1_centroids.json`

### 5.7. WaPOR-based drought index

Compute drought index per admin1 region.

```bash
# Sudan
python scripts/wapor_drought_index.py --country SDN

# Somalia
python scripts/wapor_drought_index.py --country SOM
```

Outputs:

- `data/processed/drought_index_wapor_sdn.csv`
- `data/processed/drought_index_wapor_som.csv` (etc.)

### 5.8. Populate vector store (Qdrant)

```bash
# Sudan
python scripts/populate_vector_store.py --country SDN

# Somalia
python scripts/populate_vector_store.py --country SOM
```

### 5.9. One-off migration: add country_iso3 to analysis_runs

```bash
python scripts/add_country_iso3_to_analysis_runs.py
```

---

## 6. Running the API Server

From `backend/`:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Assuming:

- FastAPI app is at `app/main.py` as `app = FastAPI(...)`.  
- Adjust module path if your main file is different.

Set a helper environment variable for the base URL:

```bash
export BASE_URL=http://localhost:8000
```

Open API docs:

- Swagger UI: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`
- Raw OpenAPI: `http://localhost:8000/openapi.json`

---

## 7. Testing API Endpoints with curl

Below are example `curl` commands for **every endpoint** you listed.  
Replace placeholders like `<run_id>`, `<region>`, `<region_name>` as needed.

> ⚠️ For POST endpoints, payloads are illustrative. For exact schema, check `/openapi.json` or `/docs`. If you get a `422 Unprocessable Entity`, adjust the JSON according to the schema.

### 7.1. Default / Health

**Root**

```bash
curl "$BASE_URL/"
```

**Health**

```bash
curl "$BASE_URL/health"
```

**OpenAPI**

```bash
curl "$BASE_URL/openapi.json"
```

---

### 7.2. Analytics

**GET /api/conflict-proneness**

```bash
curl "$BASE_URL/api/conflict-proneness?country_iso3=SDN"
```

**GET /api/conflict-risk**

```bash
curl "$BASE_URL/api/conflict-risk?country_iso3=SDN"
```

**GET /api/analytics**

```bash
curl "$BASE_URL/api/analytics?country_iso3=SDN"
```

**GET /api/monthly-trend**

```bash
curl "$BASE_URL/api/monthly-trend?country_iso3=SDN&months=12"
```

---

### 7.3. Dashboard

**GET /api/regions**

```bash
curl "$BASE_URL/api/regions?country_iso3=SDN"
```

**GET /api/dashboard**

```bash
curl "$BASE_URL/api/dashboard?country_iso3=SDN"
```

**GET /api/map-data**

```bash
curl "$BASE_URL/api/map-data?country_iso3=SDN"
```

---

### 7.4. Reports

**POST /api/generate-brief – Generate Brief**

```bash
curl -X POST "$BASE_URL/api/generate-brief"   -H "Content-Type: application/json"   -d '{
    "country_iso3": "SDN",
    "regions": ["Khartoum", "North Darfur"],
    "time_window_days": 30,
    "include_humanitarian": true,
    "include_climate": true
  }'
```

**GET /api/reports – List Reports**

```bash
curl "$BASE_URL/api/reports?region=Khartoum&source=local_actor&limit=50"
```

**POST /api/reports – Create Report**

```bash
curl -X POST "$BASE_URL/api/reports"   -H "Content-Type: application/json"   -d '{
    "region": "Khartoum",
    "source": "local_actor",
    "report_type": "FIELD_REPORT",
    "language": "en",
    "tags": ["market", "checkpoint"],
    "text": "Checkpoints reported on the main road into Khartoum.",
    "metadata": {
      "confidence": "medium"
    },
    "run_id": null,
    "created_by": "analyst@example.org"
  }'
```

**GET /api/reports/run/{run_id} – List Reports For Run**

```bash
RUN_ID="your-analysis-run-id"
curl "$BASE_URL/api/reports/run/$RUN_ID"
```

---

### 7.5. Alerts

> Note: the paths are `/api/api/...` as provided.

**GET /api/api/alerts**

```bash
curl "$BASE_URL/api/api/alerts?country_iso3=SDN"
```

**GET /api/api/alerts/conflict-proneness**

```bash
curl "$BASE_URL/api/api/alerts/conflict-proneness?country_iso3=SDN"
```

**GET /api/api/alerts/dashboard-stats**

```bash
curl "$BASE_URL/api/api/alerts/dashboard-stats?country_iso3=SDN"
```

---

### 7.6. Goldstein Escalation

**GET /api/goldstein/escalation-risk**

```bash
curl "$BASE_URL/api/goldstein/escalation-risk?country_iso3=SDN"
```

**GET /api/goldstein/timeline**

```bash
curl "$BASE_URL/api/goldstein/timeline?country_iso3=SDN&hours_back=72"
```

**GET /api/goldstein/top-risks**

```bash
curl "$BASE_URL/api/goldstein/top-risks?country_iso3=SDN&limit=10"
```

**GET /api/goldstein/events**

```bash
curl "$BASE_URL/api/goldstein/events?country_iso3=SDN&region=Khartoum&days_back=7"
```

**GET /api/goldstein/political-risk**

```bash
curl "$BASE_URL/api/goldstein/political-risk?country_iso3=SDN"
```

---

### 7.7. Intelligence

**GET /api/intelligence/health**

```bash
curl "$BASE_URL/api/intelligence/health"
```

**POST /api/intelligence/analyze**

```bash
curl -X POST "$BASE_URL/api/intelligence/analyze"   -H "Content-Type: application/json"   -d '{
    "country_iso3": "SDN",
    "query": "Summarize recent conflict dynamics in Khartoum and potential spillover.",
    "include_sources": true
  }'
```

**GET /api/intelligence/runs – List Runs**

```bash
curl "$BASE_URL/api/intelligence/runs?country_iso3=SDN&limit=20"
```

---

### 7.8. Trend Analysis

(You listed this block twice; endpoints are the same.)

**GET /api/trend/risk – Escalation risk summaries by region**

```bash
curl "$BASE_URL/api/trend/risk?country_iso3=SDN&days_back=90"
```

**GET /api/trend/forecast – Forecast for a specific region**

```bash
curl "$BASE_URL/api/trend/forecast?country_iso3=SDN&region=Khartoum&horizon_days=30"
```

---

### 7.9. Analysis

**POST /api/analysis/run – Run Conflict Analysis**

```bash
curl -X POST "$BASE_URL/api/analysis/run"   -H "Content-Type: application/json"   -d '{
    "country_iso3": "SDN",
    "regions": ["Khartoum", "North Darfur"],
    "time_window_days": 30,
    "include_climate": true,
    "include_humanitarian": true,
    "notes": "Baseline situation analysis."
  }'
```

**POST /api/analysis/scenario-run – Run Scenario Analysis**

```bash
curl -X POST "$BASE_URL/api/analysis/scenario-run"   -H "Content-Type: application/json"   -d '{
    "country_iso3": "SDN",
    "scenario_name": "Humanitarian corridors open",
    "regions": ["Khartoum"],
    "interventions": [
      {
        "region": "Khartoum",
        "type": "HUMANITARIAN_ACCESS",
        "intensity": "HIGH"
      }
    ],
    "time_horizon_days": 60
  }'
```

---

### 7.10. Collaboration

**POST /api/analysis/{run_id}/feedback – Submit feedback for a run**

```bash
RUN_ID="your-analysis-run-id"

curl -X POST "$BASE_URL/api/analysis/$RUN_ID/feedback"   -H "Content-Type: application/json"   -d '{
    "target": "SUMMARY",
    "feedback_type": "CORRECTION",
    "comment": "The situation in North Darfur is more severe than described.",
    "author": "analyst@example.org"
  }'
```

**GET /api/analysis/{run_id}/feedback – List feedback for a run**

```bash
curl "$BASE_URL/api/analysis/$RUN_ID/feedback"
```

**GET /api/regions/{region}/feedback – List feedback by region**

```bash
REGION="Khartoum"
curl "$BASE_URL/api/regions/$REGION/feedback"
```

**POST /api/regions/{region}/local-input – Submit local actor input**

```bash
REGION="Khartoum"

curl -X POST "$BASE_URL/api/regions/$REGION/local-input"   -H "Content-Type: application/json"   -d '{
    "role": "LOCAL_NGO",
    "author": "Local NGO Focal Point",
    "text": "Markets reopened in central Khartoum but supply chains remain constrained.",
    "metadata": {
      "confidence": "high"
    }
  }'
```

**GET /api/regions/{region}/local-input – List local actor inputs**

```bash
curl "$BASE_URL/api/regions/$REGION/local-input"
```

**POST /api/scenarios/preview – Scenario preview dashboard**

```bash
curl -X POST "$BASE_URL/api/scenarios/preview"   -H "Content-Type: application/json"   -d '{
    "country_iso3": "SDN",
    "regions": ["Khartoum"],
    "interventions": [
      {
        "region": "Khartoum",
        "type": "CEASEFIRE",
        "intensity": "MEDIUM"
      }
    ],
    "time_horizon_days": 30
  }'
```

---

### 7.11. Feedback (global)

**POST /api/feedback – Submit feedback**

```bash
curl -X POST "$BASE_URL/api/feedback"   -H "Content-Type: application/json"   -d '{
    "run_id": "your-analysis-run-id",
    "region": "Khartoum",
    "target": "SUMMARY",
    "feedback_type": "COMMENT",
    "comment": "The report is generally accurate but could highlight displacement more.",
    "author": "user@example.org"
  }'
```

**GET /api/feedback – List all feedback**

```bash
curl "$BASE_URL/api/feedback?run_id=your-analysis-run-id&region=Khartoum"
```

**GET /api/feedback/run/{run_id} – Feedback for a specific run**

```bash
RUN_ID="your-analysis-run-id"
curl "$BASE_URL/api/feedback/run/$RUN_ID"
```

**GET /api/feedback/region/{region} – Feedback for a region**

```bash
REGION="Khartoum"
curl "$BASE_URL/api/feedback/region/$REGION"
```

**GET /api/feedback/run/{run_id}/summary – Aggregated summary**

```bash
curl "$BASE_URL/api/feedback/run/$RUN_ID/summary"
```

---

### 7.12. Belief State

**GET /api/belief-state/region/{region} – Get Belief State**

```bash
REGION="Khartoum"
curl "$BASE_URL/api/belief-state/region/$REGION?country_iso3=SDN"
```

**POST /api/belief-state/baseline – Update Baseline**

```bash
curl -X POST "$BASE_URL/api/belief-state/baseline"   -H "Content-Type: application/json"   -d '{
    "country_iso3": "SDN",
    "region": "Khartoum",
    "baseline_risk": 6.5,
    "notes": "Baseline from latest integrated analysis."
  }'
```

**POST /api/belief-state/interventions – Apply Interventions**

```bash
curl -X POST "$BASE_URL/api/belief-state/interventions"   -H "Content-Type: application/json"   -d '{
    "country_iso3": "SDN",
    "region": "Khartoum",
    "interventions": [
      {
        "type": "HUMANITARIAN_SCALE_UP",
        "intensity": "HIGH"
      }
    ]
  }'
```

---

### 7.13. ACLED Events

**GET /api/events/acled**

```bash
curl "$BASE_URL/api/events/acled?country_iso3=SDN&region=Khartoum&days_back=30"
```

---

### 7.14. Humanitarian Layers

**GET /api/humanitarian/dtm – DTM layer**

```bash
curl "$BASE_URL/api/humanitarian/dtm?country_iso3=SDN"
```

**GET /api/humanitarian/ipc – IPC humanitarian layer**

```bash
curl "$BASE_URL/api/humanitarian/ipc?country_iso3=SDN"
```

**GET /api/humanitarian/idmc – IDMC displacement layer**

```bash
curl "$BASE_URL/api/humanitarian/idmc?country_iso3=SDN"
```

**GET /api/humanitarian/summary – Combined summary**

```bash
curl "$BASE_URL/api/humanitarian/summary?country_iso3=SDN"
```

---

### 7.15. Climate / Drought

**GET /api/climate/drought/ – List WaPOR drought index per region**

```bash
curl "$BASE_URL/api/climate/drought/?country_iso3=SDN"
```

**GET /api/climate/drought/top-driest – Top driest regions**

```bash
curl "$BASE_URL/api/climate/drought/top-driest?country_iso3=SDN&limit=10"
```

**GET /api/climate/drought/{region_name} – Drought info for one region**

```bash
REGION_NAME="North Darfur"
curl "$BASE_URL/api/climate/drought/$REGION_NAME?country_iso3=SDN"
```

(If your region has spaces, URL-encode: `North%20Darfur`.)

---

## 8. Notes & Troubleshooting

- If any `POST` call returns `422 Unprocessable Entity`, open:
  - `http://localhost:8000/docs` or `http://localhost:8000/openapi.json`
  - Check the exact request body schema (e.g. `AnalysisRequest`, `ScenarioRunRequest`).
- If DB-related errors occur:
  - Ensure `DATABASE_URL` is correct and `create_tables.py` has been run.
- For WaPOR / GISMGR issues:
  - Network must access `https://data.apps.fao.org/gismgr/api/v2`.
  - Double-check `WAPOR_RAIN_COLLECTION` (e.g. `L2-PCP-D`).
- For Qdrant:
  - Make sure `QDRANT_URL` is reachable.
  - Re-run `populate_vector_store.py` after new events are ingested.

---

