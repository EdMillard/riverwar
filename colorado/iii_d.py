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
import colorado.lb as lb
import colorado.ub as ub
import colorado.allb as all_b
import pandas as pd
from sheet import sheet
from sheet.sheet import Sheet, sheets
from typing import List
from pathlib import Path
from scipy.interpolate import interp1d
import warnings


class III_D(Sheet):
    def __init__(self, name:str):
        headers = [lb.MEXICO, lb.HOOVER_USGS, lb.MEAD, lb.MEAD_DELTA, lb.LAKE_MEAD_CUL,
                   ub.NATURAL_LEES_FERRY, all_b.III_D, ub.LEES_FERRY_USGS_WY,
                   ub.GLEN_CANYON_WY, ub.POWELL_WY, ub.POWELL_DELTA_WY, ub.POWELL_EVAPORATION_WY,
                   ub.INFLOW_WY, ub.INFLOW_UNREGULATED_WY,
                   lb.MEAD_ELEVATION, lb.MEAD_ELEVATION_DELTA,
                   ub.POWELL_ELEVATION_WY, ub.POWELL_ELEVATION_DELTA_WY,
                   ]
        super().__init__(name, headers,  start_year=1922, end_year=2026)
        self.years: List[int] = list(range(self.start_year, self.end_year+1))
        sheets.append(self)

    def load_df(self, df_compact : pd.DataFrame) -> None:
        WY = 10

        df_mx = sheet.read_csv('data/USBR_Reports/mx/usbr_mx_satisfaction_of_treaty.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df_mx, lb.MEXICO)

        sheet.usgs_annuals(self.df, '09421500', 1936, self.end_year, title=lb.HOOVER_USGS)

        usbr_lake_mead_storage_af = 6124
        sheet.usbr_last_value(self.df, usbr_lake_mead_storage_af, 1937, self.end_year, title=lb.MEAD)

        reservoir_path = Path('data/USBR_Lower_Colorado_CUL/Reservoir')
        df_mead_evap = sheet.read_csv(reservoir_path / 'lake_mead.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df_mead_evap, lb.LAKE_MEAD_CUL,divisor=1000000)

        usbr_lake_mead_elevation_ft = 6123
        sheet.usbr_last_value(self.df, usbr_lake_mead_elevation_ft, 1936, self.end_year, title=lb.MEAD_ELEVATION, divisor=1)

        sheet.lf_natural_flow_from_excel(self.df, start_row=19)

        sheet.usgs_annuals(self.df, '09380000', self.start_year, self.end_year, title=ub.LEES_FERRY_USGS_WY,
                           month=WY)

        usbr_lake_powell_storage_af = 509
        sheet.usbr_last_value(self.df, usbr_lake_powell_storage_af, 1964, self.end_year,  title=ub.POWELL_WY, month=WY)

        usbr_lake_powell_evap_af = 510
        sheet.usbr_annuals(self.df, usbr_lake_powell_evap_af, 1964, self.end_year,  title=ub.POWELL_EVAPORATION_WY, month=WY)

        usbr_lake_powell_release_total_af = 4354
        sheet.usbr_annuals(self.df, usbr_lake_powell_release_total_af, 1964, self.end_year, title=ub.GLEN_CANYON_WY, month=WY)

        usbr_lake_powell_regulated_inflow_af = 4288
        sheet.usbr_annuals(self.df, usbr_lake_powell_regulated_inflow_af, 1964, self.end_year, title=ub.INFLOW_WY, month=WY)

        usbr_lake_powell_unregulated_inflow_af = 4301
        sheet.usbr_annuals(self.df, usbr_lake_powell_unregulated_inflow_af, 1964, self.end_year, title=ub.INFLOW_UNREGULATED_WY, month=WY)

        usbr_lake_powell_elevation_af = 508
        sheet.usbr_last_value(self.df, usbr_lake_powell_elevation_af, 1965, self.end_year, title=ub.POWELL_ELEVATION_WY, divisor=1, month=WY)


    def build_sheet(self)-> None:
        ws = self.ws
        df = self.df
        self.set_bg(lb.MEXICO, color=all_b.USBR_AR_FLOW_BG)

        self.set_bg(lb.MEAD, color=all_b.LIGHT_BLUE_BG)
        self.set_bg(lb.MEAD_DELTA, color=all_b.LIGHT_BLUE_BG)
        sheet.formula_delta(ws, df, lb.MEAD_DELTA, lb.MEAD, start_row=16)
        self.set_column_negative_red(lb.MEAD_DELTA, negative_color='Red', positive_color='Color22')

        self.set_bg(lb.MEAD_ELEVATION, color=all_b.USBR_RISE_ELEVATION_BG)
        sheet.formula_delta(ws, df, lb.MEAD_ELEVATION_DELTA, lb.MEAD_ELEVATION, start_row=16)
        self.set_column_negative_red(lb.MEAD_ELEVATION_DELTA, negative_color='Red', positive_color='Color22')
        self.set_bg(lb.MEAD_ELEVATION_DELTA, color=all_b.USBR_RISE_ELEVATION_BG)

        self.set_bg(ub.NATURAL_LEES_FERRY, color=all_b.USBR_NATURAL_BG)
        self.set_bg(ub.LEES_FERRY_USGS_WY, color=all_b.USGS_BG)
        self.set_bg(ub.GLEN_CANYON_WY, color=all_b.USGS_BG)

        self.set_bg(ub.POWELL_WY, color=all_b.LIGHT_BLUE_BG)
        sheet.formula_delta(ws, df, ub.POWELL_DELTA_WY, ub.POWELL_WY, start_row=45)
        self.set_column_negative_red(ub.POWELL_DELTA_WY, negative_color='Red', positive_color='Color22')
        self.set_bg(ub.POWELL_WY, color=all_b.LIGHT_BLUE_BG)
        self.set_bg(ub.POWELL_DELTA_WY, color=all_b.LIGHT_BLUE_BG)
        self.set_bg(ub.POWELL_EVAPORATION_WY, color=all_b.EVAPORATION_BG)
        self.set_bg(ub.POWELL_ELEVATION_WY, color=all_b.USBR_RISE_ELEVATION_BG)
        self.set_bg(ub.POWELL_ELEVATION_DELTA_WY, color=all_b.USBR_RISE_ELEVATION_BG)

        self.set_bg(ub.INFLOW_WY, color=all_b.USGS_BG)
        self.set_bg(ub.INFLOW_UNREGULATED_WY, color=all_b.USGS_BG)

        sheet.formula_delta(ws, df, ub.POWELL_ELEVATION_DELTA_WY, ub.POWELL_ELEVATION_WY, start_row=45)
        self.set_column_negative_red(ub.POWELL_ELEVATION_DELTA_WY, negative_color='Red',positive_color='Color22')

        # values = sheet.usgs_annuals(self.df, '09380000', 1955, self.end_year) # ub.LEES_FERRY_USGS
        # ten_year = sheet.moving_average_10yr(values)
        # sheet.write_column(self.ws, all_b.III_D, ten_year)

        sheet.formula(ws, df, all_b.III_D,
                      f"=AVERAGE('{ub.LEES_FERRY_USGS_WY}'[row-9]:'{ub.LEES_FERRY_USGS_WY}'[row])",
                      start_row=10, insert_row_index=False)

        powell_3510_af = III_D.af_for_elevation(3510.00)
        powell_3500_af = III_D.af_for_elevation(3500.00)
        powell_current_ft = ws['R106'].value
        powell_current_af = III_D.af_for_elevation(powell_current_ft)
        above_3510_af = powell_current_af - powell_3510_af
        above_3500_af = powell_current_af - powell_3500_af
        power_heads_delta =  above_3500_af - above_3510_af

        ws['B105'] = 1.45
        ws['B106'] = 1.45

        ws['B108'] = '=AVERAGE(B97:B106)'
        ws['C108'] = ' III(c) – Mexico 10 yr average'

        ws['B109'] = '=B108/2 + 7.5'
        ws['C109'] = ' III(c) + III(d)'

        self.set_bg(lb.MEXICO, color='ffff00', start_row=105, end_row=106)
        self.set_bg(lb.MEXICO, color='ffff00', start_row=112, end_row=112)
        ws['C112'] = 'Extrapolated'

        self.set_bg(lb.MEXICO, color='00ff00', start_row=113, end_row=113)
        self.set_bg(all_b.III_D, color='00ff00', start_row=106, end_row=106)
        self.set_bg(ub.LEES_FERRY_USGS_WY, color='40ff40', start_row=106, end_row=106)
        ws['C113'] = 'Projected Oct 1, 2026'

        self.set_bg(lb.MEXICO, color='ff80ff', start_row=114, end_row=114)
        ws['C114'] = 'CAP Gaming Sweet Spot, Crashing Powell, Tripping Wire and 603'
        self.set_bg(ub.GLEN_CANYON_WY, color='ff80ff', start_row=95, end_row=99)

        ws['C116'] = 'X'

        ws['H107'] = 'To Reach Oct 1, 2026 w/o AZ tripwire & above 3510\''
        sheet.add_borders_to_column(ws, 8, 107, 107, end_col=11, which='bottom')

        ws['I108'].value = ws['I106'].value
        ws['I106'] = '=I113'
        ws['J108'] = ' Lee’s Ferry Since Oct 1, 2025'
        ws['I109'] = above_3510_af / 1000000
        ws['J109'] = ' Above 3510’ Now'
        ws['I110'] = 1.5
        ws['J110'] = ' Inflow'
        ws['H110'] = ' Editable-->'
        ws['I111'] = 1.82
        ws['J111'] = ' Flaming Gorge'
        ws['H111'] = ' Editable-->'
        ws['I112'] = '=-(M105-M106)'
        ws['J112'] = ' Powell Evaporation Remaining'
        sheet.add_borders_to_column(ws, 9, 113, 113, end_col=10, which='top')
        ws['I113'] = '=SUM(I108:I112)'
        ws['J113'] = ' Lees Ferry 2026 WY'

        ws['I115'] = '=I113-I108'
        ws['J115'] = ' Remaining release to Mead thru Oct 1, 2026'

        ws['N107'] = 'To Reach Apr 1, 2027 on ROTR'
        sheet.add_borders_to_column(ws, 14, 107, 107, end_col=16, which='bottom')
        ws['N108'] = '=N106'
        ws['O108'] = ' Inflow Oct 1 to April 1, 2027 (same as 2026)'
        ws['N109'] = '=-M106'
        ws['O109'] = ' Powell Evaporation Oct 1 to April 1, 2027 (same as 2026)'
        ws['M110'] = ' Editable-->'
        ws['N110'] = 0.5
        ws['O110'] = ' Drop Power Head 3510\' to 3500\''
        ws['M111'] = ' Editable-->'
        ws['N111'] = '=3-I111'
        ws['O111'] = ' Flaming Gorge'
        ws['M112'] = ' Editable-->'
        ws['N112'] = '=-I108'
        ws['O112'] = ' Lees Ferry Oct 1 to April 1, 2027 (same as 2026)'
        sheet.add_borders_to_column(ws, 14, 113, 113, end_col=16, which='top')
        ws['N113'] = '=SUM(N108:N112)'
        ws['O113'] = ' Powell Reserves Left Apr 1, 2027'
        ws['N114'] = '=3-I111-N111'
        ws['O114'] = ' Flaming Gorge Left Apr 1, 2027'

        ws.row_dimensions[116].height = 15

        self.set_bg(lb.MEXICO, to=ub.POWELL_ELEVATION_DELTA_WY, color='ffffff', start_row=107, end_row=107)
        sheet.set_font(ws, 107, 115, 1, ws.max_column)
        sheet.set_number_format(ws, 106, 107, 8, 9, number_format='0.000')
        sheet.set_number_format(ws, 107, 115, 2, 2, number_format='0.000')
        sheet.set_number_format(ws, 107, 115, 9, 9, number_format='0.000')
        sheet.set_number_format(ws, 107, 115, 14, 14, number_format='0.000')

        sheet.clear_range(ws, ws.max_row, ws.max_row, 1, ws.max_column)
        self.format_header()
        self.set_column_width(ub.NATURAL_LEES_FERRY, 7, to=ub.INFLOW_UNREGULATED_WY)

    @staticmethod
    def af_for_elevation(feet):
        return get_lake_powell_capacity(feet, elev_col='Elevation_ft_NAVD88', cap_col='Capacity_acrefeet')

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