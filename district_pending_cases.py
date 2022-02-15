from cgitb import text
from pickle import TRUE
from pydoc import pager
import streamlit as st
import streamlit.components.v1 as stc
import numpy as np
import pandas as pd
import pdfminer
from pdfminer.pdfinterp import PDFResourceManager,PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import io
from io import StringIO
import gspread as gs
from oauth2client.service_account import ServiceAccountCredentials
import PyPDF2
from PyPDF2 import PdfFileReader

import df2gspread as d2g
import docx2txt
import openpyxl
import jsmith_acquire
import jsmith_prepare

import pdfplumber


#title
def main():
    st.title("293rd District Court Civil and Criminal Pending Cases")
if __name__ == '__main__':
	main() 

#uploader
uploaded_file = st.file_uploader('Upload Pending Reports', type = 'pdf')
def raw_text():
    if uploaded_file is not None:
#       file_details = {"FileName":uploaded_file.name,"FileType":uploaded_file.type,"FileSize":uploaded_file.size}
#       st.write(file_details)
        if uploaded_file.type == "application/pdf":
            try:
                with pdfplumber.open(uploaded_file) as pdf:
                    pages = pdf.pages[0]
                    st.write(pages.extract_text())
            except:
                st.write("None")
                raw_text = docx2txt.process(uploaded_file)
                st.write(raw_text)

credentials = {
  "type": "service_account",
  "project_id": "pending-cases",
  "private_key_id": "1c8af459c6494b0a2194be2aeb894ebc2e83655b",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCtw8TucD1nvIqA\nsJUWc1pW7VFguuL3UqVgEnOg/q3KPguu4F/L7ZJV9nEnYl711suYMzyH1Q6VgfTU\n4d2SklFIX86V+GaQRdpxMML7fohdG7dULGIeX+TAMMbLg57xFTFFyAplyOFZfaVl\nI17L1e7mnRXpLh10wqDOwf4vmVk6f36/QabszABZqwSkY4mRQFRK1qcefjND9Yl0\nbTG9x31X6TUcOGVNLweNLaHfvcyakUsib0ZPeNFtKcZr3bv01xyzTXgrcW6QHmeQ\nwrXepSsAahPolIfJe3h+Dwbf6a9qJSUI6IKKl11MFyzHku0EnN+OaNJufsJwWeOP\nOmW3/YFnAgMBAAECggEAQucaXremXNeR+CSE8oTtZoSvDXBHTPRsKgZQsM79+N1U\nwDsxhyHsct6VCJXue/b8opgvmRjmKZhEvOZN2k4tr5D7yHBAhRHwHh6pJA2+0SKH\nvofsK0e+mmTtVZRS0P3Y38Y6gqAKa9tdoAgzSoYPGomm0wXnX3pEUfcNOCRx33xu\nmPAVB2lbGaTkFI72/DS/KRVpuBYIJ4kCN7oR1CI4PHi8xA73HW4P1IwdrpLGo9kn\nF4vpqVFgXhcqYRu1kb787nGTZ20v9UQUihYL/b7DwdVjqX66IUal4j9Swzil/2H0\nC/57b50KvlEJkKI6uC7tSifpI76olump08pXDLD7yQKBgQDepqod/V38nvyuAELu\niwvMuxjJ3GPCqdV73T0/kyNuV3i8RRlLOvE/F8AxOWRp12V+p6YZ/BRySuduv2Ue\nkP20+s5UeaI4vuc560GZWeMnIW2MFUtew15pb6jUnTjH8aHwv2ZrKuh9Csh5B5gB\nIL5EJwlvH4kjNvJXpXtt7KBiSwKBgQDHyptuW/4DiVVqmlD2oC9xZTn3Ilm+t1pC\nkAgmX3pTnlVKO/W06DJjFuH1SMsamgX08+66vsLMZ9n7TosxwzX0hmIVnNfKFANE\nG1kOcFZq5vBhpjIK5uskQErasI1IA7VhFwd6r8GZ0mEeCXSfY6evWVGy31yTFaEL\nHK8+f2eL1QKBgQCWlHsrCyccad4UQ+MAd5OEY+jw5JenmLrkKY15yKZGwuvJ0KW5\npmRwOjzmTZ1mo6Fl1jZVDpI5dgUtdk4KLR8Y3iLbKOQYoqu5FS1pbExfM5FmEyTF\nMzZP8o9pM+ep+fZ+3sOCqSNRJhDNIeCgqqdjak9MEzTpVwjxU961SjpyHwKBgQCh\nZfSAh8JBex1MvBMx2R/afEsCcXaMkjRRV2euEC2TBXKjQKLynS2vTNoHO+IPwGOV\nicXOiLJ3TGIVGVNrROb+fd0Y1paggeBNkcY02t2FCMEiMY91rSxCIcoWts+7YHuT\nTnZVT0yYBhM8n6jd5jSdfAt68+QmUi/B+U88rtGobQKBgEp8gPH50S4J7DXK3P4y\nlw5ubAxN8tCYu/Kq7gRd0EZxRazSXeOj6NPr/5/wA5drYo4FcNX3cZiRGb3Wyp6z\nizSnrDTVPX895EXGATzFJmtg9RbfUs0w+td5Tj2mIGsFJw1n/DwptsurppGR8R3i\ngHDptPNdZuhRmwkfL9Y7Ynt2\n-----END PRIVATE KEY-----\n",
  "client_email": "pending-cause-numbers@pending-cases.iam.gserviceaccount.com",
  "client_id": "117866190398620410804",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/pending-cause-numbers%40pending-cases.iam.gserviceaccount.com"
}

json_path = gs.service_account_from_dict(credentials)
#opens the google sheet by key found in the address
opens_pending_cases_gs = json_path.open_by_key('1b3fmZrbfwZWMvu4kUGJSSGsp61utlE0Ny-ebozZ5aBk')
#pulls the data from the civil_cases tab from the google pending_cases workbook
district_civil_cases_tab = opens_pending_cases_gs.get_worksheet(4)
#pulls the data from the criminal_cases tab from the google pending_cases workbook
district_criminal_cases_tab = opens_pending_cases_gs.get_worksheet(5)
#puts the district_civil_cases_tab into a dataframe
district_civil_pending_notes = pd.DataFrame(district_civil_cases_tab.get_all_records())
#puts the district_criminal_cases_tab into a dataframe
district_criminal_pending_notes = pd.DataFrame(district_criminal_cases_tab.get_all_records())
#Clears the google spreadsheet for the update



st.write('District Civil Pending Cases')
st.dataframe(district_civil_pending_notes)

st.write('District Criminal Pending Cases')
st.dataframe(district_civil_pending_notes)