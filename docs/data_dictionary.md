# Data Dictionary

## Facility Registry (`facility_registry.csv`)

Complete reference table for all health facilities in the system.

| Field | Type | Description | Allowed Values | Example |
|-------|------|-------------|----------------|---------|
| `facility_id` | String | Unique facility identifier | FAC00001 - FAC99999 | FAC00123 |
| `facility_name` | String | Official facility name | Any text | Lagos PHC 42 |
| `state` | String | Nigerian state | 37 Nigerian states (see config) | Lagos |
| `lga` | String | Local Government Area | State + direction | Lagos South |
| `facility_type` | String | Type of facility | PHC, General Hospital | PHC |
| `ownership` | String | Ownership category | Public, Private | Public |
| `latitude` | Float | Geographic latitude | 4.0 to 14.0 | 6.524379 |
| `longitude` | Float | Geographic longitude | 3.0 to 15.0 | 3.379206 |

**Row Count**: 1,200 facilities (configurable)

---

## Facility Reports (`facility_reports.csv`)

Monthly service delivery data submitted by facilities.

### Identification Fields

| Field | Type | Description | Allowed Values | Example |
|-------|------|-------------|----------------|---------|
| `facility_id` | String | Facility identifier (FK to registry) | FAC00001 - FAC99999 | FAC00123 |
| `period` | String | Reporting month | YYYY-MM format | 2024-06 |
| `submission_date` | Date | Date report was submitted | YYYY-MM-DD format | 2024-07-05 |

### Service Indicators

| Field | Type | Description | Unit | Expected Range | Constraints |
|-------|------|-------------|------|----------------|-------------|
| `opd_visits` | Integer | Total outpatient department visits | visits | 200-10,000 | >= 0 |
| `anc1_first_visit` | Integer | First antenatal care visit | visits | 10-600 | >= anc4_visits |
| `anc4_visits` | Integer | Four or more ANC visits | visits | 5-400 | <= anc1_first_visit |
| `facility_deliveries` | Integer | Deliveries at facility | deliveries | 5-400 | <= anc4_visits |
| `bcg_doses` | Integer | BCG vaccine doses administered | doses | 10-800 | >= 0 |
| `penta1_doses` | Integer | First pentavalent vaccine dose | doses | 10-800 | >= penta3_doses |
| `penta3_doses` | Integer | Third pentavalent vaccine dose | doses | 5-700 | <= penta1_doses |
| `measles1_doses` | Integer | First measles vaccine dose | doses | 5-700 | <= penta3_doses |
| `fully_immunized_under1` | Integer | Fully immunized children <1 year | children | 5-700 | <= measles1_doses |
| `vaccine_stockout_days` | Integer | Days with vaccine stockouts | days | 0-30 | 0-31 |
| `eligible_under1_population` | Integer | Estimated population under 1 year | children | 50-1,200 | > 0, stable |

**Row Count**: ~28,800 for 1,200 facilities × 24 months (with ~2% missing reports)

**Missingness**: Individual indicators have 3-7% missing values to simulate data quality issues.

**Duplicates**: ~1-2% of facility-months have duplicate records.

---

## Indicator Definitions (`indicator_definitions.csv`)

Reference table with indicator metadata.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `indicator` | String | Indicator code (column name) | opd_visits |
| `description` | String | Human-readable description | Total outpatient department visits |
| `unit` | String | Unit of measurement | visits |
| `expected_constraints` | String | Business rules and valid ranges | Range: 200-10000; No negative values |

**Row Count**: 11 indicators

---

## DQA Results - Facility-Month Level (`dqa_results_facility_month.csv`)

Detailed quality assessment results for each facility-month combination.

### Identification

| Field | Type | Description |
|-------|------|-------------|
| `facility_id` | String | Facility identifier |
| `period` | String | Reporting month (YYYY-MM) |

### Quality Scores (0-100)

| Field | Type | Description | Interpretation |
|-------|------|-------------|----------------|
| `completeness_score` | Float | Completeness sub-score | 100 = all fields present, 0 = all missing |
| `duplicates_score` | Float | Duplicates sub-score | 100 = no duplicates, 0 = duplicates exist |
| `timeliness_score` | Float | Timeliness sub-score | 100 = on-time, decreases with lateness |
| `outliers_score` | Float | Outliers sub-score | 100 = no outliers, -20 per outlier indicator |
| `spikes_score` | Float | Spikes sub-score | 100 = no spikes, -25 per spike indicator |
| `consistency_score` | Float | Consistency sub-score | 100 = no violations, -20 per violation |
| `overall_score` | Float | Weighted overall score | Composite of all sub-scores |

### Quality Flags (Boolean)

| Field | Type | Description | Values |
|-------|------|-------------|--------|
| `flag_incomplete` | Boolean | Completeness below threshold | True/False |
| `flag_duplicate` | Boolean | Duplicate record exists | True/False |
| `flag_late` | Boolean | Submitted late | True/False |
| `flag_outlier` | Boolean | Has outlier indicator(s) | True/False |
| `flag_spike` | Boolean | Has spike indicator(s) | True/False |
| `flag_inconsistent` | Boolean | Has consistency violation(s) | True/False |

---

## DQA Summary - Facility Level (`dqa_summary_facility.csv`)

Aggregated quality metrics per facility.

| Field | Type | Description | Calculation |
|-------|------|-------------|-------------|
| `facility_id` | String | Facility identifier | - |
| `num_periods` | Integer | Number of reporting periods | Count of facility-months |
| `overall_score` | Float | Average overall quality score | Mean across periods |
| `completeness_score` | Float | Average completeness score | Mean across periods |
| `timeliness_score` | Float | Average timeliness score | Mean across periods |
| `outliers_score` | Float | Average outliers score | Mean across periods |
| `spikes_score` | Float | Average spikes score | Mean across periods |
| `consistency_score` | Float | Average consistency score | Mean across periods |
| `incomplete_rate` | Float | Proportion of periods flagged incomplete | Sum(flag) / num_periods |
| `late_rate` | Float | Proportion of periods submitted late | Sum(flag) / num_periods |
| `outlier_rate` | Float | Proportion of periods with outliers | Sum(flag) / num_periods |
| `spike_rate` | Float | Proportion of periods with spikes | Sum(flag) / num_periods |
| `inconsistent_rate` | Float | Proportion of periods with violations | Sum(flag) / num_periods |

---

## DQA Summary - State Level (`dqa_summary_state.csv`)

Aggregated quality metrics per state.

| Field | Type | Description | Calculation |
|-------|------|-------------|-------------|
| `state` | String | Nigerian state name | - |
| `num_facilities` | Integer | Number of facilities in state | Unique facility count |
| `num_records` | Integer | Total facility-month records | Count of records |
| `overall_score` | Float | Average overall quality score | Mean across all facility-months |
| `completeness_score` | Float | Average completeness score | Mean across all facility-months |
| `timeliness_score` | Float | Average timeliness score | Mean across all facility-months |
| `outliers_score` | Float | Average outliers score | Mean across all facility-months |
| `spikes_score` | Float | Average spikes score | Mean across all facility-months |
| `consistency_score` | Float | Average consistency score | Mean across all facility-months |
| `incomplete_rate` | Float | Proportion flagged incomplete | Sum(flag) / num_records |
| `late_rate` | Float | Proportion submitted late | Sum(flag) / num_records |
| `outlier_rate` | Float | Proportion with outliers | Sum(flag) / num_records |
| `spike_rate` | Float | Proportion with spikes | Sum(flag) / num_records |
| `inconsistent_rate` | Float | Proportion with violations | Sum(flag) / num_records |

---

## Metrics Summary JSON (`metrics_summary.json`)

Compact JSON summary for programmatic access.

```json
{
  "generated_at": "ISO 8601 timestamp",
  "total_facilities": 1200,
  "total_records": 28800,
  "national_scores": {
    "overall_score": 75.5,
    "completeness_score": 92.3,
    ...
  },
  "issue_counts": {
    "incomplete": 245,
    "late": 1234,
    ...
  },
  "top_5_facilities": [...],
  "bottom_5_facilities": [...],
  "top_5_states": [...],
  "bottom_5_states": [...],
  "data_quality_grade": "B+"
}
```

---

## Intermediate Check Results

The pipeline generates intermediate results (not typically used directly):

### Completeness Check Output
- `facility_id`, `period`, `check_name`, `completeness_rate`, `missing_count`, `total_fields`, `flag_incomplete`

### Duplicates Check Output
- `facility_id`, `period`, `check_name`, `duplicate_count`, `flag_duplicate`

### Timeliness Check Output
- `facility_id`, `period`, `check_name`, `days_late`, `flag_late`

### Outliers Check Output (per indicator)
- `facility_id`, `period`, `indicator`, `check_name`, `value`, `peer_median`, `modified_z_score`, `flag_outlier`

### Spikes Check Output (per indicator)
- `facility_id`, `period`, `indicator`, `check_name`, `prev_value`, `curr_value`, `pct_change`, `flag_spike`

### Consistency Check Output
- `facility_id`, `period`, `check_name`, `violation_count`, `violations`, `violation_details`, `flag_inconsistent`

---

## Data Quality Grades

Quality scores are converted to letter grades:

| Score Range | Grade |
|-------------|-------|
| 95-100 | A+ |
| 90-94.9 | A |
| 85-89.9 | A- |
| 80-84.9 | B+ |
| 75-79.9 | B |
| 70-74.9 | B- |
| 65-69.9 | C+ |
| 60-64.9 | C |
| 55-59.9 | C- |
| 50-54.9 | D |
| <50 | F |

---

## Notes

1. **Synthetic Data**: All data is artificially generated. Real-world distributions may differ.

2. **Missing Values**: Represented as `NaN` or null in CSV files. Missing values are intentional in synthetic data to simulate quality issues.

3. **Duplicates**: Some facility-month combinations appear multiple times to simulate duplicate submissions.

4. **Time Periods**: Default generation spans 24 months (configurable).

5. **Geographic Coordinates**: Approximate random coordinates within Nigeria bounds. Not precise facility locations.

6. **Consistency Rules**: Domain-specific rules based on program logic (e.g., penta3 should not exceed penta1).

7. **Peer Groups**: Outlier detection uses state-level peer grouping. Other groupings (facility type, LGA) could be configured.
