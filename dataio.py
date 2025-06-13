import datetime

# Loads the IGC file and returns a list with its lines
def load_igc_file(path):
    with open(path) as file:
        lines = file.readlines()
    return lines

# Gets the H-records (flight info) out of the data and returns them in a list
def get_h_records(lines):
    return [line for line in lines if line.startswith('H')]

# Gets the B-records (flight data) out of the data and returns them in a list
def get_b_records(lines):
    return [line for line in lines if line.startswith('B')]

# Parses the H-records into a dict with all the flight info and returns the dict record
def get_flightinfo(h_records):
    date = get_igc_date(h_records)

    # next() loops over every record in the iterable h_records
    pilot = next(record for record in h_records if record.startswith("HFPLTPILOTINCHARGE")).removeprefix("HFPLTPILOTINCHARGE:").strip()
    crew = next(record for record in h_records if record.startswith("HFCM2CREW2")).removeprefix("HFCM2CREW2:").strip()
    type_ = next(record for record in h_records if record.startswith("HFGTYGLIDERTYPE")).removeprefix("HFGTYGLIDERTYPE:").strip()
    reg = next(record for record in h_records if record.startswith("HFGIDGLIDERID")).removeprefix("HFGIDGLIDERID:").strip()
    comp_id = next(record for record in h_records if record.startswith("HFCIDCOMPETITIONID")).removeprefix("HFCIDCOMPETITIONID:").strip()
    competitionclass = next(record for record in h_records if record.startswith("HFCCLCOMPETITIONCLASS")).removeprefix("HFCCLCOMPETITIONCLASS:").strip()
    loggertype = next(record for record in h_records if record.startswith("HFFTYFRTYPE")).removeprefix("HFFTYFRTYPE:").strip()

    # If there is no crew in the IGC-file
    if crew.strip() == '':
        crew = 'None'

    day = date[:2]
    month = date[2:4]
    year = date[4:]
    date = f"{day}/{month}/20{year}"   # for correctly displaying the date

    record = {
        'Date': date,
        'Pilot': pilot,
        'Crew': crew,
        'Type': type_,
        'Registration': reg,
        'Comp ID': comp_id,
        'Class': competitionclass,
        'Logger': loggertype,
    }
    return record

# Initializes the full B-records list (flight data) and returns it
def get_flightdata(igc_path):
    lines = load_igc_file(igc_path)
    b_lines = get_b_records(lines)
    b_records = [parse_b_record(line) for line in b_lines]
    return b_records

###################################
# HELPER FUNCTIONS
###################################

# Checks the altitude series and does a linear interpolation if there are 'jumps' greater than 200m
# Only used for plotting the altitude, does not affect the stored height in the flightdata!
def clean_altitude_series(altitudes, max_jump = 200):
    cleaned = [altitudes[0]]

    for i in range(1, len(altitudes)):
        height = altitudes[i]
        if abs(height - cleaned[i - 1]) < max_jump:
            cleaned.append(height)
        else:
            print("RECORD FAULTY at line " + str(i) + ". The height difference is too much: " + str(
                abs(height - cleaned[i - 1])))
            height_interpolated = (cleaned[i - 1] + altitudes[i + 1]) / 2 if i + 1 < len(altitudes) else cleaned[i - 1]
            cleaned.append(int(height_interpolated))
    return cleaned

# Returns the start time of a flight
def get_start_time(igc_path):
    b_records = get_flightdata(igc_path)

    for i in range(1, len(b_records)):
        if b_records[i]['Latitude'] != b_records[i - 1]['Latitude'] or b_records[i]['Longitude'] != b_records[i - 1]['Longitude']:
            return b_records[i]['TimeUTC']
    return -1

# Returns the end time of a flight
def get_end_time(igc_path):
    b_records = get_flightdata(igc_path)

    for i in range(len(b_records) - 1, 0, -1):
        if b_records[i]['Latitude'] != b_records[i - 1]['Latitude'] or b_records[i]['Longitude'] != b_records[i - 1]['Longitude']:
            return b_records[i]['TimeUTC']
    return -1

# Correctly parses the latitude and returns it as a decimal floating point number in degrees
# CAUTION: LATITUDE IS IN DD MMMMM
def parse_lat(lat_str, dir_str):
    degrees = int(lat_str[:2])
    minutes = int(lat_str[2:7]) / 1000.0
    decimal = degrees + (minutes / 60)
    if dir_str == 'S':
        decimal = -decimal
    return decimal

# Correctly parses the longitude and returns it as a decimal floating point number in degrees
# CAUTION: LONGITUDE IS IN DDD MMMMM
def parse_lon(lon_str, dir_str):
    degrees = int(lon_str[:3])
    minutes = int(lon_str[3:8]) / 1000.0
    decimal = degrees + (minutes / 60)
    if dir_str == 'W':
        decimal = -decimal
    return decimal

# Parses one row of the B-records (flight data)
def parse_b_record(rij):
    return {
        'TimeUTC': datetime.time(int(rij[1:3]), int(rij[3:5]), int(rij[5:7])),
        'Latitude': parse_lat(rij[7:14], rij[14]),
        'Longitude': parse_lon(rij[15:23], rij[23]),
        'Fix Validity': rij[24],
        'pressAltitude': int(rij[25:30]),
        'gpsAltitude': int(rij[30:35])
    }

# Gets the correct date out of the H-records (flight info) and returns the date
def get_igc_date(h_records):
    date_line = next(
        (line for line in h_records if line.strip().startswith('HFDTE') and not line.strip().startswith('HFDTEDATE')),
        None
    )
    if date_line:
        date_raw = date_line.strip().removeprefix('HFDTE')
    else:
        date_line = next((line for line in h_records if line.strip().startswith('HFDTEDATE:')), None)
        if date_line:
            date_raw = date_line.strip().removeprefix('HFDTEDATE:')
        else:
            # Print available header lines for debugging:
            print("DEBUG: Could not find date. Available headers:")
            for line in h_records:
                print(repr(line))
            raise ValueError("No date line found in IGC headers.")
    return date_raw.strip()


