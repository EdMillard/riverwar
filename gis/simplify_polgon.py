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
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, mapping
from typing import List, Dict, Any, Union

def simplify_polygons_for_openet(
        gdf: gpd.GeoDataFrame,
        tolerance: float = 0.001,
        crs_for_simplification: str = "EPSG:5070",  # Albers Equal Area (good for CONUS acres)
        output_format: str = "geojson",  # Options: "geojson", "coords_list", "geodataframe"
        preserve_topology: bool = True,
        min_area_acres: float = 0.0
) -> Union[str, List[List[float]], gpd.GeoDataFrame, Dict[str, Any]]:
    """
    Simplify one or more HUC8 (or other) polygons for OpenET API use.

    Removes unnecessary vertices while keeping the shape tight to the actual boundary
    (no extra rectangle acreage). Handles single or multiple polygons.

    Parameters:
    - gdf: GeoDataFrame with selected polygons (e.g., filtered HUC8 rows).
    - tolerance: Simplification tolerance. In degrees (WGS84) or meters (projected CRS).
                 Lower = more detail/more vertices. Start with 0.0005-0.005.
    - crs_for_simplification: Projected CRS for accurate simplification + area calc.
    - output_format: "geojson" (string), "coords_list" (flat [[lon,lat], ...] list),
                     "geodataframe", or "dict" (for easy API payload).
    - preserve_topology: Keep valid topology (recommended).
    - min_area_acres: Filter out tiny slivers after simplification (optional).

    Returns: Depending on output_format.
    """
    if gdf.empty:
        raise ValueError("Input GeoDataFrame is empty.")

    # Ensure WGS84 for final output (OpenET expects lon/lat)
    gdf = gdf.to_crs("EPSG:4326").copy()

    # Project for simplification and area calculation
    gdf_proj = gdf.to_crs(crs_for_simplification)

    # Simplify
    gdf_proj['geometry'] = gdf_proj['geometry'].simplify(
        tolerance=tolerance,
        preserve_topology=preserve_topology
    )

    # Clean any topology issues
    gdf_proj['geometry'] = gdf_proj['geometry'].buffer(0)

    # Back to WGS84
    gdf_simp = gdf_proj.to_crs("EPSG:4326")

    # Calculate areas (for your 50k acre check)
    gdf_simp['area_acres'] = gdf_proj.area / 4046.86  # sq meters to acres
    total_acres = gdf_simp['area_acres'].sum()
    print(f"Total simplified area: {total_acres:.0f} acres")
    if total_acres > 50000:
        print("WARNING: Exceeds OpenET 50k acre limit per query (Tier 1). "
              "Consider splitting or higher tier.")

    # Optional filter tiny polygons
    if min_area_acres > 0:
        gdf_simp = gdf_simp[gdf_simp['area_acres'] >= min_area_acres]

    # Vertex count info
    def count_vertices(geom):
        if geom.geom_type == 'Polygon':
            return len(geom.exterior.coords)
        elif geom.geom_type == 'MultiPolygon':
            return sum(len(p.exterior.coords) for p in geom.geoms)
        return 0

    total_verts = sum(count_vertices(geom) for geom in gdf_simp.geometry)
    print(f"Approximate total vertices after simplification: {total_verts}")

    if output_format == "geodataframe":
        return gdf_simp

    elif output_format == "geojson":
        return gdf_simp.to_json()

    elif output_format == "coords_list":
        # Flat list of [lon, lat] pairs (suitable for many OpenET geometry params)
        coords = []
        for geom in gdf_simp.geometry:
            if isinstance(geom, Polygon):
                coords.extend([[x, y] for x, y in geom.exterior.coords])
            elif isinstance(geom, MultiPolygon):
                for poly in geom.geoms:
                    coords.extend([[x, y] for x, y in poly.exterior.coords])
        return coords

    elif output_format == "dict":
        # Ready for JSON API payload (example structure)
        features = []
        for _, row in gdf_simp.iterrows():
            features.append({
                "type": "Feature",
                "geometry": mapping(row.geometry),  # requires from shapely.geometry import mapping
                "properties": row.drop('geometry').to_dict() if 'geometry' in row else {}
            })
        return {"type": "FeatureCollection", "features": features}

    else:
        raise ValueError("Invalid output_format")