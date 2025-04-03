import streamlit as st
import pandas as pd
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
from datetime import date
import io
import os
import DEV_pending_upload
import gspread
import streamlit_authenticator as stauth
from pathlib import Path
import re


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

def get_file_content(file_name):
    """
    This function takes in the file data returned by the streamlit file uploader. It will
    read and return the text content of the file using pdfminer3. The text content will
    be used in a following function for dataframe creation/prep.
    """
    #Set up resource manager to handle pdf content. text, images, etc.
    resource_manager = PDFResourceManager()

    #Used to display text
    fake_file_handle = io.StringIO()

    #Set up converter
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())

    #Set up page interpreter
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    with open(file_name, 'rb') as fh:

        for page in PDFPage.get_pages(fh,
                                    caching=True,
                                    check_extractable=True):
            page_interpreter.process_page(page)

        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()

    return text

def get_spreadsheet_data(sheet_name, credentials):
    """
    This function will read the Pending Reports spreadsheet and return the data from the sheet of the
    given sheet_name. It uses the credentials to allow access to the google spreadsheet.
    """

    #Set up credentials to interact with Google Sheets
    gc = gspread.service_account_from_dict(credentials)
    
    #Open 'Pending Reports' Google Sheet By Name
    gsheet = gc.open('Pending Reports')
    
    #Access cases on the given tab
    data_sheet = gsheet.worksheet(sheet_name)

    #Load the data currently on the given tab in the 'Pending Reports' spreadsheet
    df = pd.DataFrame(data_sheet.get_all_records())

    return df

def convert_datetime_format(datetime):
    """
    This function takes in a datetime value in YYYY-MM-DD HH:mm format and converts it to a string
    in this format: MM/DD/YYYY at HH:MM.

    Paramters:
        - datetime: A string representing the date and time in YYYY-MM-DD HH:mm format

    Returns:
        - string: A string in MM/DD/YYYY at HH:MM format
    """

    datetime = datetime.replace('-', '/')
    year = datetime[:4]
    month_and_day = datetime[5:10]
    new_date = month_and_day + '/' + year

    #Convert time to civilian time
    original_time = datetime[-5:]
    hour = original_time[:2]

    if hour == '00':
        hour = '12'
        meridiem = 'AM'
    elif hour == '12':
        meridiem = 'PM'
    elif int(hour) > 12:
        hour = str(int(hour) - 12)
        meridiem = 'PM'
    else:
        meridiem = 'AM'

    new_time = hour + original_time[2:] + ' ' + meridiem
    
    #Put them together and return the string
    return new_date + ' at ' + new_time

def convert_as_of_date_format(as_of_date):
    """
    This function will transform the as_of_date format from 'MM/DD/YYYY' to 'YYYYMMDD'.
    It is needed in order to always pull the correct max date when dealing with more than one year.
    Currently, the 'MM/DD/YYYY' format is not working as expected with the max() function.

    Note: Some as_of_dates are in 'MM/DD/YY' format. Check for these and convert as needed.

    Parameter:
        - as_of_date: A string representing the latest as of date in the 'MM/DD/YYYY' format

    Returns:
        - new_date: A new string representing the latest as of date in the 'YYYYMMDD' format
    """

    #First check if date is in 'MM/DD/YY' format
    if len(as_of_date) == 8:
        #Fill in the rest of the year
        as_of_date = as_of_date[:6] + '20' + as_of_date[6:]
    
    year = as_of_date[-4:]
    month = as_of_date[:2]
    day = as_of_date[3:5]

    new_date = year + month + day

    return new_date

def reverse_as_of_date_format(as_of_date):
    """
    This function will transform the as_of_date format from 'YYYYMMDD' to 'MM/DD/YYYY'.
    It is needed to make the date easier to read when displayed in the streamlit app sidebar.

    Parameter:
        - as_of_date: A string representing the latest as of date in the 'YYYYMMDD' format
    
    Returns:
        - new_date: A string representing the latest as of date in the 'MM/DD/YYYY' format
    """

    year = as_of_date[:4]
    month = as_of_date[4:6]
    day = as_of_date[6:]

    new_date = month + '/' + day + '/' + year

    return new_date

def check_report_requirements(county, report_type, is_293rd, as_of_date, last_as_of_dict):
    """
    This function takes in several pieces of information found in the report header and verifies it all meets the requirements before allowing the report to be processed.
    This will minimize future issues with the data and hopefully reduce the number of errors overall.

    Parameters:
        - county: A string representing the name of the county found in the header
        - report_type: A string representing the type of report based on the header info (criminal, civil, etc.)
        - is_293rd: A boolean representing whether or not the report is for the 293rd court district specifically
        - as_of_date: A string representing the as of date found in the header
        - last_as_of_dict: A dictionary containing the last as of date for each county and report type found in the common table

    Returns:
        - report_meets_requirements: A boolean indicating whether or not the report can be processed
    """

    #Assume report meets requirements until proven otherwise
    report_meets_requirements = True

    #If any of the information is unknown, the report fails.
    if county == 'Unknown':
        st.error("Could Not Identify County")
        report_meets_requirements = False
    if report_type == 'Unknown':
        st.error("Could Not Identify the Report Type")
        report_meets_requirements = False
    if is_293rd == False:
        st.error("Report Is Not Specific to the 293rd District Court")
        report_meets_requirements = False
    if as_of_date == 'Unknown':
        st.error("Could Not Identify the Report As Of Date")
        report_meets_requirements = False
    
    #If any of the above check failed, return false
    if report_meets_requirements == False:
        return report_meets_requirements
    
    #Get the corresponding last as of date from the common table
    if report_type == 'Juvenile':
        common_table_last_as_of_date = last_as_of_dict['Juvenile']
    elif report_type == 'Civil Disposed':
        common_table_last_as_of_date = last_as_of_dict['Civil'][county]
    elif report_type == 'Criminal Disposed':
        common_table_last_as_of_date = last_as_of_dict['Criminal'][county]
    else:
        common_table_last_as_of_date = last_as_of_dict[report_type][county]

    #If common table as of date is empty, set to all 0's
    if len(common_table_last_as_of_date) == 0:
        common_table_last_as_of_date = '00000000'
    
    #Convert the report as of date to a usable format
    as_of_date = convert_as_of_date_format(as_of_date)

    #Check that the as of date is greater than or equal to the last of date found in the common table
    if as_of_date < common_table_last_as_of_date:
        st.error("The Report As Of Date Must Be Greater Than Or Equal to the Last As Of Date For That Report Type and County")
        report_meets_requirements = False
    
    return report_meets_requirements

############################################## Begin App ##################################################

st.set_page_config(
     page_title="DEV Pending Reports",
 )

#Gather the most recent 'As Of' and 'Load' dates for each section
common_df = get_spreadsheet_data("DEV_Common_Table", credentials)

if len(common_df) > 0:
    #Verify the columns are string types. Google sheets can mess with the data types
    common_df['Last As Of Date'] = common_df['Last As Of Date'].astype(str).str.strip()
    common_df['Load DateTime'] = common_df['Load DateTime'].astype(str).str.strip()
    common_df['County'] = common_df['County'].astype(str).str.strip()
    common_df['Case Type'] = common_df['Case Type'].astype(str).str.strip()

    #Convert 'Last As Of Date' to YYYYMMDD format so that the max() function works properly.
    common_df['Last As Of Date'] = common_df['Last As Of Date'].apply(convert_as_of_date_format)

    dimmit_civil_last_as_of_date = common_df[(common_df['County'] == 'Dimmit') & (common_df['Case Type'] != 'Criminal') & (common_df['Case Type'] != 'Juvenile')]['Last As Of Date'].max()
    dimmit_civil_last_load_date = common_df[(common_df['County'] == 'Dimmit') & (common_df['Case Type'] != 'Criminal') & (common_df['Case Type'] != 'Juvenile')]['Load DateTime'].max()[:16]
    dimmit_criminal_last_as_of_date = common_df[(common_df['County'] == 'Dimmit') & (common_df['Case Type'] == 'Criminal')]['Last As Of Date'].max()
    dimmit_criminal_last_load_date = common_df[(common_df['County'] == 'Dimmit') & (common_df['Case Type'] == 'Criminal')]['Load DateTime'].max()[:16]
    maverick_civil_last_as_of_date = common_df[(common_df['County'] == 'Maverick') & (common_df['Case Type'] != 'Criminal') & (common_df['Case Type'] != 'Juvenile')]['Last As Of Date'].max()
    maverick_civil_last_load_date = common_df[(common_df['County'] == 'Maverick') & (common_df['Case Type'] != 'Criminal') & (common_df['Case Type'] != 'Juvenile')]['Load DateTime'].max()[:16]
    maverick_criminal_last_as_of_date = common_df[(common_df['County'] == 'Maverick') & (common_df['Case Type'] == 'Criminal')]['Last As Of Date'].max()
    maverick_criminal_last_load_date = common_df[(common_df['County'] == 'Maverick') & (common_df['Case Type'] == 'Criminal')]['Load DateTime'].max()[:16]
    zavala_civil_last_as_of_date = common_df[(common_df['County'] == 'Zavala') & (common_df['Case Type'] != 'Criminal') & (common_df['Case Type'] != 'Juvenile')]['Last As Of Date'].max()
    zavala_civil_last_load_date = common_df[(common_df['County'] == 'Zavala') & (common_df['Case Type'] != 'Criminal') & (common_df['Case Type'] != 'Juvenile')]['Load DateTime'].max()[:16]
    zavala_criminal_last_as_of_date = common_df[(common_df['County'] == 'Zavala') & (common_df['Case Type'] == 'Criminal')]['Last As Of Date'].max()
    zavala_criminal_last_load_date = common_df[(common_df['County'] == 'Zavala') & (common_df['Case Type'] == 'Criminal')]['Load DateTime'].max()[:16]
    juvenile_last_as_of_date = common_df[common_df['Case Type'] == 'Juvenile']['Last As Of Date'].max()
    juvenile_last_load_date = common_df[common_df['Case Type'] == 'Juvenile']['Load DateTime'].max()[:16]

    #Create a dictionary that we can use to store the last as of date for each county and report type
    last_as_of_dict = {
        'Civil': {
            'Dimmit': dimmit_civil_last_as_of_date,
            'Maverick': maverick_civil_last_as_of_date,
            'Zavala': zavala_civil_last_as_of_date
        },
        'Criminal': {
            'Dimmit': dimmit_criminal_last_as_of_date,
            'Maverick': maverick_criminal_last_as_of_date,
            'Zavala': zavala_criminal_last_as_of_date
        },
        'Juvenile': juvenile_last_as_of_date
    }

    #Create a list to find the max as of date
    as_of_date_list = [dimmit_civil_last_as_of_date,
                        dimmit_criminal_last_as_of_date,
                        maverick_civil_last_as_of_date,
                        maverick_criminal_last_as_of_date,
                        zavala_civil_last_as_of_date,
                        zavala_criminal_last_as_of_date,
                        juvenile_last_as_of_date]
    
    max_as_of_date = max(as_of_date_list)

    missing_report_container = st.empty()
    with missing_report_container.container():
        if dimmit_civil_last_as_of_date != max_as_of_date:
            st.info("Report Missing - Please Upload a Dimmit Civil Report with an As Of Date = " + reverse_as_of_date_format(max_as_of_date))
        if dimmit_criminal_last_as_of_date != max_as_of_date:
            st.info("Report Missing - Please Upload a Dimmit Criminal Report with an As Of Date = " + reverse_as_of_date_format(max_as_of_date))
        if maverick_civil_last_as_of_date != max_as_of_date:
            st.info("Report Missing - Please Upload a Maverick Civil Report with an As Of Date = " + reverse_as_of_date_format(max_as_of_date))
        if maverick_criminal_last_as_of_date != max_as_of_date:
            st.info("Report Missing - Please Upload a Maverick Criminal Report with an As Of Date = " + reverse_as_of_date_format(max_as_of_date))
        if zavala_civil_last_as_of_date != max_as_of_date:
            st.info("Report Missing - Please Upload a Zavala Civil Report with an As Of Date = " + reverse_as_of_date_format(max_as_of_date))
        if zavala_criminal_last_as_of_date != max_as_of_date:
            st.info("Report Missing - Please Upload a Zavala Criminal Report with an As Of Date = " + reverse_as_of_date_format(max_as_of_date))
        if juvenile_last_as_of_date != max_as_of_date:
            st.info("Report Missing - Please Upload a Juvenile Report with an As Of Date = " + reverse_as_of_date_format(max_as_of_date))

    #Create a sidebar to display the most recent 'As Of' and 'Load' dates for each section
    with st.sidebar:
        sidebar_container = st.empty()
        with sidebar_container.container():
            st.subheader("Dimmit Civil Cases")
            st.write("Latest As Of Date: " + reverse_as_of_date_format(dimmit_civil_last_as_of_date))
            st.write("Latest Load Date: " + convert_datetime_format(dimmit_civil_last_load_date))
            st.divider()
            st.subheader("Dimmit Criminal Cases")
            st.write("Latest As Of Date: " + reverse_as_of_date_format(dimmit_criminal_last_as_of_date))
            st.write("Latest Load Date: " + convert_datetime_format(dimmit_criminal_last_load_date))
            st.divider()
            st.subheader("Maverick Civil Cases")
            st.write("Latest As Of Date: " + reverse_as_of_date_format(maverick_civil_last_as_of_date))
            st.write("Latest Load Date: " + convert_datetime_format(maverick_civil_last_load_date))
            st.divider()
            st.subheader("Maverick Criminal Cases")
            st.write("Latest As Of Date: " + reverse_as_of_date_format(maverick_criminal_last_as_of_date))
            st.write("Latest Load Date: " + convert_datetime_format(maverick_civil_last_load_date))
            st.divider()
            st.subheader("Zavala Civil Cases")
            st.write("Latest As Of Date: " + reverse_as_of_date_format(zavala_civil_last_as_of_date))
            st.write("Latest Load Date: " + convert_datetime_format(zavala_civil_last_load_date))
            st.divider()
            st.subheader("Zavala Criminal Cases")
            st.write("Latest As Of Date: " + reverse_as_of_date_format(zavala_criminal_last_as_of_date))
            st.write("Latest Load Date: " + convert_datetime_format(zavala_criminal_last_load_date))
            st.divider()
            st.subheader("Juvenile Cases")
            st.write("Latest As Of Date: " + reverse_as_of_date_format(juvenile_last_as_of_date))
            st.write("Latest Load Date: " + convert_datetime_format(juvenile_last_load_date))
            st.divider()
else:
    #Create a dictionary that we can use to store the last as of date for each county and report type
    last_as_of_dict = {
        'Civil': {
            'Dimmit': '00000000',
            'Maverick': '00000000',
            'Zavala': '00000000'
        },
        'Criminal': {
            'Dimmit': '00000000',
            'Maverick': '00000000',
            'Zavala': '00000000'
        },
        'Juvenile': '00000000'
    }

#Create a placeholder for the page content
page_content = st.empty()

#Create container for update page content
with page_content.container():

    #Title
    st.title("Update Pending Reports")

    with st.form("my-form", clear_on_submit = True):
        file_objects = st.file_uploader("File Names Must Include Either 'CV' or 'CR' for Civil and Criminal Cases, Respectively.", type = 'pdf', accept_multiple_files = True)
        submitted = st.form_submit_button("Upload")

    if submitted and len(file_objects) > 0:
        #Give message for successful upload and begin processing
        st.write("Files Uploaded!")

        #Create a container for the progress bar message
        progress_message_container = st.empty()
        #Create a progress bar for visual verification that something is happening
        progress_message_container.header("Please Wait, Collecting File Information:")
        progress_bar = st.progress(0)

        #Use the remainder of 100 / the number of uploaded files to start the progress bar
        bar_value = int(100 % len(file_objects))

        #Update progress bar
        progress_bar.progress(bar_value)

        #How much progress should be made per file?
        progress_per_file = int((100 - bar_value) / len(file_objects))

        #Also create a container for the info messages
        info_container = st.empty()

        #Use a loop to create a dictionary for each uploaded report
        #Tell the user what's happening
        info_container.info("Collecting File Information...")

        #Create list to hold each dictionary
        report_list = []

        for file_object in file_objects:
            if file_object is not None:

                #Save the file. Will be deleted after data is uploaded
                with open(file_object.name, 'wb') as f:
                    f.write(file_object.getbuffer())

                #Create content container
                content = get_file_content(file_object.name)

                #Run preprocessing checks
                header = content[:500]

                #What county is this? This won't work for Inactive reports
                if header.count('MAVERICK') >= 1:
                    county = 'Maverick'
                elif header.count('DIMMIT') >= 1:
                    county = 'Dimmit'
                elif header.count('ZAVALA') >= 1:
                    county = 'Zavala'
                elif header.count('ALL COUNTIES') >= 1:
                    county = 'All Counties'
                else:
                    county = 'Unknown'

                #What type of report is this?
                if header.count('CRIMINAL DETAILED PENDING CASES') >= 1:
                    report_type = 'Criminal'
                elif header.count('CIVIL PENDING CASES') >= 1:
                    report_type = 'Civil'
                elif header.count('JUVENILE CASE FILINGS') >= 1:
                    report_type = 'Juvenile'
                elif header.count('CIVIL DISPOSED CASES') >= 1:
                    report_type = 'Civil Disposed'
                elif header.count('CASES DISPOSED') >= 1:
                    report_type = 'Criminal Disposed'
                elif header.count('PENDING CRIMINAL CASES - INACTIVITY REPORT') >= 1:
                    report_type = 'Criminal Inactive'
                elif header.count('PENDING CIVIL CASES - INACTIVITY REPORT') >= 1:
                    report_type = 'Civil Inactive'
                else:
                    report_type = 'Unknown'

                #Is this only for 293rd district court? The Or Statement is for the civil disposed cases report.
                #The inactive report does not indicate which court it is, so will default to False
                if header.count('293RD DISTRICT COURT') >= 1 or header.count('COURT: 293') >= 1:
                    is_293rd = True
                else:
                    is_293rd = False

                #For Inactive report county, check the name at the beginning of the header
                #If the name matches properly, it should be a 293rd district case
                if report_type == 'Criminal Inactive' or report_type == 'Civil Inactive':
                    if header.count('LEOPOLDO VIELMA') >= 1:
                        county = 'Maverick'
                        is_293rd = True
                    elif header.count('MARICELA G. GONZALEZ') >= 1:
                        county = 'Dimmit'
                        is_293rd = True
                    elif header.count('RACHEL P. RAMIREZ') >= 1:
                        county = 'Zavala'
                        is_293rd = True
                    else:
                        county = 'Unknown'
                        is_293rd = False
                
                #What is the as of date for this report?
                if report_type == 'Criminal':
                    as_of_date = re.findall(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", header)[1]
                elif report_type == 'Civil':
                    as_of_date = re.findall(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", header)[0]
                elif report_type == 'Juvenile':
                    as_of_date = re.findall(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", header)[0]
                elif report_type == 'Criminal Disposed':
                    as_of_date = re.findall(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", header)[1]
                elif report_type == 'Civil Disposed':
                    as_of_date = re.findall(r"[0-9]{2}/[0-9]{2}/[0-9]{2}", header)[1]
                elif report_type == 'Criminal Inactive':
                    as_of_date = re.findall(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", header)[1]
                elif report_type == 'Civil Inactive':
                    as_of_date = re.findall(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", header)[1]
                else:
                    as_of_date = 'Unknown'

                #Create the dictionary
                temp_dict = {
                    'File Name': file_object.name,
                    'County': county,
                    'Report Type': report_type,
                    'Is 293rd': is_293rd,
                    'As Of Date': as_of_date,
                    'Content': content
                }

                #Append temp_dict to report_list
                report_list.append(temp_dict)

                #Delete the file and continue to the next
                if os.path.exists(file_object.name):
                    os.remove(file_object.name)
                
            else:
                #Print an error message
                st.error("A File Was Not Uploaded Correctly. Please Try Again")

        #Tell the user we have started the batch checks
        progress_message_container.empty()
        progress_message_container.header("Please Wait, Running Batch Checks:")        
        
        info_container.empty()
        info_container.info("Checking As Of Dates For Each Report...")

        #Verify all reports have the same as of date
        for i in range(1, len(report_list)):
            if convert_as_of_date_format(report_list[0]['As Of Date']) != convert_as_of_date_format(report_list[i]['As Of Date']):
                info_container.empty()
                progress_message_container.empty()
                progress_message_container.header("Error: Please verify the As Of Date is the same for each report and try again.")
                st.error("Report As Of Dates Must All Match. One or more report's as of date is not the same as the others.")
                st.stop()
        
        success_container = st.empty()
        success_container.success("All Report Dates Match")

        info_container.empty()
        info_container.info("Checking For Correct As Of Dates...")

        #Once the user updates a report, do not let them update that report again until all other reports are at the same As Of Date
        #Logically, we can check this by counting the number of unique As Of Date values.
        #If there are more than 2, then send an error message and stop processing
        as_of_date_list.append(convert_as_of_date_format(report_list[0]['As Of Date']))
        if len(set(as_of_date_list)) > 2:
            info_container.empty()
            progress_message_container.empty()
            progress_message_container.header("Error: A Report's As Of Date Is Greater Than The Allowed Maximum As Of Date.")
            st.error("All Reports Must Be Updated To " + reverse_as_of_date_format(max_as_of_date) + " Before Updating To " + reverse_as_of_date_format(as_of_date_list[-1]) + ". Please Try Again.")
            st.stop()

        success_container = st.empty()
        success_container.success("All Report As Of Dates Are Allowed")
        
        info_container.empty()
        info_container.info("Checking For Duplicate Reports...")

        #Convert the list to a dataframe and check for duplicates.
        #No duplicate combinations of county and report type are allowed.
        #The only exception applies to the inactivity reports. Theres no way to tell with them
        report_df = pd.DataFrame(report_list)

        duplicate_reports = report_df[report_df.duplicated(['County', 'Report Type'], keep = False)]
        if len(duplicate_reports[duplicate_reports['Report Type'] != 'Inactive']) > 0:
            info_container.empty()
            progress_message_container.empty()
            progress_message_container.header("Error: At least one duplicate report found. Please add the correct report and try again.")
            st.error("Duplicate Report Found. Only One Report Per County and Report Type Is Allowed.")
            st.write(duplicate_reports[['File Name', 'County', 'Report Type', 'As Of Date']])
            st.stop()
        
        success_container.success("No Duplicate Reports Found")

        #Update progress message
        progress_message_container.empty()
        progress_message_container.header("Batch Checks Complete. Now Processing Reports:")  

        #Use a for loop to iterate through the uploaded files
        for report in report_list:
            if report['Report Type'] != 'Criminal Inactive' and report['Report Type'] != 'Civil Inactive':

                #Inform the user which file is being processed
                info_container.info("Verifying " + report['File Name'] + " meets report requirements...")

                #Check if report meets requirements
                report_meets_requirements = check_report_requirements(report['County'], report['Report Type'], report['Is 293rd'], report['As Of Date'], last_as_of_dict)

                #If report passes requirements check, build and prepare the dataframe, then update the spreadsheet
                if report_meets_requirements == True:
                    info_container.empty()
                    info_container.info("Began Processing " + report['File Name'])
                    DEV_pending_upload.update_spreadsheet(report['Report Type'], report['Content'])
                else:
                    st.error(report['File Name'] + " Did Not Meet Requirements and Will Not Be Processed. Please double check it is the correct version and date.")
                    info_container.empty()
                    #Update progress bar regardless of whether or not Pending Reports was successfully updated with the current file
                    bar_value += progress_per_file
                    progress_bar.progress(bar_value)
                    continue

                #Leave a success message
                success_container.empty()
                st.success("Pending Reports was successfully updated with " + report['File Name'])

                #Clear container
                info_container.empty()

                #Update progress bar regardless of whether or not Pending Reports was successfully updated with the current file
                bar_value += progress_per_file
                progress_bar.progress(bar_value)
            
            elif report['Report Type'] == 'Criminal Inactive' or report['Report Type'] == 'Civil Inactive':
                #Inform the user which file is being processed
                info_container.info("Processing Inactivity Report: " + report['File Name'])

                if report['County'] == 'Unknown':
                    st.error("Could not identify county for Inactivity Report: " + report['File Name'])
                    st.error("Skipping this file...")
                    #Clear container
                    info_container.empty()
                    #Update progress bar regardless of whether or not Pending Reports was successfully updated with the current file
                    bar_value += progress_per_file
                    progress_bar.progress(bar_value)
                    continue

                #Now process the report and update the spreadsheet
                DEV_pending_upload.update_spreadsheet(report['Report Type'], report['Content'])

                #Leave a success message
                success_container.empty()
                st.success("Pending Reports was successfully updated with " + report['File Name'])

                #Clear container
                info_container.empty()

                #Update progress bar regardless of whether or not Pending Reports was successfully updated with the current file
                bar_value += progress_per_file
                progress_bar.progress(bar_value)

        #Update message
        progress_message_container.header("Complete! All Accepted Files Processed Successfully!")

        #Gather the most recent 'As Of' and 'Load' dates for each section
        common_df = get_spreadsheet_data("DEV_Common_Table", credentials)

        if len(common_df) > 0:
            #Verify the columns are string types. Google sheets can mess with the data types
            common_df['Last As Of Date'] = common_df['Last As Of Date'].astype(str).str.strip()
            common_df['Load DateTime'] = common_df['Load DateTime'].astype(str).str.strip()
            common_df['County'] = common_df['County'].astype(str).str.strip()
            common_df['Case Type'] = common_df['Case Type'].astype(str).str.strip()

            #Convert 'Last As Of Date' to YYYYMMDD format so that the max() function works properly.
            common_df['Last As Of Date'] = common_df['Last As Of Date'].apply(convert_as_of_date_format)

            dimmit_civil_last_as_of_date = common_df[(common_df['County'] == 'Dimmit') & (common_df['Case Type'] != 'Criminal') & (common_df['Case Type'] != 'Juvenile')]['Last As Of Date'].max()
            dimmit_civil_last_load_date = common_df[(common_df['County'] == 'Dimmit') & (common_df['Case Type'] != 'Criminal') & (common_df['Case Type'] != 'Juvenile')]['Load DateTime'].max()[:16]
            dimmit_criminal_last_as_of_date = common_df[(common_df['County'] == 'Dimmit') & (common_df['Case Type'] == 'Criminal')]['Last As Of Date'].max()
            dimmit_criminal_last_load_date = common_df[(common_df['County'] == 'Dimmit') & (common_df['Case Type'] == 'Criminal')]['Load DateTime'].max()[:16]
            maverick_civil_last_as_of_date = common_df[(common_df['County'] == 'Maverick') & (common_df['Case Type'] != 'Criminal') & (common_df['Case Type'] != 'Juvenile')]['Last As Of Date'].max()
            maverick_civil_last_load_date = common_df[(common_df['County'] == 'Maverick') & (common_df['Case Type'] != 'Criminal') & (common_df['Case Type'] != 'Juvenile')]['Load DateTime'].max()[:16]
            maverick_criminal_last_as_of_date = common_df[(common_df['County'] == 'Maverick') & (common_df['Case Type'] == 'Criminal')]['Last As Of Date'].max()
            maverick_criminal_last_load_date = common_df[(common_df['County'] == 'Maverick') & (common_df['Case Type'] == 'Criminal')]['Load DateTime'].max()[:16]
            zavala_civil_last_as_of_date = common_df[(common_df['County'] == 'Zavala') & (common_df['Case Type'] != 'Criminal') & (common_df['Case Type'] != 'Juvenile')]['Last As Of Date'].max()
            zavala_civil_last_load_date = common_df[(common_df['County'] == 'Zavala') & (common_df['Case Type'] != 'Criminal') & (common_df['Case Type'] != 'Juvenile')]['Load DateTime'].max()[:16]
            zavala_criminal_last_as_of_date = common_df[(common_df['County'] == 'Zavala') & (common_df['Case Type'] == 'Criminal')]['Last As Of Date'].max()
            zavala_criminal_last_load_date = common_df[(common_df['County'] == 'Zavala') & (common_df['Case Type'] == 'Criminal')]['Load DateTime'].max()[:16]
            juvenile_last_as_of_date = common_df[common_df['Case Type'] == 'Juvenile']['Last As Of Date'].max()
            juvenile_last_load_date = common_df[common_df['Case Type'] == 'Juvenile']['Load DateTime'].max()[:16]

            #Create a list to find the max as of date
            as_of_date_list = [dimmit_civil_last_as_of_date,
                               dimmit_criminal_last_as_of_date,
                               maverick_civil_last_as_of_date,
                               maverick_criminal_last_as_of_date,
                               zavala_civil_last_as_of_date,
                               zavala_criminal_last_as_of_date,
                               juvenile_last_as_of_date]
            
            max_as_of_date = max(as_of_date_list)

            missing_report_container.empty()
            with missing_report_container.container():
                if dimmit_civil_last_as_of_date != max_as_of_date:
                    st.info("Report Missing - Please Upload a Dimmit Civil Report with an As Of Date = " + reverse_as_of_date_format(max_as_of_date))
                if dimmit_criminal_last_as_of_date != max_as_of_date:
                    st.info("Report Missing - Please Upload a Dimmit Criminal Report with an As Of Date = " + reverse_as_of_date_format(max_as_of_date))
                if maverick_civil_last_as_of_date != max_as_of_date:
                    st.info("Report Missing - Please Upload a Maverick Civil Report with an As Of Date = " + reverse_as_of_date_format(max_as_of_date))
                if maverick_criminal_last_as_of_date != max_as_of_date:
                    st.info("Report Missing - Please Upload a Maverick Criminal Report with an As Of Date = " + reverse_as_of_date_format(max_as_of_date))
                if zavala_civil_last_as_of_date != max_as_of_date:
                    st.info("Report Missing - Please Upload a Zavala Civil Report with an As Of Date = " + reverse_as_of_date_format(max_as_of_date))
                if zavala_criminal_last_as_of_date != max_as_of_date:
                    st.info("Report Missing - Please Upload a Zavala Criminal Report with an As Of Date = " + reverse_as_of_date_format(max_as_of_date))
                if juvenile_last_as_of_date != max_as_of_date:
                    st.info("Report Missing - Please Upload a Juvenile Report with an As Of Date = " + reverse_as_of_date_format(max_as_of_date))

            #Create a sidebar to display the most recent 'As Of' and 'Load' dates for each section
            #Empty the original content
            sidebar_container.empty()
            with st.sidebar:
                st.subheader("Dimmit Civil Cases")
                st.write("Latest As Of Date: " + reverse_as_of_date_format(dimmit_civil_last_as_of_date))
                st.write("Latest Load Date: " + convert_datetime_format(dimmit_civil_last_load_date))
                st.divider()
                st.subheader("Dimmit Criminal Cases")
                st.write("Latest As Of Date: " + reverse_as_of_date_format(dimmit_criminal_last_as_of_date))
                st.write("Latest Load Date: " + convert_datetime_format(dimmit_criminal_last_load_date))
                st.divider()
                st.subheader("Maverick Civil Cases")
                st.write("Latest As Of Date: " + reverse_as_of_date_format(maverick_civil_last_as_of_date))
                st.write("Latest Load Date: " + convert_datetime_format(maverick_civil_last_load_date))
                st.divider()
                st.subheader("Maverick Criminal Cases")
                st.write("Latest As Of Date: " + reverse_as_of_date_format(maverick_criminal_last_as_of_date))
                st.write("Latest Load Date: " + convert_datetime_format(maverick_civil_last_load_date))
                st.divider()
                st.subheader("Zavala Civil Cases")
                st.write("Latest As Of Date: " + reverse_as_of_date_format(zavala_civil_last_as_of_date))
                st.write("Latest Load Date: " + convert_datetime_format(zavala_civil_last_load_date))
                st.divider()
                st.subheader("Zavala Criminal Cases")
                st.write("Latest As Of Date: " + reverse_as_of_date_format(zavala_criminal_last_as_of_date))
                st.write("Latest Load Date: " + convert_datetime_format(zavala_criminal_last_load_date))
                st.divider()
                st.subheader("Juvenile Cases")
                st.write("Latest As Of Date: " + reverse_as_of_date_format(juvenile_last_as_of_date))
                st.write("Latest Load Date: " + convert_datetime_format(juvenile_last_load_date))
                st.divider()