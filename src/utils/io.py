"""
Utility functions for file I/O operations.
"""
import os
from pathlib import Path
import pandas as pd
from typing import Union, Optional


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        path: Directory path to ensure exists
        
    Returns:
        Path object for the directory
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_csv(filepath: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    Read CSV file with error handling.
    
    Args:
        filepath: Path to CSV file
        **kwargs: Additional arguments for pd.read_csv
        
    Returns:
        DataFrame with loaded data
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    return pd.read_csv(filepath, **kwargs)


def write_csv(df: pd.DataFrame, filepath: Union[str, Path], **kwargs) -> None:
    """
    Write DataFrame to CSV with directory creation.
    
    Args:
        df: DataFrame to write
        filepath: Path to output CSV file
        **kwargs: Additional arguments for df.to_csv
    """
    filepath = Path(filepath)
    ensure_dir(filepath.parent)
    df.to_csv(filepath, index=False, **kwargs)


def read_parquet(filepath: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    Read Parquet file with error handling.
    
    Args:
        filepath: Path to Parquet file
        **kwargs: Additional arguments for pd.read_parquet
        
    Returns:
        DataFrame with loaded data
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    return pd.read_parquet(filepath, **kwargs)


def write_parquet(df: pd.DataFrame, filepath: Union[str, Path], **kwargs) -> None:
    """
    Write DataFrame to Parquet with directory creation.
    
    Args:
        df: DataFrame to write
        filepath: Path to output Parquet file
        **kwargs: Additional arguments for df.to_parquet
    """
    filepath = Path(filepath)
    ensure_dir(filepath.parent)
    df.to_parquet(filepath, index=False, **kwargs)


def safe_read(filepath: Union[str, Path], format: str = 'auto', **kwargs) -> Optional[pd.DataFrame]:
    """
    Safely read file with automatic format detection.
    
    Args:
        filepath: Path to file
        format: File format ('csv', 'parquet', or 'auto' for detection)
        **kwargs: Additional arguments for read functions
        
    Returns:
        DataFrame or None if file doesn't exist
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        return None
    
    if format == 'auto':
        format = filepath.suffix.lower().lstrip('.')
    
    if format == 'csv':
        return read_csv(filepath, **kwargs)
    elif format in ['parquet', 'pq']:
        return read_parquet(filepath, **kwargs)
    else:
        raise ValueError(f"Unsupported format: {format}")
