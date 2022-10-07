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
from pathlib import Path
import pyocr
import pyocr.builders
from PIL import Image
from matplotlib import pyplot as plt
from matplotlib import image as mpimg
import re


def image_to_text(image_file_path):
    tools = pyocr.get_available_tools()[0]
    image = Image.open(image_file_path)
    builder = pyocr.builders.TextBuilder(tesseract_layout=4)
    text = tools.image_to_string(image, builder=builder)
    # text = tools.image_to_string(image, builder=pyocr.builders.WordBoxBuilder())
    # text = tools.image_to_string(image, builder=pyocr.builders.LineBoxBuilder())
    # text = tools.image_to_string(image, builder=pyocr.builders.DigitBuilder())
    return text


def year_from_file_path(file_path):
    file_name = file_path.stem
    parts = file_name.split('_')
    if len(parts) > 0:
        year = parts[0]
    else:
        year = 0
    return int(year)


def ocr_report(image_file_path, water_user='', field_id=''):
    water_user_lower = water_user.lower()
    field_id_lower = field_id.lower()
    year = year_from_file_path(image_file_path)

    text = image_to_text(image_file_path)
    strings = text.split('\n')
    look_for_diversion = False
    for string in strings:
        if not water_user_lower or water_user_lower in string.lower():
            look_for_diversion = True
        if look_for_diversion:
            string_lower = string.lower()
            if field_id_lower in string_lower:
                parts = string_lower.rsplit(field_id_lower, 1)
                if len(parts) > 0:
                    clean_string = ''
                    for c in parts[-1]:
                        if c.isdigit() or c == ' ' or c == '-' or c == '.':
                            clean_string += c
                    result = clean_string.replace('  ', ' ')
                    result = result.replace('  ', ' ')
                    result = result.strip()
                    values = result.split(' ')
                    # Did we get enough numbers to potentially be twelve month + total
                    if len(values) > 10:
                        return year, result
                else:
                    break

    return year, ''


def ocr_image_file(image_file_path, water_user, field_id, f, kaf_begin=0, kaf_end=0):
    error_tolerance = 2  # af error allowed between summation of months and annual total

    year, data = ocr_report(image_file_path, water_user, field_id)
    print_file_name_prefix = '\t' + image_file_path.name + ': '
    if year > 1900 and len(data) > 0:
        values = data.split(' ')
        # Footnotes in older reports end in '/'
        if values[0].endswith('/'):
            values.pop(0)

        if kaf_begin <= year <= kaf_end:
            n = 0
            for value in values:
                try:
                    values[n] = str(int(float(value) * 1000))
                except ValueError:
                    print('ValueError: cant convert to float: ', value)
                n += 1

        summation = 0
        for value in values[0:-1]:
            try:
                summation += int(value)
            except ValueError:
                print(print_file_name_prefix + 'ValueError in summation: ', value, year, data)
        if len(values):
            try:
                total = int(values[-1])
                error = abs(total - summation)
                out_str = ''
                for value in values:
                    out_str += value + ' '
                out_str.strip()
                error_str = ''
                if error > error_tolerance:
                    image_name = str(image_file_path.name).replace('.png', '')
                    error_str = '# error: ' + ' diff = ' + str(error) + ' got sum = ' + str(summation) \
                                + ' ' + image_name
                print(print_file_name_prefix + str(year) + ': ' + out_str + error_str)
                f.write(str(year) + ' ' + out_str + error_str + '\n')
                return year
            except ValueError:
                print(print_file_name_prefix + 'ValueError on total: ', values[-1], year, data)
        else:
            print(print_file_name_prefix + "Error Value array empty")

    return None


def ocr_reports(image_directory_path, output_file_path, water_user='', field_id='',
                start_year=None, end_year=None, kaf_begin=0, kaf_end=0):
    print('ocr_report: ', water_user + ', ' + field_id)
    image_file_paths = []
    for image_file_path in image_directory_path.iterdir():
        name = image_file_path.name
        if 'Revision' in name:
            pass
        elif name.endswith('.png'):
            image_file_paths.append(image_file_path)
    image_file_paths.sort()

    if start_year:
        tmp_paths = []
        for image_file_path in image_file_paths:
            year = year_from_file_path(image_file_path)
            if year >= start_year:
                tmp_paths.append(image_file_path)
        image_file_paths = tmp_paths

    if end_year:
        tmp_paths = []
        for image_file_path in image_file_paths:
            year = year_from_file_path(image_file_path)
            if year <= end_year:
                tmp_paths.append(image_file_path)
        image_file_paths = tmp_paths

    if len(image_file_paths):
        output_path = Path(Path(output_file_path).parent)
        output_path.mkdir(parents=True, exist_ok=True)
        f = output_file_path.open(mode='w')
        f.write('# USBR Lower Colorado Basin Annual reports: ' + water_user + ' ' + field_id + '\n')
        f.write('Year Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec Total\n')

        year_prev = int(re.split(r'\D+', image_file_paths[0].name)[0])
        year_written = 0
        for image_file_path in image_file_paths:
            year = int(re.split(r'\D+', image_file_path.name)[0])

            if year == year_written:
                continue
            elif year != year_prev:
                if not year_written:
                    print('\t', year_prev)
                    f.write(str(year_prev) + '\n')
                year_prev = year
            year_written = ocr_image_file(image_file_path, water_user, field_id, f, kaf_begin, kaf_end)

        f.close()
    else:
        print("No image files to process", image_directory_path, water_user, field_id)


def scavenge_ca(image_dir, out_path):
    image_path = image_dir.joinpath('ca/consumptive_use')

    output_path = out_path.joinpath('ca/usbr_ca_metropolitan_slrsp.csv')
    ocr_reports(image_path, output_path, water_user='Metropolitan Water District', field_id='SLRSP',
                start_year=2000, end_year=2006)

    output_path = out_path.joinpath('ca/usbr_ca_metropolitan_supplemental.csv')
    ocr_reports(image_path, output_path, water_user='Metropolitan Water District', field_id='Supplemental',
                start_year=2007, end_year=2008)

    # FIXME Run "Returns from Yuma Project" "FORT MOJAVE INDIAN RESERVATION""AGRICULTURAL - RIVER PUMPS"
    # FIXME "COLORADO RIVER INDIAN RESERVATION""Wells and pumps"
    # CA Total
    # In 2000's this turns into 'Unassigned Yuma Project Reservation Division Measured Returns'
    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_returns.csv')
    ocr_reports(image_path, output_path, water_user='Reservation Division', field_id='Return')

    # Small 'Returns' and 'cu' show up around 1982 under indian and bard on top of overall Reservation return above
    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_bard_unit_returns.csv')
    ocr_reports(image_path, output_path, water_user='Bard Unit', field_id='Returns')

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_indian_measured_returns.csv')
    ocr_reports(image_path, output_path, water_user='Indian Unit', field_id='Measured')

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_bard_measured_returns.csv')
    ocr_reports(image_path, output_path, water_user='Bard Unit', field_id='Measured')

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_indian_unmeasured_returns.csv')
    ocr_reports(image_path, output_path, water_user='Indian Unit', field_id='Unmeasured')

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_bard_unmeasured_returns.csv')
    ocr_reports(image_path, output_path, water_user='Bard Unit', field_id='Uneasured')

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_indian_unit_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Indian Unit', field_id='Diversion')

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_bard_unit_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Bard Unit', field_id='Diversion')

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_consumptive_use.csv')
    ocr_reports(image_path, output_path, field_id='Yuma Project Reservation Division Consumptive Use')

    output_path = out_path.joinpath('ca/usbr_ca_total_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='California Totals', field_id='Consumptive Us')

    output_path = out_path.joinpath('ca/usbr_ca_total_diversion.csv')
    ocr_reports(image_path, output_path, water_user='California Totals', field_id='Diversion')

    # "Measured" Returns in new reports, "Returns" in older reports
    output_path = out_path.joinpath('ca/usbr_ca_total_measured_returns.csv')
    ocr_reports(image_path, output_path, water_user='California Totals', field_id='Measured Returns')

    # Only in newer reports, how do you count 'Unmeasured Returns'?
    output_path = out_path.joinpath('ca/usbr_ca_total_unmeasured_returns.csv')
    ocr_reports(image_path, output_path, water_user='California Totals', field_id='Unmeasured Returns')

    # CA Agriculture
    output_path = out_path.joinpath('ca/usbr_ca_imperial_irrigation_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Imperial Irrigation District', field_id='Diversion')

    # False match 2012-2016 on 'DELIVERY FROM WARREN H. BROCK RESERVOIR ® CONSUMPTIVE USE'
    # In these cases in 2012-2016 use 'ID TOTAL CONSUMPTIVE USE'
    output_path = out_path.joinpath('ca/usbr_ca_imperial_irrigation_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Imperial Irrigation District', field_id='Consumptive Us')

    output_path = out_path.joinpath('ca/ca/usbr_ca_imperial_irrigation_brock.csv')
    ocr_reports(image_path, output_path, water_user='Brock Reservoir', field_id='Consumptive Us')

    output_path = out_path.joinpath('ca/usbr_ca_palo_verde_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Palo Verde Irrigation', field_id='Diversion')

    output_path = out_path.joinpath('ca/usbr_ca_palo_verde_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Palo Verde Irrigation', field_id='Consumptive Us')

    output_path = out_path.joinpath('ca/usbr_ca_coachella_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Coachella Valley', field_id='Diversion')

    output_path = out_path.joinpath('ca/usbr_ca_coachella_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Coachella Valley', field_id='Consumptive Us')

    # Yuma project has two water users, Indian and Bard
    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Project Reservation', field_id='Diversion')

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Project Reservation', field_id='Consumptive Us')

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_returns.csv')
    ocr_reports(image_path, output_path, water_user='Returns from Yuma Project', field_id='Return')

    # Municipal
    output_path = out_path.joinpath('ca/usbr_ca_metropolitan_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Metropolitan Water District', field_id='Diversion')

    output_path = out_path.joinpath('ca/usbr_ca_metropolitan_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Metropolitan Water District', field_id='Consumptive Us',
                start_year=1977)  # small returns in 1964 being ignored

    output_path = out_path.joinpath('ca/usbr_ca_needles_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Needles', field_id='Diversion')

    output_path = out_path.joinpath('ca/usbr_ca_blythe_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Blythe', field_id='Diversion')

    # Pumping
    output_path = out_path.joinpath('ca/usbr_ca_users_pumping_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Users Pumping', field_id='Diversion')

    # Fort Mohave Indian
    # Yuma Project Reservation Division
    # Bard Unit
    # Sum of Diversions for FYIR Ranches in California
    # Yuma Island


def scavenge_az(image_dir, out_path):
    image_path = image_dir.joinpath('az/consumptive_use')
    # Sturges, Warren Act 1995-1996 at least
    # Hopi

    # Sturges, Warren Act
    output_path = out_path.joinpath('az/usbr_az_sturges_warren_act_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Sturges', field_id='Consumptive Us', start_year=1993, end_year=2000)

    output_path = out_path.joinpath('az/usbr_az_sturges_warren_act_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Sturges', field_id='Diversion', start_year=1990, end_year=2000)

    # FIXME, Warren Act contractor diversions in 1964, at least

    output_path = out_path.joinpath('az/usbr_az_central_arizona_project_snwa_diversion.csv')
    # Can be "Central Arizona Project or  "Central Arizona Water Conservation District" ie 2021
    ocr_reports(image_path, output_path, water_user='Central Arizona', field_id='snwa', start_year=2004, end_year=2006)

    output_path = out_path.joinpath('az/usbr_az_gila_monster_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Gila Monster', field_id='Consumptive Us', start_year=2001)

    output_path = out_path.joinpath('az/usbr_az_bullhead_city_davis_dam_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Bullhead City', field_id='Davis Dam',
                start_year=1991, end_year=2013)

    # Also Yuma East Wetlands
    output_path = out_path.joinpath('az/usbr_az_city_of_yuma_ggmc_diversion.csv')
    ocr_reports(image_path, output_path, water_user='city of yuma', field_id='ggmc', start_year=1991)

    output_path = out_path.joinpath('az/usbr_az_city_of_yuma_gila_diversion.csv')
    ocr_reports(image_path, output_path, water_user='city of yuma', field_id='gila', start_year=1991)

    output_path = out_path.joinpath('az/usbr_az_crit_pumped_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Colorado River Indian', field_id='pump')

    output_path = out_path.joinpath('az/usbr_az_yuma_county_wua_pumped_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma County Water User', field_id='pump')

    output_path = out_path.joinpath('az/usbr_az_havasu_national_well_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Havasu National', field_id='Well', start_year=2008, end_year=2013)

    output_path = out_path.joinpath('az/usbr_az_havasu_national_topock_inlet_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Havasu National', field_id='Inlet', start_year=2005)

    output_path = out_path.joinpath('az/usbr_az_havasu_national_farm_ditch_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Havasu National', field_id='Farm Ditch', start_year=2005)

    output_path = out_path.joinpath('az/usbr_az_havasu_national_pumped_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Havasu National', field_id='Pump', start_year=2003)

    output_path = out_path.joinpath('az/usbr_az_havasu_national_measured_returns.csv')
    ocr_reports(image_path, output_path, water_user='Havasu National', field_id='Meas', start_year=2003)

    output_path = out_path.joinpath('az/usbr_az_havasu_national_unmeasured_returns.csv')
    ocr_reports(image_path, output_path, water_user='Havasu National', field_id='Unmeas', start_year=2003)

    # These need CU and returns
    # Marine Corps Air Station Yuma
    output_path = out_path.joinpath('az/usbr_az_marine_corp_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Marine Corps', field_id='Diversion', start_year=1983)

    # Town of Parker
    output_path = out_path.joinpath('az/usbr_az_town_of_parker_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Town of Parker', field_id='Diversion')

    # Gila Monster
    output_path = out_path.joinpath('az/usbr_az_gila_monster_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Gila Monster', field_id='Diversion', start_year=2001)

    # AZ Totals
    output_path = out_path.joinpath('az/usbr_az_total_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Arizona Totals', field_id='Diversion')

    output_path = out_path.joinpath('az/usbr_az_total_measured_returns.csv')
    ocr_reports(image_path, output_path, water_user='Arizona Totals', field_id='Measured Returns')

    output_path = out_path.joinpath('az/usbr_az_total_unmeasured_returns.csv')
    ocr_reports(image_path, output_path, water_user='Arizona Totals', field_id='Unmeasured Returns')

    output_path = out_path.joinpath('az/usbr_az_total_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Arizona Totals', field_id='Consumptive Us')

    # CAP
    output_path = out_path.joinpath('az/usbr_az_central_arizona_project_diversion.csv')
    # Can be "Central Arizona Project or  "Central Arizona Water Conservation District" ie 2021
    ocr_reports(image_path, output_path, water_user='Central Arizona', field_id='Diversion')

    # Wellton Mohawk
    output_path = out_path.joinpath('az/usbr_az_wellton_mohawk_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Wellton', field_id='Diversion')

    output_path = out_path.joinpath('az/usbr_az_wellton_mohawk_measured_returns.csv')
    # Some years this is "Total Meas. Returns" or "Returns Total"
    ocr_reports(image_path, output_path, water_user='Wellton', field_id='Total Returns')

    output_path = out_path.joinpath('az/usbr_az_wellton_mohawk_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Wellton', field_id='Consumptive Us')

    # Crit
    output_path = out_path.joinpath('az/usbr_az_crit_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Colorado River Indian', field_id='Diversion')

    output_path = out_path.joinpath('az/usbr_az_crit_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Colorado River Indian', field_id='Consumptive Us')

    # Cibola National Wildlife Refuge
    output_path = out_path.joinpath('az/usbr_az_cibola_national_wildlife_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Cibola National', field_id='Diversion', start_year=1976)

    output_path = out_path.joinpath('az/usbr_az_cibola_national_wildlife_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Cibola National', field_id='Consumptive Us', start_year=1987)

    # Cibola Valley IID
    output_path = out_path.joinpath('az/usbr_az_cibola_valley_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Cibola Valley', field_id='Diversion', start_year=1983)

    output_path = out_path.joinpath('az/usbr_az_cibola_valley_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Cibola Valley', field_id='Consumptive Us', start_year=2003)
    # Mohave County Water Authority Diversion
    # Hopi Tribe Diversion
    # Arizona Recreational Facilities Diversion
    # Arizona Game and Fish Diversion

    # Yuma Mesa
    output_path = out_path.joinpath('az/usbr_az_yuma_mesa_irrigation_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Mesa I', field_id='Diversion')

    output_path = out_path.joinpath('az/usbr_az_yuma_mesa_irrigation_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Mesa I', field_id='Consumptive Us')

    output_path = out_path.joinpath('az/usbr_az_yuma_mesa_irrigation_unmeas_returns.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Mesa I', field_id='Unmeas. Return', start_year=2003,
                end_year=2009)

    output_path = out_path.joinpath('az/usbr_az_yuma_mesa_irrigation_meas_returns.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Mesa I', field_id='Meas. Return', start_year=2003,
                end_year=2009)

    output_path = out_path.joinpath('az/usbr_az_yuma_mesa_irrigation_measured_returns.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Mesa I', field_id='Measured Return', start_year=2010)

    output_path = out_path.joinpath('az/usbr_az_yuma_mesa_irrigation_unmeasured_returns.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Mesa I', field_id='Unmeasured Return', start_year=2010)

    output_path = out_path.joinpath('az/usbr_az_yuma_mesa_irrigation_returns.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Mesa I', field_id='Return', start_year=1983, end_year=2002)

    output_path = out_path.joinpath('az/usbr_az_yuma_mesa_outlet_drain_returns.csv')
    ocr_reports(image_path, output_path, water_user='', field_id='yuma mesa outlet drain', end_year=1983)

    # Yuma County Water Users Association
    output_path = out_path.joinpath('az/usbr_az_yuma_county_wua_pumped_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma County Water User', field_id='pump')

    output_path = out_path.joinpath('az/usbr_az_yuma_county_wua_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma County Water User', field_id='Diversion')

    output_path = out_path.joinpath('az/usbr_az_yuma_county_wua_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Yuma County Water User', field_id='Consumptive Us')

    output_path = out_path.joinpath('az/usbr_az_yuma_county_wua_pumped_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma County Water User', field_id='Pumped from wells',
                start_year=1966)

    # Yuma Irrigation
    output_path = out_path.joinpath('az/usbr_az_yuma_irrigation_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Irrigation', field_id='Diversion', start_year=1965)

    output_path = out_path.joinpath('az/usbr_az_yuma_irrigation_pumped_diversion.csv', start_year=1967)
    ocr_reports(image_path, output_path, water_user='Yuma Irrigation', field_id='pump')

    output_path = out_path.joinpath('az/usbr_az_yuma_irrigation_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Irrigation', field_id='Consumptive Us', start_year=1983)

    output_path = out_path.joinpath('az/usbr_az_yuma_irrigation_return.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Irrigation', field_id='Return',
                start_year=1983, end_year=2002)
    # FIXME Meas. and Unmeas. returns start 2003, with pumped it gets complicated

    # Unit B
    output_path = out_path.joinpath('az/usbr_az_unit_b_no_quotes_irrigation_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Unit B', field_id='Consumptive Us')

    output_path = out_path.joinpath('az/usbr_az_unit_b_irrigation_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Unit \"B\"', field_id='Consumptive Us')

    output_path = out_path.joinpath('az/usbr_az_unit_b_no_quotes_irrigation_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Unit B', field_id='Diversion', start_year=1977)

    output_path = out_path.joinpath('az/usbr_az_unit_b_irrigation_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Unit \"B\"', field_id='diversion')

    # North & South Gila
    output_path = out_path.joinpath('az/usbr_az_north_gila_irrigation_diversion.csv')
    ocr_reports(image_path, output_path, water_user='North Gila', field_id='Diversion')

    output_path = out_path.joinpath('az/usbr_az_north_gila_irrigation_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='North Gila', field_id='Consumptive Us')

    # South Gila area, Yuma Mesa, Yuma Irrigation, Unit B jumbled together
    # Also 'Returns from South Gila"
    output_path = out_path.joinpath('az/usbr_az_south_gila_returns.csv')
    ocr_reports(image_path, output_path, water_user='', field_id='returns from south gila', end_year=1982)

    output_path = out_path.joinpath('az/usbr_az_yuma_mesa_outlet_drain.csv')
    ocr_reports(image_path, output_path, water_user='', field_id='yuma mesa outlet drain',
                start_year=1982, end_year=1982)

    output_path = out_path.joinpath('az/usbr_az_south_gila_well_return.csv')
    ocr_reports(image_path, output_path, water_user='', field_id='south gila wells', start_year=1983, end_year=2004)

    # This catches everything, not sure this works
    output_path = out_path.joinpath('az/usbr_az_south_gila.csv')
    ocr_reports(image_path, output_path, water_user='', field_id='south gila')

    # Cocopah
    output_path = out_path.joinpath('az/usbr_az_cocopah_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Cocopah Indian R', field_id='Diversion')

    output_path = out_path.joinpath('az/usbr_az_cocopah_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Cocopah Indian R', field_id='Consumptive Us', start_year=1984)

    output_path = out_path.joinpath('az/usbr_az_cocopah_returns.csv')
    ocr_reports(image_path, output_path, water_user='Cocopah Indian R', field_id='Return', start_year=1984)

    output_path = out_path.joinpath('az/usbr_az_cocopah_pumped.csv')
    ocr_reports(image_path, output_path, water_user='Cocopah Indian R', field_id='Pumped')

    output_path = out_path.joinpath('az/usbr_az_cocopah_west_pumped.csv')
    ocr_reports(image_path, output_path, water_user='Cocopah Indian R', field_id='West Cocopah', start_year=1997)

    output_path = out_path.joinpath('az/usbr_az_cocoapah_west_pumped.csv')  # Misspelled
    ocr_reports(image_path, output_path, water_user='Cocopah Indian R', field_id='West Cocoapah', start_year=1999)

    output_path = out_path.joinpath('az/usbr_az_cocopah_north_pumped.csv')
    ocr_reports(image_path, output_path, water_user='Cocopah Indian R', field_id='North Cocopah', start_year=1997)

    # Pumping
    output_path = out_path.joinpath('az/usbr_az_other_users_pumping_diversion.csv')
    ocr_reports(image_path, output_path, water_user='other users pumping', field_id='diversion', end_year=2015)

    output_path = out_path.joinpath('az/usbr_az_other_users_pumping_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='other users pumping', field_id='Consumptive Us',
                start_year=2003, end_year=2015)

    output_path = out_path.joinpath('az/usbr_az_via_pumps_diversion.csv')
    ocr_reports(image_path, output_path, water_user='via pumps', field_id='diversion',
                start_year=2014, end_year=2015)  # Bureau started listing individual users in 2016...sigh

    # Fort Mohave
    output_path = out_path.joinpath('az/usbr_az_fort_mohave_indian_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Fort Mohave', field_id='Diversion', start_year=1975, end_year=1998)

    output_path = out_path.joinpath('az/usbr_az_fort_mojave_indian_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Fort Mojave', field_id='Diversion', start_year=1999)

    output_path = out_path.joinpath('az/usbr_az_fort_mojave_indian_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Fort Mojave', field_id='Consumptive Us', start_year=2000)

    # Mohave Valley
    output_path = out_path.joinpath('az/usbr_az_mohave_valley_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Mohave Valley', field_id='Diversion', start_year=1975)

    output_path = out_path.joinpath('az/usbr_az_mohave_valley_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Mohave Valley', field_id='Consumptive Us', start_year=1975)

    # GM Gabrych
    output_path = out_path.joinpath('az/usbr_az_gabrych_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Gabrych', field_id='Diversion', start_year=2018)

    output_path = out_path.joinpath('az/usbr_az_gabrych_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Gabrych', field_id='Consumptive Us', start_year=2018)

    # Arizona Game and Fish
    output_path = out_path.joinpath('az/usbr_az_arizona_game_and_fish_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Arizona Game', field_id='Diversion', start_year=2013)

    output_path = out_path.joinpath('az/usbr_az_arizona_game_and_fish_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Arizona Game', field_id='Consumptive Us', start_year=2013)

    # Arizona State Land Development
    output_path = out_path.joinpath('az/usbr_az_arizona_state_land_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Arizona State Land', field_id='Diversion', start_year=2013)

    output_path = out_path.joinpath('az/usbr_az_arizona_state_land_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Arizona State Land', field_id='Consumptive Us', start_year=2013)

    # Havasu National Wildlife Reguge, "Havasu Lake National" until 1967 1/2
    output_path = out_path.joinpath('az/usbr_az_havasu_national_wildlife_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Havasu National', field_id='Diversion', start_year=1969)

    output_path = out_path.joinpath('az/usbr_az_havasu_national_wildlife_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Havasu National', field_id='Consumptive Us', start_year=1987)

    output_path = out_path.joinpath('az/usbr_az_havasu_national_wildlife_returns.csv')
    ocr_reports(image_path, output_path, water_user='Havasu National', field_id='Return', start_year=1990)

    # Doesnt work
    output_path = out_path.joinpath('az/usbr_az_havasu_lake_wildlife_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Havasu Lake', field_id='Diversion', end_year=1968)

    # Lake Havasu
    output_path = out_path.joinpath('az/usbr_az_lake_havasu_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Lake Havasu', field_id='Diversion', start_year=1969)

    output_path = out_path.joinpath('az/usbr_az_lake_havasu_consumptive_use.csv')  # really starts in 2003
    ocr_reports(image_path, output_path, water_user='Lake Havasu', field_id='Consumptive Us', start_year=1987)

    # Bullhead City
    output_path = out_path.joinpath('az/usbr_az_bullhead_city_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Bullhead City', field_id='Diversion', start_year=1987)

    output_path = out_path.joinpath('az/usbr_az_bullhead_city_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Bullhead City', field_id='Consumptive Us', start_year=1987)

    # Imperial National Wildlife Refuge, record is spotty especially pre 1991, some years have total only
    output_path = out_path.joinpath('az/usbr_az_imperial_national_wildlife_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Imperial National', field_id='Diversion', start_year=1983)

    output_path = out_path.joinpath('az/usbr_az_imperial_national_wildlife_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Imperial National', field_id='Consumptive Us', start_year=2003)

    # City of Yuma
    # Second diversion from gila around 1995
    output_path = out_path.joinpath('az/usbr_az_city_of_yuma_diversion.csv')
    ocr_reports(image_path, output_path, water_user='city of yuma', field_id='diversion')

    output_path = out_path.joinpath('az/usbr_az_city_of_yuma_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='city of yuma', field_id='Consumptive Us')

    # Mohave Water Conservation District
    # Hopi Tribe
    # Fort Yuma Indian
    # Golden Shores WCD
    # Ehrenburg Improvement Association
    # Sturges diversion at Imperial Dam
    # University of Arizona
    # Camille
    # Desert Lawn
    # Southern Pacific
    # Yuma Mesa Fruit growers
    # Yuma Area Office, USBR
    # Brooke Water
    # Lower Colorado River Dams Project
    # Lake Mead National Recreation Area, Lake Mead
    # Lake Mead National Recreation Area, Lake Mohave
    # Yuma Proving Ground


def scavenge_nv(image_dir, out_path):
    image_path = image_dir.joinpath('nv/consumptive_use')
    # FIXME Run "CITY OF HENDERSON" "Basic Management"
    output_path = out_path.joinpath('nv/usbr_nv_total_measured_returns.csv')
    ocr_reports(image_path, output_path, water_user='Nevada Totals', field_id='Measured Returns')

    output_path = out_path.joinpath('nv/usbr_nv_total_unmeasured_returns.csv')
    ocr_reports(image_path, output_path, water_user='Nevada Totals', field_id='Unmeasured Returns')

    output_path = out_path.joinpath('nv/usbr_nv_total_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Nevada Totals', field_id='Diversion')

    output_path = out_path.joinpath('nv/usbr_nv_total_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Nevada Totals', field_id='Consumptive Us')

    output_path = out_path.joinpath('nv/usbr_nv_snwa_griffith_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Griffith Water Project', field_id='Diversion', start_year=1984)

    # Las Valley Water District Changed to Robert B. Griffith in 1984
    output_path = out_path.joinpath('nv/usbr_nv_las_vegas_valley_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Las Vegas Valley Water District', field_id='Diversion',
                end_year=1983)

    output_path = out_path.joinpath('nv/usbr_nv_las_vegas_wash_diversion.csv')
    ocr_reports(image_path, output_path,  water_user='Las Vegas Wash', field_id='Returns')

    output_path = out_path.joinpath('nv/usbr_nv_henderson_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Henderson', field_id='Diversion')

    output_path = out_path.joinpath('nv/usbr_nv_basic_water_company_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Basic Water Company', field_id='Diversion')

    output_path = out_path.joinpath('nv/usbr_nv_fort_mojave_indian_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Fort Mojave Indian', field_id='Diversion')

    output_path = out_path.joinpath('nv/usbr_nv_big_bend_water_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Big Bend Water', field_id='Diversion')

    # Lake Havasu Irrigation and Drainage in the 80's at least
    # Bureau of Reclamation
    # Lake Mead National Recreational Area
    # Big Bend Conservation Area
    # Pacific Coast Building Products

    # Local aquifer storage
    # Las Vegas Valley Water District
    # City of North Las Vegas


def scavenge_mx(image_dir, out_path):
    image_path = image_dir.joinpath('mx')

    output_path = out_path.joinpath('mx/usbr_mx_cienega.csv')
    # Some years use 'Minute No. 319'
    ocr_reports(image_path, output_path, field_id='Cienega')

    output_path = out_path.joinpath('mx/usbr_mx_minute_319_bypass.csv')
    # Some years use 'Minute No. 319'
    ocr_reports(image_path, output_path, field_id='Minute 319')

    output_path = out_path.joinpath('mx/usbr_mx_minute_242_bypass.csv')
    # Some years use 'Minute No 242'
    ocr_reports(image_path, output_path, field_id='Minute 242')

    output_path = out_path.joinpath('mx/usbr_mx_deferred_delivery.csv')
    ocr_reports(image_path, output_path,  field_id='Mexico\'s Deferred Delivery')
    output_path = out_path.joinpath('mx/usbr_mx_creation_of_reserve.csv')
    ocr_reports(image_path, output_path,  field_id='Creation of Mexico\'s Water Reserve')

    output_path = out_path.joinpath('mx/usbr_mx_delivery_of_reserve.csv')
    ocr_reports(image_path, output_path,  field_id='Delivery of Mexico\'s Water Reserve')

    output_path = out_path.joinpath('mx/usbr_mx_creation_of_recoverable.csv')
    ocr_reports(image_path, output_path,  field_id='Creation of Mexico\'s Recoverable ')

    output_path = out_path.joinpath('mx/usbr_mx_northern_international_boundary.csv')
    # ocr_reports(image_path, output_path,  field_id='Northerly International')
    ocr_reports(image_path, output_path,  field_id='NIB')

    output_path = out_path.joinpath('mx/usbr_mx_southern_international_boundary.csv')
    # ocr_reports(image_path, output_path, field_id='Southerly International')
    ocr_reports(image_path, output_path, field_id='SIB')

    output_path = out_path.joinpath('mx/usbr_mx_tijuana.csv')
    ocr_reports(image_path, output_path, field_id='Tijuana')

    output_path = out_path.joinpath('mx/usbr_mx_satisfaction_of_treaty.csv')
    # 1990-1996 = 1500000, 1997-2000 = 1700000, 2001-2006=1500000
    ocr_reports(image_path, output_path, field_id='To Mexico As Scheduled')
    # ocr_reports(image_path, output_path, water_user='', field_id='Satisfaction of Treaty')

    output_path = out_path.joinpath('mx/usbr_mx_limitrophe.csv')
    ocr_reports(image_path, output_path, field_id='Limitrophe')

    output_path = out_path.joinpath('mx/usbr_mx_in_excess.csv')
    ocr_reports(image_path, output_path, field_id='In Excess')


def scavenge_releases(image_dir, out_path):
    image_path = image_dir.joinpath('releases')

    # Numbers are in kaf from 1990 to 2002ish

    output_path = out_path.joinpath('releases/usbr_releases_glen_canyon_dam.csv')
    ocr_reports(image_path, output_path, field_id='Glen Canyon Dam', kaf_begin=1990, kaf_end=2002)

    output_path = out_path.joinpath('releases/usbr_releases_hoover_dam.csv')
    ocr_reports(image_path, output_path, field_id='Hoover Dam', kaf_begin=1990, kaf_end=2002)

    output_path = out_path.joinpath('releases/usbr_releases_davis_dam.csv')
    ocr_reports(image_path, output_path, field_id='Davis Dam', kaf_begin=1990, kaf_end=2002)

    output_path = out_path.joinpath('releases/usbr_releases_parker_dam.csv')
    ocr_reports(image_path, output_path, field_id='Parker Dam', kaf_begin=1990, kaf_end=2002)

    output_path = out_path.joinpath('releases/usbr_releases_rock_dam.csv')
    ocr_reports(image_path, output_path, field_id='Rock Dam', kaf_begin=1990, kaf_end=2002)

    output_path = out_path.joinpath('releases/usbr_releases_palo_verde_dam.csv')
    ocr_reports(image_path, output_path, field_id='Palo Verde', kaf_begin=1990, kaf_end=2002)
    # Mittry Lake needs to be added to Imperial in 2000's
    output_path = out_path.joinpath('releases/usbr_releases_imperial_dam.csv')
    ocr_reports(image_path, output_path, field_id='Imperial Dam', kaf_begin=1990, kaf_end=2002)

    output_path = out_path.joinpath('releases/usbr_releases_laguna_dam.csv')
    ocr_reports(image_path, output_path, field_id='Laguna Dam', kaf_begin=1990, kaf_end=2002)


def ocr_print(image_file_path):
    try:
        text = image_to_text(image_file_path)
        text = text.replace(',', '')
        print(text)

        fig, ax = plt.subplots(nrows=1, ncols=1)
        fig.set_figwidth(60)
        fig.set_figheight(15)
        ax.set_title(image_file_path)
        ax.set_xlabel('')
        ax.set_ylabel('')

        image = mpimg.imread(image_file_path)
        ax.imshow(image)
        plt.show()

    except FileNotFoundError:
        print("File not found: ", str(image_file_path))


def ocr_debug(image_dir, path1='ca', path2=''):
    image_path = image_dir.joinpath(path1 + path2)
    while 1:
        print("Enter image name:")
        image_name = input()
        png_name = image_name + '.png'
        if len(png_name):
            png_path = image_path.joinpath(png_name)
            print("Image path ", png_path)
            ocr_print(png_path)
        else:
            break


if __name__ == '__main__':
    image_directory = Path('/ark/Varuna/USBR_Reports/images/')
    outputs_path = Path('/opt/dev/riverwar/data/USBR_Reports/generated')
    ocr_debug(image_directory, path1='az', path2='/consumptive_use')
    # ocr_debug(image_directory, path1='releases')
    scavenge_az(image_directory, outputs_path)
    scavenge_ca(image_directory, outputs_path)
    scavenge_releases(image_directory, outputs_path)
    scavenge_nv(image_directory, outputs_path)
    scavenge_mx(image_directory, outputs_path)
