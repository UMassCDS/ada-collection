import geopandas as gpd
from mercantile import bounds, Tile
from shapely.geometry import box
import click
import os
import numpy as np
import pandas as pd
import json
import glob
from collections import defaultdict
import rasterio
from rasterio.warp import transform_bounds
import re

np.random.seed(0)
# Get Tile bounds from Tile ID
def get_tile_bounds(tile_id):
    x, y, z = [int(m) for m in tile_id.split('_')]
    return bounds(Tile(x=x, y=y, z=z))

def get_url(filename):
    url = re.sub(r'https:--', 'https://', filename)
    url = re.sub(r'-events-', '/events/', url)
    url = re.sub(r'-pre-event-', '/pre-event/', url)
    url = re.sub(r'-post-event-', '/post-event/', url)
    url = re.sub('(?<=\d{4}-\d{2}-\d{2})-',  '/', url)
    url = re.sub('-(?=\w+.tif)',  '/', url)
    return url

def get_tiff_url(tile_bounds, bounds_and_urls):
    for tiff_bounds, url in bounds_and_urls:
        if tiff_bounds.contains(box(*tile_bounds)):
            return url
    return None

@click.command()
@click.option('--input', help='input predictions')
@click.option('--outdir', default='tiles', help='directory containing all tile geojsons')
@click.option('--out-csv', default="annotations.csv", help='file containing all tile ids and annotator info')
@click.option('--out-sample', default="samples.csv", help='file containing discount sampled tile ids')

def main(input, outdir, out_csv, out_sample):
    gdf = gpd.read_file(input)
    gdf = gdf[gdf["damage"] >= 1.0]

    os.makedirs(outdir, exist_ok=True)

    tiles_df = gdf.groupby('TILE_ID').size().reset_index().rename(columns={0: 'detector_count'})
    tiles_df.loc[:, ['true_count', 'Annotator']] = ''
    tiles_df.to_csv(out_csv, index=False)

    detector_counts = list(tiles_df['detector_count'])
    tile_ids = list(tiles_df['TILE_ID'])
    prob_dist = np.array(detector_counts) / np.sum(detector_counts)
    samples = list(np.random.choice(tile_ids, 2 * len(tile_ids), p=prob_dist, replace=True))

    tile_to_sample_map = defaultdict(list)


    # add pre_event_bounds
    pre_bounds_and_urls = []
    for pre_path in glob.glob('images/pre-event/*.tif'):
        tile_url = get_url(pre_path.split('/')[-1])
        with rasterio.open(pre_path) as geo_image_file:
            tiff_bounds = transform_bounds(geo_image_file.crs, 'epsg:4326', *geo_image_file.bounds) 
            pre_bounds_and_urls.append((box(*tiff_bounds), tile_url))

    post_bounds_and_urls = []
    for post_path in glob.glob('images/post-event/*.tif'):
        tile_url = get_url(post_path.split('/')[-1])
        with rasterio.open(post_path) as geo_image_file:
            tiff_bounds = transform_bounds(geo_image_file.crs, 'epsg:4326', *geo_image_file.bounds)
            post_bounds_and_urls.append((box(*tiff_bounds), tile_url))




    #  add post event bounds
    for i, sample in enumerate(samples):
        tile_to_sample_map[sample] += [i]

    for i, tile_id in enumerate(tile_ids):
        df = gdf.loc[gdf["TILE_ID"] == tile_id]
        tile_bounds = get_tile_bounds(tile_id)
        df_geojson = json.loads(df.to_json())
        df_geojson['indexes'] = tile_to_sample_map[tile_id]
        df_geojson['tile_bbox'] = ','.join([str(c) for c in tile_bounds])
        df_geojson['annotated'] = False
        df_geojson['detector_count'] = detector_counts[i]
        df_geojson['true_count'] = None
        df_geojson['pre_tiff_url'] = get_tiff_url(tile_bounds, pre_bounds_and_urls)
        df_geojson['post_tiff_url'] = get_tiff_url(tile_bounds, post_bounds_and_urls)
        with open(os.path.join(outdir, f'{tile_id}.geojson'), 'w') as f:
            json.dump(df_geojson, f, indent=4)

if __name__ == "__main__":
    main()