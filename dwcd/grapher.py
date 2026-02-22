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
from graph.water import WaterGraph

def calculate_tick_interval(min_val, max_val, target_ticks=10):
    """
    Calculate a suitable tick interval for a graph to have approximately target_ticks
    tick lines within the range [min_val, max_val].

    Parameters:
    - min_val: Minimum value of the range (float or int)
    - max_val: Maximum value of the range (float or int)
    - target_ticks: Desired number of tick lines (default: 10)

    Returns:
    - interval: The calculated tick interval (float)
    - ticks: Array of tick positions
    """
    # Validate inputs
    if max_val <= min_val:
        raise ValueError("max_val must be greater than min_val")
    if target_ticks < 2:
        raise ValueError("target_ticks must be at least 2")

    # Calculate the range
    range_val = max_val - min_val

    # Estimate raw interval for ~10 ticks
    raw_interval = range_val / (target_ticks - 1)

    # Find a "nice" interval (e.g., 1, 2, 5, 10, etc.)
    magnitude = 10 ** np.floor(np.log10(raw_interval))
    nice_intervals = np.array([1, 2, 5, 10]) * magnitude
    # Choose the interval closest to raw_interval
    interval = nice_intervals[np.argmin(np.abs(nice_intervals - raw_interval))]

    # Calculate tick positions
    start = np.floor(min_val / interval) * interval
    end = np.ceil(max_val / interval) * interval
    # print('calculate_tick_interval', start, end + interval, interval)
    ticks = np.arange(start, end + interval, interval)

    return interval, ticks

def create_min_max_structured_array(dates, variable):
    dtype = np.dtype([
        ('dt', 'datetime64[D]'),
        ('val', variable.dtype),  # Field for values for max of values
    ])

    # Create structured array
    structured_array = np.empty(len(dates), dtype=dtype)
    structured_array['dt'] = dates
    structured_array['val'] = variable
    # print(structured_array['val'].min())  # 10.0
    # print(structured_array['val'].max())
    return structured_array


def compute_min_max(array1, array2):
    """
    Compute min and max for two NumPy arrays individually and combined.

    Parameters:
    - array1: First NumPy array (numeric values)
    - array2: Second NumPy array (numeric values)

    Returns:
    - dict: Contains min/max for each array and combined
    """
    # Validate inputs
    if not (array1.size > 0 and array2.size > 0):
        raise ValueError("Both arrays must be non-empty")
    if not (np.issubdtype(array1.dtype, np.number) and np.issubdtype(array2.dtype, np.number)):
        raise ValueError("Both arrays must contain numeric values")

    # Compute min and max for each array
    min1 = np.min(array1)
    max1 = np.max(array1)
    min2 = np.min(array2)
    max2 = np.max(array2)

    # Compute combined min and max
    combined_min = np.minimum(min1, min2)
    combined_max = np.maximum(max1, max2)

    return combined_min, combined_max

def graph_variable_1(y, variable_name, unit='cfs'):
    graph = WaterGraph(nrows=1)

    dt = y['DATE']
    variable = y[variable_name]
    if isinstance(variable, list):
        if np.any(np.isnan(variable)):
            variable = np.nan_to_num(variable)
        variable_type = type(variable[0]).__name__
        variable_min = min(variable)
        variable_max = max(variable)
    else:
        variable_type = variable.dtype
        variable_min = variable.min()
        variable_max = variable.max()
    dtype = [('dt', 'datetime64[D]'), ('val', variable_type)]
    structured_array = np.array(list(zip(dt, variable)), dtype=dtype)
    interval, ticks  = calculate_tick_interval(variable_min, variable_max)
    graph.plot(structured_array, sub_plot=0,
               title=variable_name,
               ymin=ticks[0], ymax= ticks[-1], yinterval=interval, color='royalblue',
               ylabel=unit, format_func=WaterGraph.format_discharge)

    graph.date_and_wait()

def graph_variable(y, variable_name, against, y_interval=10, unit='cfs', label1=None, label2=None):
    graph = WaterGraph(nrows=1)

    dt = y['DATE']
    variable = y[variable_name]
    dtype = [('dt', 'datetime64[D]'), ('val', float)]
    structured_array = np.array(list(zip(dt, variable)), dtype=dtype)

    graph.plot(structured_array, sub_plot=0,
               title=variable_name,
               yinterval=y_interval, color='firebrick',
               ylabel=unit, label=label1, format_func=WaterGraph.format_discharge)

    graph.plot(against, sub_plot=0,
               title=variable_name,
               yinterval=y_interval, color='royalblue',
               ylabel=unit, label=label2, format_func=WaterGraph.format_discharge)

    graph.date_and_wait()
