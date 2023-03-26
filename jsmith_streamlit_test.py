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
import pending_upload
import gspread

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

############################################## Begin App ##################################################

st.set_page_config(
     page_title="Pending Reports",
 )

########################################## Create Tabs ###################################################

tab1, tab2 = st.tabs(["Upload Reports", "View Data"])

######################################### Upload Reports ##########################################
with tab1:
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
                    pending_upload.update_spreadsheet(file_object.name, content)

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

with tab2:
    st.header("Civil Cases")

    civil_df = get_spreadsheet_data("Civil Cases", credentials)
    criminal_df = get_spreadsheet_data("Criminal Cases", credentials)

    #Get count of civil cases without future docket dates, regardless of case type. Provide dataframe for all of the following
    st.metric(label = "Total Civil Cases Without Future Docket Dates", value = len(civil_df[civil_df["Docket Date"] == ""]))
    st.dataframe(civil_df[civil_df["Docket Date"] == ""].drop(["Case Type", "On Track", "Bad Cause Number", "Status", "load_date"], axis = 1))
    #Provide an option to download the basic dataframe as a csv
    st.download_button(
        label="Download as CSV",
        data= civil_df[civil_df["Docket Date"] == ""].drop(["Case Type", "On Track", "Bad Cause Number", "Status", "load_date"], axis = 1).to_csv(index = False).encode('utf-8'),
        file_name='Civil_Cases_Without_Future_Docket_Dates_' + str(date.today()) + '.csv',
        mime='text/csv',
    )

    #Get count of general civil cases without future docket dates,
    st.metric(label = "General Civil Cases Without Future Docket Dates", value = len(civil_df[(civil_df["Docket Date"] == "") & (civil_df["Case Type"] == "Civil")]))
    st.dataframe(civil_df[(civil_df["Docket Date"] == "") & (civil_df["Case Type"] == "Civil")].drop(["Case Type", "On Track", "Bad Cause Number", "Status", "load_date"], axis = 1))

    #Get count of tax cases without future docket dates,
    st.metric(label = "Tax Cases Without Future Docket Dates", value = len(civil_df[(civil_df["Docket Date"] == "") & (civil_df["Case Type"] == "Tax")]))
    st.dataframe(civil_df[(civil_df["Docket Date"] == "") & (civil_df["Case Type"] == "Tax")].drop(["Case Type", "On Track", "Bad Cause Number", "Status", "load_date"], axis = 1))

    #Get count of OLS cases without future docket dates,
    st.metric(label = "OLS Cases Without Future Docket Dates", value = len(civil_df[(civil_df["Docket Date"] == "") & (civil_df["Case Type"] == "OLS")]))
    st.dataframe(civil_df[(civil_df["Docket Date"] == "") & (civil_df["Case Type"] == "OLS")].drop(["Case Type", "On Track", "Bad Cause Number", "Status", "load_date"], axis = 1))

    #Get count of juvenile cases without future docket dates,
    st.metric(label = "Juvenile Cases Without Future Docket Dates", value = len(civil_df[(civil_df["Docket Date"] == "") & (civil_df["Case Type"] == "Juvenile")]))
    st.dataframe(civil_df[(civil_df["Docket Date"] == "") & (civil_df["Case Type"] == "Juvenile")].drop(["Case Type", "On Track", "Bad Cause Number", "Status", "load_date"], axis = 1))

    st.header("Criminal Cases")

    #Get count of criminal cases without future docket dates, regardless of case type
    st.metric(label = "Criminal Cases Without Future Docket Dates", value = len(criminal_df[criminal_df["Docket Date"] == ""]))
    st.dataframe(criminal_df[criminal_df["Docket Date"] == ""].drop(["Case Type", "On Track", "Bad Cause Number", "Status", "load_date"], axis = 1))
    #Provide an option to download the basic dataframe as a csv
    st.download_button(
        label="Download as CSV",
        data= criminal_df[criminal_df["Docket Date"] == ""].drop(["Case Type", "On Track", "Bad Cause Number", "Status", "load_date"], axis = 1).to_csv(index = False).encode('utf-8'),
        file_name='Criminal_Cases_Without_Future_Docket_Dates_' + str(date.today()) + '.csv',
        mime='text/csv',
    )

    
