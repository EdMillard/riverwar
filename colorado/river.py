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
import colorado.allb as all_b
from report.doc import Report
from sheet import sheet
from colorado.iii_c import III_C
from colorado.imperial import Imperial
from colorado.reservoirs import Reservoirs
from colorado.compact import Compact
from colorado.lb_tributary_cul import LBTributaryCUL
from colorado.lb_main_cul import LBMainCUL

def run():
    # Elevation_ft_NAVD88,Elevation_ft_NGVD29,Area_acres,Capacity_acrefeet

    lb_main_cul = LBMainCUL()
    iii_c = III_C()
    imperial = Imperial()
    reservoirs = Reservoirs()
    compact = Compact()
    lb_tributary_cul = LBTributaryCUL()

    file_path = Path('excel/Colorado_River_Math.xlsx')
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        compact.export(writer, all_b.COMPACT_SHEET, compact.df)
        iii_c.export(writer, all_b.III_C_SHEET, compact.df)
        lb_main_cul.export(writer, all_b.LB_MAINSTEM_CUL_SHEET, compact.df, number_format='#,##0;-#,##0')
        lb_tributary_cul.export(writer, all_b.LB_TRIBUTARY_CUL_SHEET, compact.df, number_format='#,##0;-#,##0')
        reservoirs.export(writer, all_b.RESERVOIRS_SHEET, compact.df)
        imperial.export(writer, all_b.IMPERIAL_SHEET, compact.df)

        wb: Workbook = writer.book
        wb.calcMode = "auto"  # ensure automatic calculation
        wb.calculation.fullCalcOnLoad = True
        wb.calculation.forceFullCalc = True

    notes_path = Path(f'excel/Colorado_River_{all_b.NOTES_SHEET}.xlsx')
    sheet.copy_worksheet_to_new_workbook(
        source_wb_path=notes_path,
        sheet_name=all_b.NOTES_SHEET,
        target_wb_path=file_path
    )
    Report.open_docx_in_app(file_path)


import pandas as pd
from scipy.interpolate import interp1d
import warnings

def get_lake_powell_capacity(
    elevation_ft: float,
    csv_path: str = "data/Colorado_River/Lake_Powell_2018_ElevAreaCap_interp.csv",  # <-- update this
    elev_col: str = "elevation",      # adjust if column name differs (check your CSV)
    cap_col: str = "capacity_af",     # adjust if needed (often "storage" or "capacity")
    navd88: bool = True               # reminder: elevations must be NAVD 88
) -> float:
    """
    Returns active storage capacity in acre-feet for a given elevation (ft NAVD 88)
    using the USGS 2018 Lake Powell elevation-area-capacity table (interpolated preferred).

    Example usage:
        capacity = get_lake_powell_capacity(3650.5)
        print(f"At 3650.5 ft: {capacity:,.0f} af")
    """
    if not navd88:
        warnings.warn("Elevations should be in NAVD 88 datum per 2018 USGS data.")

    # Load the CSV (skip any header rows if needed; inspect your file)
    df = pd.read_csv(csv_path)

    # Assume columns are something like: elevation_ft, area_acres, capacity_af
    # Rename for consistency if needed
    df = df.rename(columns={
        elev_col: 'elevation_ft',
        cap_col: 'capacity_af'
    })

    # Sort by elevation (should already be sorted, but ensure)
    df = df.sort_values('elevation_ft').dropna(subset=['elevation_ft', 'capacity_af'])

    if elevation_ft < df['elevation_ft'].min() or elevation_ft > df['elevation_ft'].max():
        raise ValueError(
            f"Elevation {elevation_ft} ft is outside table range "
            f"({df['elevation_ft'].min():.2f} to {df['elevation_ft'].max():.2f} ft)"
        )

    # Create linear interpolator (capacity as function of elevation)
    interpolator = interp1d(
        df['elevation_ft'],
        df['capacity_af'],
        kind='linear',
        fill_value="extrapolate"  # but we already checked bounds
    )

    capacity = interpolator(elevation_ft)

    return float(capacity)
