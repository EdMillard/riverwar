import camelot
import csv
import matplotlib
from pathlib import Path

def ensure_directory(path: str | Path) -> Path:
    """Create directory (and parents) if it doesn't exist"""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory

def read_pdf(report_path:Path, output_path:Path) -> None:
    tables = camelot.read_pdf(str(report_path), flavor='stream', pages='all')
    ensure_directory(out_path)
    # Tune: tables = camelot.read_pdf(..., table_areas=['x1,y1,x2,y2'], columns=[...])
    num_tables = len(tables)
    for table in tables:
        page_num = table.parsing_report['page']
        df = table.df
        for col in df.columns:
            # Only touch object/string columns (or ones that might contain commas)
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(',', '', regex=False)

        if num_tables >= 1000:
            out_csv_path = out_path / f'table_{page_num:04d}.csv'
        elif num_tables >= 100:
            out_csv_path = out_path / f'table_{page_num:03d}.csv'
        elif num_tables >= 10:
            out_csv_path = out_path / f'table_{page_num:02d}.csv'
        else:
            out_csv_path = out_path / f'table_{page_num:d}.csv'
        df.to_csv(out_csv_path, index=False,
          quoting=csv.QUOTE_NONE,     # ← most important for no quotes
          escapechar='\\')

if __name__ == "__main__":
    report_path = Path('/opt/dev/riverwar/data/USBR_24_Month/March_2026/24mo.pdf')
    out_path = Path(f'../data/reports/24_Month/{report_path.parent.name}/{report_path.stem}')
    read_pdf(report_path, out_path)
    for year in range(2022, 2025):
        report_path = Path(f'/opt/dev/USBR_Reports/Lower_Basin_Annual_Reports/{year}.pdf')
        out_path = Path(f'../data/reports/{report_path.parent.name}/{report_path.stem}')
        read_pdf(report_path, out_path)
