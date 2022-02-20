from pickle import TRUE
import streamlit as st
import streamlit.components.v1 as stc
import numpy as np
import pandas as pd
import PyPDF2
from PyPDF2 import PdfFileReader
import pending_upload

#Function for gathering text content of uploaded PDF 
def read_pdf(file):
    pdfReader = PdfFileReader(file) #reads pdf
    count = pdfReader.numPages #counts the number of pages
    content = " "#space holder for pdf content
    for i in range(count): #for loop to extract text from all pages
        page = pdfReader.getPage(i) #gets page numbers
        content += page.extractText() #extracts text from iterated pages
    
    return content

#title
st.title("293rd District Court Civil and Criminal Pending Cases")

#uploader
pdf_path = st.file_uploader('Upload pdf', type = 'pdf')

if pdf_path is not None:
    #Get file)name, file_type, and file_size
    file_details = {"FileName":pdf_path.name,"FileType":pdf_path.type,"FileSize":pdf_path.size}

    #Print it to streamlit app page
    st.write(file_details)

<<<<<<< HEAD
df = pending_upload.update_spreadsheet(pdf_path)

st.dataframe(df)
st.dataframe(pending_upload.current_civil_df)
st.dataframe(pending_upload.current_crim_df)
=======
    #Get PDF text content
    content = read_pdf(pdf_path)

    #Pass file name and text content to update function
    df = pending_upload.update_spreadsheet(file_details['FileName'], content)

    st.dataframe(df)
>>>>>>> dfabe4bd66903f1135fa76d906fe5d8d7525333a
