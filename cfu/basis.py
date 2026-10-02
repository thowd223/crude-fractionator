"""Basis of Design - single source of truth for the whole deliverable set."""

PROJECT = dict(
    name="100 kBPSD Crude & Vacuum Distillation Unit",
    short="CDU/VDU",
    client="Generic Refinery - Gulf Coast",
    doc_prefix="CFU",
    rev="A",
    rev_desc="Issued for review (FEED)",
    stage="FEED",
)

CAPACITY_BPSD = 100_000           # stream-day, design crude
STREAM_FACTOR = 0.95              # on-stream factor
TURNDOWN = 0.50                   # min. stable throughput fraction
DESIGN_MARGIN = 1.10              # equipment design margin on normal rates (hydraulics)

CRUDE = dict(
    name="Arab Light (design)",
    api=33.4,
    sulfur_wt=1.80,
    salt_ptb=20.0,                # lb salt / 1000 bbl, as received
    bsw_vol=0.3,                  # vol %
    tan=0.05,
    pour_C=-30,
    # TBP: (cumulative LV %, degC). Light ends (C2-C4) supplied separately below.
    tbp=[(1.70, 36), (5, 60), (10, 96), (20, 145), (30, 197), (40, 252), (50, 310),
         (60, 372), (70, 445), (80, 525), (85, 572), (90, 635), (95, 715), (100, 850)],
    light_ends_lv={"C2": 0.05, "C3": 0.40, "iC4": 0.25, "nC4": 1.00},
)
CHECK_CRUDE = dict(name="Arab Heavy (check case)", api=27.7, sulfur_wt=2.8,
                   note="Hydraulic/thermal check case; not simulated in Rev A")

# Product cut points (TBP degC)
CUTS_ATM = [("LN", 80), ("HN", 165), ("KERO", 235), ("DIESEL", 320), ("AGO", 370)]
CUTS_VAC = [("LVGO", 430), ("HVGO", 550)]

SITE = dict(
    location="US Gulf Coast (generic)",
    elevation_m=5,
    amb_design_C=35.0, amb_min_C=-5.0, wet_bulb_C=27.0,
    rel_humidity=0.8,
    wind_design="ASCE 7, 150 mph (3-s gust)",
    seismic="ASCE 7, SDC B",
    units="SI (degC, bar, kg/h, m)",
    pressure_ref="bar(g) unless noted (a)",
)

UTILITIES = dict(
    hp_steam=dict(P_barg=41.4, T_C=400, note="600 psig header"),
    mp_steam=dict(P_barg=10.3, T_C=250, note="150 psig header"),
    lp_steam=dict(P_barg=3.5, T_C=180, note="50 psig header"),
    cooling_water=dict(supply_C=32, return_C=43, P_barg=4.5),
    bfw=dict(T_C=120, P_barg=50),
    fuel_gas=dict(LHV_MJ_kg=47.0, P_barg=3.5, MW=20.0),
    instrument_air=dict(P_barg=7.0, dewpoint_C=-40),
    nitrogen=dict(P_barg=7.0),
    power=dict(utility_kV=13.8, mv_kV=4.16, lv_V=480, ac_hz=60, ups_V=120),
)

DESIGN = dict(
    # atmospheric column
    atm_top_P=2.2, atm_drum_P=1.7, atm_tray_dP=0.008,
    atm_cot_max=370.0, atm_overflash_lv=0.03,
    atm_drum_T=45.0, tl_dP=0.9, tl_dT=5.0,
    pa_split=dict(TPA=0.17, MPA=0.27, BPA=0.26),   # fraction of total heat removal
    steam_lb_per_bbl=dict(bottom=10, KERO=6, DIESEL=6, AGO=6),
    # vacuum column
    vac_top_P=0.020, vac_fz_P=0.060, vac_cot_max=415.0, vac_tl_dT=12.0,
    vac_overflash_lv=0.03, vac_steam_lb_per_bbl=dict(bottom=5, coil=1.5),
    vac_pa_split=dict(LVGO=0.40, HVGO=0.60),
    # light ends
    stab_drum_P=11.5, stab_drum_T=45.0, split_drum_P=1.8, split_drum_T=50.0,
    # heaters
    h101_eff=0.90, h201_eff=0.88, rad_flux_kW_m2=31.5, rad_fraction=0.65,
    desalter_T=135.0, wash_water_lv=0.05,
    min_approach=20.0,
)

CODES = [
    ("API 650 / 620", "Storage tanks (off-plot, interface only)"),
    ("API 560", "Fired heaters"),
    ("API 660 / TEMA R", "Shell & tube exchangers"),
    ("API 661", "Air-cooled heat exchangers"),
    ("API 610 12th ed.", "Centrifugal pumps"),
    ("API 520 / 521", "Pressure relief sizing and disposal"),
    ("API 537", "Flare details (interface)"),
    ("ASME VIII Div.1", "Pressure vessels and columns"),
    ("ASME B31.3", "Process piping"),
    ("ASME B16.5 / B16.47", "Flanges"),
    ("API RP 505 / IEC 60079-10-1", "Hazardous area classification (Zone system)"),
    ("NFPA 70 (NEC) Art. 505", "Electrical installation in Zone-classified areas"),
    ("IEEE 141 / 399", "Power system design and studies"),
    ("ISA 5.1 / 5.4 / 5.2", "Instrument symbols, loop diagrams, binary logic"),
    ("IEC 61511 / ISA 84", "Safety instrumented systems"),
    ("IEC 62443", "Industrial cybersecurity (zones and conduits)"),
    ("API 2218 / 2510A", "Fireproofing / LPG spacing"),
    ("CCPS / GAP 2.5.2", "Equipment spacing guidelines"),
    ("NACE MR0103 / API 939-C / API 571", "Materials for sour, sulfidation, naphthenic service"),
]

PRODUCT_SPECS = {
    "LPG": "C5+ <= 2 LV%; C2- <= 0.5 mol% (tie-in to LPG treating)",
    "LN": "TBP 36-80 degC; RVP <= 0.85 bar; to isomerisation",
    "HN": "TBP 80-165 degC; to NHT/reformer; ASTM D86 EP <= 185 degC",
    "KERO": "Flash >= 38 degC; D86 FBP <= 260 degC; to jet Merox/hydrotreater",
    "DIESEL": "D86 T95 <= 360 degC; flash >= 55 degC; to DHT",
    "AGO": "To DHT / FCC feed",
    "LVGO": "To hydrocracker; D1160 T95 <= 450 degC",
    "HVGO": "To FCC/hydrocracker; Ni+V <= 2 ppmw; CCR <= 0.8 wt%",
    "VR": "To delayed coker; 550 degC+ TBP",
}
