"""
Aggregate and download a series of raster images from Google Earth Engine.
Author: Jacopo Margutti (jmargutti@redcross.nl)
Date: 22-03-2021
"""
import ee
from geetools import batch
from geetools import tools
from country_bounding_boxes import country_subunits_by_iso_code
import os
import datetime
today = datetime.date.today()
start_date = datetime.date.today() + datetime.timedelta(-30)
import time
import logging


def get_data(country_iso_code, datestart, dateend, dest, collection, variable):

    # define bounding box of the Philippines
    bbox_coords = [c.bbox for c in country_subunits_by_iso_code(country_iso_code)][0]
    bounding_box = ee.Geometry.Rectangle(list(bbox_coords))
    output_dir = dest

    # get list of dates from given date range
    if not isinstance(datestart, str):
        datestart = datestart.strftime('%Y-%m-%d')
        dateend = dateend.strftime('%Y-%m-%d')

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    collection_dir = collection.replace('/', '_')
    folder = output_dir + '/' + collection_dir + '_' + variable
    if not os.path.exists(folder):
        os.mkdir(folder)

    # convert datetime objects to strings
    name = variable + '_' + datestart + '_' + dateend
    file_name = folder + '/' + name

    if os.path.exists(file_name):
        logging.error('found existing', name, ', skipping')
        return file_name

    # get ImageCollection within given dates and bounding box
    try:
        col = (ee.ImageCollection(collection)
               .filterDate(datestart, dateend)
               .filterBounds(bounding_box))
    except:
        time.sleep(30)
        col = (ee.ImageCollection(collection)
               .filterDate(datestart, dateend)
               .filterBounds(bounding_box))

    count = col.size().getInfo()
    if count == 0:
        logging.error('ERROR: no data found')
        exit(0)

    # get list of images in collection
    clist = col.toList(col.size().getInfo())
    # save the scale of first image (need to use it later to save aggregated raster)
    image_scale = int(tools.image.minscale(ee.Image(clist.get(0)).select(variable)).getInfo())

    # filter only data with good QA flag(s)
    if 'LST' in variable:
        # tranform to celsius
        def KtoC(img):
            return (img.select(variable)
                    .float()
                    .multiply(0.02)
                    .subtract(273.15))
        col = col.map(KtoC)

    if 'Rainf_f_tavg' in variable:
        def kgmstomm(img):
            return (img.select(variable)
                    .float()
                    .multiply(2.628e+6))
        col = col.map(kgmstomm)

    if 'precip' in variable.lower():
        # print('sum rainfall')
        image_agg = col.select(variable).reduce(ee.Reducer.sum())
    else:
        # calculate mean over month
        image_agg = col.select(variable).reduce(ee.Reducer.mean())

    if image_scale < 1000:
        image_scale = 1000

    # set a name to the file and download to disk
    # print('downloading ' + name)
    try:
        batch.image.toLocal(image_agg,
                            file_name,
                            scale=image_scale,
                            region=bounding_box)
    except FileExistsError:
        pass
    return file_name
