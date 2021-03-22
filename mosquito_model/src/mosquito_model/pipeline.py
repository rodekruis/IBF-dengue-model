import pandas as pd
from mosquito_model.get_data import get_data
from mosquito_model.compute_zonalstats import compute_zonalstats
from mosquito_model.compute_risk import compute_suitability
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
@click.option('--geecredentials', default='credentials/era-service-account-credentials.json',
              help='Google Earth Engine credentials')
@click.option('--admincode', default='ADM2_EN', help='which feature in vector file')
@click.option('--data', default='input', help='input data directory')
@click.option('--dest', default='output', help='output data directory')
@click.option('--predictstart', default=datetime.date.today().strftime("%Y-%m-%d"),
              help='start predictions from date (%Y-%m-%d)')
@click.option('--predictend', default=None, help='end predictions on date (%Y-%m-%d)')
@click.option('--storeraster', is_flag=True, help='store raster data')
def main(countrycode, vector, temperaturesuitability, geecredentials, admincode, data, dest, predictstart, predictend,
         storeraster):

    # initialize GEE
    with open(geecredentials) as f:
        credentials_dict = json.load(f)
        service_account = credentials_dict['client_email']
        credentials = ee.ServiceAccountCredentials(service_account, geecredentials)
        ee.Initialize(credentials)

    # define administrative divisions
    gdf = gpd.read_file(vector)
    adm_divisions = gdf[admincode].unique()

    # define date range
    start_date = datetime.datetime.strptime(predictstart, '%Y-%m-%d') - relativedelta(months=+3)
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
            df_stats = compute_zonalstats(raster_data, vector, 'ADM2_EN').reset_index()
            # save zonal statistics in dataframe for processed data
            for ix, row in df_stats.iterrows():
                df_data_processed.at[(row['adm_division'], start_date.year, start_date.month), data_tuple[1]] = row['mean']
        # remove raster data
        if not storeraster:
            shutil.rmtree(Path(raster_data).parent)

    df_data_processed.rename_axis(index=['adm_division', 'year', 'month'], inplace=True)
    print(df_data_processed.head())
    df_data_processed.to_csv(processed_data)

    # compute suitability
    df = compute_suitability(processed_data, temperaturesuitability)
    print(df.head())

    # add two months ahead to the dates in the dataframe
    df['date'] = df['year'].astype(str) + '-' + df['month'].astype(str) + '-15'
    df['date'] = pd.to_datetime(df['date'])  # convert to datetime
    df_ = df.append(pd.Series({'date': max(df['date']) + datetime.timedelta(30)}), ignore_index=True)  # one month
    df_ = df_.append(pd.Series({'date': max(df['date']) + datetime.timedelta(60)}), ignore_index=True)  # two months
    dfdates = df_.groupby('date').sum().reset_index()
    dfdates['year'] = dfdates['date'].dt.year
    dfdates['month'] = dfdates['date'].dt.month
    dfdates = dfdates[['year', 'month']]
    # remove first three months (no data to predict)
    dfdates = dfdates[3:]

    # initialize dataframe for predictions
    df_predictions = pd.DataFrame()
    for adm_division in adm_divisions:
        for year, month in zip(dfdates.year.values, dfdates.month.values):
            df_predictions = df_predictions.append(pd.Series(name=(adm_division, year, month), dtype='object'))

    # calculate predictions
    for admin_division in adm_divisions:
        df_admin_div = df[df.adm_division == admin_division]
        for year, month in zip(dfdates.year.values, dfdates.month.values):
            date_prediction = datetime.datetime.strptime(f'{year}-{month}-15', '%Y-%m-%d')
            dates_input = [date_prediction - datetime.timedelta(90),
                          date_prediction - datetime.timedelta(60),
                          date_prediction - datetime.timedelta(30)]
            weights_input = [0.16, 0.68, 0.16]
            risk_total, weight_total = 0., 0.
            for date_input, weight_input in zip(dates_input, weights_input):
                month_input = date_input.month
                year_input = date_input.year
                df_input = df_admin_div[(df_admin_div.month == month_input) & (df_admin_div.year == year_input)]
                if not df_input.empty:
                    risk_total += weight_input * df_input.iloc[0]['suitability']
                    weight_total += weight_input

            risk_total = risk_total / weight_total
            df_predictions.at[(admin_division, year, month), 'risk'] = risk_total

    df_predictions.rename_axis(index=['adm_division', 'year', 'month'], inplace=True)
    print(df_predictions.head())
    df_predictions.to_csv(predictions_data)


if __name__ == "__main__":
    main()


