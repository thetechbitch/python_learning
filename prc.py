import streamlit as st
import polars as pl

st.set_page_config(layout="wide")
st.header("Step 1: Preprocess Your File (Text to Columns)")

# File uploader
uploaded_file = st.file_uploader("Upload a CSV file", type="csv")
if uploaded_file is not None:
    # Initialize session state variables only once
    if "original_df" not in st.session_state:
        df = pl.read_csv(uploaded_file)
        st.session_state["original_df"] = df.clone()  # Save the original DataFrame in session state
        st.session_state["processed_df"] = df.clone()  # Initialize processed DataFrame in session state
else:
    st.info("Please upload a CSV file to proceed.")
    st.stop()

# Use the processed DataFrame from session state
df = st.session_state["processed_df"]

# Select column to split
col_to_split = st.selectbox("Choose a column to split", df.columns)
split_mode = st.radio("Split mode", ["Delimiter", "Fixed Width"])
new_col_prefix = st.text_input("New column name prefix", "split")

undo_requested = st.button("Undo last split", key="undo_button")
drop_blank_cols = st.checkbox("Drop blank/empty columns")

# Set up session state for split history
if "split_history" not in st.session_state:
    st.session_state.split_history = []

# Undo functionality
if undo_requested and st.session_state.split_history:
    st.session_state["processed_df"] = st.session_state.split_history.pop()
    st.success("Undo successful.")
else:
    # Ensure the column is a string
    df = df.with_columns(df[col_to_split].cast(pl.Utf8))  # Ensure the column is a string

    split_result = None  # Placeholder for split result

    if split_mode == "Delimiter":
        delimiter = st.text_input("Enter delimiter (e.g. , ; | \\t)", value=",")
        if delimiter == "\\t":
            delimiter = "\t"
        try:
            # Split the column into multiple columns
            split_cols = df.select(col_to_split).to_series(0).str.split(delimiter)
            max_len = max(len(item) for item in split_cols)
            split_result = {
                f"{col_to_split}_{i}": [x[i] if i < len(x) else None for x in split_cols]
                for i in range(max_len)
            }
        except Exception as e:
            st.error(f"Error during delimiter split: {e}")

    elif split_mode == "Fixed Width":
        preview_lines = 5
        preview_text = "\n".join(df[col_to_split].to_series(0).head(preview_lines).to_list())
        st.code(preview_text, language="text")

        widths = st.text_input("Enter fixed widths (comma-separated)", value="5,5,5")
        try:
            widths = list(map(int, widths.strip().split(",")))
            new_cols = []
            start = 0
            for i, width in enumerate(widths):
                col = df.select(col_to_split).to_series(0).str.slice(start, width)
                new_cols.append((f"{col_to_split}_{i}", col))
                start += width
            split_result = {name: col for name, col in new_cols}
        except Exception as e:
            st.error(f"Error during fixed-width split: {e}")

    # If split_result is available, preview and rename columns
    if split_result:
        st.subheader("Preview Split Columns")
        new_col_names = []
        for i, col_name in enumerate(split_result.keys()):
            name = st.text_input(f"Rename column {i}", col_name)
            new_col_names.append(name)

        # Convert split_result to a Polars DataFrame
        split_df = pl.DataFrame(split_result)
        split_df.columns = new_col_names  # Rename columns

        st.dataframe(split_df.head(10))

        # Save modifications
        if st.button("Save Split Columns"):
            try:
                # Remove the original column and add the new split columns at the same index
                col_index = df.columns.index(col_to_split)  # Get the index of the column to split
                new_columns = {name: split_df[name] for name in new_col_names}

                # Create a new DataFrame with the columns in the correct order
                new_df = (
                    df[:, :col_index]  # Columns before the split column
                    .hstack(pl.DataFrame(new_columns))  # Add the new split columns
                    .hstack(df[:, col_index + 1:])  # Columns after the split column
                )

                # Update session state
                st.session_state.split_history.append(df)
                st.session_state["processed_df"] = new_df
                st.session_state["final_df"] = st.session_state["processed_df"].clone()  # Save the final DataFrame
                st.success("Split columns saved successfully.")
            except Exception as e:
                st.error(f"Error saving split columns: {e}")

# Drop blank/empty columns
if drop_blank_cols:
    df = st.session_state["processed_df"]
    df = df.drop_nulls().drop([col for col in df.columns if df.select(col).to_series(0).null_count() == len(df)])
    st.session_state["processed_df"] = df

# Preview processed DataFrame
st.write("### Preview Processed Data:")
st.dataframe(st.session_state["processed_df"].head(50).to_pandas())

# Add a button to switch to the dashboard page
if st.session_state["processed_df"] is not None:
    st.markdown("### Preprocessing complete!")
    st.info("Click on dashboard to visualize the data.")
