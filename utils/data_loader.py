from __future__ import annotations

import base64
import io
import re
import unicodedata
from pathlib import Path

import pandas as pd
import streamlit as st
from sklearn.preprocessing import MinMaxScaler, StandardScaler


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SESSION_DEFAULTS = {
    "raw_df": None,
    "prepared_df": None,
    "data_source_name": None,
    "prep_report": None,
    "rpm_parsed_df": None,
    "rpm_source_name": None,
}
LOGO_FILE = Path(__file__).resolve().parents[1] / "assets" / "Logo_ISoSL_256px.png"


def init_session_state() -> None:
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def inject_base_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            color: #16302b;
            background:
                radial-gradient(circle at top right, rgba(84, 130, 53, 0.14), transparent 26%),
                radial-gradient(circle at bottom left, rgba(0, 89, 79, 0.10), transparent 24%),
                linear-gradient(180deg, #edf3ee 0%, #e4ece5 100%);
        }
        .stApp [data-testid="stAppViewContainer"] {
            background: transparent;
        }
        .stApp [data-testid="stHeader"] {
            background: rgba(237, 243, 238, 0.85);
            backdrop-filter: blur(8px);
        }
        .stApp [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(243, 248, 244, 0.96) 100%);
            border-right: 1px solid rgba(0, 89, 79, 0.10);
        }
        .stApp [data-testid="stSidebar"] > div:first-child {
            background: transparent;
        }
        .stApp [data-testid="stSidebar"] * {
            color: #16302b;
        }
        .stApp [data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            background: transparent;
        }
        .stApp [data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
            border-radius: 12px;
            margin-bottom: 0.25rem;
        }
        .stApp [data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {
            background: rgba(0, 89, 79, 0.08);
        }
        .stApp [data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {
            background: rgba(0, 89, 79, 0.12);
            font-weight: 600;
        }
        .stApp .block-container {
            padding-top: 2.4rem;
            padding-bottom: 2rem;
        }
        .stApp h1,
        .stApp h2,
        .stApp h3,
        .stApp h4,
        .stApp h5,
        .stApp h6,
        .stApp p,
        .stApp li,
        .stApp label,
        .stApp div,
        .stApp span,
        .stApp .stMarkdown,
        .stApp .stCaption {
            color: #16302b;
        }
        .stApp a {
            color: #00594f;
        }
        .stApp [data-baseweb="select"] > div,
        .stApp [data-baseweb="input"] > div,
        .stApp .stTextInput input,
        .stApp .stNumberInput input,
        .stApp .stTextArea textarea {
            background: rgba(255, 255, 255, 0.92);
            color: #16302b;
        }
        .stApp .stRadio > div,
        .stApp .stMultiSelect,
        .stApp .stSelectbox,
        .stApp .stFileUploader,
        .stApp .stDownloadButton,
        .stApp .stButton,
        .stApp .stAlert,
        .stApp [data-testid="stDataFrame"],
        .stApp [data-testid="stTable"] {
            color: #16302b;
        }
        .stApp [data-testid="stMetricLabel"],
        .stApp [data-testid="stMetricValue"],
        .stApp [data-testid="stMetricDelta"] {
            color: #16302b;
        }
        .stApp [data-testid="stFileUploader"] section {
            background: rgba(255, 255, 255, 0.92);
            border: 2px dashed rgba(0, 89, 79, 0.24);
            border-radius: 18px;
        }
        .stApp [data-testid="stFileUploader"] section:hover {
            background: rgba(255, 255, 255, 0.98);
            border-color: rgba(0, 89, 79, 0.42);
        }
        .stApp [data-testid="stFileUploader"] section * {
            color: #16302b;
        }
        .stApp [data-testid="stFileUploaderDropzone"] {
            background: transparent;
        }
        .stApp [data-testid="stFileUploader"] button {
            background: rgba(0, 89, 79, 0.08);
            color: #16302b;
            border: 1px solid rgba(0, 89, 79, 0.16);
        }
        .dd-logo-wrap {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(0, 89, 79, 0.10);
            border-radius: 22px;
            padding: 0.9rem 1.2rem;
            margin-bottom: 0.6rem;
            box-shadow: 0 14px 30px rgba(22, 48, 43, 0.08);
        }
        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(0, 89, 79, 0.10);
            padding: 0.9rem;
            border-radius: 1rem;
            backdrop-filter: blur(10px);
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }
        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.65);
            border-radius: 999px;
            padding-inline: 1rem;
        }
        .stApp code {
            color: #0e5f53;
            background: rgba(255, 255, 255, 0.8);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, caption: str) -> None:
    logo_base64 = base64.b64encode(LOGO_FILE.read_bytes()).decode("ascii")
    st.markdown(
        f"""
        <div class="dd-logo-wrap">
            <img src="data:image/png;base64,{logo_base64}" alt="Hospital logo" style="width:150px; height:auto; display:block;" />
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title(title)
    st.caption(caption)


def get_sample_files() -> list[Path]:
    if not DATA_DIR.exists():
        return []
    return sorted(path for path in DATA_DIR.iterdir() if path.suffix.lower() in {".csv", ".xlsx", ".xls"})


def _read_from_name_and_bytes(file_name: str, payload: bytes) -> pd.DataFrame:
    suffix = Path(file_name).suffix.lower()
    buffer = io.BytesIO(payload)
    if suffix == ".csv":
        return pd.read_csv(buffer)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(buffer)
    raise ValueError(f"Unsupported file format: {suffix}")


def load_uploaded_file(uploaded_file) -> pd.DataFrame:
    return _read_from_name_and_bytes(uploaded_file.name, uploaded_file.getvalue())


def load_sample_file(sample_path: Path) -> pd.DataFrame:
    return _read_from_name_and_bytes(sample_path.name, sample_path.read_bytes())


def _snake_case(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    return normalized.strip("_") or "column"


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    renamed = []
    used = {}

    for column in df.columns:
        base = _snake_case(column)
        count = used.get(base, 0)
        used[base] = count + 1
        renamed.append(base if count == 0 else f"{base}_{count + 1}")

    copy_df = df.copy()
    copy_df.columns = renamed
    return copy_df


def trim_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    copy_df = df.copy()
    object_columns = copy_df.select_dtypes(include=["object", "string"]).columns
    for column in object_columns:
        copy_df[column] = copy_df[column].apply(lambda value: value.strip() if isinstance(value, str) else value)
    return copy_df


def auto_parse_datetime_columns(df: pd.DataFrame, threshold: float = 0.75) -> tuple[pd.DataFrame, list[str]]:
    copy_df = df.copy()
    converted_columns = []

    for column in copy_df.select_dtypes(include=["object", "string"]).columns:
        series = copy_df[column].dropna()
        if series.empty:
            continue

        parsed = pd.to_datetime(copy_df[column], errors="coerce", dayfirst=True)
        success_ratio = parsed.notna().mean()

        if success_ratio >= threshold:
            copy_df[column] = parsed
            converted_columns.append(column)

    return copy_df, converted_columns


def coerce_numeric_columns(df: pd.DataFrame, min_success_ratio: float = 0.8) -> tuple[pd.DataFrame, list[str]]:
    copy_df = df.copy()
    converted_columns = []

    for column in copy_df.select_dtypes(include=["object", "string"]).columns:
        cleaned = copy_df[column].astype(str).str.replace(" ", "", regex=False).str.replace(",", ".", regex=False)
        parsed = pd.to_numeric(cleaned, errors="coerce")

        original_non_null = copy_df[column].notna().sum()
        if original_non_null == 0:
            continue

        success_ratio = parsed.notna().sum() / original_non_null
        if success_ratio >= min_success_ratio:
            copy_df[column] = parsed
            converted_columns.append(column)

    return copy_df, converted_columns


def handle_missing_values(df: pd.DataFrame, strategy: str) -> pd.DataFrame:
    if strategy == "Leave as is":
        return df.copy()

    copy_df = df.copy()
    numeric_columns = copy_df.select_dtypes(include=["number"]).columns
    categorical_columns = copy_df.select_dtypes(include=["object", "string", "category", "bool"]).columns

    if strategy == "Median":
        copy_df[numeric_columns] = copy_df[numeric_columns].fillna(copy_df[numeric_columns].median())
    elif strategy == "Mean":
        copy_df[numeric_columns] = copy_df[numeric_columns].fillna(copy_df[numeric_columns].mean())
    elif strategy == "Zero":
        copy_df[numeric_columns] = copy_df[numeric_columns].fillna(0)

    if strategy != "Leave as is":
        for column in categorical_columns:
            mode = copy_df[column].mode(dropna=True)
            filler = mode.iloc[0] if not mode.empty else "missing"
            copy_df[column] = copy_df[column].fillna(filler)

    return copy_df


def normalize_numeric_features(df: pd.DataFrame, method: str) -> tuple[pd.DataFrame, list[str]]:
    copy_df = df.copy()
    numeric_columns = list(copy_df.select_dtypes(include=["number"]).columns)

    if method == "None" or not numeric_columns:
        return copy_df, numeric_columns

    scaler = StandardScaler() if method == "Z-score" else MinMaxScaler()
    copy_df[numeric_columns] = scaler.fit_transform(copy_df[numeric_columns])
    return copy_df, numeric_columns


def prepare_dataset(
    df: pd.DataFrame,
    *,
    clean_columns: bool,
    trim_text: bool,
    parse_dates: bool,
    convert_numeric: bool,
    drop_duplicates: bool,
    missing_strategy: str,
    normalization: str,
) -> tuple[pd.DataFrame, dict]:
    prepared = df.copy()
    report = {
        "initial_shape": df.shape,
        "renamed_columns": clean_columns,
        "trimmed_text": trim_text,
        "parsed_dates": [],
        "converted_numeric": [],
        "duplicates_removed": 0,
        "missing_strategy": missing_strategy,
        "normalization": normalization,
        "normalized_columns": [],
    }

    if clean_columns:
        prepared = standardize_column_names(prepared)

    if trim_text:
        prepared = trim_string_columns(prepared)

    if parse_dates:
        prepared, parsed_dates = auto_parse_datetime_columns(prepared)
        report["parsed_dates"] = parsed_dates

    if convert_numeric:
        prepared, numeric_converted = coerce_numeric_columns(prepared)
        report["converted_numeric"] = numeric_converted

    if drop_duplicates:
        before = len(prepared)
        prepared = prepared.drop_duplicates()
        report["duplicates_removed"] = before - len(prepared)

    prepared = handle_missing_values(prepared, missing_strategy)
    prepared, normalized_columns = normalize_numeric_features(prepared, normalization)
    report["normalized_columns"] = normalized_columns if normalization != "None" else []
    report["final_shape"] = prepared.shape

    return prepared, report


def build_profile(df: pd.DataFrame) -> pd.DataFrame:
    total_rows = max(len(df), 1)
    return pd.DataFrame(
        {
            "column": df.columns,
            "dtype": df.dtypes.astype(str).values,
            "missing_values": df.isna().sum().values,
            "missing_pct": (df.isna().sum().values / total_rows * 100).round(2),
            "unique_values": df.nunique(dropna=True).values,
        }
    )


def dataset_summary(df: pd.DataFrame) -> dict:
    numeric_columns = list(df.select_dtypes(include=["number"]).columns)
    datetime_columns = list(df.select_dtypes(include=["datetime", "datetimetz"]).columns)
    categorical_columns = [
        column
        for column in df.columns
        if column not in numeric_columns and column not in datetime_columns
    ]
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "missing_values": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "numeric_columns": numeric_columns,
        "datetime_columns": datetime_columns,
        "categorical_columns": categorical_columns,
    }
