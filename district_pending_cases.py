from pickle import TRUE
import streamlit as st
import streamlit.components.v1 as stc
import numpy as np
import pandas as pd
import pdfplumber
import PyPDF2
from PyPDF2 import PdfFileReader

import jsmith_acquire
import jsmith_prepare

#title
st.title("293rd District Court Civil and Criminal Pending Cases")

#uploader
pdf_path = st.file_uploader('Upload pdf', type = 'pdf')
if pdf_path is not None:
    file_details = {"FileName":pdf_path.name,"FileType":pdf_path.type,"FileSize":pdf_path.size}
    st.write(file_details)

if pdf_path is not None:
    pdfReader = PdfFileReader(pdf_path) #reads pdf
    count = pdfReader.numPages #counts the number of pages
    path = " "#space holder for pdf content
    for i in range(count): #for loop to extract text from all pages
        page = pdfReader.getPage(i) #gets page numbers
        path += page.extractText() #extracts text from iterated pages

        st.write(path)
path = str(str)