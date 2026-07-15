import requests
import pandas as pd
import io
from pathlib import Path
from typing import Optional, List
from bs4 import BeautifulSoup
from datetime import datetime

ELEMENT_DESCRIPTIONS = {
    # Snow / Precip
    "WTEQ": "Snow Water Equivalent",
    "SNWD": "Snow Depth",
    "PREC": "Precipitation Accumulation",
    "PRCP": "Precipitation Increment",
    "PRCPSA": "Precipitation Increment (Snow-Adjusted)",
    "PRCPMTD": "Precipitation Month-to-Date",
    "WTEQX": "Snow Water Equivalent (Max or Derived)",
    "SNDN": "Snow Density",
    "SNRR": "Snow Rain Ratio",

    # Temperature
    "TAVG": "Air Temperature Average",
    "TMAX": "Air Temperature Maximum",
    "TMIN": "Air Temperature Minimum",
    "TOBS": "Air Temperature Observed",
    "PTEMP": "Panel Temperature",

    # Soil
    "SMS": "Soil Moisture Percent",
    "SMO": "Soil Moisture (Bars)",
    "SMV": "Soil Moisture (Volumetric)",
    "SMN": "Soil Moisture (Minimum)",
    "SMX": "Soil Moisture (Maximum)",
    "STO": "Soil Temperature Observed",
    "STV": "Soil Temperature Average",
    "STX": "Soil Temperature Maximum",
    "STN": "Soil Temperature Minimum",

    # Solar / Radiation
    "SRAD": "Solar Radiation",
    "SRADV": "Solar Radiation Average",
    "SRADT": "Solar Radiation Total",
    "SRADX": "Solar Radiation Maximum",
    "NTRDV": "Net Solar Radiation Average",
    "PARV": "Photosynthetically Active Radiation",
    "SWOTV": "Shortwave Outgoing Total",        # Albedo
    "SWINV": "Shortwave Incoming",
    "LWINV": "Longwave Incoming",
    "LWOTV": "Longwave Outgoing Total",         # Albedo

    # Wind
    "WSPDV": "Wind Speed Average",
    "WSPD": "Wind Speed",
    "WSPDX": "Wind Speed Maximum",
    "WDIRV": "Wind Direction Average",
    "WDIR": "Wind Direction",

    # Humidity / Pressure / Battery
    "RHUM": "Relative Humidity",
    "RHUMV": "Relative Humidity Average",
    "RHUMX": "Relative Humidity Maximum",
    "RHUMN": "Relative Humidity Minimum",
    "PRES": "Barometric Pressure",
    "BATT": "Battery Voltage",
    "BATX": "Battery Voltage (Auxiliary)",

    # Diagnostics
    "DIAG": "Diagnostic / Status",
}


def get_snotel_data(snotel_id: str,
                    state: str,
                    elements: List[str],
                    duration: str = "daily",
                    begin_date: str = "1980-01-01",
                    end_date: Optional[str] = None,
                    file_name: Optional[str] = None):
    """
    Fetch SNOTEL data.
    - Request uses original element names (with -2, -8 etc.)
    - Column names are cleaned AFTER downloading.
    - No hyphens in final column names.
    - Date is first column.
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # Cache
    file_path = Path('data/NRCS/SNOTEL') / f"{file_name or f'{snotel_id}_{state}_{duration}.csv'}"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.exists():
        print(f"✅ Loading cached {duration} data for {snotel_id}:{state}")
        return pd.read_csv(file_path, parse_dates=['Date'])

    # ==================== REQUEST (NO CLEANING HERE) ====================
    url = (
        "https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customSingleStationReport/"
        f"{duration}/{snotel_id}:{state}:SNTL|id=%22%22|name/"
        f"{begin_date},{end_date}/{','.join(elements)}"
    )

    print(f"🌐 Downloading {duration} data for {snotel_id}:{state}...")

    response = requests.get(url, timeout=90)
    response.raise_for_status()
    text = response.text

    # Find header row
    lines = text.splitlines()
    header_idx = next((i for i, line in enumerate(lines) if line.strip().startswith("Date,")), None)

    if header_idx is None:
        print("⚠️ Could not find Date header.")
        print(text[:500])
        return pd.DataFrame()

    # Read data
    df = pd.read_csv(
        io.StringIO(text),
        skiprows=header_idx,
        na_values=['*', ''],
        parse_dates=['Date']
    )

    # ==================== CLEAN COLUMNS ONLY AFTER DOWNLOAD ====================
    def clean_name(col: str) -> str:
        col = str(col).strip()

        # Remove units in ()
        if '(' in col:
            col = col.split('(')[0].strip()

        # Soil Moisture: SMS:-2 → 2in, SMS:-20 → 20in
        if 'SMS' in col.upper():
            match = re.search(r'-?(\d+)', col)
            if match:
                return f"{match.group(1)}in"

        # General cleaning - remove ALL hyphens
        col = (col.replace(' ', '_')
               .replace('-', '')  # Remove every hyphen
               .replace('.', '')
               .replace(':', ''))

        col = col.lower()
        return 'Date' if col == 'date' else col

    df.columns = [clean_name(col) for col in df.columns]

    # Put Date first
    if 'Date' in df.columns:
        date_col = df.pop('Date')
        df.insert(0, 'Date', date_col)

    print(f"✅ Loaded {len(df)} {duration} rows")
    print("Final columns:", df.columns.tolist())
    print(df.head(3))

    df.to_csv(file_path, index=False)
    return df

def get_snotel_hourly_data(snotel_id: str, state: str, file_name: Optional[str] = None):
    file_path = Path('data/NRCS/SNOTEL')
    file_path.mkdir(parents=True, exist_ok=True)
    file_path = file_path / f"{file_name or f'{snotel_id}_{state}_hourly.csv'}"

    if file_path.exists():
        print(f"✅ Loading cached hourly data for {snotel_id}:{state}")
        df = pd.read_csv(file_path, parse_dates=['Date'])
        df = df.set_index('Date')
        return df

    begin_date = "1980-01-01"
    end_date = "2026-07-02"

    elements = [
        "WSPDV::value",
        "WSPDX::value",
        "WDIRV::value",
        "SWINV::value",
        "SWOTV::value",
        "RHUMV::value"
    ]

    url = (
        "https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customSingleStationReport/hourly/"
        f"{snotel_id}:{state}:SNTL|id=%22%22|name/POR_BEGIN,POR_END/"
        f"{begin_date},{end_date}/"
        f"{','.join(elements)}"
    )

    print(f"🌐 Downloading HOURLY enhanced data for {snotel_id}:{state}...")
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    text = response.text

    lines = text.splitlines()
    header_idx = next((i for i, line in enumerate(lines) if line.strip().startswith("Date,")), None)

    if header_idx is None:
        print("No Date header found. First 500 chars:")
        print(text[:500])
        return pd.DataFrame()

    df = pd.read_csv(
        io.StringIO(text),
        skiprows=header_idx,
        na_values=['*', ''],
        parse_dates=['Date']
    )

    df.columns = [col.strip().split('(')[0].strip().lower().replace(' ', '_')
                  for col in df.columns]
    df = df.rename(columns={'date': 'Date'})
    df = df.set_index('Date')

    print(f"✅ Loaded {len(df)} hourly rows")
    print("Columns:", df.columns.tolist())
    print(df.tail(5))

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

def print_full_summary(df: pd.DataFrame, title: str = "Sensor Summary"):
    """Print the entire DataFrame without truncation."""
    with pd.option_context(
        'display.max_rows', None,           # Show all rows
        'display.max_columns', None,        # Show all columns
        'display.width', None,              # No line wrapping
        'display.max_colwidth', None        # Full column content
    ):
        print(title)
        print(df)
        print(f"\nTotal sensors: {len(df)}")

def parse_station_elements(data: list) -> pd.DataFrame:
    if not data or len(data) == 0:
        return pd.DataFrame()

    station = data[0]
    elements = station.get('stationElements', [])

    if not elements:
        return pd.DataFrame()

    records = []
    for el in elements:
        code = el.get('elementCode')
        records.append({
            'element_code': code,
            'description': ELEMENT_DESCRIPTIONS.get(code, 'Unknown'),
            'begin_date': el.get('beginDate'),
            'end_date': el.get('endDate'),
            'duration': el.get('durationName'),
            'ordinal': el.get('ordinal'),
            'unit': el.get('storedUnitCode'),
            'derived': el.get('derivedData', False),
        })

    df = pd.DataFrame(records)
    if 'begin_date' in df.columns:
        df['begin_date'] = pd.to_datetime(df['begin_date'], errors='coerce')
        df = df.sort_values(by='begin_date').reset_index(drop=True)

    return df

def get_snotel_station_elements(
        station_id: str,
        state: str,
        data_dir: str = "data/NRCS/SNOTEL/sensors"
) -> pd.DataFrame:
    path = Path(data_dir)
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / f"{station_id}_{state.upper()}_elements.csv"

    if file_path.exists():
        print(f"✅ Loading cached for {station_id}:{state}")
        df = pd.read_csv(file_path, parse_dates=['begin_date'])
    else:
        triplet = f"{station_id}:{state}:SNTL"
        url = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations"

        params = {
            "stationTriplets": triplet,
            "returnForecastPointMetadata": "false",
            "returnReservoirMetadata": "false",
            "returnStationElements": "true",
            "activeOnly": "true"
        }

        print(f"🌐 Querying for {triplet}...")
        response = requests.get(url, params=params, headers={"accept": "application/json"}, timeout=30)

        if not response.ok:
            print(f"❌ Error {response.status_code}")
            return pd.DataFrame()

        data = response.json()
        df = parse_station_elements(data)

        if not df.empty:
            df.to_csv(file_path, index=False)
            print(f"💾 Saved to {file_path}")

    if df.empty:
        print("No sensors found.")
        return df

    # Ensure description column exists (for old cache files)
    if 'description' not in df.columns:
        df['description'] = df['element_code'].map(ELEMENT_DESCRIPTIONS).fillna("Unknown")

    print(f"\n=== Sensors for Station {station_id}:{state} ===")
    print(f"Total installed sensors: {len(df)}")

    with pd.option_context('display.max_rows', None, 'display.max_colwidth', 60):
        print(df[['element_code', 'description', 'begin_date', 'duration', 'unit']])

    return df

def get_sensor_history_years(sensors_df: pd.DataFrame) -> int:
    """
    Returns years of history from the oldest sensor.
    Works with both old Report Generator format and new REST format.
    """
    if sensors_df.empty:
        return 0

    # Support both column names
    date_col = None
    for col in ['sensor_start_date', 'begin_date']:
        if col in sensors_df.columns:
            date_col = col
            break

    if date_col is None:
        print("No date column found in sensor DataFrame.")
        return 0

    earliest_date = pd.to_datetime(sensors_df[date_col]).min()
    current_year = datetime.now().year

    years_back = current_year - earliest_date.year

    print(f"Earliest sensor date: {earliest_date.date()}")
    print(f"Years of history: {years_back}")

    return years_back