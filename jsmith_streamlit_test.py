import streamlit as st
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import PDFPageAggregator
from pdfminer3.converter import TextConverter
import io
import os
import jsmith_acquire
import jsmith_prepare
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

#Get the file object
file_object = st.file_uploader("Please upload a .pdf file.", type = 'pdf', help = "One File At A Time, Please")

if file_object is not None:

    #Print file_object name, type, and size
    st.write("File Name: ", file_object.name)
    st.write("File Type: ", file_object.type)
    st.write("File Size: ", str(file_object.size))

    #Save the file. Will be deleted after data is uploaded
    with open(file_object.name, 'wb') as f:
        f.write(file_object.getbuffer())

    #Create content container
    content = get_file_content(file_object.name)

    #Try extracting info with current functions
    df = jsmith_acquire.build_dataframe(file_object.name, content)

    #Take a look at the df
    st.title("Unprepared DataFrame")
    st.write(df)

    #Try preparing the df with current functions
    df = jsmith_prepare.prepare_dataframe(file_object.name, df)

    #Take a look at the dataframe
    st.title("Prepared DataFrame")
    st.write(df)

    #Do a complete test using pending_uploads function
    pending_upload.update_spreadsheet(file_object.name, content)

    #Delete the saved file
    if os.path.exists(file_object.name):
        os.remove(file_object.name)
    else:
        print("The file does not exist")

    #Try uploading the new data to the google spreadsheet
    #pending_upload.update_spreadsheet(file_object.name, content)