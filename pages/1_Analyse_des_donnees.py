from pathlib import Path

import pandas as pd
import streamlit as st

from utils.data_loader import (
    build_profile,
    dataset_summary,
    get_sample_files,
    init_session_state,
    inject_base_css,
    load_sample_file,
    load_uploaded_file,
    prepare_dataset,
    render_page_header,
)


st.set_page_config(page_title="Data Preparation", page_icon="🏥", layout="wide")
init_session_state()
inject_base_css()

render_page_header(
    "Data Preparation",
    "Load hospital activity data, clean it, normalize it and keep the prepared dataset ready for exploration and ML.",
)

source_col, options_col = st.columns([1.1, 1], gap="large")

with source_col:
    st.subheader("1. Source selection")
    source_mode = st.radio("Choose a source", ["Upload file", "Use sample dataset"], horizontal=True)

    loaded_df = None
    source_name = None

    if source_mode == "Upload file":
        uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx", "xls"])
        if uploaded_file is not None:
            loaded_df = load_uploaded_file(uploaded_file)
            source_name = uploaded_file.name
    else:
        sample_files = get_sample_files()
        if sample_files:
            selected_sample = st.selectbox(
                "Choose a bundled dataset",
                sample_files,
                format_func=lambda path: Path(path).name,
            )
            loaded_df = load_sample_file(Path(selected_sample))
            source_name = Path(selected_sample).name
        else:
            st.warning("No sample dataset was found in the `data` folder.")

with options_col:
    st.subheader("2. Preparation rules")
    clean_columns = st.checkbox("Standardize column names", value=True)
    trim_text = st.checkbox("Trim text fields", value=True)
    parse_dates = st.checkbox("Auto-detect date columns", value=True)
    convert_numeric = st.checkbox("Convert numeric-like text columns", value=True)
    drop_duplicates = st.checkbox("Remove duplicate rows", value=True)
    missing_strategy = st.selectbox("Missing value strategy", ["Leave as is", "Median", "Mean", "Zero"])
    normalization = st.selectbox("Normalization", ["None", "Z-score", "Min-Max"])

if loaded_df is not None:
    st.session_state["raw_df"] = loaded_df.copy()
    st.session_state["data_source_name"] = source_name

raw_df = st.session_state["raw_df"]

if raw_df is None:
    st.info("Load a dataset to unlock profiling, transformation and downstream modeling.")
    st.stop()

prepared_df, prep_report = prepare_dataset(
    raw_df,
    clean_columns=clean_columns,
    trim_text=trim_text,
    parse_dates=parse_dates,
    convert_numeric=convert_numeric,
    drop_duplicates=drop_duplicates,
    missing_strategy=missing_strategy,
    normalization=normalization,
)

st.session_state["prepared_df"] = prepared_df
st.session_state["prep_report"] = prep_report

raw_summary = dataset_summary(raw_df)
prepared_summary = dataset_summary(prepared_df)

st.success(f"`{st.session_state['data_source_name']}` loaded successfully. Prepared dataset is now available in session.")

metric_cols = st.columns(5)
metric_cols[0].metric("Rows", prepared_summary["rows"], prepared_summary["rows"] - raw_summary["rows"])
metric_cols[1].metric("Columns", prepared_summary["columns"])
metric_cols[2].metric("Missing values", prepared_summary["missing_values"])
metric_cols[3].metric("Duplicate rows", prepared_summary["duplicate_rows"])
metric_cols[4].metric("Numeric features", len(prepared_summary["numeric_columns"]))

st.markdown("### Preparation log")
log_cols = st.columns(4)
log_cols[0].write(f"Renamed columns: `{prep_report['renamed_columns']}`")
log_cols[1].write(f"Trimmed text: `{prep_report['trimmed_text']}`")
log_cols[2].write(f"Missing strategy: `{prep_report['missing_strategy']}`")
log_cols[3].write(f"Normalization: `{prep_report['normalization']}`")

if prep_report["parsed_dates"]:
    st.write(f"Detected date columns: `{', '.join(prep_report['parsed_dates'])}`")
if prep_report["converted_numeric"]:
    st.write(f"Converted numeric-like columns: `{', '.join(prep_report['converted_numeric'])}`")
if prep_report["duplicates_removed"]:
    st.write(f"Duplicate rows removed: `{prep_report['duplicates_removed']}`")

preview_tab, profile_tab, analysis_tab, export_tab = st.tabs(
    ["Prepared preview", "Column profile", "Quick exploration", "Export-ready data"]
)

with preview_tab:
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("#### Raw data")
        st.dataframe(raw_df.head(20), use_container_width=True)
    with right:
        st.markdown("#### Prepared data")
        st.dataframe(prepared_df.head(20), use_container_width=True)

with profile_tab:
    st.dataframe(build_profile(prepared_df), use_container_width=True)

with analysis_tab:
    numeric_columns = prepared_summary["numeric_columns"]
    categorical_columns = prepared_summary["categorical_columns"]

    chart_left, chart_right = st.columns(2, gap="large")

    with chart_left:
        st.markdown("#### Numeric distribution")
        if numeric_columns:
            selected_numeric = st.selectbox("Numeric column", numeric_columns)
            st.bar_chart(prepared_df[selected_numeric].dropna(), use_container_width=True)
        else:
            st.info("No numeric column available after preparation.")

    with chart_right:
        st.markdown("#### Category frequency")
        if categorical_columns:
            selected_category = st.selectbox("Categorical column", categorical_columns)
            category_counts = prepared_df[selected_category].astype(str).value_counts().head(15)
            st.bar_chart(category_counts, use_container_width=True)
        else:
            st.info("No categorical column available after preparation.")

    if numeric_columns:
        st.markdown("#### Correlation matrix")
        st.dataframe(prepared_df[numeric_columns].corr().round(2), use_container_width=True)

with export_tab:
    csv_payload = prepared_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download prepared dataset as CSV",
        data=csv_payload,
        file_name=f"prepared_{Path(st.session_state['data_source_name']).stem}.csv",
        mime="text/csv",
    )
    st.dataframe(prepared_df.tail(20), use_container_width=True)
