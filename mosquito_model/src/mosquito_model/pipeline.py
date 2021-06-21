"""
Run the full mosquito-model pipeline.
Author: Jacopo Margutti (jmargutti@redcross.nl)
Date: 22-03-2021
"""
import pandas as pd
from mosquito_model.get_data import get_data
from mosquito_model.compute_zonalstats import compute_zonalstats
from mosquito_model.compute_risk import compute_risk
from mosquito_model.compute_suitability import compute_suitability
import datetime
from dateutil.relativedelta import relativedelta
import geopandas as gpd
from tqdm import tqdm
import os
import ee
import click
import json
import shutil
from pathlib import Path
import requests
from dotenv import load_dotenv
import errno
import json


def get_dates_in_range(begin, end):
    """
    this function returns two lists of dates (start_dates and end_dates),
    which correspond to the beginning and end of each month within the input date range (begin, end).
    Example: input: begin='2019-07-01', end='2019-08-31'
             output: start_dates=['2019-07-01', '2019-08-01'], end_dates=['2019-07-31', '2019-08-31']
    """
    dt_start = datetime.datetime.strptime(begin, '%Y-%m-%d')
    dt_end = datetime.datetime.strptime(end, '%Y-%m-%d')
    one_day = datetime.timedelta(1)
    start_dates = [dt_start]
    end_dates = []
    today = dt_start
    while today <= dt_end:
        tomorrow = today + one_day
        if tomorrow.month != today.month:
            start_dates.append(tomorrow)
            end_dates.append(today)
        today = tomorrow
    end_dates.append(dt_end)
    return start_dates[:-1], end_dates[:-1]


# define input data
input_data = [
    ('NASA/GPM_L3/IMERG_V06', 'precipitationCal'),
    ('JAXA/GPM_L3/GSMaP/v6/operational', 'hourlyPrecipRate'),
    ('MODIS/006/MOD11A1', 'LST_Day_1km'),
    ('MODIS/006/MOD11A1', 'LST_Night_1km')
]


@click.command()
@click.option('--countrycode', default='PHL', help='country iso code')
@click.option('--vector', default='input/phl_admbnda_adm2plusNCR_simplified.shp',
              help='vector file with admin boundaries')
@click.option('--temperaturesuitability', default='input/temperature_suitability.csv',
              help='table with suitability vs temperature')
@click.option('--thresholds', default='input/alert_thresholds.csv',
              help='table with thresholds anc coefficients to convert risk to dengue cases')
@click.option('--demographics', default='input/phl_vulnerability_dengue_data_ibfera.csv',
              help='table with demographic data')
@click.option('--credentials', default='credentials',
              help='directory with credentials')
@click.option('--admincode', default='ADM2_PCODE', help='which feature in vector file')
@click.option('--data', default='input', help='input data directory')
@click.option('--dest', default='output', help='output data directory')
@click.option('--predictstart', default=datetime.date.today().strftime("%Y-%m-%d"),
              help='start predictions from date (%Y-%m-%d)')
@click.option('--predictend', default=None, help='end predictions on date (%Y-%m-%d)')
@click.option('--storeraster', is_flag=True, help='store raster data')
@click.option('--verbose', is_flag=True, help='print each step')
@click.option('--ibfupload', is_flag=True, help='upload output to IBF system using IBF-API')
@click.option('--saverequest', is_flag=True, help='save IBF-API call to json')
def main(countrycode, vector, temperaturesuitability, thresholds, demographics, credentials, admincode, data, dest,
         predictstart, predictend, storeraster, verbose, ibfupload, saverequest):

    # initialize GEE
    gee_credentials = os.path.join(credentials, 'era-service-account-credentials.json')
    with open(gee_credentials) as f:
        credentials_dict = json.load(f)
        service_account = credentials_dict['client_email']
        gee_credentials_token = ee.ServiceAccountCredentials(service_account, gee_credentials)
        ee.Initialize(gee_credentials_token)

    # define administrative divisions
    gdf = gpd.read_file(vector)
    adm_divisions = gdf[admincode].unique()

    # define date range
    start_date = datetime.datetime.strptime(predictstart, '%Y-%m-%d') - relativedelta(months=+3)
    start_date = start_date.replace(day=1)
    start_date = start_date.strftime("%Y-%m-%d")
    if predictend is not None:
        end_date = datetime.datetime.strptime(predictend, '%Y-%m-%d') - relativedelta(months=+1)
        end_date = end_date.strftime("%Y-%m-%d")
        start_dates, end_dates = get_dates_in_range(start_date, end_date)
    else:
        end_date = predictstart
        start_dates, end_dates = get_dates_in_range(start_date, end_date)

    # define input/output directories
    os.makedirs(data, exist_ok=True)
    os.makedirs(dest, exist_ok=True)
    processed_data = os.path.join(dest, 'data_aggregated.csv')
    predictions_data = os.path.join(dest, 'predictions.csv')

    if not os.path.exists(processed_data):
        # initialize dataframe for processed data
        months, years = [], []
        for date in start_dates:
            years.append(date.year)
            months.append(date.month)
        df_data_processed = pd.DataFrame()
        for adm_division in adm_divisions:
            for year, month in zip(years, months):
                df_data_processed = df_data_processed.append(pd.Series(name=(adm_division, year, month), dtype='object'))

        # get raw data, compute zonal statistics and save processed data
        for data_tuple in input_data:
            print(f"starting collection {data_tuple[0]} {data_tuple[1]}")
            raster_data = ''
            for start_date, end_date in tqdm(zip(start_dates, end_dates), total=len(start_dates)):
                # get raw data
                raster_data = get_data(countrycode, start_date, end_date, data, data_tuple[0], data_tuple[1])
                # compute zonal statistics
                df_stats = compute_zonalstats(raster_data, vector, admincode).reset_index()
                # save zonal statistics in dataframe for processed data
                for ix, row in df_stats.iterrows():
                    try:
                        df_data_processed.at[(row['adm_division'], start_date.year, start_date.month), data_tuple[1]] = row['mean']
                    except:
                        print('ERROR at', data_tuple, start_date, end_date)
            # remove raster data
            if not storeraster:
                shutil.rmtree(Path(raster_data).parent)

        df_data_processed.rename_axis(index=['adm_division', 'year', 'month'], inplace=True)
        df_data_processed.to_csv(processed_data)  # store processed data
    else:
        df_data_processed = pd.read_csv(processed_data)
    if verbose:
        print('PROCESSED METEOROLOGICAL DATA')
        print(df_data_processed.head())

    # compute vector suitability
    df = compute_suitability(processed_data, temperaturesuitability)

    # compute risk
    df_predictions = compute_risk(df, adm_divisions, num_months_ahead=3)
    if verbose:
        print('VECTOR SUITABILITY AND RISK PREDICTIONS')
        print(df_predictions.head())

    # calculate exposed population
    df_thresholds = pd.read_csv(thresholds)
    df_demo = pd.read_csv(demographics, index_col=1)
    df_predictions['potential_cases'] = 0
    df_predictions['potential_cases_U9'] = 0
    df_predictions['potential_cases_65'] = 0
    df_predictions['alert'] = False

    for ix, row in df_predictions.iterrows():
        place_date = (df_thresholds['adm_division']==row['adm_division']) & (df_thresholds['month']==row['month'])
        coeff = df_thresholds[place_date]['coeff'].values[0]
        thr_std = df_thresholds[place_date]['alert_threshold_std'].values[0]
        thr_qnt = df_thresholds[place_date]['alert_threshold_qnt'].values[0]
        max_thr = max(thr_std, thr_qnt)
        if row['risk'] > thr_std and row['risk'] > thr_qnt:
            df_predictions.at[ix, 'alert'] = True
        df_predictions.at[ix, 'potential_cases'] = int(coeff * row['risk'] * df_demo.loc[row['adm_division'], 'Population'])
        df_predictions.at[ix, 'potential_cases_U9'] = int(coeff * row['risk'] * df_demo.loc[row['adm_division'], 'Population U9'])
        df_predictions.at[ix, 'potential_cases_65'] = int(coeff * row['risk'] * df_demo.loc[row['adm_division'], 'Population 65+'])
        df_predictions.at[ix, 'potential_cases_threshold'] = int(coeff * max_thr * df_demo.loc[row['adm_division'], 'Population'])
    if verbose:
        print('VECTOR SUITABILITY AND RISK PREDICTIONS AND POTENTIAL CASES')
        print(df_predictions.head())
    df_predictions.to_csv(predictions_data) # store predictions

if __name__ == "__main__":
    main()


