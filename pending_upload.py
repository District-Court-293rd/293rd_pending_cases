import streamlit as st
import numpy as np
import pandas as pd
import gspread
#from oauth2client.service_account import ServiceAccountCredentials
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

def update_spreadsheet(file_name, content):
    """
    This function takes in a list containing the file paths of the PDFs that need to be extracted. It'll loop
    and build civil and criminal case dataframes. Then, it will load the data currently stored in the 'Pending Reports'
    google sheet and turn it into a dataframe. Finally, it will append the dataframes appropriately, drop duplicates,
    and then upload the updated data to the 'Pending Reports' google sheet.
    """
    
    #Extract the PDF data
    df = jsmith_acquire.build_dataframe(file_name, content)
    #Prepare the df and add new columns
    df = jsmith_prepare.prepare_dataframe(file_name, df)

    if df['Case Type'][0] == 'Criminal':
        #Add to criminal cases tab
        update_criminal_cases_dataframe(df)

    elif df['Case Type'][0] == 'Civil' or df['Case Type'][0] == 'Tax':
        #Add to civil cases tab
        update_civil_cases_dataframe(df)

    else:
        print('Something went wrong in the loop!')
        
    return
    
def update_civil_cases_dataframe(new_civil_df):
    """
    This function takes in the newly created civil cases df and updates it with the current data on the 'Pending Reports' spreadsheet.
    It will connect to the Google Sheet, load the current data, append the new data to the current data, and drop duplicates without 
    losing previous work. Finally, it will upload the updated dataframe to the Civil Cases sheet of the 'Pending Reports' spreadsheet.
    
    Parameter:
        - new_civil_df: The newly created dataframe from the most recent civil cases PDF data

    Returns:
        - Nothing.
    """

    #Set up credentials to interact with Google Sheets
    gc = gspread.service_account_from_dict(credentials)
    
    #Open 'Pending Reports' Google Sheet By Name
    gsheet = gc.open('Pending Reports')
    
    #Civil cases go to the 'Civil Cases' tab
    civil_sheet = gsheet.worksheet('test_civil_cases')

    #Load the data currently on the civil cases tab in the 'Pending Reports' spreadsheet
    current_civil_df = pd.DataFrame(civil_sheet.get_all_records())

    #Append new_civil_df to current_civil_df
    current_civil_df = current_civil_df.append(new_civil_df, ignore_index = True)

    #Verify that all Cause Numbers are represented as strings
    current_civil_df['Cause Number'] = current_civil_df['Cause Number'].astype(str)

    #Stage 1 - Drop Duplicates for subset ['Cause Number', 'Docket Date'] while keeping first
    current_civil_df = current_civil_df.drop_duplicates(subset = ['Cause Number', 'Docket Date'], ignore_index = True, keep = 'first')

    #Stage 2 - Drop Duplicates for subset ['Cause Number'] while keeping last
    current_civil_df = current_civil_df.drop_duplicates(subset = ['Cause Number'], ignore_index = True, keep = 'last')

    #Now sort by county and then by cause number
    current_civil_df = current_civil_df.sort_values(by = ['County', 'Cause Number'], ignore_index = True)

    #Clear what's currently on the Civil Cases worksheet
    civil_sheet.clear()

    #Now upload to Civil Cases worksheet in 'Pending Reports' spreadsheet and leave a message
    civil_sheet.update([current_civil_df.columns.values.tolist()] + current_civil_df.values.tolist())
    print('Civil Cases Updated!')

    return

def update_criminal_cases_dataframe(new_crim_df):
    """
    This function takes in the newly created criminal cases df and updates it with the current data on the 'Pending Reports' spreadsheet.
    It will connect to the Google Sheet, load the current data, append the new data to the current data, and drop duplicates without 
    losing previous work. Finally, it will upload the updated dataframe to the Criminal Cases sheet of the 'Pending Reports' spreadsheet.
    
    Parameter:
        - new_criminal_df: The newly created dataframe from the most recent criminal cases PDF data

    Returns:
        - Nothing.
    """

    #Set up credentials to interact with Google Sheets
    gc = gspread.service_account_from_dict(credentials)
    
    #Open 'Pending Reports' Google Sheet By Name
    gsheet = gc.open("Pending Reports")

    #Criminal cases go to the 'Criminal Cases' tab
    crim_sheet = gsheet.worksheet('test_criminal_cases')

    #Load the data currently on the criminal cases tab in the 'Pending Reports' spreadsheet
    current_crim_df = pd.DataFrame(crim_sheet.get_all_records())

    #Append new_crim_df to current_crim_df
    current_crim_df = current_crim_df.append(new_crim_df, ignore_index = True)

    #Verify that all Cause Numbers are represented as strings
    current_crim_df['Cause Number'] = current_crim_df['Cause Number'].astype(str)

    #Stage 1 - Drop Duplicates for subset ['Cause Number', 'Docket Date'] while keeping first
    current_crim_df = current_crim_df.drop_duplicates(subset = ['Cause Number', 'Docket Date'], ignore_index = True, keep = 'first')

    #Stage 2 - Drop Duplicates for subset ['Cause Number'] while keeping last
    current_crim_df = current_crim_df.drop_duplicates(subset = ['Cause Number'], ignore_index = True, keep = 'last')

    #Now sort by county and then by cause number
    current_crim_df = current_crim_df.sort_values(by = ['County', 'Cause Number'], ignore_index = True)

    #Clear what's currently on the Criminal Cases worksheet
    crim_sheet.clear()

    #Now upload to Criminal Cases worksheet in 'Pending Reports' spreadsheet and leave a message
    crim_sheet.update([current_crim_df.columns.values.tolist()] + current_crim_df.values.tolist())
    print('Criminal Cases Updated!')

    return
