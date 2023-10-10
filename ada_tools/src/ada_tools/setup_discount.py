import json
import os
from pathlib import Path
import re

import click
import geopandas as gpd
from mercantile import bounds, Tile
import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import transform_bounds
from shapely.geometry import box

EPS = 4e-2
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

def get_image_dir_contents(image_dir):
    dir_path = Path(image_dir)
    if not (dir_path.exists() and dir_path.is_dir()):
        raise ValueError(f"Image directory does not exist: {image_dir}")

    image_bounds_and_urls = [] 
    for tif_path in dir_path.glob('*.tif'):

        tile_url = get_url(tif_path.name)
        with rasterio.open(tif_path) as geo_image_file:
            tiff_bounds = transform_bounds(geo_image_file.crs, 'epsg:4326', *geo_image_file.bounds) 
            image_bounds_and_urls.append((box(*tiff_bounds), tile_url))

    return image_bounds_and_urls


@click.command()
@click.option('--input', help='input predictions')
@click.option('--pre-images', help='directory containing pre-disaster images')
@click.option('--post-images', help='directory containing post-distaster images')
@click.option('--outdir', default='tiles', help='directory containing all tile geojsons')
@click.option('--out-csv', default="annotations.csv", help='file containing all tile ids and annotator info')

def main(input, pre_images, post_images, outdir, out_csv):
    gdf = gpd.read_file(input)
    gdf = gdf[gdf["damage"] >= 1.0]

    os.makedirs(outdir, exist_ok=True)

    tile_id_key = "TILE_ID"
    
    tiles_df = gdf.groupby(tile_id_key)['damage'].count().reset_index().rename(columns={'damage': 'detector_count'})
    tiles_df.loc[:, ['true_count', 'Annotator']] = ''
    detector_counts = list(tiles_df['detector_count'])
    if min(detector_counts) == 0:
        detector_counts = [c + max(max(detector_counts)*EPS, 1) for c in detector_counts]

    tiles_df['detector_count'] = detector_counts

    # Performs DISCount sampling
    tile_ids = list(tiles_df[tile_id_key])
    prob_dist = np.array(detector_counts) / np.sum(detector_counts)
    samples = list(np.random.choice(tile_ids, 2 * len(tile_ids), p=prob_dist, replace=True))

    # Order annotation tracking CSV by each tile's first sample index
    sample_order = np.arange(len(samples), dtype=int)
    sample_tracking_df = pd.DataFrame({tile_id_key: samples, "ordering": sample_order})
    display_order = sample_tracking_df.groupby(tile_id_key)["ordering"].min().reset_index()
    tiles_df = pd.merge(tiles_df, display_order, how="left", on=tile_id_key).sort_values(by="ordering")
    tiles_df.to_csv(out_csv, index=False, columns=[tile_id_key, "detector_count", "true_count", "Annotator"])

    # Collect sample indices to be written to each tile's geoJSON file
    tile_to_sample_map = sample_tracking_df.groupby(tile_id_key)["ordering"].apply(list).to_dict()
 
    # add event bounds
    pre_bounds_and_urls = get_image_dir_contents(pre_images)
    post_bounds_and_urls = get_image_dir_contents(post_images)

    for i, tile_id in enumerate(tile_ids):
        df = gdf.loc[gdf["TILE_ID"] == tile_id]
        tile_bounds = get_tile_bounds(tile_id)
        df_geojson = json.loads(df.to_json())
        df_geojson['indexes'] = tile_to_sample_map.get(tile_id, [])
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