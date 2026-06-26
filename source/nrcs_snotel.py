import requests
import pandas as pd
import io
#from datetime import datetime
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup

'''
WTEQ    Snow Water Equivalent       inches
SNWD    Snow Depth                  inches
PREC    Precipitation Accumulation  inches
PRCP    Precipitation Increment     inches
PRCPSA  Precipitation Increment (Snow-Adjusted) inches

Temperature Parameters
TAVG    Air Temperature Average     °F
TMAX    Air Temperature Maximum     °F
TMIN    Air Temperature Minimum     °F
TOBS    Air Temperature Observed    °F

Soil Parameters (available at many enhanced sites)
SMS                     Soil Moisture Percent                           %
STO / STV / STX / STN   Soil Temperature (Observed / Avg / Max / Min)   °F
SMO / SMV etc.          Soil Moisture (Bars)                            inches of Mercury

Other Common Meteorological Parameters
RHUM / RHUMV    Relative Humidity (or Average)  %
SRAD / SRADV    Solar Radiation (or Average)    watt/m²
WSPD / WSPDV    Wind Speed (or Average)         mph
WDIR / WDIRV    Wind Direction (or Average)     degrees
PRES            Barometric Pressure             inches of Mercury
BATT            Battery Voltage                 volts

Additional / Less Common CodesEVAP — Evaporation (inches)
DPTP — Dew Point Temperature (°F)
PARV — Photosynthetically Active Radiation
NTRDV etc. — Net Solar Radiation
WTEMP — Water Temperature (°F)
Various streamflow, reservoir, and other specialized codes (less common on standard SNOTEL)

Notes:Not every station measures every parameter. Core ones (WTEQ, SNWD, PREC, temperatures) are on almost all sites; soil moisture, wind, radiation, etc., vary.
Data is available at different time scales: Daily (_D), Hourly (_H), Monthly (_m), Water Year (_wy), etc.
You request these via the AWDB REST API, SOAP Web Service, or tools like the NRCS interactive map / Report Generator.

Official Reference: The complete list is in the AWDB Web Service User Guide (PDF).  nrcs.usda.gov
'''

def get_snotel_data(snotel_id:str, state:str, file_name:Optional[str]=None):
    file_path = Path('data/NRCS/SNOTEL')
    file_path.mkdir(parents=True, exist_ok=True)
    file_path = file_path / f"{file_name}"
    if file_path.exists():
        df = pd.read_csv(file_path)
        return df

    url = (
        "https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customSingleStationReport/daily/"
        f"{snotel_id}:{state}:SNTL|id=%22%22|name/POR_BEGIN,POR_END/"
        "TAVG::value,TMAX::value,TMIN::value,WTEQ::value,SNWD::value,PREC::value"
    )

    print("Downloading from NRCS...")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    text = response.text

    # Auto-detect header line that starts with "Date"
    lines = text.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("Date,"):
            header_idx = i
            break

    if header_idx is None:
        print("Could not find Date header. First 100 chars:")
        print(text[:1000])
        return pd.DataFrame()

    print(f"✅ Header found at line {header_idx}")

    df = pd.read_csv(
        io.StringIO(text),
        skiprows=header_idx,
        na_values=['*', ''],
        parse_dates=['Date']
    )

    # Clean column names
    df.columns = [col.strip().split('(')[0].strip().lower().replace(' ', '_')
                  for col in df.columns]
    df = df.rename(columns={'date': 'Date'})
    df = df.set_index('Date')

    # start_date = "2024-01-01"
    # end_date = None
    # if end_date is None:
    #     end_date = datetime.today().strftime("%Y-%m-%d")
    # df = df[(df.index >= start_date) & (df.index <= end_date)]

    print(f"✅ Successfully loaded {len(df)} rows")

    print(df.head())

    df.to_csv(file_path)

    return df


def get_snotel_stations(file_name:Optional[str]=None)->Optional[pd.DataFrame]:
    file_path = Path('data/NRCS/SNOTEL')
    file_path.mkdir(parents=True, exist_ok=True)
    file_path = file_path / f"{file_name}"
    if file_path.exists():
        df = pd.read_csv(file_path)
        return df
    url = "https://wcc.sc.egov.usda.gov/nwcc/sitelist.jsp"

    print("Downloading SNOTEL station list...")
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the main table (it usually has the station data)
    table = soup.find('table')
    if not table:
        raise ValueError("No table found on the page")

    # Convert HTML table to DataFrame
    df = pd.read_html(str(table))[0]

    # Clean columns
    df.columns = [col.strip() for col in df.columns]

    # Extract station ID from site_name column (e.g. "Black Mesa (1185)")
    df['station_id'] = df['site_name'].str.extract(r'\((\d+)\)').astype(int)
    df['site_name_clean'] = df['site_name'].str.replace(r' \(\d+\)', '', regex=True).str.strip()

    print(f"✅ Loaded {len(df)} SNOTEL stations")

    df.to_csv(file_path, index=False)

    return df

def stations_in_state(stations: pd.DataFrame, state: str) -> list[dict]:
    """
    Return all NRCS SNOTEL stations in the given state as a list of dictionaries.
    Each dictionary contains ALL columns from the DataFrame for that station.
    Stations are sorted by site_name_clean.
    """
    # Filter by state (case-insensitive if desired)
    mask = stations['state'].str.upper() == state.upper()
    state_stations = stations[mask].copy()

    if state_stations.empty:
        return []

    # Sort by clean site name for consistent ordering
    state_stations = state_stations.sort_values(by='site_name_clean')

    # Convert to list of dicts (each dict = one full station record)
    return state_stations.to_dict('records')

def stations_in_county(stations: pd.DataFrame, county: str) -> list[dict]:
    """
    Return all NRCS SNOTEL stations in the given county as a list of dictionaries.
    Each dictionary contains ALL columns from the DataFrame for that station.

    Parameters:
        stations (pd.DataFrame): The SNOTEL stations DataFrame
        county (str): County name (e.g. 'Summit', 'Park', 'Eagle')

    Returns:
        list[dict]: List of full station records (each dict has all columns)
    """
    # Case-insensitive matching, stripping whitespace
    mask = stations['county'].str.strip().str.upper() == county.strip().upper()

    county_stations = stations[mask].copy()

    if county_stations.empty:
        print(f"No stations found for county: {county}")
        return []

    # Sort by site name for consistent, readable output
    county_stations = county_stations.sort_values(by='site_name_clean')

    # Convert entire rows to list of dictionaries
    return county_stations.to_dict('records')


def stations_with_name(stations: pd.DataFrame, name_substring: str) -> list[dict]:
    """
    Return all NRCS SNOTEL stations whose site_name_clean contains the given substring.
    Returns a list of dictionaries with ALL columns from the DataFrame.

    Parameters:
        stations (pd.DataFrame): The SNOTEL stations DataFrame
        name_substring (str): Substring to search for (e.g. 'Summit', 'Lake', 'Grouse')

    Returns:
        list[dict]: List of full station records
    """
    # Case-insensitive substring match, ignoring extra whitespace
    mask = (
        stations['site_name_clean']
        .str.strip()
        .str.contains(name_substring.strip(), case=False, na=False)
    )

    matching_stations = stations[mask].copy()

    if matching_stations.empty:
        print(f"No stations found containing '{name_substring}' in the name.")
        return []

    # Sort by clean site name
    matching_stations = matching_stations.sort_values(by='site_name_clean')

    # Convert to list of full dictionaries
    return matching_stations.to_dict('records')

def stations_with_huc(stations: pd.DataFrame, huc_substring: str) -> list[dict]:
    """
    Return all NRCS SNOTEL stations whose HUC code contains the given substring.
    Returns a list of dictionaries with ALL columns from the DataFrame.

    Parameters:
        stations (pd.DataFrame): The SNOTEL stations DataFrame
        huc_substring (str): Substring to search for in the HUC column
                            (e.g. '140100', '1301', 'Colorado Headwaters')

    Returns:
        list[dict]: List of full station records
    """
    # Handle possible column name variations
    huc_col = None
    for col in ['huc', 'HUC', 'huc_code', 'HUC_CODE']:
        if col in stations.columns:
            huc_col = col
            break

    if huc_col is None:
        raise ValueError("No HUC column found in the DataFrame. Available columns: "
                         f"{list(stations.columns)}")

    # Case-insensitive substring match
    mask = (
        stations[huc_col]
        .astype(str)
        .str.strip()
        .str.contains(huc_substring.strip(), case=False, na=False)
    )

    matching_stations = stations[mask].copy()

    if matching_stations.empty:
        print(f"No stations found with HUC containing '{huc_substring}'.")
        return []

    # Sort by site name for readability
    matching_stations = matching_stations.sort_values(by='site_name_clean')

    # Return full records as list of dicts
    return matching_stations.to_dict('records')