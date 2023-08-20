import streamlit as st
import pandas as pd
import gspread
import DEV_acquire
import DEV_prepare

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

def update_open_cases_common_table(new_cases, common_sheet):
    """
    This function takes in a df of the newly added open cases from the uploaded PDF report. It will take their info 
    and put it in a common dataframe that will then be updated on google sheets.

    Parameters:
        - new_cases: The dataframe of new, open cases
        - common_sheet: The connection to the 'DEV_Common_Table' google sheet

    Returns:
        - Nothing
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
        "Report As Of Date": [],
        "Load DateTime": [],
        "Closed DateTime": []
    }

    df = pd.DataFrame(dict)

    #Some portion of the criminal and civil cases will be the same. Update those columns first
    df['County'] = new_cases['County']
    df['Cause Number'] = new_cases['Cause Number']
    df['File Date'] = new_cases['File Date']
    df['Docket Date'] = new_cases['Docket Date']
    df['Court'] = '293' #Hard Coded for now, but may need to change later
    df['Case Type'] = new_cases['Case Type']
    df['Status'] = new_cases['Status']
    df['Report Generated Date'] = new_cases['Report Generated Date']
    df['Report As Of Date'] = new_cases['Report As Of Date']
    df['Load DateTime'] = new_cases['Load DateTime']
    df['Closed DateTime'] = '' #These are open cases, so none will have a closed date yet

    #Determine if cases are criminal or civil. They will have different logic
    if new_cases['Case Type'][0].count('Criminal') == 0:
        df['Cause'] = new_cases['Cause of Action']
        df['Docket Type'] = new_cases['Docket Type']
        df['ANS File'] = new_cases['ANS File']
        df['CR Number'] = new_cases['CR Number']
        #The following columns are only available in Criminal reports, so set them to empty strings
        df['Outstanding Warrants'] = ''
        df['ST RPT Column'] = ''
    else:
        df['Cause'] = new_cases['First Offense']
        df['Outstanding Warrants'] = new_cases['Outstanding Warrants']
        df['ST RPT Column'] = new_cases['ST RPT Column']
        #The following columns are only available in Civil Reports, so set them to empty strings
        df['Docket Type'] = ''
        df['ANS File'] = ''
        df['CR Number'] = ''
    
    #Now update the 'DEV_Common_Table' spreadsheet on google sheets

    #First, find next available row
    next_available_row = find_next_available_row(common_sheet)

    #If the first available row is the first row in the sheet, include the column names when updating
    #Otherwise, only send the values
    if next_available_row == 'A1':
        common_sheet.update([df.columns.values.tolist()] + df.values.tolist())
    else:
        common_sheet.update(next_available_row, df.values.tolist())

    return

def update_docket_dates_common_table(new_docket_dates, common_sheet):
    """
    This function takes in the df of cases with an updated docket date and locates each one of them in the common table.
    It then updates only the docket date in the common table for these cases.

    Parameter:
        - new_docket_dates: The dataframe containing the cases with newly updated docket dates
        - common_sheet: The connection to the 'DEV_Common_Table' spreadsheet on google sheets

    Returns:
        Nothing
    """

    #Get the column values for all columns that may need to be updated
    #Docket Date
    docket_date_col = common_sheet.find('Docket Date').col
    #Docket Type
    docket_type_col = common_sheet.find('Docket Type').col
    #ANS File
    ans_file_col = common_sheet.find('ANS File').col
    #CR Number
    cr_number_col = common_sheet.find('CR Number').col
    #Report As Of Date
    as_of_date_col = common_sheet.find('Report As Of Date').col
    #Load DateTime
    load_datetime_col = common_sheet.find('Load DateTime').col

    #Iterate through each item of the df and update appropriate columns
    if new_docket_dates['Case Type'][0].count('Criminal') > 0:
        for i in new_docket_dates.index:
            cell_row = common_sheet.find(new_docket_dates['Cause Number'][i]).row
            common_sheet.update_cell(cell_row, docket_date_col, new_docket_dates['Docket Date'][i])
            common_sheet.update_cell(cell_row, as_of_date_col, new_docket_dates['Report As Of Date'][i])
            common_sheet.update_cell(cell_row, load_datetime_col, new_docket_dates['Load DateTime'][i])
    else:
        for i in new_docket_dates.index:
            cell_row = common_sheet.find(new_docket_dates['Cause Number'][i]).row
            common_sheet.update_cell(cell_row, docket_date_col, new_docket_dates['Docket Date'][i])
            common_sheet.update_cell(cell_row, as_of_date_col, new_docket_dates['Report As Of Date'][i])
            common_sheet.update_cell(cell_row, load_datetime_col, new_docket_dates['Load DateTime'][i])
            common_sheet.update_cell(cell_row, docket_type_col, new_docket_dates['Docket Type'][i])
            common_sheet.update_cell(cell_row, ans_file_col, new_docket_dates['ANS File'][i])
            common_sheet.update_cell(cell_row, cr_number_col, new_docket_dates['CR Number'][i])

    return

def update_closed_cases_common_table(closed_cases, common_sheet):
    """
    This function takes in the newly closed cases dataframe and updates the 'Status' and 'Closed DateTime' columns of the common table.

    Parameters:
        - closed_cases: The dataframe containing the newly closed cases
        - common_sheet: The connection to the 'DEV_Common_Table' spreadsheet in google sheets

    Returns:
        Nothing
    """

    #Get the column values for all columns that may need to be updated
    #Closed DateTime
    closed_date_col = common_sheet.find('Closed DateTime').col
    #Status
    status_col = common_sheet.find('Status').col

    #Iterate through each item of the df and update appropriate columns
    for i in closed_cases.index:
        cell_row = common_sheet.find(closed_cases['Cause Number'][i]).row
        common_sheet.update_cell(cell_row, closed_date_col, closed_cases['Closed DateTime'][i])
        common_sheet.update_cell(cell_row, status_col, closed_cases['Status'][i])

    return

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
    if df['Case Type'][0].count('Criminal') > 0:
        #Add to criminal cases tab
        update_criminal_cases(df)
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
    gsheet = gc.open('Pending Reports')

    #Make connection to 'DEV_Common_Table'
    common_sheet = gsheet.worksheet('DEV_Common_Table')
    
    if new_civil_df['Case Type'][0].count('OLS') > 0:
        #Send OLS data to the 'Civil OLS Cases' tab
        civil_sheet = gsheet.worksheet('DEV_OLS_Civil_Cases')
        #Send closed OLS cases to the 'Closed Civil OLS Cases' tab
        closed_sheet = gsheet.worksheet('DEV_Closed_OLS_Civil_Cases')
    else:
        #Civil cases go to the 'Civil Cases' tab
        civil_sheet = gsheet.worksheet('DEV_Civil_Cases')
        #Closed cases go to the 'Closed Civil Cases' tab
        closed_sheet = gsheet.worksheet('DEV_Closed_Civil_Cases')

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

    #Find the new cases
    if len(current_civil_df) > 0:
        new_cases = new_civil_df[~(new_civil_df['Cause Number'].isin(current_civil_df['Cause Number']))]
        new_cases.reset_index(inplace = True)
    else:
        new_cases = new_civil_df

    #Append new_civil_df to current_civil_df
    current_civil_df = current_civil_df.append(new_civil_df, ignore_index = True)

    #Verify that all Cause Numbers are represented as strings
    current_civil_df['Cause Number'] = current_civil_df['Cause Number'].astype(str).str.strip()

    #Removed on 05-27-2023
    #Convert the google boolean values for the 'On Track' column to python booleans
    #current_civil_df['On Track'] = current_civil_df['On Track'].apply(convert_to_bool)

    #Removed on 05/30/2023
    #Convert the google boolean values for the 'Bad Cause Number' column to python booleans
    #current_civil_df['Bad Cause Number'] = current_civil_df['Bad Cause Number'].apply(convert_to_bool)

    #Stage 1 - Drop Duplicates for subset ['Cause Number', 'Docket Date'] while keeping first
    #If cause number and docket date are the same, then the case hasn't changed and is still open.
    #So we'll keep the original entry
    current_civil_df = current_civil_df.drop_duplicates(subset = ['Cause Number', 'Docket Date'], ignore_index = True, keep = 'first')

    #For updating the common table, create a df of duplicated cause numbers.
    #this gives me a list of cause numbers where the docket date has been updated and I'll be able to update them
    #specifically in the common table
    new_docket_dates = current_civil_df[current_civil_df.duplicated(['Cause Number'], keep = 'first')]
    new_docket_dates.reset_index(inplace = True)

    #Stage 2 - Drop Duplicates for subset ['Cause Number'] while keeping last
    #At this point, duplicates of cause number indicate that the 'Docket Date' has been updated since last upload
    #So keep the most recent version
    current_civil_df = current_civil_df.drop_duplicates(subset = ['Cause Number'], ignore_index = True, keep = 'last')

    #Now sort by county and then by cause number
    current_civil_df = current_civil_df.sort_values(by = ['County', 'Cause Number'], ignore_index = True)

    #Clear what's currently on the Civil Cases worksheet
    civil_sheet.clear()

    #Now upload to Civil Cases worksheet in 'Pending Reports' spreadsheet and leave a message
    civil_sheet.update([current_civil_df.columns.values.tolist()] + current_civil_df.values.tolist())

    #Now update the common table with the newly opened cases
    if len(new_cases) > 0:
        update_open_cases_common_table(new_cases, common_sheet)

    #Now update the common table with the new docket dates
    if len(new_docket_dates) > 0:
        update_docket_dates_common_table(new_docket_dates, common_sheet)

    #Finally update the common table with the newly closed cases
    if len(closed_cases_df) > 0:
        update_closed_cases_common_table(closed_cases_df, common_sheet)

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
    gsheet = gc.open("Pending Reports")

    #Make connection to 'DEV_Common_Table'
    common_sheet = gsheet.worksheet('DEV_Common_Table')

    if new_crim_df['Case Type'][0].count('OLS') > 0:
        #Send OLS data to the 'Civil OLS Cases' tab
        crim_sheet = gsheet.worksheet('DEV_OLS_Criminal_Cases')
        #Send closed OLS cases to the 'Closed Civil OLS Cases' tab
        closed_sheet = gsheet.worksheet('DEV_Closed_OLS_Criminal_Cases')
    else:
        #Civil cases go to the 'Civil Cases' tab
        crim_sheet = gsheet.worksheet('DEV_Criminal_Cases')
        #Closed cases go to the 'Closed Civil Cases' tab
        closed_sheet = gsheet.worksheet('DEV_Closed_Criminal_Cases')

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

    #Find the new cases
    if len(current_crim_df) > 0:
        new_cases = new_crim_df[~(new_crim_df['Cause Number'].isin(current_crim_df['Cause Number']))]
        new_cases.reset_index(inplace = True)
    else:
        new_cases = new_crim_df

    #Append new_crim_df to current_crim_df
    current_crim_df = current_crim_df.append(new_crim_df, ignore_index = True)

    #Verify that all Cause Numbers are represented as strings
    current_crim_df['Cause Number'] = current_crim_df['Cause Number'].astype(str).str.strip()

    #Removed on 05-27-2023
    #Convert the google boolean values for the 'On Track' column to python booleans
    #current_crim_df['On Track'] = current_crim_df['On Track'].apply(convert_to_bool)

    #Removed on 05/30/2023
    #Convert the google boolean values for the 'Bad Cause Number' column to python booleans
    #current_crim_df['Bad Cause Number'] = current_crim_df['Bad Cause Number'].apply(convert_to_bool)

    #Stage 1 - Drop Duplicates for subset ['Cause Number', 'Docket Date'] while keeping first
    current_crim_df = current_crim_df.drop_duplicates(subset = ['Cause Number', 'Docket Date'], ignore_index = True, keep = 'first')

    #For updating the common table, create a df of duplicated cause numbers.
    #this gives me a list of cause numbers where the docket date has been updated and I'll be able to update them
    #specifically in the common table
    new_docket_dates = current_crim_df[current_crim_df.duplicated(['Cause Number'], keep = 'first')]
    new_docket_dates.reset_index(inplace = True)

    #Stage 2 - Drop Duplicates for subset ['Cause Number'] while keeping last
    current_crim_df = current_crim_df.drop_duplicates(subset = ['Cause Number'], ignore_index = True, keep = 'last')

    #Now sort by county and then by cause number
    current_crim_df = current_crim_df.sort_values(by = ['County', 'Cause Number'], ignore_index = True)

    #Clear what's currently on the Criminal Cases worksheet
    crim_sheet.clear()

    #Now upload to Criminal Cases worksheet in 'Pending Reports' spreadsheet and leave a message
    crim_sheet.update([current_crim_df.columns.values.tolist()] + current_crim_df.values.tolist())

    #Now update the common table with the newly opened cases
    if len(new_cases) > 0:
        update_open_cases_common_table(new_cases, common_sheet)

    #Now update the common table with the new docket dates
    if len(new_docket_dates) > 0:
        update_docket_dates_common_table(new_docket_dates, common_sheet)

    #Finally update the common table with the newly closed cases
    if len(closed_cases_df) > 0:
        update_closed_cases_common_table(closed_cases_df, common_sheet)
    
    print('Criminal Cases Updated!')

    return
