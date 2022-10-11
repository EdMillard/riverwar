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
import usbr
from source import usbr_report
from graph.water import WaterGraph
from util import add_annual, add_annuals, subtract_annual, reshape_annual_range

current_last_year = 2021


def test():
    arizona_state_land_diversion()
    state_total_vs_user_total_graph()
    others_users_pumping()
    total_returns()

    total_graph()

    # Davis Dam Area
    fort_mojave()
    bullhead_city()
    mohave_valley_irrigation()
    cibola_valley()
    cibola_national_wildlife()

    # Parker Dam Area
    central_arizona_project()
    havasu_national_wildlife()
    lake_havasu()

    # Rock Dam Area
    colorado_river_indian_tribes()

    # Imperial Dam Area
    yuma_mesa()
    yuma_county_wua()
    north_gila_irrigation()
    gila_monster()
    unit_b()
    yuma_irrigation()
    cocopah()
    wellton_mohawk()

    # Misc
    others_users_pumping()
    sturges()


def total_graph():
    usbr.util.diversion_vs_consumptive('az', 'total', 'Arizona',
                                       ymin1=900000, ymax1=3800000,
                                       ymin2=550000, ymax2=900000, yinterval2=25000)


def state_total_vs_user_total_graph():
    year_interval = 3
    graph = WaterGraph(nrows=2)

    az_total_diversion = state_total_diversion('az', 'total')
    users_total_diversion = total_diversion()
    bar_data = [
        {'data': az_total_diversion, 'label': 'State Total', 'color': 'darkmagenta'},
        {'data': users_total_diversion, 'label': 'Users', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=0,
                       title='AZ State Total Diversion vs User Total',
                       ymin=1500000, ymax=3750000, yinterval=200000,
                       xlabel='', xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf, vertical=False)
    graph.running_average(az_total_diversion, 10, sub_plot=0)
    graph.running_average(users_total_diversion, 10, sub_plot=0)

    difference = subtract_annual(az_total_diversion, users_total_diversion)
    graph.bars(difference, sub_plot=1, title='AZ State Total Diversion minus User Total', color='firebrick',
               ymin=-10000, ymax=50000, yinterval=10000,
               xlabel='Calendar Year', xinterval=4,
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.date_and_wait()

    graph = WaterGraph(nrows=2)
    az_total_cu = state_total_cu('az', 'total')
    users_total_cu = total_cu()
    bar_data = [
        {'data': az_total_cu, 'label': 'State', 'color': 'darkmagenta'},
        {'data': users_total_cu, 'label': 'Users', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=0,
                       title='AZ State Total Consumptive Use vs Users Total Consumptive Use',
                       ymin=800000, ymax=3000000, yinterval=200000,
                       xlabel='', xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf, vertical=False)
    graph.running_average(az_total_cu, 10, sub_plot=0)
    graph.running_average(users_total_cu, 10, sub_plot=0)

    difference = subtract_annual(az_total_cu, users_total_cu)
    graph.bars(difference, sub_plot=1, title='AZ State Total Consumptive Use minus User Total', color='firebrick',
               ymin=-30000, ymax=20000, yinterval=5000,
               xlabel='Calendar Year', xinterval=4,
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.date_and_wait()


def state_total_diversion(state_code, name):
    diversion_file_name = state_code + '/usbr_' + state_code + '_' + name + '_diversion.csv'
    return usbr_report.annual_af(diversion_file_name)


def state_total_cu(state_code, name):
    diversion_file_name = state_code + '/usbr_' + state_code + '_' + name + '_consumptive_use.csv'
    return usbr_report.annual_af(diversion_file_name)


def total_diversion():
    data = [
        # 2021 list in order
        # Marble Canyon
        # Lake mead rec from Lake Mead
        # Lake mead rec from Lake Mohave
        # McAlister
        # Lower Colorado River Dams Project/USBR
        bullhead_city_diversion(),
        # Mohave Water Conservation
        # Brooke Water/Epcore
        mohave_valley_diversion(),
        # Mohave County Water Authority
        fort_mojave_diversion(),  # Davis Dam, Lake Mohave
        # Golden Shores
        havasu_national_wildlife_diversion(),
        # Crystal Beach
        lake_havasu_diversion(),
        # Arizona Parks
        cap_diversion(),
        # Hillcrest
        # Springs Del Sol
        town_of_parker_diversion(),
        crit_diversion(),
        gabrych_diversion(),
        # Ehrenburg
        # B & F
        # North Baja
        cibola_valley_diversion(),
        # Red River
        # Western Water
        # Hopi Tribe
        arizona_game_and_fish_diversion(),
        # Cibola Island
        cibola_national_wildlife_diversion(),
        imperial_national_wildlife_diversion(),
        # BLM
        # Fisher's Landing
        # Shephard Water
        # Yuma Proving Ground
        # JRJ
        # Cha Cha
        # Beattie Farms
        gila_monster_diversion(),
        wellton_mohawk_diversion(),
        city_of_yuma_diversion(),
        marine_corp_diversion(),
        # Union/Southern Pacific
        # Yuma Mesa Fruit
        university_of_arizona_diversion(),
        yuma_union_high_school_diversion(),
        # Camille, Alec
        # Desert Lawn
        north_gila_irrigation_diversion(),
        yuma_irrigation_diversion(),
        yuma_mesa_diversion(),
        unit_b_diversion(),
        arizona_state_land_diversion(),
        # Ott Familyt
        # Ogram Boys
        fort_yuma_diversion(),
        # Armon Curtis
        yuma_county_wua_diversion(),
        # R Griffith
        # Power
        # Cocopa PPR No 7
        # Griffith Ranches
        # Milton Phillips
        cocopah_diversion(),
        # Yuma area office USBR
        # Arizona Public Service
        # Gary Pasquinelli
        # Misc out of order
        others_users_pumping_diversion(),
        south_gila_diversion(),
        sturges_diversion(),
        warren_act_diversion(),
    ]
    data[0] = reshape_annual_range(data[0], 1964, current_last_year)
    return add_annuals(data)


def total_cu():
    data = [
        # 2021 list in order
        # Marble Canyon
        # Lake mead rec from Lake Mead
        # Lake mead rec from Lake Mohave
        # McAlister
        # Lower Colorado River Dams Project/USBR
        bullhead_city_cu(),
        # Mohave Water Conservation
        # Brooke Water/Epcore
        mohave_valley_cu(),
        # Mohave County Water Authority
        fort_mojave_cu(),  # Davis Dam, Lake Mohave
        # Golden Shores
        havasu_national_wildlife_cu(),
        # Crystal Beach
        lake_havasu_cu(),
        # Arizona Parks
        cap_cu(),
        # Hillcrest
        # Springs Del Sol
        town_of_parker_cu(),
        crit_cu(),
        gabrych_cu(),
        # Ehrenburg
        # B & F
        # North Baja
        cibola_valley_cu(),
        # Red River
        # Western Water
        # Hopi Tribe
        arizona_game_and_fish_cu(),
        # Cibola Island
        cibola_national_wildlife_cu(),
        imperial_national_wildlife_cu(),
        # BLM
        # Fisher's Landing
        # Shephard Water
        # Yuma Proving Ground
        # JRJ
        # Cha Cha
        # Beattie Farms
        gila_monster_cu(),
        wellton_mohawk_cu(),
        city_of_yuma_cu(),
        marine_corp_cu(),
        # Union/Southern Pacific
        # Yuma Mesa Fruit
        university_of_arizona_cu(),
        yuma_union_high_school_cu(),
        # Camille, Alec
        # Desert Lawn
        north_gila_irrigation_cu(),
        yuma_irrigation_cu(),
        yuma_mesa_cu(),
        unit_b_cu(),
        arizona_state_land_cu(),
        # Ott Familyt
        # Ogram Boys
        fort_yuma_cu(),
        # Armon Curtis
        yuma_county_wua_cu(),
        # R Griffith
        # Power
        # Cocopa PPR No 7
        # Griffith Ranches
        # Milton Phillips
        cocopah_cu(),
        # Yuma area office USBR
        # Arizona Public Service
        # Gary Pasquinelli
        # Misc out of order
        others_users_pumping_cu(),
        south_gila_cu(),
        sturges_cu(),
        warren_act_cu(),
    ]
    data[0] = reshape_annual_range(data[0], 1964, current_last_year)
    total = add_annuals(data)
    return total


def total_returns():
    data = [
        # 2021 list in order
        # Marble Canyon
        # Lake mead rec from Lake Mead
        # Lake mead rec from Lake Mohave
        # McAlister
        # Lower Colorado River Dams Project/USBR
        bullhead_city_returns(),
        # Mohave Water Conservation
        # Brooke Water/Epcore
        mohave_valley_returns(),
        # Mohave County Water Authority
        fort_mojave_returns(),  # Davis Dam, Lake Mohave
        # Golden Shores
        havasu_national_wildlife_returns(),
        # Crystal Beach
        lake_havasu_returns(),
        # Arizona Parks
        # CAP Has not returns
        # Hillcrest
        # Springs Del Sol
        town_of_parker_returns(),
        crit_returns(),
        gabrych_returns(),
        # Ehrenburg
        # B & F
        # North Baja
        cibola_valley_returns(),
        # Red River
        # Western Water
        # Hopi Tribe
        arizona_game_and_fish_returns(),
        # Cibola Island
        cibola_national_wildlife_returns(),
        imperial_national_wildlife_returns(),
        # BLM
        # Fisher's Landing
        # Shephard Water
        # Yuma Proving Ground
        # JRJ
        # Cha Cha
        # Beattie Farms
        gila_monster_returns(),
        wellton_mohawk_returns(),
        city_of_yuma_returns(),
        marine_corp_returns(),
        # Union/Southern Pacific
        # Yuma Mesa Fruit
        university_of_arizona_returns(),
        yuma_union_high_school_returns(),
        # Camille, Alec
        # Desert Lawn
        north_gila_irrigation_returns(),
        yuma_irrigation_returns(),
        yuma_mesa_returns(),
        unit_b_returns(),
        arizona_state_land_returns(),
        # Ott Familyt
        # Ogram Boys
        fort_yuma_returns(),
        # Armon Curtis
        yuma_county_wua_returns(),
        # R Griffith
        # Power
        # Cocopa PPR No 7
        # Griffith Ranches
        # Milton Phillips
        cocopah_returns(),
        # Yuma area office USBR
        # Arizona Public Service
        # Gary Pasquinelli
        # Misc out of order
        others_users_pumping_returns(),
        south_gila_returns(),
        sturges_returns(),
        warren_act_returns(),
    ]
    data[0] = reshape_annual_range(data[0], 1964, current_last_year)
    return add_annuals(data)


def yuma_area_returns():
    # Yuma Irrigation Pumping
    # gila_monster()
    # Imperial wildlife ?
    data = [{'data': south_gila_returns(), 'label': 'South Gila', 'color': 'darkgray'},
            {'data': yuma_mesa_returns(), 'label': 'Yuma Mesa', 'color': 'maroon'},
            {'data': yuma_county_wua_returns(), 'label': 'Yuma County WUA', 'color': 'firebrick'},
            {'data': north_gila_irrigation_returns(), 'label': 'North Gila', 'color': 'lightcoral'},
            {'data': yuma_irrigation_returns(), 'label': 'Yuma Irrigation', 'color': 'pink'},
            {'data': unit_b_returns(), 'label': 'Unit B', 'color': 'mistyrose'},
            {'data': gila_monster_returns(), 'label': 'Gila Monster', 'color': 'mistyrose'},  # Fixme Color
            {'data': cocopah_returns(), 'label': 'Cocopah', 'color': 'mistyrose'},  # Fixme Color
            {'data': city_of_yuma_returns(), 'label': 'City of Yuma', 'color': 'darkblue'},
            {'data': wellton_mohawk_returns(), 'label': 'Wellton', 'color': 'royalblue'}]
    return data


def yuma_area_diversion():
    data = [{'data': yuma_mesa_diversion(), 'label': 'Yuma Mesa', 'color': 'maroon'},
            {'data': yuma_county_wua_diversion(), 'label': 'Yuma County WUA', 'color': 'firebrick'},
            {'data': north_gila_irrigation_diversion(), 'label': 'North Gila', 'color': 'lightcoral'},
            {'data': yuma_irrigation_diversion(), 'label': 'Yuma Irrigation', 'color': 'pink'},
            {'data': unit_b_diversion(), 'label': 'Unit B', 'color': 'mistyrose'},
            {'data': gila_monster_diversion(), 'label': 'Gila Monster', 'color': 'mistyrose'},  # Fixme Color
            {'data': cocopah_diversion(), 'label': 'Cocopah', 'color': 'mistyrose'},  # Fixme Color
            {'data': city_of_yuma_diversion(), 'label': 'City of Yuma', 'color': 'darkblue'},
            {'data': wellton_mohawk_diversion(), 'label': 'Wellton', 'color': 'royalblue'}]
    return data


def yuma_area_cu():
    data = [{'data': yuma_mesa_cu(), 'label': 'Yuma Mesa', 'color': 'maroon'},
            {'data': yuma_county_wua_cu(), 'label': 'Yuma County WUA', 'color': 'firebrick'},
            {'data': north_gila_irrigation_cu(), 'label': 'North Gila', 'color': 'lightcoral'},
            {'data': yuma_irrigation_cu(), 'label': 'Yuma Irrigation', 'color': 'pink'},
            {'data': unit_b_cu(), 'label': 'Unit B', 'color': 'mistyrose'},
            {'data': gila_monster_cu(), 'label': 'Gila Monster', 'color': 'mistyrose'},  # Fixme Color
            {'data': cocopah_cu(), 'label': 'Cocopah', 'color': 'mistyrose'},  # Fixme Color
            {'data': city_of_yuma_cu(), 'label': 'City of Yuma', 'color': 'darkblue'},
            {'data': wellton_mohawk_cu(), 'label': 'Wellton', 'color': 'royalblue'}]
    return data


def not_yuma_area_returns():
    # Fort Mojave
    # Arizona state land
    # Lake Havasu City
    # Bullhead City
    # Town of Parker
    # GM Gabrych?
    data = [{'data': crit_returns(), 'label': 'Colorado River Indian Tribes', 'color': 'maroon'},
            {'data': fort_mojave_returns(), 'label': 'Fort Mojave Indian', 'color': 'firebrick'},
            {'data': mohave_valley_returns(), 'label': 'Mohave Valley', 'color': 'lightcoral'},
            {'data': cibola_valley_returns(), 'label': 'Cibola Valley', 'color': 'pink'},
            {'data': cibola_national_wildlife_returns(), 'label': 'Mohave Valley', 'color': 'mistyrose'},
            {'data': lake_havasu_returns(), 'label': 'Lake Havasu', 'color': 'mistyrose'},
            {'data': bullhead_city_returns(), 'label': 'Bullhead City', 'color': 'mistyrose'},
            {'data': havasu_national_wildlife_returns(), 'label': 'Havasu National Wildlife Refuge',
             'color': 'darkblue'},
            {'data': sturges_returns(), 'label': 'Sturges', 'color': 'darkblue'}  # FIXME color
            ]
    return data


def fort_mojave():
    year_interval = 2

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_fort_mojave_indian_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_fort_mojave_indian_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0, title='Fort Mojave (Monthly)',
               xinterval=year_interval, ymax=13000, yinterval=1000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=13000, yinterval=1000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = fort_mojave_diversion()
    annual_cu_af = fort_mojave_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1,
                       title='Fort Mojave Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=85000, yinterval=5000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def fort_mojave_diversion():
    return usbr_report.annual_af('az/usbr_az_fort_mojave_indian_diversion.csv')


def fort_mojave_cu():
    return usbr_report.annual_af('az/usbr_az_fort_mojave_indian_consumptive_use.csv')


def fort_mojave_returns():
    return subtract_annual(fort_mojave_diversion(), fort_mojave_cu())


def mohave_valley_irrigation():
    year_interval = 2

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_mohave_valley_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_mohave_valley_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0, title='Mohave Valley IID (Monthly)',
               xinterval=year_interval, ymax=7000, yinterval=1000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=7000, yinterval=1000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = mohave_valley_diversion()
    annual_cu_af = mohave_valley_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1,
                       title='Mohave Valley IID Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=50000, yinterval=5000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def mohave_valley_diversion():
    return usbr_report.annual_af('az/usbr_az_mohave_valley_diversion.csv')


def mohave_valley_cu():
    return usbr_report.annual_af('az/usbr_az_mohave_valley_consumptive_use.csv')


def mohave_valley_returns():
    return subtract_annual(north_gila_irrigation_diversion(), north_gila_irrigation_cu())


def town_of_parker_diversion():
    return usbr_report.annual_af('az/usbr_az_town_of_parker_diversion.csv')


def town_of_parker_cu():
    return usbr_report.annual_af('az/usbr_az_town_of_parker_consumptive_use.csv')


def town_of_parker_returns():
    return subtract_annual(town_of_parker_diversion(), town_of_parker_cu())


def cibola_valley():
    year_interval = 2

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_cibola_valley_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_cibola_valley_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0, title='Cibola Valley (Monthly)',
               xinterval=year_interval, ymax=5000, yinterval=500, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=5000, yinterval=500, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = cibola_valley_diversion()
    annual_cu_af = cibola_valley_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1,
                       title='Cibola Valley Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=35000, yinterval=5000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def cibola_valley_diversion():
    return usbr_report.annual_af('az/usbr_az_cibola_valley_diversion.csv')


def cibola_valley_cu():
    return usbr_report.annual_af('az/usbr_az_cibola_valley_consumptive_use.csv')


def cibola_valley_returns():
    return subtract_annual(cibola_valley_diversion(), cibola_valley_cu())


def cibola_national_wildlife():
    year_interval = 2

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_cibola_national_wildlife_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_cibola_national_wildlife_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0, title='Cibola National Wildlife Refuge (Monthly)',
               xinterval=year_interval, ymax=3500, yinterval=500, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=3500, yinterval=500, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = cibola_national_wildlife_diversion()
    annual_cu_af = cibola_national_wildlife_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1,
                       title='Cibola National Wildlife Refuge Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=20000, yinterval=2000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def cibola_national_wildlife_diversion():
    return usbr_report.annual_af('az/usbr_az_cibola_national_wildlife_diversion.csv')


def cibola_national_wildlife_cu():
    return usbr_report.annual_af('az/usbr_az_cibola_national_wildlife_consumptive_use.csv')


def cibola_national_wildlife_returns():
    return subtract_annual(cibola_national_wildlife_diversion(), cibola_national_wildlife_cu())


def bullhead_city():
    year_interval = 3

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_bullhead_city_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_bullhead_city_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0, title='Bullhead City Diversion and Consumptive Use (Monthly)',
               xinterval=year_interval, ymax=2000, yinterval=200, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=2000, yinterval=200, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = bullhead_city_diversion()
    annual_cu_af = bullhead_city_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Bullhead City Diversion and Consumptive Use (Annual)',
                       ymin=0, ymax=14000, yinterval=1000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def bullhead_city_diversion():
    annuals = [usbr_report.annual_af('az/usbr_az_bullhead_city_diversion.csv'),
               usbr_report.annual_af('az/usbr_az_bullhead_city_davis_dam_diversion.csv')
               ]
    return add_annuals(annuals)


def bullhead_city_cu():
    return usbr_report.annual_af('az/usbr_az_bullhead_city_consumptive_use.csv')


def bullhead_city_returns():
    return subtract_annual(bullhead_city_diversion(), bullhead_city_cu())


def lake_havasu():
    year_interval = 2

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_lake_havasu_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_lake_havasu_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0, title='Lake Havasu Irrigation (Monthly)',
               xinterval=year_interval, ymax=5000, yinterval=500, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=5000, yinterval=500, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = lake_havasu_diversion()
    annual_cu_af = lake_havasu_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1,
                       title='Lake Havasu Irrigation Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=35000, yinterval=5000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def lake_havasu_diversion():
    return usbr_report.annual_af('az/usbr_az_lake_havasu_diversion.csv')


def lake_havasu_cu():
    return usbr_report.annual_af('az/usbr_az_lake_havasu_consumptive_use.csv')


def lake_havasu_returns():
    return subtract_annual(lake_havasu_diversion(), lake_havasu_cu())


def central_arizona_project():
    year_interval = 3

    monthly_af = usbr_report.load_monthly_csv('az/usbr_az_central_arizona_project_diversion.csv')
    graph = WaterGraph(nrows=3)
    graph.plot(monthly_af, sub_plot=0, title='Lake Havasu CAP Wilmer Pumping Plant (Monthly)',
               xinterval=year_interval, ymax=200000, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=1, title='Lake Havasu CAP Wilmer Pumping Plant (Annual)',
               xinterval=year_interval, ymin=0, ymax=1800000, yinterval=100000,
               xlabel='Calendar Year',   color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)

    ics = usbr.lc.lake_mead_load_ics()
    ics_az_delta = ics['AZ Delta']
    ics_az_delta = graph.reshape_annual_range(ics_az_delta, 1985, current_last_year)

    bar_data = [{'data': annual_af, 'label': 'CAP Wilmer Pumps', 'color': 'firebrick'},
                {'data': ics_az_delta, 'label': 'AZ ICS Deposits', 'color': 'mediumseagreen'},
                ]
    graph.bars_stacked(bar_data, sub_plot=2, title='Lake Havasu CAP Wilmer Pumping Plant + AZ ICS Deposits',
                       ylabel='maf', ymin=0, ymax=1800000, yinterval=100000,
                       xlabel='Calendar Year', xinterval=3, format_func=WaterGraph.format_maf)
    graph.date_and_wait()


def cap_diversion():
    annuals = [usbr_report.annual_af('az/usbr_az_central_arizona_project_diversion.csv'),
               usbr_report.annual_af('az/usbr_az_central_arizona_project_snwa_diversion.csv')
               ]
    return add_annuals(annuals)


def cap_cu():
    # CAP has no return flows so cu is the same as diversion
    return cap_diversion()


def colorado_river_indian_tribes():
    year_interval = 3

    graph = WaterGraph(nrows=2)

    diversion_annual = crit_diversion()
    cu_annual = crit_cu()

    bar_data = [{'data': diversion_annual, 'label': 'Diversion', 'color': 'darkmagenta'},
                {'data': cu_annual, 'label': 'Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=0, title='CRIT Diversion & Consumptive Use',
                       ymin=0, ymax=710000, yinterval=100000,
                       xlabel='Calendar Year', xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf, vertical=False)
    graph.running_average(diversion_annual, 10, sub_plot=0)
    graph.running_average(cu_annual, 10, sub_plot=0)

    returns_annual = subtract_annual(diversion_annual, cu_annual)
    graph.bars(returns_annual, sub_plot=1, title='Colorado River Indian Tribe Consumptive Use',
               ymin=0, ymax=400000, yinterval=50000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.date_and_wait()


def crit_diversion():
    return usbr_report.annual_af('az/usbr_az_crit_diversion.csv')


def crit_cu():
    return usbr_report.annual_af('az/usbr_az_crit_consumptive_use.csv')


def crit_returns():
    return subtract_annual(crit_diversion(), crit_cu())


def yuma_mesa():
    start_year = 1964
    year_interval = 3
    # Yuma Mesa Irrigation
    # This is complicated, early years had a drain with return flows
    # migrated to returns, then measured and unmeasured returns later
    yuma_mesa_diversion_annual_af = usbr_report.annual_af('az/usbr_az_yuma_mesa_irrigation_diversion.csv')
    yuma_mesa_cu_annual_af = usbr_report.annual_af('az/usbr_az_yuma_mesa_irrigation_consumptive_use.csv')
    yuma_mesa_drain_annual_af = usbr_report.annual_af('az/usbr_az_yuma_mesa_outlet_drain_returns.csv')

    drain_start_year = yuma_mesa_drain_annual_af['dt'][0]
    drain_end_year = yuma_mesa_drain_annual_af['dt'][-1]
    yuma_mesa_diversion_tmp = reshape_annual_range(yuma_mesa_diversion_annual_af, drain_start_year, drain_end_year)

    yuma_mesa_drain_cu_annual_af = subtract_annual(yuma_mesa_diversion_tmp, yuma_mesa_drain_annual_af)
    yuma_mesa_drain_cu_annual_af = reshape_annual_range(yuma_mesa_drain_cu_annual_af, start_year, current_last_year)

    yuma_mesa_cu_annual_af = reshape_annual_range(yuma_mesa_cu_annual_af, start_year, current_last_year)
    yuma_mesa_cu_annual_af = add_annual(yuma_mesa_cu_annual_af, yuma_mesa_drain_cu_annual_af)

    # yuma_mesa_returns_annual_af = usbr_report.annual_af('az/usbr_az_yuma_mesa_irrigation_returns.csv')
    # yuma_mesa_measured_returns_annual_af = usbr_report.annual_af(
    #     'az/usbr_az_yuma_mesa_irrigation_measured_returns.csv')
    # yuma_mesa_annual_unmeasured_returns_af = usbr_report.annual_af(
    #     'az/usbr_az_yuma_mesa_irrigation_unmeasured_returns.csv')

    graph = WaterGraph(nrows=2)
    bar_data = [
        {'data': yuma_mesa_drain_annual_af, 'label': 'Diversion minus Drain Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=0, title='Yuma Mesa Drain Returns (Annual)',
                       ymin=0, ymax=300000, yinterval=50000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(yuma_mesa_diversion_annual_af, 10, sub_plot=1)
    bar_data = [
        {'data': yuma_mesa_diversion_annual_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': yuma_mesa_cu_annual_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Yuma Mesa Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=300000, yinterval=50000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(yuma_mesa_diversion_annual_af, 10, sub_plot=1)
    graph.running_average(yuma_mesa_cu_annual_af, 10, sub_plot=1)

    graph.date_and_wait()


def yuma_mesa_diversion():
    return usbr_report.annual_af('az/usbr_az_yuma_mesa_irrigation_diversion.csv')


def yuma_mesa_cu():
    cu = usbr_report.annual_af('az/usbr_az_yuma_mesa_irrigation_consumptive_use.csv')
    cu = subtract_annual(cu, yuma_mesa_outlet_drain_returns())
    cu = subtract_annual(cu, protective_pumping_returns())
    cu = subtract_annual(cu, south_gila_returns())
    return cu


def yuma_mesa_outlet_drain_returns():
    return usbr_report.annual_af('az/usbr_az_yuma_mesa_outlet_drain_returns.csv')


def yuma_mesa_returns():
    return subtract_annual(yuma_mesa_diversion(), yuma_mesa_cu())


def yuma_county_wua():
    year_interval = 2

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_yuma_county_wua_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_yuma_county_wua_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0, title='Yuma County WUA Diversion (Monthly)',
               xinterval=year_interval, ymax=55000, yinterval=5000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=55000, yinterval=5000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = yuma_county_wua_diversion()
    annual_cu_af = yuma_county_wua_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1,
                       title='Yuma County WUA Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=400000, yinterval=50000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def yuma_county_wua_diversion():
    annuals = [usbr_report.annual_af('az/usbr_az_yuma_county_wua_diversion.csv'),
               usbr_report.annual_af('az/usbr_az_yuma_county_wua_pumped_diversion.csv')
               ]
    return add_annuals(annuals)


def yuma_county_wua_cu():
    return usbr_report.annual_af('az/usbr_az_yuma_county_wua_consumptive_use.csv')


def yuma_county_wua_returns():
    return subtract_annual(yuma_county_wua_diversion(), yuma_county_wua_cu())


def north_gila_irrigation():
    year_interval = 2

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_north_gila_irrigation_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_north_gila_irrigation_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0, title='North Gila (Monthly)',
               xinterval=year_interval, ymax=10000, yinterval=1000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=10000, yinterval=1000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = north_gila_irrigation_diversion()
    annual_cu_af = north_gila_irrigation_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1,
                       title='North Gila Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=75000, yinterval=5000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def north_gila_irrigation_diversion():
    return usbr_report.annual_af('az/usbr_az_north_gila_irrigation_diversion.csv')


def north_gila_irrigation_cu():
    return usbr_report.annual_af('az/usbr_az_north_gila_irrigation_consumptive_use.csv')


def north_gila_irrigation_returns():
    return subtract_annual(north_gila_irrigation_diversion(), north_gila_irrigation_cu())


def gila_monster():
    year_interval = 2

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_gila_monster_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_gila_monster_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0, title='Gila Monster (Monthly)',
               xinterval=year_interval, ymax=3000, yinterval=500, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=3000, yinterval=500, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = gila_monster_diversion()
    annual_cu_af = gila_monster_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1,
                       title='Gila Monster Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=15000, yinterval=1000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def gila_monster_diversion():
    return usbr_report.annual_af('az/usbr_az_gila_monster_diversion.csv')


def gila_monster_cu():
    return usbr_report.annual_af('az/usbr_az_gila_monster_consumptive_use.csv')


def gila_monster_returns():
    return subtract_annual(gila_monster_diversion(), gila_monster_cu())


def fort_yuma_diversion():
    return usbr_report.annual_af('az/usbr_az_fort_yuma_diversion.csv')


def fort_yuma_cu():
    return usbr_report.annual_af('az/usbr_az_fort_yuma_consumptive_use.csv')


def fort_yuma_returns():
    return subtract_annual(fort_yuma_diversion(), fort_yuma_cu())


def yuma_union_high_school_diversion():
    return usbr_report.annual_af('az/usbr_az_yuma_union_high_school_diversion.csv')


def yuma_union_high_school_cu():
    return usbr_report.annual_af('az/usbr_az_yuma_union_high_school_consumptive_use.csv')


def yuma_union_high_school_returns():
    return subtract_annual(yuma_union_high_school_diversion(), yuma_union_high_school_cu())


def south_gila_diversion():
    diversion = usbr_report.annual_af('az/usbr_az_south_gila_pump_diversion.csv')
    diversion = reshape_annual_range(diversion, 1964, current_last_year)
    return diversion


def south_gila_cu():
    cu = usbr_report.annual_af('az/usbr_az_south_gila_pump_consumptive_use.csv')
    cu = reshape_annual_range(cu, 1964, current_last_year)
    return cu


def protective_pumping_returns():
    return usbr_report.annual_af('az/usbr_az_protective_pumping_returns.csv')


def south_gila_returns():
    returns = usbr_report.annual_af('az/usbr_az_south_gila_returns.csv')
    returns = reshape_annual_range(returns, 1964, current_last_year)
    return returns


def yuma_irrigation():
    year_interval = 2

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_yuma_irrigation_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_yuma_irrigation_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0, title='Yuma Irrigation (Monthly)',
               xinterval=year_interval, ymax=10000, yinterval=1000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=10000, yinterval=1000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = yuma_irrigation_diversion()
    annual_cu_af = yuma_irrigation_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1,
                       title='Yuma Irrigation Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=100000, yinterval=5000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def yuma_irrigation_diversion():
    annuals = [usbr_report.annual_af('az/usbr_az_yuma_irrigation_diversion.csv'),
               usbr_report.annual_af('az/usbr_az_yuma_irrigation_pumped_diversion.csv')
               ]
    return add_annuals(annuals)


def yuma_irrigation_cu():
    annual_cu = usbr_report.annual_af('az/usbr_az_yuma_irrigation_consumptive_use.csv')
    return annual_cu


def yuma_irrigation_returns():
    return subtract_annual(yuma_irrigation_diversion(), yuma_irrigation_cu())


def unit_b():
    year_interval = 2

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_unit_b_irrigation_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_unit_b_irrigation_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0, title='Unit B (Monthly)',
               xinterval=year_interval, ymax=6000, yinterval=500, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=6000, yinterval=500, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = unit_b_diversion()
    annual_cu_af = unit_b_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1,
                       title='Unit B Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=45000, yinterval=5000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def unit_b_diversion():
    return usbr_report.annual_af('az/usbr_az_unit_b_irrigation_diversion.csv')


def unit_b_cu():
    return usbr_report.annual_af('az/usbr_az_unit_b_irrigation_consumptive_use.csv')


def unit_b_returns():
    return subtract_annual(unit_b_diversion(), unit_b_cu())


def wellton_mohawk():
    year_interval = 3

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_wellton_mohawk_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_wellton_mohawk_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0,
               title='Wellton-Mohawk Diversion  and Consumptive Use (Monthly)',
               xinterval=year_interval, ymax=75000, yinterval=5000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=75000, yinterval=5000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = wellton_mohawk_diversion()
    annual_cu_af = wellton_mohawk_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Wellton-Mohawk Diversion and Consumptive Use (Annual)',
                       ymin=0, ymax=600000, yinterval=50000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def wellton_mohawk_diversion():
    return usbr_report.annual_af('az/usbr_az_wellton_mohawk_diversion.csv')


def wellton_mohawk_cu():
    return usbr_report.annual_af('az/usbr_az_wellton_mohawk_consumptive_use.csv')


def wellton_mohawk_returns():
    return subtract_annual(wellton_mohawk_diversion(), wellton_mohawk_cu())


def city_of_yuma():
    year_interval = 3

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_city_of_yuma_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_city_of_yuma_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0, title='City of Yuma Diversion and Consumptive Use (Monthly)',
               xinterval=year_interval, ymax=4000, yinterval=500, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=4000, yinterval=500, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = city_of_yuma_diversion()
    annual_cu_af = city_of_yuma_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1, title='City of Yuma Diversion and Consumptive Use (Annual)',
                       ymin=0, ymax=40000, yinterval=2000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def city_of_yuma_diversion():
    annuals = [usbr_report.annual_af('az/usbr_az_city_of_yuma_diversion.csv'),
               usbr_report.annual_af('az/usbr_az_city_of_yuma_gila_diversion.csv')
               ]
    return add_annuals(annuals)


def city_of_yuma_cu():
    return usbr_report.annual_af('az/usbr_az_city_of_yuma_consumptive_use.csv')


def city_of_yuma_returns():
    return subtract_annual(city_of_yuma_diversion(), city_of_yuma_cu())


def cocopah():
    year_interval = 3

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_cocopah_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_cocopah_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0,
               title='Cocopah Diversion and Consumptive Use (Monthly)',
               xinterval=year_interval, ymax=3000, yinterval=500, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=3000, yinterval=500, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = cocopah_diversion()
    annual_cu_af = cocopah_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Cocopah Diversion and Consumptive Use (Annual)',
                       ymin=0, ymax=18000, yinterval=2000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def cocopah_diversion():
    annuals = [usbr_report.annual_af('az/usbr_az_cocopah_diversion.csv'),
               usbr_report.annual_af('az/usbr_az_cocopah_pumped.csv'),
               usbr_report.annual_af('az/usbr_az_cocopah_west_pumped.csv')
               ]
    return add_annuals(annuals)


def cocopah_cu():
    return usbr_report.annual_af('az/usbr_az_cocopah_consumptive_use.csv')


def cocopah_returns():
    return subtract_annual(cocopah_diversion(), cocopah_cu())


def havasu_national_wildlife():
    year_interval = 3

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_havasu_national_wildlife_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_havasu_national_wildlife_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0,
               title='Havasu National Wildlife Diversion and Consumptive Use (Monthly)',
               xinterval=year_interval, ymax=12000, yinterval=1000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=12000, yinterval=1000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = havasu_national_wildlife_diversion()
    annual_cu_af = havasu_national_wildlife_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Havasu National Wildlife Diversion and Consumptive Use (Annual)',
                       ymin=0, ymax=65000, yinterval=5000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def havasu_national_wildlife_diversion():
    annuals = [usbr_report.annual_af('az/usbr_az_havasu_national_wildlife_diversion.csv'),
               usbr_report.annual_af('az/usbr_az_havasu_national_farm_ditch_diversion.csv'),
               usbr_report.annual_af('az/usbr_az_havasu_national_pumped_diversion.csv')
               ]
    return add_annuals(annuals)


def havasu_national_wildlife_cu():
    return usbr_report.annual_af('az/usbr_az_havasu_national_wildlife_consumptive_use.csv')


def havasu_national_wildlife_returns():
    return subtract_annual(havasu_national_wildlife_diversion(), havasu_national_wildlife_cu())


def imperial_national_wildlife_diversion():
    annuals = [usbr_report.annual_af('az/usbr_az_imperial_national_wildlife_diversion.csv'),
               ]
    return add_annuals(annuals)


def imperial_national_wildlife_cu():
    return usbr_report.annual_af('az/usbr_az_imperial_national_wildlife_consumptive_use.csv')


def imperial_national_wildlife_returns():
    return subtract_annual(imperial_national_wildlife_diversion(), imperial_national_wildlife_cu())


def sturges():
    year_interval = 3

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_sturges_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_sturges_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0, title='Sturges, Warren Act (Monthly)',
               xinterval=year_interval, ymax=2500, yinterval=500, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=2500, yinterval=500, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = sturges_diversion()
    annual_cu_af = sturges_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Sturges, Warren Act, Diversion and Consumptive Use (Annual)',
                       ymin=0, ymax=20000, yinterval=1000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def marine_corp_diversion():
    return usbr_report.annual_af('az/usbr_az_marine_corp_diversion.csv')


def marine_corp_cu():
    return usbr_report.annual_af('az/usbr_az_marine_corp_consumptive_use.csv')


def marine_corp_returns():
    return subtract_annual(marine_corp_diversion(), marine_corp_cu())


def sturges_diversion():
    return usbr_report.annual_af('az/usbr_az_sturges_diversion.csv')


def sturges_cu():
    return usbr_report.annual_af('az/usbr_az_sturges_consumptive_use.csv')


def sturges_returns():
    return subtract_annual(sturges_diversion(), sturges_cu())


def warren_act_diversion():
    return usbr_report.annual_af('az/usbr_az_warren_act_diversion.csv')


def warren_act_cu():
    return usbr_report.annual_af('az/usbr_az_warren_act_consumptive_use.csv')


def warren_act_returns():
    return subtract_annual(warren_act_diversion(), warren_act_cu())


def arizona_state_land_diversion():
    return usbr_report.annual_af('az/usbr_az_arizona_state_land_diversion.csv')


def arizona_state_land_cu():
    return usbr_report.annual_af('az/usbr_az_arizona_state_land_consumptive_use.csv')


def arizona_state_land_returns():
    return subtract_annual(arizona_state_land_diversion(), arizona_state_land_cu())


def arizona_game_and_fish_diversion():
    return usbr_report.annual_af('az/usbr_az_arizona_game_and_fish_diversion.csv')


def arizona_game_and_fish_cu():
    return usbr_report.annual_af('az/usbr_az_arizona_game_and_fish_consumptive_use.csv')


def arizona_game_and_fish_returns():
    return subtract_annual(arizona_game_and_fish_diversion(), arizona_game_and_fish_cu())


def university_of_arizona_diversion():
    return usbr_report.annual_af('az/usbr_az_university_of_arizona_diversion.csv')


def university_of_arizona_cu():
    return usbr_report.annual_af('az/usbr_az_university_of_arizona_consumptive_use.csv')


def university_of_arizona_returns():
    return subtract_annual(university_of_arizona_diversion(), arizona_game_and_fish_returns())


def others_users_pumping():
    year_interval = 3

    graph = WaterGraph(nrows=2)
    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_other_users_pumping_diversion.csv')
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_other_users_pumping_consumptive_use.csv')
    graph.plot(monthly_diversion_af, sub_plot=0, title='Other Users Pumping Diversion (Monthly)',
               xinterval=year_interval, ymax=10000, yinterval=1000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=10000, yinterval=1000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = others_users_pumping_diversion()
    annual_cu_af = others_users_pumping_cu()
    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Other Users Pumping Diversion and Consumptive Use (Annual)',
                       ymin=0, ymax=110000, yinterval=10000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.date_and_wait()


def others_users_pumping_diversion():
    return usbr_report.annual_af('az/usbr_az_other_users_pumping_diversion.csv')


def others_users_pumping_cu():
    return usbr_report.annual_af('az/usbr_az_other_users_pumping_consumptive_use.csv')


def others_users_pumping_returns():
    return subtract_annual(others_users_pumping_diversion(), others_users_pumping_cu())


def gabrych_diversion():
    return usbr_report.annual_af('az/usbr_az_gabrych_diversion.csv')


def gabrych_cu():
    return usbr_report.annual_af('az/usbr_az_gabrych_consumptive_use.csv')


def gabrych_returns():
    return subtract_annual(gabrych_diversion(), gabrych_cu())
