"""
Compute dengue risk from vector suitability.
Author: Jacopo Margutti (jmargutti@redcross.nl)
Date: 22-03-2021
"""
import pandas as pd
import numpy as np
import datetime
from dateutil import relativedelta


def compute_risk(df, adm_divisions, num_months_ahead=3):

    # add N months ahead to the dates in the dataframe
    df['date'] = df['year'].astype(str) + '-' + df['month'].astype(str) + '-15'
    df['date'] = pd.to_datetime(df['date'])  # convert to datetime
    df_ = df.copy()
    for n in range(num_months_ahead):
        df_ = df_.append(pd.Series({'date': max(df['date']) + relativedelta.relativedelta(months=(n+1))}), ignore_index=True)
    dfdates = df_.groupby('date').sum().reset_index()
    dfdates['year'] = dfdates['date'].dt.year
    dfdates['month'] = dfdates['date'].dt.month
    dfdates = dfdates[['year', 'month']]
    # remove first three months (no data to predict)
    dfdates = dfdates[3:]

    # initialize dataframe for risk predictions
    df_predictions = pd.DataFrame()
    for adm_division in adm_divisions:
        for year, month in zip(dfdates.year.values, dfdates.month.values):
            df_predictions = df_predictions.append(pd.Series(name=(adm_division, year, month), dtype='object'))

    # loop over admin divisions anc calculate risk
    for admin_division in adm_divisions:
        df_admin_div = df[df.adm_division == admin_division]
        for year, month in zip(dfdates.year.values, dfdates.month.values):
            # store suitability
            df_suitability = df_admin_div[(df_admin_div.month == month) & (df_admin_div.year == year)]
            if not df_suitability.empty:
                df_predictions.at[(admin_division, year, month), 'suitability'] = df_suitability.iloc[0]['suitability']
            # calculate risk
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
            # store risk
            df_predictions.at[(admin_division, year, month), 'risk'] = risk_total

    df_predictions.rename_axis(index=['adm_division', 'year', 'month'], inplace=True)
    df_predictions.reset_index(inplace=True)
    return df_predictions
