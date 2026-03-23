import pandas as pd
import streamlit as st

from utils.data_loader import dataset_summary, init_session_state, inject_base_css, render_page_header


st.set_page_config(page_title="Executive Dashboard", page_icon="🏥", layout="wide")
init_session_state()
inject_base_css()

render_page_header(
    "Executive Dashboard",
    "Build fast management views from the prepared dataset to support hospital direction and operational review.",
)

prepared_df = st.session_state["prepared_df"]

if prepared_df is None:
    st.warning("No prepared dataset found. Start with `Data Preparation`.")
    st.stop()

summary = dataset_summary(prepared_df)
numeric_columns = summary["numeric_columns"]
categorical_columns = summary["categorical_columns"]
datetime_columns = summary["datetime_columns"]

top_metrics = st.columns(5)
top_metrics[0].metric("Rows", summary["rows"])
top_metrics[1].metric("Columns", summary["columns"])
top_metrics[2].metric("Missing values", summary["missing_values"])
top_metrics[3].metric("Numeric KPIs", len(numeric_columns))
top_metrics[4].metric("Identifiers", len(summary["identifier_columns"]))

if summary["identifier_columns"]:
    st.caption(f"Excluded identifier columns: `{', '.join(summary['identifier_columns'])}`")

filters_col, dashboard_col = st.columns([0.9, 1.4], gap="large")

with filters_col:
    st.subheader("Dashboard controls")
    selected_measure = st.selectbox("Measure", numeric_columns) if numeric_columns else None
    selected_dimension = st.selectbox("Dimension", categorical_columns) if categorical_columns else None
    selected_date = st.selectbox("Date column", ["None"] + datetime_columns)

    filtered_df = prepared_df.copy()

    if selected_dimension:
        dimension_values = filtered_df[selected_dimension].dropna().astype(str).unique().tolist()
        chosen_values = st.multiselect(
            "Filter values",
            sorted(dimension_values),
            default=sorted(dimension_values[: min(8, len(dimension_values))]),
        )
        if chosen_values:
            filtered_df = filtered_df[filtered_df[selected_dimension].astype(str).isin(chosen_values)]

with dashboard_col:
    st.subheader("Management view")

    if selected_measure:
        kpi_cols = st.columns(4)
        kpi_cols[0].metric("Total", f"{filtered_df[selected_measure].sum():,.2f}")
        kpi_cols[1].metric("Average", f"{filtered_df[selected_measure].mean():,.2f}")
        kpi_cols[2].metric("Median", f"{filtered_df[selected_measure].median():,.2f}")
        kpi_cols[3].metric("Max", f"{filtered_df[selected_measure].max():,.2f}")

    if selected_dimension and selected_measure:
        st.markdown("### Breakdown by dimension")
        grouped = (
            filtered_df.groupby(selected_dimension)[selected_measure]
            .agg(["sum", "mean", "count"])
            .sort_values("sum", ascending=False)
            .head(15)
        )
        st.bar_chart(grouped["sum"], use_container_width=True)
        st.dataframe(grouped.round(2), use_container_width=True)

    if selected_date != "None" and selected_measure:
        st.markdown("### Time trend")
        time_df = filtered_df.dropna(subset=[selected_date]).copy()
        if not time_df.empty:
            time_df["month"] = pd.to_datetime(time_df[selected_date]).dt.to_period("M").astype(str)
            monthly = time_df.groupby("month")[selected_measure].sum()
            st.line_chart(monthly, use_container_width=True)
        else:
            st.info("No valid dates are available after filtering.")

st.markdown("### Current prepared dataset")
st.dataframe(prepared_df.head(30), use_container_width=True)
