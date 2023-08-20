import pandas as pd
import re
from datetime import date, datetime
import pytz

def get_case_type(value):
    """
    This function looks at the cause number and determines what type of case it is. If the given string doesn't meet
    any of the criteria, it assumes the case is Civil.
    
    Parameter:
        -value: A string for the cause number
        
    Returns:
        -type: A string for Civil, Juvenile, OLS, or Tax
    """
    
    #Check for TX type first
    if value.upper().count('TX') > 0:
        return 'Tax'
    elif value.upper().count('CV') > 0:
        return 'Civil'
    elif value.upper().count('JU') > 0:
        return 'Juvenile'
    else:
        #Since there are many civil cases that don't follow the same formatting, 
        #I will assume that anything not matching above is a civil case.
        return 'Civil'

#Build a function to calculate the days passed and determine if a case is on track or not
def check_on_track(value):
    """
    This function takes in a datetime object and calculates the number of days between it and the current date.
    If that number is greater than 0 days (meaning the docket date is in the past), then this function returns False to indicate that 
    a case is NOT on track. Otherwise, it returns True.
    
    Parameter:
        -value: This is a datetime object representing the case Docket Date
        
    Returns:
        -Boolean: True or False
    """
    
    #Check for docket date. If none, return False
    if value == '':
        return False
    
    #Get today's date
    today = date.today()
    
    #Convert it to datetime object
    today = pd.to_datetime(today)
    
    #Convert current value to datetime object
    value = pd.to_datetime(value)
    
    #Calculate days passed
    days_passed = today - value 
    
    #Convert the datetime object to an integer
    days_passed = days_passed // pd.Timedelta('1d')
    
    #If days passed > 0, case is not on track
    if days_passed > 0:
        return False
    else:
        return True
    
def check_cause_number_format(value):
    """
    This function takes in the cause number and checks the format. If the format is wrong, the function returns true. Otherwise, it returns false.

    Parameter:
        - value: The cause number of the case

    Returns:
        -Boolean: True if the cause number is bad, false otherwise
    """
    #Check the format using regex search function
    match = re.search(r'\d{2}-\d{2}-\d{5}-[A-Z]{3,5}', value)

    if match == None:
        return True
    else:
        return False

def convert_name_list_to_string(name_list):
    """
    This function takes in the list of names for the Plaintiff, Plaintiff Attorney, Defendant, and Defendant Attorney
    in the civil cases dataframe. It will join the names in each list with a new line character. This is necessary to
    upload the dataframe to a google sheet.

    Parameter:
        - name_list: The list of names

    Returns:
        - string: A single string consisting of all the names in the list joined by new lines.
    """

    name_string = '\n'.join(name_list)

    return name_string

def prepare_closed_cases(closed_cases_df, new_cases_df):
    """
    This function takes in a dataframe of newly closed cases and prepares them to be added to the appropriate closed cases tab.
    It will set the closed date to the current date, set case status to closed, calculate the number of days it took to get a docket date
    as well as the number of days it took to close, and remove the 'Months ahead or behind' and 'On track' columns since they won't matter once a case
    is closed.

    Parameter:
        -closed_cases_df: The dataframe containing the newly closed cases
        -new_cases_df: The dataframe containing the newly uploaded cases - Needed to get the report's 'As Of' date

    Returns:
        -closed_cases_df: The dataframe containing the newly closed cases with the updated information
    """

    #Set status to closed
    closed_cases_df['Status'] = 'Closed'

    #Set the closed datetime column to the uploaded report's 'As Of' date
    date = new_cases_df['Report As Of Date'][0].strip()
    time = '00:00:00'
    datetime_str = date + ' ' + time

    datetime_object = datetime.strptime(datetime_str, '%m/%d/%Y %H:%M:%S')
    closed_cases_df['Closed DateTime'] = str(datetime_object)

    #Calculate the number of days to the final docket date
    #file_date = pd.to_datetime(closed_cases_df['File Date'])
    #docket_date = pd.to_datetime(closed_cases_df['Docket Date'])
    #closed_date = pd.to_datetime(closed_cases_df['Closed Date'])

    #days_to_docket_date = (docket_date - file_date) // pd.Timedelta('1d')
    #closed_cases_df['Days To Docket Date'] = days_to_docket_date

    #Calculate the number of days to the final closing date
    #days_to_close = (closed_date - file_date) // pd.Timedelta('1d')
    #closed_cases_df['Days To Close'] = days_to_close

    #Removed on 05-27-2023
    #Drop the 'On track' column
    #closed_cases_df = closed_cases_df.drop(['On Track'], axis = 1)

    return closed_cases_df

def prepare_dataframe(file_name, df):
    """
    This function takes in a newly created case dataframe and adds additional columns. Do not pass in a dataframe
    that has already been manually updated. It will remove any previous work.
    
    Parameter:
        - df: The newly created case dataframe. Can be civil or criminal.
        
    Returns:
        - df: The same dataframe, but with new columns added.
    """

    #Verify Cause Numbers are represented as strings
    #df['Cause Number'] = df['Cause Number'].astype(str)

    #Now check if it is criminal, civil, or OLS
    if file_name.upper().count('OLS') > 0 and file_name.upper().count('CR') > 0:
        #Assign as OLS case type
        df['Case Type'] = 'Criminal OLS'
    elif file_name.upper().count('OLS') > 0 and ( file_name.upper().count('CV') > 0 or file_name.upper().count('CIVIL') > 0 ):
        #Assign as OLS case type
        df['Case Type'] = 'Civil OLS'
    elif file_name.upper().count('CR') > 0:
        #Assign as Criminal case type
        df['Case Type'] = 'Criminal'
    else:
        #Check if any civil cases are tax cases and update accordingly
        df['Case Type'] = df['Cause Number'].apply(get_case_type)
    
    #Removed on 05-27-2023
    #Create On Track column
    #df['On Track'] = df['Docket Date'].apply(check_on_track)

    #Create Months to Docket Date column. The actual values will be created later since they need to be updated for all
    #open cases every time a new report is uploaded.
    #df['Months Ahead Or Behind'] = ''

    #Removed on 05/30/2023
    #Create Bad Cause Number column
    #df['Bad Cause Number'] = df['Cause Number'].apply(check_cause_number_format)
    
    #Create Status column. Defaults to Open
    df['Status'] = 'Open'

    #Create Load DateTime column
    america_central_tz = pytz.timezone('America/Chicago')
    df['Load DateTime'] = str(datetime.now(tz = america_central_tz))

    #As of 13 June 2023, we are no longer collecting names
    #Convert the lists of names in the civil cases dataframe to single strings with each name separated by a new line
    #if df['Case Type'][0] != 'Criminal':
    #    df['Plaintiff Name'] = df['Plaintiff Name'].apply(convert_name_list_to_string)
    #    df['Plaintiff Attorney'] = df['Plaintiff Attorney'].apply(convert_name_list_to_string)
    #    df['Defendant Name'] = df['Defendant Name'].apply(convert_name_list_to_string)
    #    df['Defendant Attorney'] = df['Defendant Attorney'].apply(convert_name_list_to_string)
    if df['Case Type'][0] == 'Criminal' or df['Case Type'][0] == 'Criminal OLS':
        df['First Offense'] = df['First Offense'].apply(convert_name_list_to_string)
        df['ST RPT Column'] = df['ST RPT Column'].apply(convert_name_list_to_string)
    
    return df