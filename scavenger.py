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
    parts = file_path.name.split('_')
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
        if water_user_lower in string.lower():
            look_for_diversion = True
        if look_for_diversion:
            string_lower = string.lower()
            if field_id_lower in string_lower:
                parts = string_lower.rsplit(field_id_lower, 1)
                if len(parts) > 0:
                    clean_string = ''
                    for c in parts[-1]:
                        if c.isdigit() or c == ' ' or c == '-':
                            clean_string += c
                    result = clean_string.replace('  ', ' ')
                    result = result.replace('  ', ' ')
                    result = result.strip()
                    return year, result
                else:
                    break

    return year, ''


def ocr_image_file(image_file_path, water_user, field_id, f):
    error_tolerance = 2  # af error allowed between summation of months and annual total

    year, data = ocr_report(image_file_path, water_user, field_id)
    print_file_name_prefix = '\t' + image_file_path.name + ': '
    if year > 1900 and len(data) > 0:
        values = data.split(' ')
        # Footnotes in older reports end in '/'
        if values[0].endswith('/'):
            values.pop(0)
        summation = 0
        for value in values[0:-1]:
            try:
                summation += int(value)
            except ValueError:
                print(print_file_name_prefix + 'ValueError in summation: ', value, year, data)
        try:
            if len(values):
                total = int(values[-1])
                error = abs(total - summation)
                out_str = ''
                for value in values:
                    out_str += value + ' '
                out_str.strip()
                error_str = ''
                if error > error_tolerance:
                    error_str = '# error: ' + ' diff = ' + str(error) + ' got sum = ' + str(summation) \
                                + ' ' + str(image_file_path)
                print(print_file_name_prefix + str(year) + ': ' + out_str + error_str)
                f.write(str(year) + ' ' + out_str + error_str + '\n')
                return year
            else:
                print(print_file_name_prefix + "Error Value array empty")
        except ValueError:
            print(print_file_name_prefix + 'ValueError on total: ', values[-1], year, data)
    return None


def ocr_reports(image_directory_path, output_file_path, water_user='', field_id='',
                start_year=None, end_year=None):
    print('ocr_report: ', water_user + ', ' + field_id)
    image_file_paths = []
    for image_file_path in image_directory_path.iterdir():
        name = image_file_path.name
        if name.endswith('.png'):
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
        f = output_file_path.open(mode='w')
        f.write('# USBR Lower Colorado Basin Annual reports: ' + water_user + ' ' + field_id + '\n')
        f.write('Year Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec Total\n')
        year_written_prev = year_from_file_path(image_file_paths[0]) - 1

        for image_file_path in image_file_paths:
            year_written = ocr_image_file(image_file_path, water_user, field_id, f)
            if year_written:
                year_difference = year_written - year_written_prev
                if year_difference > 1:
                    gap_string = '# Gap from ' + str(year_written_prev) + ' to ' + str(year_written)
                    print(gap_string)
                    f.write(gap_string + '\n')
                year_written_prev = year_written

        f.close()
    else:
        print("No image files to process", image_directory_path, water_user, field_id)


if __name__ == '__main__':
    image_directory = Path('/ark/Varuna/USBR_Reports/images/')
    outputs_path = Path('/opt/dev/riverwar/data/USBR_Reports/generated')

    # California
    #
    image_path = image_directory.joinpath('ca/consumptive_use')
    output_path = outputs_path.joinpath('ca/usbr_ca_palo_verde_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Palo Verde Irrigation', field_id='Consumptive Us')

    # CA Total
    output_path = outputs_path.joinpath('ca/usbr_ca_total_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='California Totals', field_id='Consumptive Use')

    output_path = outputs_path.joinpath('ca/usbr_ca_total_diversion.csv')
    ocr_reports(image_path, output_path, water_user='California Totals', field_id='Diversion')

    # "Measured" Returns in new reports, "Returns" in older reports
    # output_path = outputs_path.joinpath('ca/usbr_ca_total_measured_returns.csv')
    # ocr_reports(image_path, output_path, water_user='California Totals', field_id='Measured Returns')

    # Only in newer reports, how do you count 'Unmeasured Returns'?
    # output_path = outputs_path.joinpath('ca/usbr_ca_total_unmeasured_returns.csv')
    # ocr_reports(image_path, output_path, water_user='California Totals', field_id='Unmeasured Returns')

    # CA Diversions
    output_path = outputs_path.joinpath('ca/usbr_ca_imperial_irrigation_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Imperial Irrigation District', field_id='Consumptive Use')

    output_path = outputs_path.joinpath('ca/usbr_ca_imperial_irrigation_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Imperial Irrigation District', field_id='Diversion')

    output_path = outputs_path.joinpath('ca/usbr_ca_palo_verde_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Palo Verde Irrigation', field_id='Diversion')

    output_path = outputs_path.joinpath('ca/usbr_ca_palo_verde_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Palo Verde Irrigation', field_id='Consumptive Use')

    output_path = outputs_path.joinpath('ca/usbr_ca_coachella_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Coachella Valley Water', field_id='Diversion')

    output_path = outputs_path.joinpath('ca/usbr_ca_metropolitan_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Metropolitan Water District', field_id='Diversion')
    # Fort Mohave Indian
    # Yuma Project Reservation Division
    # Bard Unit
    # Sum of Diversions for FYIR Ranches in California
    # Yuma Island

    # Arizona
    #
    image_path = image_directory.joinpath('az/consumptive_use')

    # AZ Total, all parameters
    output_path = outputs_path.joinpath('az/usbr_az_total_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Arizona Totals', field_id='Diversion')

    # output_path = outputs_path.joinpath('az/usbr_az_total_measured_returns.csv')
    # ocr_reports(image_path, output_path, water_user='Arizona Totals', field_id='Measured Returns')

    # output_path = outputs_path.joinpath('az/usbr_az_total_unmeasured_returns.csv')
    # ocr_reports(image_path, output_path, water_user='Arizona Totals', field_id='Unmeasured Returns')

    output_path = outputs_path.joinpath('az/usbr_az_total_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Arizona Totals', field_id='Consumptive Use')

    # AZ Diversions
    output_path = outputs_path.joinpath('az/usbr_az_central_arizona_project_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Central Arizona Project', field_id='Diversion')

    output_path = outputs_path.joinpath('az/usbr_az_wellton_mohawk_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Wellton', field_id='Diversion')

    output_path = outputs_path.joinpath('usbr_az_crit_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Colorado River Indian', field_id='Diversion')

    output_path = outputs_path.joinpath('usbr_az_crit_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Colorado River Indian', field_id='Consumptive Use')

    output_path = outputs_path.joinpath('usbr_az_yuma_mesa_irrigation_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Mesa I', field_id='Diversion')

    output_path = outputs_path.joinpath('usbr_az_yuma_irrigation_district_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma Irrigation District', field_id='Diversion')

    output_path = outputs_path.joinpath('usbr_az_yuma_county_irrigation_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma County I', field_id='Diversion')

    output_path = outputs_path.joinpath('usbr_az_yuma_county_wua_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Yuma County Water Users', field_id='Diversion')

    output_path = outputs_path.joinpath('usbr_az_north_gila_irrigation_diversion.csv')
    ocr_reports(image_path, output_path, water_user='North Gila', field_id='Diversion')
    # Bullhead City
    # Mohave Valley I.D.D.
    # Fort Mohave Indian
    # Lake Havasu City
    # Cibola Valley I.D.D.
    # Hopu Tribe
    # Gila Monster Farms
    # City of Yuma
    # Unit B I.I.D.
    # Arizona State Land Development
    # Fort Yuma Indian
    # Cocopah Indian

    # Nevada
    #
    image_path = image_directory.joinpath('nv/consumptive_use')

    output_path = outputs_path.joinpath('usbr_nv_total_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Nevada Totals', field_id='Diversion', start_year=1984)

    output_path = outputs_path.joinpath('usbr_nv_total_consumptive_use.csv')
    ocr_reports(image_path, output_path, water_user='Nevada Totals', field_id='Consumptive Use', start_year=1984)

    output_path = outputs_path.joinpath('usbr_nv_snwa_griffith_diversion.csv')
    ocr_reports(image_path, output_path, water_user='Griffith Water Project', field_id='Diversion', start_year=1984)

    # Las Valley Water District Changed to Robert B. Griffith in 1984
    # output_path = outputs_path.joinpath('usbr_nv_las_vegas_valley_diversion.csv')
    # ocr_reports(image_path, output_path, water_user='Las Vegas Valley Water District', field_id='Diversion',
    #             end_year=1983)

    output_path = outputs_path.joinpath('usbr_nv_las_vegas_wash_diversion.csv')
    ocr_reports(image_path, output_path,  water_user='Las Vegas Wash', field_id='Returns', start_year=1984)
    # Basic Water Company
    # City of Henderson
    # Big Bend Water District
    # Fort Mohave Indian
