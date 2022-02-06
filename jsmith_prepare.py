import numpy as np
import pandas as pd
import re
from datetime import date

def get_case_type(value):
    """
    This function looks at the cause number and determines what type of case it is. If the given string doesn't meet
    any of the criteria, it assumes the case is Civil.
    
    Parameter:
        -value: A string for the cause number
        
    Returns:
        -type: A string for Civil, Criminal, or Tax
    """
    
    #Check for TX type first
    if value.count('TX') > 0:
        return 'Tax'
    elif value.count('CV') > 0:
        return 'Civil'
    elif value.count('CR') > 0:
        return 'Criminal'
    else:
        #Since there are many civil cases that don't follow the same formatting, 
        #I will assume that anything not matching above is a civil case.
        return 'Civil'


#Build a function to calculate the days passed and determine if a case is on track or not
def check_on_track(value):
    """
    This function takes in a datetime object and calculates the number of days between it and the current date.
    If that number is greater than 90 days (about 3 months), then this function returns False to indicate that 
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
    
    #If days passed > 90, case is not on track
    if days_passed > 90:
        return False
    else:
        return True

def prepare_case_dataframe(df):
    """
    This function takes in a newly created case dataframe and adds additional columns. Do not pass in a dataframe
    that has already been manually updated. It will remove any previous work.
    
    Parameter:
        - df: The newly created case dataframe. Can be civil or criminal.
        
    Returns:
        - df: The same dataframe, but with new columns added.
    """
    
    #Create case type column
    df['Case Type'] = df['Cause Number'].apply(get_case_type)
    
    #Create On Track column
    df['On Track'] = df['Docket Date'].apply(check_on_track)
    
    #Create Status column. Defaults to Pending
    df['Status'] = 'Pending'
    
    #Create File Has Image column
    df['File Has Image'] = ''
    
    #Create Need File column
    df['Need File'] = ''
    
    #Create Disposed Date column
    df['Disposed Date'] = ''
    
    #Create Finding column
    df['Finding'] = ''
    
    #Create Finding Date column
    df['Finding Date'] = ''
    
    return df