from pickle import TRUE
import streamlit as st
import streamlit.components.v1 as stc
import numpy as np
import pandas as pd
import PyPDF2
from PyPDF2 import PdfFileReader
import pending_upload

#title
st.title("293rd District Court Civil and Criminal Pending Cases")

#uploader
pdf_path = st.file_uploader('Upload pdf', type = 'pdf')
if pdf_path is not None:
    file_details = {"FileName":pdf_path.name,"FileType":pdf_path.type,"FileSize":pdf_path.size}
    st.write(file_details)

def read_pdf(file):
    pdfReader = PdfFileReader(file) #reads pdf
    count = pdfReader.numPages #counts the number of pages
    content = " "#space holder for pdf content

    for i in range(count): #for loop to extract text from all pages
        page = pdfReader.getPage(i) #gets page numbers
        content += page.extractText() #extracts text from iterated pages
    return content

content = read_pdf(pdf_path)

df = pending_upload.update_spreadsheet(file_details['name'], content)

st.dataframe(df)