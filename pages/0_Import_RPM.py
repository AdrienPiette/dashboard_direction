from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from utils.data_loader import (
    build_profile,
    dataset_summary,
    init_session_state,
    inject_base_css,
    render_page_header,
)
from utils.rpm_parser import (
    SUPPORTED_ENCODINGS,
    TYPE_OPTIONS,
    dataframe_to_excel_bytes,
    dataframe_to_sqlite_bytes,
    decode_text_payload,
    default_fixed_width_schema,
    parse_delimited_lines,
    parse_fixed_width_lines,
    parse_schema_rows,
    split_lines,
)


st.set_page_config(page_title="RPM Import", page_icon="🏥", layout="wide")
init_session_state()
inject_base_css()

render_page_header(
    "RPM Import",
    "Parse Belgian RPM text exports into a structured DataFrame and publish them to CSV, Excel or SQLite.",
)

st.info(
    "Use this page for ASCII/ANSI RPM `.txt` files. Once parsed, the result is stored in session and becomes available in the other pages."
)

uploaded_file = st.file_uploader("Upload an RPM text file", type=["txt", "dat", "asc"])

layout_col, options_col = st.columns([1.1, 1], gap="large")

with layout_col:
    parse_mode = st.radio(
        "Record format",
        ["Fixed-width positions", "Delimited text"],
        horizontal=True,
        help="Choose fixed-width if each field is defined by character positions in the official RPM layout.",
    )
    skip_blank_lines = st.checkbox("Ignore blank lines", value=True)

with options_col:
    encoding = st.selectbox("Encoding", ["Auto-detect"] + SUPPORTED_ENCODINGS, index=0)
    output_name = st.text_input("Dataset label", value="rpm_dataset")

if uploaded_file is None:
    st.stop()

payload = uploaded_file.getvalue()
decoded_text, detected_encoding = decode_text_payload(payload, None if encoding == "Auto-detect" else encoding)
lines = split_lines(decoded_text, skip_blank_lines=skip_blank_lines)

st.caption(
    f"Detected encoding: `{detected_encoding}`. Parsed candidate records: `{len(lines)}`. Source file: `{uploaded_file.name}`."
)

if not lines:
    st.error("No usable records were found in the uploaded file.")
    st.stop()

parsed_df: pd.DataFrame | None = None
parse_clicked = False

if parse_mode == "Fixed-width positions":
    st.markdown("### RPM field layout")
    st.caption(
        "Define one row per field using 1-based inclusive positions. Replace the example with the official Belgian RPM dictionary for your file type."
    )
    schema_df = st.data_editor(
        default_fixed_width_schema(),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "name": st.column_config.TextColumn("Field name", required=True),
            "start": st.column_config.NumberColumn("Start", min_value=1, step=1, required=True),
            "end": st.column_config.NumberColumn("End", min_value=1, step=1, required=True),
            "dtype": st.column_config.SelectboxColumn("Type", options=TYPE_OPTIONS, required=True),
            "date_format": st.column_config.TextColumn("Date format"),
        },
    )

    if st.button("Parse RPM file", type="primary", use_container_width=True):
        parse_clicked = True
        try:
            fields = parse_schema_rows(schema_df)
            parsed_df = parse_fixed_width_lines(lines, fields)
        except Exception as exc:
            st.error(f"Unable to parse the fixed-width file: {exc}")
            st.stop()
else:
    delimiter_col, header_col, names_col = st.columns([0.8, 0.8, 1.4], gap="large")
    with delimiter_col:
        delimiter_label = st.selectbox("Delimiter", ["Semicolon (;)", "Pipe (|)", "Tab", "Comma (,)"])
        delimiter_map = {
            "Semicolon (;)": ";",
            "Pipe (|)": "|",
            "Tab": "\t",
            "Comma (,)": ",",
        }
        delimiter = delimiter_map[delimiter_label]
    with header_col:
        has_header = st.checkbox("First line contains headers", value=False)
    with names_col:
        custom_names = st.text_input("Column names when there is no header", value="")

    if st.button("Parse RPM file", type="primary", use_container_width=True):
        parse_clicked = True
        try:
            column_names = [name.strip() for name in custom_names.split(",") if name.strip()] or None
            parsed_df = parse_delimited_lines(
                lines,
                delimiter=delimiter,
                has_header=has_header,
                column_names=column_names,
            )
        except Exception as exc:
            st.error(f"Unable to parse the delimited file: {exc}")
            st.stop()

if parse_clicked and parsed_df is not None:
    st.session_state["rpm_parsed_df"] = parsed_df.copy()
    st.session_state["rpm_source_name"] = uploaded_file.name

if parsed_df is None and st.session_state["rpm_source_name"] == uploaded_file.name:
    stored_df = st.session_state["rpm_parsed_df"]
    if stored_df is not None:
        parsed_df = stored_df.copy()

if parsed_df is None:
    preview_lines = pd.DataFrame({"raw_record_preview": lines[:20]})
    st.markdown("### Raw preview")
    st.dataframe(preview_lines, use_container_width=True)
    st.stop()

st.session_state["raw_df"] = parsed_df.copy()
st.session_state["prepared_df"] = parsed_df.copy()
st.session_state["data_source_name"] = uploaded_file.name
st.session_state["prep_report"] = {
    "initial_shape": parsed_df.shape,
    "final_shape": parsed_df.shape,
    "renamed_columns": False,
    "trimmed_text": False,
    "parsed_dates": [],
    "converted_numeric": [],
    "duplicates_removed": 0,
    "missing_strategy": "Leave as is",
    "normalization": "None",
    "normalized_columns": [],
}

summary = dataset_summary(parsed_df)

st.success("RPM file parsed successfully. The dataset is now available to the analysis, ML and dashboard pages.")

metric_cols = st.columns(5)
metric_cols[0].metric("Rows", summary["rows"])
metric_cols[1].metric("Columns", summary["columns"])
metric_cols[2].metric("Missing values", summary["missing_values"])
metric_cols[3].metric("Numeric fields", len(summary["numeric_columns"]))
metric_cols[4].metric("Date fields", len(summary["datetime_columns"]))

preview_tab, profile_tab, export_tab = st.tabs(["Parsed data", "Column profile", "Exports"])

with preview_tab:
    st.dataframe(parsed_df.head(100), use_container_width=True)

with profile_tab:
    st.dataframe(build_profile(parsed_df), use_container_width=True)

with export_tab:
    safe_name = Path(output_name).stem or "rpm_dataset"
    csv_payload = parsed_df.to_csv(index=False).encode("utf-8")
    excel_payload = dataframe_to_excel_bytes(parsed_df, sheet_name=safe_name)
    sqlite_payload = dataframe_to_sqlite_bytes(parsed_df, table_name=safe_name)

    download_cols = st.columns(3)
    download_cols[0].download_button(
        "Download CSV",
        data=csv_payload,
        file_name=f"{safe_name}.csv",
        mime="text/csv",
        use_container_width=True,
    )
    download_cols[1].download_button(
        "Download Excel",
        data=excel_payload,
        file_name=f"{safe_name}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    download_cols[2].download_button(
        "Download SQLite",
        data=sqlite_payload,
        file_name=f"{safe_name}.sqlite",
        mime="application/vnd.sqlite3",
        use_container_width=True,
    )

    st.caption(
        "For SQL Server, PostgreSQL or another database, this page gives you a normalized table first. The next step can be an ETL export once the target DB is fixed."
    )
