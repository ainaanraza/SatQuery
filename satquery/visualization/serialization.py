def to_geojson(region_id, geometry, properties):
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": properties
    }
