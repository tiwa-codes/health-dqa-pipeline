# Health DQA Report Generation - Run Log

## Date and Time
**Generated:** November 12, 2025, 02:05 UTC

## Purpose
This document logs all commands and scripts executed to generate the donor-facing health DQA report and associated figures.

---

## Data Preparation

### Step 1: Verify Raw Data
**Command:**
```bash
ls -la data/raw/
```

**Output:**
- `facility_registry.csv` - 1,200 facilities across 37 Nigerian states
- `facility_reports.csv` - 28,798 facility-month records (24 months)
- `indicator_definitions.csv` - Metadata for 11 health indicators

**Status:** ✓ Data files verified and ready for processing

---

## DQA Pipeline Execution

### Step 2: Run DQA Pipeline
**Command:**
```bash
python -m src.quality.dqa_pipeline \
  --in data/raw/facility_reports.csv \
  --registry data/raw/facility_registry.csv \
  --config config/dqa_config.yml \
  --out data/processed
```

**Pipeline Stages:**
1. Loaded configuration from `config/dqa_config.yml`
2. Loaded 28,798 facility-month records
3. Loaded 1,200 facility registry entries
4. Ran 6 quality checks:
   - Completeness check
   - Duplicate detection
   - Timeliness assessment
   - Outlier detection (MAD method)
   - Spike detection (month-over-month changes)
   - Consistency validation (5 business rules)
5. Computed quality scores (0-100 scale)
6. Generated summaries at facility, state, and national levels

**Output Files Created:**
- `data/processed/dqa_results_facility_month.csv` - Detailed scores per facility-month
- `data/processed/dqa_summary_facility.csv` - Facility-level aggregates
- `data/processed/dqa_summary_state.csv` - State-level aggregates
- `reports/metrics_summary.json` - Compact JSON summary

**Status:** ✓ Pipeline completed successfully

**Key Results:**
- National Overall Score: **90.2/100 (Grade A)**
- Total Records Processed: 28,262 (after deduplication)
- Date Range: 2024-01 to 2025-12 (24 months)

---

## Chart Generation

### Step 3: Generate Donor-Facing Charts
**Script:** `reporting-outputs/generate_donor_charts.py`

**Command:**
```bash
cd reporting-outputs
python generate_donor_charts.py
```

**Charts Created:**

1. **dqa-score-by-state.png**
   - Type: Horizontal bar chart
   - Size: 1200×675 pixels (8×4.5 inches at 150 DPI)
   - Content: Quality scores for all 37 states, color-coded by performance level
   - Data Source: `data/processed/dqa_summary_state.csv`
   - Features: 
     - Green bars (≥90): Excellent performance
     - Orange bars (80-89): Good performance
     - Red bars (<80): Needs improvement
     - Score labels on each bar
     - Reference lines at 80 and 90

2. **dqa-score-trend.png**
   - Type: Time series line chart
   - Size: 1200×675 pixels (8×4.5 inches at 150 DPI)
   - Content: Monthly trends for 4 key metrics (Jan 2024 - Dec 2025)
   - Metrics shown:
     - Overall Quality Score (blue solid line)
     - Completeness Score (green dashed line)
     - Timeliness Score (red dashed line)
     - Consistency Score (purple dashed line)
   - Data Source: `data/processed/dqa_results_facility_month.csv`
   - Features:
     - Reference line at 90 (excellence threshold)
     - Markers for data points
     - Legend with metric descriptions

**Status:** ✓ Both charts generated successfully

---

## Report Generation

### Step 4: Draft Donor Report
**File:** `reporting-outputs/health-dqa-report.md`

**Structure:**
- Title, project period, donor information, contact
- Executive Summary (3-5 key bullets with quantified results)
- Background (what we did - 1 paragraph)
- Key Findings (4-6 bullets with interpretation)
- Recommendations (3 prioritized, actionable)
- Next Steps & Timeline (quarterly milestones)
- Annex: Methods, data sources, technical notes

**Data Sources Used:**
- National scores from `reports/metrics_summary.json`
- State rankings from `data/processed/dqa_summary_state.csv`
- Issue counts from DQA pipeline summary
- Chart references: `figures/dqa-score-by-state.png` and `figures/dqa-score-trend.png`

**Status:** ✓ Report drafted

---

## PDF Conversion

### Step 5: Convert Markdown to PDF
**Command:**
```bash
pandoc health-dqa-report.md \
  -o health-dqa-report.pdf \
  --pdf-engine=xelatex \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  --highlight-style=tango
```

**Alternative (if pandoc not available):**
Use online converter (e.g., https://www.markdowntopdf.com) or print to PDF from browser.

**Status:** ✓ PDF generated

---

## Data Quality Checks Used

### 1. Completeness
- **Method:** Count non-missing values across 11 essential indicators
- **Threshold:** Flag if <95% complete
- **Weight:** 30% of overall score
- **Result:** 95.9% average completeness

### 2. Duplicates
- **Method:** Group by (facility_id, period), count records
- **Threshold:** Flag if count > 1
- **Weight:** 10% of overall score
- **Result:** 1.9% duplication rate (536 duplicates)

### 3. Timeliness
- **Method:** Calculate days late vs. 7-day deadline after month-end
- **Scoring:** Linear penalty for lateness
- **Weight:** 15% of overall score
- **Result:** 58.6% average timeliness score (71.7% of reports late)

### 4. Outliers
- **Method:** Modified Z-score using Median Absolute Deviation (MAD)
- **Threshold:** Flag if |mZ| > 3.5 (compared to state peers)
- **Weight:** 15% of overall score
- **Result:** 98.0% average (3.0% outlier rate)

### 5. Spikes
- **Method:** Month-over-month percent change
- **Threshold:** Flag if >150% increase or >50% decrease
- **Weight:** 15% of overall score
- **Result:** 88.6% average (2.4% spike rate)

### 6. Consistency
- **Method:** Check 5 business rules (e.g., penta3 ≤ penta1, anc4 ≤ anc1)
- **Threshold:** Flag any violations
- **Weight:** 15% of overall score
- **Result:** 99.1% average (4.5% violation rate)

---

## State Rankings

### Top 5 States (by Overall Score)
1. **Delta** - 94.5/100
2. **Ebonyi** - 94.4/100
3. **Edo** - 94.4/100
4. **Taraba** - 94.1/100
5. **Gombe** - 93.8/100

### Bottom 5 States (by Overall Score)
1. **Nasarawa** - 85.9/100
2. **Oyo** - 86.3/100
3. **Niger** - 86.4/100
4. **Bauchi** - 86.5/100
5. **Ogun** - 86.9/100

**Note:** All states scored above 80 (Grade B+ or better), indicating generally good data quality with room for targeted improvement.

---

## Issue Prevalence

| Issue Type | Records Flagged | Rate |
|------------|-----------------|------|
| Late submission | 20,259 | 71.7% |
| Incomplete data | 10,420 | 36.9% |
| Consistency violations | 1,267 | 4.5% |
| Outliers | 864 | 3.0% |
| Spikes | 691 | 2.4% |
| Duplicates | 536 | 1.9% |

**Key Insight:** Timeliness is the most pressing issue, with over 70% of reports submitted late.

---

## Reproducibility Notes

### To Regenerate This Report Locally:

1. **Clone repository:**
   ```bash
   git clone https://github.com/tiwa-codes/health-dqa-pipeline.git
   cd health-dqa-pipeline
   ```

2. **Install dependencies:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Generate synthetic data (if not already present):**
   ```bash
   python -m src.data.generate_synthetic_routine_data --facilities 1200 --months 24
   ```

4. **Run DQA pipeline:**
   ```bash
   python -m src.quality.dqa_pipeline \
     --in data/raw/facility_reports.csv \
     --registry data/raw/facility_registry.csv \
     --config config/dqa_config.yml \
     --out data/processed
   ```

5. **Generate charts:**
   ```bash
   cd reporting-outputs
   python generate_donor_charts.py
   ```

6. **Review outputs:**
   - Charts: `reporting-outputs/figures/*.png`
   - Report: `reporting-outputs/health-dqa-report.md`
   - Run log: `reporting-outputs/annex/run-log.md`

---

## Configuration Used

**File:** `config/dqa_config.yml`

**Key Settings:**
- Completeness minimum threshold: 95%
- Timeliness deadline: 7 days after month-end
- Outlier MAD threshold: 3.5
- Spike thresholds: +150% / -50%
- Quality score weights: Completeness (30%), Timeliness (15%), Outliers (15%), Spikes (15%), Consistency (15%), Duplicates (10%)

---

## Software Versions

- **Python:** 3.11+
- **pandas:** 2.0.0+
- **matplotlib:** 3.7.0+
- **seaborn:** 0.12.0+
- **numpy:** 1.24.0+
- **scipy:** 1.10.0+

---

## Data Privacy Note

**Important:** This report uses **synthetic data** generated for demonstration purposes. All facility names, locations, and health metrics are artificially generated and do not represent real facilities or data.

For production use with real data:
- Implement proper access controls and authentication
- Anonymize sensitive information
- Follow local data protection regulations (e.g., Nigeria Data Protection Regulation - NDPR)
- Obtain necessary approvals before sharing

---

## Contact and Support

For questions about this report or to reproduce with real data:
- **Technical Support:** [HMIS Technical Team]
- **Program Questions:** [Health Program Manager]
- **Data Requests:** [Data Governance Committee]

---

**End of Run Log**
