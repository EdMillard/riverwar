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
import numpy as np
import pandas as pd
import textwrap

from source.water_year_info import WaterYearInfo


def format_to_month_day(dt64, leading_zeroes=True):
    ts = pd.to_datetime(dt64)
    if leading_zeroes:
        string = f"{ts.strftime('%b')}-{ts.day:02d}"
    else:
        string = f"{ts.strftime('%b')}-{ts.day}"
    return string

def verify(file, logger, y1, y2, custom_data, tolerances, variable_name, formulas, equations, comments, source1, source2):
    if variable_name in tolerances:
        tolerance = tolerances[variable_name]
    else:
        tolerance = WaterYearInfo.verify_tolerance
    variables = []
    text = ''
    file.write(f"VERIFY \'{variable_name}\'\n")
    if variable_name not in y1:
        file.write(f'\tFAIL {source1} not found: {variable_name}\n')
        return variables, text, 'FAIL'
    if variable_name not in y2:
        file.write(f'\tFAIL {source2} not found: {variable_name}\n')
        return variables, text, 'FAIL'
    if 'DATE' not in y1:
        file.write(f'\tFAIL DATE not found\n')
        return variables, text, 'FAIL'

    dt = y1['DATE']

    variable1 = y1.get(variable_name)
    if np.any(np.isnan(variable1)):
        file.write(f'\tWARN \'{variable_name}\' {source1} has NaN\n')
        variable1 = np.nan_to_num(variable1)
    variable2 = y2.get(variable_name)
    if np.any(np.isnan(variable2)):
        file.write(f'\tWARN \'{variable_name}\' {source2} has NaN\n')
        variable2 = np.nan_to_num(variable2)

    if len(variable1) != len(variable2):
        file.write(f'\tFAIL size mismatch: {variable_name} {source1}={len(variable1)} {source2}={len(variable2)}\n')
        return variables, text, 'FAIL'

    diff = variable2 - variable1
    if np.all(diff == 0) and variable_name not in custom_data:
        file.write(f'\tPASS \'{variable_name}\'\n')
        return variables, text, 'FAIL'

    sum_abs = np.sum(np.abs(diff))
    if sum_abs < tolerance and variable_name not in custom_data:
        file.write(f'\tPASS \'{variable_name}\' discrepancy: {sum_abs}\n')
        return variables, text, 'FAIL'

    # file.write(f'\tFAIL \'{variable_name}\' discrepancy: {sum_abs}\n')
    non_zero_indices = np.where(diff != 0)[0]
    f = formulas.get(variable_name)
    eq = equations.get(variable_name)
    comm = comments.get(variable_name)

    errors = 0
    text = ''
    for idx in non_zero_indices:
        if not np.isclose(variable1[idx], variable2[idx], atol=tolerance):
            errors += 1
            str = format_to_month_day(dt[idx])
            fmt = WaterYearInfo.format_float
            text += f'\'{str}\': diff={diff[idx]:{fmt}} {source1}={variable1[idx]:{fmt}} {source2}={variable2[idx]:{fmt}}\n'
            if f and f[idx]:
                text += f'\texcel: {f[idx]}\n'
                # text += excel_if_to_python(f[idx])
            if eq and eq[idx] and not pd.isna(eq[idx]):
                text += f'\t          {eq[idx]}\n'
            if comm and comm[idx] and not pd.isna(comm[idx]):
                indented = textwrap.indent(comm[idx],'\t')
                text += f'\n\tcomment:\n {indented}\n'

    if errors == 0 and variable_name not in custom_data:
        return variables, text, 'PASS'

    file.write(text)
    file.flush()

    if errors == 0 and variable_name in custom_data:
        logger.log_message(f'   PASS \'{variable_name}\' with custom data')
        variables = [(0, 'exl', variable_name), (1, 'out', variable_name, 'PASS')]
        pass_fail = 'PASS with custom data'
    else:
        logger.log_message(f'   FAIL \'{variable_name}\'')
        variables = [(0, 'exl', variable_name), (1, 'out', variable_name, 'FAIL')]
        pass_fail = 'FAIL'
    custom = custom_data.get(variable_name)
    if custom is not None:
        variables.append((2, 'custom', variable_name))

    return variables, text, pass_fail

def verify_input(file, logger, inp, y1, calc, variable_name):
    if not variable_name in inp:
        logger.log_message(f'  verify_input not found {variable_name}')
        return False

    inp = inp[variable_name]
    if inp is not None:
        date = y1['DATE']
        date_inp = inp['dt']
        variable_inp = inp['val']
        # FIXME date is already datetime64 when y1 is loaded from Excel, is not when loaded from csv
        # if date[0].astype('datetime64[D]') != date_inp[0].astype('datetime64[D]'):
        if len(date_inp):
            datetime_inp = date_inp[0].astype('datetime64[D]')
            if date[0] != datetime_inp:
                logger.log_message(f'  \'{variable_name}\' verify_input start date mismatch {date[0]} {date_inp[0]}')
                return False

            if len(date) != len(date_inp):
                if len(date_inp) > len(date):
                    variable_inp = variable_inp[:len(date)]
                else:
                    logger.log_message(f'  \'{variable_name}\'  verify_input size mismatch {len(date)} {len(date_inp)}')
                    return False
        else:
            logger.log_message(f'  \'{variable_name}\' verify_input no dates {len(date)} {len(date_inp)}')
            return False

        calc[variable_name] = variable_inp
        return True
    else:
        return False
