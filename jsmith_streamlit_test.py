import streamlit as st
import pandas as pd
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io
import os
import pending_upload
import gspread
import plotly.express as px

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
     page_icon="🧊",
     initial_sidebar_state="expanded"
 )

#Create sidebar menu
page_choice = st.sidebar.selectbox(
    "Select Page:",
    ("Update Pending Reports", "Civil Dashboard", "Criminal Dashboard", "Case Lookup")
)

#Create a placeholder for the page content
page_content = st.empty()

######################################### Update Pending Reports ##########################################

if page_choice == "Update Pending Reports":
    #Create container for update page content
    with page_content.container():

        #Title
        st.title("Update Pending Reports")

        #Get the file object
        file_objects = st.file_uploader("File Names Must Include Either 'CR' or 'CV' for Criminal and Civil Cases, Respectively.", type = 'pdf', accept_multiple_files = True)

        #Only create and update progress bar if files have been uploaded
        if len(file_objects) > 0:
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

        #If files were uploaded, processing is complete at this point. Leave a message
        if len(file_objects) > 0:
            progress_message_container.header("Complete! All Files Processed!")
        
################################################### Civil Dashboard ###################################################

elif page_choice == 'Civil Dashboard':
    #Create container for civil dashboard content
    with page_content.container():

        #Add county select box in the sidebar
        county_choice = st.sidebar.selectbox(
        "Select County:",
        ("All", "Dimmit", "Maverick", "Zavala")
        )

        #Load the data for the civil dashboard
        df = get_spreadsheet_data('test_civil_cases', credentials)

        #Title
        st.title("Civil Dashboard")

        #Apply the county selection
        if county_choice == 'Dimmit':
            df = df[df['County'] == 'Dimmit']
            st.subheader('Dimmit County')
        elif county_choice == 'Maverick':
            df = df[df['County'] == 'Maverick']
            st.subheader('Maverick County')
        elif county_choice == 'Zavala':
            df = df[df['County'] == 'Zavala']
            st.subheader('Zavala County')
        else:
            st.subheader('All Counties')

        #Add horizontal line
        st.markdown("***")

        #Create first row of columns for general counts
        col1, col2, col3 = st.columns(3)

        col1.metric("Total Pending Cases", len(df[df['Status'] != 'Disposed']))
        col2.metric("Total Civl Cases", len(df[ (df['Case Type'] == 'Civil') & (df['Status'] != 'Disposed') ]))
        col3.metric("Total Tax Cases", len(df[ (df['Case Type'] == 'Tax') & (df['Status'] != 'Disposed') ]))

        #Add horizontal line
        st.markdown('***')

        #Create second row of columns
        col4, col5 = st.columns(2)

        with col4:
            #Create the dataframe
            status_counts = df['Status'].value_counts()

            #Add a title
            st.write("Status Counts")

            #Create a pie chart
            status_chart = px.pie(status_counts, values = 'Status', 
                                                 names = status_counts.index, 
                                                 color = status_counts.index, 
                                                 labels = {'index':'Status', 'Status':'Count'},
                                                 hole = .65)
            #Display the chart
            st.plotly_chart(status_chart, use_container_width = True)

        with col5:
            #Create the dataframe
            on_track_count = df['On Track'].value_counts()

            #add a title
            st.write("On Track")

            #Create a pie chart
            on_track_chart = px.pie(on_track_count, values = 'On Track', 
                                                  names = on_track_count.index, 
                                                  color = on_track_count.index, 
                                                  labels = {'index':'On Track', 'On Track':'Count'},
                                                  color_discrete_map = {'TRUE':'00CC96', 'FALSE':'royalblue'},
                                                  hole = .65)
            #Display the chart
            st.plotly_chart(on_track_chart, use_container_width = True)
        
        #Add a horizontal line
        st.markdown('***')

        #Find the 10 most common Causes of Action
        coa_df = df['Cause of Action'].value_counts().head(10)

        #Build a bar chart
        coa_chart = px.bar(coa_df,
                             x = coa_df.index,
                             y = 'Cause of Action',
                             text_auto = True, 
                             title = 'Top 10 Causes of Action',
                             labels = {'index':'Cause of Action', 'Cause of Action':'Count'})
        st.plotly_chart(coa_chart, use_container_width = True)

        #Add a horizontal bar
        st.markdown("***")

        #Find the 10 most common docket types
        d_type_df = df[df['Docket Type'] != '']['Docket Type'].value_counts().head(10)

        #Build a bar chart
        d_type_chart = px.bar(d_type_df,
                                x = d_type_df.index,
                                y = 'Docket Type',
                                text_auto = True,
                                title = 'Top 10 Docket Types',
                                labels = {'index':'Docket Type', 'Docket Type':'Count'})
        st.plotly_chart(d_type_chart, use_container_width = True)

################################################### Criminal Dashboard ###################################################

elif page_choice == 'Criminal Dashboard':
    #Create container for criminal dashboard content
    with page_content.container():

        #Add county select box in the sidebar
        county_choice = st.sidebar.selectbox(
        "Select County:",
        ("All", "Dimmit", "Maverick", "Zavala")
        )

        #Load the data for the civil dashboard
        df = get_spreadsheet_data('test_criminal_cases', credentials)

        #Title
        st.title("Criminal Dashboard")

        #Apply the county selection
        if county_choice == 'Dimmit':
            df = df[df['County'] == 'Dimmit']
            st.subheader('Dimmit County')
        elif county_choice == 'Maverick':
            df = df[df['County'] == 'Maverick']
            st.subheader('Maverick County')
        elif county_choice == 'Zavala':
            df = df[df['County'] == 'Zavala']
            st.subheader('Zavala County')
        else:
            st.subheader('All Counties')

        #Add horizontal line
        st.markdown("***")

        st.metric("Total Pending Cases", len(df[df['Status'] != 'Disposed']))

        #Add horizontal line
        st.markdown('***')

        #Create second row of columns
        crim_col1, crim_col2 = st.columns(2)

        with crim_col1:
            #Create the dataframe
            status_counts = df['Status'].value_counts()

            #Add a title
            st.write("Status Counts")

            #Create a pie chart
            status_chart = px.pie(status_counts, values = 'Status', 
                                                 names = status_counts.index, 
                                                 color = status_counts.index, 
                                                 labels = {'index':'Status', 'Status':'Count'},
                                                 hole = .65)
            #Display the chart
            st.plotly_chart(status_chart, use_container_width = True)

        with crim_col2:
            #Create the dataframe
            on_track_count = df['On Track'].value_counts()

            #add a title
            st.write("On Track")

            #Create a pie chart
            on_track_chart = px.pie(on_track_count, values = 'On Track', 
                                                  names = on_track_count.index, 
                                                  color = on_track_count.index, 
                                                  labels = {'index':'On Track', 'On Track':'Count'},
                                                  color_discrete_map = {'TRUE':'00CC96', 'FALSE':'royalblue'},
                                                  hole = .65)
            #Display the chart
            st.plotly_chart(on_track_chart, use_container_width = True)
        
        #Add a horizontal line
        st.markdown('***')

        #Find the 10 most common Offenses
        offense_df = df['Offense'].value_counts().head(10)

        #Build a bar chart
        offense_chart = px.bar(offense_df,
                             x = offense_df.index,
                             y = 'Offense',
                             text_auto = True, 
                             title = 'Top 10 Offenses',
                             labels = {'index':'Offense', 'Offense':'Count'})
        st.plotly_chart(offense_chart, use_container_width = True)

        #Add a horizontal bar
        st.markdown("***")

        #Find the 10 most common Bondsman Names
        bondsman_df = df[df['Bondsman Name'] != '']['Bondsman Name'].value_counts().head(10)

        #Build a bar chart
        bondsman_chart = px.bar(bondsman_df,
                                x = bondsman_df.index,
                                y = 'Bondsman Name',
                                text_auto = True,
                                title = 'Top 10 Bondsman Names',
                                labels = {'index':'Bondsman Name', 'Bondsman Name':'Count'})
        st.plotly_chart(bondsman_chart, use_container_width = True)

################################################### Case Lookup ###################################################

elif page_choice == 'Case Lookup':
    #Create container for case lookup content
    with page_content.container():

        #Title
        st.title("Case Lookup")

        st.write("Under Construction")