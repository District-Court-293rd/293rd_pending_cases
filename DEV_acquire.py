import pandas as pd
import re


def build_dataframe(report_type, content):
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
    if report_type == 'Criminal Disposed':
        df = build_criminal_disposed_cases_dataframe(content)
    elif report_type == 'Civil Disposed':
        df = build_civil_disposed_cases_dataframe(content)
    elif report_type == 'Civil':
        df = build_civil_cases_dataframe(content)
    elif report_type == 'Criminal':
        df = build_criminal_cases_dataframe(content)
    elif report_type == 'Juvenile':
        df = build_juvenile_cases_dataframe(content)
    elif report_type == 'Criminal Inactive':
        df = build_criminal_inactive_cases_dataframe(content)
    elif report_type == 'Civil Inactive':
        df = build_civil_inactive_cases_dataframe(content)
    else:
        #Leave a message
        print("Something Went Wrong! Could not identify the PDF as Criminal, Civil, or Juvenile.")
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
    if (string.count('CV') > 0 or string.count('TX') > 0) and (string.count('TX DFPS') == 0) and (string.count('TX LLC') == 0) and (string.count('SOUTHWEST TX') == 0):
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

    #Add 'Report Generated Date', 'Original As Of Date', 'Last As Of Date', and 'Comments' columns
    df["Report Generated Date"] = report_generated_date
    df["Original As Of Date"] = report_as_of_date
    df["Last As Of Date"] = report_as_of_date
    #Comment column removed as of 10/07/2023
    #df["Comments"] = ''
        
    return df

def build_civil_disposed_cases_dataframe(text):
    """
    This function takes in the entire PDF document as a string of text. It will gather the info for each case
    and add the info to a dictionary. The dictionary for each case will be added to a list which will be turned into
    a dataframe.
    
    Parameter:
        -text: A string consisting of the text of the entire disposed cases PDF document.
        
    Returns:
        -df: A dataframe of the newly gathered disposed case info
    """
    
    #Initialize containers
    #Establish a container list for the dictionaries
    case_list = []
    dispo_dates_list = []
    disposition_list = []
    #coa_list = []
    temp_dict = {}
    
    #Create a var to count the number of disposed dates
    dispo_count = 0
    
    #Get the header and remove surrounding whitespace
    header = text[:420].strip()

    #Get the body and remove surrounding whitespace
    body = text[420:].strip()
    
    #Get the report 'AS OF' date:
    report_as_of_date = re.findall(r"[0-9]{2}/[0-9]{2}/[0-9]{2}", header)[1]
    
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
    #This regex should identify the headers even if some of the info changes later on
    #Can't include the page break in this regex because the formatting is awful
    body = re.sub(r"""\s*[A-Z]{3,9}\s[0-9]{1,2},\s[0-9]{4}\s[a-zA-Z0-9 \n/-]*:[a-zA-Z0-9 \n/-]*:[A-Za-z0-9 \n\./-]*DEFENDANT\s{1,23}\n""", '', body)
    
    #Since the formatting is awful, manually remove the page break symbol '\n\x0c'
    body = body.replace('\n\x0c','')
    
    #Split the text on the \n to isolate each case
    cases = body.split('\n')
    
    #Drop the last two case. They're just the total case counts from the report
    cases.pop()
    cases.pop()
    
    #Remove cases that happen to be empty or consist of whitespace only
    cases = [case for case in cases if case.isspace() == False and len(case) > 0]
    
    for line in cases:
        #Check if line is the start of a new case
        if not line[0].isspace():
            #Check if the temp_dict is empty.
            #If not, add temp_dict data to case_list
            if bool(temp_dict) == True:
                #Save the last date as the case file date
                temp_dict['File Date'] = dispo_dates_list[-1]

                #Now get the length of the list and remove the last date from the dispo dates list
                file_date_starting_line = len(dispo_dates_list)
                dispo_dates_list.pop()
                dispo_count += len(dispo_dates_list)
                
                #Add disposed dates to temp_dict
                temp_dict['Disposed Dates'] = dispo_dates_list

                temp_dict['Dispositions'] = disposition_list[:file_date_starting_line - 1]

                #temp_dict['Causes of Action'] = coa_list[:file_date_starting_line - 1]

                #temp_dict['Plaintiffs'] = disposition_list[file_date_starting_line - 1:]

                #temp_dict['Defendants'] = coa_list[file_date_starting_line - 1:]

                #Add temp dict data to case_list
                case_list.append(temp_dict)

            #Reset temp_dict
            temp_dict = {}

            #Reset lists
            dispo_dates_list = []
            disposition_list = []
            #coa_list = []
            
            temp_dict['County'] = county

            #Gather the cause number
            temp_dict['Cause Number'] = line[:17].strip()

            #Get the first dispo date
            dispo_dates_list.append(line[17:29].strip())

            #Get first disposition
            disposition_list.append(line[29:64].strip())

            #Get first coa
            #coa_list.append(line[64:].strip())

            #End of line, so move to next one

        else:
            #Get additional dispo date
            dispo_date = line[17:29].strip()

            #Check if dispo_date is all whitesapace. If not, strip it and add to list
            #Also check that the string is not empty
            if dispo_date.isspace() == False and len(dispo_date) > 0:
                dispo_dates_list.append(dispo_date.strip())

            #Get additional disposition
            disposition = line[29:64].strip()

            #Check if disposition is all whitesapace. If not, strip it and add to list
            #Also check that the string is not empty
            if disposition.isspace() == False and len(disposition) > 0:
                disposition_list.append(disposition.strip())

            #Get additional coa
            #coa = line[64:].strip()

            #Check if coa is all whitesapace. If not, strip it and add to list
            #Also check that the string is not empty
            #if coa.isspace() == False and len(coa) > 0:
                #coa_list.append(coa.strip())

            #End of line

    #Check that the last case was added to the list
    #If not, add it
    #Save the last date as the case file date
    temp_dict['File Date'] = dispo_dates_list[-1]

    #Now get the length of the list and remove the last date from the dispo dates list
    file_date_starting_line = len(dispo_dates_list)
    dispo_dates_list.pop()
    dispo_count += len(dispo_dates_list)
    
    #Add disposed dates to temp_dict
    temp_dict['Disposed Dates'] = dispo_dates_list

    temp_dict['Dispositions'] = disposition_list[:file_date_starting_line - 1]

    #temp_dict['Causes of Action'] = coa_list[:file_date_starting_line - 1]

    #temp_dict['Plaintiffs'] = disposition_list[file_date_starting_line - 1:]

    #temp_dict['Defendants'] = coa_list[file_date_starting_line - 1:]

    #Add temp dict data to case_list
    case_list.append(temp_dict)
    
    #How many?
    print(f'Collected Data From {len(case_list)} Cases.')
    
    print(f'There were {dispo_count} dispositions.')
    
    #Create dataframe
    df = pd.DataFrame(case_list)
    
    #Add the as of date
    df['Disposed As Of Date'] = report_as_of_date
    
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

    #Add 'Report Generated Date', 'Original As Of Date', 'Last As Of Date', and 'Comments' columns
    df["Report Generated Date"] = report_generated_date
    df["Original As Of Date"] = report_as_of_date
    df["Last As Of Date"] = report_as_of_date
    #Comment column removed as of 10/07/2023
    #df["Comments"] = ''
    
    return df

def build_criminal_disposed_cases_dataframe(text):
    """
    This function takes in the entire PDF document as a string of text. It will gather the info for each case
    and add the info to a dictionary. The dictionary for each case will be added to a list which will be turned into
    a dataframe.
    
    Parameter:
        -text: A string consisting of the text of the entire disposed cases PDF document.
        
    Returns:
        -df: A dataframe of the newly gathered disposed case info
    """
    
    #Initialize containers
    #Establish a container list for the dictionaries
    case_list = []
    dispo_dates_list = []
    disposition_list = []
    temp_dict = {}
    
    #Add a var to count the number of dispositions
    dispo_count = 0
    
    #Get the header and remove surrounding whitespace
    header = text[:420].strip()

    #Get the body and remove surrounding whitespace
    body = text[420:].strip()
    
    #Get the 'AS OF' date:
    report_as_of_date = re.findall(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", header)[1]
    
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
    #This regex should identify the headers even if some of the info changes later on
    body = re.sub(r"""\n\x0c\s*[A-Z]{3,9}\s[0-9]{1,2},\s[0-9]{4}\s[a-zA-Z0-9 \n:/-]*#\s*[A-Z /]*\n\n""", '', body)
    
    #Split the text on the \n to isolate each case
    cases = body.split('\n')
    
    #Drop the last case. It's just the total case count from the report
    cases.pop()
    
    #Remove cases that happen to be empty or consist of whitespace only
    cases = [case for case in cases if case.isspace() == False and len(case) > 0]
    
    #Loop through each line. Add case info to temp dict, and then add that to the case list
    #Most fields are commented out because we don't need that info yet.
    for line in cases:
        #Check if line is the start of a new case
        if not line[0].isspace():
            #Check if the temp_dict is empty.
            #If not, add temp_dict data to case_list
            if bool(temp_dict) == True:
                #Add list info to temp_dict
                temp_dict['Disposed Dates'] = dispo_dates_list
                temp_dict['Dispositions'] = disposition_list
                dispo_count += len(dispo_dates_list)
                
                #Add temp dict data to case_list
                case_list.append(temp_dict)

            #Reset temp_dict
            temp_dict = {}

            #Reset lists
            dispo_dates_list = []
            disposition_list = []
            
            #Assign the county name
            temp_dict['County'] = county

            #Gather the cause number
            temp_dict['Cause Number'] = line[:17].strip()

            #Gather the defendant name
            #temp_dict['Defendant'] = line[17:45].strip()

            #Get first dispo date
            dispo_dates_list.append(line[45:55].strip())

            #Get first disposition
            disposition_list.append(line[55:78].strip())

            #Get complainant
            #temp_dict['Complainant'] = line[78:110].strip()

            #Get bondsman
            #temp_dict['Bondsman'] = line[110:].strip()

            #End of line, so move to next one

        else:
            #Get additional dispo date
            dispo_date = line[45:55].strip()

            #Check if dispo_date is all whitesapace. If not, strip it and add to list
            #Also check that the string is not empty
            if dispo_date.isspace() == False and len(dispo_date) > 0:
                dispo_dates_list.append(dispo_date.strip())

            #Get additional disposition
            disposition = line[55:78].strip()

            #Check if disposition is all whitesapace. If not, strip it and add to list
            #Also check that the string is not empty
            if disposition.isspace() == False and len(disposition) > 0:
                disposition_list.append(disposition.strip())

            #End of line

    #Check that the last case was added to the list
    #If not, add it
    #Add list info to temp_dict
    temp_dict['Disposed Dates'] = dispo_dates_list
    temp_dict['Dispositions'] = disposition_list
    dispo_count += len(dispo_dates_list)
    
    #Add temp dict data to case_list
    case_list.append(temp_dict)
    
    #How many?
    print(f'Collected Data From {len(case_list)} Cases.')
    
    print(f'There were {dispo_count} disposed cases.')
    
    #Create dataframe
    df = pd.DataFrame(case_list)
    
    #Add report as of date
    df['Disposed As Of Date'] = report_as_of_date
    
    return df

def build_juvenile_cases_dataframe(text):
    """
    This function takes in the entire PDF document as a string of text. It will gather the info for each case
    and add the info to a dictionary. The dictionary for each case will be added to a list which will be turned into
    a dataframe.
    
    Parameter:
        -text: A string consisting of the text of the entire juvenile cases PDF document.
        
    Returns:
        -df: A dataframe of the newly gathered juvenile case info
    """
    
    #Initialize containers
    #Establish a container list for the dictionaries
    case_list = []
    offense_list = []
    docket_date_list = []
    dispo_date_list = []
    temp_dict = {}
    
    #Get the header and remove surrounding whitespace
    header = text[:450].strip()

    #Get the body and remove surrounding whitespace
    body = text[450:].strip()
    
    #Get the 'AS OF' date:
    report_as_of_date = re.findall(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", header)[0]
        
    #Set up regex to remove all subsequent headers
    #This regex should identify the headers even if some of the info changes later on
    body = re.sub(r"""\n\x0c\s*[A-Z0-9 \(\)\n/#\:-]*\.\sDATE""", '', body)
    
    #Split the text on the \n to isolate each case
    cases = body.split('\n')
    
    #Drop the last case. It's just the total case count from the report
    cases.pop()
    
    #Remove cases that happen to be empty or consist of whitespace only
    cases = [case for case in cases if case.isspace() == False and len(case) > 0]
    
    #Loop through each line. Add case info to temp dict, and then add that to the case list
    #Some fields are commented out because we don't need that info yet.
    for line in cases:
        if line.isspace() or len(line) == 0:
            continue

        #Check if line is the start of a new case
        if not line[0].isspace():
            #Check if the temp_dict is empty.
            #If not, add temp_dict data to case_list
            if bool(temp_dict) == True:
                #Add list info to temp_dict
                temp_dict['Offense'] = offense_list
                temp_dict['Docket Date'] = docket_date_list
                temp_dict['Disposed Dates'] = dispo_date_list

                #Add temp dict data to case_list
                case_list.append(temp_dict)

            #Reset temp_dict
            temp_dict = {}

            #Reset lists
            offense_list = []
            docket_date_list = []
            dispo_date_list = []

            #Gather the cause number
            temp_dict['Cause Number'] = line[9:26].strip()

            #Gather the file date
            temp_dict['File Date'] = line[26:38].strip()

            #Get court
            #temp_dict['Court'] = line[38:70].strip()

            #Get respondent
            #temp_dict['Respondent'] = line[70:].strip()

            #End of line, so move to next one

        else:
            #Get offenses
            offense = line[5:88].strip()

            #Check if offense is all whitesapace. If not, strip it and add to list
            #Also check that the string is not empty
            if offense.isspace() == False and len(offense) > 0:
                offense_list.append(offense.strip())

            #Get Docket Date
            docket_date = line[88:98].strip()

            #Check if offense is all whitesapace. If not, strip it and add to list
            #Also check that the string is not empty
            if docket_date.isspace() == False and len(docket_date) > 0:
                docket_date_list.append(docket_date.strip())

            #Get Disposition Date
            dispo_date = line[98:].strip()

            #Check if offense is all whitesapace. If not, strip it and add to list
            #Also check that the string is not empty
            if dispo_date.isspace() == False and len(dispo_date) > 0:
                dispo_date_list.append(dispo_date.strip())

            #End of line
        
    #Check that the last case was added to the list
    #Add list info to temp_dict
    temp_dict['Offense'] = offense_list
    temp_dict['Docket Date'] = docket_date_list
    temp_dict['Disposed Dates'] = dispo_date_list

    #Add temp dict data to case_list
    case_list.append(temp_dict)
    
    #How many?
    print(f'Collected Data From {len(case_list)} Cases.')
    
    #Create dataframe
    df = pd.DataFrame(case_list)
    
    #Add report as of date
    df["Original As Of Date"] = report_as_of_date
    df["Last As Of Date"] = report_as_of_date
    df["Report Generated Date"] = report_as_of_date
    df["Disposed As Of Date"] = report_as_of_date
    
    return df

def build_civil_inactive_cases_dataframe(text):
    """
    This function takes in the entire PDF document as a string of text. It will gather the info for each case
    and add the info to a dictionary. The dictionary for each case will be added to a list which will be turned into
    a dataframe.
    
    Parameter:
        -text: A string consisting of the text of the entire inactive cases PDF document.
        
    Returns:
        -df: A dataframe of the newly gathered inactive case info
    """
    
    #Initialize containers
    case_list = []
    inactive_start_list = []
    inactive_end_list = []
    inactive_reason_list = []
    temp_dict = {}
    
    #Separate the first header from the body
    #We'll use this to identify the county later
    header = text[:370]

    #Use regex to find the 'AS OF' and 'RAN ON' dates
    dates = re.findall(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", header)

    #For 'AS OF' date:
    report_as_of_date = dates[1]
    
    #For county, check the name at the beginning of the header
    if header.count('LEOPOLDO VIELMA') >= 1:
        county = 'Maverick'
    elif header.count('MARICELA G. GONZALEZ') >= 1:
        county = 'Dimmit'
    elif header.count('RACHEL P. RAMIREZ') >= 1:
        county = 'Zavala'
    else:
        county = 'Unknown'
    
    #Body
    body = text[370:]
    
    #Remove subsequent page headers
    body = re.sub(r"""\s*[A-Z\.\' \n-]*\d{2}/\d{2}/\d{4}\n\s*[A-Z0-9 \:-]*\d{2}/\d{2}/\d{4}[A-Z0-9 \n#-]*INACTIVE REASON\s*\n\n""", '', body)
    
    #Split the text on the '\n' to isolate each case
    cases = body.split('\n')
    
    #Remove cases that happen to be empty or consist of whitespace only
    cases = [case for case in cases if case.isspace() == False and len(case) > 0]
    
    #Check the case count
    num_cases = cases.pop()
    num_cases = num_cases[19:].strip()
    
    #If there are zero inactive cases on the report, return
    if num_cases == '0':
        return pd.DataFrame()
    
    for case in cases:
        #Check to see if this line is the start of a new case
        if case[:35].isspace() == False:
            #Check if the temp_dict is empty
            if bool(temp_dict) == True:
                #Reverse the lists so that the newest dates appear first
                temp_dict['Inactive Start Date'] = inactive_start_list.reverse()
                temp_dict['Inactive End Date'] = inactive_end_list.reverse()
                temp_dict['Inactive Reason'] = inactive_reason_list.reverse()
                
                case_list.append(temp_dict)
                
            #Reset temp_dict and lists
            temp_dict = {}
            inactive_start_list = []
            inactive_end_list = []
            inactive_reason_list = []
            
            #Assign county
            temp_dict['County'] = county

            #Gather the cause number
            temp_dict['Cause Number'] = case[:27].strip()

            #Gather the file date
            temp_dict['File Date'] = case[27:44].strip()

            #Get inactive start date
            inactive_start_list.append(case[44:54].strip())

            #Get inactive end date
            inactive_end_list.append(case[54:73].strip())

            #Assign Status
            temp_dict['Status'] = 'Inactive'
            
            #Assign Case Type
            temp_dict['Case Type'] = 'Civil'

            #Get inactive reason
            inactive_reason_list.append(case[73:].strip())

            #End of line, so move to next one
            
        else:
            #This line is a continuation of the same case
            #Just grab the start and end dates
            #As well as the reason
            #Get inactive start date
            inactive_start_list.append(case[44:54].strip())

            #Get inactive end date
            inactive_end_list.append(case[54:73].strip())

            #Get inactive reason
            inactive_reason_list.append(case[73:].strip())
            
    #Make sure the last case gets added
    if bool(temp_dict) == True:
        temp_dict['Inactive Start Date'] = inactive_start_list.reverse()
        temp_dict['Inactive End Date'] = inactive_end_list.reverse()
        temp_dict['Inactive Reason'] = inactive_reason_list.reverse()

        case_list.append(temp_dict)
    
    #How many?
    print(f'Collected Data From {len(case_list)} Cases.')
    
    #Create dataframe
    df = pd.DataFrame(case_list)

    #Add 'Original As Of Date', 'Last As Of Date', and 'Estimated Inactive End Date' columns
    df["Original As Of Date"] = report_as_of_date
    df["Estimated Inactive End Date"] = ''
    df["Last As Of Date"] = report_as_of_date
    
    return df

def build_criminal_inactive_cases_dataframe(text):
    """
    This function takes in the entire PDF document as a string of text. It will gather the info for each case
    and add the info to a dictionary. The dictionary for each case will be added to a list which will be turned into
    a dataframe.
    
    Parameter:
        -text: A string consisting of the text of the entire inactive criminal cases PDF document.
        
    Returns:
        -df: A dataframe of the newly gathered inactive criminal case info
    """
    
    #Initialize containers
    case_list = []
    inactive_start_list = []
    inactive_end_list = []
    inactive_reason_list = []
    temp_dict = {}
    
    #Separate the first header from the body
    #We'll use this to identify the county later
    header = text[:370]

    #Use regex to find the 'AS OF' and 'RAN ON' dates
    dates = re.findall(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", header)

    #For 'AS OF' date:
    report_as_of_date = dates[1]
    
    #For county, check the name at the beginning of the header
    if header.count('LEOPOLDO VIELMA') >= 1:
        county = 'Maverick'
    elif header.count('MARICELA G. GONZALEZ') >= 1:
        county = 'Dimmit'
    elif header.count('RACHEL P. RAMIREZ') >= 1:
        county = 'Zavala'
    else:
        county = 'Unknown'
    
    #Body
    body = text[368:]
    
    #Remove all subsequent headers with regex
    body = re.sub(r"""\n\x0c\s*[A-Z\.\' \n-]*\d{2}/\d{2}/\d{4}\n\s*[A-Z0-9 \:-]*\d{2}/\d{2}/\d{4}[A-Z0-9 \n#-]*STATE REPORT COLUMN\n\n""", '', body)
    
    #Split the text on the '\n' to isolate each case
    cases = body.split('\n')
    
    #Remove cases that happen to be empty or consist of whitespace only
    cases = [case for case in cases if case.isspace() == False and len(case) > 0]
    
    #Check the case count
    num_cases = cases.pop()
    num_cases = num_cases[19:].strip()
    
    #If there are zero inactive cases on the report, return
    if num_cases == '0':
        return pd.DataFrame()
    
    for case in cases:
        #Check to see if this line is the start of a new case
        if case[:35].isspace() == False:
            #Check if the temp_dict is empty
            if bool(temp_dict) == True:
                #Reverse the lists so that the newest dates appear first
                temp_dict['Inactive Start Date'] = inactive_start_list.reverse()
                temp_dict['Inactive End Date'] = inactive_end_list.reverse()
                temp_dict['Inactive Reason'] = inactive_reason_list.reverse()
                
                case_list.append(temp_dict)
                
            #Reset temp_dict and lists
            temp_dict = {}
            inactive_start_list = []
            inactive_end_list = []
            inactive_reason_list = []
            
            #Assign county
            temp_dict['County'] = county

            #Gather the cause number
            temp_dict['Cause Number'] = case[:24].strip()

            #Gather the file date
            temp_dict['File Date'] = case[24:36].strip()

            #Get inactive start date
            inactive_start_list.append(case[36:49].strip())

            #Get inactive end date
            inactive_end_list.append(case[49:61].strip())

            #Assign Status
            temp_dict['Status'] = 'Inactive'
            
            #Assign Case Type
            temp_dict['Case Type'] = 'Criminal'

            #Get inactive reason
            inactive_reason_list.append(case[61:93].strip())
            
            #Get State Report
            temp_dict['State Report'] = case[93:].strip()

            #End of line, so move to next one
            
        else:
            #This line is a continuation of the same case
            #Just grab the start and end dates
            #As well as the reason
            #Get inactive start date
            inactive_start_list.append(case[36:49].strip())

            #Get inactive end date
            inactive_end_list.append(case[49:61].strip())

            #Get inactive reason
            inactive_reason_list.append(case[61:93].strip())
            
    #Make sure the last case gets added
    if bool(temp_dict) == True:
        temp_dict['Inactive Start Date'] = inactive_start_list.reverse()
        temp_dict['Inactive End Date'] = inactive_end_list.reverse()
        temp_dict['Inactive Reason'] = inactive_reason_list.reverse()

        case_list.append(temp_dict)
    
    #How many?
    print(f'Collected Data From {len(case_list)} Cases.')
    
    #Create dataframe
    df = pd.DataFrame(case_list)

    #Add 'Original As Of Date', 'Last As Of Date', and 'Estimated Inactive End Date' columns
    df["Original As Of Date"] = report_as_of_date
    df["Estimated Inactive End Date"] = ''
    df["Last As Of Date"] = report_as_of_date
    
    return df