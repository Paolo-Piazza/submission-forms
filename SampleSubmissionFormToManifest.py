import streamlit as st
import pandas as pd

# Streamlit app
def main():
    st.title("Excel to CSV Converter")

    # File uploader
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])

    if uploaded_file:
        # Load the Excel file
        try:
            excel_data = pd.ExcelFile(uploaded_file)
            sheet_name = st.selectbox("Select a sheet", excel_data.sheet_names)
            df = excel_data.parse(sheet_name)

            # Extract filename from cell C5
            cell_c5 = df.iloc[3, 2]  # Row 5 (index 4), Column C (index 2)
            if pd.isna(cell_c5):
                st.error("Cell C5 is empty. ")
                print(cell_c5)
                cell_c5 = "no quote number found"
                print(cell_c5)
                #return

            filename = f"{cell_c5}_sample_manifest.csv"
            print(cell_c5)

            # Extract data from row 11 onwards
            start_row = 10  # Row 11 (0-based index)
            sample_names = df.iloc[start_row:, 0].dropna()  # Column A:A
            container_names = df.iloc[start_row: start_row + len(sample_names), 12]  # Column M:M
            well_locations = df.iloc[start_row: start_row + len(sample_names), 13]  # Column N:N

            # Combine into a DataFrame
            result_df = pd.DataFrame({
                "sample_well_location": well_locations.values,
                "Sample_name": sample_names.values,
                "Container_name": container_names.values
            })

            # Display the resulting DataFrame
            st.write("Preview of the resulting CSV:")
            st.dataframe(result_df)

            # Allow download of the resulting CSV
            csv_data = result_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
