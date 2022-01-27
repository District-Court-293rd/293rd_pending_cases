import numpy as np
import pandas as pd
import re
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import PDFPageAggregator
from pdfminer3.converter import TextConverter
import io

#Create a function to identify combined cases
def check_for_combined_case(string):
    """
    This function takes in a string from the case. Normally, this string would represent the plaintiff's name,
    but sometimes the cases can be combined in the pdf. So, this function will check if this string is actually
    a cause number. If the string contains the letters 'cv' or 'tx', it will return True.
    
    Parameter:
        - string: The string to be checked
        
    Returns:
        - Boolean: True or False
    """
    
    #If the string contains a hyphen or the letters 'cv', return True
    if string.count('CV') > 0 or string.count('TX') > 0:
        return True
    else:
        return False

#Create a function that collects data from combined cases
def collect_civil_case_data(case_info):
    """
    This function takes in a list of strings that represent a single case. Each string may contain relevant information
    that will need to be collected, and added to a dictionary. That dictionary will then be added to a list 
    and returned.
    
    WARNING: This function is recursive.
    
    Parameter:
        -case_info: The list of strings representing a single case
        
    Returns:
        -case_list: A list containing the case dictionaries
    """
    
    #Initialize the temp list to store the dict(s)
    case_list = []
    
    #Initialize the temp dict
    temp_dict = {}
    
    #Remove leading whitespace
    case_info[0] = case_info[0].lstrip()

    #Get the cause number
    cause_num = case_info[0][:19].strip()

    #Get the file date
    file_date = case_info[0][15:30].strip()

    #Get the Cause of Action
    coa = case_info[0][30:56].strip()

    #Get the docket_date
    docket_date = case_info[0][56:68].strip()

    #Get the docket type
    docket_type = case_info[0][68:86].strip()

    #Get the ANS File
    ans_date = case_info[0][86:].strip()

    #Get the CR Number
    cr_num = case_info[0][96:].strip()

    #Get the names associated with each label
    #Will need to set up the lists before the loop. They will be added to the dict after the loop
    plaintiff_names = []
    plaintiff_attorneys = []
    defendant_names = []
    defendant_attorneys = []

    #The names always start on the third line (index = 2)
    for i in range(2, len(case_info)):

        #Check that this line is not the start of a combined case. If it is, collect combined case data,
        #Then break from this loop
        if check_for_combined_case(case_info[i][:38]) == True:
            #Set up temporary dictionary
            combined_case = {}

            #Find combined case text
            combined_case_text = []

            #Loop through and grab the necessary lines from the current case
            for index in range(i, len(case_info)):
                combined_case_text.append(case_info[index])

            #Collect combined case data
            combined_case = collect_civil_case_data(combined_case_text)

            #Add the temp dictionary to the overall container dict
            case_list.extend(combined_case)

            #Finally, break out of the loop
            break


        #Get the plaintiff name on current line
        plaintiff_name = case_info[i][:38]

        #Check if plaintiff_name is all whitesapace. If not, strip it and add to names list
        #Also check that the string is not empty
        if plaintiff_name.isspace() == False and len(plaintiff_name) > 0:
            plaintiff_names.append(plaintiff_name.strip())

        #Get the plaintiff attorney on current line
        plaintiff_attorney = case_info[i][38:64]

        #Check if plaintiff_attorney is all whitespace. If not, strip it and add to list
        #Also check that the string is not empty
        if plaintiff_attorney.isspace() == False and len(plaintiff_attorney) > 0:
            plaintiff_attorneys.append(plaintiff_attorney.strip())

        #Get the defendant name on current line
        defendant_name = case_info[i][64:94]

        #Check if defendant_name is all whitespace. If not, strip it and add to list
        #Also check that the string is not empty
        if defendant_name.isspace() == False and len(defendant_name) > 0:
            defendant_names.append(defendant_name.strip())

        #Get the defendant attorney on current line
        defendant_attorney = case_info[i][94:]

        #Check if the defendant_attorney is all whitespace. If not, strip it and add to list
        #Also check that the string is not empty
        if defendant_attorney.isspace() == False and len(defendant_attorney) > 0:
            defendant_attorneys.append(defendant_attorney.strip())


    #Now put all the info into a temp dict.
    temp_dict['County'] = county
    temp_dict['Cause Number'] = cause_num
    temp_dict['File Date'] = file_date
    temp_dict['Cause of Action'] = coa
    temp_dict['Docket Date'] = docket_date
    temp_dict['Docket Type'] = docket_type
    temp_dict['ANS File'] = ans_date
    temp_dict['CR Number'] = cr_num
    temp_dict['Plaintiff Name'] = plaintiff_names
    temp_dict['Plaintiff Attorney'] = plaintiff_attorneys
    temp_dict['Defendant Name'] = defendant_names
    temp_dict['Defendant Attorney'] = defendant_attorneys
    
    #Append the temp_dict to the case_list
    case_list.append(temp_dict)
    
    return case_list
    
def extract_civil_pdf_data(text):
    """
    This function takes in a page of text from a pdf file. It will extract all available information for each case on
    the page, put it all into dictionaries, and then return a list containing the other dictionaries for each
    case.
    
    Parameter:
        - text: The text of a single pdf page.
        
    Returns:
        - cases: A list containing the dictionaries of all cases.
    """
    
    #Set up the container list
    case_dicts = []
    
    #First, strip leading and trailing whitespaces
    text = text.strip()
    
    #Separate header and body text data
    #For header
    header = text[:389]
    
    #For body
    text = text[392:]
    
    #Remove headers from all subsequent pages
    text = re.sub(r"""COUNTY OF .{6,8} 293RD DISTRICT COURT CIVIL PENDING CASES AS OF .{10}

                                           RAN ON .{20,26} PAGE: \d{1,3}

        CAUSE #             FILE DATE CAUSE OF ACTION           DOCKT DATE  DOCKET TYPE       ANS FILED  CR CASE #

PLAINTIFF NAME                PLAINTIFF ATTORNEY        DEFENDANT NAME                DEFENDANT ATTORNEY""", '', text)
    
    #Use if statement to check for county names inside the header info
    if header.count('MAVERICK') >= 1:
        county = 'Maverick'
    elif header.count('DIMMIT') >= 1:
        county = 'Dimmit'
    elif header.count('ZAVALA') >= 1:
        county = 'Zavala'
    else:
        county = 'Something went wrong!'
    
    #Now split each case by the dashed lines
    cases = text.split('-------------------------------------------------------------------------------------------------------------')
    
    #Drop the last case. It only consists of the count of cases in the pdf. Not needed here
    cases.pop()
    
    #Loop through each case and build a dictionary with its info
    for case in cases:
        
        #Initialize the temp_dict
        temp_dict = {}
        
        #Remove leading whitespace only
        case = case.lstrip()
        
        #Split on the '/n'
        case_info = case.split('\n')
        
        #Gather the case data
        case_list = collect_civil_case_data(case_info)
        
        #Finally, append this dictionary to the container dict
        case_dicts.extend(case_list)
        
    return case_dicts
        
def build_civil_cases_dataframe(pdf_path):
    """
    This function reads in a pdf and extracts all available information for each case. It then returns a dataframe.
    
    Parameter:
        - pdf_path: The file path for the pdf to be read.
        
    Returns:
        - df: A dataframe of the resulting case information
    """
    
    #Set up the container list
    container_list = []
    
    #Set up resource manager to handle pdf content. text, images, etc.
    resource_manager = PDFResourceManager()

    #Used to display text
    fake_file_handle = io.StringIO()

    #Set up converter
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())

    #Set up page interpreter
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    with open(pdf_path, 'rb') as fh:

        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            #Process the current page
            page_interpreter.process_page(page)
            
        #Save the current page's text to a variable
        text = fake_file_handle.getvalue()

        #Extract info from current page
        case_dicts = extract_civil_pdf_data(text)

        #Extend case_dicts to container_dict
        container_list.extend(case_dicts)

    # close open handles
    converter.close()
    fake_file_handle.close()
    
    #How many cases were collected?
    print(f"Collected Data From {len(container_list)} Cases.")
    
    #Build dataframe
    df = pd.DataFrame(container_list)
    
    return df

