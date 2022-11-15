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


def ocr_report(image_file_path, f, water_user='', field_id='', loop=None, kaf_begin=None, kaf_end=None):
    water_user_lower = water_user.lower()
    field_id_lower = field_id.lower()
    year = year_from_file_path(image_file_path)

    text = image_to_text(image_file_path)
    strings = text.split('\n')
    look_for_diversion = False
    looping = False
    for string in strings:
        if not water_user_lower or water_user_lower in string.lower():
            look_for_diversion = True
        if look_for_diversion:
            string_lower = string.lower()
            if looping and loop in string_lower:
                return year, False
            elif field_id_lower in string_lower or looping:
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
                    # FIXME, Needs to be higher on cleaned data, lower on new OCR data
                    if len(values) > 1:
                        year = process_line_item(year, result, image_file_path, f, kaf_begin, kaf_end)
                        if not loop:
                            return year, False
                        else:
                            looping = True
                    elif len(values) > 1:
                        print("Number of fields came up short: ", len(values))
                else:
                    break

    return None, False


def ocr_image_file(image_file_path, f, water_user, field_id, loop, kaf_begin=0, kaf_end=0):
    return ocr_report(image_file_path, f, water_user, field_id, loop, kaf_begin, kaf_end)


def process_line_item(year, data, image_file_path, f, kaf_begin, kaf_end):
    error_tolerance = 2  # af error allowed between summation of months and annual total

    print_file_name_prefix = '\t' + image_file_path.name + ': '
    if year and year > 1900 and len(data) > 0:
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
                start_year=None, end_year=None, loop=None, kaf_begin=0, kaf_end=0):
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
            year_written, looping = ocr_image_file(image_file_path, f, water_user, field_id, loop, kaf_begin, kaf_end)

        f.close()
    else:
        print("No image files to process", image_directory_path, water_user, field_id)


def scavenge_ca(image_dir, out_path):
    image_path = image_dir.joinpath('ca/consumptive_use')
    #
    output_path = out_path.joinpath('ca/usbr_ca_williams_jerry_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Williams, Jerry', field_id='Diversion',
                start_year=2016, end_year=2019)

    output_path = out_path.joinpath('ca/usbr_ca_williams_jerry_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Williams, Jerry', field_id='Consumptive Us',
                start_year=2016, end_year=2019)

    output_path = out_path.joinpath('ca/usbr_ca_wetmore_kenneth_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Wetmore, Kenneth', field_id='Diversion',
                start_year=2016, end_year=2019)

    output_path = out_path.joinpath('ca/usbr_ca_wetmore_kenneth_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Wetmore, Kenneth', field_id='Consumptive Us',
                start_year=2016, end_year=2019)

    output_path = out_path.joinpath('ca/usbr_ca_wetmore_mark_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Wetmore, Mark', field_id='Diversion',
                start_year=2016, end_year=2019)

    output_path = out_path.joinpath('ca/usbr_ca_wetmore_mark_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Wetmore, Mark', field_id='Consumptive Us',
                start_year=2016, end_year=2019)

    output_path = out_path.joinpath('ca/usbr_ca_parker_dam_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Parker Dam and Gov', field_id='Diversion',
                start_year=1972, end_year=2013)

    output_path = out_path.joinpath('ca/usbr_ca_bureau_of_reclamation_parker_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Bureau of Reclamation - Parker Dam', field_id='Diversion',
                start_year=2017)

    output_path = out_path.joinpath('ca/usbr_ca_bureau_of_reclamation_parker_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Bureau of Reclamation - Parker Dam', field_id='Consumptive Us',
                start_year=2017)

    # Yuma project has two water users, Indian and Bard
    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_indian_unit_domestic_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Project Reservation',
                start_year=2014, field_id='Pumped from wells for domestic use')

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Project Reservation', field_id='Consumptive Us')

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_returns.csv')
    ocr_reports(image_path, output_path, water_user='Returns from Yuma Project', field_id='Return')

    # Dont think this is used, yuma_project_sum_consumptive_use instead
    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_indian_unit_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Indian Unit', field_id='Consumptive Us',
                start_year=1984, end_year=1989)

    # Dont think this is used, yuma_project_sum_consumptive_use instead
    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_bard_unit_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Bard Unit', field_id='Consumptive Us',
                start_year=1984, end_year=1989)

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_total_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Total Yuma Project Reservation Division',
                field_id='Consumptive Us', start_year=2014)

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_sum_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='RETURNS FROM YUMA PROJECT', field_id='Consumptive Us',
                start_year=1990)

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_sum_returns.csv')
    ocr_reports(image_path, output_path, water_user='RETURNS FROM YUMA PROJECT', field_id='Return')

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
    ocr_reports(image_path, output_path, water_user='Bard Unit', field_id='Unmeasured')

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_indian_unit_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Indian Unit', field_id='Diversion')

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_bard_unit_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Bard Unit', field_id='Diversion')

    output_path = out_path.joinpath('ca/usbr_ca_yuma_project_consumptive_use.csv')
    ocr_reports(image_path, output_path, field_id='Yuma Project Reservation Division Consumptive Use')

    output_path = out_path.joinpath('ca/usbr_ca_chemehuevi_domestic_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Chemehuevi', field_id='for domestic use', start_year=2018)

    output_path = out_path.joinpath('ca/usbr_ca_chemehuevi_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Chemehuevi', field_id='Consumptive Us', start_year=2003)

    output_path = out_path.joinpath('ca/usbr_ca_chemehuevi_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Chemehuevi', field_id='Diversion', start_year=1996)

    output_path = out_path.joinpath('ca/usbr_ca_bureau_of_land_management_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Bureau of Land Management', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_bureau_of_land_management_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Bureau of Land Management', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_lake_enterprises_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Lake Enterprises', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_lake_enterprises_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Lake Enterprises', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_non_federal_subcontractors_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Non-Federal Subcontractors to the LCWSP', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_non_federal_subcontractors_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Non-Federal Subcontractors to the LCWSP',
                field_id='Consumptive Us', start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_ppr_30_stephenson_diversion.csv')
    ocr_reports(image_path, output_path, water_user='PPR No. 30 (Stephenson)', field_id='Diversion',
                start_year=2020)

    output_path = out_path.joinpath('ca/usbr_ca_ppr_30_stephenson_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='PPR No. 30 (Stephenson)', field_id='Consumptive Us',
                start_year=2020)

    output_path = out_path.joinpath('ca/usbr_ca_ppr_38_andrade_diversion.csv')
    ocr_reports(image_path, output_path, water_user='PPR No. 38 (Andrade)', field_id='Diversion',
                start_year=2020)

    output_path = out_path.joinpath('ca/usbr_ca_ppr_38_andrade_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='PPR No. 38 (Andrade)', field_id='Consumptive Us',
                start_year=2020)

    output_path = out_path.joinpath('ca/usbr_ca_ppr_40_cooper_diversion.csv')
    ocr_reports(image_path, output_path, water_user='PPR No. 40 (Cooper)', field_id='Diversion',
                start_year=2021)

    output_path = out_path.joinpath('ca/usbr_ca_ppr_40_cooper_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='PPR No. 40 (Cooper)', field_id='Consumptive Us',
                start_year=2021)

    output_path = out_path.joinpath('ca/usbr_ca_vista_del_lago_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Vista Del Lago', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_havasu_water_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Havasu Water Company', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_havasu_water_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Havasu Water Company', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_pacific_gas_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Pacific Gas', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_pacific_gas_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Pacific Gas', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_southern_california_gas_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Southern California Gas', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_southern_california_gas_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Southern California Gas', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_imperial_irrigation_sdcwa_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Water Transferred to SDCWA', field_id='Consumptive Us',
                start_year=2004)

    output_path = out_path.joinpath('ca/usbr_ca_fort_yuma_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Fort Yuma', field_id='Consumptive Us', start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_fort_yuma_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Fort Yuma', field_id='Sum of Diversions for the FYIR Ranches',
                start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_winterhaven_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Winterhaven', field_id='Diversion')

    output_path = out_path.joinpath('ca/usbr_ca_bureau_of_land_management_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Bureau of Land Management', field_id='Diversion')

    output_path = out_path.joinpath('ca/usbr_ca_total_returns.csv')
    ocr_reports(image_path, output_path, water_user='California Totals', field_id='Return', end_year=2009)

    # East Blythe
    output_path = out_path.joinpath('ca/usbr_ca_east_blythe_diversion.csv')
    ocr_reports(image_path, output_path, water_user='East Blythe', field_id='Diversion', end_year=1978)

    output_path = out_path.joinpath('ca/usbr_ca_crit_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Colorado River Indian', field_id='Diversion', start_year=1973,
                loop='return')

    output_path = out_path.joinpath('ca/usbr_ca_fort_mojave_well_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Fort Mojave', field_id='wells',  start_year=2009)

    output_path = out_path.joinpath('ca/usbr_ca_yuma_island_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Island', field_id='Consumptive Use', start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_yuma_island_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Island', field_id='Diversion', start_year=2016)

    output_path = out_path.joinpath('ca/usbr_ca_fort_mojave_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Fort Mojave', field_id='Consumptive Us', start_year=1999)

    output_path = out_path.joinpath('ca/usbr_ca_crit_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Colorado River Indian', field_id='Consumptive Us', start_year=1987)

    output_path = out_path.joinpath('ca/usbr_ca_fort_mojave_pumped_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Fort Mojave', field_id='Pumped',  start_year=1999)

    output_path = out_path.joinpath('ca/usbr_ca_fort_mojave_needles_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Fort Mojave', field_id='Needles',  start_year=1999, end_year=2008)

    output_path = out_path.joinpath('ca/usbr_ca_fort_mohave_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Fort Mohave', field_id='Diversion',  start_year=1975)

    output_path = out_path.joinpath('ca/usbr_ca_metropolitan_for_snwa.csv')
    ocr_reports(image_path, output_path, water_user='Metropolitan Water District', field_id='SNWA',
                start_year=2004, end_year=2005)

    # City of Blythe
    output_path = out_path.joinpath('ca/usbr_ca_city_of_blythe_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Blythe', field_id='Diversion', end_year=1978)

    # City of Needles
    output_path = out_path.joinpath('ca/usbr_ca_city_of_needles_diversion.csv')
    ocr_reports(image_path, output_path, water_user='City of Needles', field_id='Diversion')

    output_path = out_path.joinpath('ca/usbr_ca_city_of_needles_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='City of Needles', field_id='Consumptive Us')

    output_path = out_path.joinpath('ca/usbr_ca_city_of_needles_returns.csv')
    ocr_reports(image_path, output_path, water_user='City of Needles', field_id='Returns')

    # Pumping
    output_path = out_path.joinpath('ca/usbr_ca_other_users_pumping_diversion.csv')
    ocr_reports(image_path, output_path, water_user='other users pumping', field_id='diversion', end_year=2015)

    output_path = out_path.joinpath('ca/usbr_ca_other_users_pumping_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='other users pumping', field_id='Consumptive Us',
                start_year=2003, end_year=2015)

    output_path = out_path.joinpath('ca/usbr_ca_via_pumps_diversion.csv')
    ocr_reports(image_path, output_path, water_user='via pumps', field_id='diversion',
                start_year=2014, end_year=2015)  # Bureau started listing individual users in 2016...sigh

    output_path = out_path.joinpath('ca/usbr_ca_metropolitan_slrsp.csv')
    ocr_reports(image_path, output_path, water_user='Metropolitan Water District', field_id='SLRSP',
                start_year=2000, end_year=2006)

    output_path = out_path.joinpath('ca/usbr_ca_metropolitan_supplemental.csv')
    ocr_reports(image_path, output_path, water_user='Metropolitan Water District', field_id='Supplemental',
                start_year=2007, end_year=2008)

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

    # Municipal
    output_path = out_path.joinpath('ca/usbr_ca_metropolitan_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Metropolitan Water District', field_id='Diversion')

    output_path = out_path.joinpath('ca/usbr_ca_metropolitan_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Metropolitan Water District', field_id='Consumptive Us',
                start_year=1977)  # small returns in 1964 being ignored

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
    # FIXME Havasu Wildlife pumps
    # FIXME Cibola Vally (Hopi, et al)
    # FIXME 1982 Protective and Regulatory Pumping Unit, Yuma Mesa Outlet Drain
    #
    output_path = out_path.joinpath('az/usbr_az_arizona_state_land_domestic_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Arizona State Land', field_id='domestic',
                start_year=2013)

    output_path = out_path.joinpath('az/usbr_az_arizona_state_land_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Arizona State Land', field_id='Diversion',
                start_year=2013)

    output_path = out_path.joinpath('az/usbr_az_arizona_state_land_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Arizona State Land', field_id='Consumptive Us', start_year=2013)

    output_path = out_path.joinpath('az/usbr_az_north_gila_irrigation_pumped_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Pumped from river', field_id='Diversion', start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_north_gila_irrigation_diversion.csv')
    ocr_reports(image_path, output_path, water_user='North Gila', field_id='Diversion')

    output_path = out_path.joinpath('az/usbr_az_north_gila_irrigation_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='North Gila', field_id='Consumptive Us')

    output_path = out_path.joinpath('az/usbr_az_gary_pasquinelli_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Gary Pasquinelli', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_gary_pasquinelli_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Gary Pasquinelli', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_arizona_public_service_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Arizona Public Service', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_arizona_public_service_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Arizona Public Service', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_griffin_family_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Griffin Family', field_id='Diversion',
                start_year=2018)

    output_path = out_path.joinpath('az/usbr_az_griffin_family_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Griffin Family', field_id='Consumptive Us',
                start_year=2018)

    output_path = out_path.joinpath('az/usbr_az_milton_phillips_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Milton Phillips', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_milton_phillips_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Milton Phillips', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_griffin_ranches_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Griffin Ranches', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_griffin_ranches_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Griffin Ranches', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_cocopah_ppr_7_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Cocopah Indian Tribe (PPR No. 7)', field_id='Diversion',
                start_year=2018)

    output_path = out_path.joinpath('az/usbr_az_cocopah_ppr_7_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Cocopah Indian Tribe (PPR No. 7)', field_id='Consumptive Us',
                start_year=2018)

    output_path = out_path.joinpath('az/usbr_az_power_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Power', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_power_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Power', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_r_griffin_diversion.csv')
    ocr_reports(image_path, output_path, water_user='R. Griffin', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_r_griffin_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='R. Griffin', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_armon_curtis_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Armon Curtis', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_armon_curtis_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Armon Curtis', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_ogram_boys_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Ogram Boys', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_ogram_boys_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Ogram Boys', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_ott_family_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Ott Family', field_id='Diversion',
                start_year=2018)

    output_path = out_path.joinpath('az/usbr_az_ott_family_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Ott Family', field_id='Consumptive Us',
                start_year=2018)

    output_path = out_path.joinpath('az/usbr_az_camille_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Camille', field_id='Diversion',
                start_year=1983, end_year=2010)

    output_path = out_path.joinpath('az/usbr_az_camille_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Camille', field_id='Consumptive Us',
                start_year=2003, end_year=2010)

    output_path = out_path.joinpath('az/usbr_az_desert_lawn_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Desert Lawn', field_id='Diversion',
                start_year=1983)

    output_path = out_path.joinpath('az/usbr_az_desert_lawn_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Desert Lawn', field_id='Consumptive Us',
                start_year=2003)

    output_path = out_path.joinpath('az/usbr_az_yuma_mesa_fruit_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Mesa Fruit', field_id='Consumptive Us',
                start_year=2003, end_year=2011)

    output_path = out_path.joinpath('az/usbr_az_yuma_mesa_fruit_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Mesa Fruit', field_id='Diversion',
                start_year=1983, end_year=2011)

    output_path = out_path.joinpath('az/usbr_az_union_pacific_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Union Pacific', field_id='Diversion',
                start_year=2008)

    output_path = out_path.joinpath('az/usbr_az_union_pacific_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Union Pacific', field_id='Consumptive Us',
                start_year=2008)

    output_path = out_path.joinpath('az/usbr_az_southern_pacific_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Southern Pacific', field_id='Diversion',
                start_year=1984, end_year=2009)

    output_path = out_path.joinpath('az/usbr_az_southern_pacific_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Southern Pacific', field_id='Consumptive Us',
                start_year=2003, end_year=2009)

    output_path = out_path.joinpath('az/usbr_az_beattie_farms_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Beattie Farms', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_beattie_farms_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Beattie Farms', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_cha_cha_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Cha Cha', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_cha_cha_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Cha Cha', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_jrj_partners_diversion.csv')
    ocr_reports(image_path, output_path, water_user='JRJ Partners', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_jrj_partners_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='JRJ Partners', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_shepard_water_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Shepard Water Company', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_shepard_water_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Shepard Water Company', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_fishers_landing_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Fisher\'s Landing', field_id='Diversion',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_fishers_landing_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Fisher\'s Landing', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_blm_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Bureau of Land Management', field_id='Diversion',
                start_year=2016, loop='Returns')

    output_path = out_path.joinpath('az/usbr_az_blm_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Bureau of Land Management', field_id='Consumptive Us',
                start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_cibola_island_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Cibola Island', field_id='Diversion', start_year=2017)

    output_path = out_path.joinpath('az/usbr_az_cibola_island_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Cibola Island', field_id='Consumptive Us',  start_year=2017)

    output_path = out_path.joinpath('az/usbr_az_gsc_farm_diversion.csv')
    ocr_reports(image_path, output_path, water_user='GSC Farm', field_id='Diversion', start_year=2013)

    output_path = out_path.joinpath('az/usbr_az_gsc_farm_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='GSC Farm', field_id='Consumptive Us',  start_year=2013)

    output_path = out_path.joinpath('az/usbr_az_western_water_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Western Water', field_id='Diversion', start_year=2018)

    output_path = out_path.joinpath('az/usbr_az_western_water_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Western Water', field_id='Consumptive Us',  start_year=2018)

    output_path = out_path.joinpath('az/usbr_az_red_river_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Red River', field_id='Diversion', start_year=2018)

    output_path = out_path.joinpath('az/usbr_az_red_river_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Red River', field_id='Consumptive Us',  start_year=2018)

    output_path = out_path.joinpath('az/usbr_az_north_baja_pipeline_diversion.csv')
    ocr_reports(image_path, output_path, water_user='North Baja Pipeline', field_id='Diversion', start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_north_baja_pipeline_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='North Baja Pipeline', field_id='Consumptive Us',  start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_b_and_f_investment_diversion.csv')
    ocr_reports(image_path, output_path, water_user='B&F Investment', field_id='Diversion', start_year=2020)

    output_path = out_path.joinpath('az/usbr_az_b_and_f_investment_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='B&F Investment', field_id='Consumptive Us',  start_year=2020)

    output_path = out_path.joinpath('az/usbr_az_ehrenberg_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Ehrenberg', field_id='Diversion', start_year=2019)

    output_path = out_path.joinpath('az/usbr_az_ehrenberg_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Ehrenberg', field_id='Consumptive Us',  start_year=2019)

    output_path = out_path.joinpath('az/usbr_az_springs_del_sol_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Springs Del Sol', field_id='Diversion',  start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_springs_del_sol_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Springs Del Sol', field_id='Consumptive Us', start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_hillcrest_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Hillcrest', field_id='Diversion', start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_hillcrest_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Hillcrest', field_id='Consumptive Us', start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_arizona_state_parks_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Arizona State Parks', field_id='Diversion', start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_arizona_state_parks_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Arizona State Parks', field_id='Consumptive Us', start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_crystal_beach_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Crystal Beach', field_id='Diversion', start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_crystal_beach_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Crystal Beach', field_id='Consumptive Us', start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_mohave_county_water_authority_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Mohave County Water Authority', field_id='Diversion',
                start_year=2013)

    output_path = out_path.joinpath('az/usbr_az_mohave_county_water_authority_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Mohave County Water Authority', field_id='Consumptive Us',
                start_year=2013)

    output_path = out_path.joinpath('az/usbr_az_mohave_co_parks_diversion.csv')  # Bullhead City Diversion
    ocr_reports(image_path, output_path, water_user='Mohave Co. Parks', field_id='Diversion',
                start_year=1991, end_year=2012)

    output_path = out_path.joinpath('az/usbr_az_mohave_county_parks_diversion.csv')  # Bullhead City Diversion
    ocr_reports(image_path, output_path, water_user='Mohave County Parks', field_id='Diversion', start_year=2004)

    output_path = out_path.joinpath('az/usbr_az_bureau_of_reclamation_davis_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Bureau of Reclamation', field_id='Diversion', start_year=2014)

    output_path = out_path.joinpath('az/usbr_az_bureau_of_reclamation_davis_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Bureau of Reclamation', field_id='Consumptive Us', start_year=2014)

    output_path = out_path.joinpath('az/usbr_az_marble_canyon_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Marble Canyon', field_id='Diversion', start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_marble_canyon_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Marble Canyon', field_id='Consumptive Us', start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_mcalister_diversion.csv')
    ocr_reports(image_path, output_path, water_user='McAlister', field_id='Diversion', start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_mcalister_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='McAlister', field_id='Consumptive Us', start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_lake_mead_national_lake_mead_diversion.csv')
    ocr_reports(image_path, output_path, water_user='From Lake Mead', field_id='Diversion',
                start_year=1993, end_year=2012)

    output_path = out_path.joinpath('az/usbr_az_lake_mead_national_lake_mead_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='From Lake Mead', field_id='Consumptive Us',
                start_year=2003, end_year=2012)

    output_path = out_path.joinpath('az/usbr_az_lake_mead_national_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Temple Bar', field_id='Diversion',  start_year=2013)

    output_path = out_path.joinpath('az/usbr_az_lake_mead_national_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Temple Bar', field_id='Consumptive Us', start_year=2013)

    output_path = out_path.joinpath('az/usbr_az_lake_mead_national_lake_mohave_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Pumped from Lake Mohave', field_id='Diversion',
                start_year=2017, loop='returns')

    output_path = out_path.joinpath('az/usbr_az_lake_mead_national_lake_mohave_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Pumped from Lake Mohave', field_id='Consumptive Us',
                start_year=2017)

    output_path = out_path.joinpath('az/usbr_az_epcor_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='EPCOR', field_id='Consumptive Us', start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_epcor_diversion.csv')
    ocr_reports(image_path, output_path, water_user='EPCOR', field_id='Diversion', start_year=2016)

    output_path = out_path.joinpath('az/usbr_az_yuma_proving_well_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Proving', field_id='Wells', start_year=1995)

    output_path = out_path.joinpath('az/usbr_az_yuma_proving_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Proving', field_id='Diversion', start_year=1964)

    output_path = out_path.joinpath('az/usbr_az_mohave_water_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Mohave Water', field_id='Consumptive Us', start_year=2003)

    output_path = out_path.joinpath('az/usbr_az_golden_shores_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Golden Shores', field_id='Consumptive Us', start_year=2003)

    output_path = out_path.joinpath('az/usbr_az_brooke_water_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Brooke Water', field_id='Consumptive Us', start_year=2003)

    output_path = out_path.joinpath('az/usbr_az_cibola_valley_all_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Cibola Valley', field_id='Diversion',
                start_year=2005, end_year=2012, loop='Returns')

    output_path = out_path.joinpath('az/usbr_az_mohave_water_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Mohave Water', field_id='Diversion', start_year=1980)

    output_path = out_path.joinpath('az/usbr_az_lake_mead_national_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Lake Mead Nat', field_id='Diversion', start_year=1964)

    output_path = out_path.joinpath('az/usbr_az_brooke_water_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Brooke Water', field_id='Diversion', start_year=1995)

    output_path = out_path.joinpath('az/usbr_az_yuma_area_office_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Area Office', field_id='Diversion', start_year=1976)

    output_path = out_path.joinpath('az/usbr_az_golden_shores_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Golden Shores', field_id='Diversion', start_year=1989)

    output_path = out_path.joinpath('az/usbr_az_camille_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Camille', field_id='Diversion', start_year=1976)

    output_path = out_path.joinpath('az/usbr_az_desert_lawn_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Desert Lawn', field_id='Diversion', start_year=1984)

    output_path = out_path.joinpath('az/usbr_az_ehrenberg_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Ehrenberg', field_id='Diversion', start_year=1976)

    output_path = out_path.joinpath('az/usbr_az_yuma_proving_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Proving', field_id='Diversion',
                start_year=1964, loop='Returns')

    output_path = out_path.joinpath('az/usbr_az_yuma_union_high_school_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Union High School', field_id='Consumptive Us',
                start_year=2003)

    output_path = out_path.joinpath('az/usbr_az_hopi_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Hopi', field_id='Consumptive Us', start_year=2005)

    output_path = out_path.joinpath('az/usbr_az_yuma_union_high_school_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Union High School', field_id='Diversion', start_year=1984)

    output_path = out_path.joinpath('az/usbr_az_fort_yuma_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Fort Yuma', field_id='Consumptive Us', start_year=2006)

    output_path = out_path.joinpath('az/usbr_az_fort_yuma_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Fort Yuma', field_id='Diversion', start_year=1984)

    output_path = out_path.joinpath('az/usbr_az_hopi_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Hopi', field_id='Diversion', start_year=2005)

    output_path = out_path.joinpath('az/usbr_az_protective_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Protective', field_id='Diversion')

    output_path = out_path.joinpath('az/usbr_az_total_returns.csv')
    ocr_reports(image_path, output_path, water_user='Arizona Totals', field_id='Return', end_year=2009)

    output_path = out_path.joinpath('az/usbr_az_havasu_national_wildlife_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Havasu National', field_id='Consumptive Us',
                start_year=1969, end_year=1982)

    output_path = out_path.joinpath('az/usbr_az_protective_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Protective', field_id='Diversion')

    # Town of Parker
    output_path = out_path.joinpath('az/usbr_az_town_of_parker_pumped_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Town of Parker', field_id='Diversion', end_year=1978,
                loop='return')

    # Town of Parker
    output_path = out_path.joinpath('az/usbr_az_town_of_parker_pumped_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Town of Parker', field_id='Diversion', start_year=1990,
                loop='return')

    output_path = out_path.joinpath('az/usbr_az_university_of_arizona_diversion.csv')
    ocr_reports(image_path, output_path, water_user='University of Arizona', field_id='Diversion', start_year=1983)

    output_path = out_path.joinpath('az/usbr_az_university_of_arizona_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='University of Arizona', field_id='Consumptive Us', start_year=1983)

    output_path = out_path.joinpath('az/usbr_az_marine_corp_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Marine Corps', field_id='Consumptive Us', start_year=2003)

    output_path = out_path.joinpath('az/usbr_az_warren_act_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Warren Act', field_id='Consumptive Us', end_year=1990)

    output_path = out_path.joinpath('az/usbr_az_warren_act_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Warren Act', field_id='Diversion', end_year=1990)

    output_path = out_path.joinpath('az/usbr_az_crit_pumped_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Colorado River Indian', field_id='pump', start_year=1964,
                loop='return')

    # Sturges, Warren Act
    output_path = out_path.joinpath('az/usbr_az_sturges_warren_act_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Sturges', field_id='Consumptive Us',
                start_year=1993, end_year=2000)

    output_path = out_path.joinpath('az/usbr_az_sturges_warren_act_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Sturges', field_id='Diversion', start_year=1990, end_year=2000)

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

    # Lake Havasu Irrigation and Drainage in the 80's at least
    # Big Bend Conservation Area
    # Local aquifer storage
    # Las Vegas Valley Water District
    # City of North Las Vegas
    output_path = out_path.joinpath('nv/usbr_nv_city_of_boulder_city_diversion.csv')  # Add diversion loop
    ocr_reports(image_path, output_path, water_user='City of Boulder City', field_id='Diversion',
                start_year=1990, end_year=2003)

    output_path = out_path.joinpath('nv/usbr_nv_boulder_city_diversion.csv')  # Add diversion loop
    ocr_reports(image_path, output_path, water_user='Boulder ', field_id='Diversion')

    output_path = out_path.joinpath('nv/usbr_nv_lake_mead_national_lake_mohave_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Lake Mead National Recreation Area',
                field_id='Diversion from Lake Mohave', start_year=1993, end_year=2013)

    output_path = out_path.joinpath('nv/usbr_nv_lake_mead_national_lake_mohave_pumped_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Pumped from Lake Mohave', field_id='Diversion', start_year=2014)

    output_path = out_path.joinpath('nv/usbr_nv_lake_mead_national_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Lake Mead Nat', field_id='Diversion', start_year=1964)

    output_path = out_path.joinpath('nv/usbr_nv_hoover_dam_diversion.csv')
    ocr_reports(image_path, output_path, water_user='hoover dam', field_id='Diversion',
                end_year=1984)

    output_path = out_path.joinpath('nv/usbr_nv_hoover_dam_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='hoover dam', field_id='Consumptive Us',
                end_year=1984)

    output_path = out_path.joinpath('nv/usbr_nv_boulder_canyon_project_diversion.csv')
    ocr_reports(image_path, output_path, water_user='boulder canyon project', field_id='Diversion',
                start_year=1985, end_year=2013)

    output_path = out_path.joinpath('nv/usbr_nv_boulder_canyon_project_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='boulder canyon project', field_id='Consumptive Us',
                start_year=1985, end_year=2013)

    output_path = out_path.joinpath('nv/usbr_nv_bureau_of_reclamation_diversion.csv')
    ocr_reports(image_path, output_path, water_user='bureau of reclamation', field_id='Diversion', start_year=2014)

    output_path = out_path.joinpath('nv/usbr_nv_bureau_of_reclamation_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='bureau of reclamation', field_id='Consumptive Us', start_year=2014)

    output_path = out_path.joinpath('nv/usbr_nv_pacific_coast_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Pacific Coast', field_id='Diversion', start_year=1978)

    output_path = out_path.joinpath('nv/usbr_nv_johns_manville_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Johns', field_id='Diversion', start_year=1968)

    # Name changed to Johns Manville in 1968
    output_path = out_path.joinpath('nv/usbr_nv_fiberboard_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Fiberboard', field_id='Diversion', end_year=1967)

    output_path = out_path.joinpath('nv/usbr_nv_nevada_fish_and_game_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user=' fish ', field_id='Consumptive Us',
                start_year=1973, end_year=2014)

    output_path = out_path.joinpath('nv/usbr_nv_nevada_dept_of_wildlife_diversion.csv')
    ocr_reports(image_path, output_path, water_user='wildlife', field_id='Diversion', start_year=2015)

    output_path = out_path.joinpath('nv/usbr_nv_nevada_dept_of_wildlife_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='wildlife', field_id='Consumptive Us', start_year=2015)

    output_path = out_path.joinpath('nv/usbr_nv_nevada_fish_and_game_diversion.csv')
    ocr_reports(image_path, output_path, water_user=' fish ', field_id='Diversion', start_year=1973, end_year=2014)

    output_path = out_path.joinpath('nv/usbr_nv_north_las_vegas_diversion.csv')
    ocr_reports(image_path, output_path, water_user='North Las Vegas', field_id='Diversion', end_year=1984)

    output_path = out_path.joinpath('nv/usbr_nv_nellis_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Nellis', field_id='Diversion')

    output_path = out_path.joinpath('nv/usbr_nv_big_bend_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Big Bend Water', field_id='Consumptive Us', start_year=1995)

    output_path = out_path.joinpath('nv/usbr_nv_city_of_henderson_diversion.csv')  # Add diversion loop
    ocr_reports(image_path, output_path, water_user='City of Henderson', field_id='Diversion',
                start_year=1984, end_year=2001)

    # Las Valley Water District Changed to Robert B. Griffith in 1984
    output_path = out_path.joinpath('nv/usbr_nv_las_vegas_valley_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Las Vegas Valley', field_id='Diversion',
                start_year=1964, end_year=1983)

    output_path = out_path.joinpath('nv/usbr_nv_henderson_diversion.csv')  # Add diversion loop
    ocr_reports(image_path, output_path, water_user='Henderson', field_id='Diversion', start_year=1972)

    output_path = out_path.joinpath('nv/usbr_nv_so_cal_edison_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Edison', field_id='Diversion')

    output_path = out_path.joinpath('nv/usbr_nv_basic_water_company_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Basic ', field_id='Diversion')

    output_path = out_path.joinpath('nv/usbr_nv_fort_mojave_indian_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Fort Mojave Indian', field_id='Consumptive Us', start_year=2003)

    output_path = out_path.joinpath('nv/usbr_nv_fort_mojave_indian_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Fort Mojave Indian', field_id='Diversion', start_year=1996)

    output_path = out_path.joinpath('nv/usbr_nv_big_bend_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Big Bend Water', field_id='Diversion')

    output_path = out_path.joinpath('nv/usbr_nv_las_vegas_wash_returns.csv')
    ocr_reports(image_path, output_path,  water_user='Las Vegas Wash', field_id='Returns', start_year=1977)

    output_path = out_path.joinpath('nv/usbr_nv_total_returns.csv')
    ocr_reports(image_path, output_path, water_user='Nevada Totals', field_id='Return', end_year=2009)

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
        fig.set_figwidth(40)
        fig.set_figheight(25)
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
    ocr_debug(image_directory, path1='ca', path2='/consumptive_use')
    # ocr_debug(image_directory, path1='releases')
    # ocr_debug(image_directory, path1='mx')
    scavenge_nv(image_directory, outputs_path)
    scavenge_ca(image_directory, outputs_path)
    scavenge_az(image_directory, outputs_path)
    scavenge_releases(image_directory, outputs_path)
    scavenge_mx(image_directory, outputs_path)
