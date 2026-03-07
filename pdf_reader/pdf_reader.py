import camelot
import matplotlib
from pathlib import Path
matplotlib.use('TkAgg')
import csv

def ensure_directory(path: str | Path) -> Path:
    """Create directory (and parents) if it doesn't exist"""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory

def read_pdf(report_path:Path):
    tables = camelot.read_pdf(str(report_path), flavor='stream', pages='all')
    out_path = Path('data/report_harvest/' + report_path.stem)
    ensure_directory(out_path)
    # Tune: tables = camelot.read_pdf(..., table_areas=['x1,y1,x2,y2'], columns=[...])
    for table in tables:
        # print(table.parsing_report)
        # Plot lines + joints → for column x-coords
        # camelot.plot(table, kind='contour', filename='debug_contour.png')  # Hover mouse → see x1,y1,x2,y2
        # camelot.plot(table, kind='joint', filename='debug_joint.png')  # Intersections show where columns split
        # camelot.plot(table, kind='line', filename='debug_line.png')
        # order_on_page = table.parsing_report['order']
        # print(df.shape)
        # print(df.head(20).to_string(index=False))

        page_num = table.parsing_report['page']
        df = table.df
        for col in df.columns:
            # Only touch object/string columns (or ones that might contain commas)
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(',', '', regex=False)

        out_csv_path = out_path / f'table_{page_num}.csv'
        df.to_csv(out_csv_path, index=False,
          quoting=csv.QUOTE_NONE,     # ← most important for no quotes
          escapechar='\\')

if __name__ == "__main__":
    # fig, ax = plt.subplots()
    # ax.plot([1, 2, 3], [4, 5, 6])
    # ax.set_title("TEST WINDOW – Do you see this?")
    # plt.show(block=True)
    # matplotlib.get_backend()

    read_pdf(Path('/opt/dev/USBR_Reports/Lower_Basin_Annual_Reports/2024.pdf'))

