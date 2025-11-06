"""
Quality metrics calculation and scoring functions.

Computes quality scores (0-100) based on check results and configured weights.
"""
import pandas as pd
import numpy as np
from typing import Dict
import json
from pathlib import Path


def compute_completeness_score(completeness_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute completeness sub-score (0-100).
    
    Args:
        completeness_df: Results from check_completeness
        
    Returns:
        DataFrame with completeness scores
    """
    scores = completeness_df.copy()
    # Convert rate to 0-100 scale
    scores['completeness_score'] = scores['completeness_rate'] * 100
    return scores[['facility_id', 'period', 'completeness_score', 'flag_incomplete']]


def compute_duplicates_score(duplicates_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute duplicates sub-score (0-100).
    
    Args:
        duplicates_df: Results from check_duplicates
        
    Returns:
        DataFrame with duplicate scores
    """
    scores = duplicates_df.copy()
    # 100 if no duplicates, 0 if duplicates exist
    scores['duplicates_score'] = (~scores['flag_duplicate']).astype(int) * 100
    return scores[['facility_id', 'period', 'duplicates_score', 'flag_duplicate']]


def compute_timeliness_score(timeliness_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute timeliness sub-score (0-100).
    
    Args:
        timeliness_df: Results from check_timeliness
        
    Returns:
        DataFrame with timeliness scores
    """
    scores = timeliness_df.copy()
    
    # Score based on days late
    # On time or early: 100
    # Up to 7 days late: linear decrease to 50
    # More than 7 days late: 50 - (days_late - 7) * 5, minimum 0
    
    def calc_timeliness_score(days_late):
        if pd.isna(days_late):
            return 0  # No submission date
        if days_late <= 0:
            return 100  # On time or early
        elif days_late <= 7:
            return 100 - (days_late / 7) * 50  # Linear decrease
        else:
            return max(0, 50 - (days_late - 7) * 5)  # Further penalty
    
    scores['timeliness_score'] = scores['days_late'].apply(calc_timeliness_score)
    return scores[['facility_id', 'period', 'timeliness_score', 'flag_late']]


def compute_outliers_score(outliers_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute outliers sub-score (0-100) per facility-period.
    
    Args:
        outliers_df: Results from check_outliers
        
    Returns:
        DataFrame with outlier scores aggregated by facility-period
    """
    if len(outliers_df) == 0:
        return pd.DataFrame(columns=['facility_id', 'period', 'outliers_score', 'outlier_count'])
    
    # Aggregate by facility-period
    agg = outliers_df.groupby(['facility_id', 'period']).agg({
        'flag_outlier': 'sum'  # Count outliers
    }).reset_index()
    
    agg.columns = ['facility_id', 'period', 'outlier_count']
    
    # Score: 100 if no outliers, decrease by 20 per outlier, minimum 0
    agg['outliers_score'] = (100 - agg['outlier_count'] * 20).clip(lower=0)
    
    return agg


def compute_spikes_score(spikes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute spikes sub-score (0-100) per facility-period.
    
    Args:
        spikes_df: Results from check_spikes
        
    Returns:
        DataFrame with spike scores aggregated by facility-period
    """
    if len(spikes_df) == 0:
        return pd.DataFrame(columns=['facility_id', 'period', 'spikes_score', 'spike_count'])
    
    # Aggregate by facility-period
    agg = spikes_df.groupby(['facility_id', 'period']).agg({
        'flag_spike': 'sum'  # Count spikes
    }).reset_index()
    
    agg.columns = ['facility_id', 'period', 'spike_count']
    
    # Score: 100 if no spikes, decrease by 25 per spike, minimum 0
    agg['spikes_score'] = (100 - agg['spike_count'] * 25).clip(lower=0)
    
    return agg


def compute_consistency_score(consistency_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute consistency sub-score (0-100).
    
    Args:
        consistency_df: Results from check_consistency
        
    Returns:
        DataFrame with consistency scores
    """
    scores = consistency_df.copy()
    
    # Score: 100 if no violations, decrease by 20 per violation, minimum 0
    scores['consistency_score'] = (100 - scores['violation_count'] * 20).clip(lower=0)
    
    return scores[['facility_id', 'period', 'consistency_score', 'flag_inconsistent', 'violation_count']]


def compute_overall_scores(
    all_scores: Dict[str, pd.DataFrame],
    weights: Dict[str, int]
) -> pd.DataFrame:
    """
    Compute weighted overall quality score.
    
    Args:
        all_scores: Dictionary of sub-score DataFrames
        weights: Dictionary of weights for each component
        
    Returns:
        DataFrame with all scores and overall score
    """
    # Start with facility-period keys
    base_df = all_scores['completeness'][['facility_id', 'period']].copy()
    
    # Merge all sub-scores
    result = base_df.copy()
    
    for check_name, score_df in all_scores.items():
        score_col = f'{check_name}_score'
        if score_col in score_df.columns:
            merge_cols = ['facility_id', 'period', score_col]
            # Add flag columns if they exist
            flag_col = [c for c in score_df.columns if c.startswith('flag_')]
            merge_cols.extend(flag_col)
            
            result = result.merge(
                score_df[merge_cols],
                on=['facility_id', 'period'],
                how='left'
            )
    
    # Fill missing scores with 100 (no issues found)
    score_columns = [col for col in result.columns if col.endswith('_score')]
    for col in score_columns:
        result[col] = result[col].fillna(100)
    
    # Calculate weighted overall score
    total_weight = sum(weights.values())
    if total_weight != 100:
        print(f"Warning: Weights sum to {total_weight}, not 100. Normalizing...")
        weights = {k: v * 100 / total_weight for k, v in weights.items()}
    
    result['overall_score'] = 0
    for component, weight in weights.items():
        score_col = f'{component}_score'
        if score_col in result.columns:
            result['overall_score'] += result[score_col] * (weight / 100)
    
    return result


def create_facility_summary(detailed_results: pd.DataFrame) -> pd.DataFrame:
    """
    Create facility-level summary statistics.
    
    Args:
        detailed_results: Facility-month level results
        
    Returns:
        DataFrame with facility-level aggregations
    """
    score_columns = [col for col in detailed_results.columns if col.endswith('_score')]
    flag_columns = [col for col in detailed_results.columns if col.startswith('flag_')]
    
    # Aggregate by facility
    agg_dict = {col: 'mean' for col in score_columns}
    agg_dict.update({col: 'sum' for col in flag_columns})
    agg_dict['period'] = 'count'  # Number of periods
    
    facility_summary = detailed_results.groupby('facility_id').agg(agg_dict).reset_index()
    facility_summary.rename(columns={'period': 'num_periods'}, inplace=True)
    
    # Calculate rates for flags
    for flag_col in flag_columns:
        rate_col = flag_col.replace('flag_', '') + '_rate'
        facility_summary[rate_col] = facility_summary[flag_col] / facility_summary['num_periods']
    
    return facility_summary


def create_state_summary(
    detailed_results: pd.DataFrame,
    registry: pd.DataFrame
) -> pd.DataFrame:
    """
    Create state-level summary statistics.
    
    Args:
        detailed_results: Facility-month level results
        registry: Facility registry with state information
        
    Returns:
        DataFrame with state-level aggregations
    """
    # Merge with registry to get state
    df_with_state = detailed_results.merge(
        registry[['facility_id', 'state']],
        on='facility_id',
        how='left'
    )
    
    score_columns = [col for col in df_with_state.columns if col.endswith('_score')]
    flag_columns = [col for col in df_with_state.columns if col.startswith('flag_')]
    
    # Aggregate by state
    agg_dict = {col: 'mean' for col in score_columns}
    agg_dict.update({col: 'sum' for col in flag_columns})
    agg_dict['facility_id'] = 'nunique'  # Number of facilities
    agg_dict['period'] = 'count'  # Number of facility-months
    
    state_summary = df_with_state.groupby('state').agg(agg_dict).reset_index()
    state_summary.rename(columns={
        'facility_id': 'num_facilities',
        'period': 'num_records'
    }, inplace=True)
    
    # Calculate rates for flags
    for flag_col in flag_columns:
        rate_col = flag_col.replace('flag_', '') + '_rate'
        state_summary[rate_col] = state_summary[flag_col] / state_summary['num_records']
    
    return state_summary


def create_metrics_summary(
    detailed_results: pd.DataFrame,
    facility_summary: pd.DataFrame,
    state_summary: pd.DataFrame,
    registry: pd.DataFrame
) -> Dict:
    """
    Create compact JSON summary of key metrics.
    
    Args:
        detailed_results: Facility-month level results
        facility_summary: Facility-level summary
        state_summary: State-level summary
        registry: Facility registry
        
    Returns:
        Dictionary with key metrics
    """
    score_columns = [col for col in detailed_results.columns if col.endswith('_score')]
    
    # National averages
    national_scores = {col: float(detailed_results[col].mean()) 
                      for col in score_columns}
    
    # Best and worst facilities
    top_facilities = facility_summary.nlargest(5, 'overall_score')[
        ['facility_id', 'overall_score']
    ].to_dict('records')
    
    bottom_facilities = facility_summary.nsmallest(5, 'overall_score')[
        ['facility_id', 'overall_score']
    ].to_dict('records')
    
    # Best and worst states
    top_states = state_summary.nlargest(5, 'overall_score')[
        ['state', 'overall_score', 'num_facilities']
    ].to_dict('records')
    
    bottom_states = state_summary.nsmallest(5, 'overall_score')[
        ['state', 'overall_score', 'num_facilities']
    ].to_dict('records')
    
    # Issue counts
    flag_columns = [col for col in detailed_results.columns if col.startswith('flag_')]
    issue_counts = {col.replace('flag_', ''): int(detailed_results[col].sum()) 
                   for col in flag_columns}
    
    summary = {
        'generated_at': pd.Timestamp.now().isoformat(),
        'total_facilities': int(registry['facility_id'].nunique()),
        'total_records': len(detailed_results),
        'national_scores': national_scores,
        'issue_counts': issue_counts,
        'top_5_facilities': top_facilities,
        'bottom_5_facilities': bottom_facilities,
        'top_5_states': top_states,
        'bottom_5_states': bottom_states,
        'data_quality_grade': get_quality_grade(national_scores['overall_score'])
    }
    
    return summary


def get_quality_grade(score: float) -> str:
    """
    Convert numeric score to letter grade.
    
    Args:
        score: Overall quality score (0-100)
        
    Returns:
        Letter grade (A+ to F)
    """
    if score >= 95:
        return "A+"
    elif score >= 90:
        return "A"
    elif score >= 85:
        return "A-"
    elif score >= 80:
        return "B+"
    elif score >= 75:
        return "B"
    elif score >= 70:
        return "B-"
    elif score >= 65:
        return "C+"
    elif score >= 60:
        return "C"
    elif score >= 55:
        return "C-"
    elif score >= 50:
        return "D"
    else:
        return "F"


def compute_all_metrics(
    check_results: Dict[str, pd.DataFrame],
    registry: pd.DataFrame,
    config: Dict,
    output_dir: Path
) -> Dict[str, pd.DataFrame]:
    """
    Compute all quality metrics and save outputs.
    
    Args:
        check_results: Dictionary of check result DataFrames
        registry: Facility registry DataFrame
        config: Configuration dictionary
        output_dir: Directory for output files
        
    Returns:
        Dictionary with all summary DataFrames
    """
    print("\nComputing quality scores...")
    
    # Compute sub-scores
    all_scores = {
        'completeness': compute_completeness_score(check_results['completeness']),
        'duplicates': compute_duplicates_score(check_results['duplicates']),
        'timeliness': compute_timeliness_score(check_results['timeliness']),
        'outliers': compute_outliers_score(check_results['outliers']),
        'spikes': compute_spikes_score(check_results['spikes']),
        'consistency': compute_consistency_score(check_results['consistency'])
    }
    
    # Compute overall scores
    weights = config.get('weights', {})
    detailed_results = compute_overall_scores(all_scores, weights)
    
    # Create summaries
    print("Creating summaries...")
    facility_summary = create_facility_summary(detailed_results)
    state_summary = create_state_summary(detailed_results, registry)
    metrics_summary = create_metrics_summary(
        detailed_results, facility_summary, state_summary, registry
    )
    
    # Save outputs
    print(f"Saving outputs to {output_dir}...")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    detailed_results.to_csv(output_dir / 'dqa_results_facility_month.csv', index=False)
    facility_summary.to_csv(output_dir / 'dqa_summary_facility.csv', index=False)
    state_summary.to_csv(output_dir / 'dqa_summary_state.csv', index=False)
    
    # Save JSON summary
    reports_dir = Path('reports')
    reports_dir.mkdir(parents=True, exist_ok=True)
    with open(reports_dir / 'metrics_summary.json', 'w') as f:
        json.dump(metrics_summary, f, indent=2)
    
    print("✓ Metrics computation complete")
    
    return {
        'detailed': detailed_results,
        'facility': facility_summary,
        'state': state_summary,
        'summary': metrics_summary
    }
