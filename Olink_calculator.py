import streamlit as st
import pandas as pd
from datetime import datetime

# Set page configuration for full width
st.set_page_config(layout="wide")

# Improved Custom CSS for intermediate width
def set_custom_css():
    st.markdown(
        """
        <style>
        .main .block-container {
            max-width: 60px !important;
            margin: auto !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

import time
time.sleep(1)  # Delay slightly for CSS override
set_custom_css()

#Logo
st.image("olink_cost_files/MTP_logo_RGB.png", caption="")

# Load category mapping
categories_csv_path = "olink_cost_files/categories.csv"
categories_df = pd.read_csv(categories_csv_path)

# Streamlit UI
st.title("Pricing Calculator")

st.subheader("Select Category")
category_options = categories_df["Category Name"].tolist()
selected_category = st.radio("Choose a panel category:", category_options, horizontal=True)

selected_file = categories_df[categories_df["Category Name"] == selected_category]["Prices File"].values[0]
prices_df = pd.read_csv(selected_file)
rules_csv_path = "olink_cost_files/pricing_rules.csv"
rules_df = pd.read_csv(rules_csv_path)

prepared_by = st.text_input("Prepared by (Your Name)")
prepared_for = st.text_input("Prepared for (Name/Email)")
notes = st.text_area("Additional Notes")

account_types = ["Internal", "External Academic", "External Commercial"]
selected_account = st.radio("Select Account Type:", account_types)

combinable_panels = prices_df[prices_df["Panel type"] == "Combinable"]["Panel Name"].tolist()
standalone_panels = prices_df[prices_df["Panel type"] == "Standalone"]["Panel Name"].tolist()

st.subheader("Select Products")
selected_combinable_panels = []
cols = st.columns(4)
for i, panel in enumerate(combinable_panels):
    with cols[i % 4]:
        if st.checkbox(panel):
            selected_combinable_panels.append(panel)
#if len(selected_combinable_panels) == len(combinable_panels):
#    selected_combinable_panels = ["Explore 3K"]

selected_standalone_panel = st.radio("Select one:", standalone_panels, index=None, key="standalone")
selected_panels = selected_combinable_panels + ([selected_standalone_panel] if selected_standalone_panel else [])

num_samples = st.number_input("Enter the number of samples:", min_value=1, step=1)


# Function to get panel details
def get_panel_details(panel):
    row = prices_df[prices_df["Panel Name"].str.strip() == panel.strip()]
    if not row.empty:
        return int(row.iloc[0]["Batch Size"]), row.iloc[0]["Product Name"].strip(), row.iloc[0][
            "Sequencing Kit"].strip(), float(row.iloc[0]["Sequencing Qty per Batch"])
    return None, None, None, None


# Function to fetch product price with volume discount
def get_product_price(product, count):
    row = rules_df[rules_df["Product Name"].str.strip() == product.strip()]
    if not row.empty:
        price_column = f"{selected_account} Price"
        base_price = float(row.iloc[0][price_column])

        # Check for volume discount
        if "Sample Number for Discount" in row and "Discount Percentage" in row:
            discount_threshold = row.iloc[0]["Sample Number for Discount"]
            discount_percentage = row.iloc[0]["Discount Percentage"]

            if count >= discount_threshold:
                base_price *= (1 - discount_percentage / 100)

        return count * base_price, base_price
    return 0, 0


valid_batches = [get_panel_details(panel)[0] for panel in selected_panels if get_panel_details(panel)[0]]
if valid_batches:
    closest_smaller = max([b * (num_samples // b) for b in valid_batches])
    closest_larger = min([b * (num_samples // b + 1) for b in valid_batches])
    num_samples = st.radio("Choose a valid sample count:", [closest_smaller, closest_larger])

st.subheader("Panel Breakdown")
panel_breakdown = {}
product_counts = {}
sequencing_counts = {}
total_cost = 0.0
if num_samples > 0 and selected_panels:
    for panel in selected_panels:
        batch_size, product_name, sequencing_kit, sequencing_qty = get_panel_details(panel)
        if batch_size and product_name:
            num_batches = num_samples // batch_size
            panel_breakdown[panel] = panel_breakdown.get(panel, 0) + num_batches
            sequencing_counts[sequencing_kit] = round(
                sequencing_counts.get(sequencing_kit, 0) + (num_batches * sequencing_qty))
            product_counts[product_name] = product_counts.get(product_name, 0) + num_batches

# Display Panel Breakdown
for panel, count in panel_breakdown.items():
    st.write(f"Panel: {panel}, Quantity: {count}")

# Adjust sequencing kits based on bundle changes

for product, seq_kit in sequencing_adjustments.items():
    if product in sequencing_counts:
        sequencing_counts[seq_kit] = sequencing_counts.pop(product)

# Display sequencing kit breakdown
st.subheader("Sequencing Kits")
for seq_kit, count in sequencing_counts.items():
    cost, unit_price = get_product_price(seq_kit, count)
    total_cost += cost
    st.write(f"{seq_kit}: {count} x {unit_price:.2f} = {cost:.2f}")


st.subheader("Products and Associated Costs")


def apply_bundle_rules(product, count):
    product_breakdown = {}
    sequencing_adjustment = {}

    row = rules_df[rules_df["Product Name"].str.strip() == product.strip()]
    
    if not row.empty and pd.notna(row.iloc[0]["Bundle Size"]):
        bundle_size = int(row.iloc[0]["Bundle Size"])
        bundle_product = row.iloc[0]["Bundle Product Name"]
        sequencing_adjusted = row.iloc[0].get("Sequencing Adjustment", None)

        if count >= bundle_size:
            bundle_count = count // bundle_size
            remainder = count % bundle_size
            product_breakdown[bundle_product] = bundle_count
            count = remainder

            # Apply sequencing adjustment if available
            if sequencing_adjusted and sequencing_adjusted.strip() != "NA":
                sequencing_adjustment[bundle_product] = sequencing_adjusted.strip()

    if count > 0:
        product_breakdown[product] = count

    return product_breakdown, sequencing_adjustment



# Apply bundle rules with sequencing adjustment
sequencing_adjustments = {}

for product, count in product_counts.items():
    updated_products, seq_adjust = apply_bundle_rules(product, count)
    
    for new_product, new_count in updated_products.items():
        cost, unit_price = get_product_price(new_product, new_count)
        total_cost += cost
        st.write(f"{new_product}: {new_count} x {unit_price:.2f} = {cost:.2f}")

        # Store sequencing adjustments
        if new_product in seq_adjust:
            sequencing_adjustments[new_product] = seq_adjust[new_product]


st.subheader("Total Experiment Cost")
st.write(f"Total Cost ({selected_account}): {total_cost:.2f}")
if selected_account in ["External Academic", "External Commercial"]:
    vat = total_cost * 0.2
    st.write(f"VAT (20%): {vat:.2f}")
    st.write(f"Total Cost Including VAT: {total_cost + vat:.2f}")

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
