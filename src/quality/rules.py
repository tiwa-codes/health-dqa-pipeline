"""
Data quality assessment rules and check functions.

Each function implements a specific quality check and returns a DataFrame
with flags and metrics for affected records.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy import stats


def check_completeness(
    df: pd.DataFrame,
    essential_columns: List[str],
    threshold: float = 0.95
) -> pd.DataFrame:
    """
    Check completeness of essential columns.
    
    Args:
        df: Input DataFrame with facility reports
        essential_columns: List of columns to check for completeness
        threshold: Minimum completeness rate to pass (default: 0.95)
        
    Returns:
        DataFrame with completeness metrics per facility-period
    """
    results = []
    
    # Group by facility and period
    for (facility_id, period), group in df.groupby(['facility_id', 'period']):
        # Count non-missing values for essential columns
        cols_to_check = [col for col in essential_columns if col in df.columns 
                        and col not in ['facility_id', 'period', 'submission_date']]
        
        total_fields = len(cols_to_check)
        non_missing = sum([group[col].notna().any() for col in cols_to_check])
        completeness_rate = non_missing / total_fields if total_fields > 0 else 1.0
        
        results.append({
            'facility_id': facility_id,
            'period': period,
            'check_name': 'completeness',
            'completeness_rate': completeness_rate,
            'missing_count': total_fields - non_missing,
            'total_fields': total_fields,
            'flag_incomplete': completeness_rate < threshold
        })
    
    return pd.DataFrame(results)


def check_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect duplicate records by facility_id and period.
    
    Args:
        df: Input DataFrame with facility reports
        
    Returns:
        DataFrame with duplicate flags and counts
    """
    # Identify duplicates
    df['is_duplicate'] = df.duplicated(subset=['facility_id', 'period'], keep=False)
    
    # Count duplicates per facility-period
    duplicate_counts = df[df['is_duplicate']].groupby(['facility_id', 'period']).size()
    
    results = []
    for (facility_id, period), group in df.groupby(['facility_id', 'period']):
        duplicate_count = duplicate_counts.get((facility_id, period), 0)
        has_duplicates = duplicate_count > 0
        
        results.append({
            'facility_id': facility_id,
            'period': period,
            'check_name': 'duplicates',
            'duplicate_count': int(duplicate_count),
            'flag_duplicate': has_duplicates
        })
    
    return pd.DataFrame(results)


def check_timeliness(
    df: pd.DataFrame,
    due_days: int = 7
) -> pd.DataFrame:
    """
    Check timeliness of report submissions.
    
    Args:
        df: Input DataFrame with facility reports
        due_days: Number of days after period end for submission deadline
        
    Returns:
        DataFrame with timeliness metrics per facility-period
    """
    from src.utils.dates import compute_days_late
    
    results = []
    
    for idx, row in df.iterrows():
        facility_id = row['facility_id']
        period = row['period']
        submission_date = row['submission_date']
        
        if pd.notna(submission_date):
            days_late = compute_days_late(submission_date, period, due_days)
            is_late = days_late > 0
        else:
            days_late = np.nan
            is_late = True  # No submission date counts as late
        
        results.append({
            'facility_id': facility_id,
            'period': period,
            'check_name': 'timeliness',
            'days_late': days_late,
            'flag_late': is_late
        })
    
    # Aggregate by facility-period (handle duplicates)
    results_df = pd.DataFrame(results)
    agg_results = results_df.groupby(['facility_id', 'period']).agg({
        'check_name': 'first',
        'days_late': 'mean',  # Average if duplicates
        'flag_late': 'any'  # Flag if any are late
    }).reset_index()
    
    return agg_results


def check_outliers(
    df: pd.DataFrame,
    indicator_cols: List[str],
    by: List[str] = ["state", "indicator"],
    method: str = "mad",
    threshold: float = 3.5
) -> pd.DataFrame:
    """
    Detect outliers using modified Z-score (MAD method).
    
    Args:
        df: Input DataFrame with facility reports and metadata
        indicator_cols: List of indicator columns to check
        by: Grouping variables for peer comparison (e.g., state, indicator)
        method: Method for outlier detection ('mad' for modified Z-score)
        threshold: Threshold for modified Z-score (default: 3.5)
        
    Returns:
        DataFrame with outlier flags per facility-period-indicator
    """
    results = []
    
    # Must have 'state' column for peer grouping
    if 'state' not in df.columns:
        raise ValueError("DataFrame must have 'state' column for outlier detection")
    
    # Process each indicator
    for indicator in indicator_cols:
        if indicator not in df.columns:
            continue
        
        # Group by state for peer comparison
        for state, state_group in df.groupby('state'):
            values = state_group[indicator].dropna()
            
            if len(values) < 3:  # Need at least 3 values for MAD
                continue
            
            # Calculate MAD-based modified Z-score
            median = values.median()
            mad = np.median(np.abs(values - median))
            
            if mad == 0:  # Avoid division by zero
                mad = 1e-10
            
            # Modified Z-score
            modified_z = 0.6745 * (values - median) / mad
            
            # Flag outliers
            for idx in values.index:
                mz = modified_z.loc[idx]
                is_outlier = abs(mz) > threshold
                
                results.append({
                    'facility_id': df.loc[idx, 'facility_id'],
                    'period': df.loc[idx, 'period'],
                    'indicator': indicator,
                    'check_name': 'outliers',
                    'value': df.loc[idx, indicator],
                    'peer_median': median,
                    'modified_z_score': mz,
                    'flag_outlier': is_outlier
                })
    
    return pd.DataFrame(results)


def check_spikes(
    df: pd.DataFrame,
    indicator_cols: List[str],
    pct_change_hi: float = 1.5,
    pct_change_lo: float = -0.5
) -> pd.DataFrame:
    """
    Detect spikes (sudden large changes) in indicators month-over-month.
    
    Args:
        df: Input DataFrame with facility reports
        indicator_cols: List of indicator columns to check
        pct_change_hi: Upper threshold for percent change (default: 1.5 = 150% increase)
        pct_change_lo: Lower threshold for percent change (default: -0.5 = 50% decrease)
        
    Returns:
        DataFrame with spike flags per facility-period-indicator
    """
    results = []
    
    # Sort by facility and period
    df_sorted = df.sort_values(['facility_id', 'period']).copy()
    
    # Process each facility
    for facility_id, facility_group in df_sorted.groupby('facility_id'):
        facility_group = facility_group.sort_values('period')
        
        # Process each indicator
        for indicator in indicator_cols:
            if indicator not in df.columns:
                continue
            
            values = facility_group[indicator].values
            periods = facility_group['period'].values
            
            # Calculate month-over-month changes
            for i in range(1, len(values)):
                curr_value = values[i]
                prev_value = values[i-1]
                
                # Skip if either value is missing
                if pd.isna(curr_value) or pd.isna(prev_value):
                    continue
                
                # Avoid division by zero
                if prev_value == 0:
                    if curr_value > 0:
                        pct_change = np.inf
                    else:
                        pct_change = 0.0
                else:
                    pct_change = (curr_value - prev_value) / prev_value
                
                # Flag spikes
                is_spike = (pct_change > pct_change_hi) or (pct_change < pct_change_lo)
                
                results.append({
                    'facility_id': facility_id,
                    'period': periods[i],
                    'indicator': indicator,
                    'check_name': 'spikes',
                    'prev_value': prev_value,
                    'curr_value': curr_value,
                    'pct_change': pct_change,
                    'flag_spike': is_spike
                })
    
    return pd.DataFrame(results)


def check_consistency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Check domain constraints and logical consistency rules.
    
    Enforces:
    - anc4_visits <= anc1_first_visit
    - facility_deliveries <= anc4_visits
    - penta3_doses <= penta1_doses
    - measles1_doses <= penta3_doses
    - fully_immunized_under1 <= measles1_doses
    
    Args:
        df: Input DataFrame with facility reports
        
    Returns:
        DataFrame with consistency violation flags per facility-period
    """
    results = []
    
    # Define consistency rules
    rules = [
        ('anc4_visits', 'anc1_first_visit', 'anc4 should be <= anc1'),
        ('facility_deliveries', 'anc4_visits', 'deliveries should be <= anc4'),
        ('penta3_doses', 'penta1_doses', 'penta3 should be <= penta1'),
        ('measles1_doses', 'penta3_doses', 'measles1 should be <= penta3'),
        ('fully_immunized_under1', 'measles1_doses', 'fully_immunized should be <= measles1')
    ]
    
    for idx, row in df.iterrows():
        facility_id = row['facility_id']
        period = row['period']
        
        violations = []
        violation_details = []
        
        # Check each rule
        for col1, col2, description in rules:
            if col1 in df.columns and col2 in df.columns:
                val1 = row[col1]
                val2 = row[col2]
                
                # Only check if both values are present
                if pd.notna(val1) and pd.notna(val2):
                    if val1 > val2:
                        violations.append(description)
                        violation_details.append(f"{col1}({val1}) > {col2}({val2})")
        
        has_violations = len(violations) > 0
        
        results.append({
            'facility_id': facility_id,
            'period': period,
            'check_name': 'consistency',
            'violation_count': len(violations),
            'violations': '; '.join(violations) if violations else None,
            'violation_details': '; '.join(violation_details) if violation_details else None,
            'flag_inconsistent': has_violations
        })
    
    # Aggregate by facility-period (handle duplicates)
    results_df = pd.DataFrame(results)
    agg_results = results_df.groupby(['facility_id', 'period']).agg({
        'check_name': 'first',
        'violation_count': 'max',  # Take worst case
        'violations': lambda x: '; '.join([v for v in x if v is not None]),
        'violation_details': lambda x: '; '.join([v for v in x if v is not None]),
        'flag_inconsistent': 'any'
    }).reset_index()
    
    # Clean up empty strings
    agg_results['violations'] = agg_results['violations'].replace('', None)
    agg_results['violation_details'] = agg_results['violation_details'].replace('', None)
    
    return agg_results


def run_all_checks(
    df: pd.DataFrame,
    registry: pd.DataFrame,
    config: Dict
) -> Dict[str, pd.DataFrame]:
    """
    Run all quality checks on the data.
    
    Args:
        df: Input DataFrame with facility reports
        registry: Facility registry with metadata
        config: Configuration dictionary with thresholds
        
    Returns:
        Dictionary of check results DataFrames
    """
    # Merge with registry to get state information
    df_merged = df.merge(registry[['facility_id', 'state', 'facility_type']], 
                         on='facility_id', how='left')
    
    # Extract config parameters
    essential_columns = config.get('essential_columns', [])
    thresholds = config.get('thresholds', {})
    
    # Get indicator columns
    indicator_cols = [col for col in essential_columns 
                     if col not in ['facility_id', 'period', 'submission_date']]
    
    print("Running quality checks...")
    
    # Run each check
    checks = {}
    
    print("  - Completeness...")
    checks['completeness'] = check_completeness(
        df_merged,
        essential_columns,
        threshold=thresholds.get('completeness_min', 0.95)
    )
    
    print("  - Duplicates...")
    checks['duplicates'] = check_duplicates(df_merged)
    
    print("  - Timeliness...")
    checks['timeliness'] = check_timeliness(
        df_merged,
        due_days=thresholds.get('timeliness_due_days', 7)
    )
    
    print("  - Outliers...")
    checks['outliers'] = check_outliers(
        df_merged,
        indicator_cols,
        threshold=thresholds.get('outliers_mad_threshold', 3.5)
    )
    
    print("  - Spikes...")
    checks['spikes'] = check_spikes(
        df_merged,
        indicator_cols,
        pct_change_hi=thresholds.get('spikes_pct_change_hi', 1.5),
        pct_change_lo=thresholds.get('spikes_pct_change_lo', -0.5)
    )
    
    print("  - Consistency...")
    checks['consistency'] = check_consistency(df_merged)
    
    return checks
