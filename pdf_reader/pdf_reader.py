import csv
from pathlib import Path
import os
import camelot
import camelot.utils as utils
import camelot.core
import matplotlib
import pandas as pd
import re
import warnings
from typing import Optional
import time
import requests
import math

os.environ['QT_QPA_PLATFORM'] = 'offscreen'      # Most important for Qt errors
os.environ['MPLBACKEND'] = 'Agg'                 # Non-interactive matplotlib backend
matplotlib.use('Agg')
os.environ['QT_SILENT'] = '1'

def ensure_directory(path: str | Path) -> Path:
    """Create directory (and parents) if it doesn't exist"""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


import pdfplumber
from pathlib import Path
from typing import List, Tuple


def get_reservoir_names_with_bounds(pdf_path: str | Path) -> List[Tuple[int, str, str | None]]:
    pdf_path = Path(pdf_path)
    results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            words = page.extract_words(keep_blank_chars=True, x_tolerance=3, y_tolerance=3)

            title_candidates = [
                word['text'].strip()
                for word in words
                if word['top'] < 280 and word['text'].strip()
            ]

            if len(title_candidates) < 4:
                continue

            reservoir = title_candidates[3]

            if not ('Lake' in reservoir or 'Reservoir' in reservoir):
                continue

            tables = page.find_tables(
                table_settings={
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "snap_tolerance": 5,
                    "intersection_x_tolerance": 10,
                }
            )

            if tables:
                # Sort by size and take the largest one
                table = max(tables, key=lambda t: (t.bbox[2] - t.bbox[0]) * (t.bbox[3] - t.bbox[1]))
                bbox = table.bbox
                area_str = f"{bbox[0] - 10:.2f},{bbox[1] - 20:.2f},{bbox[2] + 10:.2f},{bbox[3] + 30:.2f}"  # expand a bit
            else:
                # Fallback: Use a large area covering most of the page (minus top title)
                width = page.width
                height = page.height
                area_str = f"30,100,{width - 30},{height - 150}"  # <-- Adjust these numbers
            results.append((page_num, reservoir, area_str))

    return results


def get_reservoir_names(pdf_path: str | Path) -> List[Tuple[int, str]]:
    """
    Returns list of (page_number, reservoir_name) for pages that have a reservoir.
    """
    pdf_path = Path(pdf_path)
    results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            words = page.extract_words(
                keep_blank_chars=True,
                x_tolerance=3,
                y_tolerance=3
            )

            title_candidates = [
                word['text'].strip()
                for word in words
                if word['top'] < 280 and word['text'].strip()  # adjust 280 if needed
            ]

            if len(title_candidates) < 4:
                continue

            # report = title_candidates[2]
            reservoir = title_candidates[3]

            if 'Lake' in reservoir or 'Reservoir' in reservoir:
                print(f"Page {page_num:2d} → {reservoir}")
                results.append((page_num, reservoir))
            else:
                print(f"Page {page_num:2d} → Skipped (not reservoir)")

    print(f"\nFound {len(results)} reservoir pages.")
    return results


def read_pdf_camelot(report_path: Path, max_pages: int = 200, lattice=False) -> List[Tuple[int, pd.DataFrame]]:
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

            if lattice:
                tables = camelot.read_pdf(
                    str(report_path),
                    flavor='lattice',
                    pages=str(page),
                )
            else:
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


def extract_reservoir_tables(pdf_path: str | Path, output_dir: str = "extracted_tables"):
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            print(f"\n--- Page {page_num} ---")

            words = page.extract_words(keep_blank_chars=True, x_tolerance=2, y_tolerance=2)
            title_candidates = [w['text'].strip() for w in words if w['top'] < 280 and w['text'].strip()]

            if len(title_candidates) < 4:
                continue
            reservoir = title_candidates[3]
            if not ('Lake' in reservoir or 'Reservoir' in reservoir):
                continue

            print(f"Reservoir: {reservoir}")

            # === Much stronger table settings for horizontal-line-only PDFs ===
            table_settings = {
                "vertical_strategy": "text",  # Critical when no vertical lines
                "horizontal_strategy": "lines",
                "snap_tolerance": 3,
                "snap_x_tolerance": 5,
                "snap_y_tolerance": 3,
                "intersection_x_tolerance": 5,
                "intersection_y_tolerance": 5,
                "edge_min_length": 5,
                "min_words_vertical": 2,
                "min_words_horizontal": 1,
                "text_keep_blank_chars": True,
                "keep_blank_chars": True,
            }

            tables = page.find_tables(table_settings=table_settings)

            if not tables:
                print("  No table detected")
                continue

            # Take the largest table
            table = max(tables, key=lambda t: t.bbox[2] * t.bbox[3])
            extracted_table = table.extract()

            if not extracted_table or len(extracted_table) < 2:
                print("  Table found but empty")
                continue

            df = pd.DataFrame(extracted_table[1:], columns=extracted_table[0])

            # Heavy cleaning
            df.columns = [str(c).replace('\n', ' ').replace('  ', ' ').strip()
                          for c in df.columns]
            df = df.dropna(axis=1, how='all')
            df = df.map(lambda x: str(x).strip() if pd.notna(x) else x)

            df.insert(0, 'Reservoir_Name', reservoir)

            safe_name = reservoir.replace(" ", "_").replace("-", "_")
            out_path = output_dir / f"{safe_name}_page{page_num}.csv"
            df.to_csv(out_path, index=False, quoting=csv.QUOTE_NONE, escapechar='\\')

            print(f"  Saved → {len(df.columns)} columns, {len(df)} rows")

            # Optional: save debug image
            # page.to_image(resolution=150).save(f"debug_page{page_num}.png")

    print("\nExtraction finished.")

def read_reservoir_camelot(
    report_path: Path,
    out_path: Path,
    reservoir_page_names
) -> List[Tuple[int, str, pd.DataFrame]]:
    """
    Reads PDF one page at a time using camelot.
    Returns: List of tuples -> (page_number, reservoir_name, dataframe)
    """
    results: List[Tuple[int, str, pd.DataFrame]] = []
    ensure_directory(out_path)

    # Suppress noisy camelot warning
    warnings.filterwarnings("ignore",
                            message="No tables found in table area",
                            category=UserWarning)

    for page, name in reservoir_page_names:
        try:
            # print(f"Processing page {page} — {name}... ", end="")
            tables = camelot.read_pdf(
                str(report_path),
                flavor='lattice',
                pages=str(page),
                line_scale=40
            )

            '''
                if len(tables) == 0:
                    tables = camelot.read_pdf(str(report_path), flavor='stream', pages=str(page),
                                              table_areas=['35,665,535,25'])
                    camelot.plot(tables[0], kind='text').savefig(f'debug_page{page}.png')

                    tables = camelot.read_pdf(
                        str(report_path),
                        flavor='stream',
                        pages=str(page),
                        table_areas=['65,665,535,25'],
                        columns=['100'],
                        row_tol=8,
                        column_tol=8,
                        strip_text=' .\n',
                        edge_tol=50,
                        split_text = True
                    )
                    if len(tables):
                        bbox = tables[0]._bbox
                        area_str = f"{max(0, bbox[0] - 5):.2f},{max(0, bbox[1] - 10):.2f},{bbox[2] + 10:.2f},{bbox[3] + 15:.2f}"
                        print(f'area_str {area_str}')
                        df, reservoir_name = preprocess_usbr_camelot_table(tables[0].df)
                        pass
            '''
            if len(tables) == 0:
                continue

            print(f"Found {len(tables)} table(s)")

            for table in tables:
                if table.df is None or table.df.empty:
                    continue

                df = table.df.copy()

                # ====================== FIXES ======================

                # 1. Clean headers (remove newlines)
                if not df.empty:
                    df.columns = [
                        str(col).replace('\n', ' ').replace('\r', ' ')
                                 .replace('  ', ' ').strip()
                        for col in df.iloc[0]
                    ]
                    df = df.iloc[1:].reset_index(drop=True)   # drop original header row

                # 2. Prevent the unwanted "0,1,2,3..." row (MultiIndex fix)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = ['_'.join(str(i) for i in col if str(i) != '').strip()
                                  for col in df.columns]
                else:
                    df.columns = [str(col).strip() for col in df.columns]

                # Extra safety
                df.columns = list(df.columns)
                df = df.dropna(axis=1, how='all')   # drop empty columns

                # ====================== SAVING ======================
                if 'Reservoir' in name or 'Lake' in name or 'Power' in name or 'Flood' in name:
                    clean_name = clean_reservoir_name(name)
                    if not df.empty and len(df.columns) > 1:
                        if not "Date" in df.columns[0]:
                            continue
                        if "Power" in df.columns[1]:
                            clean_name += '_Power'
                    else:
                        continue
                    out_csv_path = out_path / f'{clean_name}.csv'
                else:
                    out_csv_path = out_path / f'page_{page:d}.csv'

                print(f'Saving → {out_csv_path}')

                df.to_csv(
                    str(out_csv_path),
                    index=False,
                    quoting=csv.QUOTE_NONE,
                    escapechar='\\',
                    encoding='utf-8'
                )

                results.append((page, name, df))

        except Exception as e:
            print(f"Error on page {page}: {type(e).__name__} - {e}")

    print(f"\nFinished processing {len(results)} tables.")
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
    else:
        # January style: merge row 0 + row 1 (which has units)
        text_row = h1

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
    Clean reservoir name: extract after dash, remove 'Reservoir',
    replace spaces with underscores, and handle camelCase.
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

    # Remove "Reservoir" / "Lake" if desired (optional)
    name = name.replace("Reservoir", "").replace("reservoir", "").strip()

    # Clean extra spaces
    name = " ".join(name.split())

    # Convert camelCase to snake_case (e.g. GlenCanyon → Glen_Canyon)
    name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)

    # Replace spaces with underscores and clean up
    name = name.replace(" ", "_")
    name = re.sub(r'_+', '_', name)          # multiple underscores → single
    name = name.strip('_')

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

from camelot.utils import get_page_layout, get_text_objects


def get_table_title(table, pdf_path, y_tolerance=15):
    """Find the closest text above the table (reservoir name)."""
    # Call get_page_layout with direct parameters (no layout_kwargs)
    layout, _ = get_page_layout(
        pdf_path,
        char_margin=2.0,  # higher = more tolerant grouping
        line_margin=0.5
    )

    htext_objs = get_text_objects(layout, ltype="horizontal_text")

    table_top = table._bbox[3]  # top y of table
    table_left = table._bbox[0]

    candidates = []
    for obj in htext_objs:
        text_top = obj.bbox[3]
        if text_top > table_top + y_tolerance:
            dist = math.hypot((obj.bbox[0] - table_left), (text_top - table_top))
            text = obj.get_text().strip()
            if text:
                candidates.append((dist, text))

    if candidates:
        candidates.sort(key=lambda x: x[0])  # closest first
        return candidates[0][1]

    return None

def usbr_24_month_to_csv(reservoirs: List[Tuple[int, str, pd.DataFrame]], path: str | Path):
    path = Path(path)
    ensure_directory(path)

    table_num = 0

    for page_num, name, df in reservoirs:
        table_num += 1
        if 'Reservoir' in name or 'Lake' in name or 'Power' in name or 'Flood' in name:
            if 'Powell' in name:
                pass
            name = clean_reservoir_name(name)
            value = df.iloc[0, 1]  # row 0, column 1 (0-based indexing)
            if "Power" in value:
                name += '_Power'
            out_csv_path = path / f'{name}.csv'
        else:
            out_csv_path = path / f'page_{page_num:d}.csv'
        print(f'table to csv: {out_csv_path}')
        df.to_csv(str(out_csv_path), index=False,
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
            out_csv_path = path / f'page_{page_num:04d}'
        elif num_pages >= 100:
            out_csv_path = path / f'page_{page_num:03d}'
        elif num_pages >= 10:
            out_csv_path = path / f'page_{page_num:02d}'
        else:
            out_csv_path = path / f'page_{page_num:d}'
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
                        if not out_path.exists():
                            # extract_reservoir_tables(local_path, Path('tmp/'))
                            reservoir_page_names = get_reservoir_names(local_path)
                            # extract_reservoir_tables(local_path, str(out_path))
                            reservoirs = read_reservoir_camelot(local_path, out_path, reservoir_page_names)
                            # usbr_24_month_to_csv(reservoirs, out_path)
                    continue

                try:
                    print(f"Downloading: {year}/{filename} ... {file_url} ", end="")
                    r = session.get(file_url, timeout=30)

                    if r.status_code == 200 and len(r.content) > 5000:
                        local_path.write_bytes(r.content)
                        print("✅ Done")
                    else:
                        print("Not found")
                        return
                except Exception as e:
                    print(f"Failed: {e}")

                time.sleep(delay)

    print("\n✅ Download process complete!")


if __name__ == "__main__":
    years = [2026]
    download_usbr_24mo_reports(years=years)
    # https://www.usbr.gov/lc/region/g4000/24mo/index.html
    # report_path = Path('/opt/dev/riverwar/data/USBR_24Month_Reports/May26.pdf')
    # tables = read_pdf_camelot(report_path)
    # out_path = Path(f'../data/reports/24_Month_Reports/{report_path.parent.name}/{report_path.stem}')
    # usbr_24_month_to_csv(tables, out_path)

    #for year in range(2026, 2027):
    #    report_path = Path(f'/opt/dev/USBR_Reports/Lower_Basin_Annual_Reports/{year}.pdf')
    #    tables = read_pdf_camelot(report_path)
    #    out_path = Path(f'../data/reports/{report_path.parent.name}/{report_path.stem}')
    #    tables_to_csv(tables, out_path)