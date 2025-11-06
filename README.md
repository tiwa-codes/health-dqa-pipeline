# Health Data Quality Assessment Pipeline

A reproducible Data Quality Assessment (DQA) pipeline for routine health facility reports in Nigeria. This project implements comprehensive data quality checks, scoring, and interactive visualization for monthly facility data including immunization, ANC, deliveries, and OPD services.

## 📋 Project Overview

### Objective
Create a complete, automated pipeline to assess and report on the quality of routine health facility data, helping identify issues with completeness, timeliness, consistency, outliers, and data anomalies.

### Key Features
- **Comprehensive DQA Checks**: Completeness, duplicates, timeliness, outliers (MAD method), spikes, consistency
- **Quality Scoring**: 0-100 scores per facility-month with configurable weights
- **Multi-Level Summaries**: Facility, state, and national level aggregations
- **Interactive Dashboard**: Streamlit app with filters, charts, and data downloads
- **Synthetic Data Generation**: Realistic Nigerian health data with intentional quality issues
- **Reproducible**: Seeded random generation, configuration-driven, offline execution

### Data & Indicators

**Facility Types**: Primary Health Centers (PHC), General Hospitals

**Nigerian States**: 37 states/territories (36 states + FCT Abuja)

**Health Indicators**:
- `opd_visits`: Outpatient department visits
- `anc1_first_visit`: First antenatal care visit
- `anc4_visits`: Four or more ANC visits
- `facility_deliveries`: Deliveries at facility
- `bcg_doses`: BCG vaccine doses
- `penta1_doses`, `penta3_doses`: Pentavalent vaccine doses
- `measles1_doses`: Measles vaccine doses
- `fully_immunized_under1`: Fully immunized children under 1 year
- `vaccine_stockout_days`: Days with vaccine stockouts
- `eligible_under1_population`: Eligible population denominator

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone repository
git clone https://github.com/tiwa-codes/health-dqa-pipeline.git
cd health-dqa-pipeline

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Synthetic Data

```bash
python -m src.data.generate_synthetic_routine_data --facilities 1200 --months 24
```

This creates:
- `data/raw/facility_registry.csv`: 1,200 facilities across 37 states
- `data/raw/facility_reports.csv`: ~28,800 facility-month records
- `data/raw/indicator_definitions.csv`: Indicator metadata

### 3. Run DQA Pipeline

```bash
python -m src.quality.dqa_pipeline \
  --in data/raw/facility_reports.csv \
  --registry data/raw/facility_registry.csv \
  --config config/dqa_config.yml \
  --out data/processed
```

This produces:
- `data/processed/dqa_results_facility_month.csv`: Detailed quality scores
- `data/processed/dqa_summary_facility.csv`: Facility-level summary
- `data/processed/dqa_summary_state.csv`: State-level summary
- `reports/metrics_summary.json`: Compact JSON summary

### 4. Launch Dashboard

```bash
streamlit run dashboards/dqa_app.py
```

Opens interactive dashboard at http://localhost:8501

### 5. Explore Notebook

```bash
jupyter lab
# Open notebooks/01_dqa_walkthrough.ipynb
```

### 6. Run Tests

```bash
python -m pytest -q
```

## 📁 Project Structure

```
health-dqa-pipeline/
├── README.md
├── requirements.txt
├── .gitignore
├── config/
│   └── dqa_config.yml          # Configuration (thresholds, weights)
├── data/
│   ├── raw/                    # Generated synthetic data
│   │   ├── facility_registry.csv
│   │   ├── facility_reports.csv
│   │   └── indicator_definitions.csv
│   └── processed/              # DQA outputs
│       ├── dqa_results_facility_month.csv
│       ├── dqa_summary_facility.csv
│       └── dqa_summary_state.csv
├── src/
│   ├── utils/
│   │   ├── io.py              # File I/O helpers
│   │   └── dates.py           # Date/period utilities
│   ├── data/
│   │   └── generate_synthetic_routine_data.py
│   └── quality/
│       ├── rules.py           # DQA check functions
│       ├── metrics.py         # Scoring and aggregation
│       └── dqa_pipeline.py    # Pipeline orchestration
├── dashboards/
│   └── dqa_app.py             # Streamlit dashboard
├── notebooks/
│   └── 01_dqa_walkthrough.ipynb
├── docs/
│   ├── data_dictionary.md     # Field definitions
│   └── dqa_rules.md           # Check descriptions
├── reports/
│   ├── health_dqa_memo.md     # Policy-oriented memo
│   ├── metrics_summary.json   # Summary metrics
│   └── figures/               # Notebook outputs
└── tests/
    ├── test_rules.py
    └── test_metrics.py
```

## 🔍 DQA Checks

### 1. Completeness
- **What**: Percentage of required fields with non-missing values
- **Threshold**: 95% minimum
- **Score**: Directly proportional to completeness rate

### 2. Duplicates
- **What**: Multiple records for same facility-period
- **Detection**: Group by (facility_id, period)
- **Score**: 100 if no duplicates, 0 if duplicates exist

### 3. Timeliness
- **What**: Submission delay vs. due date (7 days after month end)
- **Score**: 100 if on-time, decreases with lateness
- **Formula**: Linear penalty up to 7 days late, then accelerated

### 4. Outliers
- **What**: Values significantly different from peer group (same state)
- **Method**: Modified Z-score using Median Absolute Deviation (MAD)
- **Threshold**: |mZ| > 3.5
- **Score**: 100 - (outlier_count × 20)

### 5. Spikes
- **What**: Sudden large month-over-month changes
- **Thresholds**: >150% increase or >50% decrease
- **Score**: 100 - (spike_count × 25)

### 6. Consistency
- **What**: Logical relationships between indicators
- **Rules**:
  - anc4_visits ≤ anc1_first_visit
  - facility_deliveries ≤ anc4_visits
  - penta3_doses ≤ penta1_doses
  - measles1_doses ≤ penta3_doses
  - fully_immunized_under1 ≤ measles1_doses
- **Score**: 100 - (violation_count × 20)

## ⚙️ Configuration

Edit `config/dqa_config.yml` to customize:

```yaml
thresholds:
  completeness_min: 0.95
  timeliness_due_days: 7
  outliers_mad_threshold: 3.5
  spikes_pct_change_hi: 1.5
  spikes_pct_change_lo: -0.5

weights:
  completeness: 30
  duplicates: 10
  timeliness: 15
  outliers: 15
  spikes: 15
  consistency: 15
```

## 📊 Dashboard Features

- **Filters**: State, LGA, facility type, ownership, period range
- **KPIs**: Overall score, completeness, timeliness, issue rate
- **Charts**:
  - State-level quality scores (bar chart)
  - Quality components (bar chart)
  - Time series trends
  - Issue distribution
- **Tables**: Facility performance with download
- **Detailed Analysis**: Outliers, spikes, consistency violations

## 📝 Documentation

- **Data Dictionary** (`docs/data_dictionary.md`): Field definitions and allowed values
- **DQA Rules** (`docs/dqa_rules.md`): Detailed check descriptions and formulas
- **Policy Memo** (`reports/health_dqa_memo.md`): Non-technical summary and recommendations

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_rules.py -v

# Run with coverage
python -m pytest --cov=src tests/
```

## 🔒 Privacy & Synthetic Data

**Important**: This project uses **synthetic data** for demonstration purposes. All facility names, locations, and health metrics are artificially generated and do not represent real facilities or data.

For production use with real data:
- Implement proper access controls and authentication
- Anonymize sensitive information
- Follow local data protection regulations
- Validate thresholds on real data distributions

## 📚 References

This pipeline follows best practices from:

- WHO Data Quality Review (DQR) Toolkit
- DHIS2 Data Quality Assessment modules
- National HMIS guidelines and standard operating procedures
- CDC Data Quality Assessment Framework

**Note**: This is a demonstration project using synthetic data. Thresholds and weights should be validated and adjusted based on real data characteristics and program requirements.

## 🤝 Contributing

This is a demonstration project. For production deployment:

1. Test with real data (sample)
2. Adjust thresholds based on baseline quality
3. Customize indicators and consistency rules
4. Add facility-specific contextual factors
5. Integrate with existing HMIS systems

## 📄 License

This project is provided as-is for educational and demonstration purposes.

## 👤 Author

Created for the Nigeria Health Data DQA Initiative

---

**Need Help?**

- Run with `--help` flag: `python -m src.quality.dqa_pipeline --help`
- Check logs in terminal output
- Review configuration in `config/dqa_config.yml`
- See examples in `notebooks/01_dqa_walkthrough.ipynb`