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
# from colorado.graph_inflow_outflow import InflowOutflowChart
from graphs.graph_reservoirs import ReservoirChart
from graphs.chart_frame import ChartFrame, NotebookFrame
import colorado.lb as lb
from reservoirs.reservoir import Reservoir

from reservoirs.imperial import Imperial
# from reservoirs.roosevelt import Roosevelt
from reservoirs.srp import SRP
from reservoirs.lake_pleasant import LakePleasant
from reservoirs.lake_havasu import LakeHavasu
from reservoirs.lake_mohave import LakeMohave
from reservoirs.aquifers import Aquifers
from reservoirs.lake_mead import LakeMead
from reservoirs.lake_powell import LakePowell
from reservoirs.flaming_gorge import FlamingGorge
from reservoirs.blue_mesa import BlueMesa
from reservoirs.navajo import Navajo

from reservoirs.green_mountain import GreenMountain
from reservoirs.lake_granby import LakeGranby
from reservoirs.mcphee import Mcphee
from reservoirs.lake_nighthorse import LakeNighthorse
from reservoirs.fontenelle import Fontenelle
from reservoirs.ruedi import Ruedi
from reservoirs.taylor_park import TaylorPark
from reservoirs.vallecito import Vallecito
from reservoirs.starvation import Starvation
from reservoirs.strawberry import Strawberry
from reservoirs.dillon import Dillon
# from reservoirs.gross import Gross
# from reservoirs.groundhog import Groundhog
# from reservoirs.lemon import Lemon
# from reservoirs.grand_lake import GrandLake
# from reservoirs.shadow_mountain import ShadowMountain
# from reservoirs.heron import Heron

class ReservoirsReality(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        reports = ChartFrame.find_directories_with_file('data/USBR_24Month_Reports', 'Lake_Powell.csv')


        flaming_gorge = FlamingGorge()
        navajo = Navajo()

        strawberry = Strawberry(upstream=[])
        blue_mesa = BlueMesa()
        lake_powell = LakePowell(upstream=[flaming_gorge, blue_mesa, navajo])
        lake_mead = LakeMead(upstream=[lake_powell])
        lake_mohave = LakeMohave(upstream=[lake_mead])
        lake_havasu = LakeHavasu(upstream=[lake_mohave])
        imperial = Imperial(upstream=[lake_havasu])
        lake_pleasant = LakePleasant(upstream=[])
        # roosevelt = Roosevelt(upstream=[])
        srp = SRP(upstream=[])
        aquifers = Aquifers(upstream=[])

        self.reservoirs = [
            imperial, aquifers, srp, lake_pleasant, lake_havasu, lake_mohave,
            lake_mead, lake_powell, flaming_gorge, navajo, strawberry
        ]

        dillon = Dillon()
        fontenelle = Fontenelle(upstream=[])
        lake_granby = LakeGranby(upstream=[])
        mcphee = Mcphee(upstream=[])
        lake_nighthorse = LakeNighthorse(upstream=[])
        taylor_park = TaylorPark(upstream=[])
        vallecito = Vallecito(upstream=[])
        green_mountain = GreenMountain(upstream=[])
        starvation = Starvation(upstream=[])
        ruedi = Ruedi(upstream=[])
        # gross = Gross()
        # groundhog = Groundhog()
        # grand_lake = GrandLake(upstream=[])
        # lemon = Lemon(upstream=[])
        # shadow_mountain = ShadowMountain(upstream=[])
        # heron = Heron(upstream=[])

        self.ub_reservoirs = [
            blue_mesa, lake_granby, dillon,
            fontenelle,
            vallecito, taylor_park,  mcphee, lake_nighthorse, green_mountain,  ruedi,
            starvation,
            # grand_lake, lemon, shadow_mountain, heron, groundhog, gross
        ]
        reservoir_lists = [self.reservoirs, self.ub_reservoirs]
        super().__init__(notebook_frame, reservoir_lists=reservoir_lists, reports=reports, page_name='Reservoir Reality')


    def load_charts(self):
        start = self.start_nav.current_date
        # current = self.current_nav.current_date
        end = self.end_nav.current_date

        power_head_zones = [
            ('#ffffff', 'Available Capacity'),
            (Reservoir.high_power_pool_color, 'Normal Power Head'),
            (Reservoir.low_power_pool_color, 'Low Power Head'),
            (Reservoir.non_power_pool_color, 'Limited Access')
        ]

        aquifer_zones = [
            (lb.TUCSON_COLOR, 'Tucson AMA'),
            (lb.PINAL_COLOR, 'Pinal AMA'),
            (lb.PHX_COLOR, 'Phoenix AMA')
        ]

        reserved_zones = [
            (lb.AZ_COLOR, 'AZ'),
            (lb.NV_COLOR, 'NV'),
            (lb.CA_COLOR, 'CA')
        ]

        reservoir_chart = ReservoirChart(
            self.reservoirs, start_date=start, current_date=self.current_time_from_usbr, end_date=end, y_max=14.0,
            power_head_zones=power_head_zones, reserved_names=reserved_zones, aquifer_zones=aquifer_zones
        )
        self.charts.append(reservoir_chart)

        reservoir_chart = ReservoirChart(
            self.ub_reservoirs, start_date=start, current_date=self.current_time_from_usbr, end_date=end, y_max=0.9,
            percentage = 0.1
        )
        self.charts.append(reservoir_chart)

        # inflow_chart = InflowOutflowChart(
        #    self.reservoirs, start_date=start, current_date=current, end_date=end
        # )
        # self.charts.append(inflow_chart)
