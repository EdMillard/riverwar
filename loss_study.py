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
from rw.util import number_as_str, af_as_str, right_justified, left_justified
from usgs import az, ca, nv
from rw.reach import Reach
from rw.state import State, state_by_abbreviation
import states
from states import az, ca, nv, mx
import basins
from basins import lc, uc
from matplotlib import pyplot


class Model(object):
    def __init__(self, name):
        self.name = name
        self.states = None
        self.reaches = None
        self.reach_losses = None
        self.reset_options()
        self.option_yuma_users_moved_to_reach_4 = False
        self.option_havasu_evap_charge_to_havasu_users = False
        self.option_grand_canyon_inflow_cancels_mead_evap = False
        self.option_crit_in_reach_3a = False
        self.option_palo_verde_in_reach_3b = False

    def reset_options(self):
        self.option_yuma_users_moved_to_reach_4 = False
        self.option_havasu_evap_charge_to_havasu_users = False
        self.option_grand_canyon_inflow_cancels_mead_evap = False
        self.option_crit_in_reach_3a = False
        self.option_palo_verde_in_reach_3b = False

    def initialize(self, water_year_month=1):
        # SNWA Study losses by reach
        if self.option_grand_canyon_inflow_cancels_mead_evap:
            lake_mead_evap = 0          # Reach 1 grand canyon side inflows cancel Lake Mead evap
        else:
            lake_mead_evap = 580000     # Reach 1 Mead at 1100 ft
        # lake_mead_evap = 458000       # Reach 2 Mead at 1045 ft
        lake_mohave_evap = 193000       # Reach 2
        lake_havasu_evap = 138000       # Reach 3
        reach_3_corridor_loss = 191000  # Reach 3
        if self.option_havasu_evap_charge_to_havasu_users is True:
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

        powell = basins.uc.LakePowell(water_year_month)
        mead = basins.lc.LakeMead(water_year_month)
        mohave = basins.lc.LakeMohave(water_year_month)
        havasu = basins.lc.LakeHavasu(water_year_month)
        # rock_dam = basins.lc.RockDam(water_year_month)
        # palo_verde_dam = basins.lc.PaloVerdeDam(water_year_month)
        imperial_dam = basins.lc.ImperialDam(water_year_month)
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

        self.states = [State('Arizona', 'az', az, self.reaches, self),
                       State('California', 'ca', ca, self.reaches, self),
                       State('Nevada', 'nv', nv, self.reaches, self),
                       State('Mexico', 'mx', mx, self.reaches, self)]

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

        if self.option_havasu_evap_charge_to_havasu_users is True:
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


if __name__ == '__main__':
    pyplot.switch_backend('Agg')  # FIXME must be accessing pyplt somewhere
    summaries = []
    num_runs = 4
    for run_number in range(0, num_runs):
        snwa_loss_model = Model('snwa_loss_study')
        if run_number == 0:
            pass
        elif run_number == 1:
            snwa_loss_model.option_havasu_evap_charge_to_havasu_users = True
        elif run_number == 2:
            snwa_loss_model.option_havasu_evap_charge_to_havasu_users = True
            snwa_loss_model.option_grand_canyon_inflow_cancels_mead_evap = True
        elif run_number == 3:
            snwa_loss_model.option_havasu_evap_charge_to_havasu_users = True
            snwa_loss_model.option_grand_canyon_inflow_cancels_mead_evap = True
            snwa_loss_model.option_yuma_users_moved_to_reach_4 = True
        elif run_number == 4:
            snwa_loss_model.option_crit_in_reach_3a = True
        elif run_number == 5:
            snwa_loss_model.option_palo_verde_in_reach_3b = True
        else:
            snwa_loss_model.option_havasu_evap_charge_to_havasu_users = True
            snwa_loss_model.option_yuma_users_moved_to_reach_4 = True
            snwa_loss_model.option_grand_canyon_inflow_cancels_mead_evap = True
            snwa_loss_model.option_crit_in_reach_3a = True
            snwa_loss_model.option_palo_verde_in_reach_3b = True

        snwa_loss_model.initialize()
        snwa_loss_model.run(2019, 2021)
        summary = snwa_loss_model.print()
        summaries.append(summary)

    model_run_summaries(num_runs, summaries)
