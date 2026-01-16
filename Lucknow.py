import streamlit as st
import pandas as pd
import io

# Main Category Mapping (exact match)
MAIN_CATEGORY_MAPPING = {
    # Sanitation (7 subcategories)
    "Garbage dumped on public land": "Sanitation",
    "Overflowing Dustbin": "Sanitation", 
    "Mud/silt sticking on structures on the roadsides/footpaths/Dividers": "Sanitation",
    "Burning of Garbage, Plastic, Leaves, Branches etc.": "Sanitation",
    "Road Dust/Sand Piled on Roadside": "Sanitation",
    "Road Dust": "Sanitation",
    "Garbage Burning at roadside": "Sanitation",
    
    # Malba (4 subcategories)
    "Malba, Bricks, Bori, etc on Dumping Land": "Malba",
    "Construction material lying unattended/encroaching public spaces": "Malba",
    "Construction and Demolition Activity Without Safeguards": "Malba",
    "C&D Waste Pick up request": "Malba",
    
    # Engineering (4 subcategories)
    "Pothole": "Engineering",
    "Unpaved road": "Engineering",
    "Broken Footpath/ Divider": "Engineering",
    "End to end pavement required": "Engineering"
}

@st.cache_data
def add_main_category(df):
    """Map Subcategory to MainCategory, default to Others"""
    df['MainCategory'] = df['Subcategory'].map(MAIN_CATEGORY_MAPPING).fillna('Others')
    return df

@st.cache_data
def add_status_binary(df):
    """Convert Status Name to Open/Resolved"""
    df['StatusBinary'] = df['Status Name'].apply(lambda x: 'Resolved' if 'Resolved' in str(x) else 'Open')
    return df

@st.cache_data
def add_department(df):
    """Map Assigned User Name to Department"""
    def get_department(assigned_user):
        if pd.isna(assigned_user):
            return 'LMC'
        assigned_user_str = str(assigned_user).strip()
        if assigned_user_str.startswith('PWD'):
            return 'PWD'
        elif assigned_user_str.startswith('LDA'):
            return 'LDA'
        else:
            return 'LMC'
    
    df['Department'] = df['Assigned User Name'].apply(get_department)
    return df

@st.cache_data
def generate_status_summary(df):
    """Generate the status-wise summary table"""
    summary = df.groupby(['MainCategory', 'StatusBinary']).size().unstack(fill_value=0)
    
    # Ensure columns exist
    if 'Open' not in summary.columns:
        summary['Open'] = 0
    if 'Resolved' not in summary.columns:
        summary['Resolved'] = 0
    
    # Calculate Grand Total first
    summary['Grand Total'] = summary['Open'] + summary['Resolved']
    
    # Calculate % Closure (avoid division by zero)
    summary['% Closure'] = summary.apply(
        lambda row: (row['Resolved'] / row['Grand Total'] * 100) if row['Grand Total'] > 0 else 0, 
        axis=1
    ).round(1)
    
    # Add TOTAL row
    total_open = summary['Open'].sum()
    total_resolved = summary['Resolved'].sum()
    total_grand = total_open + total_resolved
    total_pct = (total_resolved / total_grand * 100) if total_grand > 0 else 0
    
    total_row = pd.DataFrame({
        'Open': [total_open],
        'Resolved': [total_resolved],
        'Grand Total': [total_grand],
        '% Closure': [total_pct]
    }, index=['**TOTAL**'])
    
    summary = pd.concat([summary, total_row])
    return summary

@st.cache_data
def generate_subcategory_summary(df, main_category):
    """Generate subcategory drill-down for a specific MainCategory"""
    # Filter by MainCategory
    filtered_df = df[df['MainCategory'] == main_category]
    
    # Pivot by Subcategory and StatusBinary
    summary = filtered_df.groupby(['Subcategory', 'StatusBinary']).size().unstack(fill_value=0)
    
    # Ensure columns exist
    if 'Open' not in summary.columns:
        summary['Open'] = 0
    if 'Resolved' not in summary.columns:
        summary['Resolved'] = 0
    
    # Calculate Grand Total
    summary['Grand Total'] = summary['Open'] + summary['Resolved']
    
    # Calculate % Closure
    summary['% Closure'] = summary.apply(
        lambda row: (row['Resolved'] / row['Grand Total'] * 100) if row['Grand Total'] > 0 else 0, 
        axis=1
    ).round(1)
    
    # Add TOTAL row for this category
    total_open = summary['Open'].sum()
    total_resolved = summary['Resolved'].sum()
    total_grand = total_open + total_resolved
    total_pct = (total_resolved / total_grand * 100) if total_grand > 0 else 0
    
    total_row = pd.DataFrame({
        'Open': [total_open],
        'Resolved': [total_resolved],
        'Grand Total': [total_grand],
        '% Closure': [total_pct]
    }, index=[f'**{main_category} Total**'])
    
    summary = pd.concat([summary, total_row])
    return summary

@st.cache_data
def generate_zone_subcategory_summary(df, main_category, zone):
    """Generate subcategory drill-down for a specific MainCategory and Zone"""
    # Filter by MainCategory and Zone
    filtered_df = df[(df['MainCategory'] == main_category) & (df['Zone Name'] == zone)]
    
    if filtered_df.empty:
        return pd.DataFrame()
    
    # Pivot by Subcategory and StatusBinary
    summary = filtered_df.groupby(['Subcategory', 'StatusBinary']).size().unstack(fill_value=0)
    
    # Ensure columns exist
    if 'Open' not in summary.columns:
        summary['Open'] = 0
    if 'Resolved' not in summary.columns:
        summary['Resolved'] = 0
    
    # Calculate Grand Total
    summary['Grand Total'] = summary['Open'] + summary['Resolved']
    
    # Calculate % Closure
    summary['% Closure'] = summary.apply(
        lambda row: (row['Resolved'] / row['Grand Total'] * 100) if row['Grand Total'] > 0 else 0, 
        axis=1
    ).round(1)
    
    # Add TOTAL row for this zone+category combo
    total_open = summary['Open'].sum()
    total_resolved = summary['Resolved'].sum()
    total_grand = total_open + total_resolved
    total_pct = (total_resolved / total_grand * 100) if total_grand > 0 else 0
    
    total_row = pd.DataFrame({
        'Open': [total_open],
        'Resolved': [total_resolved],
        'Grand Total': [total_grand],
        '% Closure': [total_pct]
    }, index=[f'**{main_category} - {zone} Total**'])
    
    summary = pd.concat([summary, total_row])
    return summary

@st.cache_data
def generate_department_category_summary(df, department):
    """Generate department-wise main category summary"""
    # Filter by Department
    filtered_df = df[df['Department'] == department]
    
    if filtered_df.empty:
        return pd.DataFrame()
    
    # Pivot by MainCategory and StatusBinary
    summary = filtered_df.groupby(['MainCategory', 'StatusBinary']).size().unstack(fill_value=0)
    
    # Ensure columns exist
    if 'Open' not in summary.columns:
        summary['Open'] = 0
    if 'Resolved' not in summary.columns:
        summary['Resolved'] = 0
    
    # Calculate Grand Total
    summary['Grand Total'] = summary['Open'] + summary['Resolved']
    
    # Calculate % Closure
    summary['% Closure'] = summary.apply(
        lambda row: (row['Resolved'] / row['Grand Total'] * 100) if row['Grand Total'] > 0 else 0, 
        axis=1
    ).round(1)
    
    # Add TOTAL row for this department
    total_open = summary['Open'].sum()
    total_resolved = summary['Resolved'].sum()
    total_grand = total_open + total_resolved
    total_pct = (total_resolved / total_grand * 100) if total_grand > 0 else 0
    
    total_row = pd.DataFrame({
        'Open': [total_open],
        'Resolved': [total_resolved],
        'Grand Total': [total_grand],
        '% Closure': [total_pct]
    }, index=[f'**{department} Total**'])
    
    summary = pd.concat([summary, total_row])
    return summary

@st.cache_data
def get_all_subcategory_summaries(df, main_categories):
    """Pre-compute all subcategory summaries for faster downloads"""
    all_sub_data = []
    for main_cat in main_categories:
        sub_summary = generate_subcategory_summary(df, main_cat)
        sub_summary['MainCategory'] = main_cat
        all_sub_data.append(sub_summary.reset_index())
    
    return pd.concat(all_sub_data, ignore_index=True)

@st.cache_data
def generate_officer_performance_by_category(df, main_category):
    """Generate officer-wise ticket summary for a specific MainCategory (LMC only)"""
    # Filter: LMC department + MainCategory
    filtered_df = df[
        (df['Department'] == 'LMC') & 
        (df['MainCategory'] == main_category)
    ]
    
    if filtered_df.empty:
        return pd.DataFrame()
    
    # Pivot by Officer and StatusBinary
    officer_summary = filtered_df.groupby(['Assigned User Name', 'StatusBinary']).size().unstack(fill_value=0)
    
    # Ensure both columns exist
    if 'Open' not in officer_summary.columns:
        officer_summary['Open'] = 0
    if 'Resolved' not in officer_summary.columns:
        officer_summary['Resolved'] = 0
    
    # Calculate Total and % Closure
    officer_summary['Total'] = officer_summary['Open'] + officer_summary['Resolved']
    officer_summary['% Closure'] = officer_summary.apply(
        lambda row: (row['Resolved'] / row['Total'] * 100) if row['Total'] > 0 else 0,
        axis=1
    ).round(1)
    
    # Sort by Open (descending)
    officer_summary = officer_summary.sort_values('Open', ascending=False)
    
    # Reset index to make Officer Name a column
    officer_summary = officer_summary.reset_index()
    officer_summary.rename(columns={'Assigned User Name': 'Officer Name'}, inplace=True)
    
    # Add Rank column
    officer_summary.insert(0, 'Rank', range(1, len(officer_summary) + 1))
    
    # Reorder columns
    return officer_summary[['Rank', 'Officer Name', 'Open', 'Resolved', 'Total', '% Closure']]

@st.cache_data
def generate_officer_performance_by_zone(df, zone):
    """Generate officer-wise ticket summary for a specific Zone (LMC only)"""
    # Filter: LMC department + Zone
    filtered_df = df[
        (df['Department'] == 'LMC') & 
        (df['Zone Name'] == zone)
    ]
    
    if filtered_df.empty:
        return pd.DataFrame()
    
    # Pivot by Officer and StatusBinary
    officer_summary = filtered_df.groupby(['Assigned User Name', 'StatusBinary']).size().unstack(fill_value=0)
    
    # Ensure both columns exist
    if 'Open' not in officer_summary.columns:
        officer_summary['Open'] = 0
    if 'Resolved' not in officer_summary.columns:
        officer_summary['Resolved'] = 0
    
    # Calculate Total and % Closure
    officer_summary['Total'] = officer_summary['Open'] + officer_summary['Resolved']
    officer_summary['% Closure'] = officer_summary.apply(
        lambda row: (row['Resolved'] / row['Total'] * 100) if row['Total'] > 0 else 0,
        axis=1
    ).round(1)
    
    # Sort by Open (descending)
    officer_summary = officer_summary.sort_values('Open', ascending=False)
    
    # Reset index to make Officer Name a column
    officer_summary = officer_summary.reset_index()
    officer_summary.rename(columns={'Assigned User Name': 'Officer Name'}, inplace=True)
    
    # Add Rank column
    officer_summary.insert(0, 'Rank', range(1, len(officer_summary) + 1))
    
    # Reorder columns
    return officer_summary[['Rank', 'Officer Name', 'Open', 'Resolved', 'Total', '% Closure']]

@st.cache_data
def generate_officer_performance_category_zone(df, main_category, zone):
    """Generate officer-wise ticket summary for specific MainCategory AND Zone (LMC only)"""
    # Filter: LMC department + MainCategory + Zone
    filtered_df = df[
        (df['Department'] == 'LMC') & 
        (df['MainCategory'] == main_category) & 
        (df['Zone Name'] == zone)
    ]
    
    if filtered_df.empty:
        return pd.DataFrame()
    
    # Pivot by Officer and StatusBinary
    officer_summary = filtered_df.groupby(['Assigned User Name', 'StatusBinary']).size().unstack(fill_value=0)
    
    # Ensure both columns exist
    if 'Open' not in officer_summary.columns:
        officer_summary['Open'] = 0
    if 'Resolved' not in officer_summary.columns:
        officer_summary['Resolved'] = 0
    
    # Calculate Total and % Closure
    officer_summary['Total'] = officer_summary['Open'] + officer_summary['Resolved']
    officer_summary['% Closure'] = officer_summary.apply(
        lambda row: (row['Resolved'] / row['Total'] * 100) if row['Total'] > 0 else 0,
        axis=1
    ).round(1)
    
    # Sort by Open (descending)
    officer_summary = officer_summary.sort_values('Open', ascending=False)
    
    # Reset index to make Officer Name a column
    officer_summary = officer_summary.reset_index()
    officer_summary.rename(columns={'Assigned User Name': 'Officer Name'}, inplace=True)
    
    # Add Rank column
    officer_summary.insert(0, 'Rank', range(1, len(officer_summary) + 1))
    
    # Reorder columns
    return officer_summary[['Rank', 'Officer Name', 'Open', 'Resolved', 'Total', '% Closure']]

def main():
    st.set_page_config(page_title="Complaints Dashboard - Status Summary", layout="wide")
    
    st.title("📊 Complaints Status Summary Dashboard")
    st.markdown("---")
    
    # File upload
    uploaded_file = st.file_uploader("Upload XLSX file", type=['xlsx'], help="Upload your complaints data")
    
    if uploaded_file is not None:
        try:
            # Read Excel (cached)
            @st.cache_data
            def load_excel(file):
                return pd.read_excel(file)
            
            df = load_excel(uploaded_file)
            st.success(f"✅ Loaded {len(df)} records")
            
            # Step 1: Add MainCategory
            df_processed = add_main_category(df.copy())
            
            # Step 2: Add StatusBinary
            df_processed = add_status_binary(df_processed)
            
            # Step 3: Add Department
            df_processed = add_department(df_processed)
            
            # Generate summary
            summary_table = generate_status_summary(df_processed)
            
            # ========== BATCH 1: MAIN CATEGORY SUMMARY ==========
            st.subheader("📈 BATCH 1: Status-wise Summary by Main Category")
            st.dataframe(
                summary_table.round(1),
                use_container_width=True,
                hide_index=False,
                column_config={
                    '% Closure': st.column_config.NumberColumn(
                        "Closure %",
                        format="%.1f%%"
                    )
                }
            )
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Open", f"{int(summary_table.loc['**TOTAL**', 'Open']):,}")
            with col2:
                st.metric("Total Resolved", f"{int(summary_table.loc['**TOTAL**', 'Resolved']):,}")
            with col3:
                st.metric("Total Complaints", f"{int(summary_table.loc['**TOTAL**', 'Grand Total']):,}")
            with col4:
                st.metric("Overall Closure %", f"{summary_table.loc['**TOTAL**', '% Closure']:.1f}%")
            
            st.markdown("---")
            
            # ========== BATCH 2: SUBCATEGORY DRILL-DOWN ==========
            st.subheader("🔍 BATCH 2: Subcategory Drill-Down by Main Category")
            
            # Get unique MainCategories (excluding TOTAL row)
            main_categories = sorted(df_processed['MainCategory'].unique())
            
            # Create tabs for each MainCategory
            tabs = st.tabs([f"{cat} ({len(df_processed[df_processed['MainCategory'] == cat])})" for cat in main_categories])
            
            for tab, main_cat in zip(tabs, main_categories):
                with tab:
                    st.write(f"### {main_cat} - Subcategory Breakdown")
                    
                    # Generate subcategory summary (cached)
                    sub_summary = generate_subcategory_summary(df_processed, main_cat)
                    
                    # Display table
                    st.dataframe(
                        sub_summary.round(1),
                        use_container_width=True,
                        hide_index=False,
                        column_config={
                            '% Closure': st.column_config.NumberColumn(
                                "Closure %",
                                format="%.1f%%"
                            )
                        }
                    )
                    
                    # Metrics for this category
                    cat_total = sub_summary.loc[f'**{main_cat} Total**']
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Open", f"{int(cat_total['Open']):,}")
                    with col2:
                        st.metric("Resolved", f"{int(cat_total['Resolved']):,}")
                    with col3:
                        st.metric("Total", f"{int(cat_total['Grand Total']):,}")
                    with col4:
                        st.metric("Closure %", f"{cat_total['% Closure']:.1f}%")
            
            st.markdown("---")
            
            # ========== BATCH 3: ZONE-WISE DRILL-DOWN WITH TOGGLE ==========
            st.subheader("🗺️ BATCH 3: Zone-wise Drill-Down (Toggle by Category & Zone)")
            
            # Get unique zones
            zones = sorted(df_processed['Zone Name'].dropna().unique())
            
            # Create two columns for dropdown filters
            col1, col2 = st.columns(2)
            
            with col1:
                selected_category = st.selectbox(
                    "🏷️ Select Main Category",
                    options=main_categories,
                    key="batch3_category"
                )
            
            with col2:
                selected_zone = st.selectbox(
                    "🗺️ Select Zone",
                    options=zones,
                    key="batch3_zone"
                )
            
            # Generate zone+category summary (cached) - INSTANT TOGGLE NOW!
            zone_summary = generate_zone_subcategory_summary(df_processed, selected_category, selected_zone)
            
            if not zone_summary.empty:
                st.write(f"### {selected_category} - Zone {selected_zone} - Subcategory Breakdown")
                
                # Display table
                st.dataframe(
                    zone_summary.round(1),
                    use_container_width=True,
                    hide_index=False,
                    column_config={
                        '% Closure': st.column_config.NumberColumn(
                            "Closure %",
                            format="%.1f%%"
                        )
                    }
                )
                
                # Metrics for this zone+category combo
                zone_total = zone_summary.iloc[-1]  # Last row is the total
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Open", f"{int(zone_total['Open']):,}")
                with col2:
                    st.metric("Resolved", f"{int(zone_total['Resolved']):,}")
                with col3:
                    st.metric("Total", f"{int(zone_total['Grand Total']):,}")
                with col4:
                    st.metric("Closure %", f"{zone_total['% Closure']:.1f}%")
            else:
                st.warning(f"⚠️ No data found for {selected_category} in Zone {selected_zone}")
            
            st.markdown("---")
            
            # ========== BATCH 4: DEPARTMENT-WISE DRILL-DOWN WITH TOGGLE ==========
            st.subheader("🏢 BATCH 4: Department-wise Drill-Down (Toggle by Department)")
            
            # Get unique departments
            departments = sorted(df_processed['Department'].unique())
            
            # Create dropdown filter
            selected_department = st.selectbox(
                "🏢 Select Department",
                options=departments,
                key="batch4_department"
            )
            
            # Generate department+category summary (cached) - INSTANT TOGGLE NOW!
            dept_summary = generate_department_category_summary(df_processed, selected_department)
            
            if not dept_summary.empty:
                st.write(f"### {selected_department} - Main Category Breakdown")
                
                # Display table
                st.dataframe(
                    dept_summary.round(1),
                    use_container_width=True,
                    hide_index=False,
                    column_config={
                        '% Closure': st.column_config.NumberColumn(
                            "Closure %",
                            format="%.1f%%"
                        )
                    }
                )
                
                # Metrics for this department
                dept_total = dept_summary.iloc[-1]  # Last row is the total
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Open", f"{int(dept_total['Open']):,}")
                with col2:
                    st.metric("Resolved", f"{int(dept_total['Resolved']):,}")
                with col3:
                    st.metric("Total", f"{int(dept_total['Grand Total']):,}")
                with col4:
                    st.metric("Closure %", f"{dept_total['% Closure']:.1f}%")
            else:
                st.warning(f"⚠️ No data found for {selected_department}")
            
            st.markdown("---")
            
            # ========== BATCH 5: OFFICER PERFORMANCE TRACKING ==========
            st.subheader("👨‍💼 BATCH 5: LMC Officer Performance - Open Ticket Tracking")
            
            st.markdown("**Filter by Zone OR Main Category to see officer-wise open ticket distribution**")
            
            # Get unique zones for LMC
            lmc_df = df_processed[df_processed['Department'] == 'LMC']
            zones_lmc = sorted(lmc_df['Zone Name'].dropna().unique())
            
            # Create tabs for different filtering views
            perf_tab1, perf_tab2, perf_tab3 = st.tabs([
                "📍 By Zone",
                "🏷️ By Main Category",
                "🎯 By Zone + Category"
            ])
            
            # ========== TAB : FILTER BY ZONE + CATEGORY ==========
            with perf_tab3:
                st.write("### Officer Performance - Zone + Category Open Tickets")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    selected_zone_combo = st.selectbox(
                        "🗺️ Select Zone",
                        options=zones_lmc,
                        key="batch5_zone_combo"
                    )
                
                with col2:
                    selected_category_combo = st.selectbox(
                        "🏷️ Select Main Category",
                        options=main_categories,
                        key="batch5_category_combo"
                    )
                
                officer_perf_combo = generate_officer_performance_category_zone(
                    df_processed, selected_category_combo, selected_zone_combo
                )
                
                if not officer_perf_combo.empty:
                    st.write(f"**Zone: {selected_zone_combo} | Category: {selected_category_combo}** | **Total Open: {officer_perf_combo['Open'].sum():,}** | **Officers: {len(officer_perf_combo)}**")
                    
                    st.dataframe(
                        officer_perf_combo,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            'Rank': st.column_config.NumberColumn("Rank", width=50),
                            'Officer Name': st.column_config.TextColumn("Officer Name", width=250),
                            'Open': st.column_config.NumberColumn("Open", width=80),
                            'Resolved': st.column_config.NumberColumn("Resolved", width=80),
                            'Total': st.column_config.NumberColumn("Total", width=80),
                            '% Closure': st.column_config.NumberColumn("% Closure", width=100, format="%.1f%%")
                        }
                    )
                    
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Open", f"{officer_perf_combo['Open'].sum():,}")
                    with col2:
                        st.metric("Total Resolved", f"{officer_perf_combo['Resolved'].sum():,}")
                    with col3:
                        st.metric("Active Officers", len(officer_perf_combo))
                    with col4:
                        avg_closure = (officer_perf_combo['Resolved'].sum() / officer_perf_combo['Total'].sum() * 100) if officer_perf_combo['Total'].sum() > 0 else 0
                        st.metric("Combo Closure %", f"{avg_closure:.1f}%")
                else:
                    st.warning(f"⚠️ No LMC complaints found for Zone {selected_zone_combo} in category {selected_category_combo}")
            
            st.markdown("---")
            
            # ========== DOWNLOADS ==========
            st.subheader("📥 Download Reports")
            
            col1, col2 = st.columns(2)
            
            # Download Batch 1 (Main Category Summary)
            with col1:
                csv_buffer1 = io.StringIO()
                summary_table.to_csv(csv_buffer1)
                st.download_button(
                    label="📥 Download Batch 1: Main Category Summary",
                    data=csv_buffer1.getvalue(),
                    file_name="batch1_main_category_summary.csv",
                    mime="text/csv"
                )
            
            # Download All Batch 2 (All Subcategory Summaries combined) - now cached!
            with col2:
                combined_sub = get_all_subcategory_summaries(df_processed, main_categories)
                csv_buffer2 = io.StringIO()
                combined_sub.to_csv(csv_buffer2, index=False)
                st.download_button(
                    label="📥 Download Batch 2: All Subcategories",
                    data=csv_buffer2.getvalue(),
                    file_name="batch2_all_subcategories.csv",
                    mime="text/csv"
                )
            
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.exception(e)
    
    else:
        st.info("👆 Upload your XLSX file to get started")

if __name__ == "__main__":
    main()
