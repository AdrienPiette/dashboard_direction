import streamlit as st

from utils.data_loader import get_sample_files, inject_base_css, init_session_state, render_page_header


st.set_page_config(
    page_title="Hospital Data Lab",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
inject_base_css()

render_page_header(
    "Hospital Data Lab",
    "Unified data ingestion, preparation, exploration and clustering for hospital activity datasets.",
)

hero_left, hero_right = st.columns([1.25, 1], gap="large")

with hero_left:
    st.markdown(
        """
        This Streamlit app is designed for hospital analysts who need one place to:

        - import Excel or CSV files from operational sources
        - standardize and normalize datasets before analysis
        - explore data quality, distributions and activity drivers
        - test machine learning workflows such as clustering
        - prepare management-ready indicators on a dedicated dashboard page
        """
    )

    st.info(
        "Start on the `Data Preparation` page to load a file, clean it and store the prepared dataset in session."
    )

with hero_right:
    st.markdown("### Workspace status")
    sample_files = get_sample_files()
    st.metric("Sample files available", len(sample_files))
    st.metric("Raw dataset loaded", "Yes" if st.session_state["raw_df"] is not None else "No")
    st.metric(
        "Prepared dataset ready",
        "Yes" if st.session_state["prepared_df"] is not None else "No",
    )

    if sample_files:
        st.markdown("### Bundled datasets")
        for path in sample_files:
            st.write(f"- `{path.name}`")

st.markdown("### Suggested workflow")
workflow_cols = st.columns(3, gap="large")

with workflow_cols[0]:
    st.markdown(
        """
        **1. Data Preparation**

        Upload a CSV or Excel file, clean columns, manage missing values, remove duplicates and apply normalization.
        """
    )

with workflow_cols[1]:
    st.markdown(
        """
        **2. ML Lab**

        Select numeric features and compare unsupervised clustering approaches such as K-Means, Agglomerative or DBSCAN.
        """
    )

with workflow_cols[2]:
    st.markdown(
        """
        **3. Executive Dashboard**

        Build quick KPIs and charts from the prepared dataset for department and direction reviews.
        """
    )
