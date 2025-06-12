import datetime
import matplotlib.pyplot as plt
import numpy as np

def extract_igc_date(h_records):
    # Prefer canonical 'HFDTE' lines (but not 'HFDTEDATE:')
    date_line = next(
        (line for line in h_records if line.startswith('HFDTE') and not line.startswith('HFDTEDATE')),
        None
    )
    if date_line:
        # E.g., "HFDTE060723" (no colon)
        date_raw = date_line.removeprefix('HFDTE')
    else:
        # Fall back to 'HFDTEDATE:'
        date_line = next((line for line in h_records if line.startswith('HFDTEDATE:')), None)
        if date_line:
            date_raw = date_line.removeprefix('HFDTEDATE:')
        else:
            raise ValueError("No date line found in IGC headers.")

    return date_raw.strip()

def get_flight_info(igc_path):
    with open(igc_path) as file:
        h_records = [rij for rij in file if rij.startswith("H")]

    date = extract_igc_date(h_records)
    pilot = next(record for record in h_records if record.startswith("HFPLTPILOTINCHARGE")).removeprefix("HFPLTPILOTINCHARGE:")
    crew = next(record for record in h_records if record.startswith("HFCM2CREW2")).removeprefix("HFCM2CREW2:")
    type_ = next(record for record in h_records if record.startswith("HFGTYGLIDERTYPE")).removeprefix("HFGTYGLIDERTYPE:")
    reg = next(record for record in h_records if record.startswith("HFGIDGLIDERID")).removeprefix("HFGIDGLIDERID:")
    comp_id = next(record for record in h_records if record.startswith("HFCIDCOMPETITIONID")).removeprefix("HFCIDCOMPETITIONID:")
    competitionclass = next(record for record in h_records if record.startswith("HFCCLCOMPETITIONCLASS")).removeprefix("HFCCLCOMPETITIONCLASS:")
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

def init_flightdata(igc_path):
    with open(igc_path) as file:
        b_records = []
        for rij in file:
            if rij.startswith("B"):
                record = {
                    'TimeUTC': datetime.time(int(rij[1:3]), int(rij[3:5]), int(rij[5:7])),
                    'Latitude': int(rij[7:14]),
                    'LatitudeDir': rij[14],
                    'Longitude': int(rij[15:23]),
                    'LongitudeDir': rij[23],
                    'Fix Validity': rij[24],
                    'pressAltitude': int(rij[25:30]),
                    'gpsAltitude': int(rij[30:35])
                }
                b_records.append(record)
    return b_records

def plot_height_barogram(igc_path):
    b_records = init_flightdata(igc_path)
    gps = []
    pres = []

    gps.append(b_records[0]['gpsAltitude'])
    pres.append(b_records[0]['pressAltitude'])
    for i in range(1, len(b_records)):
        gps_height = b_records[i]['gpsAltitude']
        if abs(gps_height - gps[i - 1]) < 200:
            gps.append(gps_height)
        else:
            print("GPS RECORD FAULTY at line " + str(i) + ". The height difference is too much: " + str(abs(gps_height - gps[i-1])))
            gps_height_interpolated = (gps[i-1] + b_records[i + 1]['gpsAltitude']) /2 if i+1 < len(b_records) else gps[i-1]
            gps.append(gps_height_interpolated)

    for i in range(1, len(b_records)):
        pressure_height = b_records[i]['pressAltitude']
        if abs(pressure_height - pres[i - 1]) < 200:
            pres.append(pressure_height)
        else:
            print("PRESSURE RECORD FAULTY at line " + str(i) + ". The height difference is too much: " + str(abs(pressure_height - pres[i-1])))
            pressure_height_interpolated = (pres[i-1] + b_records[i + 1]['pressAltitude']) /2 if i+1 < len(b_records) else pres[i-1]
            pres.append(pressure_height_interpolated)

    assert (len(pres) == len(gps))

    times = [record['TimeUTC'] for record in b_records]
    time_labels = [t.strftime('%H:%M:%S') for t in times]
    N = len(time_labels)
    step = max(1, N // 10)

    info = get_flight_info(igc_path)
    start_time = get_starttime(igc_path)

    lines = []
    lines.append(f"Date: {info['Date'].strip()}")
    if info['Pilot'].strip():
        lines.append(f"Pilot: {info['Pilot'].strip()}")
    if info['Crew'].strip() != 'None':
        lines.append(f"Crew: {info['Crew'].strip()}")
    if info['Type'].strip():
        lines.append(f"Glider: {info['Type'].strip()}")
    if info['Registration'].strip():
        lines.append(f"Registration: {info['Registration'].strip()}")
    if info['Comp ID'].strip():
        lines.append(f"Comp ID: {info['Comp ID'].strip()}")
    if info['Class'].strip():
        lines.append(f"Class: {info['Class'].strip()}")
    if info['Logger'].strip():
        lines.append(f"Logger: {info['Logger'].strip()}")

    lines.append(f"Takeoff time: {start_time if start_time else 'N/A'}")
    lines.append(f"Landing time: {b_records[-1]['TimeUTC']}")
    infotext = "\n".join(lines)

    # --- Set up two columns: plot + info panel ---
    fig, (ax, info_ax) = plt.subplots(1, 2, figsize=(18, 8), gridspec_kw={'width_ratios': [4, 1]})

    # ----- Plot on the first axis -----
    ax.plot(gps, label="GPS")
    ax.plot(pres, label='PRESSURE')
    ax.set_xlabel("Time (UTC)", fontsize=18, fontweight='bold')
    ax.set_ylabel("Height (m)", fontsize=18, fontweight='bold')
    min_height = 0
    max_height = max(gps) + 200
    ax.set_xticks(np.arange(0, N, step=step))
    ax.set_xticklabels([time_labels[i] for i in np.arange(0, N, step=step)], rotation=0)
    ax.set_yticks(np.arange(min_height, max_height, 250))
    ax.grid(True, linewidth=1.4, which='both')
    ax.legend()

    # ----- Info panel on the right -----
    info_ax.axis('off')  # No axes, just text!
    info_ax.text(
        0.0, 1.0, infotext,
        ha='left', va='top',
        fontsize=15,
        family='monospace'
    )

    plt.tight_layout()
    plt.show()

def get_starttime(igc_path, min_jump=5):
    b_records = init_flightdata(igc_path)

    for i in range(1, len(b_records)):
        if abs(b_records[i]['gpsAltitude'] - b_records[i-1]['gpsAltitude']) > min_jump:
            return b_records[i]['TimeUTC']
    return b_records[0]['TimeUTC']



if __name__ == "__main__":
    igc_path = "/Users/ferredecordt/Documents/IGCreaderPython/2023-07-06-LXV-2J0-01.igc"
    plot_height_barogram(igc_path)

