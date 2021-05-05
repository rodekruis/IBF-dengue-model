"""
Compute zonal statistics on raster images.
Author: Jacopo Margutti (jmargutti@redcross.nl)
Date: 22-03-2021
"""
import rasterio
import rasterio as rio
import rasterio.mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import geopandas as gpd
import numpy as np
import fiona
import os
import pandas as pd
from tqdm import tqdm
import glob
import datetime
import click


def clipTiffWithShapes(tiffLocaction, shapes):
    with rasterio.open(tiffLocaction) as src:
        outImage, out_transform = rasterio.mask.mask(src, shapes, crop=True)
        outMeta = src.meta.copy()

    outMeta.update({"driver": "GTiff",
                    "height": outImage.shape[1],
                    "width": outImage.shape[2],
                    "transform": out_transform})

    return outImage, outMeta


def calculateRasterStats(source, district, outFileAffected, exclude_zero=True):
    raster = rasterio.open(outFileAffected)

    array = raster.read(masked=True)
    band = array[0]

    if exclude_zero:
        band[band == 0] = np.nan
        band = band[~np.isnan(band)]

    theMean = band.mean()
    stats = {'source': source,
             'mean': str(theMean),
             'district': district
             }
    return stats


def compute_zonalstats(raster, vector, feat):

    raster_file_dir = raster
    rasters = []
    for root, dirs, files in os.walk(raster_file_dir):
        path = os.path.join(*root.split(os.sep))
        for file in files:
            if '.tif' in file:
                raster_path = os.path.join(path, file)
                rasters.append(raster_path)

    shapefile = vector#r'C:\Users\JMargutti\OneDrive - Rode Kruis\Rode Kruis\ERA\shapefiles\phl_admbnda_adm2_psa_namria_20200529.shp'
    fiona_shapefile = fiona.open(shapefile, "r")

    gdf_adm = gpd.read_file(shapefile)
    adm_divisions = gdf_adm[feat].tolist()

    df_final = pd.DataFrame(index=pd.MultiIndex.from_product([adm_divisions], names=['adm_division']))

    for raster_path in rasters:
        dir_col = raster_path.split('.')[1]
        # print('processing', dir_col)

        df_final[dir_col] = np.nan

        stats = []
        tempPath = "temp.tif"
        source = dir_col
        exclude_zero = True
        if 'precip' in dir_col.lower():
            exclude_zero = False

        # clip where people live
        # TBI

        # Clip affected raster per area
        for area in fiona_shapefile:
            outImage, outMeta = clipTiffWithShapes(raster_path, [area["geometry"]])

            # Write clipped raster to tempfile to calculate raster stats
            with rasterio.open(tempPath, "w", **outMeta) as dest:
                dest.write(outImage)

            statsDistrict = calculateRasterStats(source, str(area['properties'][feat]), tempPath, exclude_zero)
            stats.append(statsDistrict)

        for idx, stat_region in enumerate(stats):
            df_final.at[adm_divisions[idx], 'mean'] = stat_region['mean']
    if os.path.exists("temp.tif"):
        os.remove("temp.tif")
    return df_final


