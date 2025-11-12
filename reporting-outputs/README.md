# Health DQA Donor-Ready Report - Outputs

This directory contains the complete donor-facing report package for the Nigeria Health Data Quality Assessment.

## Deliverables

### Main Report
- **`health-dqa-report.md`** - 2-page donor report in Markdown format
- **`health-dqa-report.pdf`** - Professional PDF version (42KB)

### Figures
- **`figures/dqa-score-by-state.png`** - Bar chart showing quality scores for all 37 Nigerian states (1200×675 pixels, 130KB)
- **`figures/dqa-score-trend.png`** - Time series showing quality metric trends over 24 months (1200×675 pixels, 95KB)

### Documentation
- **`annex/run-log.md`** - Complete execution log with commands, outputs, and reproducibility instructions

### Scripts (for regeneration)
- **`generate_donor_charts.py`** - Python script to generate the two figures from DQA outputs
- **`convert_to_pdf.py`** - Python script to convert Markdown report to PDF

## Report Summary

**National Quality Score:** 90.2/100 (Grade A)

**Key Findings:**
- Strong completeness (95.9%) and consistency (99.1%)
- Timeliness challenge: 71.7% of reports late
- Geographic variation: 8.2-point gap between top/bottom states
- All states score ≥85.9, indicating good baseline quality

**Recommendations:**
1. Implement automated submission reminders (immediate, low-cost)
2. Strengthen built-in data validation (short-term, one-time cost)
3. Provide targeted support to bottom-performing states (phased, moderate cost)

## How to Regenerate

### Prerequisites
```bash
cd /path/to/health-dqa-pipeline
pip install -r requirements.txt
```

### Step 1: Run DQA Pipeline
```bash
python -m src.quality.dqa_pipeline \
  --in data/raw/facility_reports.csv \
  --registry data/raw/facility_registry.csv \
  --config config/dqa_config.yml \
  --out data/processed
```

### Step 2: Generate Charts
```bash
cd reporting-outputs
python generate_donor_charts.py
```

### Step 3: Convert to PDF (if modified)
```bash
python convert_to_pdf.py
```

## Data Sources

All analysis is based on:
- **1,200 facilities** across 37 Nigerian states
- **28,798 facility-month records** spanning 24 months (Jan 2024 - Dec 2025)
- **11 health indicators** including OPD, ANC, deliveries, and immunization

See `annex/run-log.md` for complete technical details.

## Usage

This report package is designed for:
- **Donor presentations** - Use PDF and figures
- **Stakeholder briefings** - Reference key findings
- **Technical audiences** - Review annex and run-log
- **Reproducibility** - Follow instructions in run-log.md

## Data Privacy Note

⚠️ **Important:** This report is based on synthetic data for demonstration purposes. For production use with real facility data, ensure compliance with Nigeria Data Protection Regulation (NDPR) and health data privacy requirements.

## Contact

For questions or to reproduce with real data:
- Technical Support: [HMIS Technical Team]
- Program Questions: [Health Program Manager]

---

**Generated:** November 12, 2025  
**Version:** 1.0  
**Repository:** tiwa-codes/health-dqa-pipeline
