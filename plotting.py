import matplotlib.pyplot as plt
import numpy as np

from dataio import (
    load_igc_file,
    get_h_records,
    get_b_records,
   get_flight_info,
    parse_b_record,
    clean_altitude_series, get_start_time,
)

def plot_barogram_with_info(igc_path):

    lines = load_igc_file(igc_path)
    h_records = get_h_records(lines)
    b_records_raw = get_b_records(lines)
    b_records = [parse_b_record(b) for b in b_records_raw]
    start_time = get_start_time(igc_path)
    end_time = get_start_time(igc_path)

    # --- Prepare altitude series ---
    gps = clean_altitude_series([b['gpsAltitude'] for b in b_records])
    pres = clean_altitude_series([b['pressAltitude'] for b in b_records])

    # --- Prepare time labels ---
    times = [record['TimeUTC'] for record in b_records]
    time_labels = [t.strftime('%H:%M:%S') for t in times]
    N = len(time_labels)
    step = max(1, N // 10)

    # --- Info block ---
    info = get_flight_info(igc_path)

    lines_info = []
    lines_info.append(f"Date: {info['Date'].strip()}")
    if info['Pilot'].strip():
        lines_info.append(f"Pilot: {info['Pilot'].strip()}")
    if info['Crew'].strip() != 'None':
        lines_info.append(f"Crew: {info['Crew'].strip()}")
    if info['Type'].strip():
        lines_info.append(f"Glider: {info['Type'].strip()}")
    if info['Registration'].strip():
        lines_info.append(f"Registration: {info['Registration'].strip()}")
    if info['Comp ID'].strip():
        lines_info.append(f"Comp ID: {info['Comp ID'].strip()}")
    if info['Class'].strip():
        lines_info.append(f"Class: {info['Class'].strip()}")
    if info['Logger'].strip():
        lines_info.append(f"Logger: {info['Logger'].strip()}")

    lines_info.append(f"Takeoff time: {start_time if start_time else 'N/A'}")
    lines_info.append(f"Landing time: {b_records[-1]['TimeUTC']}")
    infotext = "\n".join(lines_info)

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

plot_barogram_with_info("/Users/ferredecordt/Documents/IGCreaderPython/2022-07-05-FLA-3VT-01.igc")

