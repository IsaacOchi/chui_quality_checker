"""
utils/file_handler.py
Handles reading uploaded files (CSV, Excel, TSV) from Streamlit's UploadedFile object.
Returns a clean DataFrame + metadata dict.
"""

import io
import chardet
import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".tsv"}


def read_uploaded_file(uploaded_file) -> tuple[pd.DataFrame, dict]:
    """
    Accepts a Streamlit UploadedFile object or a file path string.
    Returns (DataFrame, metadata_dict).
    Raises ValueError with plain-English message if file is unreadable.
    """
    # Determine filename
    if hasattr(uploaded_file, "name"):
        filename = uploaded_file.name
    else:
        import os
        filename = os.path.basename(str(uploaded_file))

    ext = _get_extension(filename)

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"File type '{ext}' is not supported. "
            f"Please upload a CSV, TSV, XLS, or XLSX file."
        )

    try:
        if ext in {".xlsx", ".xls"}:
            return _read_excel(uploaded_file, filename)
        else:
            return _read_flat_file(uploaded_file, filename, ext)
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(
            f"Could not read '{filename}'. "
            f"Make sure the file is not password-protected or corrupted. "
            f"Technical detail: {str(e)}"
        )


def _get_extension(filename: str) -> str:
    import os
    return os.path.splitext(filename)[1].lower()


def _read_flat_file(uploaded_file, filename: str, ext: str) -> tuple[pd.DataFrame, dict]:
    """Read CSV or TSV file with automatic delimiter and encoding detection."""
    # Read raw bytes
    if hasattr(uploaded_file, "read"):
        raw_bytes = uploaded_file.read()
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
    else:
        with open(uploaded_file, "rb") as f:
            raw_bytes = f.read()

    # Detect encoding
    detected = chardet.detect(raw_bytes[:50000])
    encoding = detected.get("encoding") or "utf-8"
    if encoding.lower() in ("ascii", "windows-1252"):
        encoding = "utf-8"

    # Decode
    try:
        text = raw_bytes.decode(encoding, errors="replace")
    except Exception:
        text = raw_bytes.decode("utf-8", errors="replace")

    # Detect delimiter
    if ext == ".tsv":
        delimiter = "\t"
    else:
        delimiter = _sniff_delimiter(text)

    file_size_kb = round(len(raw_bytes) / 1024, 1)

    try:
        df = pd.read_csv(io.StringIO(text), sep=delimiter, low_memory=False)
    except Exception as e:
        raise ValueError(
            f"Could not parse '{filename}' as a delimited file. "
            f"Make sure it is a proper CSV or TSV. Detail: {e}"
        )

    if df.empty or len(df.columns) < 2:
        raise ValueError(
            f"'{filename}' appears to have only one column. "
            f"This usually means the wrong delimiter was detected. "
            f"Try saving your file as CSV (comma-separated) and re-uploading."
        )

    metadata = {
        "filename": filename,
        "rows": len(df),
        "columns": len(df.columns),
        "file_size_kb": file_size_kb,
        "delimiter_detected": repr(delimiter),
        "encoding": encoding,
    }

    return df, metadata


def _read_excel(uploaded_file, filename: str) -> tuple[pd.DataFrame, dict]:
    """Read Excel file (xlsx or xls)."""
    if hasattr(uploaded_file, "read"):
        raw_bytes = uploaded_file.read()
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        buf = io.BytesIO(raw_bytes)
    else:
        with open(uploaded_file, "rb") as f:
            raw_bytes = f.read()
        buf = io.BytesIO(raw_bytes)

    file_size_kb = round(len(raw_bytes) / 1024, 1)

    try:
        df = pd.read_excel(buf, engine="openpyxl")
    except Exception:
        buf.seek(0)
        df = pd.read_excel(buf)

    metadata = {
        "filename": filename,
        "rows": len(df),
        "columns": len(df.columns),
        "file_size_kb": file_size_kb,
        "delimiter_detected": "N/A (Excel)",
        "encoding": "N/A (Excel)",
    }

    return df, metadata


def _sniff_delimiter(text: str) -> str:
    """Detect delimiter from the first few lines of text."""
    import csv

    sample = "\n".join(text.splitlines()[:20])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t|;")
        return dialect.delimiter
    except csv.Error:
        # Fallback: count occurrences
        first_line = text.splitlines()[0] if text.splitlines() else ""
        counts = {
            ",": first_line.count(","),
            "\t": first_line.count("\t"),
            ";": first_line.count(";"),
            "|": first_line.count("|"),
        }
        return max(counts, key=counts.get)
