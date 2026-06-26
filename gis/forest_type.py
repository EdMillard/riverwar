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
forest_type_dict = {
    101: "Jack Pine",
    102: "Red Pine",
    103: "Eastern White Pine",
    104: "Eastern White Pine / Eastern Hemlock",
    105: "Eastern Hemlock",
    121: "Balsam Fir",
    122: "White Spruce",
    123: "Red Spruce",
    124: "Red Spruce / Balsam Fir",
    125: "Black Spruce",
    126: "Tamarack",
    127: "Northern White-Cedar",
    141: "Longleaf Pine",
    142: "Slash Pine",
    161: "Loblolly Pine",
    162: "Shortleaf Pine",
    163: "Virginia Pine",
    181: "Eastern Redcedar",
    182: "Rocky Mountain Juniper",
    183: "Western Juniper",
    184: "Juniper Woodland",
    185: "Pinyon Juniper Woodland",
    201: "Douglas-fir",
    202: "Port-Orford-Cedar",
    221: "Ponderosa Pine",
    222: "Incense Cedar",
    223: "Jeffrey Pine / Coulter Pine / Bigcone Douglas-fir",
    224: "Sugar Pine",
    225: "Western White Pine",
    231: "Lodgepole Pine",
    241: "Limber Pine",
    251: "Whitebark Pine",
    261: "White Fir",
    262: "California Red Fir",
    263: "Shasta Red Fir",
    264: "Noble Fir",
    265: "Engelmann Spruce",
    266: "Engelmann Spruce / Subalpine Fir",
    267: "Grand Fir",
    268: "Subalpine Fir",
    269: "Blue Spruce",
    281: "Western Larch",
    365: "Foxtail Pine / Bristlecone Pine",
    366: "Limber Pine",
    703: "Cottonwood",
    709: "Cottonwood / Willow",
    901: "Aspen",
    902: "Paper Birch",
    925: "Deciduous Oak Woodland",
    926: "Evergreen Oak Woodland",
    931: "Coast Live Oak",
    932: "Canyon Live Oak",
    933: "Interior Live Oak",
    934: "California Black Oak",
    935: "Gambel Oak",
    936: "Emory Oak",
    990: "Nonstocked (low tree cover)",
    999: "Non-forest / Grassland / Meadow / Barren / Water",
}