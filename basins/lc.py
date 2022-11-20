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
from os import chdir
from source import usbr_report
from graph.water import WaterGraph
from matplotlib import pyplot

from source import usbr_rise
from rw.util import reshape_annual_range, add_annuals
import usgs
from usgs import az, ca, nv, ut, lc
from rw.lake import Lake
from rw.util import number_as_str, af_as_str, right_justified, left_justified
from rw.reach import Reach
from rw.state import state_by_abbreviation
from rw.options import Options
import states
from states import az, ca, nv, mx
from states.ca import California
from states.az import Arizona
from states.nv import Nevada
from states.mx import Mexico
from basins import uc


class Model(object):
    def __init__(self, name):
        self.name = name
        self.states = None
        self.reaches = None
        self.reach_losses = None
        self.options = Options()

    def initialize(self, water_year_month=1):
        # SNWA Study losses by reach
        if self.options.grand_canyon_inflow_cancels_mead_evap:
            lake_mead_evap = 0          # Reach 1 grand canyon side inflows cancel Lake Mead evap
        else:
            lake_mead_evap = 580000     # Reach 1 Mead at 1100 ft
        # lake_mead_evap = 458000       # Reach 2 Mead at 1045 ft
        lake_mohave_evap = 193000       # Reach 2
        lake_havasu_evap = 138000       # Reach 3
        reach_3_corridor_loss = 191000  # Reach 3
        if self.options.havasu_evap_charge_to_havasu_users is True:
            reach_3_loss = reach_3_corridor_loss
        else:
            reach_3_loss = reach_3_corridor_loss + lake_havasu_evap

        reach_4_corridor_loss = 365000  # ? Reach 4
        reach_5_corridor_loss = 76000   # ? Reach 5
        self.reach_losses = [0,
                             lake_mead_evap,
                             lake_mohave_evap,
                             reach_3_loss,
                             # 0,  # Rock
                             # 0,  # Palo Verde
                             reach_4_corridor_loss,
                             reach_5_corridor_loss]

        powell = uc.LakePowell(water_year_month)
        mead = LakeMead(water_year_month)
        mohave = LakeMohave(water_year_month)
        havasu = LakeHavasu(water_year_month)
        # rock_dam = basins.lc.RockDam(water_year_month)
        # palo_verde_dam = basins.lc.PaloVerdeDam(water_year_month)
        imperial_dam = ImperialDam(water_year_month)
        # laguna_dam = Dam('laguna_dam', usbr.lc)
        morelos = states.mx.Morelos(water_year_month)
        self.reaches = [Reach('Reach0', None, powell, water_year_month),
                        Reach1(powell, mead, water_year_month),
                        Reach2(mead, mohave, water_year_month),
                        Reach3(mohave, havasu, water_year_month),
                        # basins.lc.Reach3a(havasu, rock_dam, water_year_month),
                        # basins.lc.Reach3b(rock_dam, palo_verde_dam, water_year_month),
                        Reach4(havasu, imperial_dam, water_year_month),
                        Reach5(imperial_dam, morelos, water_year_month)
                        ]
        for reach_number in range(0, len(self.reaches)):
            self.reaches[reach_number].loss = self.reach_losses[reach_number]

        self.states = [Arizona(az, self.reaches, self.options),
                       California(ca, self.reaches, self.options),
                       Nevada(nv, self.reaches, self.options),
                       Mexico(mx, self.reaches, self.options)]

    def run(self, year_begin, year_end):
        for state in self.states:
            state.loss_assessment = 0
            state.other_user_loss_assessments = 0

        for reach in self.reaches:
            for user in reach.users:
                user.assessment = 0
            reach.model(year_begin, year_end)

        model_active_users_through_reach(self.reaches)

        for i in range(1, len(self.reaches)):
            self.reaches[i].compute_through_reach_cu_avg()

        for i in range(1, len(self.reaches)):
            self.reaches[i].compute_state_assessment()

        if self.options.havasu_evap_charge_to_havasu_users is True:
            reach = self.reaches[3]
            user_cap = None
            state_az = None
            user_met = None
            state_ca = None
            for state_code in ['az', 'ca']:
                state = state_by_abbreviation(state_code)
                if state_code == 'az':
                    user_cap = state.user_for_name('cap')
                    state_az = state
                elif state_code == 'ca':
                    user_met = state.user_for_name('metropolitan')
                    state_ca = state

            if user_cap and user_met:
                lake_havasu_evap = 138000  # Reach 3
                reach.loss += lake_havasu_evap

                user_total_cu = user_cap.avg_cu() + user_met.avg_cu()

                user_cap_percent = user_cap.avg_cu() / user_total_cu
                cap_lake_evap_assessment = lake_havasu_evap * user_cap_percent
                user_cap.assessment += cap_lake_evap_assessment
                state_az.loss_assessment += cap_lake_evap_assessment
                state_dictionary = reach.state_assessment[state_az.abbreviation]
                state_dictionary['lake_evap'] = [('cap', cap_lake_evap_assessment)]

                user_met_percent = user_met.avg_cu() / user_total_cu
                met_lake_evap_assessment = lake_havasu_evap * user_met_percent
                user_met.assessment += met_lake_evap_assessment
                state_ca.loss_assessment += met_lake_evap_assessment
                state_dictionary = reach.state_assessment[state_ca.abbreviation]
                state_dictionary['lake_evap'] = [('metropolitan', met_lake_evap_assessment)]

    def summary(self):
        print('Summary of Assessments by State')
        state_summary_list = []
        total_state_assessments = 0
        for state in self.states:
            state.other_user_assessments = 0
            print(state.abbreviation + '   ' + af_as_str(state.loss_assessment))
            state_summary_list.append((state.abbreviation, state.loss_assessment))
            total_state_assessments += state.loss_assessment
        print('Total' + af_as_str(total_state_assessments))

        print('\nSummary of Water User Assessments')
        print('Major Water Users')
        major_user_list = []
        total_assessment = 0
        for i in range(1, len(self.reaches)):
            reach = self.reaches[i]
            if not reach_has_example_user(reach):
                continue
            users_in_reach_by_state = reach.users_in_reach_by_state()
            for state_code in reach.states:
                state = state_by_abbreviation(state_code)
                users_in_state = users_in_reach_by_state.get(state_code)
                if users_in_state:
                    for user in users_in_state:
                        if user.example:
                            print(str(i), state_code, left_justified(user.name, 20), af_as_str(user.assessment))
                            total_assessment += user.assessment
                            major_user_list.append((i, state_code, user.name, user.assessment))
                        else:
                            state.other_user_assessments += user.assessment
        print("Subtotal: ", right_justified(af_as_str(total_assessment), 27))

        print('\nRemaining Water Users')
        other_user_list = []
        other_sub_total = 0
        for state in self.states:
            if state.other_user_assessments != 0:
                print('   ', left_justified(state.abbreviation, 21), af_as_str(state.other_user_assessments))
                other_sub_total += state.other_user_assessments
                other_user_list.append((state.abbreviation, state.other_user_assessments))
        print("Subtotal: ", right_justified(af_as_str(other_sub_total), 27))
        print("Total:    ", right_justified(af_as_str(total_assessment + other_sub_total), 27))

        return state_summary_list, major_user_list, other_user_list

    def print(self):
        print_loss_table(self.reaches)

        # for i in range(1, len(reaches)):
        #     self.reaches[i].print_model()

        for i in range(1, len(self.reaches)):
            self.reaches[i].print_state_assessments()

        print_users(self.reaches)
        return self.summary()

    def state_by_name(self, name):
        for state in self.states:
            if state.name == name:
                return state
        return None


def reach_has_example_user(reach):
    users_in_reach_by_state = reach.users_in_reach_by_state()
    for state in reach.states:
        users_in_state = users_in_reach_by_state.get(state)
        if users_in_state is None:
            users_in_state = []
        for user in users_in_state:
            if user.example:
                return True
    return False


def print_users(reaches):
    print()
    for i in range(1, len(reaches)):
        reach = reaches[i]
        if not reach_has_example_user(reach):
            continue
        # print(reach.name + ' ' + af_as_str(reach.loss))
        print('        | Reach Loss |  State  |  State CU |  Reach CU | State Assessment |' +
              right_justified('User Name', 33) + ' | User CU  | Factor | Assessment | Lake Evap Assessment')
        # For state assessment need:
        #   state_through_reach_cu_avg
        #   reach.through_reach_cu_avg
        #   state_assessment
        # For user assessment
        #   3 yr avg user annual cu
        #   factor = user avg cu / state avg cu
        #   annual assessment = 3 yr avg user annual cu * factor
        users_in_reach_by_state = reach.users_in_reach_by_state()
        active_users_in_reach = 0
        for state in reach.states:
            users_in_state = users_in_reach_by_state.get(state)
            if users_in_state is None:
                users_in_state = []
            # print('\t'+state+'   ', number_as_str(len(users_in_state)))
            active_users_in_reach += len(users_in_state)

            for user in users_in_state:
                if user.example:
                    user_str = reach.user_as_str(user)
                    total_assessment = 0
                    for n in range(1, i+1):
                        state_assessment_reach = reaches[n]
                        s, num_users = state_assessment_reach.state_assessment_as_str(state,
                                                                                      print_num_users=False,
                                                                                      print_percent=False,
                                                                                      print_reach_cu=True)
                        state_dictionary = state_assessment_reach.state_assessment[state]
                        state_cu_avg = state_dictionary['cu_avg']
                        factor = user.avg_cu() / state_cu_avg
                        state_assessment = state_dictionary['assessment']
                        user_reach_assessment = state_assessment * factor

                        lake_evap_assessment_list = state_dictionary.get('lake_evap')
                        lake_evap_str = ''
                        if lake_evap_assessment_list:
                            for lake_evap_assessment in lake_evap_assessment_list:
                                user_name, lake_evap_assessment = lake_evap_assessment
                                if user_name == user.name:
                                    lake_evap_str = af_as_str(lake_evap_assessment, plus_minus=True)
                                    total_assessment += lake_evap_assessment

                        print(state_assessment_reach.name + ' ' + number_as_str(state_assessment_reach.loss) + ' ' + s +
                              ' ' + user_str + '  ' + "{:6.4f}".format(user.factor) + af_as_str(user_reach_assessment),
                              lake_evap_str)
                        total_assessment += user_reach_assessment
                    if user.assessment != total_assessment:
                        print(user.name, 'total by reach assessment doesn\'t match user assessment',
                              total_assessment, user.assessment)
                    print('{0: >140}'.format('Total' + af_as_str(total_assessment)))
        # print('\tTotal', number_as_str(active_users_in_reach))


def print_loss_table(reaches):
    print('\nReach Assessments (from CRSS via SNWA)')
    total = 0
    for i in range(1, len(reaches)):
        reach = reaches[i]
        print('\t' + reach.name + right_justified(reach.upper_lake.name, 15) +
              right_justified(reach.lower_lake.name, 15) +
              af_as_str(reach.loss))
        total += reach.loss
    print(right_justified('total:', 39), af_as_str(total))


def model_active_users_through_reach(reaches):
    for i in range(1, len(reaches)):
        for j in range(i, len(reaches)):
            reach = reaches[j]
            users_by_state = reach.users_in_reach_by_state()
            for state in users_by_state:
                try:
                    reaches[i].active_users_through_reach[state]
                except KeyError:
                    reaches[i].active_users_through_reach[state] = []
                reaches[i].active_users_through_reach[state].extend(users_by_state[state])


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


def model_run_summaries(runs, run_summaries):
    primary_state_summary_list, primary_major_user_list, primary_other_user_list = run_summaries[0]

    # State Summary
    print('\nSummary of Assessments by State (af/year)')
    header = '    SNWA    ' + '   Havasu   ' + 'No Mead Evap' + ' Yuma to R4 '
    print('          ' + header)
    state_totals = [0] * runs
    for primary_state_summary in primary_state_summary_list:
        primary_state_code, primary_state_assessment = primary_state_summary
        s = '  ' + primary_state_code + '   ' + af_as_str(primary_state_assessment)
        state_totals[0] += primary_state_assessment
        for run in range(1, runs):
            state_summary_list, b, c = run_summaries[run]
            for state_summary in state_summary_list:
                state_code, state_assessment = state_summary
                if state_code == primary_state_code:
                    s += af_as_str(state_assessment)
                    state_totals[run] += state_assessment
                    break
        print(s)
    s = 'Total: '
    for subtotal in state_totals:
        s += af_as_str(subtotal)
    print(s)

    # Major User Summary
    print('\nSummary of Waster User Assessments (af/year)')
    print('                            ' + header)
    major_user_subtotals = [0] * runs
    for primary_user_summary in primary_major_user_list:
        primary_reach, primary_state, primary_user_name, primary_assessment = primary_user_summary
        s = str(primary_reach) + ' ' + primary_state + ' ' + left_justified(primary_user_name, 20)
        s += af_as_str(primary_assessment)
        major_user_subtotals[0] += primary_assessment
        for run in range(1, runs):
            a, major_user_list, c = run_summaries[run]
            for user_summary in major_user_list:
                reach, state, user_name, assessment = user_summary
                if user_name == primary_user_name:
                    s += af_as_str(assessment)
                    major_user_subtotals[run] += assessment
                    break
        print(s)
    s = right_justified('Subtotal: ', 25)
    for subtotal in major_user_subtotals:
        s += af_as_str(subtotal)
    print(s)

    # Other User Summary
    state_subtotals = [0] * runs
    for primary_other_user in primary_other_user_list:
        primary_state_code, primary_state_assessment = primary_other_user
        s = '  ' + primary_state_code + ' remaining users     ' + af_as_str(primary_state_assessment)
        state_subtotals[0] += primary_state_assessment
        for run in range(1, runs):
            a, b, other_user_list = run_summaries[run]
            for state_summary in other_user_list:
                state_code, state_assessment = state_summary
                if state_code == primary_state_code:
                    s += af_as_str(state_assessment)
                    state_subtotals[run] += state_assessment
                    break
        print(s)
    s = '               Subtotal: '
    for subtotal in state_subtotals:
        s += af_as_str(subtotal)
    print(s)

    s = '                  Total: '
    for run in range(0, runs):
        total = major_user_subtotals[run] + state_subtotals[run]
        s += af_as_str(total)
    print(s)

    print("\nScenario Guide:")
    for run in range(0, runs):
        if run == 0:
            print('SNWA         - Original SNWA Loss Study')
        elif run == 1:
            print('Havasu       - plus Lake Havasu evaporation losses charged to CAP and Metropolitan, their lake :)')
        elif run == 2:
            print('No Mead Evap - plus Grand Canyon inflows cancel Lake Mead evaporation losses')
        elif run == 3:
            print('Yuma         - plus Most Yuma Users moved from Reach 5 to Reach 4 where their diversions are')
        elif run == 4:
            print("CRIT         - Move CRIT to Reach 3a")
        elif run == 5:
            print("Palo Verde   - Move Palo Verde to Reach 3b")
    print()


def test():
    lake_mead()
    lake_mead_ics_by_state()
    lake_mohave()
    lake_havasu()


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

    # usbr_lake_mead_release_total_af = 6122
    # info, daily_release_af = usbr_rise.load(usbr_lake_mead_release_total_af)
    # annual_release_af = WaterGraph.daily_to_water_year(daily_release_af, water_year_month=water_year_month)
    # rise_release = reshape_annual_range(annual_release_af, year_begin, year_end)
    # diff = subtract_annual(ar_release, rise_release)
    # print('ar vs rise lake mead release', annual_as_str(diff))
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

    # usbr_lake_mohave_release_total_af = 6131
    # info, daily_release_af = usbr_rise.load(usbr_lake_mohave_release_total_af)
    # annual_release_af = WaterGraph.daily_to_water_year(daily_release_af, water_year_month=water_year_month)
    # rise_release = reshape_annual_range(annual_release_af, year_begin, year_end)

    # diff = subtract_annual(ar_release, rise_release)
    # print('ar vs rise lake mohave release', annual_as_str(diff))
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

    # usbr_lake_havasu_release_total_af = 6126
    # info, daily_release_af = usbr_rise.load(usbr_lake_havasu_release_total_af)
    # annual_release_af = WaterGraph.daily_to_water_year(daily_release_af, water_year_month=water_year_month)
    # rise_release = reshape_annual_range(annual_release_af, year_begin, year_end)

    # diff = subtract_annual(ar_release, rise_release)
    # print('ar vs rise lake havasu release', annual_as_str(diff))
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
    az_crit = reshape_annual_range(states.az.crit_returns(), year_begin, year_end)
    ca_crit = reshape_annual_range(states.ca.crit_returns(), year_begin, year_end)
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
    return reshape_annual_range(states.ca.palo_verde_returns(water_year_month=water_year_month), year_begin, year_end)


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
        imperial_returns = states.ca.imperial_returns(self.water_year_month)
        imperial_returns = reshape_annual_range(imperial_returns, year_begin, year_end)

        coachella_returns = states.ca.coachella_returns(self.water_year_month)
        coachella_returns = reshape_annual_range(coachella_returns, year_begin, year_end)

        yuma_project_returns = states.ca.yuma_project_returns(self.water_year_month)
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


if __name__ == '__main__':
    pyplot.switch_backend('Agg')  # FIXME must be accessing pyplt somewhere
    chdir('../')
