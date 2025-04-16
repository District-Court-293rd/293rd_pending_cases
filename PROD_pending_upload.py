from codecs import ignore_errors
import streamlit as st
from datetime import date, datetime
import pandas as pd
import gspread
import PROD_acquire
import PROD_prepare

#Set up google sheet name vars
google_sheet_name = 'Pending Reports'
common_sheet_name = 'Common Table'
civil_sheet_name = 'Civil Cases'
closed_civil_sheet_name = 'Closed Civil Cases'
criminal_sheet_name = 'Criminal Cases'
closed_criminal_sheet_name = 'Closed Criminal Cases'
juvenile_sheet_name = 'Juvenile Cases'
closed_juvenile_sheet_name = 'Closed Juvenile Cases'
ols_civil_sheet_name = 'OLS Civil Cases'
closed_ols_civil_sheet_name = 'Closed OLS Civil Cases'
ols_criminal_sheet_name = 'OLS Criminal Cases'
closed_ols_criminal_sheet_name = 'Closed OLS Criminal Cases'
criminal_inactive_sheet_name = 'Inactive Criminal Cases'
civil_inactive_sheet_name = 'Inactive Civil Cases'
report_tracker_sheet_name = 'Report Tracker'

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
        "Number Of Dispositions": []#,
        #Comment column removed as of 10/07/2023
        #"Comments": []
    }

    df = pd.DataFrame(dict)

    #Some portion of the criminal, civil, and juvenile cases will be the same. Update those columns first
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
    #Comment column removed as of 10/07/2023
    #df['Comments'] = case_df['Comments']
    if case_df['Status'].iloc[0] != 'Disposed':
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
    if case_df['Case Type'].iloc[0].count('Criminal') == 1:
        df['Cause'] = case_df['First Offense']
        df['Outstanding Warrants'] = case_df['Outstanding Warrants']
        df['ST RPT Column'] = case_df['ST RPT Column']
        #The following columns are only available in Civil Reports, so set them to empty strings
        df['Docket Type'] = ''
        df['ANS File'] = ''
        df['CR Number'] = ''
    elif case_df['Case Type'].iloc[0].count('Juvenile') == 1:
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

def update_report_tracker(report):
    """
    This function will update the report tracker tab with the 'As Of Date' of the report just uploaded.
    This allows us to keep track of the which reports were uploaded last and if any still need to be uploaded
    before continuing with a future date.
    """
    #Set up credentials to interact with Google Sheets
    gc = gspread.service_account_from_dict(credentials)
    
    #Open 'Pending Reports' Google Sheet By Name
    gsheet = gc.open(google_sheet_name)

    #Make connection to 'DEV_Report_Tracker'
    report_tracker_sheet = gsheet.worksheet(report_tracker_sheet_name)

    #Load the data currently on the report tracker tab in the 'Pending Reports' spreadsheet
    report_tracker_df = pd.DataFrame(report_tracker_sheet.get_all_records())

    #Verify the columns are string types. Google sheets can mess with the data types
    report_tracker_df['County'] = report_tracker_df['County'].astype(str).str.strip()
    report_tracker_df['Report Type'] = report_tracker_df['Report Type'].astype(str).str.strip()

    #Update the df with the new report date and load datetime
    report_tracker_df.loc[(report_tracker_df['County'] == report['County']) & (report_tracker_df['Report Type'] == report['Report Type']), ['Report Date']] = report['As Of Date']
    report_tracker_df.loc[(report_tracker_df['County'] == report['County']) & (report_tracker_df['Report Type'] == report['Report Type']), ['Load DateTime']] = report['Load DateTime']

    #Finally upload the common_table_df to the common table worksheet in 'Pending Reports' spreadsheet
    report_tracker_sheet.clear()
    report_tracker_df.sort_values(by = ['County','Report Type'], ignore_index=True, inplace=True)
    report_tracker_sheet.update([report_tracker_df.columns.values.tolist()] + report_tracker_df.values.tolist())



def update_spreadsheet(report):
    """
    This function takes in a list containing the file paths of the PDFs that need to be extracted. It'll loop
    and build civil and criminal case dataframes. Then, it will load the data currently stored in the 'Pending Reports'
    google sheet and turn it into a dataframe. Finally, it will append the dataframes appropriately, drop duplicates,
    and then upload the updated data to the 'Pending Reports' google sheet.
    """
    
    #Extract the PDF data
    df = PROD_acquire.build_dataframe(report['Report Type'], report['Content'])

    #The juvenile case reports are different than the others, so will need separate string of logic
    #The inactive cases will also need a separate string of logic
    if report['Report Type'] == 'Juvenile':
        #Separate juvenile cases into pending and disposed df's
        pending_juvenile_cases = df[df["Disposed Dates"].str.len() == 0]
        disposed_juvenile_cases = df[df["Disposed Dates"].str.len() > 0]

        #Prepare pending and disposed juvenile cases df's
        pending_juvenile_cases = PROD_prepare.prepare_pending_juvenile_cases(pending_juvenile_cases)
        disposed_juvenile_cases = PROD_prepare.prepare_disposed_juvenile_cases(disposed_juvenile_cases)
        #Update pending and disposed juvenile cases in google sheet
        update_juvenile_cases(pending_juvenile_cases, disposed_juvenile_cases)
    elif report['Report Type'] == 'Criminal Inactive':
        #Update the inactive spreadsheet.
        PROD_prepare.prepare_inactive_cases(df)
        update_criminal_inactive_cases(df, report)
    elif report['Report Type'] == 'Civil Inactive':
        #Update the inactive spreadsheet.
        PROD_prepare.prepare_inactive_cases(df)
        update_civil_inactive_cases(df, report)
    else:
        #Prepare the df and add new columns
        df = PROD_prepare.prepare_dataframe(report['Report Type'], df)
        #If case type is 'Criminal' or 'Criminal OLS', send to criminal function
        #If report is for disposed cases, send them to disposed case function
        if report['Report Type'] == 'Criminal Disposed' or report['Report Type'] == 'Civil Disposed':
            #Send to disposed cases
            update_disposed_cases(df)
        elif report['Report Type'] == 'Criminal':
            #Add to criminal cases tab
            update_criminal_cases(df)
        else:
            #Add to civil cases tab
            update_civil_cases(df)
    
    #Update the report tracker tab
    update_report_tracker(report)
    
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

    #Make connection to 'PROD_Common_Table'
    common_sheet = gsheet.worksheet(common_sheet_name)
    
    if new_civil_df['Case Type'].iloc[0].count('OLS') > 0:
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
        closed_cases_df = closed_cases_df[closed_cases_df['County'] == new_civil_df['County'].iloc[0]]
        #Remove closed cases from current_civil_df
        current_civil_df = current_civil_df[~(current_civil_df['Cause Number'].isin(closed_cases_df['Cause Number']))]
        #Prepare closed cases df
        closed_cases_df = PROD_prepare.prepare_closed_cases(closed_cases_df, new_civil_df)
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

    #Update the 'Original As Of Date' and 'Comments' columns for the new cases df
    if len(current_civil_df) > 0:
        #Create a df that consists only of pending cases in the county for the current report
        current_county_pending_cases = current_civil_df[current_civil_df['County'] == new_civil_df['County'].iloc[0]]
        current_county_pending_cases.reset_index(inplace = True)
        #Iterate through each of those cases and update the corresponding version in new_civil_df
        for i in current_county_pending_cases.index:
            new_civil_df.loc[new_civil_df['Cause Number'] == current_county_pending_cases['Cause Number'].iloc[i], ['Original As Of Date']] = current_county_pending_cases['Original As Of Date'].iloc[i]
            #Check for an updated docket date. If docket date has changed and is not blank, append the old ones to the new one.
            new_docket_date = str(new_civil_df[new_civil_df['Cause Number'] == current_county_pending_cases['Cause Number'].iloc[i]]['Docket Date'].reset_index(drop=True)[0]).strip()
            current_docket_dates = str(current_county_pending_cases['Docket Date'].iloc[i]).strip()

            if len(new_docket_date) > 0 and new_docket_date.isspace() == False and current_docket_dates.find(new_docket_date) == -1:
                new_civil_df.loc[new_civil_df['Cause Number'] == current_county_pending_cases['Cause Number'].iloc[i], ['Docket Date']] = new_docket_date + '\n' + current_docket_dates
            else:
                new_civil_df.loc[new_civil_df['Cause Number'] == current_county_pending_cases['Cause Number'].iloc[i], ['Docket Date']] = current_docket_dates

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

    #Now upload to Civil Cases worksheet in 'Pending Reports' spreadsheet
    civil_sheet.update([current_civil_df.columns.values.tolist()] + current_civil_df.values.tolist())

    #Now append the current_civil_df to the common_table_df, remove duplicates, and update the closed cases
    #Drop duplicates based on cause number and status since cases have the potential to be reopened.
    common_table_df = common_table_df.append(convert_to_common_table_df(current_civil_df), ignore_index = True)
    common_table_df = common_table_df.drop_duplicates(subset = ['Cause Number', 'Status'], ignore_index = True, keep = 'last')

    if len(closed_cases_df) > 0:
        #Reset index
        closed_cases_df.reset_index(inplace = True)
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Dropped DateTime']] = closed_cases_df['Dropped DateTime'].iloc[0]
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Report Generated Date']] = closed_cases_df['Report Generated Date'].iloc[0]
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Last As Of Date']] = closed_cases_df['Last As Of Date'].iloc[0]
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Load DateTime']] = closed_cases_df['Load DateTime'].iloc[0]
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Status']] = closed_cases_df['Status'].iloc[0]

    #Finally upload the common_table_df to the common table worksheet in 'Pending Reports' spreadsheet
    common_sheet.clear()
    common_table_df.sort_values(by = ['Status'], ignore_index=True, inplace=True, ascending = False)
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

    #Make connection to 'PROD_Common_Table'
    common_sheet = gsheet.worksheet(common_sheet_name)

    if new_crim_df['Case Type'].iloc[0].count('OLS') > 0:
        #Send OLS data to the 'Criminal OLS Cases' tab
        crim_sheet = gsheet.worksheet(ols_criminal_sheet_name)
        #Send closed OLS cases to the 'Closed Criminal OLS Cases' tab
        closed_sheet = gsheet.worksheet(closed_ols_criminal_sheet_name)
    else:
        #Criminal cases go to the 'Criminal Cases' tab
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
        closed_cases_df = closed_cases_df[closed_cases_df['County'] == new_crim_df['County'].iloc[0]]
        #Remove closed cases from current_crim_df
        current_crim_df = current_crim_df[~(current_crim_df['Cause Number'].isin(closed_cases_df['Cause Number']))]
        #Prepare closed cases df
        closed_cases_df = PROD_prepare.prepare_closed_cases(closed_cases_df, new_crim_df)
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

    #Update the 'Original As Of Date' and 'Comments' columns for the new cases df
    if len(current_crim_df) > 0:
        #Create a df that consists only of pending cases in the county for the current report
        current_county_pending_cases = current_crim_df[current_crim_df['County'] == new_crim_df['County'].iloc[0]]
        current_county_pending_cases.reset_index(inplace = True)
        #Iterate through each of those cases and update the corresponding version in new_crim_df
        for i in current_county_pending_cases.index:
            new_crim_df.loc[new_crim_df['Cause Number'] == current_county_pending_cases['Cause Number'].iloc[i], ['Original As Of Date']] = current_county_pending_cases['Original As Of Date'].iloc[i]
            #Check for an updated docket date. If docket date has changed and is not blank, append the old ones to the new one.
            #Have to reset the index of the resulting series so that I can select the individual value at index = 0
            new_docket_date = str(new_crim_df[new_crim_df['Cause Number'] == current_county_pending_cases['Cause Number'].iloc[i]]['Docket Date'].reset_index(drop=True)[0]).strip()
            current_docket_dates = str(current_county_pending_cases['Docket Date'].iloc[i]).strip()

            if len(new_docket_date) > 0 and new_docket_date.isspace() == False and current_docket_dates.find(new_docket_date) == -1:
                new_crim_df.loc[new_crim_df['Cause Number'] == current_county_pending_cases['Cause Number'].iloc[i], ['Docket Date']] = new_docket_date + '\n' + current_docket_dates
            else:
                new_crim_df.loc[new_crim_df['Cause Number'] == current_county_pending_cases['Cause Number'].iloc[i], ['Docket Date']] = current_docket_dates

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

    #Now append the current_crim_df to the common_table_df, remove duplicates, and update the closed cases
    #Drop duplicates based on cause number and status since cases have the potential to be reopened.
    common_table_df = common_table_df.append(convert_to_common_table_df(current_crim_df), ignore_index = True)
    common_table_df = common_table_df.drop_duplicates(subset = ['Cause Number', 'Status'], ignore_index = True, keep = 'last')
    
    if len(closed_cases_df) > 0:
        #Reset index
        closed_cases_df.reset_index(inplace = True)
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Dropped DateTime']] = closed_cases_df['Dropped DateTime'].iloc[0]
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Report Generated Date']] = closed_cases_df['Report Generated Date'].iloc[0]
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Last As Of Date']] = closed_cases_df['Last As Of Date'].iloc[0]
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Load DateTime']] = closed_cases_df['Load DateTime'].iloc[0]
        common_table_df.loc[(common_table_df['Cause Number'].isin(closed_cases_df['Cause Number'])) & (common_table_df['Status'] == 'Open'), ['Status']] = closed_cases_df['Status'].iloc[0]

    #Finally upload the common_table_df to the common table worksheet in 'Pending Reports' spreadsheet
    common_sheet.clear()
    common_table_df.sort_values(by = ['Status'], ignore_index=True, inplace=True, ascending = False)
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

    #Make connection to 'PROD_Common_Table'
    common_sheet = gsheet.worksheet(common_sheet_name)

    #Open the associated dropped table
    if disposed_cases['Case Type'].iloc[0].count('Criminal') > 0:
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
        #Comment column removed as of 10/07/2023
        #old_disposed_cases['Comments'] = ''

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
            'Number Of Dispositions'#,
            #'Comments'
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
        #Comment column removed as of 10/07/2023
        #old_disposed_cases['Comments'] = ''

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
            'Number Of Dispositions'#,
            #'Comments'
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

    #First, separate the open cases from the dropped and disposed cases
    open_common_table_cases = common_table_df[common_table_df['Status'] == 'Open']
    closed_common_table_cases = common_table_df[common_table_df['Status'] != 'Open']

    #Now drop the disposed version of the case.
    closed_common_table_cases.sort_values(by = ['County','Cause Number','Status'], ignore_index=True, inplace=True)
    closed_common_table_cases.drop_duplicates(subset = ['Cause Number'], ignore_index=True, inplace=True, keep='last')

    #Finally, recreate the common_table_df by adding the open cases back to the closed_common_table_cases df
    common_table_df = closed_common_table_cases.append(open_common_table_cases, ignore_index = True)

    #Iterate through each of the newly disposed cases and update the corresponding version in dropped_cases
    if len(new_disposed_cases) > 0:
        for i in new_disposed_cases.index:
            dropped_cases.loc[dropped_cases['Cause Number'] == new_disposed_cases['Cause Number'].iloc[i], ['Status']] = new_disposed_cases['Status'].iloc[i]
            dropped_cases.loc[dropped_cases['Cause Number'] == new_disposed_cases['Cause Number'].iloc[i], ['Disposed Dates']] = new_disposed_cases['Disposed Dates'].iloc[i]
            dropped_cases.loc[dropped_cases['Cause Number'] == new_disposed_cases['Cause Number'].iloc[i], ['Dispositions']] = new_disposed_cases['Dispositions'].iloc[i]
            dropped_cases.loc[dropped_cases['Cause Number'] == new_disposed_cases['Cause Number'].iloc[i], ['Disposed As Of Date']] = new_disposed_cases['Disposed As Of Date'].iloc[i]
            dropped_cases.loc[dropped_cases['Cause Number'] == new_disposed_cases['Cause Number'].iloc[i], ['Number Of Dispositions']] = new_disposed_cases['Number Of Dispositions'].iloc[i]
    
    #Iterate through each of the newly disposed cases and update the corresponding version in the common table
    if len(common_table_df) > 0:
        for i in new_disposed_cases.index:
            common_table_df.loc[common_table_df['Cause Number'] == new_disposed_cases['Cause Number'].iloc[i], ['Status']] = new_disposed_cases['Status'].iloc[i]
            common_table_df.loc[common_table_df['Cause Number'] == new_disposed_cases['Cause Number'].iloc[i], ['Disposed Dates']] = new_disposed_cases['Disposed Dates'].iloc[i]
            common_table_df.loc[common_table_df['Cause Number'] == new_disposed_cases['Cause Number'].iloc[i], ['Dispositions']] = new_disposed_cases['Dispositions'].iloc[i]
            common_table_df.loc[common_table_df['Cause Number'] == new_disposed_cases['Cause Number'].iloc[i], ['Disposed As Of Date']] = new_disposed_cases['Disposed As Of Date'].iloc[i]
            common_table_df.loc[common_table_df['Cause Number'] == new_disposed_cases['Cause Number'].iloc[i], ['Number Of Dispositions']] = new_disposed_cases['Number Of Dispositions'].iloc[i]

    #Now update the google sheet
    #For common table
    common_sheet.clear()
    common_table_df.sort_values(by = ['Status'], ignore_index=True, inplace=True, ascending = False)
    common_sheet.update([common_table_df.columns.values.tolist()] + common_table_df.values.tolist())

    #For dropped cases table
    dropped_sheet.clear()
    dropped_sheet.update([dropped_cases.columns.values.tolist()] + dropped_cases.values.tolist())

    return
    
def update_juvenile_cases(pending_juvenile_cases, disposed_juvenile_cases):
    """
    This function takes in the juvenile cases dataframes (both pending and disposed) and updates it with the current data on the 'Pending Reports' spreadsheet.
    It will update the open juvenile cases table, the disposed juvenile cases table, and then finally the common table.

    Parameter:
    - pending_juvenile_cases: The newly created dataframe from the most recent juvenile cases PDF report (pending cases only)
    - disposed_juvenile_cases: The newly created dataframe from the most recent juvenile cases PDF report (disposed cases only)

    Returns:
    - Nothing.
    """

    #Set up credentials to interact with Google Sheets
    gc = gspread.service_account_from_dict(credentials)
    
    #Open 'Pending Reports' Google Sheet By Name
    gsheet = gc.open(google_sheet_name)

    #Make connection to 'PROD_Common_Table'
    common_sheet = gsheet.worksheet(common_sheet_name)
    pending_juvenile_sheet = gsheet.worksheet(juvenile_sheet_name)
    disposed_juvenile_sheet = gsheet.worksheet(closed_juvenile_sheet_name)

    #Build dataframes from existing tables
    common_table_df = pd.DataFrame(common_sheet.get_all_records())
    pending_juvenile_cases_table_df = pd.DataFrame(pending_juvenile_sheet.get_all_records())
    disposed_juvenile_cases_table_df = pd.DataFrame(disposed_juvenile_sheet.get_all_records())

    #Are the tables empty? Default to True
    is_common_table_empty = True
    is_pending_juvenile_table_empty = True
    is_disposed_juvenile_table_empty = True 

    if len(common_table_df) > 0:
        is_common_table_empty = False
    if len(pending_juvenile_cases_table_df) > 0:
        is_pending_juvenile_table_empty = False
    if len(disposed_juvenile_cases_table_df) > 0:
        is_disposed_juvenile_table_empty = False 

    #Verify that cause numbers are represented as strings
    if is_common_table_empty == False:
        common_table_df['Cause Number'] = common_table_df['Cause Number'].astype(str).str.strip()
    if is_pending_juvenile_table_empty == False:
        pending_juvenile_cases_table_df['Cause Number'] = pending_juvenile_cases_table_df['Cause Number'].astype(str).str.strip()
    if is_disposed_juvenile_table_empty == False:
        disposed_juvenile_cases_table_df['Cause Number'] = disposed_juvenile_cases_table_df['Cause Number'].astype(str).str.strip()

    #First, find which cases (if any) have been dropped since last upload
    #If a case was previously listed as pending, but cannot be found in either the newly created pending or disposed cases dataframes,
    #it will be considered dropped (but not disposed).
    if is_pending_juvenile_table_empty == False:
        dropped_cases = pending_juvenile_cases_table_df[~(pending_juvenile_cases_table_df['Cause Number'].isin(pending_juvenile_cases['Cause Number']))]
        dropped_cases = dropped_cases[~(dropped_cases['Cause Number'].isin(disposed_juvenile_cases['Cause Number']))]
    else:
        dropped_cases = pd.DataFrame()

    #Update the 'Original As Of Date' column for the new pending and disposed juvenile cases dataframes
    if is_pending_juvenile_table_empty == False:
        #Create a temporary reference table to iterate through both the pending and disposed cases. That way we know we have all the cause numbers included in one dataframe
        ref_table = pending_juvenile_cases[['Cause Number', 'Status']].append(disposed_juvenile_cases[['Cause Number', 'Original As Of Date', 'Docket Date', 'Status']], ignore_index = True)
        ref_table = ref_table[ref_table['Cause Number'].isin(pending_juvenile_cases_table_df['Cause Number'])]
        #If there are any dropped cases, remove them from the pending juvenile cases table df for the next part:
        if len(dropped_cases) > 0:
            pending_juvenile_cases_table_df = pending_juvenile_cases_table_df[~(pending_juvenile_cases_table_df['Cause Number'].isin(dropped_cases['Cause Number']))].reset_index(drop=True)

        for i in pending_juvenile_cases_table_df.index:
            #Use reference table to determine if the pending or the disposed dataframe needs to be updated. Then update
            if ref_table[ref_table['Cause Number'] == pending_juvenile_cases_table_df['Cause Number'].iloc[i]]['Status'].reset_index(drop=True)[0] == 'Open':
                pending_juvenile_cases.loc[pending_juvenile_cases['Cause Number'] == pending_juvenile_cases_table_df['Cause Number'].iloc[i], ['Original As Of Date']] = pending_juvenile_cases_table_df['Original As Of Date'].iloc[i]
                #Check for an updated docket date. If docket date has changed and is not blank, append the old ones to the new one.
                new_docket_date = str(pending_juvenile_cases[pending_juvenile_cases['Cause Number'] == pending_juvenile_cases_table_df['Cause Number'].iloc[i]]['Docket Date'].reset_index(drop=True)[0]).strip()
                current_docket_dates = str(pending_juvenile_cases_table_df['Docket Date'].iloc[i]).strip()

                if len(new_docket_date) > 0 and new_docket_date.isspace() == False and current_docket_dates.find(new_docket_date) == -1:
                    pending_juvenile_cases.loc[pending_juvenile_cases['Cause Number'] == pending_juvenile_cases_table_df['Cause Number'].iloc[i], ['Docket Date']] = new_docket_date + '\n' + current_docket_dates
                else:
                    pending_juvenile_cases.loc[pending_juvenile_cases['Cause Number'] == pending_juvenile_cases_table_df['Cause Number'].iloc[i], ['Docket Date']] = current_docket_dates
            else:
                disposed_juvenile_cases.loc[disposed_juvenile_cases['Cause Number'] == pending_juvenile_cases_table_df['Cause Number'].iloc[i], ['Original As Of Date']] = pending_juvenile_cases_table_df['Original As Of Date'].iloc[i]
                #Check for an updated docket date. If docket date has changed and is not blank, append the old ones to the new one.
                new_docket_date = str(disposed_juvenile_cases[disposed_juvenile_cases['Cause Number'] == pending_juvenile_cases_table_df['Cause Number'].iloc[i]]['Docket Date'].reset_index(drop=True)[0]).strip()
                current_docket_dates = str(pending_juvenile_cases_table_df['Docket Date'].iloc[i]).strip()

                if len(new_docket_date) > 0 and new_docket_date.isspace() == False and current_docket_dates.find(new_docket_date) == -1:
                    disposed_juvenile_cases.loc[disposed_juvenile_cases['Cause Number'] == pending_juvenile_cases_table_df['Cause Number'].iloc[i], ['Docket Date']] = new_docket_date + '\n' + current_docket_dates
                else:
                    disposed_juvenile_cases.loc[disposed_juvenile_cases['Cause Number'] == pending_juvenile_cases_table_df['Cause Number'].iloc[i], ['Docket Date']] = current_docket_dates

    #Now update the pending juvenile cases table
    #I can simply clear the entire table and add the new pending juvenile cases df because all county cases are included in each report
    pending_juvenile_sheet.clear()
    pending_juvenile_sheet.update([pending_juvenile_cases.columns.values.tolist()] + pending_juvenile_cases.values.tolist())

    #Update the disposed juvenile cases dataframe with the 'Original As Of Date' values from the disposed juvenile cases table dataframe.
    #This allows us to account for cases that have been reopened and closed again
    if is_disposed_juvenile_table_empty == False:
        #Find any previously dropped cases and add them to the disposed cases dataframe
        previously_dropped_cases = disposed_juvenile_cases_table_df[disposed_juvenile_cases_table_df['Status'] == 'Dropped']
        disposed_juvenile_cases = disposed_juvenile_cases.append(previously_dropped_cases, ignore_index = True)

        #Now remove the dropped cases from the disposed_juvenile_cases_table_df.
        #Running the for loop below without this step is likely causing issues with key errors where index = 0.
        disposed_juvenile_cases_table_df = disposed_juvenile_cases_table_df[disposed_juvenile_cases_table_df['Status'] != 'Dropped']

        for i in disposed_juvenile_cases_table_df.index:
            disposed_juvenile_cases.loc[disposed_juvenile_cases['Cause Number'] == disposed_juvenile_cases_table_df['Cause Number'].iloc[i], ['Original As Of Date']] = disposed_juvenile_cases_table_df['Original As Of Date'].iloc[i]
            disposed_juvenile_cases.loc[disposed_juvenile_cases['Cause Number'] == disposed_juvenile_cases_table_df['Cause Number'].iloc[i], ['Dropped DateTime']] = disposed_juvenile_cases_table_df['Dropped DateTime'].iloc[i]
            #Check for an updated docket date. If docket date has changed and is not blank, append the old ones to the new one.
            new_docket_date = str(disposed_juvenile_cases[disposed_juvenile_cases['Cause Number'] == disposed_juvenile_cases_table_df['Cause Number'].iloc[i]]['Docket Date'].reset_index(drop=True)[0]).strip()
            current_docket_dates = str(disposed_juvenile_cases_table_df['Docket Date'].iloc[i]).strip()

            if len(new_docket_date) > 0 and new_docket_date.isspace() == False and current_docket_dates.find(new_docket_date) == -1:
                disposed_juvenile_cases.loc[disposed_juvenile_cases['Cause Number'] == disposed_juvenile_cases_table_df['Cause Number'].iloc[i], ['Docket Date']] = new_docket_date + '\n' + current_docket_dates
            else:
                disposed_juvenile_cases.loc[disposed_juvenile_cases['Cause Number'] == disposed_juvenile_cases_table_df['Cause Number'].iloc[i], ['Docket Date']] = current_docket_dates
        

    #Now update the closed juvenile cases table
    #If there are newly dropped cases, prepare them and add to the disposed cases dataframe
    if len(dropped_cases) > 0:
            dropped_cases = PROD_prepare.prepare_dropped_juvenile_cases(dropped_cases, pending_juvenile_cases['Last As Of Date'].iloc[0])
            disposed_juvenile_cases = disposed_juvenile_cases.append(dropped_cases, ignore_index = True)
    
    #I chose to clear the entire sheet and add all currently disposed cases again because this accounts for any cases that were reopened and closed again.
    #We will have the most up to date information for each case.
    disposed_juvenile_sheet.clear()
    disposed_juvenile_sheet.update([disposed_juvenile_cases.columns.values.tolist()] + disposed_juvenile_cases.values.tolist())

    #Now update the common table
    #Append the pending juvenile cases df to the common_table_df, remove duplicates, and update the closed cases
    #Drop duplicates based on cause number and status since cases have the potential to be reopened.
    common_table_df = common_table_df.append(convert_to_common_table_df(pending_juvenile_cases), ignore_index = True)
    common_table_df = common_table_df.drop_duplicates(subset = ['Cause Number', 'Status'], ignore_index = True, keep = 'last')

    #Determine which dropped and disposed cases don't already exist in the common table.
    #These should only exist the first time we run the juvenile report
    disposed_cases_not_in_common_table = disposed_juvenile_cases[~(disposed_juvenile_cases['Cause Number'].isin(common_table_df['Cause Number']))]
    #Convert these to the common table dataframe format and append them
    #Must separate the dropped and disposed cases because the convert_to_common_table_df function can't update both at the same time
    if len(disposed_cases_not_in_common_table[disposed_cases_not_in_common_table['Status'] == 'Disposed']) > 0:
        common_table_df = common_table_df.append(convert_to_common_table_df(disposed_cases_not_in_common_table[disposed_cases_not_in_common_table['Status'] == 'Disposed']), ignore_index = True)
    if len(disposed_cases_not_in_common_table[disposed_cases_not_in_common_table['Status'] == 'Dropped']) > 0:
        common_table_df = common_table_df.append(convert_to_common_table_df(disposed_cases_not_in_common_table[disposed_cases_not_in_common_table['Status'] == 'Dropped']), ignore_index = True)
    
    if is_common_table_empty == False:
        #Reset index, iterate through the disposed juvenile cases, and update the newly dropped/disposed cases in the common table
        #I do not believe this will account for cases that were reopened and closed again. I need more info on how the report will behave in those instances before I can code for it.
        disposed_juvenile_cases.reset_index(inplace = True)
        for i in disposed_juvenile_cases.index:
            common_table_df.loc[(common_table_df['Cause Number'] == (disposed_juvenile_cases['Cause Number'].iloc[i])) & (common_table_df['Status'] == 'Open'), ['Dropped DateTime']] = disposed_juvenile_cases['Dropped DateTime'].iloc[i]
            common_table_df.loc[(common_table_df['Cause Number'] == (disposed_juvenile_cases['Cause Number'].iloc[i])) & (common_table_df['Status'] == 'Open'), ['Report Generated Date']] = disposed_juvenile_cases['Report Generated Date'].iloc[i]
            common_table_df.loc[(common_table_df['Cause Number'] == (disposed_juvenile_cases['Cause Number'].iloc[i])) & (common_table_df['Status'] == 'Open'), ['Disposed Dates']] = disposed_juvenile_cases['Disposed Dates'].iloc[i]
            #common_table_df.loc[(common_table_df['Cause Number'] == (disposed_juvenile_cases['Cause Number'].iloc[i])) & (common_table_df['Status'] == 'Open'), ['Dispositions']] = disposed_juvenile_cases['Dispositions'][i] #Juvenile reports do not contain dispositions
            common_table_df.loc[(common_table_df['Cause Number'] == (disposed_juvenile_cases['Cause Number'].iloc[i])) & (common_table_df['Status'] == 'Open'), ['Disposed As Of Date']] = disposed_juvenile_cases['Disposed As Of Date'].iloc[i]
            common_table_df.loc[(common_table_df['Cause Number'] == (disposed_juvenile_cases['Cause Number'].iloc[i])) & (common_table_df['Status'] == 'Open'), ['Number Of Dispositions']] = disposed_juvenile_cases['Number Of Dispositions'].iloc[i]
            common_table_df.loc[(common_table_df['Cause Number'] == (disposed_juvenile_cases['Cause Number'].iloc[i])) & (common_table_df['Status'] == 'Open'), ['Last As Of Date']] = disposed_juvenile_cases['Last As Of Date'].iloc[i]
            common_table_df.loc[(common_table_df['Cause Number'] == (disposed_juvenile_cases['Cause Number'].iloc[i])) & (common_table_df['Status'] == 'Open'), ['Load DateTime']] = disposed_juvenile_cases['Load DateTime'].iloc[i]
            common_table_df.loc[(common_table_df['Cause Number'] == (disposed_juvenile_cases['Cause Number'].iloc[i])) & (common_table_df['Status'] == 'Open'), ['Status']] = disposed_juvenile_cases['Status'].iloc[i]

    #Finally upload the common_table_df to the common table worksheet in 'Pending Reports' spreadsheet
    common_sheet.clear()
    common_table_df.sort_values(by = ['Case Type','County','Status'], ignore_index=True, inplace=True, ascending = False)
    common_sheet.update([common_table_df.columns.values.tolist()] + common_table_df.values.tolist())
    
    print('Juvenile Cases Updated!')

    return

def update_civil_inactive_cases(new_inactive_df, report):
    """
    This function takes in the newly created inactive cases df and updates it with the current data on the 'Pending Reports' spreadsheet.
    It will connect to the Google Sheet, load the current data, append the new data to the current data, and drop duplicates without 
    losing previous work. Finally, it will upload the updated dataframe to the Civil Inactive Cases sheet of the 'Pending Reports' spreadsheet.
    
    Parameter:
        - new_inactive_df: The newly created dataframe from the most recent civil inactive cases PDF data

    Returns:
        - Nothing.
    """

    #Set up credentials to interact with Google Sheets
    gc = gspread.service_account_from_dict(credentials)
    
    #Open 'Pending Reports' Google Sheet By Name
    gsheet = gc.open(google_sheet_name)

    #Inactive cases go to the 'Inactive Cases' tab
    inactive_sheet = gsheet.worksheet(civil_inactive_sheet_name)

    #Load the data currently on the inactive cases tab in the 'Pending Reports' spreadsheet
    current_inactive_table_df = pd.DataFrame(inactive_sheet.get_all_records())

    if len(current_inactive_table_df) > 0 and len(new_inactive_df) > 0:
        #First, Verify that all Cause Numbers are represented as strings
        new_inactive_df['Cause Number'] = new_inactive_df['Cause Number'].astype(str).str.strip()
        current_inactive_table_df['Cause Number'] = current_inactive_table_df['Cause Number'].astype(str).str.strip()

        #Split it into active and inactive cases for the current report's county
        active_table_df = current_inactive_table_df[(current_inactive_table_df['Status'] == 'Active') & (current_inactive_table_df['County'] == new_inactive_df['County'].iloc[0])]

        inactive_table_df = current_inactive_table_df[(current_inactive_table_df['Status'] == 'Inactive') & (current_inactive_table_df['County'] == new_inactive_df['County'].iloc[0])]

        #Find the newly reactivated cases, if any. These would be previously 'Inactive', but are no longer on the inactive report
        #We need to change the status of these cases to 'Active' and set the 'Estimated Inactive End Date' to the current report's 'As Of Date'.
        #Then add these cases to the active_table_df and remove them from the inactive_table_df
        reactivated_cases_df = inactive_table_df[~(inactive_table_df['Cause Number'].isin(new_inactive_df['Cause Number']))].reset_index(drop=True)
        if len(reactivated_cases_df) > 0:
            reactivated_cases_df['Status'] = 'Active'
            for i in reactivated_cases_df.index:
                if reactivated_cases_df['Estimated Inactive End Date'].iloc[i] == '':
                    reactivated_cases_df['Estimated Inactive End Date'].iloc[i] = new_inactive_df['Last As Of Date'].iloc[0]
                else:
                    reactivated_cases_df['Estimated Inactive End Date'].iloc[i] = new_inactive_df['Last As Of Date'].iloc[0] + '\n' + str(reactivated_cases_df['Estimated Inactive End Date'].iloc[i])
            
            #Now add them to the active_table_df
            active_table_df = active_table_df.append(reactivated_cases_df, ignore_index = True)
            #And remove from inactive table df
            inactive_table_df = inactive_table_df[~(inactive_table_df['Cause Number'].isin(reactivated_cases_df['Cause Number']))].reset_index(drop=True)
        
        #It's possible that some cases could have been inactivated, reactivated, and then inactivated once again.
        #We need to check for any such cases
        #Find the newly inactivated cases that are currently listed as 'Active' in the table df
        #Update the status to 'Inactive' and set the new 'Active Start Date'
        #Then add these cases to the inactive table df and remove them from the active table df
        inactivated_cases_df = new_inactive_df[(new_inactive_df['Cause Number'].isin(active_table_df['Cause Number']))].reset_index(drop=True)
        if len(inactivated_cases_df) > 0:
            for i in inactivated_cases_df.index:
                inactivated_cases_df['Estimated Inactive End Date'].iloc[i] = str(active_table_df.loc[active_table_df['Cause Number'] == (inactivated_cases_df['Cause Number'].iloc[i]), ['Estimated Inactive End Date']])
                inactivated_cases_df['Original As Of Date'].iloc[i] = str(new_inactive_df['Original As Of Date']) + '\n' + str(active_table_df.loc[active_table_df['Cause Number'] == (inactivated_cases_df['Cause Number'].iloc[i]), ['Original As Of Date']])
                inactivated_cases_df['Last As Of Date'].iloc[i] = str(new_inactive_df['Last As Of Date']) + '\n' + str(active_table_df.loc[active_table_df['Cause Number'] == (inactivated_cases_df['Cause Number'].iloc[i]), ['Last As Of Date']])
            
            #Now add them to the inactive_table_df
            inactive_table_df = inactive_table_df.append(inactivated_cases_df, ignore_index = True).reset_index(drop=True)
            #And remove them from active_table_df
            active_table_df = active_table_df[~(active_table_df['Cause Number'].isin(inactivated_cases_df['Cause Number']))].reset_index(drop=True)

        #At this point, all cases in the inactive_table_df will be in the new_inactive_df.
        #All that needs to be updated now is the last as of date
        if len(inactive_table_df) > 0:
            inactive_table_df = inactive_table_df.reset_index(drop=True)
            for i in inactive_table_df.index:
                if len(inactive_table_df['Last As Of Date'].iloc[i]) > 10:
                    inactive_table_df['Last As Of Date'].iloc[i] = str(new_inactive_df['Last As Of Date'].iloc[0]) + str(inactive_table_df['Last As Of Date'].iloc[i])[10:]
                else:
                    inactive_table_df['Last As Of Date'].iloc[i] = str(new_inactive_df['Last As Of Date'].iloc[0])
            
            #Update the load DateTime
            inactive_table_df['Load DateTime'] = new_inactive_df['Load DateTime']
        
        #Now append inactive table df to the new inactive cases df and drop duplicates, keeping last.
        #This should keep all updated info intact while adding the entirely new inactive cases to the df
        inactive_table_df = inactive_table_df.append(new_inactive_df, ignore_index = True)
        inactive_table_df.drop_duplicates(subset = ['Cause Number'], ignore_index=True, inplace=True, keep='first')

        #Now append the active table df. This should give us all cases associated with the current county
        current_county_df = inactive_table_df.append(active_table_df, ignore_index = True)

        #Now append current_county_df to the total inactive_table_df and remove duplicates, keeping last.
        #This should give use the entirely new, updated inactive table.
        current_inactive_table_df = current_inactive_table_df.append(current_county_df, ignore_index = True)
        current_inactive_table_df.drop_duplicates(subset = ['Cause Number'], ignore_index=True, inplace=True, keep='last')

        #Clear what's currently on the Criminal Cases worksheet
        inactive_sheet.clear()

        #Now upload to Inactive Cases worksheet in 'Pending Reports' spreadsheet and leave a message
        inactive_sheet.update([current_inactive_table_df.columns.values.tolist()] + current_inactive_table_df.values.tolist())

        print('Inactive Cases Updated!')
        return
    
    elif len(current_inactive_table_df) > 0 and len(new_inactive_df) == 0:
        #First, Verify that all Cause Numbers are represented as strings
        current_inactive_table_df['Cause Number'] = current_inactive_table_df['Cause Number'].astype(str).str.strip()

        #Split it into active and inactive cases for the current report's county
        active_table_df = current_inactive_table_df[(current_inactive_table_df['Status'] == 'Active') & (current_inactive_table_df['County'] == report['County'])]

        inactive_table_df = current_inactive_table_df[(current_inactive_table_df['Status'] == 'Inactive') & (current_inactive_table_df['County'] == report['County'])]

        #Since the new_inactive_df is empty in this case, all of the inactive_table_df cases must now be considered reactivated.
        #We need to change the status of these cases to 'Active' and set the 'Estimated Inactive End Date' to the current report's 'As Of Date'.
        #Then add these cases to the active_table_df and remove them from the inactive_table_df
        reactivated_cases_df = inactive_table_df.reset_index(drop=True)
        if len(reactivated_cases_df) > 0:
            reactivated_cases_df['Status'] = 'Active'
            for i in reactivated_cases_df.index:
                if reactivated_cases_df['Estimated Inactive End Date'].iloc[i] == '':
                    reactivated_cases_df['Estimated Inactive End Date'].iloc[i] = report['As Of Date']
                else:
                    reactivated_cases_df['Estimated Inactive End Date'].iloc[i] = report['As Of Date'] + '\n' + str(reactivated_cases_df['Estimated Inactive End Date'].iloc[i])
            
            #Now add them to the active_table_df
            active_table_df = active_table_df.append(reactivated_cases_df, ignore_index = True)
            #And remove from inactive table df
            inactive_table_df = inactive_table_df[~(inactive_table_df['Cause Number'].isin(reactivated_cases_df['Cause Number']))].reset_index(drop=True)

        #The active_table_df should contain all cases from the inactive report for this county in this case
        #Now append active_table_df to the total inactive_table_df and remove duplicates, keeping last.
        #This should give use the entirely new, updated inactive table.
        current_inactive_table_df = current_inactive_table_df.append(active_table_df, ignore_index = True)
        current_inactive_table_df.drop_duplicates(subset = ['Cause Number'], ignore_index=True, inplace=True, keep='last')

        #Clear what's currently on the Criminal Cases worksheet
        inactive_sheet.clear()

        #Now upload to Inactive Cases worksheet in 'Pending Reports' spreadsheet and leave a message
        inactive_sheet.update([current_inactive_table_df.columns.values.tolist()] + current_inactive_table_df.values.tolist())
    
    elif len(current_inactive_table_df) == 0 and len(new_inactive_df) > 0:
        #Now upload to Inactive Cases worksheet in 'Pending Reports' spreadsheet and leave a message
        inactive_sheet.update([new_inactive_df.columns.values.tolist()] + new_inactive_df.values.tolist())

        print('Inactive Cases Updated!')

    else:
        #Both are empty, so do nothing.
        return

def update_criminal_inactive_cases(new_inactive_df, report):
    """
    This function takes in the newly created inactive cases df and updates it with the current data on the 'Pending Reports' spreadsheet.
    It will connect to the Google Sheet, load the current data, append the new data to the current data, and drop duplicates without 
    losing previous work. Finally, it will upload the updated dataframe to the Criminal Inactive Cases sheet of the 'Pending Reports' spreadsheet.
    
    Parameter:
        - new_inactive_df: The newly created dataframe from the most recent criminal inactive cases PDF data

    Returns:
        - Nothing.
    """

    #Set up credentials to interact with Google Sheets
    gc = gspread.service_account_from_dict(credentials)
    
    #Open 'Pending Reports' Google Sheet By Name
    gsheet = gc.open(google_sheet_name)

    #Inactive cases go to the 'Inactive Cases' tab
    inactive_sheet = gsheet.worksheet(criminal_inactive_sheet_name)

    #Load the data currently on the inactive cases tab in the 'Pending Reports' spreadsheet
    current_inactive_table_df = pd.DataFrame(inactive_sheet.get_all_records())

    if len(current_inactive_table_df) > 0 and len(new_inactive_df) > 0:
        #First, Verify that all Cause Numbers are represented as strings
        new_inactive_df['Cause Number'] = new_inactive_df['Cause Number'].astype(str).str.strip()
        current_inactive_table_df['Cause Number'] = current_inactive_table_df['Cause Number'].astype(str).str.strip()

        #Split it into active and inactive cases for the current report's county
        active_table_df = current_inactive_table_df[(current_inactive_table_df['Status'] == 'Active') & (current_inactive_table_df['County'] == new_inactive_df['County'].iloc[0])]

        inactive_table_df = current_inactive_table_df[(current_inactive_table_df['Status'] == 'Inactive') & (current_inactive_table_df['County'] == new_inactive_df['County'].iloc[0])]

        #Find the newly reactivated cases, if any. These would be previously 'Inactive', but are no longer on the inactive report
        #We need to change the status of these cases to 'Active' and set the 'Estimated Inactive End Date' to the current report's 'As Of Date'.
        #Then add these cases to the active_table_df and remove them from the inactive_table_df
        reactivated_cases_df = inactive_table_df[~(inactive_table_df['Cause Number'].isin(new_inactive_df['Cause Number']))].reset_index(drop=True)
        if len(reactivated_cases_df) > 0:
            reactivated_cases_df['Status'] = 'Active'
            for i in reactivated_cases_df.index:
                if reactivated_cases_df['Estimated Inactive End Date'].iloc[i] == '':
                    reactivated_cases_df['Estimated Inactive End Date'].iloc[i] = new_inactive_df['Last As Of Date'].iloc[0]
                else:
                    reactivated_cases_df['Estimated Inactive End Date'].iloc[i] = new_inactive_df['Last As Of Date'].iloc[0] + '\n' + str(reactivated_cases_df['Estimated Inactive End Date'].iloc[i])
            
            #Now add them to the active_table_df
            active_table_df = active_table_df.append(reactivated_cases_df, ignore_index = True)
            #And remove from inactive table df
            inactive_table_df = inactive_table_df[~(inactive_table_df['Cause Number'].isin(reactivated_cases_df['Cause Number']))].reset_index(drop=True)
        
        #It's possible that some cases could have been inactivated, reactivated, and then inactivated once again.
        #We need to check for any such cases
        #Find the newly inactivated cases that are currently listed as 'Active' in the table df
        #Update the status to 'Inactive' and set the new 'Active Start Date'
        #Then add these cases to the inactive table df and remove them from the active table df
        inactivated_cases_df = new_inactive_df[(new_inactive_df['Cause Number'].isin(active_table_df['Cause Number']))].reset_index(drop=True)
        if len(inactivated_cases_df) > 0:
            for i in inactivated_cases_df.index:
                inactivated_cases_df['Estimated Inactive End Date'].iloc[i] = str(active_table_df.loc[active_table_df['Cause Number'] == (inactivated_cases_df['Cause Number'].iloc[i]), ['Estimated Inactive End Date']])
                inactivated_cases_df['Original As Of Date'].iloc[i] = str(new_inactive_df['Original As Of Date']) + '\n' + str(active_table_df.loc[active_table_df['Cause Number'] == (inactivated_cases_df['Cause Number'].iloc[i]), ['Original As Of Date']])
                inactivated_cases_df['Last As Of Date'].iloc[i] = str(new_inactive_df['Last As Of Date']) + '\n' + str(active_table_df.loc[active_table_df['Cause Number'] == (inactivated_cases_df['Cause Number'].iloc[i]), ['Last As Of Date']])
            
            #Now add them to the inactive_table_df
            inactive_table_df = inactive_table_df.append(inactivated_cases_df, ignore_index = True).reset_index(drop=True)
            #And remove them from active_table_df
            active_table_df = active_table_df[~(active_table_df['Cause Number'].isin(inactivated_cases_df['Cause Number']))].reset_index(drop=True)

        #At this point, all cases in the inactive_table_df will be in the new_inactive_df.
        #All that needs to be updated now is the last as of date and load dateTime
        if len(inactive_table_df) > 0:
            inactive_table_df = inactive_table_df.reset_index(drop=True)
            for i in inactive_table_df.index:
                if len(inactive_table_df['Last As Of Date'].iloc[i]) > 10:
                    inactive_table_df['Last As Of Date'].iloc[i] = str(new_inactive_df['Last As Of Date'].iloc[0]) + str(inactive_table_df['Last As Of Date'].iloc[i])[10:]
                else:
                    inactive_table_df['Last As Of Date'].iloc[i] = str(new_inactive_df['Last As Of Date'].iloc[0])
            
            #Update the load DateTime
            inactive_table_df['Load DateTime'] = new_inactive_df['Load DateTime']
        
        #Now append inactive table df to the new inactive cases df and drop duplicates, keeping last.
        #This should keep all updated info intact while adding the entirely new inactive cases to the df
        inactive_table_df = inactive_table_df.append(new_inactive_df, ignore_index = True)
        inactive_table_df.drop_duplicates(subset = ['Cause Number'], ignore_index=True, inplace=True, keep='first')

        #Now append the active table df. This should give us all cases associated with the current county
        current_county_df = inactive_table_df.append(active_table_df, ignore_index = True)

        #Now append current_county_df to the total inactive_table_df and remove duplicates, keeping last.
        #This should give use the entirely new, updated inactive table.
        current_inactive_table_df = current_inactive_table_df.append(current_county_df, ignore_index = True)
        current_inactive_table_df.drop_duplicates(subset = ['Cause Number'], ignore_index=True, inplace=True, keep='last')

        #Clear what's currently on the Criminal Cases worksheet
        inactive_sheet.clear()

        #Now upload to Inactive Cases worksheet in 'Pending Reports' spreadsheet and leave a message
        inactive_sheet.update([current_inactive_table_df.columns.values.tolist()] + current_inactive_table_df.values.tolist())

        print('Inactive Cases Updated!')
        return
    
    elif len(current_inactive_table_df) > 0 and len(new_inactive_df) == 0:
        #First, Verify that all Cause Numbers are represented as strings
        current_inactive_table_df['Cause Number'] = current_inactive_table_df['Cause Number'].astype(str).str.strip()

        #Split it into active and inactive cases for the current report's county
        active_table_df = current_inactive_table_df[(current_inactive_table_df['Status'] == 'Active') & (current_inactive_table_df['County'] == report['County'])]

        inactive_table_df = current_inactive_table_df[(current_inactive_table_df['Status'] == 'Inactive') & (current_inactive_table_df['County'] == report['County'])]

        #Since the new_inactive_df is empty in this case, all of the inactive_table_df cases must now be considered reactivated.
        #We need to change the status of these cases to 'Active' and set the 'Estimated Inactive End Date' to the current report's 'As Of Date'.
        #Then add these cases to the active_table_df and remove them from the inactive_table_df
        reactivated_cases_df = inactive_table_df.reset_index(drop=True)
        if len(reactivated_cases_df) > 0:
            reactivated_cases_df['Status'] = 'Active'
            for i in reactivated_cases_df.index:
                if reactivated_cases_df['Estimated Inactive End Date'].iloc[i] == '':
                    reactivated_cases_df['Estimated Inactive End Date'].iloc[i] = report['As Of Date']
                else:
                    reactivated_cases_df['Estimated Inactive End Date'].iloc[i] = report['As Of Date'] + '\n' + str(reactivated_cases_df['Estimated Inactive End Date'].iloc[i])
            
            #Now add them to the active_table_df
            active_table_df = active_table_df.append(reactivated_cases_df, ignore_index = True)
            #And remove from inactive table df
            inactive_table_df = inactive_table_df[~(inactive_table_df['Cause Number'].isin(reactivated_cases_df['Cause Number']))].reset_index(drop=True)

        #The active_table_df should contain all cases from the inactive report for this county in this case
        #Now append active_table_df to the total inactive_table_df and remove duplicates, keeping last.
        #This should give use the entirely new, updated inactive table.
        current_inactive_table_df = current_inactive_table_df.append(active_table_df, ignore_index = True)
        current_inactive_table_df.drop_duplicates(subset = ['Cause Number'], ignore_index=True, inplace=True, keep='last')

        #Clear what's currently on the Criminal Cases worksheet
        inactive_sheet.clear()

        #Now upload to Inactive Cases worksheet in 'Pending Reports' spreadsheet and leave a message
        inactive_sheet.update([current_inactive_table_df.columns.values.tolist()] + current_inactive_table_df.values.tolist())
    
    elif len(current_inactive_table_df) == 0 and len(new_inactive_df) > 0:
        #Now upload to Inactive Cases worksheet in 'Pending Reports' spreadsheet and leave a message
        inactive_sheet.update([new_inactive_df.columns.values.tolist()] + new_inactive_df.values.tolist())

        print('Inactive Cases Updated!')

    else:
        #Both are empty, so do nothing.
        return