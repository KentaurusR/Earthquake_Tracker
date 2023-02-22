import pandas as pd  # Library for data manipulation and analysis, we upload our USGS data into a pandas DataFrame
import geopandas as gpd  # Adds support for geospatial data to pandas objects
from shapely.geometry import Point  # Allows us to create point shape data
from sklearn.cluster import DBSCAN  # DBSCAN = Density-Based Spatial Clustering of Applications with Noise
import numpy as np  # Library that adds support for large arrays/matrices
import folium  # Allows us to create a map in a separate HTML file, can be used to create many types of Leaflet Maps, in this program we use the default openstreetmap setting
from branca.colormap import LinearColormap  # Used to create a linear color map, which is used as our legend for our different colors of points
import time  # Used to add pauses at certain points of the program

url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.csv"  # URL for our USGS past month earthquake data

print("Hi, welcome to my Earthquake Tracker.\nThis program uses USGS databases to track earthquakes worldwide from the past month and plots them on a map in an HTML file.")
print("You will be able to find the HTML map file in the same folder that this program is stored in.\n")
print("This program will also identify earthquake clusters and print the location, number of earthquakes, and average magnitude.\n")
print("")


# This line of code loads earthquake data from the USGS csv into a Pandas DataFrame
df = pd.read_csv(url)

# We need to convert latitude and longitude columns to a Point object, which can be mapped
geometry = [Point(xy) for xy in zip(df["longitude"], df["latitude"])]

# We need to create a GeoDataFrame from the Pandas DataFrame and Point object
gdf = gpd.GeoDataFrame(df, geometry=geometry)  # utilizes geopandas, which uses our pandas DataFrame and point objects

# Set the coordinate reference system (CRS) to WGS84 (standard USDoD definition for global reference system for geospatial information)
gdf.crs = "EPSG:4326"  # EPSG:4326 is a Geographic Coordinate System (GCS) that uses the WGS84 ellipsoid

# Now, we apply the DBSCAN clustering algorithm, which will help us identify clusters of earthquakes
coords = np.radians(gdf[["latitude","longitude"]])  # creates a numpy array called 'coords', which stores latitude and longitude values
epsilon = 50/6371.0  # 50km divided by 6,371km (which is the radius of the earth), used to define the radius of the area around each point that will be considered when identifying clusters
min_samples = 20  # determines the minimum number of earthquakes in an area to be considered a cluster
dbscan = DBSCAN(eps=epsilon, min_samples=min_samples, algorithm="ball_tree", metric="haversine").fit(coords)  # the fit() method applies our DBSCAN algorithm to our 'coords' numpy array, explanation on DBSCAN algorithm listed below this block of code
gdf["cluster"] = dbscan.labels_  # creates a new column in our GeoDataFrame ('gdf') named cluster, which we can use to access our cluster data

# Explanation on Arguments passed to the DBSCAN function:
    # we set eps equal to our epsilon value, which determiens the maximum distance between two points for them to be considered part of the same cluster
    # we set out min_samples to our established min_samples variable, which is 10
    # we set our algorithm equal to ball_tree, which is an algorithm that builds a tree to represent the data and uses the tree to search for neighbors (using our eps value)
    # we set our metric, which is used to compute distance between points, to the haversvine formula determines the great-circle distance between two points on a sphere given their longitude and latitude, we need this because if we used Euclidean distance, which assumes a flat plane, we would get inaccurate results

input("Press 'Enter' or 'Return' to continue: ")

# Now, we retrieve the number of identified clusters
n_clusters = len(set(dbscan.labels_)) - (1 if -1 in dbscan.labels_ else 0)

print("\nEarthquake Clusters Detected: "+str(n_clusters))
time.sleep(1)

# Now, we print information about each cluster
for i in range(n_clusters):
    cluster_indices = np.where(dbscan.labels_ == i)[0]  # uses numpy, which adds support for large arrays/matrices, to create a list of earthquake clusters
    cluster_size = len(cluster_indices)  # determines number of earthquakes in cluster
    cluster_magnitude = gdf.loc[cluster_indices, "mag"].mean()  # determines mean magnitude of cluster
    cluster_gdf = gdf.iloc[cluster_indices]  # iloc() function helps us retrieve a specific value from a row or column, we set it to the value of cluster_indices
    cluster_location = cluster_gdf['place'].iloc[0]  # pulls location data for each cluster
    print(f"Cluster {i+1}: {cluster_size} earthquakes, average magnitude of {cluster_magnitude:.2f},location: {cluster_location}")

print("\nPlease wait a moment while the HTML map file is created.\n")

# We define a function to determine the color of each marker based on magnitude
def get_color(mag):
    if mag < 3:
        return 'green'
    elif mag < 5:
        return 'orange'
    elif mag >= 5:
        return 'red'

# Create a colormap for the legend using the LinearColormap() function from branca
colormap = LinearColormap(
    ['green', 'orange', 'red'],  #sets the color gradient for the colormap, it will appear in the order listed
    vmin=0,  # sets the minimum number value for the colormap, which will always be 0
    vmax=df['mag'].max(),  # sets the maximum number value for the colormap, since the max value of the data can change with time, we set this value to the max() value of our 'mag'
    caption = 'Magnitude Scale'  # sets the caption for the colormap
)

# Create a map that is centered on the mean of the earthquake coordinates
center_lat = df["latitude"].mean()
center_lon = df["longitude"].mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=3,control_scale=True)
# location uses our mean data to center the map with our data, zoom_start establishes initial zoom level for the map, control_scale=True gives us a scale for our map

# Add markers to the map for each earthquake
for i, row in df.iterrows(): # we move through each row in our data set, and find coordinate data to map out each point
    if row['mag'] > 0:
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=5,
            color=get_color(row["mag"]),  # use our get_color function to determine the color of the point based on its magnitude
            fill=True,
            fill_color=get_color(row["mag"]),
            fill_opacity=0.7,  # determines opacity of the interior color of each point
            tooltip=f"Magnitude: {row['mag']}",  # Adds the magnitude as a viewable element for each point, on the map you can hover over each point and see the magnitude
        ).add_to(m)
    else:
        pass

# Add the legend to the map
# If you wanted to add additional layers to your map, and include the option to change layers, you would type 'm.add_child(folium.map.LayerControl())', but for this program we're just using the openstreetmap
colormap.add_to(m)  # adds our color map (which is our legend) to our map


# Save the map as an HTML file
m.save('USGS Worldwide Earthquakes Past Month.html')

# Information to clarify location of map, and map legend
print("\nThe map HTML map file has been completed.")
print("\nEarthquakes with a magnitude under 3 are marked as green.")
print("Earthquakes with a magnitude between 3 and 5 are marked orange.")
print("Earthquakes with a magnitude of 5 or higher are marked red.")

print("\nCheck the folder that this program is stored in, there will be an HTML file called 'USGS Worldwide Earthquakes Past Month', you can open it in your web browser of choice.")
print("\nThank you for using my Earthquake Tracker!")