from pickle import TRUE
import streamlit as st
import pandas as pd
import PyPDF2
from PyPDF2 import PdfFileReader
import re
import gspread as gs
import df2gspread as d2g
import docx2txt
import openpyxl


def read_pdf(file):
    pdfReader = PdfFileReader(file) #reads pdf
    count = pdfReader.numPages #counts the number of pages
    content = " "#space holder for pdf content
    for i in range(count): #for loop to extract text from all pages
        page = pdfReader.getPage(i) #gets page numbers
        content += page.extractText() #extracts text from iterated pages
    
    return content

#title
def main():
    st.title("Pending Case Report")
if __name__ == '__main__':
	main() 

###########reads and extracts text from pdf.
#uploader
docx_file = st.file_uploader('Upload pdf', type = 'pdf')

#checks to make sure it is a pdf doc
def raw_text():
    if docx_file is not None:
        if docx_file.type == "pdf":
            read_pdf(docx_file)
    else:
        raw_text = read_pdf(docx_file)#reads as bites
       
#regex to find cause numbers from raw text and converts it to a string.
finds_cause_numbers = re.findall(r'(\d{2}-\d{2}-\d{5}-\w*|\d*-\d*-\d*-\w*|\d*-\w*)\s*(\d{2}/\d{2}/\d{4})\s*(\D.{23})\s*(\d{2}/\d{2}/\d{4}|[ ]{0,1})(\D.[M$][O$][T$][I$].{,12}|\D.[W$][O$][N$]..{,12}|\D.[T$][R$][I$]..{,12}|\D.[J$][U$][R$]..{,12}|\D.[S$][T$][A$]..{,12}|\D.[H$][E$][A$]..{,12}|\D.[P$][R$][E$]..{,12}|\D.[E$][N$][T$]..{,12}|\D.[P$][E$][T$]..{,12}|\D.[F$][I$][N$]..{,12}|\D.[C$][O$][M$]..{,12}|\D.[P$][L$][E$]..{,12}|\D.[N$][O$][T$]..{,12}|[ ]{0,1})\s(\D.{,20})', str(raw_text))
#puts the cause numbers into a dataframe with the column name 'cause_number'
pending_cause_number_df = pd.DataFrame(finds_cause_numbers, columns = ['cause_number', 'file_date', 'cause_of_action', 'docket_date', 'docket_type', 'plaintiff'])

########Pulls in the goolge sheet data, compares it, drops the duplicates and updates the spreadsheet with the latest cause numbers
#json credentials
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
opens_civil_pending_gs = json_path.open_by_key('1b3fmZrbfwZWMvu4kUGJSSGsp61utlE0Ny-ebozZ5aBk')
    #pulls the data from the google worksheet (civil_pending_notes tab)
civil_pending_notes_tab = opens_civil_pending_gs.get_worksheet(0)
    #puts the data from the google sheet and puts it into a dataframe
civil_pending_notes = pd.DataFrame(civil_pending_notes_tab.get_all_records())
    #Clears the google spreadsheet for the update
civil_pending_notes_tab.clear()
    #adds both lists together in order to search for dups later
appended_pending = civil_pending_notes.append(pd.DataFrame(pending_cause_number_df), ignore_index=True)
    #drops the duplicated cause numbers and reindexes the dataframe
    #resets the index and drops the output index
    #fills in the na with an empty space to avoid error
ready_to_work_pending_list = appended_pending.drop_duplicates('cause_number').reset_index(drop=True).fillna(' ').astype(str)
#updates the google sheet with the new list of pending cases
civil_pending_notes_tab.update([ready_to_work_pending_list.columns.values.tolist()] + ready_to_work_pending_list.values.tolist())


#########Calculates counts
total = ready_to_work_pending_list.cause_number.count() #Counts total pending cases
#disposed = (ready_to_work_pending_list['disposed']).value_counts()['TRUE']#Counts the total of disposed cases

#combined dataframe
st.dataframe(ready_to_work_pending_list)

#total count oof cause numbers after appended both lists
st.write('Total Pending Cases', total)
#total where disposed is TRUE
#st.write('Total Disposed:', disposed)
