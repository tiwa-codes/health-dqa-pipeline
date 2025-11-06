# Data Quality Assessment Rules

## Overview

This document describes the six data quality checks implemented in the DQA pipeline, their rationale, calculation methods, thresholds, and interpretation guidance.

---

## 1. Completeness Check

### Purpose
Measure the extent to which required data fields are populated (non-missing).

### Rationale
Missing data prevents accurate analysis, target-setting, and performance monitoring. High completeness is foundational for data use.

### Method

**For each facility-month:**

1. Count total essential fields (excluding identifiers): typically 11 indicators
2. Count fields with non-missing values
3. Calculate: `completeness_rate = non_missing / total_fields`
4. Flag if `completeness_rate < threshold` (default: 0.95 or 95%)

### Scoring Formula

```
completeness_score = completeness_rate × 100
```

**Range**: 0-100 (directly proportional to completeness rate)

### Configuration

```yaml
thresholds:
  completeness_min: 0.95  # Flag if below 95%

essential_columns:
  - opd_visits
  - anc1_first_visit
  - ... (all indicators)
```

### Interpretation

| Score Range | Interpretation | Action |
|-------------|----------------|--------|
| 95-100 | Excellent | Maintain practices |
| 85-94.9 | Good | Minor improvement needed |
| 70-84.9 | Fair | Review data collection |
| <70 | Poor | Urgent intervention |

### Common Causes of Low Completeness
- Incomplete forms at submission
- Data entry errors or skipped fields
- Service not provided (vs. data not recorded)
- System/network issues during submission

---

## 2. Duplicate Detection

### Purpose
Identify facility-months with multiple records, indicating duplicate submissions.

### Rationale
Duplicates inflate counts, skew analysis, and indicate process issues (double entry, system errors).

### Method

**For each facility-month:**

1. Group by `(facility_id, period)`
2. Count records per group
3. Flag if count > 1
4. Record `duplicate_count` per facility-month

### Scoring Formula

```
duplicates_score = 100 if no duplicates, else 0
```

**Binary**: Either 100 (clean) or 0 (has duplicates)

### Configuration

No configurable thresholds (presence/absence).

### Interpretation

| Score | Interpretation | Action |
|-------|----------------|--------|
| 100 | No duplicates | Normal |
| 0 | Duplicates exist | Investigate and deduplicate |

### Common Causes of Duplicates
- Accidental double submission
- System errors (timeouts, retries)
- Offline-online sync issues
- Multiple users entering same month

### Handling Duplicates in Analysis
The pipeline flags duplicates but does not automatically remove them. Downstream analysis should:
- Keep only the latest submission (by `submission_date`)
- Or manually review and choose correct record
- Document deduplication rules

---

## 3. Timeliness Check

### Purpose
Assess whether reports are submitted on time according to submission deadlines.

### Rationale
Timely data is critical for outbreak response, supply chain, and monthly reviews. Late data limits decision-making.

### Method

**For each facility-month:**

1. Calculate `due_date = period_end + due_days` (default: 7 days)
   - Example: February 2024 ends Feb 29; due date is March 7
2. Calculate `days_late = submission_date - due_date`
   - Negative if early, zero if on-time, positive if late
3. Flag if `days_late > 0`

### Scoring Formula

```python
if days_late <= 0:
    score = 100  # On-time or early
elif days_late <= 7:
    score = 100 - (days_late / 7) × 50  # Linear decrease to 50
else:
    score = max(0, 50 - (days_late - 7) × 5)  # Further penalty
```

**Examples**:
- 0 days late: 100
- 3 days late: 78.6
- 7 days late: 50
- 10 days late: 35
- 17 days late: 0

### Configuration

```yaml
thresholds:
  timeliness_due_days: 7  # Days after month-end
```

### Interpretation

| Score Range | Interpretation | Lateness |
|-------------|----------------|----------|
| 90-100 | Excellent | ≤1 day |
| 70-89.9 | Good | 2-4 days |
| 50-69.9 | Fair | 5-10 days |
| <50 | Poor | >10 days |

### Common Causes of Lateness
- Facility staffing constraints
- Internet/connectivity issues
- Monthly workload peaks
- Lack of timely feedback/incentives
- State/LGA review delays

---

## 4. Outlier Detection

### Purpose
Identify values that are unusually high or low compared to peer facilities.

### Rationale
Outliers may indicate:
- Data entry errors (extra zero, decimal misplacement)
- Exceptional events (campaigns, outbreaks)
- Fraud or fabrication
- Unique facility characteristics

### Method

**Modified Z-Score using Median Absolute Deviation (MAD)**:

1. **Peer Grouping**: Group facilities by state (or other peer variable)
2. **For each indicator in each state**:
   - Calculate median: `M = median(values)`
   - Calculate MAD: `MAD = median(|values - M|)`
   - Calculate modified Z-score: `mZ = 0.6745 × (value - M) / MAD`
3. **Flag if** `|mZ| > threshold` (default: 3.5)

**Why MAD over standard deviation?**
- Robust to existing outliers
- Doesn't assume normal distribution
- Common in epidemiological surveillance

### Scoring Formula

```
outliers_score = max(0, 100 - outlier_count × 20)
```

**Per facility-month**: Count indicators flagged as outliers.

**Examples**:
- 0 outliers: 100
- 1 outlier: 80
- 2 outliers: 60
- 5+ outliers: 0

### Configuration

```yaml
thresholds:
  outliers_mad_threshold: 3.5
```

**Interpretation of Modified Z-Score**:
- |mZ| < 2: Normal variation
- 2 ≤ |mZ| < 3.5: Moderately unusual
- |mZ| ≥ 3.5: Highly unusual (flagged)

### Interpretation

| Outlier Count | Interpretation | Action |
|---------------|----------------|--------|
| 0 | Normal | None |
| 1 | Minor concern | Review specific indicator |
| 2-3 | Moderate concern | Verify data entry |
| 4+ | High concern | Contact facility |

### Common Causes of Outliers
- Decimal point errors (1,200 entered as 12,000)
- Transposed digits (123 vs. 132)
- Catch-up campaigns (e.g., mass immunization)
- Facility serves large catchment (genuine outlier)
- Stockout followed by surge

---

## 5. Spike Detection

### Purpose
Detect sudden, large month-over-month changes in indicators.

### Rationale
Spikes may indicate:
- Data entry errors
- System errors (duplicate additions)
- Programmatic changes (campaigns)
- Catch-up after stockout
- Seasonal variation (beyond normal)

### Method

**For each facility and indicator:**

1. Sort records by period
2. Calculate month-over-month percent change:
   ```
   pct_change = (curr_value - prev_value) / prev_value
   ```
3. Flag if:
   - `pct_change > pct_change_hi` (default: 1.5 = 150% increase)
   - OR `pct_change < pct_change_lo` (default: -0.5 = 50% decrease)

**Handle edge cases**:
- If `prev_value = 0` and `curr_value > 0`: treat as infinite increase (flag)
- If both zero: no change (don't flag)

### Scoring Formula

```
spikes_score = max(0, 100 - spike_count × 25)
```

**Per facility-month**: Count indicators with spikes.

**Examples**:
- 0 spikes: 100
- 1 spike: 75
- 2 spikes: 50
- 4+ spikes: 0

### Configuration

```yaml
thresholds:
  spikes_pct_change_hi: 1.5   # 150% increase
  spikes_pct_change_lo: -0.5  # 50% decrease
```

### Interpretation

| Spike Count | Interpretation | Action |
|-------------|----------------|--------|
| 0 | Normal | None |
| 1 | Minor concern | Review indicator |
| 2-3 | Moderate concern | Verify and document reason |
| 4+ | High concern | Contact facility urgently |

### Common Causes of Spikes
- Data entry errors (typo, duplicate addition)
- Campaigns or outreach events
- Service resumption after closure/stockout
- Batch data entry (multiple months entered once)
- Population influx (displacement, events)

---

## 6. Consistency Check

### Purpose
Enforce logical relationships and domain constraints between related indicators.

### Rationale
Inconsistencies violate program logic and indicate:
- Data entry errors
- Misunderstanding of indicator definitions
- System errors (field mix-ups)

### Method

**Business rules enforced:**

1. **anc4_visits ≤ anc1_first_visit**
   - Women with 4+ visits must first have an ANC1 visit
   
2. **facility_deliveries ≤ anc4_visits**
   - Facility deliveries expected to be subset of ANC4 (women receiving comprehensive care)
   
3. **penta3_doses ≤ penta1_doses**
   - Children receiving 3rd dose must have received 1st dose
   
4. **measles1_doses ≤ penta3_doses**
   - Measles typically given after Penta series (age 9 months vs 6,10,14 weeks)
   
5. **fully_immunized_under1 ≤ measles1_doses**
   - Fully immunized requires measles dose

**For each facility-month:**

1. Check each rule
2. Count violations
3. Record violation details
4. Flag if any violations exist

### Scoring Formula

```
consistency_score = max(0, 100 - violation_count × 20)
```

**Examples**:
- 0 violations: 100
- 1 violation: 80
- 2 violations: 60
- 5+ violations: 0

### Configuration

Rules are hard-coded based on program logic. Future versions could make rules configurable.

### Interpretation

| Violation Count | Interpretation | Action |
|----------------|----------------|--------|
| 0 | Consistent | None |
| 1 | Minor issue | Review specific relationship |
| 2-3 | Moderate issue | Verify data entry |
| 4+ | Major issue | Contact facility, retrain |

### Common Causes of Inconsistencies
- Indicator definition confusion
- Field label mix-ups during entry
- Copy-paste errors
- Transposed columns
- Reporting from different registers

---

## Overall Quality Score

### Weighted Composite Score

The overall score combines all sub-scores using configurable weights:

```
overall_score = Σ (sub_score × weight / 100)
```

**Default weights:**

| Component | Weight |
|-----------|--------|
| Completeness | 30% |
| Duplicates | 10% |
| Timeliness | 15% |
| Outliers | 15% |
| Spikes | 15% |
| Consistency | 15% |
| **Total** | **100%** |

### Configuration

```yaml
weights:
  completeness: 30
  duplicates: 10
  timeliness: 15
  outliers: 15
  spikes: 15
  consistency: 15
```

### Grade Conversion

| Score | Grade | Interpretation |
|-------|-------|----------------|
| 95-100 | A+ | Excellent quality |
| 90-94.9 | A | Very good |
| 85-89.9 | A- | Good |
| 80-84.9 | B+ | Above average |
| 75-79.9 | B | Average |
| 70-74.9 | B- | Below average |
| 65-69.9 | C+ | Fair |
| 60-64.9 | C | Needs improvement |
| 55-59.9 | C- | Poor |
| 50-54.9 | D | Very poor |
| <50 | F | Unacceptable |

---

## Recommendations by Score Range

### A-range (85-100)
- **Action**: Maintain current practices
- **Frequency**: Quarterly DQA reviews
- **Recognition**: Share best practices

### B-range (70-84.9)
- **Action**: Targeted improvements on low components
- **Frequency**: Monthly monitoring
- **Support**: Refresher training, feedback

### C-range (60-69.9)
- **Action**: Comprehensive intervention
- **Frequency**: Weekly monitoring
- **Support**: Mentorship, on-site support

### D/F range (<60)
- **Action**: Urgent remediation
- **Frequency**: Daily monitoring
- **Support**: Intensive mentorship, investigation

---

## Threshold Adjustment Guidance

### When to Adjust Thresholds

1. **Baseline Period**: Run on 3-6 months of data to establish baseline
2. **Context Factors**: Rural vs. urban, facility size, internet access
3. **Programmatic Changes**: New systems, campaigns, training
4. **Indicator-Specific**: Some indicators naturally more variable

### How to Adjust

```yaml
# Start strict, loosen if needed
outliers_mad_threshold: 3.5  # Try 4.0 if too many false positives
spikes_pct_change_hi: 1.5    # Try 2.0 for naturally variable indicators
completeness_min: 0.95       # Try 0.90 during transition periods
```

**Important**: Document all threshold changes and rationale.

---

## Limitations and Caveats

1. **Synthetic Data**: Current thresholds tuned to synthetic data. Real data may differ.

2. **Peer Groups**: State-level grouping may not account for facility size, type, catchment differences.

3. **Seasonality**: Seasonal patterns (malaria, flu) may trigger false spike flags.

4. **Campaigns**: Mass campaigns will trigger outliers and spikes (expected and acceptable).

5. **Data Entry Timing**: Batch entry of multiple months may appear as spikes.

6. **Context Matters**: Flags are signals for investigation, not automatic data rejection.

### Using DQA Results

**✓ DO:**
- Investigate flagged records
- Contact facilities for clarification
- Document explanations (campaigns, etc.)
- Use scores for targeted support
- Track improvement over time

**✗ DON'T:**
- Automatically reject flagged data
- Punish facilities for low scores (early on)
- Ignore contextual factors
- Use scores for high-stakes decisions without verification

---

## References

- WHO. (2017). *Data Quality Review (DQR) Toolkit*
- MEASURE Evaluation. (2018). *Routine Data Quality Assessment Tool*
- CDC. (2020). *Data Quality Assessment Framework*
- DHIS2. *Data Quality App Documentation*

---

*This is a living document. Update thresholds and rules based on program experience and validation.*
