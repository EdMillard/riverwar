"""
Copyright (c) 2022 Ed Millard

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
from source import usbr_report
from graph.water import WaterGraph
from source import usbr_rise
from rw.util import reshape_annual_range, add_annuals, subtract_annual, annual_as_str
import usgs
from rw.state import State
from rw.lake import Lake
from rw.reach import Reach
import usbr
from usbr import az, ca, uc, nv, mx


def initialize(water_year_month=1):
    # SNWA Study losses by reach
    lake_mead_evap = 580000         # Reach 1 Mead at 1100 ft
    # lake_mead_evap = 458000       # Reach 2 Mead at 1045 ft
    lake_mohave_evap = 193000       # Reach 2
    lake_havasu_evap = 138000       # Reach 3
    reach_3_corridor_loss = 191000  # Reach 3

    reach_4_corridor_loss = 365000  # ? Reach 4
    reach_5_corridor_loss = 76000   # ? Reach 5

    reach_losses = [0,
                    lake_mead_evap,
                    lake_mohave_evap,
                    lake_havasu_evap + reach_3_corridor_loss,
                    0,  # Rock
                    0,  # Palo Verde
                    reach_4_corridor_loss,
                    reach_5_corridor_loss]

    powell = usbr.uc.LakePowell(water_year_month)
    mead = usbr.lc.LakeMead(water_year_month)
    mohave = usbr.lc.LakeMohave(water_year_month)
    havasu = usbr.lc.LakeHavasu(water_year_month)
    rock_dam = usbr.lc.RockDam(water_year_month)
    palo_verde_dam = usbr.lc.PaloVerdeDam(water_year_month)
    imperial_dam = usbr.lc.ImperialDam(water_year_month)
    # laguna_dam = Dam('laguna_dam', usbr.lc)
    morelos = usbr.mx.Morelos(water_year_month)

    reaches = [Reach('Reach0', None, powell, water_year_month),
               usbr.lc.Reach1(powell, mead, water_year_month),
               usbr.lc.Reach2(mead, mohave, water_year_month),
               usbr.lc.Reach3(mohave, havasu, water_year_month),
               usbr.lc.Reach3a(havasu, rock_dam, water_year_month),
               usbr.lc.Reach3b(rock_dam, palo_verde_dam, water_year_month),
               usbr.lc.Reach4(palo_verde_dam, imperial_dam, water_year_month),
               usbr.lc.Reach5(imperial_dam, morelos, water_year_month)
               ]
    for reach_number in range(0, len(reaches)):
        reaches[reach_number].loss = reach_losses[reach_number]

    State('Arizona', 'az', az, reaches)
    State('California', 'ca', ca, reaches)
    State('Nevada', 'nv', nv, reaches)
    State('Mexico', 'mx', mx, reaches)
    return reaches


def model(reaches, year_begin, year_end):
    for reach in reaches:
        reach.model(year_begin, year_end)

    for i in range(1, len(reaches)):
        active_users_through_reach = 0
        for j in range(i, len(reaches)):
            reach = reaches[j]
            users_by_state = reach.users_in_reach_by_state()
            for state in users_by_state:
                try:
                    reaches[i].active_users_through_reach[state]
                except KeyError:
                    reaches[i].active_users_through_reach[state] = []
                reaches[i].active_users_through_reach[state].extend(users_by_state[state])
            active_users_through_reach += len(reaches[j].active_users_in_reach)

    total = 0
    for i in range(1, len(reaches)):
        reach = reaches[i]
        print('\t' + reach.name + '\t',
              # annual_as_str(reach.loss_evaporation), '+',
              # annual_as_str(reach.loss_corridor), '=',
              reach.loss)
        total += reach.loss
    print('total loss: ', total)

    for i in range(1, len(reaches)):
        reach = reaches[i]
        reach.print_model()

    for i in range(1, len(reaches)):
        reach = reaches[i]
        reach.print_users()

    print()


def test():
    lake_mead()
    lake_mead_ics_by_state()
    lake_mohave()
    lake_havasu()


class Reach1(Reach):
    def __init__(self, upper_lake, lower_lake, water_month):
        Reach.__init__(self, 'Reach1', upper_lake, lower_lake, water_month)

    def model(self, year_begin, year_end):
        if year_begin < 1991:
            print('Reach 1 model only works from 1991-Present, Colorado Gage above Diamond Creek record limited')
        Reach.model(self, year_begin, year_end)


class Reach2(Reach):
    def __init__(self, upper_lake, lower_lake, water_month):
        Reach.__init__(self, 'Reach2', upper_lake, lower_lake, water_month)


class Reach3(Reach):
    def __init__(self, upper_lake, lower_lake, water_month):
        Reach.__init__(self, 'Reach3', upper_lake, lower_lake, water_month)


class Reach3a(Reach):
    def __init__(self, upper_lake, lower_lake, water_month):
        Reach.__init__(self, 'Reach3a', upper_lake, lower_lake, water_month)


class Reach3b(Reach):
    def __init__(self, upper_lake, lower_lake, water_month):
        Reach.__init__(self, 'Reach3b', upper_lake, lower_lake, water_month)


class Reach4(Reach):
    def __init__(self, upper_lake, lower_lake, water_month):
        Reach.__init__(self, 'Reach4', upper_lake, lower_lake, water_month)


class Reach5(Reach):
    def __init__(self, upper_lake, lower_lake, water_month):
        Reach.__init__(self, 'Reach5', upper_lake, lower_lake, water_month)


def lake_mead_load_ics():
    results = usbr_report.load_ics_csv('usbr_lake_mead_ics.csv', sep='\t')
    return results


def lake_mead_ics_by_state():
    ics = lake_mead_load_ics()
    ics_az_total = ics['AZ Total']
    ics_ca_total = ics['CA Total']
    ics_nv_total = ics['NV Total']

    bar_data = [{'data': ics_nv_total, 'label': 'NV ICS', 'color': 'maroon'},
                {'data': ics_az_total, 'label': 'AZ ICS', 'color': 'firebrick'},
                {'data': ics_ca_total, 'label': 'CA ICS', 'color': 'lightcoral'}
                ]
    graph = WaterGraph()
    graph.bars_stacked(bar_data, title='Lower Basin ICS By State',
                       ylabel='maf', ymin=0, ymax=3000000, yinterval=100000,
                       xlabel='Calendar Year', xinterval=1, format_func=WaterGraph.format_maf)
    graph.date_and_wait()


class LakeMead(Lake):
    def __init__(self, water_month):
        Lake.__init__(self, 'lake_mead', water_month)

    def inflow(self, year_begin, year_end):
        colorado_above_diamond_creek = usgs.az.colorado_above_diamond_creek_near_peach_springs(graph=False)
        colorado_above_diamond_creek_annual_af = colorado_above_diamond_creek.annual_af(year_begin, year_end)
        virgin_river = usgs.ut.virgin_river_at_virgin(graph=False)
        virgin_river_annual_af = virgin_river.annual_af(year_begin, year_end)

        # virgin_river_overton = usgs.nv.virgin_abv_lake_mead_nr_overton(graph=False)
        # virgin_river_overton_annual_af = virgin_river_overton.annual_af(year_begin, year_end)
        # virgin_diff = subtract_annual(virgin_river_annual_af, virgin_river_overton_annual_af)

        muddy_river_annual_af = usgs.nv.muddy_near_glendale(graph=False).annual_af(year_begin, year_end)

        inflow = add_annuals([colorado_above_diamond_creek_annual_af, virgin_river_annual_af, muddy_river_annual_af])
        return inflow

    # def side_inflow(self, year_begin, year_end):
    #    annual_af = usbr_report.annual_af('usbr_lake_mead_side_inflow.csv', multiplier=1000, path='data/USBR_24_Month')
    #    return reshape_annual_range(annual_af, year_begin, year_end)
    #
    def release(self, year_begin, year_end):
        return lake_mead_release(year_begin, year_end, water_year_month=self.water_year_month)

    def storage(self):
        usbr_lake_mead_storage_af = 6124
        info, daily_storage_af = usbr_rise.load(usbr_lake_mead_storage_af)
        return daily_storage_af

    def evaporation(self, year_begin, year_end):
        annual_af = usbr_report.annual_af('usbr_lake_mead_evap_losses.csv', multiplier=1000, path='data/USBR_24_Month')
        return reshape_annual_range(annual_af, year_begin, year_end)


def lake_mead_release(year_begin, year_end, water_year_month):
    annual_af = usbr_report.annual_af('releases/usbr_releases_hoover_dam.csv', water_year_month=water_year_month)
    ar_release = reshape_annual_range(annual_af, year_begin, year_end)

    usbr_lake_mead_release_total_af = 6122
    info, daily_release_af = usbr_rise.load(usbr_lake_mead_release_total_af)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af, water_year_month=water_year_month)
    rise_release = reshape_annual_range(annual_release_af, year_begin, year_end)
    diff = subtract_annual(ar_release, rise_release)
    print('ar vs rise lake mead release', annual_as_str(diff))
    return ar_release


def lake_mead_storage():
    usbr_lake_mead_storage_af = 6124
    info, daily_storage_af = usbr_rise.load(usbr_lake_mead_storage_af)
    return daily_storage_af


def lake_mead(graph=True):
    usbr_lake_mead_release_total_af = 6122
    # usbr_lake_mead_elevation_ft = 6123
    usbr_lake_mead_storage_af = 6124
    # usbr_lake_mead_release_total_cfs = 6125
    # info, daily_elevation_ft = usbr_rise.load(usbr_lake_mead_elevation_ft)
    # graph.plot(daily_elevation_ft, sub_plot=0, title='Lake Mead Elevation', color='firebrick',
    #            ylabel='ft', ymin=900, ymax=1230, yinterval=20,
    #            format_func=WaterGraph.format_elevation)

    if graph:
        graph = WaterGraph(nrows=2)
        info, daily_storage_af = usbr_rise.load(usbr_lake_mead_storage_af)
        graph.plot(daily_storage_af, sub_plot=0, title='Lake Mead Storage (Hoover Dam)', color='firebrick',
                   ymax=32000000, yinterval=2000000,
                   ylabel='maf', format_func=WaterGraph.format_10maf)
        # usbr.lake_mead.ics_by_state(graph)

    info, daily_release_af = usbr_rise.load(usbr_lake_mead_release_total_af)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    if graph:
        graph.bars(annual_release_af, sub_plot=1, title='Lake Mead Release (Hoover Dam)', color='firebrick',
                   ymin=3000000, ymax=22500000, yinterval=1000000,
                   xlabel='Water Year', xinterval=5,
                   ylabel='maf', format_func=WaterGraph.format_maf)
        graph.date_and_wait()
    return annual_release_af


class LakeMohave(Lake):
    def __init__(self, water_month):
        Lake.__init__(self, 'lake_mohave', water_month)

    def inflow(self, year_begin, year_end):
        return lake_mead_release(year_begin, year_end, self.water_year_month)

    def side_inflow(self, year_begin, year_end):
        annual_af = usbr_report.annual_af('usbr_lake_mohave_side_inflow.csv',
                                          multiplier=1000, path='data/USBR_24_Month')
        return reshape_annual_range(annual_af, year_begin, year_end)

    def release(self, year_begin, year_end):
        return lake_mohave_release(year_begin, year_end, water_year_month=self.water_year_month)

    def storage(self):
        usbr_lake_mohave_storage_af = 6134
        info, daily_storage_af = usbr_rise.load(usbr_lake_mohave_storage_af)
        return daily_storage_af

    def evaporation(self, year_begin, year_end):
        annual_af = usbr_report.annual_af('usbr_lake_mohave_evap_losses.csv',
                                          multiplier=1000, path='data/USBR_24_Month')
        return reshape_annual_range(annual_af, year_begin, year_end)


def lake_mohave_release(year_begin, year_end, water_year_month):
    annual_af = usbr_report.annual_af('releases/usbr_releases_davis_dam.csv', water_year_month=water_year_month)
    ar_release = reshape_annual_range(annual_af, year_begin, year_end)

    usbr_lake_mohave_release_total_af = 6131
    info, daily_release_af = usbr_rise.load(usbr_lake_mohave_release_total_af)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af, water_year_month=water_year_month)
    rise_release = reshape_annual_range(annual_release_af, year_begin, year_end)

    diff = subtract_annual(ar_release, rise_release)
    print('ar vs rise lake mohave release', annual_as_str(diff))
    return ar_release


def lake_mohave(graph=False):
    usbr_lake_mohave_release_total_af = 6131
    # usbr_lake_mohave_water_temperature_degf = 6132
    # usbr_lake_mohave_elevation_ft = 6133
    usbr_lake_mohave_storage_af = 6134
    # usbr_lake_mohave_release_total_cfs = 6135

    if graph:
        graph = WaterGraph(nrows=2)
        # info, daily_elevation_ft = usbr_rise.load(usbr_lake_mohave_elevation_ft)
        # graph.plot(daily_elevation_ft, sub_plot=0, title='Lake Mohave Elevation', color='firebrick',
        #            ymin=620, ymax=647, yinterval=2,
        #            ylabel='ft', format_func=WaterGraph.format_elevation)
        info, daily_storage_af = usbr_rise.load(usbr_lake_mohave_storage_af)
        graph.plot(daily_storage_af, sub_plot=0, title='Lake Mohave Storage (Davis Dam)', color='firebrick',
                   ymin=1000000, ymax=1900000, yinterval=100000,
                   ylabel='maf', format_func=WaterGraph.format_maf)

    info, daily_release_af = usbr_rise.load(usbr_lake_mohave_release_total_af)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    if graph:
        graph.bars(annual_release_af, sub_plot=1, title='Lake Mohave Release (Davis Dam)', color='firebrick',
                   ymin=6500000, ymax=23000000, yinterval=1000000,
                   xlabel='Water Year', xinterval=4,
                   ylabel='maf', format_func=WaterGraph.format_maf)
        graph.date_and_wait()
    return annual_release_af


def lake_havasu_release(year_begin, year_end, water_year_month):
    annual_af = usbr_report.annual_af('releases/usbr_releases_parker_dam.csv', water_year_month=water_year_month)
    ar_release = reshape_annual_range(annual_af, year_begin, year_end)

    usbr_lake_havasu_release_total_af = 6126
    info, daily_release_af = usbr_rise.load(usbr_lake_havasu_release_total_af)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af, water_year_month=water_year_month)
    rise_release = reshape_annual_range(annual_release_af, year_begin, year_end)

    diff = subtract_annual(ar_release, rise_release)
    print('ar vs rise lake havasu release', annual_as_str(diff))
    return ar_release


class LakeHavasu(Lake):
    def __init__(self, water_month):
        Lake.__init__(self, 'lake_havasu', water_month)

    def inflow(self, year_begin, year_end):
        return lake_mohave_release(year_begin, year_end, self.water_year_month)

    def side_inflow(self, year_begin, year_end):
        annual_af = usbr_report.annual_af('usbr_lake_havasu_side_inflow.csv',
                                          multiplier=1000, path='data/USBR_24_Month')
        return reshape_annual_range(annual_af, year_begin, year_end)

    def release(self, year_begin, year_end):
        return lake_havasu_release(year_begin, year_end, water_year_month=self.water_year_month)

    def storage(self):
        usbr_lake_havasu_storage_af = 6129
        info, daily_storage_af = usbr_rise.load(usbr_lake_havasu_storage_af)
        return daily_storage_af

    def evaporation(self, year_begin, year_end):
        annual_af = usbr_report.annual_af('usbr_lake_havasu_evap_losses.csv', multiplier=1000,
                                          path='data/USBR_24_Month')
        return reshape_annual_range(annual_af, year_begin, year_end)


def lake_havasu(graph=True):
    usbr_lake_havasu_release_total_af = 6126
    # usbr_lake_havasu_water_temperature_degf = 6127
    # usbr_lake_havasu_elevation_ft = 6128
    usbr_lake_havasu_storage_af = 6129
    # usbr_lake_havasu_release_total_cfs = 6130

    if graph:
        graph = WaterGraph(nrows=2)
        # info, daily_elevation_ft = usbr_rise.load(usbr_lake_havasu_elevation_ft)
        # graph.plot(daily_elevation_ft, sub_plot=0, title='Lake Havasu Elevation', color='firebrick',
        #            ymin=440, ymax=451, yinterval=1,
        #            ylabel='ft', format_func=WaterGraph.format_elevation)

        info, daily_storage_af = usbr_rise.load(usbr_lake_havasu_storage_af)
        graph.plot(daily_storage_af, sub_plot=0, title='Lake Havasu Storage (Parker Dam)', color='firebrick',
                   ymax=700000, yinterval=50000,
                   ylabel='kaf', format_func=WaterGraph.format_kaf)

    info, daily_release_af = usbr_rise.load(usbr_lake_havasu_release_total_af)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    if graph:
        graph.bars(annual_release_af, sub_plot=1, title='Lake Havasu Release (Parker Dam)', color='firebrick',
                   ymin=4000000, ymax=19200000, yinterval=1000000,
                   xlabel='Water Year', xinterval=4,
                   ylabel='maf',  format_func=WaterGraph.format_maf)
        graph.fig.waitforbuttonpress()
    return annual_release_af


def parker_dam_release(water_year_month):
    rock_release = usbr_report.annual_af('releases/usbr_releases_parker.csv', water_year_month=water_year_month)
    return rock_release


class RockDam(Lake):
    def __init__(self, water_month):
        Lake.__init__(self, 'rock_dam', water_month)

    def inflow(self, year_begin, year_end):
        return lake_havasu_release(year_begin, year_end, self.water_year_month)

    def bypass(self, year_begin, year_end):
        return rock_dam_bypass(year_begin, year_end, self.water_year_month)

    def release(self, year_begin, year_end):
        return rock_dam_release(year_begin, year_end, self.water_year_month)


def rock_dam_release(year_begin, year_end, water_year_month):
    annual_af = usbr_report.annual_af('releases/usbr_releases_rock_dam.csv', water_year_month=water_year_month)
    return reshape_annual_range(annual_af, year_begin, year_end)


def rock_dam_bypass(year_begin, year_end,  *_):
    az_crit = reshape_annual_range(usbr.az.crit_returns(), year_begin, year_end)
    ca_crit = reshape_annual_range(usbr.ca.crit_returns(), year_begin, year_end)
    return add_annuals([az_crit, ca_crit])


class PaloVerdeDam(Lake):
    def __init__(self, water_month):
        Lake.__init__(self, 'palo_verde_dam', water_month)

    def inflow(self, year_begin, year_end):
        rock_release = rock_dam_release(year_begin, year_end, self.water_year_month)
        rock_bypass = rock_dam_bypass(year_begin, year_end, self.water_year_month)
        return add_annuals([rock_release, rock_bypass])

    def bypass(self, year_begin, year_end):
        return palo_verde_dam_bypass(year_begin, year_end, self.water_year_month)

    def release(self, year_begin, year_end):
        return palo_verde_dam_release(year_begin, year_end, self.water_year_month)


def palo_verde_dam_release(year_begin, year_end, water_year_month):
    annual_af = usbr_report.annual_af('releases/usbr_releases_palo_verde_dam.csv', water_year_month=water_year_month)
    return reshape_annual_range(annual_af, year_begin, year_end)


def palo_verde_dam_bypass(year_begin, year_end, water_year_month):
    return reshape_annual_range(usbr.ca.palo_verde_returns(water_year_month=water_year_month), year_begin, year_end)


class ImperialDam(Lake):
    def __init__(self, water_month):
        Lake.__init__(self, 'imperial_dam', water_month)

    def inflow(self, year_begin, year_end):
        release = palo_verde_dam_release(year_begin, year_end, self.water_year_month)
        bypass = palo_verde_dam_bypass(year_begin, year_end, self.water_year_month)
        return add_annuals([release, bypass])

    def release(self, year_begin, year_end):
        imperial_release = usbr_report.annual_af('releases/usbr_releases_imperial_dam.csv',
                                                 water_year_month=self.water_year_month)
        return reshape_annual_range(imperial_release, year_begin, year_end)

    def bypass(self, year_begin, year_end):
        imperial_returns = usbr.ca.imperial_returns(self.water_year_month)
        imperial_returns = reshape_annual_range(imperial_returns, year_begin, year_end)

        coachella_returns = usbr.ca.coachella_returns(self.water_year_month)
        coachella_returns = reshape_annual_range(coachella_returns, year_begin, year_end)

        yuma_project_returns = usbr.ca.yuma_project_returns(self.water_year_month)
        yuma_project_returns = reshape_annual_range(yuma_project_returns, year_begin, year_end)

        below_yuma_wasteway_gage = usgs.lc.below_yuma_wasteway(graph=False)
        below_yuma_wasteway_returns = below_yuma_wasteway_gage.annual_af(water_year_month=self.water_year_month,
                                                                         start_year=year_begin, end_year=year_end)

        pilot_knob_gage = usgs.ca.pilot_knob_powerplant_and_wasteway(graph=False)
        pilot_knob = pilot_knob_gage.annual_af(water_year_month=self.water_year_month,
                                               start_year=year_begin, end_year=year_end)

        return add_annuals([imperial_returns,
                            coachella_returns,
                            yuma_project_returns,
                            below_yuma_wasteway_returns,
                            pilot_knob])

    def storage(self):
        pass

    def evaporation(self, year_begin, year_end):
        pass


def laguna_dam_release():
    laguna_release = usbr_report.annual_af('releases/usbr_releases_laguna_dam.csv')
    return laguna_release
