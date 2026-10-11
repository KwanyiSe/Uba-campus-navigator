#@kwanyi :)

def point_in_polygon(latitude, longitude, polygon):
    """Ray-casting point-in-polygon. Polygon is [[lat, lng], ...]."""
    try:
        x=float(longitude); y=float(latitude)
    except (TypeError, ValueError):
        return False
    if not polygon or len(polygon) < 3:
        return False
    inside=False
    j=len(polygon)-1
    for i in range(len(polygon)):
        try:
            yi=float(polygon[i][0]); xi=float(polygon[i][1])
            yj=float(polygon[j][0]); xj=float(polygon[j][1])
        except (TypeError, ValueError, IndexError):
            return False
        intersects=((yi>y)!=(yj>y)) and (x < (xj-xi)*(y-yi)/(yj-yi+1e-15)+xi)
        if intersects: inside=not inside
        j=i
    return inside


def valid_polygon(polygon):
    return isinstance(polygon,list) and len(polygon)>=3 and all(isinstance(p,list) and len(p)>=2 for p in polygon)
