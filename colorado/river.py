"""
Copyright (c) 2026 Ed Millard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from pathlib import Path
from openpyxl import Workbook
import colorado.lb as lb
import colorado.allb as all_b
import pandas as pd
from report.doc import Report
from sheet import sheet
from colorado.iii_c import III_C
from colorado.imperial import Imperial
from colorado.reservoirs import Reservoirs
from colorado.compact import Compact
from colorado.lb_CUL import LB_CUL


def run():
    iii_c = III_C()
    imperial = Imperial()
    reservoirs = Reservoirs()
    compact = Compact()
    lb_CUL = LB_CUL()

    file_path = Path('excel/Colorado_River_Math.xlsx')
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        lb_CUL.export(writer, lb.LB_CUL, compact.df, number_format='#,##0;-#,##0')
        compact.export(writer, all_b.COMPACT, compact.df)
        iii_c.export(writer, all_b.III_C, compact.df)
        reservoirs.export(writer, all_b.RESERVOIRS, compact.df)
        imperial.export(writer, lb.IMPERIAL, compact.df)

        wb: Workbook = writer.book
        wb.calcMode = "auto"  # ensure automatic calculation

    notes_path = Path('excel/Colorado_River_Notes.xlsx')
    sheet.copy_worksheet_to_new_workbook(
        source_wb_path=notes_path,
        sheet_name="Notes",
        target_wb_path=file_path
    )
    Report.open_docx_in_app(file_path)