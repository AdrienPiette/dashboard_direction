from __future__ import annotations

import io
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


SUPPORTED_ENCODINGS = ["cp1252", "latin-1", "utf-8-sig", "utf-8"]
TYPE_OPTIONS = ["string", "integer", "float", "date"]


@dataclass(frozen=True)
class FixedWidthField:
    name: str
    start: int
    end: int
    dtype: str = "string"
    date_format: str = "%d%m%Y"

    @property
    def width(self) -> int:
        return self.end - self.start + 1


def detect_encoding(payload: bytes, candidates: list[str] | None = None) -> str:
    for encoding in candidates or SUPPORTED_ENCODINGS:
        try:
            payload.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "latin-1"


def decode_text_payload(payload: bytes, encoding: str | None = None) -> tuple[str, str]:
    selected_encoding = encoding or detect_encoding(payload)
    text = payload.decode(selected_encoding, errors="replace")
    return text.replace("\r\n", "\n").replace("\r", "\n"), selected_encoding


def split_lines(text: str, *, skip_blank_lines: bool = True) -> list[str]:
    lines = text.split("\n")
    if skip_blank_lines:
        return [line for line in lines if line.strip()]
    return lines


def parse_schema_rows(schema_df: pd.DataFrame) -> list[FixedWidthField]:
    fields: list[FixedWidthField] = []
    required_columns = {"name", "start", "end", "dtype", "date_format"}
    missing = required_columns.difference(schema_df.columns)
    if missing:
        raise ValueError(f"Schema is missing columns: {', '.join(sorted(missing))}")

    clean_df = schema_df.dropna(how="all")
    if clean_df.empty:
        raise ValueError("At least one field definition is required.")

    for _, row in clean_df.iterrows():
        name = str(row["name"]).strip()
        if not name:
            raise ValueError("Each field needs a name.")

        start = int(row["start"])
        end = int(row["end"])
        if start <= 0 or end < start:
            raise ValueError(f"Invalid positions for field '{name}'.")

        dtype = str(row["dtype"]).strip().lower() or "string"
        if dtype not in TYPE_OPTIONS:
            raise ValueError(f"Unsupported dtype '{dtype}' for field '{name}'.")

        date_format = str(row["date_format"]).strip() or "%d%m%Y"
        fields.append(FixedWidthField(name=name, start=start, end=end, dtype=dtype, date_format=date_format))

    return fields


def _coerce_series(series: pd.Series, field: FixedWidthField) -> pd.Series:
    cleaned = series.replace("", pd.NA)

    if field.dtype == "integer":
        return pd.to_numeric(cleaned.str.replace(" ", "", regex=False), errors="coerce").astype("Int64")
    if field.dtype == "float":
        normalized = (
            cleaned.str.replace(" ", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        return pd.to_numeric(normalized, errors="coerce")
    if field.dtype == "date":
        return pd.to_datetime(cleaned, format=field.date_format, errors="coerce")
    return cleaned


def parse_fixed_width_lines(lines: list[str], fields: list[FixedWidthField]) -> pd.DataFrame:
    records: list[dict[str, object]] = []

    for line_number, line in enumerate(lines, start=1):
        record = {"source_line_number": line_number, "source_record": line}
        for field in fields:
            raw_value = line[field.start - 1 : field.end]
            record[field.name] = raw_value.strip()
        records.append(record)

    df = pd.DataFrame(records)
    for field in fields:
        df[field.name] = _coerce_series(df[field.name].astype("string"), field)
    return df


def parse_delimited_lines(
    lines: list[str],
    *,
    delimiter: str = ";",
    has_header: bool = True,
    column_names: list[str] | None = None,
) -> pd.DataFrame:
    text = "\n".join(lines)
    header = 0 if has_header else None
    df = pd.read_csv(io.StringIO(text), sep=delimiter, header=header, dtype="string")

    if not has_header:
        if column_names:
            if len(column_names) != len(df.columns):
                raise ValueError("The number of custom column names does not match the parsed file.")
            df.columns = column_names
        else:
            df.columns = [f"column_{index + 1}" for index in range(len(df.columns))]

    return df


def dataframe_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "RPM") -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31] or "RPM")
    buffer.seek(0)
    return buffer.getvalue()


def dataframe_to_sqlite_bytes(df: pd.DataFrame, table_name: str = "rpm_data") -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as handle:
        temp_path = Path(handle.name)

    try:
        with sqlite3.connect(temp_path) as connection:
            df.to_sql(table_name, connection, if_exists="replace", index=False)
        return temp_path.read_bytes()
    finally:
        temp_path.unlink(missing_ok=True)


def default_fixed_width_schema() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"name": "record_type", "start": 1, "end": 2, "dtype": "string", "date_format": "%d%m%Y"},
            {"name": "patient_id", "start": 3, "end": 12, "dtype": "string", "date_format": "%d%m%Y"},
            {"name": "stay_start", "start": 13, "end": 20, "dtype": "date", "date_format": "%d%m%Y"},
            {"name": "stay_end", "start": 21, "end": 28, "dtype": "date", "date_format": "%d%m%Y"},
            {"name": "amount", "start": 29, "end": 36, "dtype": "float", "date_format": "%d%m%Y"},
        ]
    )
