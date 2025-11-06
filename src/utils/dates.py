"""
Utility functions for date and period handling.
"""
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
from typing import Union, Tuple


def parse_period(period: str) -> datetime:
    """
    Parse period string (YYYY-MM format) to datetime.
    
    Args:
        period: Period string in YYYY-MM format
        
    Returns:
        Datetime object representing the first day of the period
    """
    return pd.to_datetime(period, format='%Y-%m')


def period_to_str(dt: datetime) -> str:
    """
    Convert datetime to period string (YYYY-MM format).
    
    Args:
        dt: Datetime object
        
    Returns:
        Period string in YYYY-MM format
    """
    return dt.strftime('%Y-%m')


def get_period_bounds(period: str) -> Tuple[datetime, datetime]:
    """
    Get start and end dates for a period.
    
    Args:
        period: Period string in YYYY-MM format
        
    Returns:
        Tuple of (period_start, period_end) datetime objects
    """
    period_start = parse_period(period)
    period_end = period_start + relativedelta(months=1) - timedelta(days=1)
    return period_start, period_end


def make_due_date(period: str, due_days: int = 7) -> datetime:
    """
    Calculate submission due date for a period.
    
    Args:
        period: Period string in YYYY-MM format
        due_days: Number of days after period end for submission deadline
        
    Returns:
        Due date datetime
    """
    _, period_end = get_period_bounds(period)
    return period_end + timedelta(days=due_days)


def compute_days_late(submission_date: Union[str, datetime], 
                      period: str, 
                      due_days: int = 7) -> int:
    """
    Compute how many days late a submission is.
    
    Args:
        submission_date: Date of submission (string or datetime)
        period: Period string in YYYY-MM format
        due_days: Number of days after period end for submission deadline
        
    Returns:
        Number of days late (negative if early, 0 if on time)
    """
    if isinstance(submission_date, str):
        submission_date = pd.to_datetime(submission_date)
    
    due_date = make_due_date(period, due_days)
    days_late = (submission_date - due_date).days
    return days_late


def generate_periods(start_period: str, num_months: int) -> list:
    """
    Generate list of period strings.
    
    Args:
        start_period: Starting period in YYYY-MM format
        num_months: Number of months to generate
        
    Returns:
        List of period strings
    """
    start = parse_period(start_period)
    periods = []
    for i in range(num_months):
        period_date = start + relativedelta(months=i)
        periods.append(period_to_str(period_date))
    return periods


def add_months_to_period(period: str, months: int) -> str:
    """
    Add months to a period string.
    
    Args:
        period: Period string in YYYY-MM format
        months: Number of months to add (can be negative)
        
    Returns:
        New period string
    """
    dt = parse_period(period)
    new_dt = dt + relativedelta(months=months)
    return period_to_str(new_dt)
