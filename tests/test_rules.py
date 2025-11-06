"""
Unit tests for DQA rules.
"""
import pytest
import pandas as pd
import numpy as np
from src.quality.rules import (
    check_completeness,
    check_duplicates,
    check_timeliness,
    check_outliers,
    check_spikes,
    check_consistency
)


def test_check_completeness():
    """Test completeness check."""
    # Create test data
    df = pd.DataFrame({
        'facility_id': ['FAC001', 'FAC002', 'FAC003'],
        'period': ['2024-01', '2024-01', '2024-01'],
        'opd_visits': [100, 200, np.nan],
        'anc1_first_visit': [50, np.nan, 30],
        'bcg_doses': [80, 90, 100]
    })
    
    essential_columns = ['facility_id', 'period', 'opd_visits', 'anc1_first_visit', 'bcg_doses']
    
    result = check_completeness(df, essential_columns, threshold=0.95)
    
    assert len(result) == 3
    assert 'completeness_rate' in result.columns
    assert 'flag_incomplete' in result.columns
    
    # FAC001 should be complete (2/2 indicators)
    fac001 = result[result['facility_id'] == 'FAC001'].iloc[0]
    assert fac001['completeness_rate'] == 1.0
    assert fac001['flag_incomplete'] == False
    
    # FAC002 and FAC003 should be incomplete (1/2 indicators each)
    fac002 = result[result['facility_id'] == 'FAC002'].iloc[0]
    assert fac002['completeness_rate'] < 1.0


def test_check_duplicates():
    """Test duplicate detection."""
    # Create test data with duplicates
    df = pd.DataFrame({
        'facility_id': ['FAC001', 'FAC001', 'FAC002'],
        'period': ['2024-01', '2024-01', '2024-01'],
        'opd_visits': [100, 105, 200]
    })
    
    result = check_duplicates(df)
    
    assert len(result) == 2  # 2 unique facility-periods
    assert 'flag_duplicate' in result.columns
    
    # FAC001 should be flagged as duplicate
    fac001 = result[result['facility_id'] == 'FAC001'].iloc[0]
    assert fac001['flag_duplicate'] == True
    assert fac001['duplicate_count'] > 0
    
    # FAC002 should not be flagged
    fac002 = result[result['facility_id'] == 'FAC002'].iloc[0]
    assert fac002['flag_duplicate'] == False


def test_check_timeliness():
    """Test timeliness check."""
    # Create test data with various submission dates
    df = pd.DataFrame({
        'facility_id': ['FAC001', 'FAC002', 'FAC003'],
        'period': ['2024-01', '2024-01', '2024-01'],
        'submission_date': ['2024-02-05', '2024-02-10', '2024-02-20']  # Due: 2024-02-07
    })
    
    result = check_timeliness(df, due_days=7)
    
    assert len(result) == 3
    assert 'days_late' in result.columns
    assert 'flag_late' in result.columns
    
    # FAC001 should be early (submitted Feb 5, due Feb 7)
    fac001 = result[result['facility_id'] == 'FAC001'].iloc[0]
    assert fac001['days_late'] < 0
    assert fac001['flag_late'] == False
    
    # FAC002 should be slightly late (3 days)
    fac002 = result[result['facility_id'] == 'FAC002'].iloc[0]
    assert fac002['days_late'] == 3
    assert fac002['flag_late'] == True
    
    # FAC003 should be very late (13 days)
    fac003 = result[result['facility_id'] == 'FAC003'].iloc[0]
    assert fac003['days_late'] == 13
    assert fac003['flag_late'] == True


def test_check_outliers():
    """Test outlier detection using MAD."""
    # Create test data with an outlier
    df = pd.DataFrame({
        'facility_id': ['FAC001', 'FAC002', 'FAC003', 'FAC004', 'FAC005'],
        'period': ['2024-01'] * 5,
        'state': ['Lagos'] * 5,
        'opd_visits': [100, 110, 105, 95, 1000]  # FAC005 is outlier
    })
    
    result = check_outliers(df, ['opd_visits'], by=['state', 'indicator'], threshold=3.5)
    
    assert len(result) > 0
    assert 'flag_outlier' in result.columns
    assert 'modified_z_score' in result.columns
    
    # FAC005 should be flagged as outlier
    outliers = result[result['flag_outlier'] == True]
    assert len(outliers) > 0
    assert 'FAC005' in outliers['facility_id'].values


def test_check_spikes():
    """Test spike detection."""
    # Create test data with a spike
    df = pd.DataFrame({
        'facility_id': ['FAC001', 'FAC001', 'FAC001'],
        'period': ['2024-01', '2024-02', '2024-03'],
        'opd_visits': [100, 100, 300]  # Spike in March (3x increase)
    })
    
    result = check_spikes(df, ['opd_visits'], pct_change_hi=1.5, pct_change_lo=-0.5)
    
    assert len(result) > 0
    assert 'flag_spike' in result.columns
    assert 'pct_change' in result.columns
    
    # Should detect spike in March
    spikes = result[result['flag_spike'] == True]
    assert len(spikes) > 0
    assert '2024-03' in spikes['period'].values


def test_check_consistency():
    """Test consistency rule checks."""
    # Create test data with violations
    df = pd.DataFrame({
        'facility_id': ['FAC001', 'FAC002', 'FAC003'],
        'period': ['2024-01', '2024-01', '2024-01'],
        'anc1_first_visit': [100, 50, 100],
        'anc4_visits': [80, 60, 90],  # FAC002 violates: anc4 > anc1
        'penta1_doses': [200, 150, 180],
        'penta3_doses': [180, 170, 160]  # FAC002 violates: penta3 > penta1
    })
    
    result = check_consistency(df)
    
    assert len(result) == 3
    assert 'flag_inconsistent' in result.columns
    assert 'violation_count' in result.columns
    
    # FAC001 should be consistent
    fac001 = result[result['facility_id'] == 'FAC001'].iloc[0]
    assert fac001['flag_inconsistent'] == False
    assert fac001['violation_count'] == 0
    
    # FAC002 should have violations
    fac002 = result[result['facility_id'] == 'FAC002'].iloc[0]
    assert fac002['flag_inconsistent'] == True
    assert fac002['violation_count'] > 0


def test_check_consistency_edge_cases():
    """Test consistency check with edge cases."""
    # Test with missing values (should not flag)
    df = pd.DataFrame({
        'facility_id': ['FAC001'],
        'period': ['2024-01'],
        'anc1_first_visit': [np.nan],
        'anc4_visits': [80]
    })
    
    result = check_consistency(df)
    fac001 = result[result['facility_id'] == 'FAC001'].iloc[0]
    # Should not flag because anc1 is missing
    assert fac001['violation_count'] == 0


def test_check_completeness_all_missing():
    """Test completeness with all missing values."""
    df = pd.DataFrame({
        'facility_id': ['FAC001'],
        'period': ['2024-01'],
        'opd_visits': [np.nan],
        'anc1_first_visit': [np.nan],
        'bcg_doses': [np.nan]
    })
    
    essential_columns = ['facility_id', 'period', 'opd_visits', 'anc1_first_visit', 'bcg_doses']
    result = check_completeness(df, essential_columns)
    
    fac001 = result[result['facility_id'] == 'FAC001'].iloc[0]
    assert fac001['completeness_rate'] == 0.0
    assert fac001['flag_incomplete'] == True


def test_check_spikes_zero_division():
    """Test spike detection with zero previous value."""
    df = pd.DataFrame({
        'facility_id': ['FAC001', 'FAC001'],
        'period': ['2024-01', '2024-02'],
        'opd_visits': [0, 100]  # From 0 to 100
    })
    
    result = check_spikes(df, ['opd_visits'])
    
    # Should handle zero previous value gracefully
    assert len(result) > 0
    # Spike from 0 to positive should be flagged
    assert result['flag_spike'].any()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
