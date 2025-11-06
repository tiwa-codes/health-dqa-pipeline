"""
Generate synthetic routine health facility data for Nigeria.

This module creates realistic facility data with intentional quality issues
for testing and demonstrating the DQA pipeline.
"""
import argparse
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.dates import generate_periods, make_due_date


# Nigerian states (37 total: 36 states + FCT Abuja)
NIGERIAN_STATES = [
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue",
    "Borno", "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu",
    "Gombe", "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi",
    "Kwara", "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo",
    "Plateau", "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara", "FCT Abuja"
]

# Rough latitude/longitude bounds for Nigeria
LAT_BOUNDS = (4.0, 14.0)
LON_BOUNDS = (3.0, 15.0)


def generate_facility_registry(num_facilities: int, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic facility registry.
    
    Args:
        num_facilities: Number of facilities to generate
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with facility registry information
    """
    np.random.seed(seed)
    
    facilities = []
    
    # Distribute facilities across states
    facilities_per_state = num_facilities // len(NIGERIAN_STATES)
    extra = num_facilities % len(NIGERIAN_STATES)
    
    facility_counter = 1
    
    for state_idx, state in enumerate(NIGERIAN_STATES):
        # Add extra facilities to first few states
        n_facilities = facilities_per_state + (1 if state_idx < extra else 0)
        
        for i in range(n_facilities):
            facility_id = f"FAC{facility_counter:05d}"
            
            # Generate facility attributes
            facility_type = np.random.choice(
                ["PHC", "General Hospital"],
                p=[0.8, 0.2]  # 80% PHC, 20% hospitals
            )
            
            ownership = np.random.choice(
                ["Public", "Private"],
                p=[0.85, 0.15]  # 85% public, 15% private
            )
            
            # Generate plausible LGA name (simplified)
            lga = f"{state} {np.random.choice(['North', 'South', 'East', 'West', 'Central'])}"
            
            # Random coordinates within Nigeria bounds
            latitude = np.random.uniform(LAT_BOUNDS[0], LAT_BOUNDS[1])
            longitude = np.random.uniform(LON_BOUNDS[0], LON_BOUNDS[1])
            
            # Generate facility name
            facility_name = f"{state} {facility_type} {i+1}"
            
            facilities.append({
                "facility_id": facility_id,
                "facility_name": facility_name,
                "state": state,
                "lga": lga,
                "facility_type": facility_type,
                "ownership": ownership,
                "latitude": round(latitude, 6),
                "longitude": round(longitude, 6)
            })
            
            facility_counter += 1
    
    return pd.DataFrame(facilities)


def generate_facility_reports(
    registry: pd.DataFrame,
    start_period: str,
    num_months: int,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic monthly facility reports with intentional quality issues.
    
    Args:
        registry: Facility registry DataFrame
        start_period: Starting period in YYYY-MM format
        num_months: Number of months to generate
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with monthly facility reports
    """
    np.random.seed(seed)
    
    periods = generate_periods(start_period, num_months)
    reports = []
    
    # Create baseline values for each facility (for consistency)
    facility_baselines = {}
    for facility_id in registry['facility_id']:
        facility_baselines[facility_id] = {
            'opd_visits': np.random.randint(200, 10000),
            'anc1_first_visit': np.random.randint(10, 600),
            'anc4_visits': np.random.randint(5, 400),
            'facility_deliveries': np.random.randint(5, 400),
            'bcg_doses': np.random.randint(10, 800),
            'penta1_doses': np.random.randint(10, 800),
            'penta3_doses': np.random.randint(5, 700),
            'measles1_doses': np.random.randint(5, 700),
            'fully_immunized_under1': np.random.randint(5, 700),
            'vaccine_stockout_days': np.random.randint(0, 5),
            'eligible_under1_population': np.random.randint(50, 1200)
        }
    
    # Generate reports for each facility and period
    for facility_id in registry['facility_id']:
        baseline = facility_baselines[facility_id]
        
        for period_idx, period in enumerate(periods):
            # Skip some reports to create missingness at facility-period level
            if np.random.random() < 0.02:  # 2% completely missing reports
                continue
            
            # Generate values with realistic variation
            report = {
                'facility_id': facility_id,
                'period': period
            }
            
            # Generate indicators with variation and relationships
            # Add seasonal variation and random noise
            seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * period_idx / 12)
            noise_factor = np.random.uniform(0.8, 1.2)
            
            opd_visits = int(baseline['opd_visits'] * seasonal_factor * noise_factor)
            anc1 = int(baseline['anc1_first_visit'] * seasonal_factor * noise_factor)
            
            # Ensure logical relationships with some noise
            anc4 = int(min(anc1 * np.random.uniform(0.3, 0.7), baseline['anc4_visits'] * noise_factor))
            deliveries = int(min(anc4 * np.random.uniform(0.5, 0.9), baseline['facility_deliveries'] * noise_factor))
            
            penta1 = int(baseline['penta1_doses'] * seasonal_factor * noise_factor)
            penta3 = int(min(penta1 * np.random.uniform(0.6, 0.9), baseline['penta3_doses'] * noise_factor))
            measles1 = int(min(penta3 * np.random.uniform(0.7, 1.0), baseline['measles1_doses'] * noise_factor))
            fully_imm = int(min(measles1 * np.random.uniform(0.7, 0.95), baseline['fully_immunized_under1'] * noise_factor))
            
            bcg = int(baseline['bcg_doses'] * seasonal_factor * noise_factor)
            stockout_days = np.random.poisson(baseline['vaccine_stockout_days'])
            eligible_pop = int(baseline['eligible_under1_population'] * (1 + np.random.uniform(-0.05, 0.05)))
            
            # Inject consistency violations (5% chance)
            if np.random.random() < 0.05:
                if np.random.random() < 0.5:
                    anc4 = int(anc1 * np.random.uniform(1.05, 1.3))  # anc4 > anc1
                else:
                    penta3 = int(penta1 * np.random.uniform(1.05, 1.2))  # penta3 > penta1
            
            # Inject spikes (3% chance of large increase)
            if np.random.random() < 0.03 and period_idx > 0:
                spike_indicator = np.random.choice(['opd_visits', 'bcg_doses', 'penta1_doses'])
                if spike_indicator == 'opd_visits':
                    opd_visits = int(opd_visits * np.random.uniform(2.0, 3.5))
                elif spike_indicator == 'bcg_doses':
                    bcg = int(bcg * np.random.uniform(2.0, 3.0))
                else:
                    penta1 = int(penta1 * np.random.uniform(2.0, 3.0))
            
            report['opd_visits'] = opd_visits
            report['anc1_first_visit'] = anc1
            report['anc4_visits'] = anc4
            report['facility_deliveries'] = deliveries
            report['bcg_doses'] = bcg
            report['penta1_doses'] = penta1
            report['penta3_doses'] = penta3
            report['measles1_doses'] = measles1
            report['fully_immunized_under1'] = fully_imm
            report['vaccine_stockout_days'] = stockout_days
            report['eligible_under1_population'] = eligible_pop
            
            # Inject missingness in individual indicators (3-7% per indicator)
            for indicator in ['opd_visits', 'anc1_first_visit', 'anc4_visits', 
                            'facility_deliveries', 'bcg_doses', 'penta1_doses',
                            'penta3_doses', 'measles1_doses', 'fully_immunized_under1']:
                if np.random.random() < np.random.uniform(0.03, 0.07):
                    report[indicator] = np.nan
            
            # Generate submission date
            due_date = make_due_date(period, due_days=7)
            
            # Vary lateness by state and facility type
            state = registry[registry['facility_id'] == facility_id]['state'].values[0]
            facility_type = registry[registry['facility_id'] == facility_id]['facility_type'].values[0]
            
            # Some states/facilities are consistently late
            state_lateness = hash(state) % 15 - 5  # -5 to 10 days variation by state
            facility_lateness = 5 if facility_type == "PHC" else 0  # PHCs tend to be later
            
            days_variation = int(np.random.normal(state_lateness + facility_lateness, 7))
            submission_date = due_date + timedelta(days=days_variation)
            
            report['submission_date'] = submission_date.strftime('%Y-%m-%d')
            
            reports.append(report)
    
    df = pd.DataFrame(reports)
    
    # Inject duplicates (1-2% of facility-months)
    num_duplicates = int(len(df) * np.random.uniform(0.01, 0.02))
    if num_duplicates > 0:
        duplicate_indices = np.random.choice(df.index, size=num_duplicates, replace=False)
        duplicates = df.loc[duplicate_indices].copy()
        # Slightly modify duplicates to simulate data entry errors
        for idx in duplicates.index:
            indicator = np.random.choice(['opd_visits', 'bcg_doses'])
            if pd.notna(duplicates.loc[idx, indicator]):
                duplicates.loc[idx, indicator] = int(duplicates.loc[idx, indicator] * np.random.uniform(0.95, 1.05))
        df = pd.concat([df, duplicates], ignore_index=True)
    
    # Inject outliers (0.5% extreme values)
    num_outliers = int(len(df) * 0.005)
    outlier_indices = np.random.choice(df.index, size=num_outliers, replace=False)
    for idx in outlier_indices:
        indicator = np.random.choice(['opd_visits', 'bcg_doses', 'penta1_doses'])
        if pd.notna(df.loc[idx, indicator]):
            # Either extremely high or extremely low
            if np.random.random() < 0.5:
                df.loc[idx, indicator] = int(df.loc[idx, indicator] * np.random.uniform(5, 10))
            else:
                df.loc[idx, indicator] = max(0, int(df.loc[idx, indicator] * np.random.uniform(0.05, 0.2)))
    
    return df.sort_values(['facility_id', 'period']).reset_index(drop=True)


def generate_indicator_definitions() -> pd.DataFrame:
    """
    Generate indicator definitions reference table.
    
    Returns:
        DataFrame with indicator metadata
    """
    indicators = [
        {
            "indicator": "opd_visits",
            "description": "Total outpatient department visits",
            "unit": "visits",
            "expected_constraints": "Range: 200-10000; No negative values"
        },
        {
            "indicator": "anc1_first_visit",
            "description": "First antenatal care visit",
            "unit": "visits",
            "expected_constraints": "Range: 10-600; Should be >= anc4_visits"
        },
        {
            "indicator": "anc4_visits",
            "description": "Four or more antenatal care visits",
            "unit": "visits",
            "expected_constraints": "Range: 5-400; Should be <= anc1_first_visit"
        },
        {
            "indicator": "facility_deliveries",
            "description": "Deliveries at facility",
            "unit": "deliveries",
            "expected_constraints": "Range: 5-400; Should be <= anc4_visits"
        },
        {
            "indicator": "bcg_doses",
            "description": "BCG vaccine doses administered",
            "unit": "doses",
            "expected_constraints": "Range: 10-800; No negative values"
        },
        {
            "indicator": "penta1_doses",
            "description": "First pentavalent vaccine dose",
            "unit": "doses",
            "expected_constraints": "Range: 10-800; Should be >= penta3_doses"
        },
        {
            "indicator": "penta3_doses",
            "description": "Third pentavalent vaccine dose",
            "unit": "doses",
            "expected_constraints": "Range: 5-700; Should be <= penta1_doses"
        },
        {
            "indicator": "measles1_doses",
            "description": "First measles vaccine dose",
            "unit": "doses",
            "expected_constraints": "Range: 5-700; Should be <= penta3_doses"
        },
        {
            "indicator": "fully_immunized_under1",
            "description": "Fully immunized children under 1 year",
            "unit": "children",
            "expected_constraints": "Range: 5-700; Should be <= measles1_doses"
        },
        {
            "indicator": "vaccine_stockout_days",
            "description": "Days with vaccine stockouts",
            "unit": "days",
            "expected_constraints": "Range: 0-30; No negative values"
        },
        {
            "indicator": "eligible_under1_population",
            "description": "Estimated population under 1 year",
            "unit": "children",
            "expected_constraints": "Range: 50-1200; Relatively stable over time"
        }
    ]
    
    return pd.DataFrame(indicators)


def main():
    """Main function to generate synthetic data."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic routine health facility data for Nigeria"
    )
    parser.add_argument(
        "--facilities",
        type=int,
        default=1200,
        help="Number of facilities to generate (default: 1200)"
    )
    parser.add_argument(
        "--months",
        type=int,
        default=24,
        help="Number of months to generate (default: 24)"
    )
    parser.add_argument(
        "--start-period",
        type=str,
        default="2024-01",
        help="Starting period in YYYY-MM format (default: 2024-01)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Output directory for generated files (default: data/raw)"
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("Synthetic Health Data Generator for Nigeria")
    print("="*70)
    print(f"Generating {args.facilities} facilities across 37 Nigerian states")
    print(f"Reporting periods: {args.months} months starting from {args.start_period}")
    print(f"Random seed: {args.seed}")
    print()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate facility registry
    print("Step 1/3: Generating facility registry...")
    registry = generate_facility_registry(args.facilities, seed=args.seed)
    registry_path = output_dir / "facility_registry.csv"
    registry.to_csv(registry_path, index=False)
    print(f"  ✓ Created {registry_path}")
    print(f"    - {len(registry)} facilities")
    print(f"    - {registry['state'].nunique()} states")
    print(f"    - Facility types: {dict(registry['facility_type'].value_counts())}")
    print()
    
    # Generate facility reports
    print("Step 2/3: Generating monthly facility reports...")
    print("  (This may take a minute...)")
    reports = generate_facility_reports(
        registry, 
        args.start_period, 
        args.months, 
        seed=args.seed
    )
    reports_path = output_dir / "facility_reports.csv"
    reports.to_csv(reports_path, index=False)
    print(f"  ✓ Created {reports_path}")
    print(f"    - {len(reports)} facility-month records")
    print(f"    - Expected records: {args.facilities * args.months}")
    print(f"    - Missing rate: {1 - len(reports)/(args.facilities * args.months):.1%}")
    
    # Check for duplicates
    duplicates = reports.duplicated(subset=['facility_id', 'period'], keep=False).sum()
    print(f"    - Duplicate facility-months: {duplicates} ({duplicates/len(reports):.1%})")
    
    # Check missingness by indicator
    print(f"    - Indicator missingness:")
    indicators = ['opd_visits', 'anc1_first_visit', 'bcg_doses', 'penta1_doses']
    for ind in indicators:
        missing_pct = reports[ind].isna().sum() / len(reports) * 100
        print(f"      • {ind}: {missing_pct:.1f}%")
    print()
    
    # Generate indicator definitions
    print("Step 3/3: Generating indicator definitions...")
    definitions = generate_indicator_definitions()
    definitions_path = output_dir / "indicator_definitions.csv"
    definitions.to_csv(definitions_path, index=False)
    print(f"  ✓ Created {definitions_path}")
    print(f"    - {len(definitions)} indicators defined")
    print()
    
    print("="*70)
    print("✓ Data generation complete!")
    print("="*70)
    print("\nGenerated files:")
    print(f"  1. {registry_path}")
    print(f"  2. {reports_path}")
    print(f"  3. {definitions_path}")
    print("\nNext steps:")
    print("  - Run DQA pipeline: python -m src.quality.dqa_pipeline")
    print("  - Open dashboard: streamlit run dashboards/dqa_app.py")
    print("  - Explore notebook: jupyter lab notebooks/01_dqa_walkthrough.ipynb")


if __name__ == "__main__":
    main()
