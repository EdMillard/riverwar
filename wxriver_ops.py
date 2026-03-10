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
import colorado.ub as ub
import colorado.allb as all_b
from report.doc import Report
from sheet import sheet
from sheet.sheet import Sheet
import pandas as pd
from scipy.interpolate import interp1d
import warnings

class Colorado_River_Ops(Sheet):
    def __init__(self):
        headers = [lb.MEAD_ELEVATION, lb.MEAD, ub.POWELL_ELEVATION, ub.POWELL, ub.FLAMING_GORGE, ub.BLUE_MESA]
        super().__init__(headers, start_year=2026, end_year=2026)


    def load_df(self, df_compact : pd.DataFrame) -> None:
        df_len = len(self.df) + 2
        usbr_lake_mead_elevation_ft = 6123
        sheet.usbr_last_value(self.df, usbr_lake_mead_elevation_ft, self.start_year, self.end_year, title=lb.MEAD_ELEVATION, divisor=1)

        usbr_lake_mead_storage_af = 6124
        sheet.usbr_last_value(self.df, usbr_lake_mead_storage_af, self.start_year, self.end_year, title=lb.MEAD, month=10, divisor=1)

        usbr_lake_powell_elevation_af = 508
        sheet.usbr_last_value(self.df, usbr_lake_powell_elevation_af, self.start_year, self.end_year, title=ub.POWELL_ELEVATION, divisor=1)

        usbr_lake_powell_storage_af = 509
        sheet.usbr_last_value(self.df, usbr_lake_powell_storage_af, self.start_year, self.end_year, title=ub.POWELL, divisor=1)

        usbr_flaming_gorge_storage_af = 3371
        sheet.usbr_last_value(self.df, usbr_flaming_gorge_storage_af, self.start_year, self.end_year, title=ub.FLAMING_GORGE, divisor=1)

        usbr_blue_mesa_storage_af = 76
        sheet.usbr_last_value(self.df, usbr_blue_mesa_storage_af, self.start_year, self.end_year, title=ub.BLUE_MESA, divisor=1)

    def build_sheet(self)-> None:
        # self.set_bg(lb.MX_TREATY, ub.GLEN_CANYON_RELEASE, color=all_b.USBR_AR_FLOW)

        self.format_header()


def run():
    # Elevation_ft_NAVD88,Elevation_ft_NGVD29,Area_acres,Capacity_acrefeet
    deadpool = 1_578_783

    a3510 = get_lake_powell_capacity(3510.0, elev_col='Elevation_ft_NAVD88', cap_col='Capacity_acrefeet') - deadpool
    a3500 = get_lake_powell_capacity(3500.0, elev_col='Elevation_ft_NAVD88', cap_col='Capacity_acrefeet') - deadpool
    a3490 = get_lake_powell_capacity(3490.0, elev_col='Elevation_ft_NAVD88', cap_col='Capacity_acrefeet') - deadpool
    now = get_lake_powell_capacity(3530.19, elev_col='Elevation_ft_NAVD88', cap_col='Capacity_acrefeet') - deadpool
    print(f'3530.19:\t{now:8,.0f}\n3510.00:\t{a3510:8,.0f}\t{now-a3510:8,.0f}\n3500.00:\t{a3500:8,.0f}\t{now-a3500:8,.0f}\n3490.00:\t{a3490:8,.0f}\t{now-a3490:8,.0f}')

    river_ops = Colorado_River_Ops()
    file_path = Path('excel/Colorado_River_Ops.xlsx')
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        river_ops.export(writer, all_b.OPERATIONS, None, number_format='#,##0;-#,##0')

        wb: Workbook = writer.book
        wb.calcMode = "auto"  # ensure automatic calculation

    Report.open_docx_in_app(file_path)


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


if __name__ == "__main__":
    run()