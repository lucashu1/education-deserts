import rtree
import shapely
from rtree import index
from helper import get_bounding_box

def build(centroids, colleges):
    centroid_index = index.Index()
    college_index = index.Index()
    for geo_id in centroids:
        lat, lon = centroids[geo_id]
        centroid_index.insert(geo_id, (lat, lon, lat, lon))

    #store centroid index to file (see http://toblerity.org/rtree/tutorial.html)
    
    centroid_50_miles = {}

    for geo_id in centroids:
        lat, lon = centroids[geo_id]
        bb = get_bounding_box(lat, lon)
        within_50_miles = list(centroid_index.intersection(bb))
        centroid_50_miles[geo_id] = {'list': within_50_miles, 'edu_desert':1}

    for id in colleges:
        lat, lon = colleges[id]
        bb = get_bounding_box(lat, lon)
        within_50_miles = list(centroid_index.intersection(bb))
        for geo_id in within_50_miles:
            centroid_50_miles[geo_id]['edu_desert'] = 0

    #store centroid 50 mile dict to file