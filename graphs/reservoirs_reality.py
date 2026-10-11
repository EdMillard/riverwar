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
'''
The Colorado River Storage Project has four initial storage units. “Participating projects” are a separate list of irrigation and municipal projects that share in CRSP power revenues; most do not have one reservoir capacity the way the storage units do.

Initial storage units

| Unit | Reservoir | River | Capacity | Power |
|---|---|---|---|---|
| Glen Canyon | Lake Powell | Colorado (AZ/UT) | 24,322,000 acre-feet live capacity at elevation 3,700 | 1,320 MW |
| Flaming Gorge | Flaming Gorge | Green (UT/WY) | 3,788,900 acre-feet total; about 3,749,000 usable | 152 MW |
| Navajo | Navajo | San Juan (NM/CO) | about 1,696,000 acre-feet active | no powerplant |
| Wayne N. Aspinall | Blue Mesa | Gunnison (CO) | 940,800 total; 829,500 usable | 86 MW |
| Wayne N. Aspinall | Morrow Point | Gunnison | 117,190 total | 173 MW |
| Wayne N. Aspinall | Crystal | Gunnison | 26,000 total | 32 MW |

Lake Powell is about 80 percent of the combined storage of the four initial units. Older tables sometimes list Glen Canyon at about 27 million acre-feet total capacity; the operating figure Reclamation uses is the 24.3 million acre-foot live capacity.

Participating projects

The 1956 act authorized 11. Later acts brought the authorized total to 22 after Pine River Extension was deleted. Reclamation says 16 were built or are being completed, and five were found infeasible and not built. Together the built projects supply more than 554,000 acre-feet a year for irrigation.

Built or in progress:

Central Utah, initial phase (Bonneville, Jensen, Vernal, and related units) — Utah
Emery County — Utah
Florida — Colorado
Hammond — New Mexico
Lyman — Wyoming and Utah
Paonia — Colorado
Seedskadee — Wyoming
Silt — Colorado
Smith Fork — Colorado
Eden — Wyoming
San Juan-Chama — Colorado and New Mexico
Navajo Indian Irrigation — New Mexico
Bostwick Park — Colorado
Dolores — Colorado
Dallas Creek — Colorado
Animas-La Plata — Colorado and New Mexico
Navajo-Gallup Water Supply — New Mexico (later participating project)

Authorized but infeasible or not built: La Barge (Wyoming), Fruitland Mesa (Colorado), Savery-Pot Hook (Colorado and Wyoming), San Miguel (Colorado), and West Divide (Colorado). Pine River Extension was deleted.

Those participating projects are sized as irrigation and municipal service, not as a single storage capacity, so there is no one acre-foot figure per project comparable to Lake Powell.
These are the Colorado River Storage Project participating-project reservoirs, not the four initial storage units. Capacities are total storage in acre-feet from Reclamation and basin reservoir tables.

Colorado

| Project | Reservoir | Capacity (AF) |
|---|---|---:|
| Dolores | McPhee | 381,195 |
| Animas-La Plata | Lake Nighthorse (Ridges Basin) | about 120,000 |
| Dallas Creek | Ridgway | 84,230 |
| Florida | Lemon | 39,792 |
| Paonia | Paonia | 16,703 |

| Smith Fork | Crawford | 14,395 |
| Bostwick Park | Silver Jack | 13,520 |
| Silt | Rifle Gap | about 12,200 |

Fruitland Mesa, San Miguel, and West Divide were authorized and not built.

Utah

| Project | Reservoir | Capacity (AF) |
|---|---|---:|
| Central Utah, Bonneville Unit | Strawberry (enlarged) | 1,106,500 |
| Central Utah, Bonneville Unit | Jordanelle | about 320,300 |
| Central Utah, Bonneville Unit | Starvation | 165,320 |
| Central Utah, Bonneville Unit | Upper Stillwater | 31,382 |
| Central Utah, Bonneville Unit | Currant Creek | 15,460 |
| Emery County | Joes Valley | 61,590 |
| Vernal Unit | Steinaker | 34,455 |
| Jensen Unit | Red Fleet | 25,700 |

| Emery County | Huntington North | 4,220 |

Wyoming and Wyoming–Utah

| Project | Reservoir | Capacity (AF) |
|---|---|---:|
| Seedskadee | Fontenelle | 344,800 |
| Eden | Big Sandy | 38,300 |
| Lyman | Meeks Cabin | 32,470 |
| Lyman | Stateline | 14,000 |

New Mexico and Colorado–New Mexico

| Project | Reservoir | Capacity (AF) |
|---|---|---:|
| San Juan-Chama | Heron | about 401,000 |
| Hammond | none | no storage reservoir |
| Navajo Indian Irrigation | uses Navajo Reservoir | Navajo is an initial CRSP unit, 1,696,000 active, not a participating-project reservoir |

La Barge and Savery-Pot Hook were authorized and not built. Pine River Extension was deleted. Navajo-Gallup is a later participating project and is a pipeline from Navajo Reservoir, not a new storage reservoir.

Denver Water
https://www.denverwater.org/sites/default/files/water-watch-report.pdf

MWD
https://www.bewaterwise.com/reservoir-water-storage/2.2.4_reservoir_storage.pdf
https://www.mwdh2o.com/management/general-manager/?query=Report

'''
# from colorado.graph_inflow_outflow import InflowOutflowChart
from graphs.graph_reservoirs import ReservoirChart
import wx
from colorado.river_war import RiverWar
from graphs.chart_frame import ChartFrame, NotebookFrame
import colorado.lb as lb
from reservoirs.reservoir import Reservoir, ReservoirGroup
from reservoirs.imperial import Imperial
# from reservoirs.roosevelt import Roosevelt
from reservoirs.srp import SRP
from reservoirs.lake_pleasant import LakePleasant
from reservoirs.mwd import MWD
from reservoirs.aquifers import Aquifers
# Lower Colorado
from reservoirs.lake_havasu import LakeHavasu
from reservoirs.lake_mohave import LakeMohave
from reservoirs.lake_mead import LakeMead
# CRSP
from reservoirs.lake_powell import LakePowell
from reservoirs.flaming_gorge import FlamingGorge
from reservoirs.blue_mesa import BlueMesa
from reservoirs.morrow_point import MorrowPoint
from reservoirs.crystal import Crystal
from reservoirs.navajo import Navajo
# CO Participating
from reservoirs.mcphee import Mcphee
from reservoirs.lake_nighthorse import LakeNighthorse
from reservoirs.ruedi import Ruedi
from reservoirs.taylor_park import TaylorPark
from reservoirs.vallecito import Vallecito
from reservoirs.ridgway import Ridgway
from reservoirs.paonia import Paonia
from reservoirs.lemon import Lemon
from reservoirs.rifle_gap import RifleGap
from reservoirs.crawford import Crawford
from reservoirs.silver_jack import SilverJack

# UT
from reservoirs.starvation import Starvation
from reservoirs.strawberry import Strawberry
from reservoirs.jordanelle import Jordanelle
from reservoirs.joes_valley import JoesValley
from reservoirs.steinaker import Steinaker
from reservoirs.red_fleet import RedFleet
from reservoirs.upper_stillwater import UpperStillwater
from reservoirs.huntington_north import HuntingtonNorth
# WY
from reservoirs.fontenelle import Fontenelle
from reservoirs.big_sandy import BigSandy
from reservoirs.meeks_cabin import MeeksCabin
from reservoirs.stateline import Stateline

# NM
from reservoirs.heron import Heron

# CO
from reservoirs.green_mountain import GreenMountain
from reservoirs.lake_granby import LakeGranby
from reservoirs.horsetooth import Horsetooth
from reservoirs.carter_lake import CarterLake
from reservoirs.dillon import Dillon
from reservoirs.wolford import Wolford
from reservoirs.moon_lake import MoonLake
from reservoirs.groundhog import Groundhog
from reservoirs.shadow_mountain import ShadowMountain
from reservoirs.jackson_gulch import JacksonGulch
from reservoirs.williams_fork import WilliamsFork

# from reservoirs.gross import Gross
# from reservoirs.grand_lake import GrandLake       # Not useful


class ReservoirsReality(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        self.name = 'Reservoir Reality'
        current_size = notebook_frame.GetSize()
        current_size.x = 2048
        notebook_frame.SetSize(current_size)
        reports = ChartFrame.find_directories_with_file('data/USBR_24Month_Reports', 'Lake_Powell.csv')

        # Initial Units
        flaming_gorge = FlamingGorge()
        navajo = Navajo()
        blue_mesa = BlueMesa()
        morrow_point = MorrowPoint()
        crystal = Crystal()
        lake_powell = LakePowell(upstream=[flaming_gorge, blue_mesa, navajo])

        # USBR Lower Basin
        lake_mead = LakeMead(upstream=[lake_powell])
        lake_mohave = LakeMohave(upstream=[lake_mead])
        lake_havasu = LakeHavasu(upstream=[lake_mohave])

        # Lower Basin
        imperial = Imperial(upstream=[lake_havasu])
        lake_pleasant = LakePleasant()
        mwd = MWD()
        # roosevelt = Roosevelt(upstream=[])
        srp = SRP()
        aquifers = Aquifers()

        self.show_upper_basin_reservoirs = True
        if self.show_upper_basin_reservoirs:
            # Participating Units
            # CO
            mcphee = Mcphee()
            lake_nighthorse = LakeNighthorse()
            taylor_park = TaylorPark()
            vallecito = Vallecito()
            ruedi = Ruedi()
            paonia = Paonia()
            ridgeway = Ridgway()
            lemon = Lemon()
            rifle_gap = RifleGap()
            crawford = Crawford()
            silver_jack = SilverJack()

            # WY
            fontenelle = Fontenelle()
            big_sandy = BigSandy()
            meeks_cabin = MeeksCabin()
            state_line = Stateline()

            # UT
            strawberry = Strawberry()
            starvation = Starvation()
            jordanelle = Jordanelle()
            joes_valley = JoesValley()
            steinaker = Steinaker()
            red_fleet = RedFleet()
            huntington_north = HuntingtonNorth()
            upper_stillwater = UpperStillwater()

            # NM
            heron = Heron(upstream=[])

            # Not USBR
            # CO
            dillon = Dillon()
            lake_granby = LakeGranby()
            wolford = Wolford()
            green_mountain = GreenMountain()
            horsetooth = Horsetooth()
            carter_lake = CarterLake()
            groundhog = Groundhog()
            shadow_mountain = ShadowMountain()
            moon_lake = MoonLake()
            jackson_gulch = JacksonGulch()
            williams_fork = WilliamsFork()
            # gross = Gross()
            # Grand is a big 66,000 af natural lake but USBR only tracks a narrow band under 1,000 AF Northern Water uses for pumping
            # so this isnt really good for anything
            # grand_lake = GrandLake(upstream=[])
            self.upper_colorado_states = ReservoirGroup('Upper Colorado',
                                                   [lake_granby, dillon, horsetooth, green_mountain, carter_lake,
                                                    williams_fork,
                                                    wolford, moon_lake, groundhog, shadow_mountain, jackson_gulch],
                                                        legend_position= (0.77, 1.0))
            self.participating = ReservoirGroup('Participating',
                        [strawberry, heron, fontenelle, jordanelle, mcphee,  starvation, vallecito, lake_nighthorse,
                         taylor_park, ruedi, joes_valley, ridgeway, lemon, big_sandy, steinaker, upper_stillwater, meeks_cabin,
                         red_fleet, paonia, state_line, rifle_gap, crawford, silver_jack, huntington_north],
                                                legend_position= (0.77, 1.0))
        else:
            self.upper_colorado_states = ReservoirGroup('Upper Colorado', [])
            self.participating = ReservoirGroup('Participating', [])

        self.lower_colorado_states = ReservoirGroup('Lower Colorado',
                                                    [imperial, aquifers, srp, lake_pleasant, mwd])
        self.lower_colorado_usbr = ReservoirGroup('USBR Lower Colorado',
                                                  [lake_havasu, lake_mohave, lake_mead],
                                                  legend_position= (0.25, 0.80))
        self.crsp_initial_units = ReservoirGroup('CRSP Initial Units',
                                                 [lake_powell, flaming_gorge, navajo, blue_mesa, morrow_point, crystal],
                                                 legend_position= (0.70, 0.80))
        self.reservoirs = [
            imperial, aquifers, srp, lake_pleasant, mwd, lake_havasu, lake_mohave,
            lake_mead, lake_powell, flaming_gorge, navajo, blue_mesa, morrow_point, crystal
        ]
        if self.show_upper_basin_reservoirs:
            reservoir_lists = [self.reservoirs, self.participating.reservoirs, self.upper_colorado_states.reservoirs]
        else:
            reservoir_lists = [self.reservoirs]

        super().__init__(notebook_frame, reservoir_lists=reservoir_lists, reports=reports, page_name=self.name)

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
            (lb.PHX_COLOR, 'Phoenix AMA'),
            (lb.CUT_COLOR, 'Cut to Aquifer')
        ]

        reserved_zones = [
            (lb.AZ_COLOR, 'AZ'),
            (lb.NV_COLOR, 'NV'),
            (lb.CA_COLOR, 'CA')
        ]

        reservoir_chart = ReservoirChart(
            self.reservoirs, start_date=start, current_date=self.current_time_from_usbr, end_date=end, y_max=14.0,
            reservoir_totals=[self.lower_colorado_usbr, self.crsp_initial_units],
            reserved_names=reserved_zones, aquifer_zones=aquifer_zones
        )
        self.charts.append(reservoir_chart)

        if self.show_upper_basin_reservoirs:
            reservoir_chart = ReservoirChart(
                self.participating.reservoirs, start_date=start, current_date=self.current_time_from_usbr, end_date=end, y_max=1.1,
                reservoir_totals = [self.participating],
                percentage = 0.05
            )
            self.charts.append(reservoir_chart)

            reservoir_chart = ReservoirChart(
                self.upper_colorado_states.reservoirs, start_date=start, current_date=self.current_time_from_usbr, end_date=end, y_max=1.1,
                reservoir_totals=[self.upper_colorado_states],
                percentage = 0.05
            )
            self.charts.append(reservoir_chart)

        # inflow_chart = InflowOutflowChart(
        #    self.reservoirs, start_date=start, current_date=current, end_date=end
        # )
        # self.charts.append(inflow_chart)

if __name__ == "__main__":
    app = wx.App(False)

    river_war = RiverWar()
    notebook_frame = NotebookFrame([], river_war)

    ReservoirsReality( notebook_frame=notebook_frame)

    notebook_frame.Show()
    app.MainLoop()