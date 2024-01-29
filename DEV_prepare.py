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

def count_number_of_dispositions(date_list):
    """
    This function takes in the list of disposition dates for disposed cases and counts how many there are.

    Parameter:
        - date_list: The list of strings representing the different disposed dates a case has

    Returns:
        - int: The number of disposed dates a case has, i.e., the number of dispositions related to that case
    """

    return len(date_list)

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
    closed_cases_df['Status'] = 'Dropped'

    #Set the dropped datetime column to the uploaded report's 'As Of' date
    date = new_cases_df['Last As Of Date'][0].strip()
    time = '00:00:00'
    datetime_str = date + ' ' + time

    datetime_object = datetime.strptime(datetime_str, '%m/%d/%Y %H:%M:%S')
    closed_cases_df['Dropped DateTime'] = str(datetime_object)

    #Add other disposed case columns
    closed_cases_df['Disposed Dates'] = ''
    closed_cases_df['Dispositions'] = ''
    closed_cases_df['Disposed As Of Date'] = ''
    closed_cases_df['Number Of Dispositions'] = 0

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
    
    #Create Status column. Defaults to open unless reading disposed cases
    if file_name.upper().count('DISP') > 0:
        df['Status'] = 'Disposed'
    else:
        df['Status'] = 'Open'

    #Create a new column for disposed cases that counts the number of dispositions related to a cause number
    #Also convert the disposition list to a single string with each item separated by a new line
    if file_name.upper().count('DISP') > 0:
        df['Number Of Dispositions'] = df['Dispositions'].apply(count_number_of_dispositions)
        df['Dispositions'] = df['Dispositions'].apply(convert_name_list_to_string)
        df['Disposed Dates'] = df['Disposed Dates'].apply(convert_name_list_to_string)

    #Create Load Date column
    #df['load_date'] = str(date.today())

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
    if (df['Case Type'][0] == 'Criminal' or df['Case Type'][0] == 'Criminal OLS') and df['Status'][0] != 'Disposed':
        df['First Offense'] = df['First Offense'].apply(convert_name_list_to_string)
        df['ST RPT Column'] = df['ST RPT Column'].apply(convert_name_list_to_string)
    
    return df

def prepare_pending_juvenile_cases(pending_juvenile_cases):
    """
    This function takes in a dataframe of pending juvenile cases.
    It will add required columns and perform transformations as necessary.
    It returns the updated dataframe.

    Parameter:
        pending_juvenile_cases: A dataframe representing pending juvenile cases only

    Returns:
        pending_juvenile_cases: The updated version of the original dataframe
    """

    #Add case type
    pending_juvenile_cases['Case Type'] = 'Juvenile'

    #Add case status
    pending_juvenile_cases['Status'] = 'Open'

    #Convert offense list into a single string
    pending_juvenile_cases['Offense'] = pending_juvenile_cases['Offense'].apply(convert_name_list_to_string)

    #Convert docket date list into a single string
    pending_juvenile_cases['Docket Date'] = pending_juvenile_cases['Docket Date'].apply(convert_name_list_to_string)

    #Add court
    pending_juvenile_cases['Court'] = '293'

    #Create Load DateTime column
    america_central_tz = pytz.timezone('America/Chicago')
    pending_juvenile_cases['Load DateTime'] = str(datetime.now(tz = america_central_tz))

    #Drop 'Disposed Dates' and 'Disposed As Of Date' columns
    pending_juvenile_cases = pending_juvenile_cases.drop(columns=['Disposed Dates', 'Disposed As Of Date'])

    #Reorder columns
    pending_juvenile_cases = pending_juvenile_cases[[
        'County',
        'Cause Number',
        'File Date',
        'Offense',
        'Docket Date',
        'Report Generated Date',
        'Original As Of Date',
        'Last As Of Date',
        'Case Type',
        'Status',
        'Load DateTime'
    ]]

    return pending_juvenile_cases

def prepare_disposed_juvenile_cases(disposed_juvenile_cases):
    """
    This function takes in a dataframe of disposed juvenile cases.
    It will add required columns and perform transformations as necessary.
    It returns the updated dataframe.

    Parameter:
        disposed_juvenile_cases: A dataframe representing disposed juvenile cases only

    Returns:
        disposed_juvenile_cases: The updated version of the original dataframe
    """

    #Add case type
    disposed_juvenile_cases['Case Type'] = 'Juvenile'

    #Add case status
    disposed_juvenile_cases['Status'] = 'Disposed'

    #Add disposition description (this data is not included in the report, but the column is needed to match up with the other case reports)
    disposed_juvenile_cases['Dispositions'] = ''

    #Count number of dispositions
    disposed_juvenile_cases['Number Of Dispositions'] = disposed_juvenile_cases['Disposed Dates'].apply(count_number_of_dispositions)

    #Convert disposition date list into a single string
    disposed_juvenile_cases['Disposed Dates'] = disposed_juvenile_cases['Disposed Dates'].apply(convert_name_list_to_string)

    #Convert offense list into a single string
    disposed_juvenile_cases['Offense'] = disposed_juvenile_cases['Offense'].apply(convert_name_list_to_string)

    #Convert docket date list into a single string
    disposed_juvenile_cases['Docket Date'] = disposed_juvenile_cases['Docket Date'].apply(convert_name_list_to_string)

    #Add court
    disposed_juvenile_cases['Court'] = '293'

    #Set the dropped datetime column to the uploaded report's 'As Of' date
    date = disposed_juvenile_cases['Last As Of Date'][0].strip()
    time = '00:00:00'
    datetime_str = date + ' ' + time

    datetime_object = datetime.strptime(datetime_str, '%m/%d/%Y %H:%M:%S')
    disposed_juvenile_cases['Dropped DateTime'] = str(datetime_object)

    #Create Load DateTime column
    america_central_tz = pytz.timezone('America/Chicago')
    disposed_juvenile_cases['Load DateTime'] = str(datetime.now(tz = america_central_tz))

    #Reorder columns
    disposed_juvenile_cases = disposed_juvenile_cases[[
        'County',
        'Cause Number',
        'File Date',
        'Offense',
        'Docket Date',
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

    return disposed_juvenile_cases

def prepare_dropped_juvenile_cases(dropped_juvenile_cases, dropped_as_of_date):
    """
    This function takes in a dataframe of dropped juvenile cases.
    It will add required columns and perform transformations as necessary.
    It returns the updated dataframe ready to be added to the closed juvenile cases table.

    Parameter:
        dropped_juvenile_cases: A dataframe representing dropped juvenile cases only
        dropped_as_of_date: A string representing the date the case was dropped from the juvenile report.

    Returns:
        dropped_juvenile_cases: The updated version of the original dataframe
    """

    #Add case status
    dropped_juvenile_cases['Status'] = 'Dropped'

    #Add disposition description (this data is not included in the report, but the column is needed to match up with the other case reports)
    dropped_juvenile_cases['Dispositions'] = ''

    #Set number of dispositions to 0 since the case was dropped.
    dropped_juvenile_cases['Number Of Dispositions'] = 0

    #Set disposed dates to an empty string since the case was dropped.
    dropped_juvenile_cases['Disposed Dates'] = ''

    #Set the dropped datetime column to the newest report's 'As Of' date
    time = '00:00:00'
    datetime_str = dropped_as_of_date + ' ' + time
    datetime_object = datetime.strptime(datetime_str, '%m/%d/%Y %H:%M:%S')
    dropped_juvenile_cases['Dropped DateTime'] = str(datetime_object)

    #Reorder columns
    dropped_juvenile_cases = dropped_juvenile_cases[[
        'County',
        'Cause Number',
        'File Date',
        'Offense',
        'Docket Date',
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

    return dropped_juvenile_cases