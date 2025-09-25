import os
from pathlib import Path
from io import StringIO
import pandas as pd
import streamlit as st

#-----------temp
import streamlit as st, hashlib, sys, os
from pathlib import Path

APP_FILE = Path(__file__)
APP_HASH = hashlib.md5(APP_FILE.read_bytes()).hexdigest()[:10]

st.caption(f"Build marker: {APP_FILE.name} @ {APP_HASH}")
st.caption(f"Streamlit version: {st.__version__}")
st.caption(f"Running from: {APP_FILE.resolve()}")
st.caption(f"Working dir: {Path.cwd()}")
st.caption(f"Python: {sys.version.split()[0]}")
#-----------end temp

# ---------- Helpers ----------
def find_common_items(original_df: pd.DataFrame, custom_df: pd.DataFrame, key_column: str) -> pd.DataFrame:
    """Return rows from original_df whose key_column appears in custom_df[key_column]."""
    # normalize to string to reduce false negatives due to type mismatch
    left = original_df.copy()
    right = custom_df.copy()
    left[key_column] = left[key_column].astype(str)
    right[key_column] = right[key_column].astype(str)
    return left[left[key_column].isin(right[key_column])]

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Return a UTF-8 CSV as bytes for st.download_button."""
    return df.to_csv(index=False).encode("utf-8")

# ---------- Paths (safe even on Streamlit Cloud) ----------
APP_DIR = Path(__file__).parent if "__file__" in globals() else Path.cwd()
DATA_DIR = APP_DIR / "data"
TEMPLATE_DIR = APP_DIR / "template"
TEMPLATE_FILE = TEMPLATE_DIR / "template.csv"

# Ensure directories exist (won't error if they don't; we just handle gracefully)
preloaded_files = []
if DATA_DIR.exists():
    preloaded_files = sorted([p.name for p in DATA_DIR.glob("*.csv")])

# ---------- UI ----------
st.title("CSV List Comparator")

# Template download (if present)
if TEMPLATE_FILE.exists():
    st.download_button(
        label="Download CSV Template",
        data=TEMPLATE_FILE.read_bytes(),
        file_name=TEMPLATE_FILE.name,
        mime="text/csv",
    )

# Pick preloaded files
selected_preloaded_files = st.multiselect("Select preloaded files:", preloaded_files)
if st.checkbox("Select all preloaded files"):
    selected_preloaded_files = preloaded_files

# Uploads
uploaded_files = st.file_uploader("Or Upload Original CSV Files", type=["csv"], accept_multiple_files=True)
custom_file = st.file_uploader("Upload Custom CSV File", type=["csv"], accept_multiple_files=False)

# Build a normalized list of sources: [{"name": "file.csv", "df": DataFrame}]
sources = []

# Add preloaded files
for fname in selected_preloaded_files:
    path = DATA_DIR / fname
    try:
        df = pd.read_csv(path)
        sources.append({"name": fname, "df": df, "source": "preloaded"})
    except Exception as e:
        st.warning(f"Could not read preloaded file '{fname}': {e}")

# Add uploaded files
if uploaded_files:
    for uf in uploaded_files:
        try:
            # Important: read into DataFrame NOW and keep it, so we don't depend on re-reading buffers later.
            df = pd.read_csv(uf)
            sources.append({"name": uf.name, "df": df, "source": "uploaded"})
        except Exception as e:
            st.warning(f"Could not read uploaded file '{uf.name}': {e}")

if sources and custom_file:
    try:
        custom_df = pd.read_csv(custom_file)
    except Exception as e:
        st.error(f"Could not read custom CSV: {e}")
        st.stop()

    st.write("Custom List Preview")
    st.dataframe(custom_df.head(20), use_container_width=True)

    key_column = st.selectbox("Select the common column for comparison:", list(custom_df.columns))

    if st.button("Compare Lists"):
        results = []
        skipped = []

        for item in sources:
            name, original_df = item["name"], item["df"]
            if key_column not in original_df.columns:
                skipped.append(name)
                continue
            try:
                common = find_common_items(original_df, custom_df, key_column)
                results.append((name, len(common), common))
            except Exception as e:
                st.warning(f"Error comparing '{name}': {e}")

        # Sort by matches desc
        results.sort(key=lambda x: x[1], reverse=True)

        # Summary
        st.subheader("Summary of Matches")
        if results:
            summary_lines = [f"{name}: {count} matches found" for name, count, _ in results]
            summary_text = "\n".join(summary_lines)
            st.code(summary_text)
            st.download_button(
                "Download summary",
                data=summary_text.encode("utf-8"),
                file_name="comparison_summary.txt",
                mime="text/plain",
            )
        else:
            st.info("No matches found in the selected files.")

        if skipped:
            st.info(
                "Skipped files (missing selected key column): "
                + ", ".join(skipped)
            )

        # Per-file downloads
        for name, count, common_df in results:
            st.markdown(f"**{name}: {count} matches found**")
            st.dataframe(common_df.head(50), use_container_width=True)
            st.download_button(
                label=f"Download common items for {name}",
                data=df_to_csv_bytes(common_df),
                file_name=f"common_items_{name}",
                mime="text/csv",
            )
else:
    st.info("Select or upload at least one original CSV **and** upload a custom CSV to begin.")

