"""
Compute dengue vector suitability from meteorological data.
Author: Jacopo Margutti (jmargutti@redcross.nl)
Date: 22-03-2021
"""
import pandas as pd
import numpy as np


def compute_suitability(data, temperaturesuitability):
    df = pd.read_csv(data)

    # calculate rainfall contribution
    df['rainfall'] = (df['hourlyPrecipRate'] + df['precipitationCal'])/2.
    for ix, row in df.iterrows():
        df.at[ix, 'rain_suit'] = 1. if row['rainfall'] > 300. else row['rainfall']/300.

    # correct temperature NCR
    df = df.rename(columns={'Unnamed: 0': 'adm_division'})
    NCR_index = df[df['adm_division'].isin(['PH133900000', 'PH137400000', 'PH137500000', 'PH137600000'])].index.tolist()
    df.at[NCR_index, 'LST_Day_1km'] = df.loc[NCR_index]['LST_Day_1km'] - 4.

    # calculate temperature suitability
    df_temp = pd.read_csv(temperaturesuitability)
    for ix, row in df.iterrows():
        if not pd.isna(row['LST_Day_1km']):
            index = df_temp['temperature'].sub(row['LST_Day_1km']).abs().idxmin()
            df.at[ix, 'temp_suit_day'] = df_temp.iloc[index]['temperature_suitability']
        else:
            df.at[ix, 'temp_suit_day'] = np.nan
        if not pd.isna(row['LST_Night_1km']):
            index = df_temp['temperature'].sub(row['LST_Night_1km']).abs().idxmin()
            df.at[ix, 'temp_suit_night'] = df_temp.iloc[index]['temperature_suitability']
        else:
            df.at[ix, 'temp_suit_night'] = np.nan
    df['temp_suit'] = df[['temp_suit_day', 'temp_suit_night']].min(axis=1)

    # final suitability score
    df['suitability'] = (df['temp_suit'] + df['rain_suit'])/2.

    df = df.rename(columns={'Unnamed: 0': 'adm_division',
                            'Unnamed: 1': 'year',
                            'Unnamed: 2': 'month'})
    return df
