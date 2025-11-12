#!/usr/bin/env python3
"""
Generate donor-facing charts from DQA pipeline outputs.
Creates two charts:
1. dqa-score-by-state.png - Bar chart showing quality scores by state
2. dqa-score-trend.png - Time series showing quality metric trends
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style for professional-looking charts
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9

def load_data():
    """Load DQA summary data."""
    state_summary = pd.read_csv('../data/processed/dqa_summary_state.csv')
    facility_month = pd.read_csv('../data/processed/dqa_results_facility_month.csv')
    return state_summary, facility_month

def create_state_chart(state_summary, output_path):
    """Create bar chart of DQA scores by state."""
    # Sort states by overall score
    state_summary_sorted = state_summary.sort_values('overall_score', ascending=True)
    
    # Create figure with appropriate size (1200x675 pixels at 150 DPI = 8x4.5 inches)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    
    # Color bars by score - use traffic light colors
    colors = []
    for score in state_summary_sorted['overall_score']:
        if score >= 90:
            colors.append('#2ecc71')  # Green
        elif score >= 80:
            colors.append('#f39c12')  # Orange
        else:
            colors.append('#e74c3c')  # Red
    
    # Create horizontal bar chart
    bars = ax.barh(range(len(state_summary_sorted)), 
                    state_summary_sorted['overall_score'],
                    color=colors, alpha=0.85)
    
    # Set y-axis labels
    ax.set_yticks(range(len(state_summary_sorted)))
    ax.set_yticklabels(state_summary_sorted['state'], fontsize=8)
    
    # Set labels and title
    ax.set_xlabel('Quality Score (0-100)', fontweight='bold')
    ax.set_title('Data Quality Scores by State\nNigeria Health Facility Reporting System', 
                 fontweight='bold', pad=15)
    
    # Add score labels on bars
    for i, (idx, row) in enumerate(state_summary_sorted.iterrows()):
        score = row['overall_score']
        ax.text(score + 0.5, i, f'{score:.1f}', 
                va='center', fontsize=7, fontweight='bold')
    
    # Add reference lines
    ax.axvline(x=90, color='green', linestyle='--', alpha=0.3, linewidth=1)
    ax.axvline(x=80, color='orange', linestyle='--', alpha=0.3, linewidth=1)
    
    # Add legend for color coding
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2ecc71', alpha=0.85, label='Excellent (≥90)'),
        Patch(facecolor='#f39c12', alpha=0.85, label='Good (80-89)'),
        Patch(facecolor='#e74c3c', alpha=0.85, label='Needs Improvement (<80)')
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=8, framealpha=0.9)
    
    # Set x-axis limits
    ax.set_xlim(75, 100)
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Add grid for readability
    ax.grid(axis='x', alpha=0.3, linestyle='-', linewidth=0.5)
    
    # Tight layout
    plt.tight_layout()
    
    # Save figure
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✓ Created: {output_path}")
    plt.close()

def create_trend_chart(facility_month, output_path):
    """Create time series chart of quality metric trends."""
    # Aggregate by period
    trend_data = facility_month.groupby('period').agg({
        'overall_score': 'mean',
        'completeness_score': 'mean',
        'timeliness_score': 'mean',
        'consistency_score': 'mean'
    }).reset_index()
    
    # Sort by period
    trend_data = trend_data.sort_values('period')
    
    # Create figure
    fig, ax = plt.subplots(figsize=(8, 4.5))
    
    # Plot lines for key metrics
    ax.plot(range(len(trend_data)), trend_data['overall_score'], 
            marker='o', linewidth=2.5, markersize=5, label='Overall Quality', 
            color='#3498db', alpha=0.9)
    ax.plot(range(len(trend_data)), trend_data['completeness_score'], 
            marker='s', linewidth=2, markersize=4, label='Completeness', 
            color='#2ecc71', alpha=0.8, linestyle='--')
    ax.plot(range(len(trend_data)), trend_data['timeliness_score'], 
            marker='^', linewidth=2, markersize=4, label='Timeliness', 
            color='#e74c3c', alpha=0.8, linestyle='--')
    ax.plot(range(len(trend_data)), trend_data['consistency_score'], 
            marker='d', linewidth=2, markersize=4, label='Consistency', 
            color='#9b59b6', alpha=0.8, linestyle='--')
    
    # Set x-axis labels - show every 3rd month to avoid crowding
    x_labels = [period if i % 3 == 0 else '' for i, period in enumerate(trend_data['period'])]
    ax.set_xticks(range(len(trend_data)))
    ax.set_xticklabels(x_labels, rotation=45, ha='right', fontsize=8)
    
    # Set labels and title
    ax.set_xlabel('Reporting Period', fontweight='bold')
    ax.set_ylabel('Quality Score (0-100)', fontweight='bold')
    ax.set_title('Data Quality Trends Over Time\nNigeria Health Facility Reporting System', 
                 fontweight='bold', pad=15)
    
    # Add reference line at 90 (excellence threshold)
    ax.axhline(y=90, color='gray', linestyle=':', alpha=0.5, linewidth=1)
    ax.text(len(trend_data)-1, 91, 'Excellence (90)', fontsize=7, 
            ha='right', va='bottom', color='gray')
    
    # Set y-axis limits
    ax.set_ylim(40, 105)
    
    # Add legend
    ax.legend(loc='lower right', fontsize=9, framealpha=0.9)
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Add grid
    ax.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
    
    # Tight layout
    plt.tight_layout()
    
    # Save figure
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✓ Created: {output_path}")
    plt.close()

def main():
    """Generate both donor-facing charts."""
    print("Generating donor-facing charts...")
    
    # Load data
    state_summary, facility_month = load_data()
    
    # Create output directory
    output_dir = Path('figures')
    output_dir.mkdir(exist_ok=True)
    
    # Generate charts
    create_state_chart(state_summary, output_dir / 'dqa-score-by-state.png')
    create_trend_chart(facility_month, output_dir / 'dqa-score-trend.png')
    
    print("\n✓ All charts generated successfully!")

if __name__ == '__main__':
    main()
