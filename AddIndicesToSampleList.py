import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO

def main():
    st.title("Sample Manifest Management")

    # Step 1: Upload Sample Manifest
    st.header("Step 1: Upload Sample Manifest")
    uploaded_files = st.file_uploader("Upload Sample Manifest(s)", type=["csv"], accept_multiple_files=True)

    if uploaded_files:
        dataframes = [pd.read_csv(file) for file in uploaded_files]
        sample_manifest = pd.concat(dataframes, ignore_index=True)
        st.write("Sample Manifest:")
        editable_manifest = sample_manifest.copy()
        st.dataframe(editable_manifest)
    else:
        st.warning("Please upload one or more sample manifest files.")
        return

    # Step 2: Assign Batch ID
    st.header("Step 2: Assign Batch ID")
    batch = st.text_input("Enter Batch ID:")

    if batch:
        editable_manifest['batch'] = batch

    st.write("Updated Sample Manifest:")
    st.dataframe(editable_manifest)

    # Step 3: Assign Indexes (Multiple Source Files)
    st.header("Step 3: Assign Indexes")
    source_files = st.file_uploader("Upload Source Files for Indexes", type=["csv"], accept_multiple_files=True)

    # Initialize session state to persist selections across interactions
    if "selected_indexes" not in st.session_state:
        st.session_state["selected_indexes"] = set()

    all_index_data = pd.DataFrame()

    if source_files:
        for source_file in source_files:
            index_data = pd.read_csv(source_file)
            st.write(f"Source File Data ({source_file.name}):")
            st.dataframe(index_data)

            st.subheader(f"Select Indexes for {source_file.name}")
            rows = ["A", "B", "C", "D", "E", "F", "G", "H"]
            columns = list(range(1, 13))

            # Bulk selection buttons
            col1, col2, col3 = st.columns(3)
            if col1.button("Select All", key=f"select_all_{source_file.name}"):
                st.session_state["selected_indexes"].update({f"{row}{col:02d}" for col in columns for row in rows})
            if col2.button("Clear All", key=f"clear_all_{source_file.name}"):
                st.session_state["selected_indexes"].clear()

            # Option to select multiple columns
            selected_columns = col3.multiselect("Select Columns to Toggle", columns, key=f"multi_column_select_{source_file.name}")
            if st.button("Toggle Selected Columns", key=f"toggle_selected_columns_{source_file.name}"):
                for selected_column in selected_columns:
                    for row in rows:
                        index = f"{row}{selected_column:02d}"
                        if index in st.session_state["selected_indexes"]:
                            st.session_state["selected_indexes"].remove(index)
                        else:
                            st.session_state["selected_indexes"].add(index)

            # Display the grid with checkboxes
            grid_selections = []
            for row in rows:
                cols = st.columns(len(columns))
                for col_label, col in zip(columns, cols):
                    checkbox_label = f"{row}{col_label:02d}"
                    checked = checkbox_label in st.session_state["selected_indexes"]

                    # Use checkbox and update selection set in session_state
                    if col.checkbox(checkbox_label, value=checked, key=f"grid_{source_file.name}_{checkbox_label}"):
                        st.session_state["selected_indexes"].add(checkbox_label)
                    else:
                        st.session_state["selected_indexes"].discard(checkbox_label)

                    # Collect the current state of the grid selections
                    if checkbox_label in st.session_state["selected_indexes"]:
                        grid_selections.append(checkbox_label)

            # Ensure selected_indexes remains unique and sorted in column-wise order
            ordered_indexes = sorted(st.session_state["selected_indexes"], key=lambda x: (int(x[1:]), x[0]))
            st.write("Selected Indexes (Column-Wise Order):")
            st.write(", ".join(ordered_indexes))

            for selected in ordered_indexes:
                row_data = index_data[index_data.iloc[:, 0] == selected]  # Match on the first column (index ID)
                if not row_data.empty:
                    all_index_data = pd.concat([all_index_data, row_data])

        st.write("Selected Indexes Across All Files:", ordered_indexes)
        st.write("Combined Index Data:")
        st.dataframe(all_index_data)

        # Map selected indexes to manifest
        for i, sample in editable_manifest.iterrows():
            if i < len(all_index_data):
                for key, value in all_index_data.iloc[i].items():
                    editable_manifest.at[i, key] = value

        st.write("Manifest with Assigned Indexes:")
        st.dataframe(editable_manifest)
    else:
        st.warning("Please upload one or more source files to assign indexes.")

    # Step 4: Check for Duplicates
    st.header("Step 4: Check for Duplicates")

    def check_for_duplicates(df, subset):
        duplicates = df[df.duplicated(subset=subset, keep=False)]
        return duplicates

    if st.button("Check for Duplicates"):
        if 'batch' in editable_manifest.columns and 'i5' in editable_manifest.columns and 'i7' in editable_manifest.columns:
            duplicates = check_for_duplicates(editable_manifest, ['batch', 'i5', 'i7'])
            if not duplicates.empty:
                st.error("Duplicates found:")
                st.write(duplicates)
            else:
                st.success("No duplicates found!")
        else:
            st.error("Required columns ('batch', 'i5', 'i7') are missing in the manifest.")

    # Step 5: Save Final Manifest
    st.header("Step 5: Save Final Manifest")

    if st.button("Save Final Manifest"):
        buffer = StringIO()
        editable_manifest.to_csv(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            label="Download Final Manifest",
            data=buffer.getvalue(),
            file_name="final_manifest.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
