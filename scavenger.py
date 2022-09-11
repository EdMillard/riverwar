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

import signal
import sys
from source import usbr_report
from pathlib import Path
import pyocr
import pyocr.builders
from PIL import Image

def image_to_text(file_path):
    tools = pyocr.get_available_tools()[0]
    image = Image.open(file_path)
    builder = pyocr.builders.TextBuilder(tesseract_layout=4)
    text = tools.image_to_string(image, builder=builder)
    # text = tools.image_to_string(image, builder=pyocr.builders.WordBoxBuilder())
    # text = tools.image_to_string(image, builder=pyocr.builders.LineBoxBuilder())
    # text = tools.image_to_string(image, builder=pyocr.builders.DigitBuilder())
    return text


def ocr_report(file_name, water_user='', field_id=''):
    water_user_lower = water_user.lower()
    field_id_lower = field_id.lower()

    parts = file_name.name.split('_')
    if len(parts) > 0:
        year = parts[0]
    else:
        year = 0
    text = image_to_text(file_name)
    strings = text.split('\n')
    look_for_diversion = False
    for string in strings:
        if water_user_lower in string.lower():
            look_for_diversion = True
        if look_for_diversion:
            string_lower = string.lower()
            if field_id_lower in string_lower:
                parts = string_lower.rsplit(field_id_lower, 1)
                #parts = string_lower.split(field_id_lower)
                if len(parts) > 0:
                    result = parts[-1].replace(',', '')
                    result = parts[-1].replace('.', '')
                    result = result.replace('=', '')
                    result = result.replace('«', '')
                    result = result.replace('\'', '')
                    result = result.replace('©', '')
                    result = result.replace(',', '')
                    result = result.replace(':', '')
                    result = result.replace(')', '')
                    result = result.replace('§', '')
                    result = result.replace('|', '')
                    result = result.replace('—', '')
                    result = result.replace('-', '')
                    result = result.replace('$', '')
                    result = result.replace(']', '')
                    result = result.replace('  ', ' ')

                    result = result.strip()
                    return year, result
                else:
                    break

    return year, ''


def ocr_reports(file_path, output_path, water_user='', field_id=''):
    print('ocr_reports: ', water_user, field_id)
    file_names = []
    for file_name in file_path.iterdir():
        name = file_name.name
        if name.endswith('.png'):
            file_names.append(file_name)
    file_names.sort()

    f = output_path.open(mode='w')
    f.write('# USBR Lower Colorado Basin Annual reports: ' + water_user + ' ' + field_id + '\n')
    f.write('Year Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec Total\n')
    for file_name in file_names:
        year, data = ocr_report(file_name, water_user, field_id)
        print(file_name.name, ':')
        if year and len(data) > 0:
            values = data.split(' ')
            # Footnotes in older reports end in '/'
            if values[0].endswith('/'):
                values.pop(0)
            summation = 0
            for value in values[0:-1]:
                try:
                    summation += int(value)
                except ValueError:
                    print('ValueError in summation: ', value, year, data)
            try:
                if len(values):
                    total = int(values[-1])
                    if summation == total:
                        out_str = ''
                        for value in values:
                            out_str += value + ' '
                        out_str.strip()
                        print(year, out_str)
                        f.write(year + ' ' + out_str + '\n')
                    else:
                        print('data error in report', year, 'expected = ', total, 'got = ', summation, year, data)
                else:
                    print("value array empty")
            except ValueError:
                print('ValueError on total: ', values[-1], year, data)
    f.close()


# noinspection PyUnusedLocal
def keyboardInterruptHandler(sig, frame):
    global interrupted
    interrupted = True

    try:
        print("exit")
        sys.exit(0)
    except OSError as e:
        print("riverwar exit exception:", e)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, keyboardInterruptHandler)

    file_path = Path('/opt/dev/riverwar/data/USBR_Reports/images/nevada/consumptive_use')
    output_path = Path('/opt/dev/riverwar/data/USBR_Reports/').joinpath('usbr_lake_mead_nevada_totals.csv')
    ocr_reports(file_path, output_path, water_user='Nevada Totals', field_id='Diversion')

    file_path = Path('/opt/dev/riverwar/data/USBR_Reports/images/nevada/consumptive_use')
    output_path = Path('/opt/dev/riverwar/data/USBR_Reports/').joinpath('usbr_lake_mead_las_vegas_wash.csv')
    ocr_reports(file_path, output_path,  water_user='Las Vegas Wash', field_id='Returns')

    file_path = Path('/opt/dev/riverwar/data/USBR_Reports/images/nevada/consumptive_use')
    output_path = Path('/opt/dev/riverwar/data/USBR_Reports/').joinpath('usbr_lake_mead_snwa_griffith_pumps.csv')
    ocr_reports(file_path, output_path, water_user='Griffith Water Project', field_id='Diversion')

    # Las Valley Water District Changed to Robert B. Griffith in 1984
    file_path = Path('/opt/dev/riverwar/data/USBR_Reports/images/nevada/consumptive_use')
    output_path = Path('/opt/dev/riverwar/data/USBR_Reports/').joinpath('usbr_lake_mead_las_vegas_valley.csv')
    ocr_reports(file_path, output_path, water_user='Las Vegas Valley Water District', field_id='Diversion')