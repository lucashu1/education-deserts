import rtree
import shapely

def build(centroids):
    centroid_index = index.Index()
    
    #store index to file (see http://toblerity.org/rtree/tutorial.html)