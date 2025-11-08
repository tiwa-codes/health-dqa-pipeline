"""
Streamlit dashboard for interactive DQA results exploration.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Page configuration
st.set_page_config(
    page_title="Health DQA Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data
def load_data():
    """Load all DQA results with caching."""
    try:
        detailed = pd.read_csv('data/processed/dqa_results_facility_month.csv')
        facility_summary = pd.read_csv('data/processed/dqa_summary_facility.csv')
        state_summary = pd.read_csv('data/processed/dqa_summary_state.csv')
        registry = pd.read_csv('data/raw/facility_registry.csv')
        
        # Merge detailed with registry for filters
        detailed_merged = detailed.merge(
            registry[['facility_id', 'state', 'lga', 'facility_type', 'ownership']],
            on='facility_id',
            how='left'
        )
        
        # Ensure expected score/flag columns exist to avoid KeyErrors in plotting
        expected_score_cols = [
            'overall_score', 'completeness_score', 'timeliness_score'
        ]
        expected_flag_cols = [
            'flag_incomplete', 'flag_outlier', 'flag_spike', 'flag_inconsistent'
        ]
        for col in expected_score_cols:
            if col not in detailed_merged.columns:
                detailed_merged[col] = 0.0
        for col in expected_flag_cols:
            if col not in detailed_merged.columns:
                detailed_merged[col] = False
        
        # Load metrics summary
        with open('reports/metrics_summary.json', 'r') as f:
            metrics_summary = json.load(f)
        
        return {
            'detailed': detailed_merged,
            'facility': facility_summary,
            'state': state_summary,
            'registry': registry,
            'summary': metrics_summary
        }
    except FileNotFoundError as e:
        st.error(f"Data files not found: {e}")
        st.info("Please run the DQA pipeline first:\n```\npython -m src.quality.dqa_pipeline\n```")
        st.stop()


def create_sidebar_filters(data):
    """Create sidebar filters and return filtered data."""
    st.sidebar.header("🔍 Filters")
    
    # State filter
    all_states = sorted(data['detailed']['state'].dropna().unique())
    selected_states = st.sidebar.multiselect(
        "Select States",
        options=all_states,
        default=all_states[:5]  # Default to first 5 states
    )
    
    # LGA filter (dependent on states)
    if selected_states:
        available_lgas = sorted(
            data['detailed'][data['detailed']['state'].isin(selected_states)]['lga'].dropna().unique()
        )
        selected_lgas = st.sidebar.multiselect(
            "Select LGAs",
            options=available_lgas,
            default=[]
        )
    else:
        selected_lgas = []
    
    # Facility type filter
    facility_types = sorted(data['detailed']['facility_type'].dropna().unique())
    selected_facility_types = st.sidebar.multiselect(
        "Facility Type",
        options=facility_types,
        default=facility_types
    )
    
    # Ownership filter
    ownerships = sorted(data['detailed']['ownership'].dropna().unique())
    selected_ownerships = st.sidebar.multiselect(
        "Ownership",
        options=ownerships,
        default=ownerships
    )
    
    # Period range filter
    all_periods = sorted(data['detailed']['period'].unique())
    period_range = st.sidebar.select_slider(
        "Period Range",
        options=all_periods,
        value=(all_periods[0], all_periods[-1])
    )
    
    # Apply filters
    filtered = data['detailed'].copy()
    
    if selected_states:
        filtered = filtered[filtered['state'].isin(selected_states)]
    
    if selected_lgas:
        filtered = filtered[filtered['lga'].isin(selected_lgas)]
    
    filtered = filtered[filtered['facility_type'].isin(selected_facility_types)]
    filtered = filtered[filtered['ownership'].isin(selected_ownerships)]
    filtered = filtered[
        (filtered['period'] >= period_range[0]) & 
        (filtered['period'] <= period_range[1])
    ]
    
    return filtered, {
        'states': selected_states,
        'lgas': selected_lgas,
        'facility_types': selected_facility_types,
        'ownerships': selected_ownerships,
        'period_range': period_range
    }


def display_kpis(filtered_data):
    """Display key performance indicators."""
    st.header("📊 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_score = filtered_data['overall_score'].mean()
        st.metric(
            "Overall Quality Score",
            f"{avg_score:.1f}",
            delta=None,
            help="Average overall quality score (0-100)"
        )
    
    with col2:
        completeness = filtered_data['completeness_score'].mean()
        st.metric(
            "Completeness Score",
            f"{completeness:.1f}",
            delta=None,
            help="Average data completeness score"
        )
    
    with col3:
        timeliness = filtered_data['timeliness_score'].mean()
        st.metric(
            "Timeliness Score",
            f"{timeliness:.1f}",
            delta=None,
            help="Average submission timeliness score"
        )
    
    with col4:
        outlier_rate = filtered_data['flag_incomplete'].sum() / len(filtered_data) * 100
        st.metric(
            "Records with Issues",
            f"{outlier_rate:.1f}%",
            delta=None,
            help="Percentage of records flagged with issues"
        )


def plot_state_scores(state_summary, selected_states):
    """Plot state-level quality scores."""
    st.header("🗺️ State-Level Quality Scores")
    
    # Filter to selected states if any
    if selected_states:
        plot_data = state_summary[state_summary['state'].isin(selected_states)]
    else:
        plot_data = state_summary
    
    # Sort by score
    plot_data = plot_data.sort_values('overall_score', ascending=True)
    
    fig = px.bar(
        plot_data,
        x='overall_score',
        y='state',
        orientation='h',
        title='Overall Quality Score by State',
        labels={'overall_score': 'Quality Score', 'state': 'State'},
        color='overall_score',
        color_continuous_scale='RdYlGn',
        range_color=[0, 100]
    )
    
    fig.update_layout(height=max(400, len(plot_data) * 25))
    st.plotly_chart(fig, width='stretch')


def plot_score_components(filtered_data):
    """Plot quality score components"""
    st.header("📈 Quality Score Components")
    
    score_cols = [col for col in filtered_data.columns if col.endswith('_score')]
    
    # Calculate averages
    avg_scores = {
        col.replace('_score', '').replace('_', ' ').title(): filtered_data[col].mean()
        for col in score_cols
    }
    
    df_scores = pd.DataFrame({
        'Component': list(avg_scores.keys()),
        'Score': list(avg_scores.values())
    })
    
    fig = px.bar(
        df_scores,
        x='Component',
        y='Score',
        title='Average Score by Component',
        labels={'Score': 'Average Score (0-100)'},
        color='Score',
        color_continuous_scale='RdYlGn',
        range_color=[0, 100]
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, width='stretch')


def plot_time_series(filtered_data):
    """Plot quality scores over time."""
    st.header("📅 Quality Trends Over Time")
    
    # Ensure the columns we will aggregate exist
    for col in ['overall_score', 'completeness_score', 'timeliness_score', 'flag_outlier', 'flag_spike']:
        if col not in filtered_data.columns:
            filtered_data[col] = 0 if col.startswith('flag_') else 0.0
    
    # Aggregate by period
    time_series = filtered_data.groupby('period').agg({
        'overall_score': 'mean',
        'completeness_score': 'mean',
        'timeliness_score': 'mean',
        'flag_outlier': 'sum',
        'flag_spike': 'sum'
    }).reset_index()
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=time_series['period'],
        y=time_series['overall_score'],
        name='Overall Score',
        mode='lines+markers',
        line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=time_series['period'],
        y=time_series['completeness_score'],
        name='Completeness',
        mode='lines',
        line=dict(color='green', width=1, dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=time_series['period'],
        y=time_series['timeliness_score'],
        name='Timeliness',
        mode='lines',
        line=dict(color='orange', width=1, dash='dash')
    ))
    
    fig.update_layout(
        title='Quality Scores Over Time',
        xaxis_title='Period',
        yaxis_title='Score (0-100)',
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig, width='stretch')


def plot_issue_distribution(filtered_data):
    """Plot distribution of quality issues."""
    st.header("⚠️ Quality Issues Distribution")
    
    flag_cols = [col for col in filtered_data.columns if col.startswith('flag_')]
    
    issue_counts = {
        col.replace('flag_', '').replace('_', ' ').title(): filtered_data[col].sum()
        for col in flag_cols
    }
    
    df_issues = pd.DataFrame({
        'Issue Type': list(issue_counts.keys()),
        'Count': list(issue_counts.values())
    })
    
    df_issues = df_issues.sort_values('Count', ascending=True)
    
    fig = px.bar(
        df_issues,
        x='Count',
        y='Issue Type',
        orientation='h',
        title='Count of Quality Issues',
        labels={'Count': 'Number of Records Flagged'},
        color='Count',
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, width='stretch')


def display_facility_table(filtered_data, facility_summary):
    """Display interactive facility table."""
    st.header("🏥 Facility Performance Table")
    
    # Get facilities in filtered data
    filtered_facility_ids = filtered_data['facility_id'].unique()
    facility_table = facility_summary[
        facility_summary['facility_id'].isin(filtered_facility_ids)
    ].copy()
    
    # Merge with registry for display
    registry = pd.read_csv('data/raw/facility_registry.csv')
    facility_table = facility_table.merge(
        registry[['facility_id', 'facility_name', 'state', 'facility_type']],
        on='facility_id',
        how='left'
    )
    
    # Select and order columns
    display_cols = [
        'facility_id', 'facility_name', 'state', 'facility_type',
        'overall_score', 'completeness_score', 'timeliness_score',
        'num_periods'
    ]
    
    display_cols = [col for col in display_cols if col in facility_table.columns]
    facility_table = facility_table[display_cols]
    
    # Sort by overall score
    facility_table = facility_table.sort_values('overall_score', ascending=False)
    
    # Display with formatting
    st.dataframe(
        facility_table.style.format({
            'overall_score': '{:.1f}',
            'completeness_score': '{:.1f}',
            'timeliness_score': '{:.1f}'
        }).background_gradient(
            subset=['overall_score'],
            cmap='RdYlGn',
            vmin=0,
            vmax=100
        ),
        height=400
    )
    
    # Download button
    csv = facility_table.to_csv(index=False)
    st.download_button(
        label="📥 Download Facility Data",
        data=csv,
        file_name='facility_quality_scores.csv',
        mime='text/csv'
    )


def display_detailed_analysis(data):
    """Display detailed analysis section using the cached/loaded data."""
    st.header("🔬 Detailed Analysis")

    tab1, tab2, tab3 = st.tabs(["Outliers", "Spikes", "Consistency Issues"])

    detailed = data['detailed'].copy()
    registry = data.get('registry')
    if registry is None:
        registry = pd.read_csv('data/raw/facility_registry.csv')

    # Ensure display fields: merge if either facility_name or state missing
    if not {'facility_name', 'state'}.issubset(set(detailed.columns)):
        detailed = detailed.merge(registry[['facility_id', 'facility_name', 'state']], on='facility_id', how='left')

    # Ensure expected flag cols exist
    for col in ['flag_outlier', 'flag_spike', 'flag_inconsistent']:
        if col not in detailed.columns:
            detailed[col] = False

    def safe_display(df, wanted_cols, **kwargs):
        cols = [c for c in wanted_cols if c in df.columns]
        st.dataframe(df[cols].head(50), **kwargs)

    with tab1:
        st.subheader("Records Flagged as Outliers")
        outliers = detailed[detailed.get('flag_outlier', False) == True]
        if len(outliers) > 0:
            st.write(f"Found {len(outliers)} facility-months with outliers")
            safe_display(outliers, ['facility_id', 'facility_name', 'state', 'period', 'overall_score'], height=300)
        else:
            st.info("No outliers detected")

    with tab2:
        st.subheader("Records Flagged with Spikes")
        spikes = detailed[detailed.get('flag_spike', False) == True]
        if len(spikes) > 0:
            st.write(f"Found {len(spikes)} facility-months with spikes")
            safe_display(spikes, ['facility_id', 'facility_name', 'state', 'period', 'overall_score'], height=300)
        else:
            st.info("No spikes detected")

    with tab3:
        st.subheader("Records with Consistency Violations")
        inconsistent = detailed[detailed.get('flag_inconsistent', False) == True]
        if len(inconsistent) > 0:
            st.write(f"Found {len(inconsistent)} facility-months with consistency issues")
            safe_display(inconsistent, ['facility_id', 'facility_name', 'state', 'period', 'overall_score'], height=300)
        else:
            st.info("No consistency violations detected")


def main():
    """Main dashboard application."""
    # Title
    st.title("🏥 Health Data Quality Assessment Dashboard")
    st.markdown("**Nigeria Routine Health Facility Reporting System**")
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading data..."):
        data = load_data()
    
    # Sidebar filters
    filtered_data, filters = create_sidebar_filters(data)
    
    # Show filter summary
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Showing {len(filtered_data):,} records**")
    st.sidebar.markdown(f"**{filtered_data['facility_id'].nunique()} facilities**")
    
    # Main content
    if len(filtered_data) == 0:
        st.warning("No data matches the selected filters. Please adjust your selections.")
        return
    
    # KPIs
    display_kpis(filtered_data)
    
    st.markdown("---")
    
    # Charts in columns
    col1, col2 = st.columns(2)
    
    with col1:
        plot_score_components(filtered_data)
    
    with col2:
        plot_issue_distribution(filtered_data)
    
    # State scores
    if filters['states']:
        plot_state_scores(data['state'], filters['states'])
    
    # Time series
    plot_time_series(filtered_data)
    
    st.markdown("---")
    
    # Facility table
    display_facility_table(filtered_data, data['facility'])
    
    st.markdown("---")
    
    # Detailed analysis
    display_detailed_analysis(data)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    **About this Dashboard**
    
    This dashboard provides interactive exploration of routine health data quality.
    Use the filters in the sidebar to focus on specific states, facility types, or time periods.
    
    **Interpretation Guide:**
    - **Overall Score**: Weighted composite of all quality dimensions (0-100)
    - **Completeness**: Percentage of required fields with data
    - **Timeliness**: Score based on submission delays
    - **Outliers**: Values significantly different from peers
    - **Spikes**: Sudden large changes month-over-month
    - **Consistency**: Logical relationships between indicators
    
    *Note: This dashboard uses synthetic data for demonstration purposes.*
    """)


if __name__ == "__main__":
    main()
