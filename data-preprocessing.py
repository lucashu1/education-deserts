# Library Imports
import fiona 
import rtree
import shapely
from shapely.geometry import shape
import geopandas as gpd
import pandas as pd
import numpy as np
import subprocess
import os
import requests
from bs4 import BeautifulSoup

# Shapely library to help with calculation
# of the representative centroid position
from shapely.geometry import MultiPoint

# default dictionary (a dictionary with a default value if a key doesn't exist)
from collections import defaultdict

# To unzip file
import zipfile

# To have progress bar
from tqdm import tqdm
import json

# Helper function to create a new folder
def mkdir(path):
    try: 
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise
        else:
            print("(%s) already exists" % (path))
            
# Main function
if __name__ == '__main__':
    
    ################################  CONSTANTS ################################ 
    print('Initializing constants...')
    # Buffer radius
    BUFFER = 40233.6 # 25 miles in metres
    
    # Census tracts shapefiles url
    ct_shape_url = 'https://www.census.gov/geo/maps-data/data/cbf/cbf_tracts.html'

    # Census tracts data url from 2012 - 2017
    ct_file_name = 'acs_5_year_estimates_census_tracts.csv'
    ct_data_url = 'https://www.dropbox.com/s/ni28x7mw6uh00dg/' + ct_file_name + '.zip?dl=1'

    # American University Data
    au_file_name = 'IPEDS_data.xlsx'
    au_data_url = 'https://public.tableau.com/s/sites/default/files/media/Resources/' + au_file_name

    # Directory of datasets
    DATASETS_PATH = 'datasets/'

    # Directory of census tract shapefile data
    CENSUS_TRACTS_PATH = DATASETS_PATH + 'census_tracts/'

    # Make the directory for the census tracts shapefiles data
    mkdir(DATASETS_PATH)
    
    ################################ CENSUS TRACT FEATURES DATA ################################ 
    print('Downloading census tract features data...')
    # Download CENSUS TRACT SHAPEFILES data 
    if not os.path.isfile(DATASETS_PATH + ct_file_name):

        os.system('!wget --directory-prefix={} -Nq {}'.format(DATASETS_PATH, ct_data_url))

        # Unzipping the file
        zip_ref = zipfile.ZipFile(DATASETS_PATH + ct_file_name + '.zip', 'r')
        zip_ref.extractall(DATASETS_PATH + ct_file_name + '/')
        zip_ref.close()

        # Remove the old census tract .zip shapefile
        subprocess.call(['rm', '-rf', DATASETS_PATH + ct_file_name + '.zip'])
        
    # Store data in census_tracts
    census_tracts = pd.read_csv(DATASETS_PATH + ct_file_name, encoding='ISO-8859-1', low_memory=False)
    
    ################################ UNIVERSITY DATA ################################  
    print('Downloading university data...')
    # Download AMERICAN UNIVERSITIES data 
    if not os.path.isfile(DATASETS_PATH + au_file_name):

        os.system('!wget --directory-prefix={} -Nq {}'.format(DATASETS_PATH, au_data_url))
    
    # Store data in universities
    universities = pd.read_excel(DATASETS_PATH + au_file_name, index_col='ID number')

    # List of tuples to store all the university
    # locations as Shapely Points
    uni_list = []

    for idx, id_num in enumerate(universities.index):
        uni_list.append((id_num, shape({"type": "Point",
                                        "coordinates": (universities.loc[id_num, 'Longitude location of institution'],
                                                        universities.loc[id_num, 'Latitude location of institution'])})))
    
    # Setting our coordinate system for the tracts 
    # and universities to EPSG:2163 https://epsg.io/2163
    uni_gdf = gpd.GeoDataFrame(geometry=[uni_pt for uniid, uni_pt in uni_list], index=[uniid for uniid, uni_pt in uni_list])
    uni_gdf.crs = {'init': 'epsg:4269'}
    uni_gdf.to_crs({'init': 'epsg:2163'}, inplace=True);
    
    # ----------------------------
    # Initialize rtree spatial index
    # with just its centroid
    uni_index = rtree.index.Index()

    # Iterate over all american universities
    for idx, (id_num, uni) in tqdm(enumerate(uni_gdf.iterrows())):

        # add coordinates of univeristy location and store id along with it
        uni_index.insert(idx, coordinates=uni.geometry.bounds, obj=id_num)
        
    ################################ CENSUS TRACT SHAPE FILES ################################  
    print('Downloading census tract shapefiles data...')
    # Make request to get the webpage
    r = requests.get(ct_shape_url)
    soup = BeautifulSoup(r.content, "html.parser")

    # Get the download links from the dropdown <option> tag
    locations = soup.find('select',
                          {'name':'Location',
                           'id':'ct2017m'}).findChildren('option' , recursive=False)[1:]

    # Put all the states and the urls for their shape files in a dictionary
    state_urls = {location.text.strip() : location.attrs['value'] for location in locations}
    
    # Download data 
    if not os.path.isdir(CENSUS_TRACTS_PATH):

        # Make the directory for the census tracts shapefiles data
        mkdir(CENSUS_TRACTS_PATH)

        for state, state_url in state_urls.items():
            os.system('wget --directory-prefix={} -Nq {}'.format(CENSUS_TRACTS_PATH, state_url))

        # Storing the shape file names
        census_tract_shapefiles = []
        for state, state_url in state_urls.items():

            # Extracting the name of shapefile
            shapefile = state_url[state_url.rindex('/') + 1:]
            census_tract_shapefiles.append(shapefile)

            # Renaming the file
            os.rename(CENSUS_TRACTS_PATH + shapefile, CENSUS_TRACTS_PATH + state + '.zip')

            # Unzipping the file
            zip_ref = zipfile.ZipFile(CENSUS_TRACTS_PATH + state + '.zip', 'r')
            zip_ref.extractall(CENSUS_TRACTS_PATH + state + '/')
            zip_ref.close()

            # Remove the old census tract .zip shapefile
            subprocess.call(['rm', '-rf', CENSUS_TRACTS_PATH + state + '.zip'])
    
    # ----------------------------
    # Let's calculate and store each of 
    # the centroids of each
    # census tract in a list of tuples
    tract_centroids = []

    # ----------------------------
    # Let's store a list of each census 
    # tract's geometry as well
    tract_list = []

    for subdir, dirs, files in list(os.walk(CENSUS_TRACTS_PATH))[1:]:

        # Opening the shapefile
        state_shapes = fiona.open(subdir, 'r')

        # Looping through each census tract in each state and 
        # making key: geoid, value: centroid position
        # of (longitude, latitude) as well as building the 
        # RTree index for census tracts
        for idx, census_tract in enumerate(state_shapes):

            geoid = census_tract['properties']['GEOID']
            geometry = np.array(census_tract['geometry']['coordinates'])
            points = None

            # Some of the geometries are in a 2d and some in 3d array
            if len([True for lat_long in geometry[0] if len(lat_long) != 2]) > 0:

                # Create the Multipoint object to find centroid
                points = MultiPoint(geometry[0][0])

            else:

                # Create the Multipoint object to find centroid
                points = MultiPoint(geometry[0])

            # ----------------------------
            # Create Census tract Polygon
            tract = shapely.geometry.shape(census_tract['geometry'])

            # ----------------------------
            # Store the Census tract Polygon
            # in our list for the RTree index
            # later on
            tract_list.append((geoid, tract))

            # ----------------------------
            # Create Census tract Centroid
            # True centroid, not necessarily an existing point
            centroid_pt = points.centroid

            # A represenative point, not centroid,
            # that is guarnateed to be with the geometry
            tract_centroids.append((geoid, shapely.geometry.shape(points.representative_point())))
    
    # Setting our coordinate system for the tracts 
    # and universities to EPSG:2163 https://epsg.io/2163
    tract_gdf = gpd.GeoDataFrame(geometry=[tract_shape for geoid, tract_shape in tract_list], index=[geoid for geoid, tract_pt in tract_list])
    tract_gdf.crs = {'init': 'epsg:4269'}
    tract_gdf.to_crs({'init': 'epsg:2163'}, inplace=True)

    tract_centroids_gdf = gpd.GeoDataFrame(geometry=[tract_pt for geoid, tract_pt in tract_centroids], index=[geoid for geoid, tract_pt in tract_centroids])
    tract_centroids_gdf.crs = {'init': 'epsg:4269'}
    tract_centroids_gdf.to_crs({'init': 'epsg:2163'}, inplace=True)
    
    # ----------------------------
    # Initialize rtree spatial index
    # for census tract centroids with
    # CENTROID point bounding box
    tract_centroid_index = rtree.index.Index()

    # Iterate over all census tract centroids
    for idx, (geoid, centroid) in tqdm(enumerate(tract_centroids_gdf.iterrows())):

        # add coordinates of census tract and store geoid along with it
        tract_centroid_index.insert(idx, coordinates=centroid.geometry.bounds, obj=geoid)
    
    ################################ CENSUS TRACTS WITHIN BUFFER RADIUS ################################ 
    print('Finding census tracts that are within buffer radius...')
    # Dictionary of Key: GeoID
    # Value: List(GeoID)
    # Contains which census tract centroids are accessible to 
    # that census tract within BUFFER radius
    tracts_in_buffer = defaultdict(list)

    # 1. Go through each census tract centroid
    # 2. Create a BOUNDING BOX of BUFFER radius around that centroid
    # 3. Find which centroids are inside that BOX
    # 4. Check if that centroid exists in the BUFFER CIRCLE of the census tract 
    for idx, (geoid, centroid) in tqdm(enumerate(tract_centroids_gdf.iterrows())):

        tracts_in_buffer[geoid] = []

        # get iterable (generator) of indices from RTree index of census tracts centroids
        # that are contained within a BUFFER BOX of the current centroid
        # http://toblerity.org/rtree/tutorial.html#intersection
        for overlapping_ind in tract_centroid_index.intersection(centroid.geometry.buffer(BUFFER).bounds):

            # Check if current tract centroid's BUFFER CIRCLE
            # contains the overlapping index's CENTROID
            if tract_centroids_gdf.iloc[overlapping_ind].name != geoid and centroid.geometry.buffer(BUFFER).contains(shapely.geometry.shape(tract_centroids_gdf.iloc[overlapping_ind].geometry)):

                # add the overlapping_ind's geoID of the census tract into the current census tract's list
                # of census tracts accessible within buffer radius
                tracts_in_buffer[geoid].append(tract_centroids_gdf.iloc[overlapping_ind].name)
     
    # Store centroid BUFFER dict to file
    print('Saving to ./datasets/tracts_in_buffer.json...')
    with open('./datasets/tracts_in_buffer.json', 'w') as fp:
        json.dump(tracts_in_buffer, fp)
        
    ################################ UNIVERSITIES WITHIN BUFFER RADIUS ################################ 
    print('Finding universities that are within buffer radius...')
    # Dictionary of Keys: geoId
    # Value: List(id_num of university)
    # Contains which universities are accessible to 
    # that census tract within BUFFER radius
    tract_universities = defaultdict(list)

    # 1. Go through each census tract centroid
    # 2. Create a BOUNDING BOX of BUFFER radius around that centroid
    # 3. Find which universities are inside that BOX
    # 4. Check if that university exists in the BUFFER CIRCLE of the census tract 
    for idx, (geoid, centroid) in tqdm(enumerate(tract_centroids_gdf.iterrows())):

        tract_universities[geoid] = []

        # get iterable (generator) of indices from RTree index of universities
        # that are contained within a BUFFER BOX of the current centroid
        # http://toblerity.org/rtree/tutorial.html#intersection
        for overlapping_ind in uni_index.intersection(centroid.geometry.buffer(BUFFER).bounds):

            # Check if current tract centroid's BUFFER CIRCLE
            # contains the overlapping UNIVERSITY index's centre point
            if centroid.geometry.buffer(BUFFER).contains(shapely.geometry.shape(uni_gdf.iloc[overlapping_ind].geometry)):

                # add the overlapping_ind's geoID of the census tract into the current census tract's list
                # of census tracts accessible within buffer radius
                tract_universities[geoid].append(str(uni_gdf.iloc[overlapping_ind].name))
    
    # Store centroid BUFFER dict of universities to file
    print('Saving to ./datasets/tract_universities.json...')
    with open('./datasets/tract_universities.json', 'w') as fp:
        json.dump(tract_universities, fp)
        
    # Create a dictionary of number of universities accessible to each census tract
    num_accessible_unis = {geoid: len(unis) for geoid, unis in tract_universities.items()}
    
    # Creating Pandas Dataframe from dictionary
    education_deserts = pd.DataFrame.from_dict(num_accessible_unis, orient='index', columns=['Number of Accessible Universities'])
    education_deserts['Education Desert'] = 0
    education_deserts.loc[education_deserts['Number of Accessible Universities'] == 0, 'Education Desert'] = 1
    
    print('Number of Education Deserts in our dataset: {}'.format(len(education_deserts[education_deserts['Education Desert'] == 1])))
    print('Number of Non-Education Deserts in our dataset: {}'.format(len(education_deserts[education_deserts['Education Desert'] == 0])))
    
    # Write to csv file
    print('Saving to ./datasets/education_deserts.csv...')
    education_deserts.to_csv(r'./datasets/education_deserts.csv')