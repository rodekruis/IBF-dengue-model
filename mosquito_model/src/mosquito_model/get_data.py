"""
This is a simple script to access, aggregate and download a series of raster files from Google Earth Engine.
The data source is the GSMaP dataset.
This script gets GSMaP data on rainfall within the Philippines and sum all values within a month, i.e. it
computes the monthly cumulative rainfall, expressed in mm/h.
Author: Jacopo Margutti (jmargutti@redcross.nl)
Date: 27-09-2019
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
import math
import click

# Computes the bits we need to extract.
def getQABits(image, start, end, newName):
    pattern = 0
    listB = list(range(start, end + 1))
    for one in listB:
        pattern += math.pow(2, one)
        pattern = int(pattern)

    return (image.select([0], [newName])
            .bitwiseAnd(pattern)
            .rightShift(start))


# @click.command()
# @click.option('--datestart', help='start date (%Y-%m-%d)')
# @click.option('--dateend', help='end date (%Y-%m-%d)')
# @click.option('--dest', help='output directory')
# @click.option('--collection', help='GEE collection')
# @click.option('--variable', help='GEE variable in collection')
def get_data(country_iso_code, datestart, dateend, dest, collection, variable):
    # initialize Google Earth Engine
    # ee.Initialize()

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

    # print to screen which dates are being selected
    # print('processing dates', datestart, dateend)
    file_name = folder + '/' + name

    if os.path.exists(file_name):
        print('found existing', name, ', skipping')
        return file_name

    # get GSMaP ImageCollection within given dates and bounding box
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
        print('ERROR: no data found')
        return 'error'

    # get list of images in collection
    clist = col.toList(col.size().getInfo())
    # save the scale of first image (need to use it later to save aggregated raster)
    image_scale = int(tools.image.minscale(ee.Image(clist.get(0)).select(variable)).getInfo())

    # filter only data with good QA flag(s)
    if 'LST' in variable:
        # lst_qa = {}
        # lst_qa['LST_Day_1km'] = 'QC_Day'
        # lst_qa['LST_Night_1km'] = 'QC_Night'
        # def maskbyBitsLST(img):
        #     QA = img.select(lst_qa[variable])
        #     QA1 = getQABits(QA, 0, 1, 'QA')
        #     QA2 = getQABits(QA, 2, 3, 'QA')
        #     QA3 = getQABits(QA, 4, 5, 'QA')
        #     QA4 = getQABits(QA, 6, 7, 'QA')
        #     mask = QA1.eq(0).And(QA2.eq(0)).And(QA3.lt(2)).And(QA4.lt(2))
        #     return img.updateMask(mask)
        # col = col.map(maskbyBitsLST).select(variable)
        # tranform to celsius
        def KtoC(img):
            return (img.select(variable)
                    .float()
                    .multiply(0.02)
                    .subtract(273.15))
        col = col.map(KtoC)

    # elif 'VI' in variable:
        # def maskbyBitsVI(img):
        #     QA = img.select('DetailedQA')
        #     QA1 = getQABits(QA, 0, 1, 'QA')
        #     QA2 = getQABits(QA, 2, 5, 'QA')
        #     QA3 = getQABits(QA, 6, 7, 'QA')
        #     QA4 = getQABits(QA, 8, 8, 'QA')
        #     QA5 = getQABits(QA, 10, 10, 'QA')
        #     QA6 = getQABits(QA, 15, 15, 'QA')
        #     mask = QA1.lt(2).And(QA2.lt(12)).And(QA3.neq(3)).And(QA3.neq(0)).And(QA4.eq(0)).And(QA5.eq(0)).And(
        #         QA6.eq(0))
        #     return img.updateMask(mask)
        # col = col.map(maskbyBitsVI).select(variable)

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
    batch.image.toLocal(image_agg,
                        file_name,
                        scale=image_scale,
                        region=bounding_box)
    return file_name


# if __name__ == "__main__":
#     get_data()