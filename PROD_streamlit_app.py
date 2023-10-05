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
import PROD_pending_upload
import gspread
import streamlit_authenticator as stauth
from pathlib import Path

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


############################################## Begin App ##################################################

st.set_page_config(
     page_title="Pending Reports",
 )

#Gather the most recent 'As Of' and 'Load' dates for each section
common_df = get_spreadsheet_data("Common Table", credentials)

if len(common_df) > 0:
    #Verify the columns are string types
    common_df['Last As Of Date'] = common_df['Last As Of Date'].astype(str).str.strip()
    common_df['Load DateTime'] = common_df['Load DateTime'].astype(str).str.strip()
    common_df['County'] = common_df['County'].astype(str).str.strip()
    common_df['Case Type'] = common_df['Case Type'].astype(str).str.strip()

    dimmit_civil_last_as_of_date = common_df[(common_df['County'] == 'Dimmit') & (common_df['Case Type'] != 'Criminal')]['Last As Of Date'].max()
    dimmit_civil_last_load_date = common_df[(common_df['County'] == 'Dimmit') & (common_df['Case Type'] != 'Criminal')]['Load DateTime'].max()[:16]
    dimmit_criminal_last_as_of_date = common_df[(common_df['County'] == 'Dimmit') & (common_df['Case Type'] == 'Criminal')]['Last As Of Date'].max()
    dimmit_criminal_last_load_date = common_df[(common_df['County'] == 'Dimmit') & (common_df['Case Type'] == 'Criminal')]['Load DateTime'].max()[:16]
    maverick_civil_last_as_of_date = common_df[(common_df['County'] == 'Maverick') & (common_df['Case Type'] != 'Criminal')]['Last As Of Date'].max()
    maverick_civil_last_load_date = common_df[(common_df['County'] == 'Maverick') & (common_df['Case Type'] != 'Criminal')]['Load DateTime'].max()[:16]
    maverick_criminal_last_as_of_date = common_df[(common_df['County'] == 'Maverick') & (common_df['Case Type'] == 'Criminal')]['Last As Of Date'].max()
    maverick_criminal_last_load_date = common_df[(common_df['County'] == 'Maverick') & (common_df['Case Type'] == 'Criminal')]['Load DateTime'].max()[:16]
    zavala_civil_last_as_of_date = common_df[(common_df['County'] == 'Zavala') & (common_df['Case Type'] != 'Criminal')]['Last As Of Date'].max()
    zavala_civil_last_load_date = common_df[(common_df['County'] == 'Zavala') & (common_df['Case Type'] != 'Criminal')]['Load DateTime'].max()[:16]
    zavala_criminal_last_as_of_date = common_df[(common_df['County'] == 'Zavala') & (common_df['Case Type'] == 'Criminal')]['Last As Of Date'].max()
    zavala_criminal_last_load_date = common_df[(common_df['County'] == 'Zavala') & (common_df['Case Type'] == 'Criminal')]['Load DateTime'].max()[:16]

    #Create a sidebar to display the most recent 'As Of' and 'Load' dates for each section
    with st.sidebar:
        st.subheader("Dimmit Civil Cases")
        st.write("Latest As Of Date: " + dimmit_civil_last_as_of_date)
        st.write("Latest Load Date: " + convert_datetime_format(dimmit_civil_last_load_date))
        st.divider()
        st.subheader("Dimmit Criminal Cases")
        st.write("Latest As Of Date: " + dimmit_criminal_last_as_of_date)
        st.write("Latest Load Date: " + convert_datetime_format(dimmit_criminal_last_load_date))
        st.divider()
        st.subheader("Maverick Civil Cases")
        st.write("Latest As Of Date: " + maverick_civil_last_as_of_date)
        st.write("Latest Load Date: " + convert_datetime_format(maverick_civil_last_load_date))
        st.divider()
        st.subheader("Maverick Criminal Cases")
        st.write("Latest As Of Date: " + maverick_criminal_last_as_of_date)
        st.write("Latest Load Date: " + convert_datetime_format(maverick_civil_last_load_date))
        st.divider()
        st.subheader("Zavala Civil Cases")
        st.write("Latest As Of Date: " + zavala_civil_last_as_of_date)
        st.write("Latest Load Date: " + convert_datetime_format(zavala_civil_last_load_date))
        st.divider()
        st.subheader("Zavala Criminal Cases")
        st.write("Latest As Of Date: " + zavala_criminal_last_as_of_date)
        st.write("Latest Load Date: " + convert_datetime_format(zavala_criminal_last_load_date))
        st.divider()


#Create a placeholder for the page content
page_content = st.empty()

#Create container for update page content
with page_content.container():

    #Title
    st.title("Update Pending Reports")

    with st.form("my-form", clear_on_submit = True):
        file_objects = st.file_uploader("File Names Must Include Either 'CV', 'JU', or 'CR' for Civil, Juvenile, and Criminal Cases, Respectively.", type = 'pdf', accept_multiple_files = True)
        submitted = st.form_submit_button("Upload")

    if submitted and len(file_objects) > 0:
        #Give message for successful upload and begin processing
        st.write("Files Uploaded!")

        #Create a container for the progress bar message
        progress_message_container = st.empty()
        #Create a progress bar for visual verification that something is happening
        progress_message_container.header("Please Wait, Processing In Progress:")
        progress_bar = st.progress(0)

        #Use the remainder of 100 / the number of uploaded files to start the progress bar
        bar_value = int(100 % len(file_objects))

        #Update progress bar
        progress_bar.progress(bar_value)

        #How much progress should be made per file?
        progress_per_file = int((100 - bar_value) / len(file_objects))

        #Also create a container for the info messages
        info_container = st.empty()

        #Use a for loop to iterate through the uploaded files
        for file_object in file_objects:

            if file_object is not None:

                #Inform the user which file is being processed
                info_container.info("Began Processing " + file_object.name)

                #Save the file. Will be deleted after data is uploaded
                with open(file_object.name, 'wb') as f:
                    f.write(file_object.getbuffer())

                #Create content container
                content = get_file_content(file_object.name)

                #Build and prepare the dataframe, then update the spreadsheet
                PROD_pending_upload.update_spreadsheet(file_object.name, content)

                #Delete the saved file. Leave messages for success or failure
                if os.path.exists(file_object.name):
                    os.remove(file_object.name)

                    #Leave a success message
                    st.success("Pending Reports was successfully updated with " + file_object.name)
                
                else:
                    st.error("Could Not Delete File " + file_object.name)

                #Clear container
                info_container.empty()

            else:
                #Print an error message
                st.error("A File Was Not Uploaded Correctly. Please Try Again")

            #Update progress bar regardless of whether or not Pending Reports was successfully updated with the current file
            bar_value += progress_per_file
            progress_bar.progress(bar_value)

        #Update message
        progress_message_container.header("Complete! All Files Processed Successfully!")