import numpy as np
import pandas as pd
import gspread
#from oauth2client.service_account import ServiceAccountCredentials
import jsmith_acquire
import jsmith_prepare

#JSON credentials for accessing the Pending Reports Spreadsheet
credentials = {
  "type": "service_account",
  "project_id": "rd-spreadsheet-test",
  "private_key_id": "1faeb4841e331afa6694c29e689ebfea2b909c93",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCDIp2Wh+zVQE0y\ncRVXAZLUstsBc8we+wLuMJm4PvkvAcMG6TjfkCmYYVfLRObKUkRjGCeXchfQIutl\nH54kJrL/WnkLUTuWmHcGNp9DIm5ukdO5wHmBW4YxeGpXffBL00aZybXZQjIj0xJy\n0Zb/KADN9XXNwAHazJsDA45jAJcyN0ZLnwIkYjtbROHPGcTDWkd1WbluwYu+joHp\n+Qib2lHoEGx9Evm56/QjpS2NuL0+dC64xs8kCmHSWNJYf1hrwxmmNF6dWL8pU6ET\nHmktoLc4fCR2lXQbRUbJVx63QqK0fKR97nOrXKLU42JmH4O0Sa3FCRF8fos8yaIO\n/MgsVsptAgMBAAECggEADbiuB6XCZM/9I+WMR5XdEM+ENgMxXR6DwHuqYgqI1V/Y\nUd1Oe6ogiBbLcnQLuCjiigHphqHEFx3IRsUHrZ21Bh4n40TFOO1MKwTFJmewaXZt\n0pZuwFfc00lXyz7cyXpafVYLZqfUCkaYPBZtN9auOt7PzE8mgof9QlP5bqeNqo3S\nv6Hjmzkn3ht9rq8i6QWAXqaJVsnOurVnDGXdTdD4Tk5vK0VYmu2DOkM60xxTx0tC\nM2Lm0tI46czQydZopf+yH9gP0LAUkATZLLwxP0PcnmS/I9hj6vdJRq64jWHYUwvx\npezLdSh5pYstBSqiKIbkn3RlXnT7dFL7PWxVJmNL6wKBgQC3s4BDna/yHVwkMGpK\nbbb8tO6gNEBNvWLHonVqQDd/+p4Ar2GxTsdckLfwMdjqgAleTWndoZ9QScmbZdpS\nvdND+2Y4RkX2CMz+UzmhKVVE5dwY0tO8g8Tqy+/+5l3s9uaqST495QCUqI1lDGlI\nBJ4CWOVnoWbbxq//Xl8samclXwKBgQC2vuvCYsFTxzNa9xMEvBjfC37KjyX3X3vQ\nA3/lhgP9M/T9Eihf6I2nzYUZu2ZQTazQ9I1V8PRrq1M4RHLxUZDvA4QwukRL4GTX\n9l15b4/5AT9uOnsmqHX9p5P843z+4HZGlzoF9IDyMU6+ttkR40K5udzQqtQeb6Tq\noYy7Xnf3swKBgQCCab5/Qi0sl0dYsb5jxGwKD3Dw7udPyUmdLGpq2dgM1SDin5+d\nPq4tute6f8jdAbSk7BRiMWFmoFuuJKrP3s9jDdDN1qXIOws86lyZWzybwwtz3AhR\nZsKfZdSlg2ne1pF/BqxXSIIXB2oJ+LutUwnR5MZHwb/B+tXrV1X9tDQxxQKBgCBo\n9dkQuKbKEmKUpSvWzDZqjH8SKjKYHZZDuKAVR4nVeCKV4NE5pj3XZj6tDLU7QWYB\nqTtPs5mQ1f6JrTT9OU4aeoxFzK0ES/49NFDAJ3GK9hvvhT3S7LIi0U0tb1KornFQ\nirrZpTDO699JAHB6tK/Jtc7QLTSEqmPuaM4mL/KfAoGBAKFMUu/c23wEKR1rZ3IN\nsQ/YhvZIIGjnB4gGsAlyPK9+imbbDufZQL2QzroUEG3HyZTgdJ+xmx0v08jQhfS9\nHpk12TSqiTijpXm7QkBXb8I2Lz2DsFcS0/ObOYinxwoPkvYZErYbKHYqq9Zvu62w\nTRoTE+bQdS/V45ZMWUh/S2pb\n-----END PRIVATE KEY-----\n",
  "client_email": "jsmith-creds@rd-spreadsheet-test.iam.gserviceaccount.com",
  "client_id": "106138092146303165019",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/jsmith-creds%40rd-spreadsheet-test.iam.gserviceaccount.com"
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
