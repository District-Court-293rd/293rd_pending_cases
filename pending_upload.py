import streamlit as st
import numpy as np
import pandas as pd
import gspread
import jsmith_acquire
import jsmith_prepare
import jsmith_historical

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

def convert_to_bool(value):
    """
    This function takes in a string. The string could be "TRUE", "FALSE", or empty. This funciton will replace the given string
    with the appropriate boolean value. This is necessary because the boolean values read in from the google spreadsheet is 
    represented as a string. So when that value is uploaded back to the spreadsheet, the data validation doesn't recognize it
    and flags the value. This should fix that problem.

    Parameter:
        - value: "TRUE", "FALSE", or nothing

    Returns:
        - boolean: The appropriate boolean value for the given string. If the given string is empty, it will return an empty string
    """

    #Use an if else statement to assign the proper boolean values
    if value == "TRUE" or value == True:
        return True
    elif value == "FALSE" or value == False:
        return False
    else:
        return ''

def find_next_available_row(worksheet):
    """
    This function takes in a google spreadsheet and finds the first available row. It will return a string representing the first
    empty cell in the first column.

    Parameter:
        - worksheet: The google sheet you wish to find the first available row for

    Returns:
        - str: The first available cell in the first row. Represented in A1 format
    """
    #Count the number of unavailable rows
    num_unavailable_rows = len(list(worksheet.col_values(1)))

    #Add one and create the string
    first_available_row = 'A' + str(num_unavailable_rows + 1)

    return first_available_row

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
    else:
        #Add to civil cases tab
        update_civil_cases_dataframe(df)
    
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

    #Closed cases go to the 'Closed Civil Cases' tab
    closed_sheet = gsheet.worksheet('Closed Civil Cases')

    #Load the data currently on the civil cases tab in the 'Pending Reports' spreadsheet
    current_civil_df = pd.DataFrame(civil_sheet.get_all_records())

    #Before appending the new cases, create the closed cases df and udpate the closed cases tab
    if len(current_civil_df) > 0:
        #First, Verify that all Cause Numbers are represented as strings
        new_civil_df['Cause Number'] = new_civil_df['Cause Number'].astype(str).str.strip()
        current_civil_df['Cause Number'] = current_civil_df['Cause Number'].astype(str).str.strip()
        #Create closed cases df
        closed_cases_df = current_civil_df[~(current_civil_df['Cause Number'].isin(new_civil_df['Cause Number']))]
        #Make sure the closed cases are only cases from the same county as the new_civil_df
        closed_cases_df = closed_cases_df[closed_cases_df['County'] == new_civil_df['County'][0]]
        #Remove closed cases from current_civil_df
        current_civil_df = current_civil_df[~(current_civil_df['Cause Number'].isin(closed_cases_df['Cause Number']))]
        #Prepare closed cases df
        closed_cases_df = jsmith_prepare.prepare_closed_cases(closed_cases_df)
        #Find next available row
        next_available_row = find_next_available_row(closed_sheet)
        #If any cases were closed, add the newly closed cases to the 'Closed Civil Cases' tab
        if len(closed_cases_df) > 0:
            #If the first available row is the first row in the sheet, include the column names when updating
            #Otherwise, only send the values
            if next_available_row == 'A1':
                closed_sheet.update([closed_cases_df.columns.values.tolist()] + closed_cases_df.values.tolist())
            else:
                closed_sheet.update(next_available_row, closed_cases_df.values.tolist())


    #Append new_civil_df to current_civil_df
    current_civil_df = current_civil_df.append(new_civil_df, ignore_index = True)

    #Verify that all Cause Numbers are represented as strings
    current_civil_df['Cause Number'] = current_civil_df['Cause Number'].astype(str).str.strip()

    #Convert the google boolean values for the 'On Track' column to python booleans
    current_civil_df['On Track'] = current_civil_df['On Track'].apply(convert_to_bool)

    #Convert the google boolean values for the 'On Track' column to python booleans
    current_civil_df['Bad Cause Number'] = current_civil_df['Bad Cause Number'].apply(convert_to_bool)

    #Stage 1 - Drop Duplicates for subset ['Cause Number', 'Docket Date'] while keeping first
    current_civil_df = current_civil_df.drop_duplicates(subset = ['Cause Number', 'Docket Date'], ignore_index = True, keep = 'first')

    #Stage 2 - Drop Duplicates for subset ['Cause Number'] while keeping last
    current_civil_df = current_civil_df.drop_duplicates(subset = ['Cause Number'], ignore_index = True, keep = 'last')

    #Now sort by county and then by cause number
    current_civil_df = current_civil_df.sort_values(by = ['County', 'Cause Number'], ignore_index = True)

    #Update the 'Months Ahead or Behind' column
    current_civil_df['Months Ahead Or Behind'] = current_civil_df['Docket Date'].apply(jsmith_prepare.get_months_ahead_or_behind)

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

    #Closed cases go to the 'Closed Criminal Cases' tab
    closed_sheet = gsheet.worksheet('Closed Criminal Cases')

    #Load the data currently on the criminal cases tab in the 'Pending Reports' spreadsheet
    current_crim_df = pd.DataFrame(crim_sheet.get_all_records())

    #Before appending the new cases, create the closed cases df and udpate the closed cases tab
    if len(current_crim_df) > 0:
        #First, Verify that all Cause Numbers are represented as strings
        new_crim_df['Cause Number'] = new_crim_df['Cause Number'].astype(str).str.strip()
        current_crim_df['Cause Number'] = current_crim_df['Cause Number'].astype(str).str.strip()
        #Create closed cases df
        closed_cases_df = current_crim_df[~(current_crim_df['Cause Number'].isin(new_crim_df['Cause Number']))]
        #Make sure the closed cases are only cases from the same county as the new_crim_df
        closed_cases_df = closed_cases_df[closed_cases_df['County'] == new_crim_df['County'][0]]
        #Remove closed cases from current_crim_df
        current_crim_df = current_crim_df[~(current_crim_df['Cause Number'].isin(closed_cases_df['Cause Number']))]
        #Prepare closed cases df
        closed_cases_df = jsmith_prepare.prepare_closed_cases(closed_cases_df)
        #Find the next available row
        next_available_row = find_next_available_row(closed_sheet)
        #If any cases were closed, add the newly closed cases to the 'Closed Criminal Cases' tab
        if len(closed_cases_df) > 0:
            #If the first available row is the first row in the sheet, include the column names when updating
            #Otherwise, only send the values
            if next_available_row == 'A1':
                closed_sheet.update([closed_cases_df.columns.values.tolist()] + closed_cases_df.values.tolist())
            else:
                closed_sheet.update(next_available_row, closed_cases_df.values.tolist())

    #Append new_crim_df to current_crim_df
    current_crim_df = current_crim_df.append(new_crim_df, ignore_index = True)

    #Verify that all Cause Numbers are represented as strings
    current_crim_df['Cause Number'] = current_crim_df['Cause Number'].astype(str).str.strip()

    #Convert the google boolean values for the 'On Track' column to python booleans
    current_crim_df['On Track'] = current_crim_df['On Track'].apply(convert_to_bool)

    #Convert the google boolean values for the 'Bad Cause Number' column to python booleans
    current_crim_df['Bad Cause Number'] = current_crim_df['Bad Cause Number'].apply(convert_to_bool)

    #Stage 1 - Drop Duplicates for subset ['Cause Number', 'Docket Date'] while keeping first
    current_crim_df = current_crim_df.drop_duplicates(subset = ['Cause Number', 'Docket Date'], ignore_index = True, keep = 'first')

    #Stage 2 - Drop Duplicates for subset ['Cause Number'] while keeping last
    current_crim_df = current_crim_df.drop_duplicates(subset = ['Cause Number'], ignore_index = True, keep = 'last')

    #Now sort by county and then by cause number
    current_crim_df = current_crim_df.sort_values(by = ['County', 'Cause Number'], ignore_index = True)

    #Update the 'Months Ahead or Behind' column
    current_crim_df['Months Ahead Or Behind'] = current_crim_df['Docket Date'].apply(jsmith_prepare.get_months_ahead_or_behind)

    #Clear what's currently on the Criminal Cases worksheet
    crim_sheet.clear()

    #Now upload to Criminal Cases worksheet in 'Pending Reports' spreadsheet and leave a message
    crim_sheet.update([current_crim_df.columns.values.tolist()] + current_crim_df.values.tolist())
    print('Criminal Cases Updated!')

    return
