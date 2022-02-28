import streamlit as st
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io
import os
import pending_upload

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

############################################## Begin App ##################################################

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

