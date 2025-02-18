import streamlit as st
import pandas as pd
from datetime import datetime

# Load category mapping
categories_csv_path = "U:/categories.csv"  # Ensure this file exists with category-to-file mapping
categories_df = pd.read_csv(categories_csv_path)

# Streamlit UI
st.title("Olink Panel Pricing Calculator")

# Select category to determine which pricing file to load
st.subheader("Select Category")
category_options = categories_df["Category Name"].tolist()
selected_category = st.radio("Choose a panel category:", category_options)

# Get corresponding pricing file
selected_file = categories_df[categories_df["Category Name"] == selected_category]["Prices File"].values[0]

# Load the selected pricing data
prices_df = pd.read_csv(selected_file)
rules_csv_path = "U:/pricing_rules.csv"
rules_df = pd.read_csv(rules_csv_path)

# User information input
prepared_by = st.text_input("Prepared by (Your Name)")
prepared_for = st.text_input("Prepared for (Name/Email)")
notes = st.text_area("Additional Notes")

# Account type selection
account_types = ["Internal", "External Academic", "External Commercial"]
selected_account = st.radio("Select Account Type:", account_types)

# Extract panel names dynamically
combinable_panels = prices_df[prices_df["Panel type"] == "Combinable"]["Panel Name"].tolist()
standalone_panels = prices_df[prices_df["Panel type"] == "Standalone"]["Panel Name"].tolist()

# Panel selection UI
st.subheader("Select Panels")

# Grid-based selection for combinable panels
selected_combinable_panels = []
cols = st.columns(4)
for i, panel in enumerate(combinable_panels):
    with cols[i % 4]:  # Distribute checkboxes in a grid
        if st.checkbox(panel):
            selected_combinable_panels.append(panel)

# Automatically assign "Explore 3K" if all combinable panels are selected
if len(selected_combinable_panels) == len(combinable_panels):
    selected_combinable_panels = ["Explore 3K"]

# Radio buttons for standalone panels
selected_standalone_panel = st.radio("Select one:", standalone_panels, index=None, key="standalone")

# Combine selections
selected_panels = selected_combinable_panels + ([selected_standalone_panel] if selected_standalone_panel else [])

# User input for number of samples
num_samples = st.number_input("Enter the number of samples:", min_value=1, step=1)

# Function to get batch size and product details
def get_panel_details(panel):
    row = prices_df[prices_df["Panel Name"].str.strip() == panel.strip()]
    if not row.empty:
        try:
            batch_size = int(row.iloc[0]["Batch Size"])
            product_name = row.iloc[0]["Product Name"].strip()
            sequencing_kit = row.iloc[0]["Sequencing Kit"].strip()
            sequencing_qty = float(row.iloc[0]["Sequencing Qty per Batch"])
            return batch_size, product_name, sequencing_kit, sequencing_qty
        except (ValueError, TypeError):
            return None, None, None, None
    return None, None, None, None

# Function to fetch product price
def get_product_price(product, count):
    row = rules_df[rules_df["Product Name"].str.strip() == product.strip()]
    if not row.empty:
        price_column = f"{selected_account} Price"
        price_per_unit = float(row.iloc[0][price_column])
        return count * price_per_unit, price_per_unit
    return 0, 0

# Determine closest valid sample numbers
valid_batches = []
for panel in selected_panels:
    batch_size, _, _, _ = get_panel_details(panel)
    if batch_size:
        valid_batches.append(batch_size)
if valid_batches:
    closest_smaller = max([b * (num_samples // b) for b in valid_batches])
    closest_larger = min([b * (num_samples // b + 1) for b in valid_batches])
    num_samples = st.radio("Choose a valid sample count:", [closest_smaller, closest_larger])

# Process selection and calculate costs
st.subheader("Panel Breakdown")
panel_breakdown = {}
product_counts = {}
sequencing_counts = {}
total_cost = 0.0
export_data = [["Prepared by", prepared_by], ["Prepared for", prepared_for], ["Account Type", selected_account], ["Number of Samples", num_samples], ["Notes", notes]]
if num_samples > 0 and selected_panels:
    for panel in selected_panels:
        batch_size, product_name, sequencing_kit, sequencing_qty = get_panel_details(panel)
        if batch_size and product_name:
            num_batches = num_samples // batch_size
            panel_breakdown[panel] = panel_breakdown.get(panel, 0) + num_batches
            sequencing_counts[sequencing_kit] = sequencing_counts.get(sequencing_kit, 0) + (num_batches * sequencing_qty)
            product_counts[product_name] = product_counts.get(product_name, 0) + num_batches

# Round sequencing kit quantities
for seq_kit in sequencing_counts:
    sequencing_counts[seq_kit] = round(sequencing_counts[seq_kit])

# Display panel breakdown
for panel, count in panel_breakdown.items():
    st.write(f"Panel: {panel}, Quantity: {count}")
    export_data.append(["Panel", panel, count])

# Apply bundle rules and calculate total cost
st.subheader("Products and Associated Costs")
final_product_counts = {}
def apply_bundle_rules(product, count):
    product_breakdown = {}
    row = rules_df[rules_df["Product Name"].str.strip() == product.strip()]
    if not row.empty and pd.notna(row.iloc[0]["Bundle Size"]):
        bundle_size = int(row.iloc[0]["Bundle Size"])
        bundle_product = row.iloc[0]["Bundle Product Name"]
        if count >= bundle_size:
            bundle_count = count // bundle_size
            remainder = count % bundle_size
            product_breakdown[bundle_product] = bundle_count
            count = remainder
    if count > 0:
        product_breakdown[product] = count
    return product_breakdown

for product, count in product_counts.items():
    updated_products = apply_bundle_rules(product, count)
    for new_product, new_count in updated_products.items():
        cost, unit_price = get_product_price(new_product, new_count)
        total_cost += cost
        st.write(f"{new_product}: {new_count} x {unit_price:.2f} = {cost:.2f}")
        export_data.append([new_product, new_count, unit_price, cost])

# Display sequencing kit breakdown
st.subheader("Sequencing Kits")
for seq_kit, count in sequencing_counts.items():
    cost, unit_price = get_product_price(seq_kit, count)
    total_cost += cost
    st.write(f"{seq_kit}: {count} x {unit_price:.2f} = {cost:.2f}")
    export_data.append([seq_kit, count, unit_price, cost])

# Display total cost
st.subheader("Total Experiment Cost")
st.write(f"Total Cost for the Experiment ({selected_account}): {total_cost:.2f}")
if selected_account in ["External Academic", "External Commercial"]:
    vat = total_cost * 0.2
    st.write(f"VAT (20%): {vat:.2f}")
    st.write(f"Total Cost Including VAT: {total_cost + vat:.2f}")
    export_data.append(["VAT (20%)", vat])
    export_data.append(["Total Cost Including VAT", total_cost + vat])

# Format CSV data
csv_data = []
date_today = datetime.today().strftime('%Y-%m-%d')
header = ["Date", "Prepared by", "Prepared for", "Account Type", "Category", "Number of Samples", "Notes", "Panels", "Products", "Sequencing Kits", "Total Cost", "VAT", "Total Including VAT"]

# Prepare data rows
panels_str = ", ".join([f"{count} {panel}" for panel, count in panel_breakdown.items()])
products_str = ", ".join([f"{count} {product}" for product, count in product_counts.items()])
sequencing_str = ", ".join([f"{count} {seq_kit}" for seq_kit, count in sequencing_counts.items()])
vat = total_cost * 0.2 if selected_account in ["External Academic", "External Commercial"] else 0

data_row = [date_today, prepared_by, prepared_for, selected_account, selected_category, num_samples, notes, panels_str, products_str, sequencing_str, total_cost, vat, total_cost + vat]
csv_data.append(data_row)

df_export = pd.DataFrame(csv_data, columns=header)
st.download_button("Download CSV", df_export.to_csv(index=False), "pricing_summary.csv", "text/csv")
