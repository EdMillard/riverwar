import camelot
import matplotlib
from pathlib import Path
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

def read_pdf(path:Path):
    tables = camelot.read_pdf(str(path), flavor='stream', pages='25')
    # Tune: tables = camelot.read_pdf(..., table_areas=['x1,y1,x2,y2'], columns=[...])
    for table in tables:
        print(table.parsing_report)
        # camelot.plot(table, kind='contour', filename='debug_contour.png')  # Hover mouse → see x1,y1,x2,y2

        # Plot lines + joints → for column x-coords
        # camelot.plot(table, kind='joint', filename='debug_joint.png')  # Intersections show where columns split
        # camelot.plot(table, kind='line', filename='debug_line.png')

        order_on_page = table.parsing_report['order']
        # Check accuracy/whitespace
        page_num = table.parsing_report['page']
        df = table.df
        print(df.shape)
        print(df.head(20).to_string(index=False))
        # if df.shape[1] <= 2:  # usually 1 column in your case
        #     df = df.T.reset_index(drop=True)

        df.to_csv(f'{path.stem}_table_{page_num}.csv')

if __name__ == "__main__":
    # fig, ax = plt.subplots()
    # ax.plot([1, 2, 3], [4, 5, 6])
    # ax.set_title("TEST WINDOW – Do you see this?")
    # plt.show(block=True)
    # matplotlib.get_backend()

    read_pdf(Path('/opt/dev/USBR_Reports/Lower_Basin_Annual_Reports/2024.pdf'))

