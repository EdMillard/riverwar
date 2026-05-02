"""
Copyright (c) 2025 Ed Millard

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
from data_sets.data_set import DataSet
import pandas as pd
from pathlib import Path
from typing import Optional, List
from reservoirs.aquifers import LTSC
import colorado.lb as lb

class AZLTSCDataSet(DataSet):
    def __init__(self, name:str, month:int=10):
        super().__init__(name, month=month)
        self.df = self.from_csv(name)

    def load(self) -> Optional[pd.DataFrame]:
        path: Path = Path('data/ADWR/AMA')
        # start_year = 1989
        # end_year = 2023
        # years: List[int] = list(range(start_year, end_year+1))
        # self.recharge_summary_data_from_excel(path, years)

        out_headers = ['Water_Delivered', 'Annual_Recovery', 'Evaporation_Transpiration_Losses', 'Cut_to_Aquifer',
                       'Other_Losses', 'LTS_Credits_Recovered', 'LTS_Credits_Extinguished', 'Other_Adjustment']
        ltsc_total = LTSC(path, 'total', out_headers)

        # stored = self.water_delivered - self.annual_recovery - self.credits_recovered
        # stored_adjusted = stored - self.cut_to_aquifer  # Unclear if we can count this as stored water, no accounting
        # stored_adjusted = stored_adjusted - self.et_losses - self.other_losses # - self.credits_extinguished

        # === Calculate Stored (per year) ===
        ltsc_total.df[lb.AZ_LTSC_STORED] = (
                ltsc_total.df['Water_Delivered']
                - ltsc_total.df['Annual_Recovery']
                - ltsc_total.df.get('LTS_Credits_Recovered', 0)
        )

        # === Calculate Stored_Adjusted (per year) ===
        # df['Stored_Adjusted'] = (
        #         df['Stored']
        #         - df.get('Cut_to_Aquifer', 0)
        #         - df.get('Evaporation_Transpiration_Losses', 0)
        #        - df.get('Other_Losses', 0)
        #    # - df.get('LTS_Credits_Extinguished', 0)   # you had this commented
        #)

        # Optional: round to reasonable decimal places
        # ltsc_total.df[['Stored', 'Stored_Adjusted']] = ltsc_total.df[['Stored', 'Stored_Adjusted']].round(4)

        return ltsc_total.df

