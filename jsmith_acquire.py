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


def build_dataframe(pdf_path):
    """
    This function takes in a path to the desired PDF, determines whether or not it is a civil
    or criminal case PDF, and then calls the respective function to extract the PDF data
    and build a dataframe.

    Parameter:
        - pdf_path: A string representing the file path for the PDF

    Returns:
        - df: A dataframe of the information extracted from the given PDF
    """

    #Verify the file is a pdf. If not, print a message and return -1
    if pdf_path[-4:] != '.pdf':
        print('This file is not a PDF. Please use PDF files only.')
        return -1 

    #Now check if it is criminal or civil and then call the associated functions
    if pdf_path.upper().count('CR') > 0:
        df = build_criminal_cases_dataframe(pdf_path)
    elif pdf_path.upper().count('CV') > 0:
        df = build_civil_cases_dataframe(pdf_path)
    else:
        #Leave a message
        print("Something Went Wrong! Could not identify the PDF as Criminal or Civil.")
        return -1

    return df


#Create a function to identify combined cases in the civil cases PDF
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
    
    #If the string contains the letters 'CV' or 'TX' and IS NOT 'TX DFPS', return True
    if (string.count('CV') > 0 or string.count('TX') > 0) and (string.count('TX DFPS') == 0):
        return True
    else:
        return False

#Create a function that collects data from combined cases
def collect_civil_case_data(case_info, county):
    """
    This function takes in a list of strings that represent a single case. Each string may contain relevant information
    that will need to be collected, and added to a dictionary. That dictionary will then be added to a list 
    and returned.
    
    WARNING: This function is recursive.
    
    Parameter:
        -case_info: The list of strings representing a single case
        -county: The county information acquired from the previous function
        
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
    file_date = case_info[0][19:30].strip()

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
            combined_case = collect_civil_case_data(combined_case_text, county)

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
    text = text[389:]
    
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
        case_list = collect_civil_case_data(case_info, county)
        
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



    ###################################### FOR CRIMINAL CASE PDFS #########################################



def extract_criminal_pdf_data(text):
    """
    This function takes in the entire PDF document as a string of text. It will gather the info for each case
    and add the info to a dictionary. The dictionary for each case will be added to a list which will be turned into
    a dataframe.
    
    Parameter:
        -text: A string consisting of the text of the entire PDF document.
        
    Returns:
        -df: A dataframe of the newly gathered case info
    """
    
    #Initialize container list
    case_list = []
    
    #Separate the first header from the body
    #We'll use this to identify the county later
    header = text[:517]
    
    #Body
    body = text[517:]
    
    #Remove leading and trailing whitespaces from the body text
    body = body.strip()
    
    #Use if statement to check for county names inside the header info
    if header.count('MAVERICK') >= 1:
        county = 'Maverick'
    elif header.count('DIMMIT') >= 1:
        county = 'Dimmit'
    elif header.count('ZAVALA') >= 1:
        county = 'Zavala'
    else:
        county = 'Something went wrong!'
        
    #Set up regex to remove all subsequent headers
    #This regex should identify the headers even if the name of the district clerk changes later on
    body = re.sub(r"""\n
                                                  .{6,8} COUNTY CRIMINAL PENDING REPORT -- PAGE: \d{1,3}
                                                        .*, DISTRICT CLERK
                                                              RUN ON .{19}
                                                                   AS OF .{10}

CAUSE #           FILE DATE  DEFENDANT NAME             ATTORNEY         BONDSMAN NAME    OFFENSE DESCRIPTION                  CASE STATUS""",
    '', body)
    
    
    #########################################################################################################
    #Set up regex to remove the MTR/MTA separation
    body = re.sub("""TOTAL FILED CASES: \d{1,4}

MTR/MTA CASES FILED

""", '', body)
    
    
    #########################################################################################################
    #Set up regex to remove the case count section at the end
    body = re.sub("""
NUMBER OF MTR/MTA CASES: \d{1,4}

.*\d{1,4}
.*\d{1,4}
------------------------------
.*\d{1,4}""", '', body)
    
    #########################################################################################################
    
    #Split the text on the '\n' to isolate each case
    cases = body.split('\n')
    
    #Remove cases that happen to be empty or consist of whitespace only
    cases = [case for case in cases if case.isspace() == False and len(case) > 0]
    
    #Loop through each case. Add case info to temp dict, and then add that to the case list
    for case in cases:
        #Create temp_dict
        temp_dict = {}

        #Verify this is a valid case. Check for cause number
        if case[:17].isspace():
            continue
        
        #Strip leading and trailing whitespace
        case = case.strip()

        #Gather the cause number
        cause_num = case[:17].strip()

        #Gather the file date
        file_date = case[17:29].strip()

        #Get defendant name
        defendant_name = case[29:56].strip()

        #Get attorney name
        attorney = case[56:72].strip()

        #Get bondsman name
        bondsman = case[72:90].strip()

        #Get offense description
        offense = case[90:127].strip()

        #Get case status
        status = case[127:].strip()

        #Add info to temp dict
        temp_dict['County'] = county
        temp_dict['Cause Number'] = cause_num
        temp_dict['File Date'] = file_date
        temp_dict['Docket Date'] = ''
        temp_dict['Defendant Name'] = defendant_name
        temp_dict['Attorney Name'] = attorney
        temp_dict['Bondsman Name'] = bondsman
        temp_dict['Offense'] = offense

        #Append to case list
        case_list.append(temp_dict)
    
    #How many?
    print(f'Collected Data From {len(case_list)} Cases.')
    
    #Create dataframe
    df = pd.DataFrame(case_list)
    
    return df


def build_criminal_cases_dataframe(pdf_path):
    """
    This function reads in the criminal cases pdf document and extracts all available information for each case. 
    It then returns a dataframe.
    
    Parameter:
        - pdf_path: The file path for the pdf to be read.
        
    Returns:
        - df: A dataframe of the resulting case information
    """
    
    #Set up resource manager to handle pdf content. text, images, etc.
    resource_manager = PDFResourceManager()

    #Used to display text
    fake_file_handle = io.StringIO()

    #Set up converter
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())

    #Set up page interpreter
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    with open(pdf_path, 'rb') as fh:

        for page_num, page in enumerate(PDFPage.get_pages(fh, caching=True, check_extractable=True)):
            #Process the current page
            page_interpreter.process_page(page)

        #Save the current page's text to a variable
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    
    #Collect criminal case info and get the df
    df = extract_criminal_pdf_data(text)
    
    return df