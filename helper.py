import math

# Credit to https://www.johndcook.com/blog/2009/04/27/converting-miles-to-degrees-longitude-or-latitude/
# for the change in latitude and longitude formulas

earth_radius = 3960.0
degrees_to_radians = math.pi/180.0
radians_to_degrees = 180.0/math.pi

def change_in_latitude(miles):
    return (miles/earth_radius)*radians_to_degrees

def change_in_longitude(latitude, miles):
    r = earth_radius*math.cos(latitude*degrees_to_radians)
    return (miles/r)*radians_to_degrees

def get_bounding_box(lat, lon):
    lat_change = change_in_latitude(50)
    long_change = change_in_longitude(lat, 50)
    return (lat-lat_change, lon-long_change, lat+lat_change, lon-long_change)