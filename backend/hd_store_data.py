"""
Home Depot – West Roxbury, MA (Store #2665) store layout and offline product catalogue.

Grid: 16 columns × 10 rows, 60 px per cell → 960 × 600 canvas.
Origin (0,0) = top-left = back-left of store (near outdoor garden / greenhouse).
Entrance row = y≈9.5. Entrance = bottom-center-left (matches HD mobile app map).

Real store layout (derived from Home Depot mobile app map):
  ┌──────────────────────────────────────────────────────────────────────┐ gy=0
  │OutdoorGarden│  Electrical  │  Tools   │ Hardware │ Windows│  Millwork│
  │ (left strip)├──────────────┴──────────┴──────────┴────────┴──────────┤ gy=3
  │             │  Lighting    │ Appliances & Ktch │ Carpet │  Storage  │
  │             ├──────────────┴────────────────────┴────────┴───────────┤ gy=6
  │             │ Bath/IndGdn │ Paint │ Plumbing │  Lumber & Bldg Mat   │
  │             ├─────────────┴───────┴──────────┴──────────────────────┤ gy=8.5
  │             │         Checkout              │     Pro Desk           │ gy=9.5
  └──────────────────────────────────────────────────────────────────────┘
                         ↑ Entrance (gx≈6)  ↑ Exit (gx≈8)
"""

from __future__ import annotations
import hashlib
from typing import Any

# ── Store meta ────────────────────────────────────────────────────────────────

STORE_META = {
    "name":    "The Home Depot – West Roxbury, MA",
    "address": "1213 VFW Pkwy, West Roxbury, MA 02132",
    "phone":   "(617) 323-4434",
    "store_id": "2665",
    "hours": {
        "Mon–Sat": "6:00 AM – 10:00 PM",
        "Sunday":  "8:00 AM – 8:00 PM",
    },
    "google_maps_url": (
        "https://www.google.com/maps/search/?api=1"
        "&query=Home+Depot+West+Roxbury+MA"
    ),
}

GRID     = {"cols": 16, "rows": 10, "cell_px": 60}
# Entrance/exit at bottom-center-left, matching the real store map
ENTRANCE = {"gx": 6.0, "gy": 9.5, "label": "Entrance / Exit"}
EXIT     = {"gx": 8.0, "gy": 9.5, "label": "Exit / Returns"}

# ── Store sections (positions derived from HD mobile app map) ─────────────────

SECTIONS: list[dict[str, Any]] = [

    # ── Outdoor Garden – full-height left strip ───────────────────────────────
    {"id":"garden",       "label":"Garden & Outdoors",     "gx":0,  "gy":0,  "gw":2, "gh":8.5, "color":"#86EFAC"},

    # ── Back of store (gy 0-3) ────────────────────────────────────────────────
    {"id":"electrical",   "label":"Electrical",            "gx":2,  "gy":0,  "gw":4, "gh":3,   "color":"#FDE68A"},
    {"id":"tools",        "label":"Tools & Equipment",     "gx":6,  "gy":0,  "gw":2, "gh":3,   "color":"#FB923C"},
    {"id":"hardware",     "label":"Hardware",              "gx":8,  "gy":0,  "gw":3, "gh":3,   "color":"#D1D5DB"},
    {"id":"windows_doors","label":"Windows & Doors",       "gx":11, "gy":0,  "gw":3, "gh":3,   "color":"#BAE6FD"},
    {"id":"millwork",     "label":"Millwork & Trim",       "gx":14, "gy":0,  "gw":2, "gh":3,   "color":"#D4B896"},

    # ── Middle row (gy 3-6) ───────────────────────────────────────────────────
    {"id":"lighting",     "label":"Lighting & Fans",       "gx":2,  "gy":3,  "gw":4, "gh":3,   "color":"#FEF08A"},
    {"id":"appliances",   "label":"Appliances & Kitchens", "gx":6,  "gy":3,  "gw":4, "gh":3,   "color":"#CBD5E1"},
    {"id":"flooring",     "label":"Carpet & Flooring",     "gx":10, "gy":3,  "gw":3, "gh":3,   "color":"#B8860B"},
    {"id":"storage",      "label":"Storage & Org",         "gx":13, "gy":3,  "gw":3, "gh":3,   "color":"#6EE7B7"},

    # ── Front-middle row (gy 6-8.5) ───────────────────────────────────────────
    {"id":"bath",         "label":"Indoor Garden & Bath",  "gx":2,  "gy":6,  "gw":3, "gh":2.5, "color":"#BBF7D0"},
    {"id":"paint",        "label":"Paint & Supplies",      "gx":5,  "gy":6,  "gw":2, "gh":2.5, "color":"#FCA5A5"},
    {"id":"plumbing",     "label":"Plumbing",              "gx":7,  "gy":6,  "gw":2, "gh":2.5, "color":"#93C5FD"},
    {"id":"lumber",       "label":"Lumber",                "gx":9,  "gy":6,  "gw":4, "gh":2.5, "color":"#C8A96E"},
    {"id":"building_mat", "label":"Building Materials",    "gx":13, "gy":6,  "gw":3, "gh":2.5, "color":"#BFA07A"},

    # ── Checkout / front row (gy 8.5-9.5) ────────────────────────────────────
    {"id":"checkout",     "label":"Checkout",              "gx":2,  "gy":8.5,"gw":9, "gh":1,   "color":"#F3F4F6"},
    {"id":"pro_desk",     "label":"Pro Desk",              "gx":11, "gy":8.5,"gw":5, "gh":1,   "color":"#FED7AA"},
]

SECTION_MAP: dict[str, dict] = {s["id"]: s for s in SECTIONS}

# Horizontal corridor y-coords used by route planner to keep paths in aisles
H_LANES = [3.0, 6.0, 8.5, 9.5]

# ── Category → section mapping ────────────────────────────────────────────────

_CAT_RULES: list[tuple[list[str], str]] = [
    (["lumber","wood","plywood","osb","beam","board","2x4","2x6","stud"],               "lumber"),
    (["drywall","cement","concrete","insulation","roofing","siding","framing","masonry"],"building_mat"),
    (["door","window","glass","sliding"],                                                "windows_doors"),
    (["flooring","tile","laminate","hardwood","vinyl","carpet","rug","grout","underlayment","thinset"], "flooring"),
    (["moulding","trim","baseboard","casing","stair"],                                  "millwork"),
    (["plumbing","pipe","faucet","toilet","sink","drain","water heater","pvc","copper","valve","shower"], "plumbing"),
    (["electrical","wire","outlet","switch","breaker","panel","conduit","plug","extension cord","gfci"], "electrical"),
    (["paint","primer","stain","caulk","brush","roller","tape","drop cloth","spray"],   "paint"),
    (["hardware","screw","bolt","nail","anchor","hinge","lock","deadbolt","knob","pull"], "hardware"),
    (["power tool","drill","saw","sander","grinder","nailer","compressor","generator","tool","workbench","ladder","level"], "tools"),
    (["storage","shelf","shelving","cabinet","bin","hook","rack","organizer","safe","toolbox"], "storage"),
    (["kitchen","countertop","backsplash","island","range hood","cabinet"],              "appliances"),
    (["bath","vanity","shower head","towel bar","toilet paper holder"],                  "bath"),
    (["lighting","light","fixture","bulb","ceiling fan","lamp","led","chandelier","sconce"], "lighting"),
    (["appliance","refrigerator","washer","dryer","dishwasher","range","oven","microwave","hvac","air conditioner","dehumidifier"], "appliances"),
    (["garden","plant","soil","mulch","fertilizer","seed","hose","sprinkler","mower","leaf blower","edger","outdoor","patio","grill","bbq","seasonal","christmas","holiday"], "garden"),
    (["blind","shade","curtain","décor","art","mirror","rug","mat"],                    "flooring"),
]

def infer_section(title: str, category_hint: str = "") -> str:
    text = (title + " " + category_hint).lower()
    for keywords, section in _CAT_RULES:
        if any(kw in text for kw in keywords):
            return section
    return "hardware"   # safe default


def product_grid_position(section_id: str, product_id: str) -> tuple[float, float]:
    """Deterministic placement inside section based on product ID hash."""
    sec = SECTION_MAP.get(section_id, SECTION_MAP["hardware"])
    h = int(hashlib.md5(str(product_id).encode()).hexdigest(), 16)
    rx = ((h & 0xFF)       / 255.0) * max(0.1, sec["gw"] - 0.5) + 0.25
    ry = ((h >> 8 & 0xFF)  / 255.0) * max(0.1, sec["gh"] - 0.3) + 0.15
    return round(sec["gx"] + rx, 2), round(sec["gy"] + ry, 2)


# ── Aisle-coordinate helpers ──────────────────────────────────────────────────

# Matches existing aisle_num formula: int((gx / 16) * 35) + 1
# Garden zone uses prefix "G"
def gx_to_aisle(gx: float) -> str:
    """Convert grid-x to HD aisle number string (e.g. '07' or 'G2')."""
    if gx < 2.0:
        g = max(1, min(4, int(gx * 2) + 1))
        return f"G{g}"
    n = max(1, min(35, int((gx / GRID["cols"]) * 35) + 1))
    return f"{n:02d}"


def gy_to_bay(gy: float) -> int:
    """Convert grid-y to bay number (Bay 1 = front/checkout side, Bay 6 = back wall)."""
    normalized = 1.0 - min(1.0, max(0.0, gy / 8.5))
    return max(1, min(6, int(normalized * 6) + 1))


def aisle_label(section_id: str, gx: float, gy: float = 4.5) -> str:
    aisle_num = max(1, min(35, int((gx / GRID["cols"]) * 35) + 1))
    bay_num = gy_to_bay(gy)
    sec = SECTION_MAP.get(section_id, {})
    return f"{sec.get('label','Dept')} · Aisle {aisle_num:02d}, Bay {bay_num}"


def build_nav_steps(
    from_gx: float, from_gy: float,
    to_gx: float, to_gy: float,
    product: dict,
) -> list[dict]:
    """
    Generate human-readable step-by-step navigation instructions.
    Returns list of {icon, text} dicts — first item is the current action.
    """
    steps: list[dict] = []
    dx = to_gx - from_gx
    dy = to_gy - from_gy   # negative = deeper into store (back wall at gy=0)

    from_aisle_str = gx_to_aisle(from_gx)
    to_aisle_str   = gx_to_aisle(to_gx)
    to_bay         = gy_to_bay(to_gy)

    def _aisle_int(s: str) -> int:
        return int(s) if s.isdigit() or s[1:].isdigit() else 0

    aisle_delta = abs(_aisle_int(to_aisle_str) - _aisle_int(from_aisle_str.lstrip("G")))
    sec_label   = SECTION_MAP.get(product.get("section", "hardware"), {}).get("label", "the department")
    prod_name   = product.get("name", "").split(",")[0]

    # ── Step 0: entering the store ─────────────────────────────────────
    if from_gy >= 8.5:
        steps.append({"icon": "🚪", "text": "Enter through the main entrance"})

    # ── Step 1: lateral movement – which aisle column ──────────────────
    if abs(dx) > 0.5:
        if to_gx < 2.0:
            steps.append({"icon": "←", "text": "Turn left into the Garden & Outdoors section"})
        elif dx < 0:
            aisle_word = f"{aisle_delta} aisle{'s' if aisle_delta != 1 else ''}"
            steps.append({"icon": "←", "text": f"Walk left past {aisle_word} → stop at Aisle {to_aisle_str}"})
        else:
            aisle_word = f"{aisle_delta} aisle{'s' if aisle_delta != 1 else ''}"
            steps.append({"icon": "→", "text": f"Walk right past {aisle_word} → stop at Aisle {to_aisle_str}"})

    # ── Step 2: depth into the aisle ───────────────────────────────────
    if abs(dy) > 1.0:
        depth_phrase = "toward the back of the store" if dy < 0 else "toward checkout (front)"
        steps.append({"icon": "↑" if dy < 0 else "↓",
                       "text": f"Enter Aisle {to_aisle_str} → walk {depth_phrase} to Bay {to_bay}"})
    elif abs(dx) > 0.5:
        steps.append({"icon": "↑", "text": f"Enter Aisle {to_aisle_str} at Bay {to_bay}"})

    # ── Step 3: arrival ────────────────────────────────────────────────
    steps.append({"icon": "📦",
                  "text": f"{prod_name} — {sec_label}, Aisle {to_aisle_str}, Bay {to_bay}"})

    return steps


# ── Offline fallback product catalogue ───────────────────────────────────────
# gx/gy values match the real store grid above.

FALLBACK_PRODUCTS: list[dict[str, Any]] = [
    # ── Tools (back of store, gx 6-8, gy 0-3) ─────────────────────────────────
    {"id":"dewalt_drill","name":"20V MAX Cordless Drill/Driver Kit","brand":"DEWALT","category":"Tools",
     "section":"tools","gx":6.3,"gy":0.5,"aisle":"Tools · Aisle 14","price":179.0,"unit":"kit",
     "tags":["drill","cordless","dewalt","power tool","20v","driver"]},
    {"id":"dewalt_circ","name":"7-1/4 in. Circular Saw 20V MAX","brand":"DEWALT","category":"Tools",
     "section":"tools","gx":6.7,"gy":0.5,"aisle":"Tools · Aisle 15","price":149.0,"unit":"each",
     "tags":["circular saw","saw","dewalt","cordless","cutting"]},
    {"id":"m18_combo","name":"M18 18V Cordless 6-Tool Combo Kit","brand":"Milwaukee","category":"Tools",
     "section":"tools","gx":7.2,"gy":0.5,"aisle":"Tools · Aisle 16","price":499.0,"unit":"kit",
     "tags":["milwaukee","m18","combo kit","cordless","power tool"]},
    {"id":"6ft_ladder","name":"6 ft. Fiberglass Step Ladder (300 lb.)","brand":"Werner","category":"Tools",
     "section":"tools","gx":6.5,"gy":1.2,"aisle":"Tools · Aisle 15","price":79.98,"unit":"each",
     "tags":["ladder","step ladder","6 foot","fiberglass","werner"]},
    {"id":"tape_measure","name":"25 ft. Tape Measure","brand":"Stanley","category":"Tools",
     "section":"tools","gx":7.5,"gy":1.4,"aisle":"Tools · Aisle 17","price":14.97,"unit":"each",
     "tags":["tape measure","measuring","stanley","25 ft","tool"]},
    {"id":"stud_finder","name":"Pro Sensor 5000+ Stud Finder","brand":"Franklin Sensors","category":"Tools",
     "section":"tools","gx":7.0,"gy":1.2,"aisle":"Tools · Aisle 16","price":49.97,"unit":"each",
     "tags":["stud finder","wall","sensor","franklin","drywall"]},

    # ── Electrical (back-left, gx 2-6, gy 0-3) ────────────────────────────────
    {"id":"romex_12","name":"12/2 NM-B Wire (250 ft.)","brand":"Southwire","category":"Electrical",
     "section":"electrical","gx":2.8,"gy":0.6,"aisle":"Electrical · Aisle 07","price":89.98,"unit":"250 ft roll",
     "tags":["wire","romex","12 gauge","electrical","southwire","wiring"]},
    {"id":"gfci_outlet","name":"15-Amp GFCI Outlet White","brand":"Leviton","category":"Electrical",
     "section":"electrical","gx":3.4,"gy":0.6,"aisle":"Electrical · Aisle 08","price":17.98,"unit":"each",
     "tags":["gfci","outlet","leviton","electrical","bathroom","kitchen"]},
    {"id":"led_bulb","name":"A19 LED 60W Equivalent Soft White (8-Pack)","brand":"Cree","category":"Electrical",
     "section":"electrical","gx":4.0,"gy":0.6,"aisle":"Electrical · Aisle 10","price":12.98,"unit":"8-pack",
     "tags":["led","bulb","60 watt","cree","light bulb","a19"]},
    {"id":"breaker_20a","name":"20-Amp Single-Pole Circuit Breaker","brand":"Square D","category":"Electrical",
     "section":"electrical","gx":4.6,"gy":1.0,"aisle":"Electrical · Aisle 11","price":11.98,"unit":"each",
     "tags":["circuit breaker","20 amp","square d","panel","electrical"]},
    {"id":"ext_cord_50","name":"50 ft. 12/3 Heavy-Duty Extension Cord","brand":"Southwire","category":"Electrical",
     "section":"electrical","gx":5.2,"gy":0.6,"aisle":"Electrical · Aisle 12","price":39.98,"unit":"each",
     "tags":["extension cord","50 ft","outdoor","heavy duty","12 gauge","southwire"]},

    # ── Hardware (back-center, gx 8-11, gy 0-3) ───────────────────────────────
    {"id":"2in_screws","name":"#8 x 2 in. Phillips Bugle-Head Screw (1 lb.)","brand":"Grip-Rite","category":"Hardware",
     "section":"hardware","gx":8.3,"gy":0.6,"aisle":"Hardware · Aisle 19","price":8.98,"unit":"1 lb box",
     "tags":["screws","drywall screw","2 inch","#8","phillips","grip-rite","fastener"]},
    {"id":"3in_nails","name":"16d 3-1/2 in. Common Nails (1 lb.)","brand":"Grip-Rite","category":"Hardware",
     "section":"hardware","gx":8.8,"gy":0.6,"aisle":"Hardware · Aisle 20","price":5.98,"unit":"1 lb box",
     "tags":["nails","16d","3.5 inch","common nail","framing","grip-rite"]},
    {"id":"deadbolt","name":"Keyed Entry Deadbolt Satin Nickel","brand":"Schlage","category":"Hardware",
     "section":"hardware","gx":9.3,"gy":0.6,"aisle":"Hardware · Aisle 21","price":39.98,"unit":"each",
     "tags":["deadbolt","lock","schlage","satin nickel","door","security","keyed"]},
    {"id":"toggle_bolt","name":"1/4 in. Toggle Bolt (10-Pack)","brand":"Hillman","category":"Hardware",
     "section":"hardware","gx":9.8,"gy":1.0,"aisle":"Hardware · Aisle 22","price":4.48,"unit":"10-pack",
     "tags":["toggle bolt","wall anchor","1/4 inch","hollow wall","hillman","fastener"]},
    {"id":"duct_tape","name":"3.77 in. x 35 yd. Multi-Use Duct Tape","brand":"3M","category":"Hardware",
     "section":"hardware","gx":10.2,"gy":0.6,"aisle":"Hardware · Aisle 23","price":11.97,"unit":"each",
     "tags":["duct tape","3m","tape","multi-use","silver","utility"]},

    # ── Lighting (middle-left, gx 2-6, gy 3-6) ────────────────────────────────
    {"id":"led_shop_light","name":"4 ft. LED Shop Light 4800 Lumens","brand":"Commercial Electric","category":"Lighting",
     "section":"lighting","gx":2.6,"gy":3.6,"aisle":"Lighting · Aisle 07","price":34.97,"unit":"each",
     "tags":["shop light","led","4 foot","garage","4800 lumen","commercial electric","ceiling"]},
    {"id":"ceiling_fan","name":"52 in. Matte Black Ceiling Fan w/ Remote","brand":"Hampton Bay","category":"Lighting",
     "section":"lighting","gx":3.2,"gy":3.6,"aisle":"Lighting · Aisle 08","price":109.0,"unit":"each",
     "tags":["ceiling fan","52 inch","hampton bay","black","remote","lighting","fan"]},
    {"id":"motion_sensor","name":"150° Motion-Sensing Security Light","brand":"Defiant","category":"Lighting",
     "section":"lighting","gx":3.8,"gy":3.6,"aisle":"Lighting · Aisle 09","price":34.97,"unit":"each",
     "tags":["motion sensor","security light","outdoor","defiant","floodlight","150 degree"]},
    {"id":"recessed_light","name":"6 in. Canless Recessed LED (4-Pack)","brand":"Commercial Electric","category":"Lighting",
     "section":"lighting","gx":4.4,"gy":4.0,"aisle":"Lighting · Aisle 11","price":59.97,"unit":"4-pack",
     "tags":["recessed light","6 inch","led","canless","4-pack","commercial electric","ceiling"]},

    # ── Appliances (middle-center, gx 6-10, gy 3-6) ───────────────────────────
    {"id":"water_heater","name":"50 Gal. 40000 BTU Natural Gas Water Heater","brand":"Rheem","category":"Appliances",
     "section":"appliances","gx":6.5,"gy":3.6,"aisle":"Appliances · Aisle 15","price":629.0,"unit":"each",
     "tags":["water heater","50 gallon","rheem","natural gas","40000 btu","tank"]},
    {"id":"dehumidifier","name":"50-Pint Dehumidifier ENERGY STAR","brand":"hOmeLabs","category":"Appliances",
     "section":"appliances","gx":7.2,"gy":3.6,"aisle":"Appliances · Aisle 17","price":219.0,"unit":"each",
     "tags":["dehumidifier","50 pint","energy star","homelabs","basement","moisture"]},

    # ── Flooring / Carpet (middle-center-right, gx 10-13, gy 3-6) ─────────────
    {"id":"porcelain_tile","name":"Merola Tile Hex 8.7 in. Porcelain (10 sq ft/case)","brand":"Merola","category":"Flooring",
     "section":"flooring","gx":10.4,"gy":3.6,"aisle":"Flooring · Aisle 24","price":12.45,"unit":"case/10 sq ft",
     "tags":["tile","porcelain","hex","merola","floor tile","bathroom","10 sq ft"]},
    {"id":"lvp_flooring","name":"Pergo LVP 6mm 20 mil 7.5 in. x 47 in.","brand":"Pergo","category":"Flooring",
     "section":"flooring","gx":11.0,"gy":3.6,"aisle":"Flooring · Aisle 25","price":3.19,"unit":"sq ft",
     "tags":["lvp","vinyl plank","pergo","waterproof","flooring","6mm","click lock"]},
    {"id":"grout","name":"Sanded Grout 25 lb. Linen","brand":"Custom Building Products","category":"Flooring",
     "section":"flooring","gx":11.6,"gy":4.0,"aisle":"Flooring · Aisle 26","price":21.97,"unit":"25 lb bag",
     "tags":["grout","sanded","25 lb","tile grout","floor","custom building"]},
    {"id":"thinset","name":"Fortified Thinset Mortar White 50 lb.","brand":"Custom Building Products","category":"Flooring",
     "section":"flooring","gx":12.2,"gy":3.6,"aisle":"Flooring · Aisle 27","price":19.97,"unit":"50 lb bag",
     "tags":["thinset","mortar","tile adhesive","50 lb","white","flooring"]},

    # ── Storage (middle-right, gx 13-16, gy 3-6) ──────────────────────────────
    {"id":"heavy_shelf","name":"5-Tier Heavy-Duty Steel Shelving (2000 lb.)","brand":"Husky","category":"Storage",
     "section":"storage","gx":13.4,"gy":3.6,"aisle":"Storage · Aisle 30","price":148.0,"unit":"each",
     "tags":["shelving","steel shelving","5 tier","husky","garage","2000 lb","heavy duty"]},
    {"id":"pegboard","name":"4 ft. x 4 ft. White Pegboard","brand":"Everbilt","category":"Storage",
     "section":"storage","gx":14.0,"gy":3.6,"aisle":"Storage · Aisle 31","price":19.97,"unit":"each",
     "tags":["pegboard","4x4","white","everbilt","wall organizer","garage","hooks"]},
    {"id":"plastic_bins","name":"6 Qt. Clear Stackable Storage Bins (6-Pack)","brand":"Sterilite","category":"Storage",
     "section":"storage","gx":14.6,"gy":4.0,"aisle":"Storage · Aisle 32","price":24.98,"unit":"6-pack",
     "tags":["storage bin","clear","6 qt","sterilite","stackable","organizer","plastic"]},

    # ── Bath / Indoor Garden (front-left, gx 2-5, gy 6-8.5) ──────────────────
    {"id":"toilets_std","name":"Elongated Toilet Complete 1.28 GPF WaterSense","brand":"Glacier Bay","category":"Bath",
     "section":"bath","gx":2.6,"gy":6.6,"aisle":"Indoor Garden & Bath · Aisle 07","price":128.0,"unit":"each",
     "tags":["toilet","elongated","1.28 gpf","watersense","glacier bay","bathroom"]},
    {"id":"shower_head","name":"5-Spray 4.7 in. Fixed Shower Head Chrome","brand":"Delta","category":"Bath",
     "section":"bath","gx":3.2,"gy":6.6,"aisle":"Indoor Garden & Bath · Aisle 08","price":32.88,"unit":"each",
     "tags":["shower head","delta","chrome","5-spray","4.7 inch","bathroom","fixed"]},

    # ── Paint (front-center-left, gx 5-7, gy 6-8.5) ──────────────────────────
    {"id":"behr_primer","name":"BEHR PREMIUM PLUS 1 gal. Interior Primer","brand":"BEHR","category":"Paint",
     "section":"paint","gx":5.3,"gy":6.6,"aisle":"Paint · Aisle 12","price":34.98,"unit":"1 gallon",
     "tags":["primer","behr","interior","gallon","paint","white"]},
    {"id":"behr_eggshell","name":"BEHR 1 gal. Eggshell Interior Paint","brand":"BEHR","category":"Paint",
     "section":"paint","gx":5.8,"gy":6.6,"aisle":"Paint · Aisle 13","price":42.98,"unit":"1 gallon",
     "tags":["paint","behr","eggshell","interior","gallon","wall"]},
    {"id":"purdy_brush","name":"4 in. XL Sprig Trim Brush","brand":"Purdy","category":"Paint",
     "section":"paint","gx":6.2,"gy":7.0,"aisle":"Paint · Aisle 14","price":19.98,"unit":"each",
     "tags":["paint brush","purdy","trim","4 inch","brush","wall"]},
    {"id":"roller_tray","name":"9 in. Roller Frame + Tray Kit","brand":"Wooster","category":"Paint",
     "section":"paint","gx":5.5,"gy":7.2,"aisle":"Paint · Aisle 13","price":14.98,"unit":"kit",
     "tags":["roller","tray","9 inch","paint roller","wooster","kit"]},
    {"id":"painters_tape","name":"1.88 in. x 60 yd Blue Painter's Tape (3-Pack)","brand":"ScotchBlue","category":"Paint",
     "section":"paint","gx":6.5,"gy":6.6,"aisle":"Paint · Aisle 15","price":16.97,"unit":"3-pack",
     "tags":["painters tape","scotchblue","masking tape","3m","blue tape","paint"]},

    # ── Plumbing (front-center, gx 7-9, gy 6-8.5) ────────────────────────────
    {"id":"pvc_4in","name":"4 in. x 10 ft. PVC DWV Pipe","brand":"Charlotte Pipe","category":"Plumbing",
     "section":"plumbing","gx":7.3,"gy":6.6,"aisle":"Plumbing · Aisle 17","price":13.48,"unit":"10 ft pipe",
     "tags":["pvc","pipe","4 inch","drain","dwv","plumbing","charlotte pipe"]},
    {"id":"ball_valve","name":"1/2 in. SharkBite Ball Valve","brand":"SharkBite","category":"Plumbing",
     "section":"plumbing","gx":7.7,"gy":6.6,"aisle":"Plumbing · Aisle 18","price":19.98,"unit":"each",
     "tags":["ball valve","sharkbite","1/2 inch","shutoff","plumbing","push-to-connect"]},
    {"id":"moen_faucet","name":"Adler 2-Handle Kitchen Faucet Chrome","brand":"Moen","category":"Plumbing",
     "section":"plumbing","gx":8.1,"gy":6.6,"aisle":"Plumbing · Aisle 19","price":109.0,"unit":"each",
     "tags":["faucet","kitchen faucet","moen","chrome","2-handle","sink"]},
    {"id":"wax_ring","name":"Universal Toilet Wax Ring with Flange","brand":"Fluidmaster","category":"Plumbing",
     "section":"plumbing","gx":7.5,"gy":7.2,"aisle":"Plumbing · Aisle 17","price":8.98,"unit":"each",
     "tags":["wax ring","toilet","fluidmaster","flange","plumbing","seal"]},
    {"id":"pex_half","name":"1/2 in. x 100 ft. PEX-A Tubing","brand":"Uponor","category":"Plumbing",
     "section":"plumbing","gx":8.4,"gy":6.6,"aisle":"Plumbing · Aisle 19","price":54.98,"unit":"100 ft coil",
     "tags":["pex","tubing","1/2 inch","100 ft","plumbing","uponor","water line"]},

    # ── Lumber (front-right, gx 9-13, gy 6-8.5) ──────────────────────────────
    {"id":"2x4_8","name":"2 in. x 4 in. x 8 ft. Stud","brand":"Generic","category":"Lumber",
     "section":"lumber","gx":9.4,"gy":6.6,"aisle":"Lumber · Aisle 21","price":4.28,"unit":"each",
     "tags":["2x4","stud","lumber","framing","wood","8 foot"]},
    {"id":"2x6_8","name":"2 in. x 6 in. x 8 ft. #2 Prime","brand":"Generic","category":"Lumber",
     "section":"lumber","gx":9.9,"gy":6.6,"aisle":"Lumber · Aisle 22","price":6.98,"unit":"each",
     "tags":["2x6","lumber","framing","wood","8 foot","dimensional"]},
    {"id":"plywood_half","name":"1/2 in. 4x8 Plywood Sheathing","brand":"Generic","category":"Lumber",
     "section":"lumber","gx":10.5,"gy":6.3,"aisle":"Lumber · Aisle 24","price":38.98,"unit":"4x8 sheet",
     "tags":["plywood","1/2 inch","4x8","sheathing","lumber","sheet"]},
    {"id":"osb_716","name":"7/16 in. 4x8 OSB Sheathing","brand":"Generic","category":"Lumber",
     "section":"lumber","gx":11.1,"gy":6.3,"aisle":"Lumber · Aisle 25","price":19.98,"unit":"4x8 sheet",
     "tags":["osb","oriented strand board","sheathing","7/16","4x8","lumber"]},

    # ── Building Materials (far front-right, gx 13-16, gy 6-8.5) ─────────────
    {"id":"drywall_half","name":"1/2 in. 4x8 Drywall Panel","brand":"USG","category":"Building Materials",
     "section":"building_mat","gx":13.4,"gy":6.6,"aisle":"Building Materials · Aisle 30","price":13.38,"unit":"4x8 sheet",
     "tags":["drywall","sheetrock","1/2 inch","4x8","usg","gypsum","wall"]},
    {"id":"joint_compound","name":"All-Purpose Joint Compound 4.5 gal.","brand":"USG","category":"Building Materials",
     "section":"building_mat","gx":13.9,"gy":7.0,"aisle":"Building Materials · Aisle 31","price":17.98,"unit":"4.5 gal pail",
     "tags":["joint compound","mud","drywall","usg","all purpose","4.5 gallon","finishing"]},

    # ── Garden & Outdoors (left strip, gx 0-2, gy 0-8) ────────────────────────
    {"id":"hose_50","name":"50 ft. Heavy-Duty Garden Hose","brand":"Gilmour","category":"Garden",
     "section":"garden","gx":0.5,"gy":3.5,"aisle":"Garden · Aisle 01","price":29.98,"unit":"each",
     "tags":["garden hose","50 ft","gilmour","hose","outdoor","water","watering"]},
    {"id":"mulch_bag","name":"2 cu. ft. Hardwood Brown Mulch","brand":"Vigoro","category":"Garden",
     "section":"garden","gx":0.8,"gy":4.2,"aisle":"Garden · Aisle 02","price":4.27,"unit":"2 cu ft bag",
     "tags":["mulch","hardwood","brown","vigoro","2 cubic foot","garden","landscape"]},
    {"id":"leaf_blower","name":"40V Cordless Brushless Leaf Blower","brand":"Ryobi","category":"Garden",
     "section":"garden","gx":1.2,"gy":5.0,"aisle":"Garden · Aisle 03","price":149.0,"unit":"tool only",
     "tags":["leaf blower","40v","ryobi","cordless","outdoor","yard","brushless"]},
    {"id":"rear_trigger_nozzle","name":"Rear Trigger 8-Pattern Nozzle","brand":"Gilmour","category":"Garden",
     "section":"garden","gx":0.6,"gy":2.8,"aisle":"Garden · Aisle 01","price":9.97,"unit":"each",
     "tags":["nozzle","hose nozzle","8 pattern","gilmour","garden","watering","rear trigger"]},
]

FALLBACK_MAP: dict[str, dict] = {p["id"]: p for p in FALLBACK_PRODUCTS}

# ── Helper functions ──────────────────────────────────────────────────────────

_STOP_WORDS = frozenset({
    "where","is","the","a","an","i","me","my","we","in","on","at","for",
    "of","and","or","to","do","can","you","your","it","its","find","need",
    "want","looking","please","some","any","get","show","help","have","what",
})

def search_fallback(query: str, max_results: int = 8) -> list[dict]:
    import re as _re
    q = query.lower()
    tokens = _re.findall(r"[a-z0-9]+", q)
    terms = [t for t in tokens if len(t) >= 2 and t not in _STOP_WORDS] or tokens

    scored: list[tuple[int, dict]] = []
    for p in FALLBACK_PRODUCTS:
        score = 0
        name = p["name"].lower()
        haystack = name + " " + p["brand"].lower() + " " + " ".join(p["tags"])
        matched_terms = 0
        for t in terms:
            term_matched = False
            if _re.search(rf"\b{_re.escape(t)}\b", name):
                score += 25; term_matched = True
            elif t in name:
                score += 10; term_matched = True
            if _re.search(rf"\b{_re.escape(t)}\b", haystack):
                score += 8; term_matched = True
            if t in p["tags"]:
                score += 15; term_matched = True
            if term_matched:
                matched_terms += 1
        if query.lower() in name:
            score += 50
        min_terms_required = min(2, len(terms)) if len(terms) > 1 else 1
        if score > 0 and matched_terms >= min_terms_required:
            scored.append((score, p))

    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored[:max_results]]


def plan_route(product_ids: list[str], products_lookup: list[dict] | None = None) -> dict:
    """Nearest-neighbour TSP from store entrance."""
    items: list[dict] = []
    lookup = {p["id"]: p for p in (products_lookup or [])}
    lookup.update(FALLBACK_MAP)
    for pid in product_ids:
        p = lookup.get(str(pid))
        if p:
            items.append(p)

    if not items:
        return {"order": [], "steps": [], "estimated_minutes": 0}

    visited: list[dict] = []
    remaining = list(items)
    cx, cy = ENTRANCE["gx"], ENTRANCE["gy"]
    while remaining:
        closest = min(remaining, key=lambda p: (p["gx"]-cx)**2 + (p["gy"]-cy)**2)
        visited.append(closest)
        cx, cy = closest["gx"], closest["gy"]
        remaining.remove(closest)

    steps = []
    for i, p in enumerate(visited, 1):
        steps.append({
            "stop": i,
            "product_id": p["id"],
            "product_name": p["name"],
            "brand": p.get("brand",""),
            "aisle": p["aisle"],
            "section": p["section"],
            "section_label": SECTION_MAP.get(p["section"], {}).get("label",""),
            "price": p.get("price", 0),
            "unit": p.get("unit",""),
            "image": p.get("image",""),
            "gx": p["gx"],
            "gy": p["gy"],
        })

    # Rough time estimate
    total = 0.0
    px, py = ENTRANCE["gx"], ENTRANCE["gy"]
    for s in steps:
        total += ((s["gx"]-px)**2 + (s["gy"]-py)**2)**0.5
        px, py = s["gx"], s["gy"]
    total += ((EXIT["gx"]-px)**2 + (EXIT["gy"]-py)**2)**0.5
    est = max(2, round(total * 6 / 1.2 / 60))

    return {"order": [s["product_id"] for s in steps], "steps": steps, "estimated_minutes": est}
