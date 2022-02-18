from pickle import TRUE
import streamlit as st
import streamlit.components.v1 as stc
import numpy as np
import pandas as pd
import PyPDF2
from PyPDF2 import PdfFileReader
import gspread
import pdfminer
import io
import re
import jsmith_acquire
import jsmith_prepare
import pending_upload

#title
st.title("293rd District Court Civil and Criminal Pending Cases")

#uploader
pdf_path = st.file_uploader('Upload pdf', type = 'pdf')
if pdf_path is not None:
    file_details = {"FileName":pdf_path.name,"FileType":pdf_path.type,"FileSize":pdf_path.size}
    st.write(file_details)

df = pending_upload.update_spreadsheet(file_details)

st.dataframe(df)