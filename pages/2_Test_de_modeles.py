import pandas as pd
import streamlit as st
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

from utils.data_loader import init_session_state, inject_base_css, render_page_header


st.set_page_config(page_title="ML Lab", page_icon="🏥", layout="wide")
init_session_state()
inject_base_css()

render_page_header(
    "ML Lab",
    "Test unsupervised models on the prepared dataset and segment activity profiles without leaving the app.",
)

prepared_df = st.session_state["prepared_df"]

if prepared_df is None:
    st.warning("No prepared dataset found. Go to `Data Preparation` first.")
    st.stop()

numeric_columns = list(prepared_df.select_dtypes(include=["number"]).columns)

if len(numeric_columns) < 2:
    st.warning("At least two numeric columns are required to run clustering.")
    st.stop()

setup_col, results_col = st.columns([1, 1.4], gap="large")

with setup_col:
    st.subheader("Model setup")
    selected_features = st.multiselect(
        "Numeric features",
        options=numeric_columns,
        default=numeric_columns[: min(6, len(numeric_columns))],
    )
    algorithm = st.selectbox("Algorithm", ["K-Means", "Agglomerative", "DBSCAN"])

    n_clusters = None
    eps = None
    min_samples = None

    if algorithm in {"K-Means", "Agglomerative"}:
        n_clusters = st.slider("Number of clusters", min_value=2, max_value=10, value=3)
    else:
        eps = st.slider("DBSCAN eps", min_value=0.1, max_value=5.0, value=0.8, step=0.1)
        min_samples = st.slider("DBSCAN min samples", min_value=2, max_value=20, value=5)

    run_model = st.button("Run clustering", type="primary", use_container_width=True)

with results_col:
    st.subheader("Prepared dataset preview")
    st.dataframe(prepared_df.head(15), use_container_width=True)

if not run_model:
    st.stop()

if len(selected_features) < 2:
    st.error("Select at least two numeric features.")
    st.stop()

model_input = prepared_df[selected_features].dropna()

if len(model_input) < 3:
    st.error("Not enough complete rows remain after dropping missing values for the selected features.")
    st.stop()

if algorithm == "K-Means":
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = model.fit_predict(model_input)
elif algorithm == "Agglomerative":
    model = AgglomerativeClustering(n_clusters=n_clusters)
    labels = model.fit_predict(model_input)
else:
    model = DBSCAN(eps=eps, min_samples=min_samples)
    labels = model.fit_predict(model_input)

clustered_df = model_input.copy()
clustered_df["cluster"] = labels

valid_clusters = [label for label in pd.Series(labels).unique() if label != -1]
cluster_count = len(valid_clusters)

score = None
if cluster_count >= 2:
    mask = clustered_df["cluster"] != -1
    if mask.sum() >= 3 and clustered_df.loc[mask, "cluster"].nunique() >= 2:
        score = silhouette_score(clustered_df.loc[mask, selected_features], clustered_df.loc[mask, "cluster"])

pca = PCA(n_components=2)
projection = pca.fit_transform(model_input)
plot_df = pd.DataFrame(projection, columns=["component_1", "component_2"], index=model_input.index)
plot_df["cluster"] = labels.astype(str)

summary_cols = st.columns(4)
summary_cols[0].metric("Rows modeled", len(model_input))
summary_cols[1].metric("Features used", len(selected_features))
summary_cols[2].metric("Clusters found", cluster_count)
summary_cols[3].metric("Silhouette score", f"{score:.3f}" if score is not None else "N/A")

chart_col, table_col = st.columns([1.15, 1], gap="large")

with chart_col:
    st.markdown("### Cluster projection")
    st.scatter_chart(plot_df, x="component_1", y="component_2", color="cluster", use_container_width=True)

with table_col:
    st.markdown("### Cluster sizes")
    cluster_sizes = (
        clustered_df["cluster"]
        .value_counts(dropna=False)
        .rename_axis("cluster")
        .reset_index(name="rows")
        .sort_values("cluster")
    )
    st.dataframe(cluster_sizes, use_container_width=True)

st.markdown("### Feature averages by cluster")
cluster_profile = clustered_df.groupby("cluster")[selected_features].mean().round(3)
st.dataframe(cluster_profile, use_container_width=True)

st.markdown("### Modeled records")
st.dataframe(clustered_df.head(50), use_container_width=True)
