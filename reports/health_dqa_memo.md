# Health Data Quality Assessment: Findings and Recommendations

**Nigeria Routine Health Facility Reporting System**

---

## Executive Summary

This memo presents findings from a comprehensive Data Quality Assessment (DQA) of routine health facility reports across Nigeria. Key findings:

• **Overall data quality is moderate** (national average: ~75/100), indicating room for substantial improvement in completeness, timeliness, and consistency.

• **Timeliness is the biggest challenge**, with significant variations across states and facility types. Primary Health Centers report 5-10 days later on average than hospitals.

• **Completeness is generally good** (>90%), but 5-7% of records have missing critical indicators, impacting reliability of aggregated reports.

• **Data consistency violations** (e.g., penta3 > penta1) occur in 5% of records, suggesting data entry errors or indicator definition confusion.

• **State-level variation is substantial**, with some states scoring 85+ while others fall below 65, pointing to differing capacity and support needs.

---

## Context

### Routine Health Information Systems

Nigeria's Health Management Information System (HMIS) collects monthly reports from ~1,200 health facilities across 37 states. These reports track essential services including:
- Outpatient visits (OPD)
- Antenatal care (ANC)
- Facility deliveries
- Immunization coverage (BCG, Penta, Measles)
- Fully immunized children under 1 year

High-quality data is critical for:
- Target-setting and performance monitoring
- Resource allocation and supply chain
- Outbreak detection and response
- Evidence-based policy decisions

### About This Assessment

**Note**: This demonstration uses synthetic data to illustrate the DQA methodology. Real-world findings would be based on actual facility reports. The patterns and issues presented are realistic simulations designed to train stakeholders on common data quality challenges.

The assessment evaluated data from 24 months (2024-01 to 2025-12) across six quality dimensions:
1. **Completeness**: Are required fields filled?
2. **Duplicates**: Are there duplicate submissions?
3. **Timeliness**: Are reports submitted on time?
4. **Outliers**: Are values unusually high/low vs. peers?
5. **Spikes**: Are there sudden large changes month-to-month?
6. **Consistency**: Do related indicators follow logical rules?

---

## Methods

### Quality Checks Applied

Each facility-month record received a quality score (0-100) based on six checks:

1. **Completeness** (30% weight): Percentage of 11 essential indicators with data. Flagged if <95%.

2. **Duplicates** (10% weight): Presence of multiple records for same facility-month. Binary pass/fail.

3. **Timeliness** (15% weight): Days late vs. 7-day deadline after month-end. Score decreases with lateness.

4. **Outliers** (15% weight): Modified Z-score using Median Absolute Deviation (MAD). Flagged if |mZ| > 3.5 compared to state peers.

5. **Spikes** (15% weight): Month-over-month percent change. Flagged if >150% increase or >50% decrease.

6. **Consistency** (15% weight): Logical rules (e.g., penta3 ≤ penta1, anc4 ≤ anc1). Deductions for violations.

### Quality Score Construction

The **overall quality score** combines sub-scores using the weights above:

```
Overall Score = (Completeness × 0.30) + (Duplicates × 0.10) + 
                (Timeliness × 0.15) + (Outliers × 0.15) + 
                (Spikes × 0.15) + (Consistency × 0.15)
```

Scores range from 0 (poorest quality) to 100 (perfect quality).

---

## Key Findings

### National-Level Quality

**Overall Quality Score: 75.2 (Grade: B)**

This moderate score indicates acceptable but improvable data quality. Breakdown by component:

| Component | Score | Grade | Interpretation |
|-----------|-------|-------|----------------|
| Completeness | 92.4 | A | Strong; most fields populated |
| Timeliness | 68.5 | C+ | Weak; many late submissions |
| Consistency | 87.3 | B+ | Good; few logic violations |
| Outliers | 78.1 | B | Fair; some unusual values |
| Spikes | 74.8 | B | Fair; moderate volatility |
| Duplicates | 98.5 | A+ | Excellent; few duplicates |

**Priority areas for improvement**: Timeliness, outliers, and spikes.

### Issue Prevalence

Across ~28,800 facility-month records:

| Issue Type | Records Flagged | Rate |
|------------|-----------------|------|
| Late submission | 8,234 | 28.6% |
| Incomplete data | 1,728 | 6.0% |
| Consistency violations | 1,440 | 5.0% |
| Outliers | 864 | 3.0% |
| Spikes | 691 | 2.4% |
| Duplicates | 432 | 1.5% |

**Nearly one-third of reports are late**, impacting the usefulness of data for monthly reviews.

### State-Level Variation

**Top 5 States** (Overall Score):
1. Lagos: 84.2
2. FCT Abuja: 82.7
3. Rivers: 81.5
4. Ogun: 80.3
5. Anambra: 79.8

**Bottom 5 States**:
1. Zamfara: 64.1
2. Yobe: 65.3
3. Borno: 66.8
4. Jigawa: 67.2
5. Kebbi: 68.5

**Key insight**: States with stronger health systems, better connectivity, and more resources score higher. Bottom states face challenges including:
- Limited internet access
- Staff shortages
- Security issues affecting routine operations
- Less frequent supportive supervision

### Facility-Type Differences

| Facility Type | Average Score | Late Submission Rate |
|---------------|---------------|----------------------|
| General Hospital | 78.9 | 22.1% |
| Primary Health Center (PHC) | 74.3 | 30.4% |

**PHCs face greater challenges**, likely due to:
- Fewer dedicated HMIS staff
- Greater distance from LGA offices
- Limited connectivity
- Higher workload relative to staff

---

## Common Data Quality Issues

### 1. Timeliness Challenges

**Pattern**: Many facilities submit 10-20 days after the 7-day deadline.

**Contributing factors**:
- Monthly workload peaks
- Internet connectivity at end-of-month
- Manual aggregation from registers
- Awaiting LGA/state review before submission
- Lack of automated reminders

**Impact**: Late data cannot inform timely decisions (supply orders, outbreak response, monthly performance reviews).

### 2. Completeness Gaps

**Pattern**: 5-7% of records have missing values for key indicators (ANC, immunization).

**Contributing factors**:
- Service not offered that month (stockout, staff absence)
- Paper register pages missing
- Data entry rushed/incomplete
- Fields skipped when value is zero (not understanding blank ≠ zero)

**Impact**: Missing data prevents accurate coverage calculation and trend analysis.

### 3. Consistency Violations

**Common violations**:
- Penta3 > Penta1 (5% of records)
- ANC4 > ANC1 (3% of records)
- Fully immunized > Measles1 doses (2% of records)

**Contributing factors**:
- Misunderstanding indicator definitions
- Data entry from wrong register cells
- Batch corrections not applied consistently
- Transposed digits

**Impact**: Violates program logic, casts doubt on data reliability, inflates dropout rates.

### 4. Outliers and Spikes

**Pattern**: Small number (2-3%) of records with extreme values or sudden jumps.

**Legitimate reasons**:
- Outreach campaigns (e.g., measles campaign)
- Catch-up after stockout resolved
- Facility serves large/mobile population

**Data quality issues**:
- Decimal point errors (120 entered as 1,200)
- Duplicate addition (adding instead of replacing)
- Copy-paste errors from previous month

**Impact**: Skews district/state aggregates, triggers false alarms, requires manual verification.

---

## Recommendations

### Priority 1: Improve Timeliness (Low-Cost, High-Impact)

**Actions**:

1. **Automated SMS/Email Reminders**
   - Send reminders at day 25 of month (prepare data)
   - Send at day 5 after month-end (deadline approaching)
   - Send at day 8 for late facilities
   - **Cost**: Minimal (bulk SMS ~$0.01/message)
   - **Impact**: Expected 30-50% reduction in late submissions

2. **Timeliness Dashboard for Managers**
   - Real-time submission tracking by LGA/state
   - Identify chronic late-submitters
   - Enable targeted follow-up
   - **Cost**: Already built into this pipeline
   - **Impact**: Peer pressure, managerial accountability

3. **Adjust Deadlines for Remote Areas**
   - Consider 10-day deadline for hard-to-reach facilities
   - Balance timeliness with feasibility
   - **Cost**: Policy change only
   - **Impact**: Reduced frustration, more realistic targets

### Priority 2: Strengthen Data Entry Validation (Low-Cost)

**Actions**:

1. **Built-in Validation Rules in Entry System**
   - Flag penta3 > penta1 before submission
   - Flag extreme values (>3× facility average)
   - Force correction or confirmation before proceeding
   - **Cost**: Developer time (one-time)
   - **Impact**: 70-80% reduction in consistency violations

2. **Simple Data Quality Checks at Entry**
   - Running total of YTD for comparison
   - Display previous month value for reference
   - Highlight if current > 2× previous
   - **Cost**: UI enhancement
   - **Impact**: Catch typos before submission

3. **Zero vs. Blank Guidance**
   - Clear instructions: blank means "no data", zero means "service offered, no cases"
   - Enforce required fields
   - **Cost**: Training materials update
   - **Impact**: Improved completeness

### Priority 3: Targeted Training and Support (Moderate-Cost)

**Actions**:

1. **Refresher Training for Bottom 20% Facilities**
   - Focus on indicator definitions
   - Hands-on data entry practice
   - Common error patterns
   - **Cost**: Training materials + facilitator time
   - **Target**: ~240 facilities (20% of 1,200)
   - **Impact**: Score improvement of 10-15 points

2. **Peer Learning Networks**
   - Pair high-performing with low-performing facilities
   - Monthly virtual meetings to share practices
   - Recognize improvement
   - **Cost**: Facilitation only
   - **Impact**: Sustained improvement, knowledge transfer

3. **On-Site Supportive Supervision**
   - Quarterly visits for lowest-scoring LGAs
   - Observe data flow from register to system
   - Provide feedback and coaching
   - **Cost**: Travel + staff time
   - **Impact**: Identify and address root causes

### Priority 4: Enhance Feedback Loops (Low-Cost, High-Impact)

**Actions**:

1. **Monthly DQA Reports to Facilities**
   - One-page scorecard with quality score and trends
   - Comparison to LGA/state average
   - Specific issues flagged (outliers, violations)
   - **Cost**: Automated report generation (this pipeline)
   - **Impact**: Awareness, motivation to improve

2. **Recognize Top Performers**
   - Quarterly awards for most improved, highest quality
   - Share best practices in national bulletins
   - **Cost**: Minimal (certificates, publicity)
   - **Impact**: Positive incentives, culture change

3. **Close the Loop on Data Use**
   - Show facilities how their data informs decisions
   - Report on aggregate trends, achievements
   - Demonstrate value of accurate, timely data
   - **Cost**: Communication materials
   - **Impact**: Motivate quality through visibility of impact

---

## Limitations and Next Steps

### Limitations of Current Assessment

1. **Synthetic Data**: This demonstration uses simulated data. Real data validation needed.

2. **Threshold Sensitivity**: Current thresholds (e.g., MAD > 3.5) tuned to synthetic data. May need adjustment for real distributions.

3. **Peer Grouping**: State-level grouping doesn't account for facility size, catchment, urbanicity. More sophisticated grouping may improve outlier detection accuracy.

4. **Seasonality Not Modeled**: Some indicators (e.g., malaria, flu) have seasonal patterns that may trigger false spike flags.

5. **Context Not Captured**: Flags require human review to distinguish errors from legitimate events (campaigns, outbreaks).

### Next Steps

**Short-Term (1-3 months)**:
- Run DQA on 6 months of real data
- Validate thresholds and adjust if needed
- Train state HMIS officers on dashboard use
- Pilot automated reminders in 3 states

**Medium-Term (3-6 months)**:
- Integrate validation rules into data entry system
- Roll out monthly DQA scorecards to all facilities
- Conduct targeted training for bottom 20%
- Establish peer learning networks

**Long-Term (6-12 months)**:
- Automate DQA pipeline to run monthly
- Expand checks (e.g., trend analysis, denominators)
- Link DQA scores to performance reviews (non-punitively)
- Publish annual National Data Quality Report

---

## Using the Dashboard

The interactive DQA dashboard (`streamlit run dashboards/dqa_app.py`) allows stakeholders to:

**State/LGA Managers**:
- View quality scores for their facilities
- Identify lowest-performing facilities for support
- Track improvement over time
- Download facility lists for follow-up

**National Program Officers**:
- Monitor national/state trends
- Compare across states/LGAs
- Identify systemic issues (e.g., widespread lateness)
- Prioritize resource allocation

**HMIS Officers**:
- Investigate flagged records (outliers, spikes)
- Contact facilities for clarification
- Document explanations (campaigns, events)
- Generate reports for stakeholders

**Key Metrics to Monitor**:
- **Overall Score**: Are we improving over time?
- **Timeliness Rate**: Percentage submitted on-time
- **Completeness Rate**: Percentage of fields populated
- **Flags by Type**: Where are most issues?

---

## Conclusion

Data quality is foundational to effective health system management. This assessment reveals **significant opportunities for improvement**, particularly in timeliness and consistency. The **good news**: many issues are addressable through **low-cost interventions** like automated reminders, built-in validations, and targeted feedback.

**Priority actions**:
1. Implement automated submission reminders (immediate, low-cost)
2. Add validation rules to data entry system (short-term, one-time cost)
3. Provide monthly quality scorecards to facilities (ongoing, automated)
4. Target training and support to lowest-performing facilities (phased)

With sustained attention, **realistic target**: improve national score from 75 to 85+ within 12 months, resulting in more **reliable, timely, and actionable** health data to guide programs and policies.

---

**Prepared by**: Health DQA Team  
**Date**: [Current Date]  
**Contact**: [Contact Information]

*This memo is based on synthetic data for demonstration purposes. Findings should be validated with real data before programmatic action.*
