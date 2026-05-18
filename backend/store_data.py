"""
Costco Wholesale – Dedham, MA
Store layout and product database for the GemmaCart navigator.

Grid coordinate system: 12 columns (x) × 14 rows (y)
Origin (0,0) = top-left of warehouse floor.
Checkout row is y=13. Entrance is bottom-right; exit is bottom-left.
Each cell = 60 px when rendered on canvas.
"""

from __future__ import annotations
from typing import Any

# ── Store meta ──────────────────────────────────────────────────────────────

STORE_META = {
    "name": "Costco Wholesale – Dedham, MA",
    "address": "1 Dedham Place, Dedham, MA 02026",
    "phone": "(781) 329-3400",
    "hours": {
        "Mon–Fri": "10:00 AM – 8:30 PM",
        "Saturday": "9:30 AM – 6:00 PM",
        "Sunday":   "10:00 AM – 6:00 PM",
    },
}

# ── Grid configuration ───────────────────────────────────────────────────────

GRID = {"cols": 12, "rows": 14, "cell_px": 60}

# Entrance / exit grid positions (in cell-centre coordinates)
ENTRANCE = {"gx": 10.5, "gy": 13.0, "label": "Entrance"}
EXIT      = {"gx":  0.5, "gy": 13.0, "label": "Exit / Checkout"}

# ── Store sections ───────────────────────────────────────────────────────────
# Each section: id, display label, grid rect (gx,gy,gw,gh), hex colour

SECTIONS: list[dict[str, Any]] = [
    # Top stripe – services
    {"id": "food_court",    "label": "Food Court",       "gx": 0,  "gy": 0, "gw": 2,  "gh": 2,  "color": "#e74c3c"},
    {"id": "pharmacy",      "label": "Pharmacy",          "gx": 2,  "gy": 0, "gw": 2,  "gh": 1,  "color": "#3498db"},
    {"id": "optical",       "label": "Optical",           "gx": 4,  "gy": 0, "gw": 2,  "gh": 1,  "color": "#2980b9"},
    {"id": "electronics",   "label": "Electronics",       "gx": 6,  "gy": 0, "gw": 3,  "gh": 3,  "color": "#8e44ad"},
    {"id": "clothing",      "label": "Clothing & Luggage","gx": 9,  "gy": 0, "gw": 3,  "gh": 3,  "color": "#c0392b"},

    # Mid-upper
    {"id": "seasonal",      "label": "Seasonal",          "gx": 2,  "gy": 1, "gw": 2,  "gh": 1,  "color": "#e67e22"},
    {"id": "hearing_aid",   "label": "Hearing Aid",       "gx": 4,  "gy": 1, "gw": 2,  "gh": 1,  "color": "#2471a3"},
    {"id": "home",          "label": "Home & Garden",     "gx": 0,  "gy": 2, "gw": 3,  "gh": 2,  "color": "#16a085"},
    {"id": "furniture",     "label": "Furniture",         "gx": 3,  "gy": 2, "gw": 3,  "gh": 2,  "color": "#795548"},
    {"id": "appliances",    "label": "Appliances",        "gx": 0,  "gy": 4, "gw": 3,  "gh": 2,  "color": "#607d8b"},
    {"id": "office",        "label": "Office & School",   "gx": 3,  "gy": 4, "gw": 3,  "gh": 2,  "color": "#5d6d7e"},
    {"id": "health_beauty", "label": "Health & Beauty",   "gx": 6,  "gy": 3, "gw": 3,  "gh": 3,  "color": "#00bcd4"},
    {"id": "vitamins",      "label": "Vitamins",          "gx": 9,  "gy": 3, "gw": 3,  "gh": 3,  "color": "#009688"},

    # Mid floor – grocery
    {"id": "paper_cleaning","label": "Paper & Cleaning",  "gx": 0,  "gy": 6, "gw": 4,  "gh": 2,  "color": "#27ae60"},
    {"id": "snacks",        "label": "Snacks & Candy",    "gx": 4,  "gy": 6, "gw": 4,  "gh": 2,  "color": "#f39c12"},
    {"id": "beverages",     "label": "Beverages",         "gx": 8,  "gy": 6, "gw": 4,  "gh": 2,  "color": "#2196f3"},
    {"id": "breakfast",     "label": "Breakfast & Cereal","gx": 0,  "gy": 8, "gw": 4,  "gh": 2,  "color": "#fbc02d"},
    {"id": "canned_goods",  "label": "Canned Goods",      "gx": 4,  "gy": 8, "gw": 4,  "gh": 2,  "color": "#a1887f"},
    {"id": "international", "label": "International Foods","gx": 8,  "gy": 8, "gw": 4,  "gh": 2,  "color": "#ff7043"},

    # Back wall – perishables
    {"id": "frozen",        "label": "Frozen Foods",      "gx": 0,  "gy": 10, "gw": 4, "gh": 3,  "color": "#80deea"},
    {"id": "dairy",         "label": "Dairy & Eggs",      "gx": 4,  "gy": 10, "gw": 4, "gh": 2,  "color": "#fff9c4"},
    {"id": "bakery",        "label": "Bakery",            "gx": 4,  "gy": 12, "gw": 4, "gh": 1,  "color": "#ffccbc"},
    {"id": "deli",          "label": "Deli",              "gx": 8,  "gy": 10, "gw": 2, "gh": 2,  "color": "#f8bbd0"},
    {"id": "meat_seafood",  "label": "Meat & Seafood",    "gx": 10, "gy": 10, "gw": 2, "gh": 2,  "color": "#ef9a9a"},
    {"id": "produce",       "label": "Fresh Produce",     "gx": 8,  "gy": 12, "gw": 4, "gh": 1,  "color": "#a5d6a7"},

    # Checkout strip
    {"id": "checkout",      "label": "Checkout",          "gx": 0,  "gy": 13, "gw": 12, "gh": 1, "color": "#ecf0f1"},
]

# Build lookup: section_id → section dict
SECTION_MAP: dict[str, dict] = {s["id"]: s for s in SECTIONS}

# ── Product database ──────────────────────────────────────────────────────────
# Each product:
#   id, name, brand, category, section_id,
#   gx/gy (exact grid float coords for pin),
#   aisle (human label), price, unit, tags

PRODUCTS: list[dict[str, Any]] = [

    # ── FRESH PRODUCE ────────────────────────────────────────────────────────
    {"id":"spinach",     "name":"Organic Baby Spinach",          "brand":"Kirkland Signature","category":"Produce",
     "section":"produce","gx":8.5, "gy":12.4,"aisle":"Produce – Left Wall",
     "price":5.99,  "unit":"2 lb bag",   "tags":["spinach","greens","salad","organic","leafy"]},
    {"id":"strawberries","name":"Organic Strawberries",          "brand":"Driscoll's",        "category":"Produce",
     "section":"produce","gx":9.2, "gy":12.4,"aisle":"Produce – Left Wall",
     "price":7.99,  "unit":"2 lb",       "tags":["strawberries","berries","fruit","organic"]},
    {"id":"blueberries", "name":"Organic Blueberries",           "brand":"Kirkland Signature","category":"Produce",
     "section":"produce","gx":9.8, "gy":12.4,"aisle":"Produce – Left Wall",
     "price":9.49,  "unit":"3 lb",       "tags":["blueberries","berries","fruit","organic"]},
    {"id":"broccoli",    "name":"Broccoli Florets",              "brand":"Organic",           "category":"Produce",
     "section":"produce","gx":10.4,"gy":12.4,"aisle":"Produce – Center",
     "price":4.99,  "unit":"3 lb bag",   "tags":["broccoli","vegetable","green","florets"]},
    {"id":"avocados",    "name":"Hass Avocados",                 "brand":"Fresh",             "category":"Produce",
     "section":"produce","gx":11.0,"gy":12.4,"aisle":"Produce – Right End",
     "price":6.99,  "unit":"6-pack",     "tags":["avocado","avocados","guacamole","fruit"]},
    {"id":"romaine",     "name":"Organic Romaine Hearts",        "brand":"Kirkland Signature","category":"Produce",
     "section":"produce","gx":8.8, "gy":12.6,"aisle":"Produce – Left Wall",
     "price":4.49,  "unit":"6-pack",     "tags":["romaine","lettuce","salad","hearts","organic"]},
    {"id":"bananas",     "name":"Bananas",                       "brand":"Fresh",             "category":"Produce",
     "section":"produce","gx":9.5, "gy":12.6,"aisle":"Produce – Center",
     "price":1.99,  "unit":"~3.5 lb",    "tags":["bananas","banana","fruit","yellow"]},
    {"id":"apples",      "name":"Gala Apples",                   "brand":"Fresh",             "category":"Produce",
     "section":"produce","gx":10.1,"gy":12.6,"aisle":"Produce – Center",
     "price":6.99,  "unit":"5 lb bag",   "tags":["apples","apple","gala","fruit"]},
    {"id":"spring_mix",  "name":"Organic Spring Mix",            "brand":"Kirkland Signature","category":"Produce",
     "section":"produce","gx":10.7,"gy":12.6,"aisle":"Produce – Right End",
     "price":5.49,  "unit":"1 lb",       "tags":["spring mix","salad","greens","organic","lettuce"]},
    {"id":"tomatoes",    "name":"Grape Tomatoes",                "brand":"NatureSweet",       "category":"Produce",
     "section":"produce","gx":11.3,"gy":12.6,"aisle":"Produce – Right End",
     "price":5.99,  "unit":"2 lb",       "tags":["tomatoes","tomato","grape","cherry","vegetable"]},

    # ── MEAT & SEAFOOD ───────────────────────────────────────────────────────
    {"id":"chicken_breast","name":"Boneless Skinless Chicken Breast","brand":"Kirkland Signature","category":"Meat",
     "section":"meat_seafood","gx":10.3,"gy":10.3,"aisle":"Meat – Aisle 1",
     "price":23.99, "unit":"~6 lb avg",  "tags":["chicken","chicken breast","poultry","protein"]},
    {"id":"ground_beef", "name":"Ground Beef 90/10",              "brand":"Kirkland Signature","category":"Meat",
     "section":"meat_seafood","gx":10.8,"gy":10.3,"aisle":"Meat – Aisle 1",
     "price":19.99, "unit":"~5 lb avg",  "tags":["ground beef","beef","hamburger","mince"]},
    {"id":"salmon",      "name":"Atlantic Salmon Fillets",         "brand":"Kirkland Signature","category":"Seafood",
     "section":"meat_seafood","gx":10.3,"gy":10.7,"aisle":"Seafood – Aisle 2",
     "price":29.99, "unit":"~3 lb avg",  "tags":["salmon","fish","seafood","atlantic","fillet"]},
    {"id":"bacon",       "name":"Thick Cut Bacon",                 "brand":"Kirkland Signature","category":"Meat",
     "section":"meat_seafood","gx":10.8,"gy":10.7,"aisle":"Meat – Aisle 2",
     "price":16.99, "unit":"4 lb pkg",   "tags":["bacon","pork","breakfast meat","strips"]},
    {"id":"pork_tenderloin","name":"Pork Tenderloin",             "brand":"Kirkland Signature","category":"Meat",
     "section":"meat_seafood","gx":10.3,"gy":11.1,"aisle":"Meat – Aisle 3",
     "price":14.99, "unit":"~2.5 lb avg","tags":["pork","tenderloin","loin","protein"]},
    {"id":"shrimp",      "name":"Frozen Cooked Shrimp",            "brand":"Kirkland Signature","category":"Seafood",
     "section":"meat_seafood","gx":10.8,"gy":11.1,"aisle":"Seafood – Aisle 3",
     "price":17.99, "unit":"2 lb bag",   "tags":["shrimp","prawns","seafood","frozen","cooked"]},

    # ── DELI ─────────────────────────────────────────────────────────────────
    {"id":"rotisserie",  "name":"Rotisserie Chicken",             "brand":"Kirkland Signature","category":"Deli",
     "section":"deli",  "gx":8.3, "gy":10.3,"aisle":"Deli – Front",
     "price":4.99,  "unit":"whole chicken","tags":["rotisserie","chicken","hot food","deli","cooked"]},
    {"id":"sliced_turkey","name":"Oven Roasted Turkey Breast",    "brand":"Kirkland Signature","category":"Deli",
     "section":"deli",  "gx":8.8, "gy":10.3,"aisle":"Deli – Front",
     "price":11.99, "unit":"2 lb pkg",   "tags":["turkey","deli meat","sliced","sandwich","cold cuts"]},
    {"id":"pepperoni",   "name":"Pepperoni Slices",               "brand":"Hormel",            "category":"Deli",
     "section":"deli",  "gx":8.3, "gy":10.7,"aisle":"Deli – Back",
     "price":9.99,  "unit":"2 lb pkg",   "tags":["pepperoni","pizza","deli","salami","meat"]},
    {"id":"prosciutto",  "name":"Prosciutto di Parma",            "brand":"Citterio",          "category":"Deli",
     "section":"deli",  "gx":8.8, "gy":10.7,"aisle":"Deli – Back",
     "price":14.99, "unit":"12 oz",      "tags":["prosciutto","italian","ham","deli","charcuterie"]},

    # ── BAKERY ───────────────────────────────────────────────────────────────
    {"id":"croissants",  "name":"All Butter Croissants",          "brand":"Kirkland Signature","category":"Bakery",
     "section":"bakery", "gx":4.5, "gy":12.4,"aisle":"Bakery – Left",
     "price":8.99,  "unit":"12-pack",    "tags":["croissants","bread","pastry","butter","breakfast"]},
    {"id":"muffins",     "name":"Chocolate Chip Muffins",         "brand":"Kirkland Signature","category":"Bakery",
     "section":"bakery", "gx":5.2, "gy":12.4,"aisle":"Bakery – Center",
     "price":9.99,  "unit":"12-pack",    "tags":["muffins","chocolate chip","bakery","breakfast","baked"]},
    {"id":"sourdough",   "name":"Sourdough Bread Loaves",         "brand":"Kirkland Signature","category":"Bakery",
     "section":"bakery", "gx":5.9, "gy":12.4,"aisle":"Bakery – Center",
     "price":5.99,  "unit":"2-pack",     "tags":["sourdough","bread","loaf","baked","bakery"]},
    {"id":"cookies",     "name":"Chocolate Chunk Cookies",        "brand":"Kirkland Signature","category":"Bakery",
     "section":"bakery", "gx":6.6, "gy":12.4,"aisle":"Bakery – Right",
     "price":9.99,  "unit":"24-pack",    "tags":["cookies","chocolate chip","baked","dessert","sweets"]},
    {"id":"bagels",      "name":"Everything Bagels",              "brand":"Kirkland Signature","category":"Bakery",
     "section":"bakery", "gx":7.3, "gy":12.4,"aisle":"Bakery – Right",
     "price":7.99,  "unit":"12-pack",    "tags":["bagels","everything bagel","bread","breakfast"]},

    # ── DAIRY & EGGS ─────────────────────────────────────────────────────────
    {"id":"whole_milk",  "name":"Whole Milk",                     "brand":"Kirkland Signature","category":"Dairy",
     "section":"dairy",  "gx":4.5, "gy":10.4,"aisle":"Dairy – Aisle 1",
     "price":5.79,  "unit":"1 gallon",   "tags":["milk","whole milk","dairy","gallon"]},
    {"id":"almond_milk", "name":"Unsweetened Almond Milk",        "brand":"Kirkland Signature","category":"Dairy",
     "section":"dairy",  "gx":5.1, "gy":10.4,"aisle":"Dairy – Aisle 1",
     "price":9.99,  "unit":"6-pack 32oz","tags":["almond milk","milk alternative","dairy free","plant based"]},
    {"id":"eggs",        "name":"Large Eggs",                     "brand":"Kirkland Signature","category":"Dairy",
     "section":"dairy",  "gx":5.7, "gy":10.4,"aisle":"Dairy – Aisle 2",
     "price":7.49,  "unit":"24-count",   "tags":["eggs","large eggs","dairy"]},
    {"id":"butter",      "name":"Salted Butter",                  "brand":"Kirkland Signature","category":"Dairy",
     "section":"dairy",  "gx":6.3, "gy":10.4,"aisle":"Dairy – Aisle 2",
     "price":9.99,  "unit":"4 × 1 lb",  "tags":["butter","salted","dairy","baking"]},
    {"id":"greek_yogurt","name":"Greek Yogurt Plain",             "brand":"Chobani",           "category":"Dairy",
     "section":"dairy",  "gx":6.9, "gy":10.4,"aisle":"Dairy – Aisle 3",
     "price":8.99,  "unit":"32 oz × 2", "tags":["yogurt","greek yogurt","chobani","protein","dairy"]},
    {"id":"cheddar",     "name":"Sharp Cheddar Cheese Block",     "brand":"Tillamook",         "category":"Dairy",
     "section":"dairy",  "gx":4.5, "gy":11.0,"aisle":"Dairy – Aisle 4",
     "price":12.99, "unit":"4 lb block", "tags":["cheddar","cheese","sharp","tillamook","dairy"]},
    {"id":"parmesan",    "name":"Shredded Parmesan Cheese",       "brand":"Kirkland Signature","category":"Dairy",
     "section":"dairy",  "gx":5.1, "gy":11.0,"aisle":"Dairy – Aisle 4",
     "price":11.99, "unit":"2 lb bag",   "tags":["parmesan","cheese","italian","shredded","dairy"]},
    {"id":"cream_cheese","name":"Cream Cheese",                   "brand":"Philadelphia",      "category":"Dairy",
     "section":"dairy",  "gx":5.7, "gy":11.0,"aisle":"Dairy – Aisle 5",
     "price":8.99,  "unit":"3 × 8 oz",  "tags":["cream cheese","philadelphia","cheese","dairy","spread"]},
    {"id":"oat_milk",    "name":"Oat Milk",                       "brand":"Oatly",             "category":"Dairy",
     "section":"dairy",  "gx":6.3, "gy":11.0,"aisle":"Dairy – Aisle 5",
     "price":11.99, "unit":"6-pack",     "tags":["oat milk","oatly","dairy free","milk alternative"]},

    # ── FROZEN FOODS ─────────────────────────────────────────────────────────
    {"id":"frozen_broccoli","name":"Frozen Organic Broccoli",     "brand":"Kirkland Signature","category":"Frozen",
     "section":"frozen","gx":0.5, "gy":10.3,"aisle":"Frozen – Door 1",
     "price":7.99,  "unit":"4 lb bag",   "tags":["frozen broccoli","broccoli","frozen vegetable","organic"]},
    {"id":"frozen_lasagna","name":"Meat Lasagna",                 "brand":"Kirkland Signature","category":"Frozen",
     "section":"frozen","gx":1.1, "gy":10.3,"aisle":"Frozen – Door 2",
     "price":13.99, "unit":"6 lb",       "tags":["lasagna","frozen meal","pasta","italian","dinner"]},
    {"id":"dumplings",   "name":"Steamed Dumplings",              "brand":"Bibigo",            "category":"Frozen",
     "section":"frozen","gx":1.7, "gy":10.3,"aisle":"Frozen – Door 3",
     "price":12.99, "unit":"72-count",   "tags":["dumplings","bibigo","korean","dim sum","frozen","potstickers"]},
    {"id":"ice_cream",   "name":"Vanilla Ice Cream",              "brand":"Kirkland Signature","category":"Frozen",
     "section":"frozen","gx":2.3, "gy":10.3,"aisle":"Frozen – Door 4",
     "price":9.99,  "unit":"1 gallon",   "tags":["ice cream","vanilla","dessert","frozen"]},
    {"id":"edamame",     "name":"Frozen Edamame (Shelled)",       "brand":"Seapoint Farms",    "category":"Frozen",
     "section":"frozen","gx":0.5, "gy":11.0,"aisle":"Frozen – Door 5",
     "price":8.99,  "unit":"4 lb bag",   "tags":["edamame","soybeans","frozen","asian","appetizer"]},
    {"id":"cauliflower_rice","name":"Frozen Riced Cauliflower",   "brand":"Kirkland Signature","category":"Frozen",
     "section":"frozen","gx":1.1, "gy":11.0,"aisle":"Frozen – Door 6",
     "price":9.99,  "unit":"4 lb bag",   "tags":["cauliflower rice","rice","keto","low carb","frozen"]},
    {"id":"frozen_waffles","name":"Buttermilk Waffles",           "brand":"Kirkland Signature","category":"Frozen",
     "section":"frozen","gx":1.7, "gy":11.0,"aisle":"Frozen – Door 7",
     "price":7.99,  "unit":"60-count",   "tags":["waffles","frozen breakfast","buttermilk","morning"]},
    {"id":"pizza_rolls", "name":"Pizza Rolls",                    "brand":"Totino's",          "category":"Frozen",
     "section":"frozen","gx":2.3, "gy":11.0,"aisle":"Frozen – Door 8",
     "price":10.99, "unit":"200-count",  "tags":["pizza rolls","totinos","frozen snack","appetizer"]},
    {"id":"frozen_berries","name":"Organic Frozen Berry Blend",   "brand":"Kirkland Signature","category":"Frozen",
     "section":"frozen","gx":0.5, "gy":11.7,"aisle":"Frozen – Door 9",
     "price":10.99, "unit":"4 lb bag",   "tags":["frozen berries","berry blend","smoothie","organic","fruit"]},
    {"id":"chicken_nuggets","name":"Breaded Chicken Breast Chunks","brand":"Kirkland Signature","category":"Frozen",
     "section":"frozen","gx":1.1, "gy":11.7,"aisle":"Frozen – Door 10",
     "price":16.99, "unit":"5 lb bag",   "tags":["chicken nuggets","chicken","frozen","kids","breaded"]},

    # ── SNACKS & CANDY ───────────────────────────────────────────────────────
    {"id":"trail_mix",   "name":"Trail Mix",                      "brand":"Kirkland Signature","category":"Snacks",
     "section":"snacks", "gx":4.3, "gy":6.4,"aisle":"Snacks – Aisle 1",
     "price":13.99, "unit":"3 lb",       "tags":["trail mix","nuts","dried fruit","snack","hiking"]},
    {"id":"cashews",     "name":"Whole Cashews Roasted & Salted", "brand":"Kirkland Signature","category":"Snacks",
     "section":"snacks", "gx":4.9, "gy":6.4,"aisle":"Snacks – Aisle 1",
     "price":14.99, "unit":"2.5 lb can", "tags":["cashews","nuts","roasted","salted","snack"]},
    {"id":"almonds",     "name":"Dry Roasted Almonds No Salt",    "brand":"Kirkland Signature","category":"Snacks",
     "section":"snacks", "gx":5.5, "gy":6.4,"aisle":"Snacks – Aisle 2",
     "price":11.99, "unit":"3 lb",       "tags":["almonds","nuts","dry roasted","unsalted","snack"]},
    {"id":"kind_bars",   "name":"Kind Bars Variety Pack",         "brand":"Kind",              "category":"Snacks",
     "section":"snacks", "gx":6.1, "gy":6.4,"aisle":"Snacks – Aisle 2",
     "price":19.99, "unit":"30-count",   "tags":["kind bars","granola bars","snack bars","healthy snack","nuts"]},
    {"id":"goldfish",    "name":"Goldfish Crackers Variety",      "brand":"Pepperidge Farm",   "category":"Snacks",
     "section":"snacks", "gx":6.7, "gy":6.4,"aisle":"Snacks – Aisle 3",
     "price":11.99, "unit":"66 oz",      "tags":["goldfish","crackers","kids","snack","cheddar"]},
    {"id":"pita_chips",  "name":"Pita Chips",                     "brand":"Stacy's",           "category":"Snacks",
     "section":"snacks", "gx":7.3, "gy":6.4,"aisle":"Snacks – Aisle 3",
     "price":10.99, "unit":"25 oz",      "tags":["pita chips","chips","stacys","snack","hummus"]},
    {"id":"popcorn",     "name":"Organic Popcorn",                "brand":"Kirkland Signature","category":"Snacks",
     "section":"snacks", "gx":4.3, "gy":7.0,"aisle":"Snacks – Aisle 4",
     "price":8.99,  "unit":"20 bags",    "tags":["popcorn","organic","snack","microwave","movie"]},
    {"id":"protein_bars","name":"Protein Bars Variety",           "brand":"Quest",             "category":"Snacks",
     "section":"snacks", "gx":4.9, "gy":7.0,"aisle":"Snacks – Aisle 4",
     "price":24.99, "unit":"30-count",   "tags":["protein bars","quest","snack bar","protein","fitness"]},
    {"id":"mixed_nuts",  "name":"Deluxe Mixed Nuts",              "brand":"Kirkland Signature","category":"Snacks",
     "section":"snacks", "gx":5.5, "gy":7.0,"aisle":"Snacks – Aisle 5",
     "price":16.99, "unit":"2.5 lb",     "tags":["mixed nuts","nuts","deluxe","cashews","almonds","pecans"]},
    {"id":"dark_chocolate","name":"Belgian Dark Chocolate",       "brand":"Kirkland Signature","category":"Snacks",
     "section":"snacks", "gx":6.1, "gy":7.0,"aisle":"Snacks – Aisle 5",
     "price":12.99, "unit":"2 lb",       "tags":["dark chocolate","chocolate","belgian","dessert","candy"]},

    # ── BEVERAGES ────────────────────────────────────────────────────────────
    {"id":"water",       "name":"Purified Drinking Water",        "brand":"Kirkland Signature","category":"Beverages",
     "section":"beverages","gx":8.3,"gy":6.4,"aisle":"Beverages – Aisle 1",
     "price":4.99,  "unit":"40 × 16.9 oz","tags":["water","bottled water","drinking water","hydration"]},
    {"id":"sparkling_water","name":"Sparkling Water Variety",     "brand":"La Croix",          "category":"Beverages",
     "section":"beverages","gx":8.9,"gy":6.4,"aisle":"Beverages – Aisle 1",
     "price":12.99, "unit":"24-pack",    "tags":["sparkling water","la croix","carbonated","seltzer","fizzy"]},
    {"id":"coffee_beans","name":"Colombian Supremo Coffee Beans", "brand":"Kirkland Signature","category":"Beverages",
     "section":"beverages","gx":9.5,"gy":6.4,"aisle":"Beverages – Aisle 2",
     "price":26.99, "unit":"3 lb bag",   "tags":["coffee","coffee beans","colombian","dark roast","caffeine"]},
    {"id":"oj",          "name":"100% Pure Orange Juice",         "brand":"Kirkland Signature","category":"Beverages",
     "section":"beverages","gx":10.1,"gy":6.4,"aisle":"Beverages – Aisle 2",
     "price":9.99,  "unit":"2 × 59 oz",  "tags":["orange juice","oj","juice","fruit juice","vitamin c"]},
    {"id":"gatorade",    "name":"Gatorade Thirst Quencher",       "brand":"Gatorade",          "category":"Beverages",
     "section":"beverages","gx":10.7,"gy":6.4,"aisle":"Beverages – Aisle 3",
     "price":19.99, "unit":"28 × 20 oz","tags":["gatorade","sports drink","electrolytes","hydration","exercise"]},
    {"id":"green_tea",   "name":"Green Tea Bags",                 "brand":"Kirkland Signature","category":"Beverages",
     "section":"beverages","gx":11.3,"gy":6.4,"aisle":"Beverages – Aisle 3",
     "price":9.99,  "unit":"100-count",  "tags":["green tea","tea","bags","antioxidants","caffeine"]},
    {"id":"energy_drinks","name":"Energy Drinks Variety",         "brand":"Monster",           "category":"Beverages",
     "section":"beverages","gx":8.3,"gy":7.0,"aisle":"Beverages – Aisle 4",
     "price":26.99, "unit":"24-pack",    "tags":["energy drink","monster","caffeine","energy","boost"]},
    {"id":"kombucha",    "name":"Kombucha Variety",               "brand":"GT's",              "category":"Beverages",
     "section":"beverages","gx":8.9,"gy":7.0,"aisle":"Beverages – Aisle 4",
     "price":22.99, "unit":"9 × 16 oz", "tags":["kombucha","fermented","probiotic","gut health","drink"]},

    # ── PAPER & CLEANING ────────────────────────────────────────────────────
    {"id":"paper_towels","name":"Paper Towels Select-A-Size",     "brand":"Kirkland Signature","category":"Paper",
     "section":"paper_cleaning","gx":0.5,"gy":6.4,"aisle":"Paper – Aisle 1",
     "price":19.99, "unit":"12 XL rolls","tags":["paper towels","towels","cleaning","kitchen"]},
    {"id":"toilet_paper","name":"Bath Tissue Ultra Soft",         "brand":"Kirkland Signature","category":"Paper",
     "section":"paper_cleaning","gx":1.1,"gy":6.4,"aisle":"Paper – Aisle 1",
     "price":21.99, "unit":"30 double rolls","tags":["toilet paper","bath tissue","bathroom","soft"]},
    {"id":"laundry_detergent","name":"Ultra Clean HE Detergent",  "brand":"Kirkland Signature","category":"Cleaning",
     "section":"paper_cleaning","gx":1.7,"gy":6.4,"aisle":"Paper – Aisle 2",
     "price":16.99, "unit":"194 fl oz",  "tags":["laundry detergent","laundry","washing","he","cleaning"]},
    {"id":"tide_pods",   "name":"Tide PODS Laundry Detergent",    "brand":"Tide",              "category":"Cleaning",
     "section":"paper_cleaning","gx":2.3,"gy":6.4,"aisle":"Paper – Aisle 2",
     "price":32.99, "unit":"152-count",  "tags":["tide pods","laundry","detergent","pods","washing","tide"]},
    {"id":"trash_bags",  "name":"Flex-Tuf Trash Bags 33 Gal",     "brand":"Kirkland Signature","category":"Cleaning",
     "section":"paper_cleaning","gx":2.9,"gy":6.4,"aisle":"Paper – Aisle 3",
     "price":15.99, "unit":"100-count",  "tags":["trash bags","garbage bags","33 gallon","kitchen","cleaning"]},
    {"id":"dishwasher_pods","name":"Platinum Dishwasher Pods",    "brand":"Cascade",           "category":"Cleaning",
     "section":"paper_cleaning","gx":3.5,"gy":6.4,"aisle":"Paper – Aisle 3",
     "price":22.99, "unit":"90-count",   "tags":["dishwasher pods","cascade","dishwasher","cleaning","pods"]},
    {"id":"ziploc_bags", "name":"Storage Bags Variety Pack",      "brand":"Ziploc",            "category":"Paper",
     "section":"paper_cleaning","gx":0.5,"gy":7.0,"aisle":"Paper – Aisle 4",
     "price":14.99, "unit":"3 sizes pk", "tags":["ziploc","storage bags","sandwich bags","freezer bags","plastic"]},
    {"id":"aluminum_foil","name":"Heavy Duty Aluminum Foil",      "brand":"Kirkland Signature","category":"Paper",
     "section":"paper_cleaning","gx":1.1,"gy":7.0,"aisle":"Paper – Aisle 4",
     "price":16.99, "unit":"2 × 150 ft","tags":["aluminum foil","foil","cooking","baking","wrap"]},
    {"id":"plastic_wrap","name":"Stretch-Tite Plastic Wrap",      "brand":"Kirkland Signature","category":"Paper",
     "section":"paper_cleaning","gx":1.7,"gy":7.0,"aisle":"Paper – Aisle 5",
     "price":12.99, "unit":"2 × 750 ft","tags":["plastic wrap","cling wrap","food wrap","saran wrap","storage"]},
    {"id":"hand_soap",   "name":"Foaming Hand Soap Refills",      "brand":"Method",            "category":"Cleaning",
     "section":"paper_cleaning","gx":2.3,"gy":7.0,"aisle":"Paper – Aisle 5",
     "price":12.99, "unit":"4 × 28 oz", "tags":["hand soap","soap","method","foaming","bathroom","kitchen"]},

    # ── BREAKFAST & CEREAL ──────────────────────────────────────────────────
    {"id":"rolled_oats",  "name":"Organic Rolled Oats",           "brand":"Kirkland Signature","category":"Breakfast",
     "section":"breakfast","gx":0.5,"gy":8.4,"aisle":"Breakfast – Aisle 1",
     "price":8.99,  "unit":"10 lb bag",  "tags":["oats","rolled oats","oatmeal","organic","breakfast","porridge"]},
    {"id":"granola",      "name":"Granola with Ancient Grains",   "brand":"Kirkland Signature","category":"Breakfast",
     "section":"breakfast","gx":1.1,"gy":8.4,"aisle":"Breakfast – Aisle 1",
     "price":10.99, "unit":"4 lb",       "tags":["granola","breakfast","cereal","ancient grains","healthy"]},
    {"id":"pancake_mix",  "name":"Flapjack & Waffle Mix",         "brand":"Kodiak Cakes",      "category":"Breakfast",
     "section":"breakfast","gx":1.7,"gy":8.4,"aisle":"Breakfast – Aisle 2",
     "price":13.99, "unit":"5 lb",       "tags":["pancake mix","waffles","kodiak","breakfast","protein","baking"]},
    {"id":"maple_syrup",  "name":"Pure Maple Syrup",              "brand":"Kirkland Signature","category":"Breakfast",
     "section":"breakfast","gx":2.3,"gy":8.4,"aisle":"Breakfast – Aisle 2",
     "price":14.99, "unit":"2 × 33 oz", "tags":["maple syrup","syrup","pancakes","waffles","breakfast","pure"]},
    {"id":"cereal_variety","name":"Cereal Variety Pack",          "brand":"Kellogg's",         "category":"Breakfast",
     "section":"breakfast","gx":2.9,"gy":8.4,"aisle":"Breakfast – Aisle 3",
     "price":11.99, "unit":"30-pack",    "tags":["cereal","variety","kelloggs","breakfast","kids","corn flakes"]},
    {"id":"granola_bars", "name":"Chewy Granola Bars",            "brand":"Nature Valley",     "category":"Breakfast",
     "section":"breakfast","gx":3.5,"gy":8.4,"aisle":"Breakfast – Aisle 3",
     "price":9.99,  "unit":"48-count",   "tags":["granola bars","nature valley","snack","oats","breakfast bar"]},
    {"id":"instant_oatmeal","name":"Instant Oatmeal Variety",     "brand":"Quaker",            "category":"Breakfast",
     "section":"breakfast","gx":0.5,"gy":9.0,"aisle":"Breakfast – Aisle 4",
     "price":9.99,  "unit":"52-count",   "tags":["instant oatmeal","oatmeal","quaker","quick oats","breakfast"]},
    {"id":"peanut_butter","name":"Peanut Butter Creamy",          "brand":"Kirkland Signature","category":"Breakfast",
     "section":"breakfast","gx":1.1,"gy":9.0,"aisle":"Breakfast – Aisle 4",
     "price":10.99, "unit":"2 × 28 oz", "tags":["peanut butter","pb","spread","creamy","breakfast","nut butter"]},

    # ── CANNED GOODS ────────────────────────────────────────────────────────
    {"id":"olive_oil",    "name":"Extra Virgin Olive Oil",        "brand":"Kirkland Signature","category":"Pantry",
     "section":"canned_goods","gx":4.3,"gy":8.4,"aisle":"Canned – Aisle 1",
     "price":14.99, "unit":"2 L",        "tags":["olive oil","evoo","extra virgin","cooking oil","kirkland"]},
    {"id":"diced_tomatoes","name":"Organic Diced Tomatoes",       "brand":"Kirkland Signature","category":"Canned",
     "section":"canned_goods","gx":4.9,"gy":8.4,"aisle":"Canned – Aisle 1",
     "price":8.99,  "unit":"8 × 14.5 oz","tags":["diced tomatoes","canned tomatoes","organic","tomatoes","cooking"]},
    {"id":"chicken_broth","name":"Organic Chicken Broth",         "brand":"Kirkland Signature","category":"Canned",
     "section":"canned_goods","gx":5.5,"gy":8.4,"aisle":"Canned – Aisle 2",
     "price":8.99,  "unit":"6 × 32 oz", "tags":["chicken broth","stock","organic","soup","cooking"]},
    {"id":"tuna",         "name":"Albacore Tuna in Water",        "brand":"Kirkland Signature","category":"Canned",
     "section":"canned_goods","gx":6.1,"gy":8.4,"aisle":"Canned – Aisle 2",
     "price":14.99, "unit":"8 × 7 oz",  "tags":["tuna","albacore","canned fish","protein","sandwich"]},
    {"id":"baked_beans",  "name":"Baked Beans Original",          "brand":"Bush's",            "category":"Canned",
     "section":"canned_goods","gx":6.7,"gy":8.4,"aisle":"Canned – Aisle 3",
     "price":7.99,  "unit":"8 × 16 oz", "tags":["baked beans","bushs","beans","side dish","bbq"]},
    {"id":"coconut_oil",  "name":"Organic Virgin Coconut Oil",    "brand":"Kirkland Signature","category":"Pantry",
     "section":"canned_goods","gx":7.3,"gy":8.4,"aisle":"Canned – Aisle 3",
     "price":12.99, "unit":"54 oz",      "tags":["coconut oil","organic","cooking oil","baking","keto"]},
    {"id":"honey",        "name":"Raw Wildflower Honey",          "brand":"Kirkland Signature","category":"Pantry",
     "section":"canned_goods","gx":4.3,"gy":9.0,"aisle":"Canned – Aisle 4",
     "price":12.99, "unit":"5 lb",       "tags":["honey","raw honey","wildflower","sweetener","natural"]},
    {"id":"pasta",        "name":"Penne Rigate Pasta",            "brand":"Kirkland Signature","category":"Pantry",
     "section":"canned_goods","gx":4.9,"gy":9.0,"aisle":"Canned – Aisle 4",
     "price":8.99,  "unit":"6 × 1 lb",  "tags":["pasta","penne","noodles","italian","dinner"]},
    {"id":"marinara",     "name":"Italian Tomato Pasta Sauce",    "brand":"Kirkland Signature","category":"Pantry",
     "section":"canned_goods","gx":5.5,"gy":9.0,"aisle":"Canned – Aisle 5",
     "price":9.99,  "unit":"2 × 48 oz", "tags":["marinara","pasta sauce","tomato sauce","italian","spaghetti"]},
    {"id":"salsa",        "name":"Organic Salsa",                 "brand":"Kirkland Signature","category":"Pantry",
     "section":"canned_goods","gx":6.1,"gy":9.0,"aisle":"Canned – Aisle 5",
     "price":6.99,  "unit":"38 oz",      "tags":["salsa","organic","chips","dip","tomato","mexican"]},

    # ── INTERNATIONAL FOODS ─────────────────────────────────────────────────
    {"id":"soy_sauce",    "name":"Organic Tamari Soy Sauce",      "brand":"San-J",             "category":"International",
     "section":"international","gx":8.3,"gy":8.4,"aisle":"International – Aisle 1",
     "price":8.99,  "unit":"20 oz",      "tags":["soy sauce","tamari","san-j","japanese","asian","cooking"]},
    {"id":"sriracha",     "name":"Sriracha Hot Chili Sauce",      "brand":"Huy Fong",          "category":"International",
     "section":"international","gx":8.9,"gy":8.4,"aisle":"International – Aisle 1",
     "price":6.99,  "unit":"28 oz × 2", "tags":["sriracha","hot sauce","spicy","asian","chili","huy fong"]},
    {"id":"sesame_oil",   "name":"Toasted Sesame Oil",            "brand":"Kadoya",            "category":"International",
     "section":"international","gx":9.5,"gy":8.4,"aisle":"International – Aisle 2",
     "price":9.99,  "unit":"56 oz",      "tags":["sesame oil","toasted","asian","cooking","japanese","chinese"]},
    {"id":"rice",         "name":"Jasmine Rice",                  "brand":"Kirkland Signature","category":"International",
     "section":"international","gx":10.1,"gy":8.4,"aisle":"International – Aisle 2",
     "price":14.99, "unit":"25 lb bag",  "tags":["rice","jasmine rice","white rice","asian","grains","staple"]},
    {"id":"tortillas",    "name":"Flour Tortillas",               "brand":"Mission",           "category":"International",
     "section":"international","gx":10.7,"gy":8.4,"aisle":"International – Aisle 3",
     "price":5.99,  "unit":"80-count",   "tags":["tortillas","flour tortillas","mission","mexican","wraps","burritos"]},
    {"id":"hot_sauce",    "name":"Hot Sauce",                     "brand":"Frank's RedHot",    "category":"International",
     "section":"international","gx":11.3,"gy":8.4,"aisle":"International – Aisle 3",
     "price":7.99,  "unit":"2 × 23 oz", "tags":["hot sauce","franks","buffalo","spicy","wing sauce"]},

    # ── HEALTH & BEAUTY ─────────────────────────────────────────────────────
    {"id":"sunscreen",    "name":"Sport SPF 50 Sunscreen",        "brand":"Kirkland Signature","category":"Health",
     "section":"health_beauty","gx":6.3,"gy":3.4,"aisle":"Health – Aisle 1",
     "price":16.99, "unit":"3-pack 12oz","tags":["sunscreen","spf 50","sport","sun protection","skin care"]},
    {"id":"shampoo",      "name":"Moisture Shampoo",              "brand":"Kirkland Signature","category":"Beauty",
     "section":"health_beauty","gx":6.9,"gy":3.4,"aisle":"Health – Aisle 1",
     "price":9.99,  "unit":"2 × 25 oz", "tags":["shampoo","hair","moisture","kirkland","personal care"]},
    {"id":"body_wash",    "name":"Dove Body Wash",                "brand":"Dove",              "category":"Beauty",
     "section":"health_beauty","gx":7.5,"gy":3.4,"aisle":"Health – Aisle 2",
     "price":14.99, "unit":"3 × 24 oz", "tags":["body wash","dove","shower gel","skin care","moisturizing"]},
    {"id":"toothbrush",   "name":"Electric Toothbrush Refill Heads","brand":"Oral-B",          "category":"Health",
     "section":"health_beauty","gx":8.1,"gy":3.4,"aisle":"Health – Aisle 2",
     "price":29.99, "unit":"8-count",    "tags":["toothbrush","electric toothbrush","oral-b","dental","refill heads"]},
    {"id":"face_wash",    "name":"Daily Facial Cleanser",         "brand":"Cetaphil",          "category":"Beauty",
     "section":"health_beauty","gx":6.3,"gy":4.0,"aisle":"Health – Aisle 3",
     "price":14.99, "unit":"2 × 16 oz", "tags":["face wash","cetaphil","cleanser","skin care","facial","gentle"]},
    {"id":"moisturizer",  "name":"Daily Moisturizing Lotion",     "brand":"CeraVe",            "category":"Beauty",
     "section":"health_beauty","gx":6.9,"gy":4.0,"aisle":"Health – Aisle 3",
     "price":16.99, "unit":"2 × 19 oz", "tags":["moisturizer","cerave","lotion","skin care","daily","hydration"]},
    {"id":"razors",       "name":"Fusion5 Razor Blade Refills",   "brand":"Gillette",          "category":"Health",
     "section":"health_beauty","gx":7.5,"gy":4.0,"aisle":"Health – Aisle 4",
     "price":32.99, "unit":"16-count",   "tags":["razors","gillette","shaving","fusion5","blades","refills"]},
    {"id":"deodorant",    "name":"Clinical Strength Deodorant",   "brand":"Dove",              "category":"Health",
     "section":"health_beauty","gx":8.1,"gy":4.0,"aisle":"Health – Aisle 4",
     "price":14.99, "unit":"3-pack",     "tags":["deodorant","dove","antiperspirant","clinical","personal care"]},

    # ── VITAMINS ────────────────────────────────────────────────────────────
    {"id":"fish_oil",     "name":"Omega-3 Fish Oil",              "brand":"Kirkland Signature","category":"Vitamins",
     "section":"vitamins","gx":9.3,"gy":3.4,"aisle":"Vitamins – Aisle 1",
     "price":18.99, "unit":"400 softgels","tags":["fish oil","omega-3","supplement","heart health","vitamins"]},
    {"id":"vitamin_d",    "name":"Vitamin D3 2000 IU",            "brand":"Kirkland Signature","category":"Vitamins",
     "section":"vitamins","gx":9.9,"gy":3.4,"aisle":"Vitamins – Aisle 1",
     "price":8.99,  "unit":"600 softgels","tags":["vitamin d","d3","supplement","bone health","immunity"]},
    {"id":"vitamin_c",    "name":"Chewable Vitamin C 500 mg",     "brand":"Nature Made",       "category":"Vitamins",
     "section":"vitamins","gx":10.5,"gy":3.4,"aisle":"Vitamins – Aisle 2",
     "price":9.99,  "unit":"300-count",  "tags":["vitamin c","ascorbic acid","immunity","antioxidant","chewable"]},
    {"id":"melatonin",    "name":"Melatonin 10 mg",               "brand":"Kirkland Signature","category":"Vitamins",
     "section":"vitamins","gx":11.1,"gy":3.4,"aisle":"Vitamins – Aisle 2",
     "price":7.99,  "unit":"365 tablets","tags":["melatonin","sleep aid","supplement","sleep","10mg"]},
    {"id":"multivitamin", "name":"Complete Multivitamin Adults",  "brand":"Kirkland Signature","category":"Vitamins",
     "section":"vitamins","gx":9.3,"gy":4.0,"aisle":"Vitamins – Aisle 3",
     "price":14.99, "unit":"500 tablets","tags":["multivitamin","multi","vitamin","supplement","daily","adults"]},
    {"id":"magnesium",    "name":"Magnesium Glycinate 400 mg",    "brand":"Kirkland Signature","category":"Vitamins",
     "section":"vitamins","gx":9.9,"gy":4.0,"aisle":"Vitamins – Aisle 3",
     "price":17.99, "unit":"320 capsules","tags":["magnesium","supplement","sleep","muscle","anxiety","glycinate"]},
    {"id":"coq10",        "name":"CoQ10 300 mg",                  "brand":"Kirkland Signature","category":"Vitamins",
     "section":"vitamins","gx":10.5,"gy":4.0,"aisle":"Vitamins – Aisle 4",
     "price":24.99, "unit":"100 softgels","tags":["coq10","coenzyme","heart health","energy","antioxidant"]},

    # ── ELECTRONICS ─────────────────────────────────────────────────────────
    {"id":"samsung_tv",   "name":"65\" Class QLED 4K TV",         "brand":"Samsung",           "category":"Electronics",
     "section":"electronics","gx":6.5,"gy":0.5,"aisle":"Electronics – Display A",
     "price":699.99,"unit":"65-inch",    "tags":["tv","television","samsung","4k","qled","65 inch","smart tv"]},
    {"id":"airpods",      "name":"AirPods Pro 2nd Generation",    "brand":"Apple",             "category":"Electronics",
     "section":"electronics","gx":7.1,"gy":0.5,"aisle":"Electronics – Display A",
     "price":199.99,"unit":"1 pair",     "tags":["airpods","apple","earbuds","wireless","noise cancelling","earphones"]},
    {"id":"hp_laptop",    "name":"15.6\" Laptop Intel i7",        "brand":"HP",                "category":"Electronics",
     "section":"electronics","gx":7.7,"gy":0.5,"aisle":"Electronics – Display B",
     "price":649.99,"unit":"laptop",     "tags":["laptop","hp","computer","intel","i7","15 inch","windows"]},
    {"id":"ipad",         "name":"iPad 10th Generation",          "brand":"Apple",             "category":"Electronics",
     "section":"electronics","gx":8.3,"gy":0.5,"aisle":"Electronics – Display B",
     "price":449.99,"unit":"tablet",     "tags":["ipad","apple","tablet","10th gen","screen","ios"]},
    {"id":"ring_doorbell","name":"Video Doorbell Pro",            "brand":"Ring",              "category":"Electronics",
     "section":"electronics","gx":6.5,"gy":1.5,"aisle":"Electronics – Display C",
     "price":169.99,"unit":"doorbell",   "tags":["ring","doorbell","smart home","security","camera","video"]},
    {"id":"wifi_router",  "name":"Whole Home WiFi System",        "brand":"TP-Link Deco",      "category":"Electronics",
     "section":"electronics","gx":7.1,"gy":1.5,"aisle":"Electronics – Display C",
     "price":149.99,"unit":"3-pack",     "tags":["wifi","router","mesh","tp-link","deco","internet","network"]},
    {"id":"speaker",      "name":"Portable Bluetooth Speaker",    "brand":"Bose",              "category":"Electronics",
     "section":"electronics","gx":7.7,"gy":1.5,"aisle":"Electronics – Display D",
     "price":149.99,"unit":"speaker",    "tags":["speaker","bose","bluetooth","portable","wireless","audio"]},
    {"id":"smart_watch",  "name":"Garmin GPS Sport Watch",        "brand":"Garmin",            "category":"Electronics",
     "section":"electronics","gx":8.3,"gy":1.5,"aisle":"Electronics – Display D",
     "price":249.99,"unit":"watch",      "tags":["watch","garmin","gps","fitness tracker","sport","smartwatch"]},

    # ── CLOTHING & LUGGAGE ──────────────────────────────────────────────────
    {"id":"fleece_jacket","name":"Men's Full-Zip Fleece Jacket",  "brand":"Columbia",          "category":"Clothing",
     "section":"clothing","gx":9.3,"gy":0.5,"aisle":"Clothing – Aisle 1",
     "price":29.99, "unit":"jacket",     "tags":["jacket","fleece","columbia","mens","zip","outdoor","warm"]},
    {"id":"jeans",        "name":"5-Pocket Stretch Jeans",        "brand":"Kirkland Signature","category":"Clothing",
     "section":"clothing","gx":9.9,"gy":0.5,"aisle":"Clothing – Aisle 1",
     "price":14.99, "unit":"pair",       "tags":["jeans","denim","pants","kirkland","stretch","5-pocket"]},
    {"id":"socks",        "name":"Cushion Comfort Crew Socks",    "brand":"Kirkland Signature","category":"Clothing",
     "section":"clothing","gx":10.5,"gy":0.5,"aisle":"Clothing – Aisle 2",
     "price":11.99, "unit":"12-pack",    "tags":["socks","crew socks","cushion","comfort","kirkland"]},
    {"id":"luggage",      "name":"20/27\" 2-Piece Luggage Set",   "brand":"Kirkland Signature","category":"Luggage",
     "section":"clothing","gx":11.1,"gy":0.5,"aisle":"Clothing – Aisle 2",
     "price":79.99, "unit":"2-piece set","tags":["luggage","suitcase","travel","carry-on","checked bag","rolling"]},

    # ── HOME & GARDEN ────────────────────────────────────────────────────────
    {"id":"rubbermaid",   "name":"Food Storage Container Set",    "brand":"Rubbermaid",        "category":"Home",
     "section":"home",   "gx":0.5,"gy":2.4,"aisle":"Home – Aisle 1",
     "price":24.99, "unit":"42-piece",   "tags":["rubbermaid","storage containers","food storage","tupperware","set"]},
    {"id":"instant_pot",  "name":"7-in-1 Electric Pressure Cooker","brand":"Instant Pot",     "category":"Home",
     "section":"home",   "gx":1.1,"gy":2.4,"aisle":"Home – Aisle 1",
     "price":79.99, "unit":"8-quart",    "tags":["instant pot","pressure cooker","slow cooker","electric","kitchen"]},
    {"id":"roomba",       "name":"Wi-Fi Connected Robot Vacuum",  "brand":"iRobot",            "category":"Home",
     "section":"home",   "gx":1.7,"gy":2.4,"aisle":"Home – Aisle 2",
     "price":249.99,"unit":"vacuum",     "tags":["roomba","irobot","robot vacuum","smart home","vacuum","cleaning"]},

    # ── OFFICE ───────────────────────────────────────────────────────────────
    {"id":"copy_paper",   "name":"Multipurpose Copy Paper 8.5×11","brand":"Kirkland Signature","category":"Office",
     "section":"office", "gx":3.3,"gy":4.4,"aisle":"Office – Aisle 1",
     "price":24.99, "unit":"10 ream / 5000 sheets","tags":["copy paper","printer paper","office paper","white","8.5x11"]},
    {"id":"pens",         "name":"Ballpoint Pen Assortment",      "brand":"BIC",               "category":"Office",
     "section":"office", "gx":3.9,"gy":4.4,"aisle":"Office – Aisle 1",
     "price":9.99,  "unit":"60-pack",    "tags":["pens","ballpoint","bic","office","writing","school"]},
    {"id":"batteries",    "name":"AA Alkaline Batteries",         "brand":"Kirkland Signature","category":"Office",
     "section":"office", "gx":4.5,"gy":4.4,"aisle":"Office – Aisle 2",
     "price":16.99, "unit":"48-count",   "tags":["batteries","aa","alkaline","kirkland","remote","power"]},
    {"id":"usb_hub",      "name":"7-Port USB 3.0 Hub",            "brand":"Sabrent",           "category":"Office",
     "section":"office", "gx":5.1,"gy":4.4,"aisle":"Office – Aisle 2",
     "price":19.99, "unit":"hub",        "tags":["usb hub","usb","sabrent","port","computer","peripheral"]},
]

# ── Helper functions ──────────────────────────────────────────────────────────

_STOP_WORDS = frozenset({
    "where","is","the","a","an","i","me","my","we","our","you","your",
    "it","its","be","am","are","was","were","can","do","does","did",
    "will","would","could","should","have","has","had","get","to","in",
    "on","at","by","for","of","and","or","but","so","yet","nor","if",
    "find","need","want","looking","show","tell","help","please","some",
    "any","much","more","how","what","which","when","who","there","here",
})


def search_products(query: str, max_results: int = 8) -> list[dict]:
    """
    Robust keyword product search with stop-word filtering.
    Returns ranked results (best match first).
    """
    import re
    query_lower = query.lower()
    # Strip punctuation, extract alpha tokens, remove stop words
    raw_tokens = re.findall(r"[a-z]+", query_lower)
    terms = [t for t in raw_tokens if len(t) >= 3 and t not in _STOP_WORDS]
    # Fall back to all tokens ≥ 3 chars if nothing survives filtering
    if not terms:
        terms = [t for t in raw_tokens if len(t) >= 3]

    # Also keep raw query (with spaces) for multi-word tag matching
    query_clean = " ".join(terms)

    scored: list[tuple[int, dict]] = []
    for p in PRODUCTS:
        score = 0
        name  = p["name"].lower()
        brand = p["brand"].lower()
        cat   = p["category"].lower()
        tags  = p["tags"]
        haystack = name + " " + brand + " " + cat + " " + " ".join(tags)

        # Exact whole-query match on name (highest weight)
        if query_clean and query_clean in name:
            score += 80
        # Exact name match on individual meaningful terms
        for term in terms:
            # Only boost when the term appears as a whole word (avoids "is" in "rotisserie")
            if re.search(rf"\b{re.escape(term)}\b", name):
                score += 25
            elif term in name:
                score += 10
            # Whole-word in haystack
            if re.search(rf"\b{re.escape(term)}\b", haystack):
                score += 8
            # Exact tag match
            if term in tags:
                score += 15
            # Multi-word tag contains term
            if any(term in tag for tag in tags):
                score += 5

        if score > 0:
            scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:max_results]]


def get_product_by_id(product_id: str) -> dict | None:
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    return None


def plan_shopping_route(product_ids: list[str]) -> dict:
    """
    Nearest-neighbour TSP starting from entrance.
    Returns ordered list of stops with human-readable directions.
    """
    items = [get_product_by_id(pid) for pid in product_ids]
    items = [i for i in items if i]  # drop unknowns

    if not items:
        return {"order": [], "steps": [], "estimated_minutes": 0}

    visited: list[dict] = []
    remaining = list(items)
    cx, cy = ENTRANCE["gx"], ENTRANCE["gy"]

    while remaining:
        closest = min(remaining, key=lambda p: (p["gx"] - cx) ** 2 + (p["gy"] - cy) ** 2)
        visited.append(closest)
        cx, cy = closest["gx"], closest["gy"]
        remaining.remove(closest)

    steps = []
    for i, p in enumerate(visited, 1):
        sec = SECTION_MAP.get(p["section"], {})
        steps.append({
            "stop": i,
            "product_id": p["id"],
            "product_name": p["name"],
            "brand": p["brand"],
            "aisle": p["aisle"],
            "section_label": sec.get("label", p["section"]),
            "price": p["price"],
            "unit": p["unit"],
            "gx": p["gx"],
            "gy": p["gy"],
        })

    # Rough walking time: assume 3.5 m/s, each grid cell ≈ 6 m
    total_dist_cells = 0.0
    px, py = ENTRANCE["gx"], ENTRANCE["gy"]
    for s in steps:
        total_dist_cells += ((s["gx"] - px) ** 2 + (s["gy"] - py) ** 2) ** 0.5
        px, py = s["gx"], s["gy"]
    total_dist_cells += ((EXIT["gx"] - px) ** 2 + (EXIT["gy"] - py) ** 2) ** 0.5
    est_seconds = (total_dist_cells * 6) / 1.2  # 1.2 m/s walking speed
    est_minutes = max(1, round(est_seconds / 60))

    return {"order": [s["product_id"] for s in steps], "steps": steps, "estimated_minutes": est_minutes}


def get_section_info(section_name: str) -> dict | None:
    name_lower = section_name.lower()
    for sec in SECTIONS:
        if name_lower in sec["id"] or name_lower in sec["label"].lower():
            products_here = [p for p in PRODUCTS if p["section"] == sec["id"]]
            return {
                **sec,
                "product_count": len(products_here),
                "sample_products": [p["name"] for p in products_here[:5]],
            }
    return None
