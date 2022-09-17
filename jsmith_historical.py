import streamlit as st
from datetime import date
import numpy as np
import pandas as pd
import gspread
import jsmith_acquire
import jsmith_prepare

credentials = {
  "type": st.secrets["type"],
  "project_id": st.secrets["project_id"],
  "private_key_id": st.secrets["private_key_id"],
  "private_key" : st.secrets["private_key"],
  "client_email": st.secrets["client_email"],
  "client_id": st.secrets["client_id"],
  "auth_uri": st.secrets["auth_uri"],
  "token_uri": st.secrets["token_uri"],
  "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
  "client_x509_cert_url": st.secrets["client_x509_cert_url"]
}

def prepare_open_cases(open_cases):
    """
    This function will take in a df containing current open cases. It will prepare the given dataframe
    accordingly and convert it to a time series dataframe that has been resampled for a single day.

    Parameters:
        - open_cases: This is a df containing currently open cases

    Returns:
        - prepared_df: This is the prepared time series dataframe that has been resampled for a single day
    """
    #Get today's date
    today = str(date.today())

    #Create temp_dict
    temp_dict = {}

    #Add load_date
    temp_dict['load_date'] = today
    
    #Get total number of open cases
    temp_dict['total_open_cases'] = len(open_cases)

    #Get total number of open cases and number of newly opened cases in Dimmit county
    temp_dict['total_open_dimmit_cases'] = len(open_cases[open_cases['County'] == 'Dimmit'])
    temp_dict['total_new_dimmit_cases'] = len(open_cases[(open_cases['County'] == 'Dimmit') & (open_cases['load_date'] == today)])

    #Get total number of open cases and number of newly opened cases in Maverick county
    temp_dict['total_open_maverick_cases'] = len(open_cases[open_cases['County'] == 'Maverick'])
    temp_dict['total_new_maverick_cases'] = len(open_cases[(open_cases['County'] == 'Maverick') & (open_cases['load_date'] == today)])

    #Get total number of open cases and number of newly opened cases in Zavala county
    temp_dict['total_open_zavala_cases'] = len(open_cases[open_cases['County'] == 'Zavala'])
    temp_dict['total_new_zavala_cases'] = len(open_cases[(open_cases['County'] == 'Zavala') & (open_cases['load_date'] == today)])

    #Get counts of case type per day and per county
    if open_cases['Case Type'][0] == 'Criminal':
        #Since all cases are criminal type for criminal PDF uploads, totals will be the same as above
        #For Dimmit county
        temp_dict['total_open_dimmit_crim_cases'] = temp_dict['total_open_dimmit_cases']
        temp_dict['total_new_dimmit_crim_cases'] = temp_dict['total_new_dimmit_cases']
        #For Maverick county
        temp_dict['total_open_maverick_crim_cases'] = temp_dict['total_open_maverick_cases']
        temp_dict['total_new_maverick_crim_cases'] = temp_dict['total_new_maverick_cases']
        #For Zavala county
        temp_dict['total_open_zavala_crim_cases'] = temp_dict['total_open_zavala_cases']
        temp_dict['total_new_zavala_crim_cases'] = temp_dict['total_new_zavala_cases']
    else:
        #Total counts regardless of county
        temp_dict['total_open_civil_cases'] = len(open_cases[open_cases['Case Type'] == 'Civil'])
        temp_dict['total_new_civil_cases'] = len(open_cases[(open_cases['Case Type'] == 'Civil') & (open_cases['load_date'] == today)])
        temp_dict['total_open_tax_cases'] = len(open_cases[open_cases['Case Type'] == 'Tax'])
        temp_dict['total_new_tax_cases'] = len(open_cases[(open_cases['Case Type'] == 'Tax') & (open_cases['load_date'] == today)])
        temp_dict['total_open_family_cases'] = len(open_cases[open_cases['Case Type'] == 'Family'])
        temp_dict['total_new_family_cases'] = len(open_cases[(open_cases['Case Type'] == 'Family') & (open_cases['load_date'] == today)])
        temp_dict['total_open_juvenile_cases'] = len(open_cases[open_cases['Case Type'] == 'Juvenile'])
        temp_dict['total_new_juvenile_cases'] = len(open_cases[(open_cases['Case Type'] == 'Juvenile') & (open_cases['load_date'] == today)])
        temp_dict['total_open_ols_cases'] = len(open_cases[open_cases['Case Type'] == 'OLS'])
        temp_dict['total_new_ols_cases'] = len(open_cases[(open_cases['Case Type'] == 'OLS') & (open_cases['load_date'] == today)])
        #For Dimmit county
        temp_dict['total_open_dimmit_civil_cases'] = len(open_cases[(open_cases['County'] == 'Dimmit') & (open_cases['Case Type'] == 'Civil')])
        temp_dict['total_new_dimmit_civil_cases'] = len(open_cases[(open_cases['County'] == 'Dimmit') & (open_cases['Case Type'] == 'Civil') & (open_cases['load_date'] == today)])
        temp_dict['total_open_dimmit_tax_cases'] = len(open_cases[(open_cases['County'] == 'Dimmit') & (open_cases['Case Type'] == 'Tax')])
        temp_dict['total_new_dimmit_tax_cases'] = len(open_cases[(open_cases['County'] == 'Dimmit') & (open_cases['Case Type'] == 'Tax') & (open_cases['load_date'] == today)])
        temp_dict['total_open_dimmit_family_cases'] = len(open_cases[(open_cases['County'] == 'Dimmit') & (open_cases['Case Type'] == 'Family')])
        temp_dict['total_new_dimmit_family_cases'] = len(open_cases[(open_cases['County'] == 'Dimmit') & (open_cases['Case Type'] == 'Family') & (open_cases['load_date'] == today)])
        temp_dict['total_open_dimmit_juvenile_cases'] = len(open_cases[(open_cases['County'] == 'Dimmit') & (open_cases['Case Type'] == 'Juvenile')])
        temp_dict['total_new_dimmit_juvenile_cases'] = len(open_cases[(open_cases['County'] == 'Dimmit') & (open_cases['Case Type'] == 'Juvenile') & (open_cases['load_date'] == today)])
        temp_dict['total_open_dimmit_ols_cases'] = len(open_cases[(open_cases['County'] == 'Dimmit') & (open_cases['Case Type'] == 'OLS')])
        temp_dict['total_new_dimmit_ols_cases'] = len(open_cases[(open_cases['County'] == 'Dimmit') & (open_cases['Case Type'] == 'OLS') & (open_cases['load_date'] == today)])
        #For Maverick county
        temp_dict['total_open_maverick_civil_cases'] = len(open_cases[(open_cases['County'] == 'Maverick') & (open_cases['Case Type'] == 'Civil')])
        temp_dict['total_new_maverick_civil_cases'] = len(open_cases[(open_cases['County'] == 'Maverick') & (open_cases['Case Type'] == 'Civil') & (open_cases['load_date'] == today)])
        temp_dict['total_open_maverick_tax_cases'] = len(open_cases[(open_cases['County'] == 'Maverick') & (open_cases['Case Type'] == 'Tax')])
        temp_dict['total_new_maverick_tax_cases'] = len(open_cases[(open_cases['County'] == 'Maverick') & (open_cases['Case Type'] == 'Tax') & (open_cases['load_date'] == today)])
        temp_dict['total_open_maverick_family_cases'] = len(open_cases[(open_cases['County'] == 'Maverick') & (open_cases['Case Type'] == 'Family')])
        temp_dict['total_new_maverick_family_cases'] = len(open_cases[(open_cases['County'] == 'Maverick') & (open_cases['Case Type'] == 'Family') & (open_cases['load_date'] == today)])
        temp_dict['total_open_maverick_juvenile_cases'] = len(open_cases[(open_cases['County'] == 'Maverick') & (open_cases['Case Type'] == 'Juvenile')])
        temp_dict['total_new_maverick_juvenile_cases'] = len(open_cases[(open_cases['County'] == 'Maverick') & (open_cases['Case Type'] == 'Juvenile') & (open_cases['load_date'] == today)])
        temp_dict['total_open_maverick_ols_cases'] = len(open_cases[(open_cases['County'] == 'Maverick') & (open_cases['Case Type'] == 'OLS')])
        temp_dict['total_new_maverick_ols_cases'] = len(open_cases[(open_cases['County'] == 'Maverick') & (open_cases['Case Type'] == 'OLS') & (open_cases['load_date'] == today)])
        #For Zavala county
        temp_dict['total_open_zavala_civil_cases'] = len(open_cases[(open_cases['County'] == 'Zavala') & (open_cases['Case Type'] == 'Civil')])
        temp_dict['total_new_zavala_civil_cases'] = len(open_cases[(open_cases['County'] == 'Zavala') & (open_cases['Case Type'] == 'Civil') & (open_cases['load_date'] == today)])
        temp_dict['total_open_zavala_tax_cases'] = len(open_cases[(open_cases['County'] == 'Zavala') & (open_cases['Case Type'] == 'Tax')])
        temp_dict['total_new_zavala_tax_cases'] = len(open_cases[(open_cases['County'] == 'Zavala') & (open_cases['Case Type'] == 'Tax') & (open_cases['load_date'] == today)])
        temp_dict['total_open_zavala_family_cases'] = len(open_cases[(open_cases['County'] == 'Zavala') & (open_cases['Case Type'] == 'Family')])
        temp_dict['total_new_zavala_family_cases'] = len(open_cases[(open_cases['County'] == 'Zavala') & (open_cases['Case Type'] == 'Family') & (open_cases['load_date'] == today)])
        temp_dict['total_open_zavala_juvenile_cases'] = len(open_cases[(open_cases['County'] == 'Zavala') & (open_cases['Case Type'] == 'Juvenile')])
        temp_dict['total_new_zavala_juvenile_cases'] = len(open_cases[(open_cases['County'] == 'Zavala') & (open_cases['Case Type'] == 'Juvenile') & (open_cases['load_date'] == today)])
        temp_dict['total_open_zavala_ols_cases'] = len(open_cases[(open_cases['County'] == 'Zavala') & (open_cases['Case Type'] == 'OLS')])
        temp_dict['total_new_zavala_ols_cases'] = len(open_cases[(open_cases['County'] == 'Zavala') & (open_cases['Case Type'] == 'OLS') & (open_cases['load_date'] == today)])
        
    #Stop here for testing, then add more data

    #Create the prepared_df dataframe with all the calculated values from above
    prepared_df = pd.DataFrame(temp_dict, index = [0])

    return prepared_df

def prepare_closed_cases(closed_cases):
    """
    This function will take in a df containing newly closed cases. It will prepare the given dataframe
    accordingly and convert it to a time series dataframe that has been resampled for a single day.

    Parameters:
        - closed_cases: This is a df containing newly closed cases

    Returns:
        - prepared_df: This is the prepared time series dataframe that has been resampled for a single day
    """
    #Get today's date
    today = str(date.today())

    #Create temp_dict
    temp_dict = {}

    #Add load_date
    temp_dict['load_date'] = today

    #Get total number of open cases
    temp_dict['total_newly_closed_cases'] = len(closed_cases)

    #Get total number of open cases and number of newly opened cases in Dimmit county
    temp_dict['total_newly_closed_dimmit_cases'] = len(closed_cases[closed_cases['County'] == 'Dimmit'])

    #Get total number of open cases and number of newly opened cases in Maverick county
    temp_dict['total_newly_closed_maverick_cases'] = len(closed_cases[closed_cases['County'] == 'Maverick'])

    #Get total number of open cases and number of newly opened cases in Zavala county
    temp_dict['total_newly_closed_zavala_cases'] = len(closed_cases[closed_cases['County'] == 'Zavala'])

    #For testing, print the closed_cases dataframe and the length
    st.info(closed_cases[0])
    st.info(closed_cases['Case Type'].iloc[0])

    #Get counts of case type per day and per county
    if closed_cases['Case Type'].iloc[0] == 'Criminal':
        #Since all cases are criminal type for criminal PDF uploads, totals will be the same as above
        #For Dimmit county
        temp_dict['total_newly_closed_dimmit_crim_cases'] = temp_dict['total_newly_closed_dimmit_cases']
        #For Maverick county
        temp_dict['total_newly_closed_maverick_crim_cases'] = temp_dict['total_newly_closed_maverick_cases']
        #For Zavala county
        temp_dict['total_newly_closed_zavala_crim_cases'] = temp_dict['total_newly_closed_zavala_cases']
    else:
        #Total counts regardless of county
        temp_dict['total_newly_closed_civil_cases'] = len(closed_cases[closed_cases['Case Type'] == 'Civil'])
        temp_dict['total_newly_closed_tax_cases'] = len(closed_cases[closed_cases['Case Type'] == 'Tax'])
        temp_dict['total_newly_closed_family_cases'] = len(closed_cases[closed_cases['Case Type'] == 'Family'])
        temp_dict['total_newly_closed_juvenile_cases'] = len(closed_cases[closed_cases['Case Type'] == 'Juvenile'])
        temp_dict['total_newly_closed_ols_cases'] = len(closed_cases[closed_cases['Case Type'] == 'OLS'])
        #For Dimmit county
        temp_dict['total_newly_closed_dimmit_civil_cases'] = len(closed_cases[(closed_cases['County'] == 'Dimmit') & (closed_cases['Case Type'] == 'Civil')])
        temp_dict['total_newly_closed_dimmit_tax_cases'] = len(closed_cases[(closed_cases['County'] == 'Dimmit') & (closed_cases['Case Type'] == 'Tax')])
        temp_dict['total_newly_closed_dimmit_family_cases'] = len(closed_cases[(closed_cases['County'] == 'Dimmit') & (closed_cases['Case Type'] == 'Family')])
        temp_dict['total_newly_closed_dimmit_juvenile_cases'] = len(closed_cases[(closed_cases['County'] == 'Dimmit') & (closed_cases['Case Type'] == 'Juvenile')])
        temp_dict['total_newly_closed_dimmit_ols_cases'] = len(closed_cases[(closed_cases['County'] == 'Dimmit') & (closed_cases['Case Type'] == 'OLS')])
        #For Maverick county
        temp_dict['total_newly_closed_maverick_civil_cases'] = len(closed_cases[(closed_cases['County'] == 'Maverick') & (closed_cases['Case Type'] == 'Civil')])
        temp_dict['total_newly_closed_maverick_tax_cases'] = len(closed_cases[(closed_cases['County'] == 'Maverick') & (closed_cases['Case Type'] == 'Tax')])
        temp_dict['total_newly_closed_maverick_family_cases'] = len(closed_cases[(closed_cases['County'] == 'Maverick') & (closed_cases['Case Type'] == 'Family')])
        temp_dict['total_newly_closed_maverick_juvenile_cases'] = len(closed_cases[(closed_cases['County'] == 'Maverick') & (closed_cases['Case Type'] == 'Juvenile')])
        temp_dict['total_newly_closed_maverick_ols_cases'] = len(closed_cases[(closed_cases['County'] == 'Maverick') & (closed_cases['Case Type'] == 'OLS')])
        #For Zavala county
        temp_dict['total_newly_closed_zavala_civil_cases'] = len(closed_cases[(closed_cases['County'] == 'Zavala') & (closed_cases['Case Type'] == 'Civil')])
        temp_dict['total_newly_closed_zavala_tax_cases'] = len(closed_cases[(closed_cases['County'] == 'Zavala') & (closed_cases['Case Type'] == 'Tax')])
        temp_dict['total_newly_closed_zavala_family_cases'] = len(closed_cases[(closed_cases['County'] == 'Zavala') & (closed_cases['Case Type'] == 'Family')])
        temp_dict['total_newly_closed_zavala_juvenile_cases'] = len(closed_cases[(closed_cases['County'] == 'Zavala') & (closed_cases['Case Type'] == 'Juvenile')])
        temp_dict['total_newly_closed_zavala_ols_cases'] = len(closed_cases[(closed_cases['County'] == 'Zavala') & (closed_cases['Case Type'] == 'OLS')])
        
    #Stop here for testing, then add more data

    #Create the prepared_df dataframe with all the calculated values from above
    prepared_df = pd.DataFrame(temp_dict, index = [0])

    return prepared_df


def update_historical_table(current_open_cases, newly_closed_cases):
    """
    This function will take in the current_open_cases and newly_closed_cases dataframes and use them to create new time series dataframes.
    They will then be merged together on the common date time index of 'load_date' and the new time series data for the most recent load date will
    be added to the historical table in google sheets. 

    Parameters:
        - current_open_cases: This is a df containing the currently open cases. Can be criminal or civil.
        - newly_closed_cases: This is a df containing the newly closed cases. Can be criminal or civil.

    Returns:
        - Nothing
    """

    #Prepare the open cases dataframe and turn it into a time series df, resampled for a single day
    prepared_open_cases = prepare_open_cases(current_open_cases)

    #Prepare the closed cases dataframe and turn it into a time series df, resampled for a single day
    prepared_closed_cases = prepare_closed_cases(newly_closed_cases)

    #For testing
    st.info(prepared_open_cases.columns)
    st.info(prepared_closed_cases.columns)

    #Merge the two prepared time series dataframes on the common datetime index 'load_date'
    complete_historical_df = prepared_open_cases.merge(right = prepared_closed_cases, how = 'inner', on = 'load_date')

    #Set up credentials to interact with Google Sheets
    gc = gspread.service_account_from_dict(credentials)
    #Open 'Pending Reports' Google Sheet By Name
    gsheet = gc.open('Pending Reports')
    #Access either civil or criminal historical table tab
    if current_open_cases['Case Type'][0] == 'Criminal':
        historical_sheet = gsheet.worksheet('Criminal Historical Table')
    else:
        historical_sheet = gsheet.worksheet('Civil Historical Table')

    #Find the most recent load_date in google sheets. The load_date should be under the 'A' column in the google sheet
    num_rows = len(list(historical_sheet.col_values(1)))
    most_recent_row = 'A' + str(num_rows)
    next_available_row = 'A' + str(num_rows + 1)

    #Update the google sheet with the complete time series df. It should be a single row with the most recent load_date as the index
    if most_recent_row == 'A0':
        #Sheet is empty so add both columns and values starting at the first row
        historical_sheet.update([complete_historical_df.columns.values.tolist()] + complete_historical_df.values.tolist())
    else:
        #Find the last load_date
        last_load_date = historical_sheet.acell(most_recent_row).value
        #If most recent load_date is today's date, overwrite it. Otherwise, find the first available row and insert there
        if last_load_date == str(date.today()):
            historical_sheet.update(most_recent_row, complete_historical_df.values.tolist())
        else:
            historical_sheet.update(next_available_row, complete_historical_df.values.tolist())

    return