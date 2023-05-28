import math

def calculate_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    lat = lat2 - lat1
    lon = lon2 - lon1

    a = math.sin(lat/2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(lon/2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = earth_radius * c
    return distance