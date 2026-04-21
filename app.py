import streamlit as st
import pandas as pd
import os
from xlsxwriter.utility import xl_col_to_name

st.set_page_config(page_title="Data Validation Tool", layout="wide")

# ================= PREMIUM UI =================
st.markdown("""
<style>
body {
    background: linear-gradient(180deg, #f8fafc, #eef2ff);
}
.block-container {
    padding-top: 1.5rem !important;
}
[data-testid="stSidebar"] {
    width: 300px;
    background: linear-gradient(180deg, #e0e7ff, #f1f5f9);
}
section[data-testid="stSidebar"] .stButton button {
    width: 100%;
    text-align: left;
    background-color: transparent;
    border: none;
    padding: 10px 14px;
    border-radius: 10px;
    font-size: 14px;
    color: #334155;
    transition: all 0.25s ease;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background-color: #c7d2fe;
    color: #1e3a8a;
    padding-left: 18px;
    transform: scale(1.03);
}
section[data-testid="stSidebar"] .stButton button:focus {
    background-color: #818cf8;
    color: white;
    font-weight: 600;
}
button[kind="primary"] {
    background: linear-gradient(90deg, #22c55e, #16a34a) !important;
    color: white !important;
    border-radius: 10px !important;
    height: 44px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🚀 Data Validation & Comparison Tool")

# ================= SESSION =================
for key in ["mapping", "file1_fmt", "file2_fmt", "f1_sort", "f2_sort"]:
    if key not in st.session_state:
        st.session_state[key] = {}

# ================= SIDEBAR =================
st.sidebar.header("⚙️ Configuration")

file1 = st.sidebar.file_uploader("Upload File 1", type=["csv", "xlsx"])
file2 = st.sidebar.file_uploader("Upload File 2", type=["csv", "xlsx"])

if "section" not in st.session_state:
    st.session_state.section = "Preview"

st.sidebar.markdown("### 📂 Navigation")

if st.sidebar.button("📈 Preview"):
    st.session_state.section = "Preview"
if st.sidebar.button("🔗 Mapping"):
    st.session_state.section = "Mapping"
if st.sidebar.button("🛠️ Formatting"):
    st.session_state.section = "Formatting"
if st.sidebar.button("⚙️ Sorting"):
    st.session_state.section = "Sorting"

section = st.session_state.section

# ================= FUNCTIONS =================
def clean_name(name):
    return name.split('.')[0][:30]

def convert_column(series, fmt):
    result = []
    for val in series:
        val = str(val).strip()
        if val in ["", "nan", "None", "NaT"]:
            result.append("")
            continue
        if "T" in val:
            val = val.split("T")[0]

        dt = None
        for f in ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%m/%d/%y"]:
            try:
                dt = pd.to_datetime(val, format=f)
                break
            except:
                continue

        result.append(val if dt is None else dt.strftime(fmt))

    return pd.Series(result)

def normalize(df):
    df = df.copy()
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace(['nan', 'None', 'NaT'], '')
    return df

def apply_format(df, config):
    df = df.copy()
    for col in config:
        if col in df.columns:
            df[col] = convert_column(df[col], config[col])
    return df

def apply_sort(df, cols, order):
    if not cols:
        return df
    asc = [order[c] == "ASC" for c in cols]
    return df.sort_values(by=cols, ascending=asc).reset_index(drop=True)

# ================= MAIN =================
if file1 and file2:

    df1 = pd.read_csv(file1, dtype=str) if file1.name.endswith('csv') else pd.read_excel(file1)
    df2 = pd.read_csv(file2, dtype=str) if file2.name.endswith('csv') else pd.read_excel(file2)

    df1.columns = df1.columns.str.strip()
    df2.columns = df2.columns.str.strip()

    col1 = list(df1.columns)
    col2 = list(df2.columns)

    if section == "Preview":
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("File1")
            st.dataframe(df1.head())
        with c2:
            st.subheader("File2")
            st.dataframe(df2.head())

    if section == "Mapping":
        st.subheader("🔗 Column Mapping")
        colA, colB = st.columns([8, 2])
        with colB:
            if st.button("Reset"):
                for key in list(st.session_state.keys()):
                    if key.startswith("map_"):
                        del st.session_state[key]
                st.session_state.mapping = {}

        cols = st.columns(3)
        for i, col in enumerate(col1):
            with cols[i % 3]:
                selected = st.selectbox(col, [""] + col2, key=f"map_{col}")
                st.session_state.mapping[col] = selected

    if section == "Formatting":
        st.subheader("🛠️ Data Type Management")

        format_options = {
            "YYYY-MM-DD": "%Y-%m-%d",
            "DD-MM-YYYY": "%d-%m-%Y",
            "MM/DD/YYYY": "%m/%d/%Y"
        }

        tabs = st.tabs(["📅 Dates", "🔤 Text", "🔢 Numbers"])

        with tabs[0]:
            c1, c2 = st.columns(2)
            with c1:
                f1_cols = st.multiselect("Column Name", col1)
                for col in f1_cols:
                    st.session_state.file1_fmt[col] = format_options[
                        st.selectbox("Format", list(format_options.keys()), key=f"f1_{col}")
                    ]
            with c2:
                f2_cols = st.multiselect("Column Name", col2)
                for col in f2_cols:
                    st.session_state.file2_fmt[col] = format_options[
                        st.selectbox("Format", list(format_options.keys()), key=f"f2_{col}")
                    ]

    if section == "Sorting":
        st.subheader("⚙️ Sorting")

        c1, c2 = st.columns(2)
        with c1:
            f1_cols = st.multiselect("Column Name", col1)
            for col in f1_cols:
                st.session_state.f1_sort[col] = st.selectbox("Order", ["ASC", "DESC"], key=f"s1_{col}")
        with c2:
            f2_cols = st.multiselect("Column Name", col2)
            for col in f2_cols:
                st.session_state.f2_sort[col] = st.selectbox("Order", ["ASC", "DESC"], key=f"s2_{col}")

    col1_, col2_, col3_ = st.columns([3, 2, 3])
    with col2_:
        run = st.button("🚀 Run Comparison", type="primary")

    if run:

        progress = st.progress(0)
        status = st.empty()

        def update(p, msg):
            progress.progress(p)
            status.text(f"{p}% - {msg}")

        try:
            update(10, "Normalizing...")
            df1_n = normalize(df1)
            df2_n = normalize(df2)

            update(30, "Formatting...")
            df1_n = apply_format(df1_n, st.session_state.file1_fmt)
            df2_n = apply_format(df2_n, st.session_state.file2_fmt)

            update(50, "Sorting...")
            df1_n = apply_sort(df1_n, list(st.session_state.f1_sort.keys()), st.session_state.f1_sort)
            df2_n = apply_sort(df2_n, list(st.session_state.f2_sort.keys()), st.session_state.f2_sort)

            update(70, "Mapping...")
            mapping = {k: v for k, v in st.session_state.mapping.items() if v}

            if not mapping:
                st.error("Please map columns")
                st.stop()

            df1_n = df1_n[list(mapping.keys())]
            df2_n = df2_n[list(mapping.values())]
            df2_n.columns = df1_n.columns

            # FIX ALIGNMENT
            df1_n = df1_n.reset_index(drop=True)
            df2_n = df2_n.reset_index(drop=True)

            max_len = max(len(df1_n), len(df2_n))
            df1_n = df1_n.reindex(range(max_len), fill_value='')
            df2_n = df2_n.reindex(range(max_len), fill_value='')

            update(90, "Writing Excel...")

            output = "comparison_output.xlsx"

            sheet1 = clean_name(file1.name)
            sheet2 = clean_name(file2.name)

            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:

                df1_n.to_excel(writer, sheet_name=sheet1, index=False)
                df2_n.to_excel(writer, sheet_name=sheet2, index=False)

                validation = pd.DataFrame()

                for i, col in enumerate(df1_n.columns):
                    col_letter = xl_col_to_name(i)

                    validation[col] = [
                        f'=IF(TRIM({sheet1}!{col_letter}{r})=TRIM({sheet2}!{col_letter}{r}),"TRUE","FALSE")'
                        for r in range(2, max_len + 2)
                    ]

                validation.to_excel(writer, sheet_name="Validation", index=False)

                workbook = writer.book

                for name, df in [(sheet1, df1_n), (sheet2, df2_n), ("Validation", validation)]:
                    ws = writer.sheets[name]
                    rows, cols = df.shape

                    ws.add_table(0, 0, rows, cols - 1, {
                        'columns': [{'header': c} for c in df.columns]
                    })

            update(100, "Done")

            st.success("✅ Comparison Completed")

            with open(output, "rb") as f:
                st.download_button("📥 Download Result", f, file_name=output)

        except Exception as e:
            st.error(str(e))