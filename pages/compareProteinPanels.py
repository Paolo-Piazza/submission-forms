import streamlit as st
import pandas as pd
import os
from io import BytesIO


def find_common_items(original_df, custom_df, key_column):
    return original_df[original_df[key_column].isin(custom_df[key_column])]


def convert_df_to_csv(df):
    output = BytesIO()
    df.to_csv(output, index=False)
    return output.getvalue()


st.title("CSV List Comparator")

DATA_DIR = "data/"  # Folder where preloaded files are stored
TEMPLATE_DIR = "template/"  # Folder where template files are stored
TEMPLATE_FILE = "template.csv"  # Template file name

preloaded_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

# Download button for the template file
if os.path.exists(os.path.join(TEMPLATE_DIR, TEMPLATE_FILE)):
    with open(os.path.join(TEMPLATE_DIR, TEMPLATE_FILE), "rb") as template:
        st.download_button(
            label="Download CSV Template",
            data=template,
            file_name=TEMPLATE_FILE,
            mime="text/csv"
        )

#DATA_DIR_Temp = os.path.join(os.path.dirname(__file__), "template")
#template_file = [f for f in os.listdir(DATA_DIR_Temp) if f.endswith("template.csv")]
#st.download_button("template.csv", template_file)
#DATA_DIR = "https://github.com/Paolo-Piazza/submission-forms/tree/main"  # Folder where preloaded files are stored
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
preloaded_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]


# Checkbox selection for multiple preloaded files
st.preloaded_files(df.sort_values(by="preloaded_files").preloaded_files.unique())
selected_preloaded_files = st.multiselect("Select preloaded files:", preloaded_files)
select_all = st.checkbox("Select all preloaded files")

if select_all:
    selected_preloaded_files = preloaded_files

# File uploaders
uploaded_files = st.file_uploader("Or Upload Original CSV Files", type=["csv"], accept_multiple_files=True)
custom_file = st.file_uploader("Upload Custom CSV File", type=["csv"], accept_multiple_files=False)

# Merge preloaded and uploaded files
all_files = uploaded_files if uploaded_files else []
for filename in selected_preloaded_files:
    all_files.append(open(os.path.join(DATA_DIR, filename), "rb"))

if all_files and custom_file:
    custom_df = pd.read_csv(custom_file)
    st.write("Custom List Preview:", custom_df.head())

    key_column = st.selectbox("Select the common column for comparison:", custom_df.columns)

    if st.button("Compare Lists"):
        results = {}
        for file in all_files:
            original_df = pd.read_csv(file)
            common_items = find_common_items(original_df, custom_df, key_column)
            results[file.name] = len(common_items)

        # Sort results by number of matches in descending order
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

        # Display summary of results

        st.write("### Summary of Matches")
        summary_text = "\n".join(
            [f"{os.path.basename(file_name)}: {match_count} matches found" for file_name, match_count in sorted_results])
        st.text(summary_text)


        for file_name, match_count in sorted_results:
            st.write(f"**{os.path.basename(file_name)}: {match_count} matches found**")

            original_df = pd.read_csv(
                os.path.join(DATA_DIR, file_name)) if file_name in preloaded_files else pd.read_csv(file_name)
            common_items = find_common_items(original_df, custom_df, key_column)
            csv_data = convert_df_to_csv(common_items)
            st.download_button(
                label=f"Download common items for {os.path.basename(file_name)}",
                data=csv_data,
                file_name=f"common_items_{file_name}",
                mime="text/csv",
            )
                #text_contents = str(all_results)
        st.download_button("download summary", summary_text)
