from codecs import ignore_errors
import streamlit as st
from datetime import date, datetime
import pandas as pd
import gspread
import DEV_acquire
import DEV_prepare

#Set up google sheet name vars
google_sheet_name = 'Pending Reports'
common_sheet_name = 'DEV_Common_Table'
civil_sheet_name = 'DEV_Civil_Cases'
closed_civil_sheet_name = 'DEV_Closed_Civil_Cases'
criminal_sheet_name = 'DEV_Criminal_Cases'
closed_criminal_sheet_name = 'DEV_Closed_Criminal_Cases'
ols_civil_sheet_name = 'DEV_OLS_Civil_Cases'
closed_ols_civil_sheet_name = 'DEV_Closed_OLS_Civil_Cases'
ols_criminal_sheet_name = 'DEV_OLS_Criminal_Cases'
closed_ols_criminal_sheet_name = 'DEV_Closed_OLS_Criminal_Cases'

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

def convert_to_common_table_df(case_df):
    """
    This function takes in a df of cases in their original format and converts them to the same format as the common table.

    Parameters:
        - case_df: The original case dataframe

    Returns:
        - common_table_df: The newly created df in common table format
    """

    #Set up the common df
    dict = {
        "County":[],
        "Cause Number": [],
        "File Date": [],
        "Docket Date": [],
        "Court": [],
        "Cause": [],
        "Docket Type": [],
        "ANS File": [],
        "CR Number": [],
        "Case Type": [],
        "Status": [],
        "Outstanding Warrants": [],
        "ST RPT Column": [],
        "Report Generated Date": [],
        "Original As Of Date": [],
        "Last As Of Date": [],
        "Load DateTime": [],
        "Dropped DateTime": [],
        "Disposed Dates": [],
        "Dispositions": [],
        "Disposed As Of Date": [],
        "Number Of Dispositions": []
    }

    df = pd.DataFrame(dict)

    #Some portion of the criminal and civil cases will be the same. Update those columns first
    df['County'] = case_df['County']
    df['Cause Number'] = case_df['Cause Number']
    df['File Date'] = case_df['File Date']
    df['Docket Date'] = case_df['Docket Date']
    df['Court'] = '293' #Hard Coded for now, but may need to change later
    df['Case Type'] = case_df['Case Type']
    df['Status'] = case_df['Status']
    df['Report Generated Date'] = case_df['Report Generated Date']
    df['Original As Of Date'] = case_df['Original As Of Date']
    df['Last As Of Date'] = case_df['Last As Of Date']
    df['Load DateTime'] = case_df['Load DateTime']
    df['Dropped DateTime'] = '' #These are open cases, so none will have a closed date yet
    if case_df['Status'][0] != 'Disposed':
        df['Disposed Dates'] = ''
        df['Dispositions'] = ''
        df['Disposed As Of Date'] = ''
        df['Number Of Dispositions'] = 0
    else:
        df['Disposed Dates'] = case_df['Disposed Dates']
        df['Dispositions'] = case_df['Dispositions']
        df['Disposed As Of Date'] = case_df['Disposed As Of Date']
        df['Number Of Dispositions'] = case_df['Number Of Dispositions']

    #Determine if cases are criminal, juvenile, or civil. They will have different logic
    if case_df['Case Type'][0].count('Criminal') == 1:
        df['Cause'] = case_df['First Offense']
        df['Outstanding Warrants'] = case_df['Outstanding Warrants']
        df['ST RPT Column'] = case_df['ST RPT Column']
        #The following columns are only available in Civil Reports, so set them to empty strings
        df['Docket Type'] = ''
        df['ANS File'] = ''
        df['CR Number'] = ''
    elif case_df['Case Type'][0].count('Juvenile') == 1:
        df['Cause'] = case_df['Offense']
        #The following columns are not available in Juvenile Reports, so set them to empty strings
        df['Docket Type'] = ''
        df['ANS File'] = ''
        df['CR Number'] = ''
        df['Outstanding Warrants'] = ''
        df['ST RPT Column'] = ''
    else:
        df['Cause'] = case_df['Cause of Action']
        df['Docket Type'] = case_df['Docket Type']
        df['ANS File'] = case_df['ANS File']
        df['CR Number'] = case_df['CR Number']
        #The following columns are only available in Criminal reports, so set them to empty strings
        df['Outstanding Warrants'] = ''
        df['ST RPT Column'] = ''

    return df

def update_spreadsheet(file_name, content):
    """
    This function takes in a list containing the file paths of the PDFs that need to be extracted. It'll loop
    and build civil and criminal case dataframes. Then, it will load the data currently stored in the 'Pending Reports'
    google sheet and turn it into a dataframe. Finally, it will append the dataframes appropriately, drop duplicates,
    and then upload the updated data to the 'Pending Reports' google sheet.
    """
    
    #Extract the PDF data
    df = DEV_acquire.build_dataframe(file_name, content)
    #Prepare the df and add new columns
    df = DEV_prepare.prepare_dataframe(file_name, df)

    #If case type is 'Criminal' or 'Criminal OLS', send to criminal function
    #If report is for disposed cases, send them to disposed case function
    if df['Status'][0].count('Disposed') > 0:
        #Send to disposed cases
        update_disposed_cases(df)
    elif df['Case Type'][0].count('Criminal') > 0:
        #Add to criminal cases tab
        update_criminal_cases(df)
    elif df['Case Type'][0].count('Juvenile') > 0:
        #Add juvenile cases to common table
        update_juvenile_cases(df)
    else:
        #Add to civil cases tab
        update_civil_cases(df)
    
    return
    
def update_civil_cases(new_civil_df):
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
    gsheet = gc.open(google_sheet_name)

    #Make connection to 'DEV_Common_Table'
    common_sheet = gsheet.worksheet(common_sheet_name)
    
    if new_civil_df['Case Type'][0].count('OLS') > 0:
        #Send OLS data to the 'Civil OLS Cases' tab
        civil_sheet = gsheet.worksheet(ols_civil_sheet_name)
        #Send closed OLS cases to the 'Closed Civil OLS Cases' tab
        closed_sheet = gsheet.worksheet(closed_ols_civil_sheet_name)
    else:
        #Civil cases go to the 'Civil Cases' tab
        civil_sheet = gsheet.worksheet(civil_sheet_name)
        #Closed cases go to the 'Closed Civil Cases' tab
        closed_sheet = gsheet.worksheet(closed_civil_sheet_name)

    #Load the data currently on the civil cases tab in the 'Pending Reports' spreadsheet
    current_civil_df = pd.DataFrame(civil_sheet.get_all_records())

    #Load the data currently on the common table in the 'Pending Reports' spreadsheet
    common_table_df = pd.DataFrame(common_sheet.get_all_records())

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
        closed_cases_df = DEV_prepare.prepare_closed_cases(closed_cases_df, new_civil_df)
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
    else:
        #Instanciate closed_cases_df
        closed_cases_df = pd.DataFrame()

    #Update the 'Original As Of Date' for the new cases df
    if len(current_civil_df) > 0:
        #Create a df that consists only of pending cases in the county for the current report
        current_county_pending_cases = current_civil_df[current_civil_df['County'] == new_civil_df['County'][0]]
        current_county_pending_cases.reset_index(inplace = True)
        #Iterate through each of those cases and update the corresponding version in new_civil_df
        for i in current_county_pending_cases.index:
            new_civil_df.loc[new_civil_df['Cause Number'] == current_county_pending_cases['Cause Number'][i], ['Original As Of Date']] = current_county_pending_cases['Original As Of Date'][i]

    #Append new_civil_df to current_civil_df
    current_civil_df = current_civil_df.append(new_civil_df, ignore_index = True)

    #Verify that all Cause Numbers are represented as strings
    current_civil_df['Cause Number'] = current_civil_df['Cause Number'].astype(str).str.strip()
    
    if len(common_table_df) > 0:
        common_table_df['Cause Number'] = common_table_df['Cause Number'].astype(str).str.strip()

    #Drop duplicate cases while keeping the most recent version
    current_civil_df = current_civil_df.drop_duplicates(subset = ['Cause Number'], ignore_index = True, keep = 'last')

    #Clear what's currently on the Civil Cases worksheet
    civil_sheet.clear()

    #Now upload to Civil Cases worksheet in 'Pending Reports' spreadsheet and leave a message
    civil_sheet.update([current_civil_df.columns.values.tolist()] + current_civil_df.values.tolist())

    #Now append the current_civil_df to the common_table_df, remove duplicates, and update the closed cases
    #Drop duplicates based on cause number and status since cases have the potential to be reopened.
    common_table_df = common_table_df.append(convert_to_common_table_df(current_civil_df), ignore_index = True)
    common_table_df = common_table_df.drop_duplicates(subset = ['Cause Number', 'Status'], ignore_index = True, keep = 'last')

    if len(closed_cases_df) > 0:
        #Reset index
        closed_cases_df.reset_index(inplace = True)
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Dropped DateTime']] = closed_cases_df['Dropped DateTime'][0]
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Report Generated Date']] = closed_cases_df['Report Generated Date'][0]
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Last As Of Date']] = closed_cases_df['Last As Of Date'][0]
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Load DateTime']] = closed_cases_df['Load DateTime'][0]
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Status']] = closed_cases_df['Status'][0]

    #Finally upload the common_table_df to the common table worksheet in 'Pending Reports' spreadsheet
    common_sheet.clear()
    common_sheet.update([common_table_df.columns.values.tolist()] + common_table_df.values.tolist())
    
    print('Civil Cases Updated!')

    return

def update_criminal_cases(new_crim_df):
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
    gsheet = gc.open(google_sheet_name)

    #Make connection to 'DEV_Common_Table'
    common_sheet = gsheet.worksheet(common_sheet_name)

    if new_crim_df['Case Type'][0].count('OLS') > 0:
        #Send OLS data to the 'Criminal OLS Cases' tab
        crim_sheet = gsheet.worksheet(ols_criminal_sheet_name)
        #Send closed OLS cases to the 'Closed Criminal OLS Cases' tab
        closed_sheet = gsheet.worksheet(closed_ols_criminal_sheet_name)
    else:
        #Civil cases go to the 'Criminal Cases' tab
        crim_sheet = gsheet.worksheet(criminal_sheet_name)
        #Closed cases go to the 'Closed Criminal Cases' tab
        closed_sheet = gsheet.worksheet(closed_criminal_sheet_name)

    #Load the data currently on the criminal cases tab in the 'Pending Reports' spreadsheet
    current_crim_df = pd.DataFrame(crim_sheet.get_all_records())

    #Load the data currently on the common table in the 'Pending Reports' spreadsheet
    common_table_df = pd.DataFrame(common_sheet.get_all_records())

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
        closed_cases_df = DEV_prepare.prepare_closed_cases(closed_cases_df, new_crim_df)
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
    else:
        #Instanciate closed_cases_df
        closed_cases_df = pd.DataFrame()

    #Update the 'Original As Of Date' for the new cases df
    if len(current_crim_df) > 0:
        #Create a df that consists only of pending cases in the county for the current report
        current_county_pending_cases = current_crim_df[current_crim_df['County'] == new_crim_df['County'][0]]
        current_county_pending_cases.reset_index(inplace = True)
        #Iterate through each of those cases and update the corresponding version in new_crim_df
        for i in current_county_pending_cases.index:
            new_crim_df.loc[new_crim_df['Cause Number'] == current_county_pending_cases['Cause Number'][i], ['Original As Of Date']] = current_county_pending_cases['Original As Of Date'][i]

    #Append new_crim_df to current_crim_df
    current_crim_df = current_crim_df.append(new_crim_df, ignore_index = True)

    #Verify that all Cause Numbers are represented as strings
    current_crim_df['Cause Number'] = current_crim_df['Cause Number'].astype(str).str.strip()

    if len(common_table_df) > 0:
        common_table_df['Cause Number'] = common_table_df['Cause Number'].astype(str).str.strip()

    #Drop duplicate cases while keeping the most recent version
    current_crim_df = current_crim_df.drop_duplicates(subset = ['Cause Number'], ignore_index = True, keep = 'last')

    #Clear what's currently on the Criminal Cases worksheet
    crim_sheet.clear()

    #Now upload to Criminal Cases worksheet in 'Pending Reports' spreadsheet and leave a message
    crim_sheet.update([current_crim_df.columns.values.tolist()] + current_crim_df.values.tolist())

    #Now append the current_ccrim_df to the common_table_df, remove duplicates, and update the closed cases
    #Drop duplicates based on cause number and status since cases have the potential to be reopened.
    common_table_df = common_table_df.append(convert_to_common_table_df(current_crim_df), ignore_index = True)
    common_table_df = common_table_df.drop_duplicates(subset = ['Cause Number', 'Status'], ignore_index = True, keep = 'last')
    
    if len(closed_cases_df) > 0:
        #Reset index
        closed_cases_df.reset_index(inplace = True)
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Dropped DateTime']] = closed_cases_df['Dropped DateTime'][0]
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Report Generated Date']] = closed_cases_df['Report Generated Date'][0]
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Last As Of Date']] = closed_cases_df['Last As Of Date'][0]
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Load DateTime']] = closed_cases_df['Load DateTime'][0]
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Status']] = closed_cases_df['Status'][0]

    #Finally upload the common_table_df to the common table worksheet in 'Pending Reports' spreadsheet
    common_sheet.clear()
    common_sheet.update([common_table_df.columns.values.tolist()] + common_table_df.values.tolist())
    
    print('Criminal Cases Updated!')

    return

def update_disposed_cases(disposed_cases):
    """
    This function takes in the disposed cases df and updates it with the current data on the 'Pending Reports' spreadsheet.
    It will update the appropriate dropped cases tables as well as the common table.
    
    Parameter:
        - disposed_cases: The newly created dataframe from the most recent disposed cases PDF report

    Returns:
        - Nothing.
    """

    #Set up credentials to interact with Google Sheets
    gc = gspread.service_account_from_dict(credentials)
    
    #Open 'Pending Reports' Google Sheet By Name
    gsheet = gc.open(google_sheet_name)

    #Make connection to 'DEV_Common_Table'
    common_sheet = gsheet.worksheet(common_sheet_name)

    #Open the associated dropped table
    if disposed_cases['Case Type'][0].count('Criminal') > 0:
        dropped_sheet = gsheet.worksheet(closed_criminal_sheet_name)
        is_crim = True
    else:
        dropped_sheet = gsheet.worksheet(closed_civil_sheet_name)
        is_crim = False
    
    #Build dataframes
    dropped_cases = pd.DataFrame(dropped_sheet.get_all_records())
    common_table_df = pd.DataFrame(common_sheet.get_all_records())

    #Verify cause numbers are represented as strings
    if len(dropped_cases) > 0:
        dropped_cases['Cause Number'] = dropped_cases['Cause Number'].astype(str).str.strip()
    if len(common_table_df) > 0:
        common_table_df['Cause Number'] = common_table_df['Cause Number'].astype(str).str.strip()

    #Find the cases that are not in the dropped cases df
    #These cases will need to be added into the closed and common table because we don't have data this old
    #These disposed cases can go back as far as 01/01/2019
    if len(dropped_cases) > 0:
        old_disposed_cases = disposed_cases[~(disposed_cases['Cause Number'].isin(dropped_cases['Cause Number']))]
        old_disposed_cases.reset_index(inplace = True)
    else:
        old_disposed_cases = disposed_cases

    #Find the cases that are already in the dropped cases df, but not yet labeled as disposed
    #Since these are already in the dropped table, we only need to update a few of the columns
    if len(dropped_cases) > 0:
        new_disposed_cases = disposed_cases[disposed_cases['Cause Number'].isin(dropped_cases[dropped_cases['Status'] == 'Dropped']['Cause Number'])]
        new_disposed_cases.reset_index(inplace = True)
    else:
        new_disposed_cases = pd.DataFrame()


    #Iterate through each of those cases and update the corresponding version
    if is_crim:
        old_disposed_cases['File Date'] = ''
        old_disposed_cases['Court'] = '293'
        old_disposed_cases['Docket Date'] = ''
        old_disposed_cases['Outstanding Warrants'] = ''
        old_disposed_cases['First Offense'] = ''
        old_disposed_cases['ST RPT Column'] = ''
        old_disposed_cases['Report Generated Date'] = ''
        old_disposed_cases['Original As Of Date'] = old_disposed_cases['Disposed As Of Date']
        old_disposed_cases['Last As Of Date'] = old_disposed_cases['Disposed As Of Date']
        old_disposed_cases['Dropped DateTime'] = ''
        #Correct the order of the columns
        old_disposed_cases = old_disposed_cases[[
            'County',
            'Cause Number',
            'File Date',
            'Court',
            'Docket Date',
            'Outstanding Warrants',
            'First Offense',
            'ST RPT Column',
            'Report Generated Date',
            'Original As Of Date',
            'Last As Of Date',
            'Case Type',
            'Status',
            'Load DateTime',
            'Dropped DateTime',
            'Disposed Dates',
            'Dispositions',
            'Disposed As Of Date',
            'Number Of Dispositions'
        ]]

        #Now append to dropped cases df
        dropped_cases = dropped_cases.append(old_disposed_cases, ignore_index = True)
    else:
        old_disposed_cases['Cause of Action'] = ''
        old_disposed_cases['Docket Date'] = ''
        old_disposed_cases['Docket Type'] = ''
        old_disposed_cases['ANS File'] = ''
        old_disposed_cases['CR Number'] = ''
        old_disposed_cases['Report Generated Date'] = ''
        old_disposed_cases['Original As Of Date'] = old_disposed_cases['Disposed As Of Date']
        old_disposed_cases['Last As Of Date'] = old_disposed_cases['Disposed As Of Date']
        old_disposed_cases['Dropped DateTime'] = ''
        #Correct the order of the columns
        old_disposed_cases = old_disposed_cases[[
            'County',
            'Cause Number',
            'File Date',
            'Cause of Action',
            'Docket Date',
            'Docket Type',
            'ANS File',
            'CR Number',
            'Report Generated Date',
            'Original As Of Date',
            'Last As Of Date',
            'Case Type',
            'Status',
            'Load DateTime',
            'Dropped DateTime',
            'Disposed Dates',
            'Dispositions',
            'Disposed As Of Date',
            'Number Of Dispositions'
        ]]

        #Now append to dropped cases df
        dropped_cases = dropped_cases.append(old_disposed_cases, ignore_index = True)

    #Now append the old cases df to the common_table_df
    if len(old_disposed_cases) > 0:
        if len(common_table_df) > 0:
            common_table_df = common_table_df.append(convert_to_common_table_df(old_disposed_cases), ignore_index = True)
        else:
            common_table_df = convert_to_common_table_df(old_disposed_cases)

    #Some cases may have reopened and been disposed again. This will have caused two entries in each table.
    #One entry labeled as 'Dropped' (the reopened version), and one entry labeled 'Disposed' (the original version)
    #Since the disposed report should now contain the disposed dates for the reopened version, we can drop the original version
    #and simply update the reopened version with the new disposed information.
    new_disposed_cases.sort_values(by = ['County', 'Cause Number', 'Status'], ignore_index=True, inplace=True)
    new_disposed_cases.drop_duplicates(subset = ['Cause Number'], ignore_index=True, inplace=True, keep='last')
    common_table_df.sort_values(by = ['County','Cause Number','Status'], ignore_index=True, inplace=True)
    common_table_df.drop_duplicates(subset = ['Cause Number'], ignore_index=True, inplace=True, keep='last')

    #Iterate through each of the newly disposed cases and update the corresponding version in dropped_cases
    if len(new_disposed_cases) > 0:
        for i in new_disposed_cases.index:
            dropped_cases.loc[dropped_cases['Cause Number'] == new_disposed_cases['Cause Number'][i], ['Status']] = new_disposed_cases['Status'][i]
            dropped_cases.loc[dropped_cases['Cause Number'] == new_disposed_cases['Cause Number'][i], ['Disposed Dates']] = new_disposed_cases['Disposed Dates'][i]
            dropped_cases.loc[dropped_cases['Cause Number'] == new_disposed_cases['Cause Number'][i], ['Dispositions']] = new_disposed_cases['Dispositions'][i]
            dropped_cases.loc[dropped_cases['Cause Number'] == new_disposed_cases['Cause Number'][i], ['Disposed As Of Date']] = new_disposed_cases['Disposed As Of Date'][i]
            dropped_cases.loc[dropped_cases['Cause Number'] == new_disposed_cases['Cause Number'][i], ['Number Of Dispositions']] = new_disposed_cases['Number Of Dispositions'][i]
    
    #Iterate through each of the newly disposed cases and update the corresponding version in the common table
    if len(common_table_df) > 0:
        for i in new_disposed_cases.index:
            common_table_df.loc[common_table_df['Cause Number'] == new_disposed_cases['Cause Number'][i], ['Status']] = new_disposed_cases['Status'][i]
            common_table_df.loc[common_table_df['Cause Number'] == new_disposed_cases['Cause Number'][i], ['Disposed Dates']] = new_disposed_cases['Disposed Dates'][i]
            common_table_df.loc[common_table_df['Cause Number'] == new_disposed_cases['Cause Number'][i], ['Dispositions']] = new_disposed_cases['Dispositions'][i]
            common_table_df.loc[common_table_df['Cause Number'] == new_disposed_cases['Cause Number'][i], ['Disposed As Of Date']] = new_disposed_cases['Disposed As Of Date'][i]
            common_table_df.loc[common_table_df['Cause Number'] == new_disposed_cases['Cause Number'][i], ['Number Of Dispositions']] = new_disposed_cases['Number Of Dispositions'][i]

    #Now update the google sheet
    #For common table
    common_sheet.clear()
    common_sheet.update([common_table_df.columns.values.tolist()] + common_table_df.values.tolist())

    #For dropped cases table
    dropped_sheet.clear()
    dropped_sheet.update([dropped_cases.columns.values.tolist()] + dropped_cases.values.tolist())

    return
    
def update_juvenile_cases(juvenile_cases):
    """
    This function takes in the juvenile cases df and updates it with the current data on the 'Pending Reports' spreadsheet.
    It will only update the common table.

    Parameter:
    - juvenile_cases: The newly created dataframe from the most recent juvenile cases PDF report

    Returns:
    - Nothing.
    """

    #Set up credentials to interact with Google Sheets
    gc = gspread.service_account_from_dict(credentials)
    
    #Open 'Pending Reports' Google Sheet By Name
    gsheet = gc.open(google_sheet_name)

    #Make connection to 'DEV_Common_Table'
    common_sheet = gsheet.worksheet(common_sheet_name)

    #Build common table df
    common_table_df = pd.DataFrame(common_sheet.get_all_records())

    #Find the new juvenile cases (not already in the common table)
    new_juvenile_cases = juvenile_cases[~(juvenile_cases['Cause Number'].isin(common_table_df['Cause Number']))]
    new_juvenile_cases.reset_index(inplace = True)

    #Find the existing juvenile cases (already in the common table)
    existing_juvenile_cases = juvenile_cases[juvenile_cases['Cause Number'].isin(common_table_df['Cause Number'])]
    existing_juvenile_cases.reset_index(inplace = True)

    if len(common_table_df) > 0:
        #Verify that cause numbers are represented as strings
        common_table_df['Cause Number'] = common_table_df['Cause Number'].astype(str).str.strip()

        #Create a df that consists only of pending juvenile cases in the county for the current report
        current_county_cases = common_table_df[common_table_df['County'] == juvenile_cases['County'][0]]
        current_county_cases = current_county_cases[current_county_cases['Case Type'] == 'Juvenile']
        current_county_pending_cases = current_county_cases[current_county_cases['Status'] == 'Open']
        current_county_pending_cases.reset_index(inplace = True)
        #Update the 'Original As Of Date' for the new cases df
        for i in current_county_pending_cases.index:
            juvenile_cases.loc[juvenile_cases['Cause Number'] == current_county_pending_cases['Cause Number'][i], ['Original As Of Date']] = current_county_pending_cases['Original As Of Date'][i]

        #Update dropped cases in common table
        dropped_cases = current_county_pending_cases[~(current_county_pending_cases['Cause Number'].isin(juvenile_cases['Cause Number']))]
        dropped_cases.reset_index(inplace = True)

        if len(dropped_cases) > 0:
            #Set the dropped datetime column to the uploaded report's 'As Of' date
            date = juvenile_cases['Last As Of Date'][0].strip()
            time = '00:00:00'
            datetime_str = date + ' ' + time

            datetime_object = datetime.strptime(datetime_str, '%m/%d/%Y %H:%M:%S')

            for i in dropped_cases.index:
                common_table_df.loc[common_table_df['Cause Number'] == dropped_cases['Cause Number'][i], ['Status']] = 'Dropped'
                common_table_df.loc[common_table_df['Cause Number'] == dropped_cases['Cause Number'][i], ['Dropped DateTime']] = datetime_object
                common_table_df.loc[common_table_df['Cause Number'] == dropped_cases['Cause Number'][i], ['Report Generated Date']] = dropped_cases['Report Generated Date'][i]
                common_table_df.loc[common_table_df['Cause Number'] == dropped_cases['Cause Number'][i], ['Last As Of Date']] = dropped_cases['Last As Of Date'][i]
                common_table_df.loc[common_table_df['Cause Number'] == dropped_cases['Cause Number'][i], ['Load DateTime']] = dropped_cases['Load DateTime'][i]

    #Now append the juvenile_cases dataframe to the common_table_df, and remove duplicates
    #Drop duplicates based on cause number and status since cases have the potential to be reopened.
    common_table_df = common_table_df.append(convert_to_common_table_df(juvenile_cases), ignore_index = True)
    common_table_df = common_table_df.drop_duplicates(subset = ['Cause Number', 'Status'], ignore_index = True, keep = 'last')

    #Finally upload the common_table_df to the common table worksheet in 'Pending Reports' spreadsheet
    common_sheet.clear()
    common_sheet.update([common_table_df.columns.values.tolist()] + common_table_df.values.tolist())
    
    print('Juvenile Cases Updated!')