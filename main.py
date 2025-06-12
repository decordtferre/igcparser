from dataio import (
    load_igc_file,
    get_h_records,
    get_b_records,
    extract_flight_info,
    parse_b_record,
    init_flightdata,
    clean_altitude_series
)

def main():
    igc_path = "/Users/ferredecordt/Documents/IGCreaderPython/2022-07-05-FLA-3VT-01.igc"

    # Load the file and extract records
    lines = load_igc_file(igc_path)
    h_records = get_h_records(lines)
    b_records_raw = get_b_records(lines)
    b_records = [parse_b_record(b) for b in b_records_raw]

    # Flight info
    flight_info = extract_flight_info(h_records)
    print("Flight info:")
    for k, v in flight_info.items():
        print(f"{k}: {v}")

    # Get and clean altitude series
    gps_altitudes = [b['gpsAltitude'] for b in b_records]
    clean_gps_altitudes = clean_altitude_series(gps_altitudes)


if __name__ == "__main__":
    main()
