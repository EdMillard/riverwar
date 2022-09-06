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
import datetime
import requests
import numpy as np
import os
from pathlib import Path

# USGS Gage parameter definitions
# https://help.waterdata.usgs.gov/code/parameter_cd_query?fmt=rdb&inline=true&group_cd=%

# USGS query gage and return Tab separated csv'ish text file
# https://waterdata.usgs.gov/nwis/dv?cb_00060=on&format=rdb&site_no=09380000&referred_module=sw&period=&begin_date=1921-10-01&end_date=2022-08-22

# USGS National Water Dashboard
# https://dashboard.waterdata.usgs.gov/app/nwd/?aoi=default


class USGSGage(object):
    """
    Essential paramaters to load and display a USGS gage site
  """

    def __init__(self, site, start_date, cfs_min=0, cfs_max=1000, cfs_interval=100,
                 annual_min=0, annual_max=100, annual_interval=10, annual_unit='kaf',
                 year_interval=5, color='royalblue'):
        self.site = site
        self.site_name = ''

        self.start_date = start_date
        self.end_date = str(datetime.date.today())

        self.cfs_min = cfs_min
        self.cfs_max = cfs_max
        self.cfs_interval = cfs_interval

        self.annual_min = annual_min
        self.annual_max = annual_max
        self.annual_interval = annual_interval
        self.annual_unit = annual_unit

        self.year_interval = year_interval
        self.color = color

        self.daily_discharge_cfs = ''
        self.annual_af = ''

    # def __del__(self):
    def daily_discharge(self):
        file_path = Path('data/USGS_Gages/')
        file_name = file_path.joinpath(self.site + '.csv')
        if not file_name.exists():
            self.request_daily_discharge(self.start_date, self.end_date)

        return self.load_daily_discharge(self.site)

    def load_time_series_csv(self, filename):
        date_time_format = "%Y-%m-%d"

        f = open(filename, )
        content = f.read()
        strings = content.split('\n')
        headers = []
        line = 0
        days = 0
        for s in strings:
            if s.startswith('#'):
                if s.startswith('#    USGS'):
                    self.site_name = s.replace('#    USGS', '')
                continue
            else:
                line += 1
                if line == 1:
                    headers = s.split('\t')
                elif line == 2:
                    continue
                else:
                    days += 1

        discharge_mean_index = usgs_discharge_mean_column(headers)

        a = np.empty(days - 1, [('dt', 'datetime64[s]'), ('val', 'f')])
        line = 0
        day = 0
        for s in strings:
            if s.startswith('#'):
                continue
            else:
                line += 1
                if line == 1:
                    continue
                elif line == 2:
                    continue
                else:
                    fields = s.split('\t')
                    if len(fields) > 1:
                        date_time = datetime.datetime.strptime(fields[2], date_time_format)
                        discharge_string = fields[discharge_mean_index]
                        if len(discharge_string):
                            try:
                                discharge = float(discharge_string)
                            except ValueError:
                                discharge = 0.0
                        else:
                            discharge = 0.0
                        # state = fields[4]
                        a[day][0] = date_time
                        a[day][1] = discharge
                        # print(fields)
                        day += 1
                    else:
                        break
        f.close()
        return a

    def request_daily_discharge(self, start_date, end_date, append=False):
        url = 'https://waterdata.usgs.gov/nwis/dv?cb_00060=on&format=rdb&site_no='
        url += self.site
        url += '&referred_module=sw&period=&begin_date='
        url += start_date
        url += '&end_date='
        url += end_date
        r = requests.get(url)
        if r.status_code == 200:
            try:
                data_path = Path('data/USGS_Gages/')
                data_path.mkdir(parents=True, exist_ok=True)

                file_name = data_path.joinpath(self.site + '.csv')
                if append:
                    f = open(file_name, 'a')
                    strings = r.content.decode("utf-8").split('\n')
                    for s in strings:
                        if s.startswith('USGS'):
                            s += '\n'
                            f.write(s)
                else:
                    f = open(file_name, 'w')
                    f.write(r.content.decode("utf-8"))
                f.close()
            except FileNotFoundError:
                print("usgs_get_gage_discharge cache file open failed for site: ", self.site)
        else:
            print('usgs_get_gage_discharge failed with response: ', r.status_code, ' ', r.reason)

    def load_daily_discharge(self, site):
        file_path = Path('data/USGS_Gages/')
        file_path.mkdir(parents=True, exist_ok=True)
        file_name = file_path.joinpath(self.site + '.csv')
        if not file_name.exists():
            print('USGS path doesn\'t exist: ', file_name)
            return file_name
        self.daily_discharge_cfs = self.load_time_series_csv(file_name)
        end_datetime64 = self.daily_discharge_cfs[-1]['dt']
        end_date = end_datetime64.astype(datetime.datetime).date()
        yesterdays_date = datetime.datetime.now().date() - datetime.timedelta(days=1)
        if end_date < yesterdays_date:
            end_date += datetime.timedelta(days=1)
            print('Gage updating from USGS: ', self.site_name, ' ', end_date, ' to ', yesterdays_date)
            self.request_daily_discharge(str(end_date), str(yesterdays_date), append=True)
            self.daily_discharge_cfs = self.load_time_series_csv(file_name)

        daily_discharge_af = convert_cfs_to_af_per_day(self.daily_discharge_cfs)
        self.annual_af = daily_to_water_year(daily_discharge_af)
        return self.daily_discharge_cfs


def usgs_discharge_mean_column(headers):
    discharge_mean_index = 0
    for header in headers:
        parts = header.split('_')
        if len(parts) == 3:
            # print(parts)
            if parts[1] == '00060' and parts[2] == '00003':
                break
        discharge_mean_index += 1

    return discharge_mean_index


def daily_to_water_year(a):
    water_year_month = 10
    dt = datetime.date(1, water_year_month, 1)
    total = 0
    result = []
    for o in a:
        obj = o['dt'].astype(object)
        if obj.month == 10 and obj.day == 1:
            if total > 0:
                result.append([dt, total])
                total = 0
            dt = datetime.date(obj.year+1, water_year_month, 1)
        elif dt.year == 1:
            if obj.month < water_year_month:
                dt = datetime.date(obj.year, water_year_month, 1)
            else:
                dt = datetime.date(obj.year+1, water_year_month, 1)

        total += o['val']

    if total > 0:
        result.append([dt, total])

    a = np.empty(len(result), [('dt', 'i'), ('val', 'f')])
    day = 0
    for l in result:
        # a[day][0] = np.datetime64(l[0])
        a[day][0] = l[0].year
        a[day][1] = l[1]
        day += 1

    return a


def convert_cfs_to_af_per_day(cfs):
    a = np.empty(len(cfs), [('dt', 'datetime64[s]'), ('val', 'f')])
    day = 0
    for l in cfs:
        a[day][0] = l[0]
        a[day][1] = l[1] * 1.983459
        day += 1
    return a


"""
def usgs_daily_discharge(site, start_date, end_date):
    sites = [site]
    name = usgs_gage_site_info(sites)

    daily_discharge_cfs = usgs_gage_daily_values(sites, start_date, end_date)
    return name, daily_discharge_cfs


def usgs_gage_site_info(sites):
    data_frame = nwis.get_record(sites=sites, service='site')
    print(data_frame.to_markdown())
    # print(data_frame.axes)
    info_values = data_frame.to_numpy()
    print(info_values[:, 1], info_values[:, 2])
    return sites[0] + ' - ' + info_values[0, 2]  # Site Name


def usgs_gage_instantaneous(sites, start_date, end_date):
    data_frame = nwis.get_record(sites=sites, service='iv', start=start_date, end=end_date)
    print(data_frame.to_markdown())
    print(data_frame.axes)
    print(data_frame.to_numpy()[:, 5])


def usgs_gage_daily_values(sites, start_date, end_date):
    data_frame = nwis.get_record(sites=sites, service='dv', start=start_date, end=end_date)
    print(data_frame.to_markdown())
    axes = data_frame.axes
    dates = axes[0].to_numpy()
    print('from: ', dates[0], ' to: ', dates[-1])
    # print(dates)
    new_array = np.array(data_frame.index.to_pydatetime(), dtype=np.datetime64)
    values = data_frame.to_numpy()[:, 3]
    # print(values)

    days = len(dates)
    a = np.empty(days, [('dt', 'datetime64[s]'), ('val', 'f')])
    for day in range(days):
        try:
            dt = new_array[day]
            value = values[day]
            if np.isnan(value):
                value = 0.0
            # print(value)
            a[day][0] = dt
            a[day][1] = value
        except KeyError:
            break
        day += 1

    return a


def usgs_gage_discharge_stats(sites, start_date, end_date, report_type='daily'):
    stats_tuple = nwis.get_stats(sites=sites,
                                 parameterCd=['00060'],  # Discharge=60 Temperature=10 GageHeight=65 conductance=95
                                 startDT=start_date,
                                 endDT=end_date,
                                 statReportType=report_type,  # daily, monthly, annual
                                 statTypeCd=['mean'])  # all, mean, max, min, median
    stats_df = stats_tuple[0]  # Headers
    print(stats_df.to_markdown())
    stats_values = stats_df.to_numpy()
    print(stats_values)  # Headers


def usgs_gage_water_quality(sites, start_date, end_date):
    data_frame = nwis.get_record(sites=sites, service='qwdata', start=start_date, end=end_date)
    print(data_frame.to_markdown())

"""

# sites = ['09134100']  # NORTH FORK GUNNISON RIVER BELOW PAONIA, CO
# sites = ['09114500']  # Gunnison River Near Gunnison, CO
# sites = ['09114520']  # Gunnison River at Gunnison WHitewater Park, CO
# sites = ['09128000']  # Gunnison River Below Gunnison Tunnel
# sites = ['09152500']  # GUNNISON RIVER NEAR GRAND JUNCTION, CO

# sites = ['09080400']  # FRYINGPAN RIVER NEAR RUEDI, CO

# sites = ['09149500']  # UNCOMPAHGRE RIVER AT DELTA, CO

# sites = ['09209400']  # Green River Near La Barge, WY
# sites = ['09261000']  # Green River Near Jensen, UT
# sites = ['09315000']  # Green River At Green River, UT
# sites = ['09328920']  # GREEN RIVER AT MINERAL BOTTOM NR CYNLNDS NTL PARK  2014-03-04

# sites = ['09239500']  # YAMPA RIVER AT STEAMBOAT SPRINGS, CO
# sites = ['09246200']  # ELKHEAD CREEK ABOVE LONG GULCH, NEAR HAYDEN, CO
# sites = ['09247600']  # YAMPA RIVER BELOW CRAIG, CO
# sites = ['09251000']  # YAMPA RIVER NEAR MAYBELL, CO

# sites = ['09253000']  # LITTLE SNAKE RIVER NEAR SLATER, CO

# sites = ['09304800']  # WHITE RIVER BELOW MEEKER, CO
# sites = ['09306290']  # WHITE RIVER BELOW BOISE CREEK, NEAR RANGELY, CO

# sites = ['09358000']  # ANIMAS RIVER AT SILVERTON, CO
# sites = ['09361500']  # ANIMAS RIVER AT DURANGO, CO
# sites = ['09363500']  # ANIMAS RIVER AT CEDAR HILL, NM
# sites = ['09364010']  # ANIMAS RIVER BELOW AZTEC, NM

# sites = ['09367000']  # LA PLATA RIVER AT LA PLATA, NM
# sites = ['09366500']  # LA PLATA RIVER AT COLORADO-NEW MEXICO STATE LINE

# sites = ['09371492']  # MUD CREEK AT STATE HIGHWAY 32, NEAR CORTEZ, CO
# sites = ['09371520']  # MCELMO CREEK ABOVE TRAIL CANYON NEAR CORTEZ, CO
# sites = ['09372000']  # MCELMO CREEK NEAR COLORADO-UTAH STATE LINE

# sites = ['09342500']  # San Juan River at Pagosa Springs, CO
# sites = ['09365000']  # San Juan River at Farmington, NM
# sites = ['09368000']  # San Juan River at Shiprock, NM
# sites = ['09371010']  # San Juan River at Four Corners, CO
# sites = ['09379500']  # San Juan River Near Bluff, UT

# sites = ['09172500']  # SAN MIGUEL RIVER NEAR PLACERVILLE, CO
# sites = ['09177000']  # SAN MIGUEL RIVER NEAR URAVAN, CO

# sites = ['09165000']  # Dolores River below Rico, CO
# sites = ['09166500']  # Dolores River at Dolores, CO
# sites = ['09168730']  # Dolores River near Slick Rock, CO
# sites = ['09169500']  # Dolores River at Bedrock, CO
# sites = ['09180000']  # Dolores River near Cisco, UT

# sites = ['09046600']  # Blue River Near Dillon, CO
# sites = ['09050700']  # Blue River Below Dillon, CO
# sites = ['09057500']  # Blue River Below Green Mountain Reservoir, CO

# sites = ['09010500']  # COLORADO RIVER BELOW BAKER GULCH NR GRAND LAKE, CO
# sites = ['09034250']  # Colorado River At Windy Gap, Near Grandby, CO
# sites = ['09019500']  # Colorado River Near Grandby, CO
# sites = ['09058000']  # Colorado River Near Kremmling, CO
# sites = ['09070500']  # Colorado River Near Dotsero, CO
# sites = ['09085100']  # Colorado River Below Glenwood Springs, CO
# sites = ['09095500']  # Colorado River Near Cameo, CO
# sites = ['09106150']  # COLO RIVER BELOW GRAND VALLEY DIV NR PALISADE, CO
# sites = ['09163500']  # Colorado River Near Colorado-Utah State Line
# sites = ['09180500']  # COLORADO RIVER NEAR CISCO, UT
# sites = ['09185600']  # COLORADO RIVER AT POTASH, UT

# sites = ['09380000']  # Colorado River at Lees Ferry, AZ
# sites = ['09382000']  # Paria River at Lees Ferry, AZ

# sites = ['09383400']  # Little Colorado At Greer, AZ
# sites = ['09397000']  # Little Colorado At Holbrook, AZ
# sites = ['09400350']  # Little Colorado Near Winslow, AZ
# sites = ['09402000']  # Little Colorado Near Cameron, AZ

# sites = ['09406000']  # Virgin River at Virgin, UT
# sites = ['09408150']  # Virgin River near Hurricane, UT
# sites = ['09413500']  # Virgin River near St.George, UT
# sites = ['09415000']  # VIRGIN RV AT LITTLEFIELD, AZ

# sites = ['09416000']  # Muddy River NR Moapa, NV
# sites = ['09419000']  # Muddy River NR Glendale, NV

# sites = ['09431500']  # GILA RIVER NEAR REDROCK, NM
# sites = ['09448500']  # GILA RIVER NEAR GILA, NM
# sites = ['09439000']  # GILA RIVER AT DUNCAN, AZ
# sites = ['09442000']  # GILA RIVER NEAR CLIFTON, AZ
# sites = ['09430500']  # GILA RIVER AT HEAD OF SAFFORD VALLEY, NR SOLOMON
# sites = ['09514100']  # GILA RIVER AT ESTRELLA PARKWAY, NEAR GOODYEAR, AZ (River is extirpated in Phoenix here)

# sites = ['09497500']  # SALT RIVER NEAR CHRYSOTILE, AZ
# sites = ['09498500']  # SALT RIVER NEAR ROOSEVELT, AZ
# sites = ['09502000']  # SALT RIVER BLW STEWART MOUNTAIN DAM, AZ

# sites = ['09508500']  # VERDE RVR BLW TANGLE CREEK, ABV HORSESHOE DAM, AZ
# sites = ['09510000']  # VERDE RIVER BELOW BARTLETT DAM, AZ
# sites = ['09511300']  # VERDE RIVER NEAR SCOTTSDALE, AZ

# sites = ['09423000']  # Colorado River Below Davis Dam, Az-Nv
# sites = ['09426620']  # Bill Williams River Near Parker, AZ
# sites = ['09427520']  # Colorado River Below Parker Dam, Az-Ca
# sites = ['09428500']  # CRIR MAIN CANAL NEAR PARKER, AZ
# sites = ['09429000']  # Palo Verde Canal Near Blythe, CA
# sites = ['09429100']  # Colorado River Below Palo Verde Dam, Az-Ca
# sites = ['09522500']  # Gila Gravity Main Canal At Imperial Dam
# sites = ['09527590']  # Coachella Canal Above All-American Diversion
# sites = ['09523000']  # All-American Canal Near Imperial Dam
# sites = ['09527700']  # ALL-AMERICAN CANAL BELOW DROP 2 RESERVOIR OUTLET  (Coachella and Alamo to Mexico removed)

# sites = ['09429500']  # Colorado River Below Imperial Dam
# sites = ['09429600']  # Colorado River Below Laguna Dam
# sites = ['09525500']  # Yuma Main Canal Below Colorado River Siphon
# sites = ['09521100']  # Colorado River Yuma Main Canal WW at Yuma, AZ
