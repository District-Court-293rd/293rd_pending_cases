from pickle import TRUE
import streamlit as st
import numpy as np
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import df2gspread as d2g
import docx2txt
import openpyxl

import jsmith_acquire
import jsmith_prepare

#title
def main():
    st.title("293rd District Court Civil and Criminal Pending Cases")
if __name__ == '__main__':
	main() 

#uploader
docx_file = st.file_uploader('Upload pdf', type = 'pdf')