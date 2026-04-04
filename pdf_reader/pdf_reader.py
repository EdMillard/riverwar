import csv
from pathlib import Path
import os
import camelot
import camelot.utils as utils
import camelot.core
import matplotlib
import pdfplumber
import pandas as pd
import re
from typing import List, Tuple
import warnings

os.environ['QT_QPA_PLATFORM'] = 'offscreen'      # Most important for Qt errors
os.environ['MPLBACKEND'] = 'Agg'                 # Non-interactive matplotlib backend
matplotlib.use('Agg')
os.environ['QT_SILENT'] = '1'

def ensure_directory(path: str | Path) -> Path:
    """Create directory (and parents) if it doesn't exist"""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def read_pdf_camelot(report_path: Path, max_pages: int = 200) -> List[Tuple[int, pd.DataFrame]]:
    """
    Reads PDF one page at a time using camelot.
    Returns: List of tuples -> (page_number, dataframe)
    """
    results: List[Tuple[int, pd.DataFrame]] = []
    page = 1
    consecutive_empty_pages = 0

    # Suppress only the noisy camelot warning
    warnings.filterwarnings("ignore",
                            message="No tables found in table area",
                            category=UserWarning)

    while page <= max_pages:
        try:
            print(f"Processing page {page}... ", end="")

            tables = camelot.read_pdf(
                str(report_path),
                flavor='stream',
                pages=str(page),
                row_tol=8,
                column_tol=8,
                strip_text=' .\n',
                edge_tol=50
            )

            if len(tables) == 0:
                print("No tables found")
                consecutive_empty_pages += 1
            else:
                print(f"Found {len(tables)} table(s)")
                consecutive_empty_pages = 0

                for table in tables:
                    if table.df is not None and not table.df.empty:
                        df = table.df.copy()
                        results.append((page, df))  # ← Tuple: (page, dataframe)

        except Exception as e:
            print(f"Error: {type(e).__name__} - {e}")
            consecutive_empty_pages += 1

        # Stop gracefully at end of document
        if consecutive_empty_pages >= 5:
            print(f"\nStopping after {consecutive_empty_pages} consecutive empty pages.")
            break

        page += 1

    print(f"\nFinished! Extracted {len(results)} tables total.")
    return results


def read_pdf_plumber(pdf_path: str | Path, pages: str = "all") -> List[pd.DataFrame]:
    """
    Safer pdfplumber reader for USBR-style tables.
    """
    pdf_path = Path(pdf_path)
    dataframes = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            if pages != "all" and str(page_num) not in str(pages).replace(' ', '').split(','):
                continue

            # Correct parameters - do NOT use True/False for explicit_*
            table_settings = {
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
                "explicit_vertical_lines": None,  # ← Fixed
                "explicit_horizontal_lines": None,  # ← Fixed
                "snap_tolerance": 3,
                "join_tolerance": 3,
                "edge_min_length": 10,
            }

            extracted_tables = page.extract_tables(table_settings)

            for table in extracted_tables:
                if table and len(table) > 1:  # at least one header + data row
                    # Convert to DataFrame
                    df = pd.DataFrame(table[1:], columns=table[0])
                    dataframes.append(df)

    return dataframes

def preprocess_usbr_camelot_table(df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    """
    Preprocess USBR 24-Month Study table from Camelot.

    - Extracts reservoir name ONLY from row 3 (0-based index 2)
    - Removes the first 3 rows (indices 0, 1, 2)
    """
    if df.empty or len(df) < 3:
        return df, "Unknown"

    df = df.copy()

    # === Extract reservoir name from row 2 only (index 1) ===
    reservoir_name = "Unknown"

    if len(df) > 2:
        row1 = df.iloc[1].astype(str).str.strip()
        for cell in row1:
            cell_str = str(cell).strip()
            if cell_str and cell_str not in ["", "nan", "None"]:
                # Avoid generic titles like "Minimum Probable Inflow"
                if "Probable Inflow" not in cell_str and "Inflow" not in cell_str:
                    reservoir_name = cell_str
                    break

    # === Remove first 3 rows ===
    cleaned_df = df.iloc[2:].reset_index(drop=True)

    return cleaned_df, reservoir_name

def clean_reservoir_name(text: str) -> str:
    """
    Extract name after dash and remove 'Reservoir' if present.
    """
    if not text or text.strip() == "":
        return "Unknown"

    # Split on dash (handles both - and –)
    if '–' in text:
        name = text.split('–', 1)[-1].strip()
    elif '-' in text:
        name = text.split('-', 1)[-1].strip()
    else:
        name = text.strip()

    # Remove "Reservoir" (case insensitive)
    name = name.replace("Reservoir", "").replace("reservoir", "").strip()

    # Clean up extra spaces
    name = " ".join(name.split())

    name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)

    return name

def usbr_24_month_to_csv(tables: List[Tuple[int, pd.DataFrame]], path: str | Path):
    path = Path(path)
    ensure_directory(path)
    # Tune: tables = camelot.read_pdf(..., table_areas=['x1,y1,x2,y2'], columns=[...])
    num_tables = len(tables)
    table_num = 0
    for page_num, df in tables:
        table_num += 1
        df_clean, name = preprocess_usbr_camelot_table(df)
        if 'Reservoir' in name or 'Lake' in name:
            name = clean_reservoir_name(name)
            out_csv_path = out_path / f'{name}.csv'
        else:
            out_csv_path = out_path / f'page_{page_num:d}.csv'
        df_clean.to_csv(out_csv_path, index=False,
                  quoting=csv.QUOTE_NONE,  # ← most important for no quotes
                  escapechar='\\')

def tables_to_csv(tables: List[Tuple[int, pd.DataFrame]], path: str | Path):
    path = Path(path)
    ensure_directory(path)
    # Tune: tables = camelot.read_pdf(..., table_areas=['x1,y1,x2,y2'], columns=[...])
    num_pages = 0
    for page_num, df in tables:
        if page_num > num_pages:
            num_pages = page_num

    last_page = 0
    table_num = 0
    for page_num, df in tables:
        df, reservoir_name = preprocess_usbr_camelot_table(df)
        if num_pages >= 1000:
            out_csv_path = out_path / f'page_{page_num:04d}'
        elif num_pages >= 100:
            out_csv_path = out_path / f'page_{page_num:03d}'
        elif num_pages >= 10:
            out_csv_path = out_path / f'page_{page_num:02d}'
        else:
            out_csv_path = out_path / f'page_{page_num:d}'
        if page_num == last_page:
            table_num += 1
            out_csv_path = out_csv_path.parent / f"{out_csv_path.stem}_{table_num:d}.csv"
        else:
            table_num = 0
            out_csv_path = out_csv_path.with_suffix('.csv')
        last_page = page_num
        # df = df.fillna('')  # replace NaNs with empty string
        # df = df.replace(r'^\s*$', '', regex=True)
        try:
            for col in df.columns:
                # Only touch object/string columns (or ones that might contain commas)
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace(',', '', regex=False)

            df.to_csv(out_csv_path, index=False,
                      quoting=csv.QUOTE_MINIMAL,
                      escapechar='\\')
        except Exception as e:
            print(f'tables_to_csv error: {e}')

def safe_bbox_intersection_area(ba, bb):
    area_a = utils.bbox_area(ba)
    if area_a == 0:
        return 0.0
    return utils.bbox_intersection_area(ba, bb) / area_a

if __name__ == "__main__":
    # https://www.usbr.gov/lc/region/g4000/24mo/index.html
    # report_path = Path('/opt/dev/riverwar/data/USBR_24_Month/March_2026/24mo.pdf')
    # tables = read_pdf_camelot(report_path)
    # out_path = Path(f'../data/reports/24_Month/{report_path.parent.name}/{report_path.stem}')
    # usbr_24_month_to_csv(tables, out_path)

    # report_path = Path('/opt/dev/riverwar/data/USBR_24_Month/March_2026/24mo_MIN.pdf')
    # tables = read_pdf_camelot(report_path)
    # out_path = Path(f'../data/reports/24_Month/{report_path.parent.name}/{report_path.stem}')
    # usbr_24_month_to_csv(tables, out_path)

    report_path = Path('/opt/dev/riverwar/data/USBR_24_Month/April_2025/24Month_04.pdf')
    tables = read_pdf_camelot(report_path)
    out_path = Path(f'../data/reports/24_Month/{report_path.parent.name}/{report_path.stem}')
    usbr_24_month_to_csv(tables, out_path)

    # for year in range(2022, 2025):
    #     report_path = Path(f'/opt/dev/USBR_Reports/Lower_Basin_Annual_Reports/{year}.pdf')
    #     tables = read_pdf_camelot(report_path)
    #    out_path = Path(f'../data/reports/{report_path.parent.name}/{report_path.stem}')
    #    tables_to_csv(tables, out_path)