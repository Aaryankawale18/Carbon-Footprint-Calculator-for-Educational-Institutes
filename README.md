# Carbon Footprint Calculator for Educational Institutes

A production-grade, multipage Streamlit web application designed for academic sustainability offices, estate administrators, and green campus committees to calculate, monitor, analyze, and mitigate institutional greenhouse gas emissions.

---

## 1. Accounting Methodology & Emission Factors

Emissions are quantified in accordance with the international GHG Protocol Corporate Standard using the core activity-based formula:

$$\text{Emissions } (\text{kg CO}_2) = \text{Activity Data} \times \text{Emission Factor}$$

All output metrics are standardized in **kilograms of carbon dioxide equivalent ($\text{kg CO}_2$)**.

### Official Emission Factor Reference Table

| Category | Subcategory | Activity Unit | Factor Value ($\text{kg CO}_2\text{ / unit}$) | Regulatory / Scientific Source |
| :--- | :--- | :--- | :--- | :--- |
| **Electricity** | Grid | $\text{kWh}$ | $0.820$ | Central Electricity Authority (CEA 2023) |
| **Diesel Generator** | DG Set | $\text{Litre}$ | $2.680$ | IPCC Guidelines for National GHG Inventories |
| **Water** | Supply + Treatment | $\text{kL}$ ($1,000\text{ L}$) | $0.298$ | Central Pollution Control Board (CPCB) |
| **Transportation** | Two-wheeler | $\text{km}$ | $0.050$ | IPCC Mobile Combustion |
| **Transportation** | Car Petrol | $\text{km}$ | $0.120$ | IPCC Mobile Combustion |
| **Transportation** | Car Diesel | $\text{km}$ | $0.140$ | IPCC Mobile Combustion |
| **Transportation** | Bus | $\text{km}$ | $0.900$ | IPCC Fleet Average |

*Source file:* `data/emission_factors.csv`

---

## 2. Relational Data Model (SQLite)

The application enforces relational integrity via foreign keys (`PRAGMA foreign_keys = ON;`) and cascading deletes (`ON DELETE CASCADE`):

```
+--------------------+           +------------------------+           +----------------------+
|     institutes     |           |    monthly_records     |           |    transport_rows    |
+--------------------+           +------------------------+           +----------------------+
| id (PK)            | 1       * | id (PK)                | 1       * | id (PK)              |
| name (UNIQUE)      |<----------| institute_id (FK)      |<----------| record_id (FK)       |
| address            |           | month ("YYYY-MM")      |           | vehicle_type         |
| academic_year      |           | electricity_kwh        |           | vehicle_count        |
| total_students     |           | water_kl               |           | distance_km          |
| total_staff        |           | diesel_litres          |           | factor               |
| campus_area_sqft   |           | electricity_co2        |           | co2_kg               |
| created_at         |           | diesel_co2             |           +----------------------+
| updated_at         |           | water_co2              |
+--------------------+           | transport_co2          |
                                 | total_co2              |
                                 | created_at             |
                                 | updated_at             |
                                 | UNIQUE(inst_id, month) |
                                 +------------------------+
```

---

## 3. Tech Stack & Architecture

- **Runtime & UI:** Python 3.10+, Streamlit (multipage configuration under `pages/`)
- **Theme:** Configured via `.streamlit/config.toml` (institutional light palette, `#2E7D32` forest green accent, `#F3F8F4` secondary background, `#1B2A1F` dark typography)
- **Visualizations:** Plotly (`plotly.graph_objects`, `plotly_white` template, chronological categorical month axes)
- **Data & Computations:** Pandas, NumPy
- **Persistence:** SQLite (`sqlite3`) with explicit foreign key cascades
- **Sustainability Advisor:** Multi-provider architecture:
  - **Google Gemini** (`gemini-2.5-flash` via official `google-genai` SDK)
  - **Groq Cloud** (`llama-3.3-70b-versatile` via `groq` SDK)
  - **Built-in Campus Analytics Engine:** Instant, zero-crash local analytical advisor analyzing actual campus audit records, solar PV feasibility, and MoM deltas when in project-ID mode or offline.

### Repository Structure

```
carbon_app/
├── app.py                      # Institutional landing page & overview
├── pages/
│   ├── 1_Institute_Details.py  # Profile registration & estate parameters
│   ├── 2_Calculator.py         # Monthly utility input & instant audit dashboard
│   ├── 3_Data.py               # Historical records repository & CSV export
│   └── 4_Chatbot.py            # Groq-powered sustainability advisor
├── modules/
│   ├── __init__.py
│   ├── emission_factors.py     # CSV loader and factor lookup utilities
│   ├── calculator.py           # Core emission mathematical equations
│   ├── database.py             # SQLite persistence, schema, and queries
│   ├── charts.py               # Plotly figure builders (donut, bars, trends)
│   ├── results.py              # Shared, identical audit results renderer
│   ├── chatbot.py              # Groq system prompt builder & streaming client
│   └── ui.py                   # Institutional CSS, metric cards, shared selectors
├── data/
│   └── emission_factors.csv    # Official baseline emission factors
├── scripts/
│   └── seed_demo.py            # Demo institute & 3-month sample records
├── .streamlit/
│   └── config.toml             # Streamlit visual theme configuration
├── .env.example                # Example environment variables
├── .gitignore                  # Git exclude patterns
├── requirements.txt            # Python dependencies
└── README.md                   # System documentation and deployment guide
```

---

## 4. Local Setup & Execution

### 1. Clone or Navigate to the Repository

```bash
cd carbon_app
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (Optional for Chatbot)

Copy `.env.example` to `.env` and insert your Groq API key:

```bash
cp .env.example .env
```

Edit `.env`:
```ini
GROQ_API_KEY=gsk_your_actual_key_here
```

### 5. Seed Demonstration Data (Optional)

To immediately populate the system with a demo institute (*Greenfield Institute of Technology*) and 3 consecutive months of realistic utility records:

```bash
python scripts/seed_demo.py
```

### 6. Launch the Application

```bash
streamlit run app.py
```

The web application will open automatically at `http://localhost:8501`.

---

## 5. Deployment Guide (Render)

The application is structured for turnkey deployment on cloud container environments like [Render](https://render.com).

### Deployment Configuration

1. **Repository:** Push this repository to GitHub or GitLab.
2. **Service Type:** Select **Web Service**.
3. **Environment:** `Python 3`
4. **Build Command:**
   ```bash
   pip install -r requirements.txt
   ```
5. **Start Command:**
   ```bash
   streamlit run app.py --server.port $PORT --server.address 0.0.0.0
   ```
6. **Environment Variables:**
   - Add `GROQ_API_KEY` under the **Environment** tab with your Groq API key.

> **Important Persistence Note on Render Free Tier:**
> On Render's ephemeral free web service tier, local filesystem storage (including the SQLite `.db` file) resets when the service spins down due to inactivity. For production deployments requiring persistent SQLite data, attach a **Persistent Disk** on Render (e.g. mounted at `/data/carbon_footprint.db`) or configure an external database engine.
