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
from data_sets.data_set import DataSet

class USGSGageDataSet(DataSet):
    def __init__(self, name:str, month:int=10):
        super().__init__(name, month=month)

        self.gage_to_name = {
            '09072500': 'Colorado River At Glenwood Springs, CO',
            '09095500': 'Colorado River Near Cameo, CO',
            '09109000': 'Taylor River Below Taylor Park Reservoir, CO',
            '09124700': 'Gunnision River Above Blue Mesa Reservoir,CO',
            '09127800': 'Gunnison River At Crystal Reservoir,CO',
            '09152500': 'Gunnison River Near Grand Junction, CO',
            '09180000': 'Dolores River Near Cisco, UT',
            '09180500': 'Colorado River Near Cisco UT',
            '09211200': 'Green R Bel Fontenelle Res WY',
            '09217000': 'Green R. Nr Green River, WyY',
            '09234500': 'Green River Near Greendale, UT',
            '09251000': 'Yampa River Near Maybell, CO\\',
            '09260000': 'Little Snake River Near Lily, CO',
            '09302000': 'Duchesne River Near Randlett, UT',
            '09306500': 'White River Near Watson, UT',
            '09315000': 'Green River At Green River, UT',
            '09328500': 'San Rafael River Near Green River, UT',
            '09355500': 'San Juan River Near Archuleta,NM',
            '09379500': 'San Juan River Near Bluff, UT',
            '09380000': 'Colorado R At Lees Ferry, AZ',
            '09382000': 'Paria R At Lees Ferry, AZ',
            '09402000': 'Little Colorado River Near Cameron, AZ',
            '09402500': 'Colorado River Near Grand Canyon, AZ',
            '09415000': 'Virgin River At Littlefield, AZ',
            '09421500': 'Colorado River Below Hoover Dam, AZ-NV',
            '09423000': 'Colorado River Below Davis Dam, AZ-NV',
            '09426000': 'Bill Williams River Below Alamo Dam, AZ',
            '09427520': 'Colorado River Below Parker Dam, AZ-CA',
            '09429490': 'Colorado River Above Imperial Dam, AZ'
        }
        self.name_to_gage = {
            'Colorado River At Glenwood Springs, CO': '09072500',
            'Colorado River Near Cameo, CO': '09095500',
            'Taylor River Below Taylor Park Reservoir, CO': '09109000',
            'Gunnision River Above Blue Mesa Reservoir,CO': '09124700',
            'Gunnison River At Crystal Reservoir,CO': '09127800',
            'Gunnison River Near Grand Junction, CO': '09152500',
            'Dolores River Near Cisco, UT': '09180000',
            'Colorado River Near Cisco UT': '09180500',
            'Green R Bel Fontenelle Res WY': '09211200',
            'Green R. Nr Green River, WyY': '09217000',
            'Green River Near Greendale, UT': '09234500',
            'Yampa River Near Maybell, CO\\': '09251000',
            'Little Snake River Near Lily, CO': '09260000',
            'Duchesne River Near Randlett, UT': '09302000',
            'White River Near Watson, UT': '09306500',
            'Green River At Green River, UT': '09315000',
            'San Rafael River Near Green River, UT': '09328500',
            'San Juan River Near Archuleta,NM': '09355500',
            'San Juan River Near Bluff, UT': '09379500',
            'Colorado R At Lees Ferry, AZ': '09380000',
            'Paria R At Lees Ferry, AZ': '09382000',
            'Little Colorado River Near Cameron, AZ': '09402000',
            'Colorado River Near Grand Canyon, AZ': '09402500',
            'Virgin River At Littlefield, AZ': '09415000',
            'Colorado River Below Hoover Dam, AZ-NV': '09421500',
            'Colorado River Below Davis Dam, AZ-NV': '09423000',
            'Bill Williams River Below Alamo Dam, AZ': '09426000',
            'Colorado River Below Parker Dam, AZ-CA': '09427520',
            'Colorado River Above Imperial Dam, AZ': '09429490'
        }
