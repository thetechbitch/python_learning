import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Analysis", layout="wide")

@st.cache_data
def load_data(file_path):
    try:
        with st.spinner('Loading data...'):
            df = pd.read_csv(file_path)
            return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

def display_pivot_table(pivot_df):
    st.subheader("Pivot Table")
    st.write(pivot_df)
    csv = pivot_df.to_csv()
    st.download_button(
        "Download Results",
        csv,
        "pivot_results.csv",
        "text/csv",
        key='download-csv'
    )

def plot_pivot_table(pivot_df, agg_function, value_field):
    st.subheader("Visualization")
    viz_type = st.radio("Visualization Type", ["Bar Chart", "Heatmap"])
    
    if viz_type == "Bar Chart":
        fig = go.Figure()
        if isinstance(pivot_df.columns, pd.MultiIndex):
            for col in pivot_df.columns.levels[0]:
                for sub_col in pivot_df[col].columns:
                    fig.add_trace(go.Bar(
                        x=pivot_df.index,
                        y=pivot_df[col][sub_col].values,
                        name=f"{col} - {sub_col}"
                    ))
        else:
            fig.add_trace(go.Bar(
                x=pivot_df.index,
                y=pivot_df.values.flatten(),
                name=value_field
            ))
        fig.update_layout(
            xaxis_type='category',
            barmode='group',
            title=f"{agg_function.capitalize()} of {value_field}"
        )
    else:
        if isinstance(pivot_df.columns, pd.MultiIndex):
            x_labels = [f"{col} - {sub_col}" for col in pivot_df.columns.levels[0] for sub_col in pivot_df[col].columns]
        else:
            x_labels = pivot_df.columns.tolist()
        fig = go.Figure(
            data=go.Heatmap(
                z=pivot_df.values,
                x=x_labels,
                y=pivot_df.index,
                colorscale='RdYlBu_r'
            )
        )
        fig.update_layout(
            title=f"{agg_function.capitalize()} of {value_field}"
        )
    
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.title("Transaction Analysis Dashboard")
    
    # File uploader
    uploaded_file = st.file_uploader("Choose CSV file", type="csv")
    if uploaded_file is None:
        st.info("Please upload a CSV file")
        return

    # Load data
    df = load_data(uploaded_file)
    if df is None:
        return

    # Sidebar configuration
    st.sidebar.header("Pivot Table Configuration")
    
    # Select pivot index (rows)
    pivot_rows = st.sidebar.multiselect(
        "Select Rows",
        options=df.columns.tolist(),
        default=["priority"] if "priority" in df.columns else []
    )

    # Select pivot columns
    pivot_columns = st.sidebar.multiselect(
        "Select Columns",
        options=df.columns.tolist(),
        default=["transaction_type"] if "transaction_type" in df.columns else []
    )

    # Select aggregation function and value field
    agg_function = st.sidebar.selectbox(
        "Aggregation Function",
        options=["count", "min", "max", "mean"],
        index=0
    )
    
    value_field = st.sidebar.selectbox(
        "Value Field",
        options=df.columns.tolist(),
        index=df.columns.tolist().index("data_size") if "data_size" in df.columns else 0
    )

    # Add options for totals
    show_totals = st.sidebar.checkbox("Show Totals", value=False)

    # Filters
    st.sidebar.header("Filters")
    filtered_df = df.copy()
    for col in df.columns:
        if df[col].nunique() < 20:  # Only show filter for categorical fields
            selected_values = st.sidebar.multiselect(
                f"Filter {col}",
                options=sorted(df[col].unique()),
                default=sorted(df[col].unique())
            )
            filtered_df = filtered_df[filtered_df[col].isin(selected_values)]

    # Create pivot table
    if pivot_rows and pivot_columns:
        try:
            pivot_df = pd.pivot_table(
                filtered_df,
                index=pivot_rows,
                columns=pivot_columns,
                values=value_field,
                aggfunc=agg_function,
                fill_value=0,
                margins=show_totals
            )
            
            # Display results
            tab1, tab2 = st.tabs(["Pivot Table", "Visualization"])
            
            with tab1:
                display_pivot_table(pivot_df)
            
            with tab2:
                plot_pivot_table(pivot_df, agg_function, value_field)

        except Exception as e:
            st.error(f"Error creating pivot table: {e}")
            st.info("Try selecting different combinations of rows and columns")

if __name__ == "__main__":
    main()
