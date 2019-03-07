# Library Imports
import fiona 
import rtree
import shapely
from shapely.geometry import shape
from helper import get_bounding_box
import json

# Shapely library to help with calculation
# of the representative centroid position
from shapely.geometry import MultiPoint

import geopandas
import pandas as pd
import numpy as np
import subprocess
import os
import requests
from bs4 import BeautifulSoup
import seaborn as sns
sns.set(style="ticks")

# default dictionary (a dictionary with a default value if a key doesn't exist)
from collections import defaultdict

# To unzip file
import zipfile

# To have progress bar
from tqdm import tqdm

# plotting libraries
import matplotlib
import matplotlib.pyplot as plt
plt.style.use('seaborn-paper')
get_ipython().run_line_magic('matplotlib', 'inline')

# Helper function to create a new folder
def mkdir(path):
    try: 
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise
        else:
            print("(%s) already exists" % (path))


# Function that returns 4 items:
# 1. RTree Index for Universities
# 2. List of (<str> UniID, <shapely.Point> Point of university)
# 3. RTree Index for Census Tracts
# 4. List of (<str> GeoID, <shapelyPoint> Point of census tract centroid)
def get_uni_tract_data():
    # ---
    # ## Datasets

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

    # Download data 
    if not os.path.isfile(DATASETS_PATH + ct_file_name):

        os.system('!wget --directory-prefix={} -Nq {}'.format(DATASETS_PATH, ct_data_url))

        # Unzipping the file
        zip_ref = zipfile.ZipFile(DATASETS_PATH + ct_file_name + '.zip', 'r')
        zip_ref.extractall(DATASETS_PATH + ct_file_name + '/')
        zip_ref.close()

        # Remove the old census tract .zip shapefile
        subprocess.call(['rm', '-rf', DATASETS_PATH + ct_file_name + '.zip'])

    # Let's take a look at the census tract data
    census_tracts = pd.read_csv(DATASETS_PATH + ct_file_name, encoding='ISO-8859-1', low_memory=False)

    # ### American University Data
    # Download data 
    if not os.path.isfile(DATASETS_PATH + au_file_name):

        os.system('!wget --directory-prefix={} -Nq {}'.format(DATASETS_PATH, au_data_url))

    # Let's take a look at the american university data
    universities = pd.read_excel(DATASETS_PATH + au_file_name, index_col='ID number')

    # ### University Points Dictionary
    # __Let's store the IDs and Location (Lat, Long) of the universities as Shapely Point objects in list__

    # List of tuples to store all the university
    # locations as Shapely Points
    uni_list = []

    for idx, id_num in enumerate(universities.index):
        uni_list.append((id_num, shape({"type": "Point",
                                       "coordinates": (universities.loc[id_num, 'Longitude location of institution'],
                                                       universities.loc[id_num, 'Latitude location of institution'])})))


    # ### University RTree Index
    # __Let's store the IDs and Location (Lat, Long) of the universities in an RTree Index__

    # Initialize rtree spatial index
    uni_index = rtree.index.Index()

    # Iterate over all american universities
    for idx, (id_num, uni) in enumerate(uni_list):

        # add coordinates of univeristy location and store id along with it
        uni_index.insert(idx, coordinates=uni.bounds, obj=id_num)

        # we can now query this datastructure with a point and it will tell us which 
        # polygon it lies in


    # ### Census Tract Shape Files
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


    # ### Census Tract Centroid Points Dictionary
    # __Let's store the geoIDs and Location (Lat, Long) of the census tract centroids as Shapely Point objects in list__
    # 
    # ### Census Tract RTree Index
    # __Let's store the geoIDs and Location (Lat, Long) of the universities in an RTree Index__

    # ----------------------------
    # Let's calculate and store each of 
    # the centroids of each
    # census tract in a list of tuples
    tract_centroids = []

    # ----------------------------
    # Initialize rtree spatial index
    tract_index = rtree.index.Index()

    for subdir, dirs, files in list(os.walk(CENSUS_TRACTS_PATH))[1:]:

        # Opening the shapefile
        state_shapes = fiona.open(subdir)

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

            # add bounding box of census tract and store geoid along with it
            tract_index.insert(idx, coordinates=tract.bounds, obj=geoid)

            # we can now query this datastructure with a point and it will tell us which 
            # polygon it lies in

            # ----------------------------
            # Create Census tract Centroid
            # True centroid, not necessarily an existing point
            centroid_pt = points.centroid

            # A represenative point, not centroid,
            # that is guarnateed to be with the geometry
            tract_centroids.append((geoid, points.representative_point()))
            
    return uni_index, uni_list, tract_index, tract_centroids