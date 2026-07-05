"""
Copyright (c) 2025 Ed Millard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all

copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
forest_types = {
    # Pines
    101: {"name": "Jack Pine", "color": (150, 150, 150)},
    102: {"name": "Red Pine", "color": (150, 150, 150)},
    103: {"name": "Eastern White Pine", "color": (150, 150, 150)},
    104: {"name": "Eastern White Pine / Eastern Hemlock", "color": (150, 150, 150)},
    105: {"name": "Eastern Hemlock", "color": (150, 150, 150)},
    121: {"name": "Balsam Fir", "color": (0, 180, 140)},
    122: {"name": "White Spruce", "color": (0, 160, 140)},      # added color
    123: {"name": "Red Spruce", "color": (150, 150, 150)},
    124: {"name": "Red Spruce / Balsam Fir", "color": (150, 150, 150)},
    125: {"name": "Black Spruce", "color": (150, 150, 150)},
    126: {"name": "Tamarack", "color": (150, 150, 150)},
    127: {"name": "Northern White-Cedar", "color": (150, 150, 150)},

    141: {"name": "Longleaf Pine", "color": (150, 150, 150)},
    142: {"name": "Slash Pine", "color": (150, 150, 150)},
    161: {"name": "Loblolly Pine", "color": (150, 150, 150)},
    162: {"name": "Shortleaf Pine", "color": (150, 150, 150)},
    163: {"name": "Virginia Pine", "color": (150, 150, 150)},

    181: {"name": "Eastern Redcedar", "color": (150, 150, 150)},
    182: {"name": "Rocky Mountain Juniper", "color": (139, 69, 19)},   # brown
    183: {"name": "Western Juniper", "color": (150, 150, 150)},
    184: {"name": "Juniper Woodland", "color": (139, 69, 19)},
    185: {"name": "Pinyon Juniper Woodland", "color": (0, 80, 0)},

    201: {"name": "Douglas-fir", "color": (0, 180, 140)},

    221: {"name": "Ponderosa Pine", "color": (139, 69, 19)},

    222: {"name": "Incense Cedar", "color": (150, 150, 150)},
    223: {"name": "Jeffrey Pine / Coulter Pine / Bigcone Douglas-fir", "color": (150, 150, 150)},
    224: {"name": "Sugar Pine", "color": (150, 150, 150)},
    225: {"name": "Western White Pine", "color": (150, 150, 150)},

    231: {"name": "Lodgepole Pine", "color": (150, 150, 150)},

    241: {"name": "Limber Pine", "color": (150, 150, 150)},
    251: {"name": "Whitebark Pine", "color": (150, 150, 150)},

    261: {"name": "White Fir", "color": (0, 180, 140)},
    262: {"name": "California Red Fir", "color": (0, 180, 140)},
    263: {"name": "Shasta Red Fir", "color": (0, 180, 140)},
    264: {"name": "Noble Fir", "color": (0, 180, 140)},

    265: {"name": "Engelmann Spruce", "color": (0, 255, 100)},
    266: {"name": "Engelmann Spruce / Subalpine Fir", "color": (0, 160, 140)},
    267: {"name": "Grand Fir", "color": (0, 180, 140)},
    268: {"name": "Subalpine Fir", "color": (0, 160, 140)},
    269: {"name": "Blue Spruce", "color": (0, 255, 255)},

    281: {"name": "Western Larch", "color": (150, 150, 150)},

    362: {"name": "Bristlecone Pine", "color": (150, 150, 150)},   # added
    365: {"name": "Foxtail Pine / Bristlecone Pine", "color": (180, 100, 220)},
    366: {"name": "Limber Pine", "color": (100, 180, 100)},

    703: {"name": "Cottonwood", "color": (0, 200, 120)},
    709: {"name": "Cottonwood / Willow", "color": (0, 160, 100)},

    901: {"name": "Aspen", "color": (255, 215, 0)},

    925: {"name": "Deciduous Oak Woodland", "color": (200, 100, 50)},
    926: {"name": "Evergreen Oak Woodland", "color": (150, 150, 150)},
    931: {"name": "Coast Live Oak", "color": (150, 150, 150)},
    932: {"name": "Canyon Live Oak", "color": (150, 150, 150)},
    933: {"name": "Interior Live Oak", "color": (150, 150, 150)},
    934: {"name": "California Black Oak", "color": (150, 150, 150)},
    935: {"name": "Gambel Oak", "color": (150, 150, 150)},
    936: {"name": "Emory Oak", "color": (150, 150, 150)},

    971: {"name": "California Mixed Evergreen Woodland", "color": (0, 150, 0)},
    973: {"name": "California Oak Woodland", "color": (150, 150, 150)},
    974: {"name": "California Chaparral", "color": (150, 150, 150)},
    975: {"name": "California Coastal Scrub", "color": (150, 150, 150)},

    990: {"name": "Nonstocked (low tree cover)", "color": (50, 50, 50)},
    999: {"name": "Non-forest / Grassland / Meadow / Barren / Water", "color": (100, 100, 100)},
}