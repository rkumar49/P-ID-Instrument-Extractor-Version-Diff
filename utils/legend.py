"""
P&ID Symbol & Tag Legend.
Supports both ISA-5.1 standard and KKS-style (European plant) tags.
"""

INSTRUMENT_PREFIXES = {
    "LT":  "Level Transmitter",
    "LG":  "Level Gauge (sight glass)",
    "LS":  "Level Switch",
    "LA":  "Level Alarm",
    "LI":  "Level Indicator",
    "LIC": "Level Indicating Controller",
    "LC":  "Level Controller",
    "LE":  "Level Element",
    "FT":  "Flow Transmitter",
    "FI":  "Flow Indicator",
    "FIC": "Flow Indicating Controller",
    "FC":  "Flow Controller",
    "FS":  "Flow Switch",
    "FA":  "Flow Alarm",
    "FE":  "Flow Element",
    "FQ":  "Flow Quantity / Totalizer",
    "TT":  "Temperature Transmitter",
    "TI":  "Temperature Indicator",
    "TIC": "Temperature Indicating Controller",
    "TC":  "Temperature Controller",
    "TS":  "Temperature Switch",
    "TA":  "Temperature Alarm",
    "TE":  "Temperature Element",
    "PT":  "Pressure Transmitter",
    "PI":  "Pressure Indicator",
    "PIC": "Pressure Indicating Controller",
    "PC":  "Pressure Controller",
    "PS":  "Pressure Switch",
    "PA":  "Pressure Alarm",
    "PG":  "Pressure Gauge",
    "BIC": "Batch Indicating Controller",
    "BI":  "Batch Indicator",
    "WIC": "Weight Indicating Controller",
    "WI":  "Weight Indicator",
    "AIC": "Analyzer Indicating Controller",
    "AI":  "Analyzer Indicator",
    "AT":  "Analyzer Transmitter",
    "HS":  "Hand Switch",
    "HV":  "Hand Valve",
    "XV":  "On/Off Valve",
    "FV":  "Flow Control Valve",
    "LV":  "Level Control Valve",
    "PV":  "Pressure Control Valve",
    "TV":  "Temperature Control Valve",
    "SC":  "Speed Controller",
    "SI":  "Speed Indicator",
    "ST":  "Speed Transmitter",
    "HC":  "Hand Controller",
    "HIC": "Hand Indicating Controller",
    "ZY":  "Positioner",
    "SOV": "Solenoid Valve",
    "FY":  "Signal Converter / Relay",
}

EQUIPMENT_PREFIXES = {
    "V": "Vessel / Tank",
    "P": "Pump",
    "K": "Compressor / Blower",
    "E": "Heat Exchanger",
    "R": "Reactor",
    "T": "Tower / Column",
    "M": "Motor / Mixer / Agitator",
    "F": "Fan / Filter",
    "H": "Heater / Furnace",
    "C": "Centrifuge / Conveyor",
    "B": "Boiler",
    "D": "Dryer",
    "S": "Separator / Silo",
    "G": "Generator",
    "X": "Miscellaneous Equipment",
}

FLUID_CODES = {
    "N2":  "Nitrogen",
    "PA":  "Plant Air",
    "IA":  "Instrument Air",
    "CW":  "Cooling Water",
    "CWR": "Cooling Water Return",
    "CWS": "Cooling Water Supply",
    "ST":  "Steam",
    "SC":  "Steam Condensate",
    "HC":  "Hydrocarbon",
    "BD":  "Blowdown",
    "FW":  "Fire Water",
    "PW":  "Process Water",
    "DM":  "Demineralized Water",
    "NG":  "Natural Gas",
    "H2":  "Hydrogen",
    "O2":  "Oxygen",
    "CD":  "Condensate",
    "WW":  "Waste Water",
    "VG":  "Vent Gas",
    "FL":  "Flare",
}

KKS_EQUIPMENT_TYPES = {
    "MA": "Motor / Agitator",
    "MP": "Motor-driven Pump",
    "AP": "Pump (auxiliary)",
    "AH": "Heat Exchanger",
    "AG": "Agitator",
    "AA": "Valve (motor-actuated)",
    "AB": "Valve (manual)",
    "AC": "Valve (control)",
    "AN": "Vessel",
    "AT": "Transformer",
    "CP": "Compressor",
    "CT": "Cooling Tower",
    "FN": "Fan",
    "GT": "Generator",
    "HE": "Heat Exchanger",
    "KT": "Boiler",
    "RE": "Reactor",
    "TA": "Tank",
    "GP": "General Part",
}

STATUS_WORDS = {
    "STREPAN", "LEER", "STOP", "STARTUP", "DRAIN", "DRAINHA",
    "ABFALL", "ABLASS", "SPERREN", "SCHLIESSEN",
    "START", "ENDE", "WARTEN", "BEREIT", "BEM",
}

# 3-tuple: (glyph, name, meaning)
SYMBOL_GLYPHS = [
    ("O",   "Circle",             "Field-mounted instrument (local)"),
    ("(O)", "Circle in circle",   "Panel-mounted instrument (DCS)"),
    ("O|",  "Circle with line",   "Software / shared display"),
    ("[]",  "Square",             "Logic / interlock function"),
    ("<>",  "Diamond",            "Programmable logic (PLC)"),
    ("//",  "Two triangles",      "Control valve with positioner"),
    ("v",   "Inverted triangle",  "Hand valve"),
    ("^o",  "Triangle + circle",  "Self-actuated regulator"),
    ("{}",  "Hexagon",            "Orifice plate / restriction"),
    ("->",  "Two arrows",         "Flow direction"),
    ("===", "Three lines",        "Insulation / heat tracing"),
]

# Regex patterns
EQUIP_SCOPED_INSTRUMENT_RE = r"([A-Z]{2,4}\d{2,4})-([A-Z]{2,4})(\d{2,3})"
KKS_RE                     = r"([A-Z]{2}\d[A-Z]{2,4}\d{2}[A-Z]{2}\d{3})-([A-Z]{2}\d{2})"
LINE_RE                    = r"([A-Z0-9]{2,4})\((\d{1,4})\)(\d{2,4})-([A-Z0-9]+)-([A-Z0-9]+)"
SIMPLE_ISA_RE              = r"([A-Z]{2,4})-(\d{3,6})"
DN_RE                      = r"DN(\d{2,4})"


def lookup_instrument(prefix):
    return INSTRUMENT_PREFIXES.get(prefix.upper(), "Unknown instrument")


def lookup_equipment(prefix):
    return EQUIPMENT_PREFIXES.get(prefix.upper(), "Unknown equipment")


def lookup_fluid(code):
    return FLUID_CODES.get(code.upper(), code)


def describe_tag(tag):
    import re
    tag = tag.strip().upper().replace(" ", "")

    m = re.fullmatch(EQUIP_SCOPED_INSTRUMENT_RE, tag)
    if m:
        equip_code, func, instance = m.groups()
        return {
            "raw": tag, "category": "Instrument", "prefix": func,
            "meaning": lookup_instrument(func) + " (on " + equip_code + ")",
            "number": instance, "equipment": equip_code,
        }

    m = re.fullmatch(KKS_RE, tag)
    if m:
        plant_part, equip_part = m.groups()
        equip_type = equip_part[:2]
        return {
            "raw": tag, "category": "Equipment (KKS)", "prefix": equip_type,
            "meaning": KKS_EQUIPMENT_TYPES.get(equip_type, "Unknown KKS equipment"),
            "number": equip_part, "equipment": plant_part,
        }

    m = re.fullmatch(LINE_RE, tag)
    if m:
        fluid, size, rating, spec, insul = m.groups()
        return {
            "raw": tag, "category": "Line", "prefix": fluid,
            "meaning": lookup_fluid(fluid) + ", " + size + " mm, rating " + rating,
            "number": size + "-" + rating + "-" + spec + "-" + insul,
        }

    m = re.fullmatch(SIMPLE_ISA_RE, tag)
    if m:
        prefix, number = m.groups()
        return {
            "raw": tag, "category": "Instrument (ISA)", "prefix": prefix,
            "meaning": lookup_instrument(prefix), "number": number,
        }

    m = re.fullmatch(r"DN(\d{2,4})", tag)
    if m:
        return {
            "raw": tag, "category": "Nominal Diameter", "prefix": "DN",
            "meaning": "Nominal diameter " + m.group(1) + " mm", "number": m.group(1),
        }

    if tag in STATUS_WORDS:
        return {
            "raw": tag, "category": "Status Label", "prefix": "",
            "meaning": "Operational state: " + tag.title(), "number": "",
        }

    return {
        "raw": tag, "category": "Unknown", "prefix": "",
        "meaning": "Unrecognized", "number": "",
    }
