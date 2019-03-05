import math

# Distances are measured in miles.
# Longitudes and latitudes are measured in degrees.
# Earth is assumed to be perfectly spherical.

earth_radius = 3960.0
degrees_to_radians = math.pi/180.0
radians_to_degrees = 180.0/math.pi

def change_in_latitude(miles):
    "Given a distance north, return the change in latitude."
    return (miles/earth_radius)*radians_to_degrees

def change_in_longitude(latitude, miles):
    "Given a latitude and a distance west, return the change in longitude."
    # Find the radius of a circle around the earth at given latitude.
    r = earth_radius*math.cos(latitude*degrees_to_radians)
    return (miles/r)*radians_to_degrees