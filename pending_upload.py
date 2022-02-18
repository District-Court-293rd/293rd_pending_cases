import numpy as np
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import jsmith_acquire
import jsmith_prepare

def update_spreadsheet(pdf_path):
    """
    This function takes in a list containing the file paths of the PDFs that need to be extracted. It'll loop
    and build civil and criminal case dataframes. Then, it will load the data currently stored in the 'Pending Reports'
    google sheet and turn it into a dataframe. Finally, it will append the dataframes appropriately, drop duplicates,
    and then upload the updated data to the 'Pending Reports' google sheet.
    """
    #Set up dataframes for new data
    new_civil_df = pd.DataFrame()
    
    new_crim_df = pd.DataFrame()
    
    
    for path in pdf_path:
        #Extract the PDF data
        df = jsmith_acquire.build_dataframe(path)
        #Prepare the df and add new columns
        df = jsmith_prepare.prepare_dataframe(df)

        if df['Case Type'][0] == 'Criminal':
            #Add to criminal cases tab
            new_crim_df = new_crim_df.append(df, ignore_index = True)
        elif df['Case Type'][0] == 'Civil' or df['Case Type'][0] == 'Tax':
            new_civil_df = new_civil_df.append(df, ignore_index = True)
        else:
            print('Something went wrong in the loop!')
        
    #Set up credentials to interact with Google Sheets
    gc = gspread.service_account(filename='pending_cases.json')
    
    #Open 'Pending Reports' Google Sheet By Name
    gsheet = gc.open("Pending Reports")
    
    #Civil cases go to the 'Civil Cases' tab
    civil_sheet = gsheet.worksheet('test_civil_cases')

    #Criminal cases go to the 'Criminal Cases' tab
    crim_sheet = gsheet.worksheet('test_criminal_cases')
    
    #Load the data currently on the civil cases tab in the 'Pending Reports' spreadsheet
    current_civil_df = pd.DataFrame(civil_sheet.get_all_records())
    
    #Load the data currently on the criminal cases tab in the 'Pending Reports' spreadsheet
    current_crim_df = pd.DataFrame(crim_sheet.get_all_records())
    
    #Append new_civil_df to current_civil_df
    current_civil_df = current_civil_df.append(new_civil_df, ignore_index = True)
    
    #Append new_crim_df to current_crim_df
    current_crim_df = current_crim_df.append(new_crim_df, ignore_index = True)
    
    #Stage 1 - Drop Duplicates for subset ['Cause Number', 'Docket Date'] while keeping first
    #For civil cases
    current_civil_df = current_civil_df.drop_duplicates(subset = ['Cause Number', 'Docket Date'], ignore_index = True, keep = 'first')
    
    #For criminal cases
    current_crim_df = current_crim_df.drop_duplicates(subset = ['Cause Number', 'Docket Date'], ignore_index = True, keep = 'first')
    
    #Stage 2 - Drop Duplicates for subset ['Cause Number'] while keeping last
    #For civil cases
    current_civil_df = current_civil_df.drop_duplicates(subset = ['Cause Number'], ignore_index = True, keep = 'last')
    
    #For criminal cases
    current_crim_df = current_crim_df.drop_duplicates(subset = ['Cause Number'], ignore_index = True, keep = 'last')
    
    #Now sort by county and then by cause number
    #For civil cases
    current_civil_df = current_civil_df.sort_values(by = ['County', 'Cause Number'], ignore_index = True)
    
    #For criminal cases
    current_crim_df = current_crim_df.sort_values(by = ['County', 'Cause Number'], ignore_index = True)
    
    #Now upload to appropriate tabs in 'Pending Reports' spreadsheet and leave a message
    #For civil cases
    civil_sheet.update([current_civil_df.columns.values.tolist()] + current_civil_df.values.tolist())
    print('Civil Cases Updated!')
    
    #For criminal cases
    crim_sheet.update([current_crim_df.columns.values.tolist()] + current_crim_df.values.tolist())
    print('Criminal Cases Updated!')
    
    return
    
    