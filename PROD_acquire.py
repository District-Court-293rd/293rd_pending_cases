import pandas as pd
import re


def build_dataframe(file_name, content):
    """
    This function takes in the file name and text content of the uploaded PDF. It will use the file name to determine
    whether the PDF is a civil case or criminal case PDF. After that, it will feed the text content to the appropriate
    function to gather the data and build a dataframe.

    Parameter:
        - file_name: A string representing the file name of the uploaded PDF.
        - content: A string representing the text content of the uploaded PDF.

    Returns:
        - df: A dataframe of the information extracted from the uploaded PDF.
    """
    #Check if it is criminal or civil and then call the associated functions
    if file_name.upper().count('CR') > 0:
        df = build_criminal_cases_dataframe(content)
    elif file_name.upper().count('CV') > 0 or file_name.upper().count('CIVIL') > 0:
        df = build_civil_cases_dataframe(content)
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
    
    #If the string contains the letters 'CV' or 'TX' and IS NOT 'TX DFPS' or 'TX LLC', return True
    if (string.count('CV') > 0 or string.count('TX') > 0) and (string.count('TX DFPS') == 0) and (string.count('TX LLC') == 0):
        return True
    else:
        return False

#Create a function that collects data from combined cases
def extract_civil_case_data(case_info, county):
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
    ans_date = case_info[0][86:96].strip()

    #Get the CR Number
    cr_num = case_info[0][96:].strip()

    #Get the names associated with each label
    #Will need to set up the lists before the loop. They will be added to the dict after the loop
    #plaintiff_names = []
    #plaintiff_attorneys = []
    #defendant_names = []
    #defendant_attorneys = []

    #As of 13 June 2023, we are no longer collecting names
    #We still need to check for combined cases though and go through each line
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
            combined_case = extract_civil_case_data(combined_case_text, county)

            #Add the temp dictionary to the overall container dict
            case_list.extend(combined_case)

            #Finally, break out of the loop
            break

        #As of 13 June 2023, we are no longer collecting names

        #Get the plaintiff name on current line
        #plaintiff_name = case_info[i][:38]

        #Check if plaintiff_name is all whitesapace. If not, strip it and add to names list
        #Also check that the string is not empty
        #if plaintiff_name.isspace() == False and len(plaintiff_name) > 0:
        #    plaintiff_names.append(plaintiff_name.strip())

        #Get the plaintiff attorney on current line
        #plaintiff_attorney = case_info[i][38:64]

        #Check if plaintiff_attorney is all whitespace. If not, strip it and add to list
        #Also check that the string is not empty
        #if plaintiff_attorney.isspace() == False and len(plaintiff_attorney) > 0:
        #    plaintiff_attorneys.append(plaintiff_attorney.strip())

        #Get the defendant name on current line
        #defendant_name = case_info[i][64:94]

        #Check if defendant_name is all whitespace. If not, strip it and add to list
        #Also check that the string is not empty
        #if defendant_name.isspace() == False and len(defendant_name) > 0:
        #    defendant_names.append(defendant_name.strip())

        #Get the defendant attorney on current line
        #defendant_attorney = case_info[i][94:]

        #Check if the defendant_attorney is all whitespace. If not, strip it and add to list
        #Also check that the string is not empty
        #if defendant_attorney.isspace() == False and len(defendant_attorney) > 0:
        #    defendant_attorneys.append(defendant_attorney.strip())

    #As of 13 June 2023, we are no longer collecting names
    #Now put all the info into a temp dict.
    temp_dict['County'] = county
    temp_dict['Cause Number'] = cause_num
    temp_dict['File Date'] = file_date
    temp_dict['Cause of Action'] = coa
    temp_dict['Docket Date'] = docket_date
    temp_dict['Docket Type'] = docket_type
    temp_dict['ANS File'] = ans_date
    temp_dict['CR Number'] = cr_num
    #temp_dict['Plaintiff Name'] = plaintiff_names
    #temp_dict['Plaintiff Attorney'] = plaintiff_attorneys
    #temp_dict['Defendant Name'] = defendant_names
    #temp_dict['Defendant Attorney'] = defendant_attorneys
    
    #Append the temp_dict to the case_list
    case_list.append(temp_dict)
    
    return case_list
    
def build_civil_cases_dataframe(text):
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
    
    #For header. Doesn't have to be perfect, we only need the county name included here
    header = text[:389]

    #Use regex to find the 'AS OF' and 'RAN ON' dates
    #For 'RAN ON' date:
    report_generated_date = re.findall(r"[A-Z]{3,9}\s[0-9]{2},\s[0-9]{4}", header)[0]

    #For 'AS OF' date:
    report_as_of_date = re.findall(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", header)[0]
    
    #Remove headers from all pages
    text = re.sub(r"""[A-Z0-9 ()/]*\n\n\s*[A-Za-z0-9 #,:\n]*DEFENDANT ATTORNEY""",'', text)
    
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
        
        #Remove leading whitespace only
        case = case.lstrip()
        
        #Split on the '/n'
        case_info = case.split('\n')
        
        #Gather the case data
        case_list = extract_civil_case_data(case_info, county)
        
        #Finally, append this dictionary to the container dict
        case_dicts.extend(case_list)

    #How many cases were collected?
    print(f"Collected Data From {len(case_dicts)} Cases.")

    #Create df
    df = pd.DataFrame(case_dicts)

    #Add 'Report Generated Date' and 'Report As Of Date' columns
    df["Report Generated Date"] = report_generated_date

    df["Report As Of Date"] = report_as_of_date
        
    return df


###################################### FOR CRIMINAL CASE PDFS #########################################



def build_criminal_cases_dataframe(text):
    """
    This function takes in the entire PDF document as a string of text. It will gather the info for each case
    and add the info to a dictionary. The dictionary for each case will be added to a list which will be turned into
    a dataframe.
    
    Parameter:
        -text: A string consisting of the text of the entire PDF document.
        
    Returns:
        -df: A dataframe of the newly gathered case info
    """
    
    #Initialize containers
    case_list = []
    #attorney_names = []
    offense_list = []
    st_rpt_list = []
    temp_dict = {}
    
    #Separate the first header from the body
    #We'll use this to identify the county later
    header = text[:500]

    #Use regex to find the 'AS OF' and 'RAN ON' dates
    dates = re.findall(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", header)
    #For 'RAN ON' date:
    report_generated_date = dates[0]

    #For 'AS OF' date:
    report_as_of_date = dates[1]
    
    #Body
    body = text[500:]
    
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
    body = re.sub(r"""\n\x0c\s*[A-Z -]*\d{2}/\d{2}/\d{4}\n\s*\w{6,8}[A-Z0-9 -]*\n\s*[A-Z ]*\d{2}/\d{2}/\d{4}[A-Z0-9 -]*\n\n[A-Z ]*#\s*[A-Z -']*\n[A-Z0-9/ -]*\n\n""", '', body)
    
    #########################################################################################################
    #Now remove the last divider sections using regex
    body = re.sub(r"""\nTOTAL NUMBER OF CASES FILED: [0-9\n-]*MTR-A[A-Z\n ]*[-]*""", '', body)
    
    body = re.sub(r"""\n{0,1}TOTAL NUMBER OF MTR-A FILINGS: [0-9\n-]*ALL OTHER CASES ADDED/APPEALED[\n-]*""", '', body)
    
    body = re.sub(r"""\n{0,1}TOTAL NUMBER OF CASES ADDED/APPEALED: [0-9- a-zA-Z\.#;,:'=\n]*""", '', body)
    
    #########################################################################################################
    
    #Split the text on the '\n' to isolate each case
    cases = body.split('\n')
    
    #Remove cases that happen to be empty or consist of whitespace only
    cases = [case for case in cases if case.isspace() == False and len(case) > 0]
    
    #Loop through each line. Add case info to temp dict, and then add that to the case list
    for line in cases:
        #Check if line is the start of a new case
        if not line[0].isspace():
            #Check if the temp_dict is empty.
            #If not, add temp_dict data to case_list
            if bool(temp_dict) == True:
                #Add list info to temp_dict
                #temp_dict['Attorney'] = attorney_names
                temp_dict['First Offense'] = offense_list
                temp_dict['ST RPT Column'] = st_rpt_list

                #Add temp dict data to case_list
                case_list.append(temp_dict)

            #Reset temp_dict
            temp_dict = {}

            #Reset lists
            #attorney_names = []
            offense_list = []
            st_rpt_list = []

            #Assign county
            temp_dict['County'] = county

            #Gather the cause number
            temp_dict['Cause Number'] = line[:22].strip()

            #Gather the file date
            temp_dict['File Date'] = line[22:34].strip()

            #As of 13 June 2023, we are no longer collecting names
            #Get defendant name
            #temp_dict['Defendant'] = line[34:72].strip()
        
            #Get court
            temp_dict['Court'] = line[72:79].strip()

            #Get docket date
            temp_dict['Docket Date'] = line[79:89].strip()

            #Get outstanding warrants
            temp_dict['Outstanding Warrants'] = line[89:].strip()

            #End of line, so move to next one

        else:
            #As of 13 June 2023, we are no longer collecting names
            
            #Get attorney name
            #attorney_name = line[:35].strip()

            #Check if attorney_name is all whitesapace. If not, strip it and add to names list
            #Also check that the string is not empty
            #if attorney_name.isspace() == False and len(attorney_name) > 0:
            #    attorney_names.append(attorney_name.strip())

            #Get first offense
            offense = line[35:74].strip()

            #Check if offense is all whitesapace. If not, strip it and add to names list
            #Also check that the string is not empty
            if offense.isspace() == False and len(offense) > 0:
                offense_list.append(offense.strip())

            #Get ST RPT Column
            st_rpt = line[74:].strip()

            #Check if st_rpt is all whitesapace. If not, strip it and add to names list
            #Also check that the string is not empty
            if st_rpt.isspace() == False and len(st_rpt) > 0:
                st_rpt_list.append(st_rpt.strip())

            #End of line
        
    #Check that the last case was added to the list
    #If not, add it
    #Add list info to temp_dict
    #temp_dict['Attorney'] = attorney_names
    temp_dict['First Offense'] = offense_list
    temp_dict['ST RPT Column'] = st_rpt_list

    #Add temp dict data to case_list
    case_list.append(temp_dict)

    
    #How many?
    print(f'Collected Data From {len(case_list)} Cases.')
    
    #Create dataframe
    df = pd.DataFrame(case_list)

    #Add 'Report Generated Date' and 'Report As Of Date' columns
    df["Report Generated Date"] = report_generated_date

    df["Report As Of Date"] = report_as_of_date
    
    return df
