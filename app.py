import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder

# Set page layout to wide
st.set_page_config(layout="wide")

# Load data
df = pd.read_csv('simulation_metrics.csv')

# Streamlit app
st.title('Simulation Metrics')

# Directory selection
dir_options = df['TOP_DIR'].unique()
selected_dirs = st.multiselect('Select directories', dir_options, default=dir_options)

# Experiment selection
exp_options = df['EXPERIMENT'].unique()
selected_exps = st.multiselect('Select experiments', exp_options, default=exp_options)

# Test case selection
testcase_options = df['TESTCASE'].unique()
selected_testcases = st.multiselect('Select test cases', testcase_options, default=testcase_options)

# Metric selection
metric_options = [col for col in df.columns if col.startswith('METRIC')]
selected_metrics = st.multiselect('Select metrics', metric_options, default=metric_options[:3])

# Filter data
filtered_df = df[(df['TOP_DIR'].isin(selected_dirs)) & 
                 (df['EXPERIMENT'].isin(selected_exps)) & 
                 (df['TESTCASE'].isin(selected_testcases))]

# Melt data to long format
melted_df = pd.melt(filtered_df, 
                    id_vars=['EXPERIMENT', 'TESTCASE', 'TOP_DIR'], 
                    value_vars=selected_metrics, 
                    var_name='METRIC', 
                    value_name='Value')

# Pivot table
pivot_df = melted_df.pivot_table(index=['EXPERIMENT', 'TESTCASE'], columns=['METRIC', 'TOP_DIR'], values='Value')

# Reset index for Ag-Grid
pivot_df = pivot_df.reset_index()

# Rename columns for clarity
pivot_df = pivot_df.rename(columns={'level_0': 'Experiment', 'level_1': 'Test Case'})

# Flatten column MultiIndex
pivot_df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in pivot_df.columns.values]

# Display pivot table with Ag-Grid
gb = GridOptionsBuilder.from_dataframe(pivot_df)
gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=True)
gb.configure_selection('single', use_checkbox=True)
gb.configure_pagination()
#gb.configure_column('Experiment', pinned='left')
#gb.configure_column('Test Case', pinned='left')
gridOptions = gb.build()
AgGrid(pivot_df, gridOptions=gridOptions)

# Create line plot
melted_df['Exp_Test'] = melted_df['EXPERIMENT'] + '_' + melted_df['TESTCASE']

fig = px.line(melted_df, 
              x='Exp_Test', 
              y='Value', 
              color='TOP_DIR', 
              line_dash='METRIC', 
              title='Metrics Across Test Cases and Experiments',
              color_discrete_sequence=px.colors.qualitative.D3)

# Display plot
st.plotly_chart(fig, use_container_width=True)
