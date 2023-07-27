import geopandas as gpd
from mercantile import bounds, Tile
import click
import os
import numpy as np
import pandas as pd

# Get Tile bounds from Tile ID
def getcoordinates(tile_id):
    x, y, z = [int(m) for m in tile_id.split('_')]
    coords = bounds(Tile(x=x, y=y, z=z))
    return ','.join([str(c) for c in coords])


@click.command()
@click.option('--input', help='input predictions')
@click.option('--outdir', default='tiles', help='directory containing all tile geojsons')
@click.option('--out-csv', default="annotations.csv", help='file containing all tile ids and annotator info')
@click.option('--out-sample', default="samples.csv", help='file containing discount sampled tile ids')

def main(input, outdir, out_csv, out_sample):
    gdf = gpd.read_file(input)
    gdf = gdf[gdf["damage"] >= 1.0]

    os.makedirs(outdir, exist_ok=True)
    all_tile_ids = gdf['TILE_ID'].unique()
    for tile_id in all_tile_ids:
        df = gdf.loc[gdf["TILE_ID"] == tile_id]
        df.loc[:, 'tile_bbox'] = getcoordinates(tile_id)
        df.to_file(os.path.join(outdir, f'{tile_id}.geojson'), driver='GeoJSON')

    
    tiles_df = gdf.groupby('TILE_ID').size().reset_index().rename(columns={0: 'detector_count'})
    tiles_df.loc[:, ['true_count', 'Annotator']] = ''
    tiles_df.to_csv(out_csv, index=False)

    detector_counts = list(tiles_df['detector_count'])
    tile_ids = list(tiles_df['TILE_ID'])
    prob_dist = np.array(detector_counts) / np.sum(detector_counts)
    samples = list(np.random.choice(tile_ids, 2 * len(tile_ids), p=prob_dist, replace=True))
    samples_df = pd.DataFrame({ 'sample': samples })
    samples_df.loc[:, 'annotated'] = False
    samples_df.to_csv(out_sample, index=False)
if __name__ == "__main__":
    main()