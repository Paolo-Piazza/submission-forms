import streamlit as st
import pandas as pd
from io import StringIO

def main():
    st.title("Sample Manifest Management")

    # Initialize session state
    if "file_selections" not in st.session_state:
        st.session_state.file_selections = {}  # Dictionary to hold selections for each file
    if "all_index_data" not in st.session_state:
        st.session_state.all_index_data = pd.DataFrame()

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
    source_files = st.file_uploader("Upload Source Files for Indexes", type=["csv"], accept_multiple_files=True, key="source_files")

    if source_files:
        for source_file in source_files:
            file_name = source_file.name
            index_data = pd.read_csv(source_file)
            st.write(f"Source File Data ({file_name}):")
            st.dataframe(index_data)

            # Initialize selection set for this file
            if file_name not in st.session_state.file_selections:
                st.session_state.file_selections[file_name] = set()

            # Get current selection for this file
            current_selections = st.session_state.file_selections[file_name]

            st.subheader(f"Select Indexes for {file_name}")
            rows = ["A", "B", "C", "D", "E", "F", "G", "H"]
            columns = list(range(1, 13))

            # Bulk selection buttons
            col1, col2, col3 = st.columns(3)
            if col1.button("Select All", key=f"select_all_{file_name}"):
                current_selections.update({f"{row}{col:02d}" for col in columns for row in rows})
            if col2.button("Clear All", key=f"clear_all_{file_name}"):
                current_selections.clear()

            # Option to select multiple columns
            selected_columns = col3.multiselect("Select Columns to Toggle", columns, key=f"multi_column_select_{file_name}")
            if st.button("Toggle Selected Columns", key=f"toggle_selected_columns_{file_name}"):
                for selected_column in selected_columns:
                    for row in rows:
                        index = f"{row}{selected_column:02d}"
                        if index in current_selections:
                            current_selections.remove(index)
                        else:
                            current_selections.add(index)

            # Display the grid with checkboxes
            grid_selections = []
            for row in rows:
                cols = st.columns(len(columns))
                for col_label, col in zip(columns, cols):
                    checkbox_label = f"{row}{col_label:02d}"
                    checked = checkbox_label in current_selections
                    if col.checkbox(checkbox_label, value=checked, key=f"grid_{file_name}_{checkbox_label}"):
                        current_selections.add(checkbox_label)
                    else:
                        current_selections.discard(checkbox_label)
                    if checkbox_label in current_selections:
                        grid_selections.append(checkbox_label)

            # Update session state for this file
            st.session_state.file_selections[file_name] = current_selections

            # Display selected indexes for this file
            ordered_indexes = sorted(current_selections, key=lambda x: (int(x[1:]), x[0]))  # Column-wise sorting
            st.write(f"Selected Indexes for {file_name} (Column-Wise Order):")
            st.write(", ".join(ordered_indexes))

            # Add selected data to combined index data
            for selected in ordered_indexes:
                row_data = index_data[index_data.iloc[:, 0] == selected]  # Match on the first column (index ID)
                if not row_data.empty:
                    st.session_state.all_index_data = pd.concat([st.session_state.all_index_data, row_data])

        # Display combined index data from all files
        st.write("Combined Index Data Across All Files:")
        st.dataframe(st.session_state.all_index_data)

        # Map selected indexes to manifest
        for i, sample in editable_manifest.iterrows():
            if i < len(st.session_state.all_index_data):
                for key, value in st.session_state.all_index_data.iloc[i].items():
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
