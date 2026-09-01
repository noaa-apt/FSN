STATIONS = {
    "NMF (Boston, MA) — Atlantic Ocean": [
        (4235.0, "USB"),
        (6340.5, "USB"),
        (9110.0, "USB"),
        (12750.0, "USB"),
    ],
    "NMG (New Orleans, LA) — Gulf of Mexico": [
        (4317.9, "USB"),
        (8503.9, "USB"),
        (12789.9, "USB"),
        (17146.4, "USB"),
    ],
    "NMC (Point Reyes, CA) — Pacific Ocean": [
        (4346.0, "USB"),
        (8682.0, "USB"),
        (12786.0, "USB"),
        (17151.2, "USB"),
        (22527.0, "USB"),
    ],
    "DDH / DDK (Hamburg, Germany)": [
        (3855.0, "USB"),
        (7880.0, "USB"),
        (13882.5, "USB"),
    ],
    "GYA (Northwood, United Kingdom)": [
        (2618.5, "USB"),
        (4610.0, "USB"),
        (8040.0, "USB"),
        (11086.5, "USB"),
    ],
    "JMH (Tokyo, Japan)": [
        (3622.5, "USB"),
        (7795.0, "USB"),
        (13988.5, "USB"),
    ],
    "VMC (Charleville, Australia)": [
        (2628.0, "USB"),
        (5100.0, "USB"),
        (11030.0, "USB"),
        (13920.0, "USB"),
        (20469.0, "USB"),
    ],
}

ALL_FREQS = []
for station, freqs in STATIONS.items():
    for f, mode in freqs:
        ALL_FREQS.append({"station": station, "freq": f, "mode": mode})
