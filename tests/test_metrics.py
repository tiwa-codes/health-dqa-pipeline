"""
Unit tests for quality metrics and scoring.
"""
import pytest
import pandas as pd
import numpy as np
from src.quality.metrics import (
    compute_completeness_score,
    compute_duplicates_score,
    compute_timeliness_score,
    compute_outliers_score,
    compute_spikes_score,
    compute_consistency_score,
    compute_overall_scores,
    get_quality_grade
)


def test_compute_completeness_score():
    """Test completeness score calculation."""
    df = pd.DataFrame({
        'facility_id': ['FAC001', 'FAC002'],
        'period': ['2024-01', '2024-01'],
        'completeness_rate': [1.0, 0.75],
        'flag_incomplete': [False, True]
    })
    
    result = compute_completeness_score(df)
    
    assert len(result) == 2
    assert 'completeness_score' in result.columns
    assert result.iloc[0]['completeness_score'] == 100.0
    assert result.iloc[1]['completeness_score'] == 75.0


def test_compute_duplicates_score():
    """Test duplicates score calculation."""
    df = pd.DataFrame({
        'facility_id': ['FAC001', 'FAC002'],
        'period': ['2024-01', '2024-01'],
        'flag_duplicate': [False, True]
    })
    
    result = compute_duplicates_score(df)
    
    assert len(result) == 2
    assert result.iloc[0]['duplicates_score'] == 100
    assert result.iloc[1]['duplicates_score'] == 0


def test_compute_timeliness_score():
    """Test timeliness score calculation."""
    df = pd.DataFrame({
        'facility_id': ['FAC001', 'FAC002', 'FAC003', 'FAC004'],
        'period': ['2024-01'] * 4,
        'days_late': [-2, 0, 3, 10],
        'flag_late': [False, False, True, True]
    })
    
    result = compute_timeliness_score(df)
    
    assert len(result) == 4
    assert 'timeliness_score' in result.columns
    
    # Early or on-time should be 100
    assert result.iloc[0]['timeliness_score'] == 100
    assert result.iloc[1]['timeliness_score'] == 100
    
    # 3 days late should be between 50 and 100
    score_3days = result.iloc[2]['timeliness_score']
    assert 50 < score_3days < 100
    
    # 10 days late should be less than 50
    score_10days = result.iloc[3]['timeliness_score']
    assert score_10days < 50


def test_compute_outliers_score():
    """Test outliers score calculation."""
    df = pd.DataFrame({
        'facility_id': ['FAC001', 'FAC001', 'FAC002'],
        'period': ['2024-01', '2024-01', '2024-01'],
        'indicator': ['opd_visits', 'bcg_doses', 'opd_visits'],
        'flag_outlier': [True, True, False]
    })
    
    result = compute_outliers_score(df)
    
    assert len(result) == 2  # 2 unique facility-periods
    assert 'outliers_score' in result.columns
    assert 'outlier_count' in result.columns
    
    # FAC001 has 2 outliers: 100 - 2*20 = 60
    fac001 = result[result['facility_id'] == 'FAC001'].iloc[0]
    assert fac001['outlier_count'] == 2
    assert fac001['outliers_score'] == 60
    
    # FAC002 has 0 outliers: 100
    fac002 = result[result['facility_id'] == 'FAC002'].iloc[0]
    assert fac002['outlier_count'] == 0
    assert fac002['outliers_score'] == 100


def test_compute_spikes_score():
    """Test spikes score calculation."""
    df = pd.DataFrame({
        'facility_id': ['FAC001', 'FAC002'],
        'period': ['2024-01', '2024-01'],
        'indicator': ['opd_visits', 'bcg_doses'],
        'flag_spike': [True, False]
    })
    
    result = compute_spikes_score(df)
    
    assert len(result) == 2
    assert 'spikes_score' in result.columns
    assert 'spike_count' in result.columns
    
    # FAC001 has 1 spike: 100 - 1*25 = 75
    fac001 = result[result['facility_id'] == 'FAC001'].iloc[0]
    assert fac001['spike_count'] == 1
    assert fac001['spikes_score'] == 75


def test_compute_consistency_score():
    """Test consistency score calculation."""
    df = pd.DataFrame({
        'facility_id': ['FAC001', 'FAC002', 'FAC003'],
        'period': ['2024-01'] * 3,
        'violation_count': [0, 1, 3],
        'flag_inconsistent': [False, True, True]
    })
    
    result = compute_consistency_score(df)
    
    assert len(result) == 3
    assert 'consistency_score' in result.columns
    
    # 0 violations: 100
    assert result.iloc[0]['consistency_score'] == 100
    
    # 1 violation: 100 - 1*20 = 80
    assert result.iloc[1]['consistency_score'] == 80
    
    # 3 violations: 100 - 3*20 = 40
    assert result.iloc[2]['consistency_score'] == 40


def test_compute_overall_scores():
    """Test overall score computation with weights."""
    # Create sub-scores
    completeness = pd.DataFrame({
        'facility_id': ['FAC001'],
        'period': ['2024-01'],
        'completeness_score': [90.0],
        'flag_incomplete': [False]
    })
    
    duplicates = pd.DataFrame({
        'facility_id': ['FAC001'],
        'period': ['2024-01'],
        'duplicates_score': [100.0],
        'flag_duplicate': [False]
    })
    
    timeliness = pd.DataFrame({
        'facility_id': ['FAC001'],
        'period': ['2024-01'],
        'timeliness_score': [80.0],
        'flag_late': [True]
    })
    
    outliers = pd.DataFrame({
        'facility_id': ['FAC001'],
        'period': ['2024-01'],
        'outliers_score': [100.0]
    })
    
    spikes = pd.DataFrame({
        'facility_id': ['FAC001'],
        'period': ['2024-01'],
        'spikes_score': [100.0]
    })
    
    consistency = pd.DataFrame({
        'facility_id': ['FAC001'],
        'period': ['2024-01'],
        'consistency_score': [100.0],
        'flag_inconsistent': [False],
        'violation_count': [0]
    })
    
    all_scores = {
        'completeness': completeness,
        'duplicates': duplicates,
        'timeliness': timeliness,
        'outliers': outliers,
        'spikes': spikes,
        'consistency': consistency
    }
    
    weights = {
        'completeness': 30,
        'duplicates': 10,
        'timeliness': 15,
        'outliers': 15,
        'spikes': 15,
        'consistency': 15
    }
    
    result = compute_overall_scores(all_scores, weights)
    
    assert len(result) == 1
    assert 'overall_score' in result.columns
    
    # Calculate expected: 90*0.3 + 100*0.1 + 80*0.15 + 100*0.15 + 100*0.15 + 100*0.15
    # = 27 + 10 + 12 + 15 + 15 + 15 = 94
    expected_score = 94.0
    assert abs(result.iloc[0]['overall_score'] - expected_score) < 0.01


def test_compute_overall_scores_weights_normalization():
    """Test that weights are normalized if they don't sum to 100."""
    completeness = pd.DataFrame({
        'facility_id': ['FAC001'],
        'period': ['2024-01'],
        'completeness_score': [100.0],
        'flag_incomplete': [False]
    })
    
    # Minimal set for testing
    all_scores = {'completeness': completeness}
    
    # Weights that don't sum to 100
    weights = {'completeness': 50}
    
    result = compute_overall_scores(all_scores, weights)
    
    # Should still compute (with normalization warning)
    assert len(result) == 1
    assert result.iloc[0]['overall_score'] == 100.0


def test_get_quality_grade():
    """Test quality grade assignment."""
    assert get_quality_grade(97) == "A+"
    assert get_quality_grade(92) == "A"
    assert get_quality_grade(87) == "A-"
    assert get_quality_grade(82) == "B+"
    assert get_quality_grade(77) == "B"
    assert get_quality_grade(72) == "B-"
    assert get_quality_grade(67) == "C+"
    assert get_quality_grade(62) == "C"
    assert get_quality_grade(57) == "C-"
    assert get_quality_grade(52) == "D"
    assert get_quality_grade(45) == "F"


def test_score_clipping():
    """Test that scores are properly clipped to 0-100 range."""
    # Test with excessive violations
    df = pd.DataFrame({
        'facility_id': ['FAC001'],
        'period': ['2024-01'],
        'violation_count': [10],
        'flag_inconsistent': [True]
    })
    
    result = compute_consistency_score(df)
    
    # Should be clipped at 0, not negative
    assert result.iloc[0]['consistency_score'] >= 0


def test_compute_overall_scores_missing_subscores():
    """Test overall score computation with missing sub-scores."""
    # Only provide some sub-scores
    completeness = pd.DataFrame({
        'facility_id': ['FAC001'],
        'period': ['2024-01'],
        'completeness_score': [80.0],
        'flag_incomplete': [False]
    })
    
    timeliness = pd.DataFrame({
        'facility_id': ['FAC001'],
        'period': ['2024-01'],
        'timeliness_score': [90.0],
        'flag_late': [False]
    })
    
    all_scores = {
        'completeness': completeness,
        'timeliness': timeliness
    }
    
    weights = {
        'completeness': 30,
        'timeliness': 15
    }
    
    result = compute_overall_scores(all_scores, weights)
    
    # Should compute with available scores (missing ones filled with 100)
    assert len(result) == 1
    assert 'overall_score' in result.columns


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
