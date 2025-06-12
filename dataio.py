import datetime

def load_igc_file(path):
    with open(path) as file:
        lines = file.readlines()
    return lines

def get_h_records(lines):
    return [line for line in lines if line.startswith('H')]

def get_b_records(lines):
    return [line for line in lines if line.startswith('B')]

def extract_igc_date(h_records):
    date_line = next(
        (line for line in h_records if line.startswith('HFDTE') and not line.startswith('HFDTEDATE')),
        None
    )
    if date_line:
        date_raw = date_line.removeprefix('HFDTE')
    else:
        date_line = next((line for line in h_records if line.startswith('HFDTEDATE:')), None)
        if date_line:
            date_raw = date_line.removeprefix('HFDTEDATE:')
        else:
            raise ValueError("No date line found in IGC headers.")

    return date_raw.strip()

def extract_flight_info(h_records):
    date = extract_igc_date(h_records)

    pilot = next(record for record in h_records if record.startswith("HFPLTPILOTINCHARGE")).removeprefix(
        "HFPLTPILOTINCHARGE:")
    crew = next(record for record in h_records if record.startswith("HFCM2CREW2")).removeprefix("HFCM2CREW2:")
    type_ = next(record for record in h_records if record.startswith("HFGTYGLIDERTYPE")).removeprefix(
        "HFGTYGLIDERTYPE:")
    reg = next(record for record in h_records if record.startswith("HFGIDGLIDERID")).removeprefix("HFGIDGLIDERID:")
    comp_id = next(record for record in h_records if record.startswith("HFCIDCOMPETITIONID")).removeprefix(
        "HFCIDCOMPETITIONID:")
    competitionclass = next(record for record in h_records if record.startswith("HFCCLCOMPETITIONCLASS")).removeprefix(
        "HFCCLCOMPETITIONCLASS:")
    loggertype = next(record for record in h_records if record.startswith("HFFTYFRTYPE")).removeprefix("HFFTYFRTYPE:")

    if crew.strip() == '':
        crew = 'None'

    day = date[:2]
    month = date[2:4]
    year = date[4:]
    date = f"{day}/{month}/20{year}"

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

def parse_lat(lat_str, dir_str):
    degrees = int(lat_str[:2])
    minutes = int(lat_str[2:7]) / 1000.0
    decimal = degrees + minutes / 60
    if dir_str == 'S':
        decimal = -decimal
    return decimal

def parse_lon(lon_str, dir_str):
    degrees = int(lon_str[:3])
    minutes = int(lon_str[3:8]) / 1000.0
    decimal = degrees + minutes / 60
    if dir_str == 'W':
        decimal = -decimal
    return decimal

def parse_b_record(rij):
    # Assume rij is a B record string of the standard IGC format
    return {
        'TimeUTC': datetime.time(int(rij[1:3]), int(rij[3:5]), int(rij[5:7])),
        'Latitude': parse_lat(rij[7:14], rij[14]),
        'Longitude': parse_lon(rij[15:23], rij[23]),
        'Fix Validity': rij[24],
        'pressAltitude': int(rij[25:30]),
        'gpsAltitude': int(rij[30:35])
    }

def init_flightdata(igc_path):
    lines = load_igc_file(igc_path)
    b_lines = get_b_records(lines)
    b_records = [parse_b_record(line) for line in b_lines]
    return b_records

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