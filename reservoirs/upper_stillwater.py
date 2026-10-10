"""
Copyright (c) 2026 Ed Millard

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
from reservoirs.reservoir import Reservoir
from typing import List, Optional

class UpperStillwater(Reservoir):
    def __init__(self, upstream: Optional[List[Reservoir]] = None):
        headers:List[str] = []
        super().__init__('Upper Stillwater', headers, catalog_id=2468, upstream=upstream)
        self.start_year = 0
        # Elevations
        #
        self.dead_pool_feet = 0
        self.dead_pool_af = 0

        # Normal / active storage: ~33,123 acre-feet
        # Maximum storage: ~35,253 acre-feet
        # Older USBR reference: 32,496 acre-feet
        #
        # ElevationFull / normal pool surface elevation: ~8,175.5–8,176 ft
        # (design maximum water surface elevation is 8,175.5 ft; Wikipedia lists 8,176 ft)
        # USBR RISE location elevation listed as 8,169 ft (reference elevation)
        self.full_feet = 8_169
        self.full_af = 33_123

        # Critical
        self.power_head_target_feet = 0
        self.power_head_target_af = 0

        self.power_head_min_feet = 0
        self.power_head_min_af = 0

        self.turbine_intake_feet = 0
        self.turbine_intake_af = 0
        self.critical_elevations_feet = [("Safe Power Head", self.power_head_min_feet, self.power_head_min_af, Reservoir.non_power_pool_color),
                                         ("Min Power Head", self.power_head_target_feet, self.power_head_target_af, Reservoir.low_power_pool_color)]
