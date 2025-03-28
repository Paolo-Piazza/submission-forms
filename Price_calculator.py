
import pandas as pd
import math
import streamlit as st
import time
import json
from datetime import datetime

# Session timeout duration (in seconds)
SESSION_TIMEOUT = 600
# Set page configuration for full width
st.set_page_config(layout="wide")

# Custom CSS for intermediate width


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


time.sleep(1)  # Delay slightly for CSS override
set_custom_css()

# Function to load users from a JSON file


def load_users():
    with open("TOM/users.json", "r") as file:
        return json.load(file)

# Function to validate email and password


def validate_login(email, password):
    users = load_users()
    for user in users:
        if user["email"] == email and user["password"] == password:
            return user  # Return the entire user dictionary
    return None

# Function to log user activity


def log_user_activity(email):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("user_log.csv", "a") as f:
        f.write(f"{timestamp}, {email}\n")

# Function to check for session timeout


def check_session_timeout():
    if "last_active" in st.session_state:
        if time.time() - st.session_state.last_active > SESSION_TIMEOUT:
            st.session_state.authenticated = False
            st.warning("Session expired due to inactivity. Please log in again.")

# Initialize session state for authentication


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if st.session_state.authenticated:
    check_session_timeout()

# If user is not authenticated, show login form


if not st.session_state.authenticated:
    st.title("Login with Email and Password")
    email = st.text_input("Enter your email")
    password = st.text_input("Enter your password", type="password")

    user = validate_login(email, password)
    if user is not None:
        st.session_state.authenticated = True
        st.session_state.user_email = email
        st.session_state.user_name = user.get("user_name", email)  # Use the user's name if available
        st.session_state.last_active = time.time()
        log_user_activity(email)
        st.success("Login successful!")
        st.rerun()
    else:
        st.error("Invalid email or password. Please try again.")

    st.stop()  # Stop further execution until the user logs in

# User is now authenticated; use their email for the "Prepared by" field
prepared_by = st.session_state.user_name
st.write(f"Welcome back: **{prepared_by}**")



#Logo


st.image("olink_cost_files/MTP_logo_RGB.png", caption="")

# Load category mapping


categories_csv_path = "olink_cost_files/categories.csv"  # Ensure this file exists with category-to-file mapping
categories_df = pd.read_csv(categories_csv_path)

# Streamlit UI


st.title("Price Calculator")

# Select category to determine which pricing file to load


st.subheader("Select Category")
category_options = categories_df["Category Name"].tolist()
selected_category = st.radio("Choose a panel category:", category_options, horizontal=True)

# Get corresponding pricing file


selected_file = categories_df[categories_df["Category Name"] == selected_category]["Prices File"].values[0]

# Load the selected pricing data
prices_df = pd.read_csv(selected_file)
rules_csv_path = "olink_cost_files/pricing_rules.csv"
rules_df = pd.read_csv(rules_csv_path)

# User information input
#prepared_by = st.text_input("Prepared by (Your Name)")
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
            return batch_size, product_name
        except (ValueError, TypeError):
            return None, None
    return None, None

# Function to fetch product price
def get_product_price(product, count):
    row = rules_df[rules_df["Product Name"].str.strip() == product.strip()]
    if not row.empty:
        price_column = f"{selected_account} Price"
        base_price = float(row.iloc[0][price_column])

        # Check for volume discount
        if "Batch Number for Discount" in row and "Discount Percentage" in row:
            discount_threshold = row.iloc[0]["Sample Number for Discount"]
            discount_percentage = row.iloc[0]["Discount Percentage"]

            if count >= discount_threshold:
                base_price *= (1 - discount_percentage / 100)

        return count * base_price, base_price
    return 0, 0

# Get sequencing kit information
def get_sequencing_kit_info(product):
    row = rules_df[rules_df["Product Name"].str.strip() == product.strip()]
    if not row.empty:
        sequencing_kit = row.iloc[0].get("Sequencing Kit", "").strip()
        sequencing_qty = float(row.iloc[0].get("Sequencing Qty per Batch", 0))
        return sequencing_kit, sequencing_qty
    return None, 0

# Determine closest valid sample numbers
valid_batches = []
for panel in selected_panels:
    batch_size, product_name = get_panel_details(panel)
    if batch_size:
        valid_batches.append(batch_size)
if valid_batches:
    closest_smaller = max([b * (num_samples // b) for b in valid_batches])
    closest_larger = min([b * (num_samples // b + 1) for b in valid_batches])
    num_samples = st.radio("Choose a valid sample count:", [closest_smaller, closest_larger])


def apply_bundle_rules(product, sample_count, batch_size):
    row = rules_df[rules_df["Product Name"].str.strip() == product.strip()]

    if not row.empty:
        bundle_size = row.iloc[0].get("Bundle Size")
        bundle_product = row.iloc[0].get("Bundle Product Name")

        if pd.notna(bundle_size) and pd.notna(bundle_product):
            bundle_size = int(bundle_size)
            batch_count = sample_count // batch_size  # Number of full batches
            full_bundles = batch_count // bundle_size  # Number of complete bundled products
            remainder_batches = batch_count % bundle_size  # Remaining unbundled batches

            result = {}
            if full_bundles > 0:
                result[bundle_product] = full_bundles
            if remainder_batches > 0:
                result[product] = remainder_batches  # Remainder stays as original product

            return result

    # If no bundling is needed, return the original product count
    return {product: sample_count // batch_size}


# Process selection and calculate costs

panel_breakdown = {}
product_counts = {}
sequencing_counts = {}
total_cost = 0.0
export_data = [["Prepared by", prepared_by], ["Prepared for", prepared_for], ["Account Type", selected_account], ["Number of Samples", num_samples], ["Notes", notes]]

if num_samples > 0 and selected_panels:
    for panel in selected_panels:
        batch_size, product_name = get_panel_details(panel)
        if batch_size and product_name:
            product_batches = num_samples // batch_size  # Calculate full batch count
            bundled_products = apply_bundle_rules(product_name, num_samples, batch_size)

            for bundled_product, bundled_count in bundled_products.items():
                product_counts[bundled_product] = product_counts.get(bundled_product, 0) + bundled_count

                # Ensure sequencing kits are assigned correctly based on the final product
                sequencing_kit, sequencing_qty = get_sequencing_kit_info(bundled_product)
                if sequencing_kit:
                    sequencing_counts[sequencing_kit] = sequencing_counts.get(sequencing_kit, 0) + (
                                bundled_count * sequencing_qty)

# Round sequencing kit quantities
#for seq_kit in sequencing_counts:
 #   sequencing_counts[seq_kit] = math.ceil(sequencing_counts[seq_kit])

#for seq_kit, count in sequencing_counts.items():
#    cost, unit_price = get_product_price(seq_kit, count)
#    total_cost += cost
#    st.write(f"Sequencing Kit: {seq_kit}, Quantity: {count}, Cost: {cost:.2f}")

#for seq_kit in sequencing_counts:


# Display panel breakdown
st.subheader("Panel Breakdown")
panel_breakdown = {}
if num_samples > 0 and selected_panels:
    for panel in selected_panels:
        batch_size, _ = get_panel_details(panel)
        if batch_size:
            panel_count = num_samples // batch_size
            panel_breakdown[panel] = panel_breakdown.get(panel, 0) + panel_count



for panel, count in panel_breakdown.items():
    st.write(f"Panel: {panel}, Quantity: {count}")


# Apply bundle rules and calculate total cost
st.subheader("Products and Associated Costs")
for product, count in product_counts.items():
    cost, unit_price = get_product_price(product, count)
    total_cost += cost
    st.write(f"{product}: {count} x {unit_price:.2f} = {cost:.2f}")

if not product_counts:
    st.write("No products found.")


# Display sequencing kit breakdown
st.subheader("Sequencing Kits")

for seq_kit in sequencing_counts:
    sequencing_counts[seq_kit] = math.ceil(sequencing_counts[seq_kit])


for seq_kit, count in sequencing_counts.items():
    cost, unit_price = get_product_price(seq_kit, count)
    total_cost += cost
    st.write(f"Sequencing Kit: {seq_kit}, Quantity: {count}, Cost: {cost:.2f}")





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
header = ["Date", "Prepared by", "Prepared for", "Account Type", "Category", "Number of Samples", "Notes", "Panels", "Products", "Sequencing Kits", "Total Cost", "Cost per sample", "VAT", "Total Including VAT"]

# Prepare data rows
panels_str = ", ".join([f"{count} {panel}" for panel, count in panel_breakdown.items()])
products_str = ", ".join([f"{count} {product}" for product, count in product_counts.items()])
sequencing_str = ", ".join([f"{count} {seq_kit}" for seq_kit, count in sequencing_counts.items()])
vat = total_cost * 0.2 if selected_account in ["External Academic", "External Commercial"] else 0
if num_samples == 0:
    cost_per_sample = "not applicable"

else: cost_per_sample = str(round(total_cost/num_samples, 2))

data_row = [date_today, prepared_by, prepared_for, selected_account, selected_category, num_samples, notes, panels_str, products_str, sequencing_str, total_cost, cost_per_sample, vat, total_cost + vat]
csv_data.append(data_row)

df_export = pd.DataFrame(csv_data, columns=header)
st.download_button("Download CSV", df_export.to_csv(index=False), prepared_by + prepared_for + date_today +".csv", "text/csv")

# After processing products (e.g. if product_counts exists)
if product_counts:

    def merge_csv_files(uploaded_files):
        all_data = []
        for file in uploaded_files:
            try:
                df = pd.read_csv(file)
                st.write(f"Successfully read {file.name}:", df.head())  # Debug output
                all_data.append(df)
            except Exception as e:
                st.error(f"Error reading {file.name}: {e}")
        if all_data:
            merged_df = pd.concat(all_data, ignore_index=True)
            return merged_df
        return None

    st.title("Olink Pricing Summary Merger")

    st.write("Upload multiple pricing summary files to merge them into a single report.")

    uploaded_files = st.file_uploader("Upload CSV files", type=["csv"], accept_multiple_files=True)

    # Debugging: show what files were uploaded
    if uploaded_files:
        st.write("Uploaded files:", [file.name for file in uploaded_files])

    if uploaded_files:
        merged_df = merge_csv_files(uploaded_files)
        if merged_df is not None:
            st.subheader("Merged Data Preview")
            st.dataframe(merged_df)

            csv = merged_df.to_csv(index=False)
            st.download_button("Download Merged File", csv, "merged_pricing_summary.csv", "text/csv")
        else:
            st.warning("No valid data found in uploaded files.")
