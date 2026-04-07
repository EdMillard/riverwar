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
from typing import List, Optional
import time
import requests

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


def merge_header_units(df: pd.DataFrame, replacements: Optional[List[tuple]] = None) -> pd.DataFrame:
    """
    - If row 1 contains units → standard case (January style)
    - If row 1 has NO units but row 2 does → 3-row case (February style)
    """
    if replacements is None:
        replacements = []

    if len(df) < 2:
        return df

    df = df.copy()
    h0 = df.iloc[0].astype(str).str.strip()   # Top row
    h1 = df.iloc[1].astype(str).str.strip()   # Middle row

    # Check if this is 3-header-row case (Feb)
    is_three_row = len(df) > 2 and any('(' in str(x) for x in df.iloc[2]) and not any('(' in str(x) for x in h1)

    if is_three_row:
        # February style: merge row 0 + row 1, units are in row 2
        text_row = h1
        units_row_idx = 2
    else:
        # January style: merge row 0 + row 1 (which has units)
        text_row = h1
        units_row_idx = 1

    new_h0 = []

    for col0, col_text in zip(h0, text_row):
        col0 = str(col0).strip()
        col_text = str(col_text).strip()

        if col_text and col_text.lower() not in ['nan', '']:
            merged = f"{col0} {col_text}".strip() if col0 and col0.lower() not in ['nan', ''] else col_text
        else:
            merged = col0

        # Apply your replacements
        for old, new in replacements:
            merged = merged.replace(old, new)

        # Basic camelCase fix
        merged = re.sub('([a-z0-9])([A-Z])', r'\1 \2', merged)
        merged = " ".join(merged.split())

        new_h0.append(merged)

    df.iloc[0] = new_h0

    # Drop the middle text row if it was 3-row case
    if is_three_row:
        df = pd.concat([df.iloc[[0]], df.iloc[2:]], ignore_index=True)

    return df

def preprocess_usbr_camelot_table(df: pd.DataFrame,
                                  replacements: Optional[List[tuple]] = None) -> Tuple[pd.DataFrame, str]:
    if df.empty or len(df) < 4:
        return pd.DataFrame(), "Rejected"

    df = df.copy()

    # Detect table type
    table_type = None
    if len(df) > 1:
        cell = str(df.iloc[1, 0]).strip().upper()
        if cell == "DATE" or cell.startswith("DATE"):
            table_type = "shifted"

    if table_type is None and len(df) > 3:
        cell = str(df.iloc[3, 0]).strip().upper()
        if cell == "DATE" or cell.startswith("DATE"):
            table_type = "good"

    if table_type is None:
        return pd.DataFrame(), "Rejected"

    # Reservoir name
    reservoir_name = "Unknown"
    if table_type == "good" and len(df) > 1:
        row1 = df.iloc[1].astype(str).str.strip()
        for cell in row1:
            cell_str = str(cell).strip()
            if cell_str and cell_str not in ["", "nan", "None", "Date"] and "Inflow" not in cell_str:
                reservoir_name = cell_str
                break

    # Keep two header rows
    if table_type == "good":
        cleaned_df = df.iloc[2:].reset_index(drop=True)
    else:
        cleaned_df = df.reset_index(drop=True)

    # Simple merge with your replacements
    final_df = merge_header_units(cleaned_df, replacements)

    return final_df, reservoir_name

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

def check_row_col_exists(df, row_idx=0, col_idx=1):
    if df is None or not isinstance(df, pd.DataFrame):
        print("Error: Input is not a DataFrame")
        return False

    # Check if DataFrame is empty
    if df.empty:
        print("DataFrame is empty")
        return False

    # Check if row 0 exists
    if row_idx >= len(df):
        print(f"Row {row_idx} does not exist (only {len(df)} rows)")
        return False

    # Check if column 1 exists (by integer position)
    if col_idx >= df.shape[1]:
        print(f"Column {col_idx} does not exist (only {df.shape[1]} columns)")
        return False

    # Optional: also check by column name if you know it
    # if col_name not in df.columns: ...

    return True


def usbr_24_month_to_csv(tables: List[Tuple[int, pd.DataFrame]], path: str | Path):
    path = Path(path)
    ensure_directory(path)
    # Tune: tables = camelot.read_pdf(..., table_areas=['x1,y1,x2,y2'], columns=[...])
    replacements = [
        ("Glento", "Glen to"),
        ("Endof", "End of"),
    ]
    table_num = 0
    previous_name = ''
    for page_num, df in tables:
        table_num += 1
        df_clean, name = preprocess_usbr_camelot_table(df, replacements=replacements)
        if name == 'Rejected':
            continue
        elif check_row_col_exists(df_clean, 0, 1):
            if name == 'Unknown':
                if previous_name == 'FlamingGorgeReservoir':
                    name = 'TaylorParkReservoir'
            previous_name = name
            if 'Reservoir' in name or 'Lake' in name or 'Power' in name or 'Flood' in name:
                if 'Mead' in name:
                    print("=== RAW FIRST 5 ROWS ===")
                    print(','.join([str(x).strip() for x in df.iloc[0]]))
                    print(','.join([str(x).strip() for x in df.iloc[1]]))
                    print(','.join([str(x).strip() for x in df.iloc[2]]))
                    print(','.join([str(x).strip() for x in df.iloc[3]]))
                    print(','.join([str(x).strip() for x in df.iloc[4]]))
                    print("=== CLEAN FIRST 4 ROWS ===")
                    print(','.join([str(x).strip() for x in df_clean.iloc[0]]))
                    print(','.join([str(x).strip() for x in df_clean.iloc[1]]))
                    print(','.join([str(x).strip() for x in df_clean.iloc[2]]))
                    print(','.join([str(x).strip() for x in df_clean.iloc[3]]))
                    print("\n=== COLUMN COUNT ===")
                    print(len(df.columns))
                name = clean_reservoir_name(name)
                value = df_clean.iloc[0, 1]  # row 0, column 1 (0-based indexing)
                if "Power" in value:
                    name += '_Power'
                out_csv_path = path / f'{name}.csv'
            else:
                out_csv_path = path / f'page_{page_num:d}.csv'
            print(f'table to csv: {out_csv_path}')
            df_clean.to_csv(str(out_csv_path), index=False,
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


from pathlib import Path
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
import time


def download_usbr_24mo_reports(
        base_url: str = "https://www.usbr.gov/lc/region/g4000/24mo/",
        download_dir: Path | str = "../data/USBR_24Month_Reports",
        years: Optional[List[int]] = None,
        months: Optional[List[str]] = None,
        delay: float = 0.5
) -> None:
    """
    Download USBR Lower Colorado 24-Month Study reports.
    Uses full month name for Chart files (e.g., March-Chart.pdf).
    """

    if isinstance(download_dir, str):
        download_dir = Path(download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

    if years is None:
        current_year = 2026
        years = list(range(2010, current_year + 1))

    # Month mapping: 3-letter -> Full name
    month_map = {
        "JAN": "January", "FEB": "February", "MAR": "March", "APR": "April",
        "MAY": "May", "JUN": "June", "JUL": "July", "AUG": "August",
        "SEP": "September", "OCT": "October", "NOV": "November", "DEC": "December"
    }

    if months is None:
        months = list(month_map.keys())

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; USBR-Downloader)"})

    print(f"Starting download to: {download_dir}\n")

    for year in years:
        year_dir = download_dir / str(year)
        year_dir.mkdir(exist_ok=True)

        for month in months:
            base_name = f"{month}{str(year)[-2:]}"  # e.g., MAR26

            files_to_try = [
                f"{base_name}.pdf",  # Most Probable
                f"{base_name}_MIN.pdf",  # Minimum Probable
                f"{month_map[month]}-Chart.pdf"  # ← Full month name for Chart
            ]

            year_url = f"{base_url}{year}/"

            for filename in files_to_try:
                file_url = year_url + filename
                local_path = year_dir / filename

                if local_path.exists():
                    print(f"✓ Already exists: {year}/{filename}")
                    if not 'Chart' in filename:
                        out_path = Path(local_path.with_suffix(''))
                        # FIXME - RESTORE THIS
                        # if not out_path.exists():
                        tables = read_pdf_camelot(local_path)
                        usbr_24_month_to_csv(tables, out_path)
                    continue

                try:
                    print(f"Downloading: {year}/{filename} ... ", end="")
                    r = session.get(file_url, timeout=30)

                    if r.status_code == 200 and len(r.content) > 5000:
                        local_path.write_bytes(r.content)
                        print("✅ Done")
                    else:
                        print("Not found")
                except Exception as e:
                    print(f"Failed: {e}")

                time.sleep(delay)

    print("\n✅ Download process complete!")


if __name__ == "__main__":
    years = [2026]
    download_usbr_24mo_reports(years=years)
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