"""
Data Quality Assessment Pipeline Orchestration.

Coordinates the execution of all DQA checks and metrics computation.
"""
import argparse
import sys
from pathlib import Path
import yaml
import pandas as pd
from tabulate import tabulate

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.io import read_csv
from src.quality.rules import run_all_checks
from src.quality.metrics import compute_all_metrics


def load_config(config_path: str) -> dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config YAML file
        
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def print_summary_report(
    reports_df: pd.DataFrame,
    check_results: dict,
    summaries: dict
):
    """
    Print a summary report of the DQA pipeline run.
    
    Args:
        reports_df: Original reports DataFrame
        check_results: Dictionary of check results
        summaries: Dictionary of summary DataFrames
    """
    print("\n" + "="*70)
    print("DATA QUALITY ASSESSMENT SUMMARY")
    print("="*70)
    
    # Basic statistics
    print("\n📊 Data Overview")
    print("-" * 70)
    overview = [
        ["Total facilities", reports_df['facility_id'].nunique()],
        ["Total periods", reports_df['period'].nunique()],
        ["Total records", len(reports_df)],
        ["Date range", f"{reports_df['period'].min()} to {reports_df['period'].max()}"]
    ]
    print(tabulate(overview, tablefmt='simple'))
    
    # Quality scores
    print("\n⭐ National Quality Scores (0-100)")
    print("-" * 70)
    detailed = summaries['detailed']
    score_cols = [col for col in detailed.columns if col.endswith('_score')]
    scores_table = []
    for col in score_cols:
        component = col.replace('_score', '').replace('_', ' ').title()
        score = detailed[col].mean()
        grade = get_grade(score)
        scores_table.append([component, f"{score:.1f}", grade])
    
    print(tabulate(scores_table, headers=['Component', 'Score', 'Grade'], tablefmt='simple'))
    
    # Issues summary
    print("\n⚠️  Quality Issues Detected")
    print("-" * 70)
    flag_cols = [col for col in detailed.columns if col.startswith('flag_')]
    issues_table = []
    for col in flag_cols:
        issue_type = col.replace('flag_', '').replace('_', ' ').title()
        count = detailed[col].sum()
        rate = (count / len(detailed)) * 100
        issues_table.append([issue_type, int(count), f"{rate:.1f}%"])
    
    print(tabulate(issues_table, headers=['Issue Type', 'Count', '% of Records'], tablefmt='simple'))
    
    # Top and bottom states
    print("\n🏆 Top 5 States by Overall Score")
    print("-" * 70)
    state_summary = summaries['state']
    top_states = state_summary.nlargest(5, 'overall_score')
    top_table = []
    for _, row in top_states.iterrows():
        top_table.append([
            row['state'],
            f"{row['overall_score']:.1f}",
            int(row['num_facilities']),
            int(row['num_records'])
        ])
    print(tabulate(top_table, headers=['State', 'Score', 'Facilities', 'Records'], tablefmt='simple'))
    
    print("\n⚠️  Bottom 5 States by Overall Score")
    print("-" * 70)
    bottom_states = state_summary.nsmallest(5, 'overall_score')
    bottom_table = []
    for _, row in bottom_states.iterrows():
        bottom_table.append([
            row['state'],
            f"{row['overall_score']:.1f}",
            int(row['num_facilities']),
            int(row['num_records'])
        ])
    print(tabulate(bottom_table, headers=['State', 'Score', 'Facilities', 'Records'], tablefmt='simple'))
    
    print("\n" + "="*70)
    print("✓ DQA Pipeline Complete")
    print("="*70)


def get_grade(score: float) -> str:
    """Get letter grade for a score."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def run_pipeline(
    reports_path: str,
    registry_path: str,
    config_path: str,
    output_dir: str
):
    """
    Run the complete DQA pipeline.
    
    Args:
        reports_path: Path to facility reports CSV
        registry_path: Path to facility registry CSV
        config_path: Path to configuration YAML
        output_dir: Directory for output files
    """
    print("\n" + "="*70)
    print("HEALTH DATA QUALITY ASSESSMENT PIPELINE")
    print("="*70)
    
    # Load configuration
    print(f"\n📋 Loading configuration from {config_path}...")
    config = load_config(config_path)
    
    # Load data
    print(f"\n📁 Loading data...")
    print(f"  - Reports: {reports_path}")
    reports_df = read_csv(reports_path)
    print(f"    Loaded {len(reports_df)} records")
    
    print(f"  - Registry: {registry_path}")
    registry_df = read_csv(registry_path)
    print(f"    Loaded {len(registry_df)} facilities")
    
    # Run quality checks
    print(f"\n🔍 Running quality checks...")
    check_results = run_all_checks(reports_df, registry_df, config)
    
    # Compute metrics and save outputs
    output_path = Path(output_dir)
    summaries = compute_all_metrics(check_results, registry_df, config, output_path)
    
    # Print summary report
    print_summary_report(reports_df, check_results, summaries)
    
    # Print output files
    print(f"\n📄 Output Files:")
    print(f"  - {output_path / 'dqa_results_facility_month.csv'}")
    print(f"  - {output_path / 'dqa_summary_facility.csv'}")
    print(f"  - {output_path / 'dqa_summary_state.csv'}")
    print(f"  - reports/metrics_summary.json")
    print()


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Run Data Quality Assessment pipeline on health facility data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default paths
  python -m src.quality.dqa_pipeline
  
  # Run with custom paths
  python -m src.quality.dqa_pipeline \\
    --in data/raw/facility_reports.csv \\
    --registry data/raw/facility_registry.csv \\
    --config config/dqa_config.yml \\
    --out data/processed
        """
    )
    
    parser.add_argument(
        '--in',
        dest='reports',
        type=str,
        default='data/raw/facility_reports.csv',
        help='Path to facility reports CSV (default: data/raw/facility_reports.csv)'
    )
    
    parser.add_argument(
        '--registry',
        type=str,
        default='data/raw/facility_registry.csv',
        help='Path to facility registry CSV (default: data/raw/facility_registry.csv)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/dqa_config.yml',
        help='Path to configuration YAML (default: config/dqa_config.yml)'
    )
    
    parser.add_argument(
        '--out',
        dest='output',
        type=str,
        default='data/processed',
        help='Output directory for results (default: data/processed)'
    )
    
    args = parser.parse_args()
    
    # Check if input files exist
    reports_path = Path(args.reports)
    registry_path = Path(args.registry)
    config_path = Path(args.config)
    
    if not reports_path.exists():
        print(f"❌ Error: Reports file not found: {reports_path}")
        print("\nPlease generate data first:")
        print("  python -m src.data.generate_synthetic_routine_data")
        sys.exit(1)
    
    if not registry_path.exists():
        print(f"❌ Error: Registry file not found: {registry_path}")
        print("\nPlease generate data first:")
        print("  python -m src.data.generate_synthetic_routine_data")
        sys.exit(1)
    
    if not config_path.exists():
        print(f"❌ Error: Config file not found: {config_path}")
        sys.exit(1)
    
    # Run pipeline
    try:
        run_pipeline(
            str(reports_path),
            str(registry_path),
            str(config_path),
            args.output
        )
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
