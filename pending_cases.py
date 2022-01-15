import streamlit as st
import streamlit.components.v1 as stc
import pandas as pd
import docx2txt
from PyPDF2 import PdfFileReader
import re
import gspread
import df2gspread as d2g

def read_pdf(file):
    pdfReader = PdfFileReader(file) #reads pdf
    count = pdfReader.numPages #counts the number of pages
    content = " "#space holder for pdf content
    for i in range(count): #for loop to extract text from all pages
        page = pdfReader.getPage(i) #gets page numbers
        content += page.extractText() #extracts text from iterated pages
    
    return content

def main():
    st.title("Pending Case Report")

#uploads pdf
pdf_file = st.file_uploader('Upload pdf', type = 'pdf')

if pdf_file is not None:
    read_pdf(pdf_file)

if __name__ == '__main__':
	main()

pdf_raw_text = read_pdf(pdf_file) 
#regex to find cause numbers
finds_cause_numbers = re.findall(r'\d{2}-\d{2}-\d{5}-\w*', pdf_file)
#puts the cause numbers into a dataframe with the column name 'cause_number'
pending_cause_number_df = pd.DataFrame(finds_cause_numbers, columns = ['cause_number'])

#opens the google sheet of pending case notes
    #sets the json to service account path
json_path = gspread.service_account(filename = '/Users/hector/codeup-data-science/293pending_cases/pending_cases.json')
    #opens the google sheet by key found in the address
opens_civil_pending_gs = json_path.open_by_key('1b3fmZrbfwZWMvu4kUGJSSGsp61utlE0Ny-ebozZ5aBk')
    #pulls the data from the google worksheet (civil_pending_notes tab)
civil_pending_notes_tab = opens_civil_pending_gs.get_worksheet(0)
    #puts the data from the google sheet and puts it into a dataframe
civil_pending_notes = pd.DataFrame(civil_pending_notes_tab.get_all_records())

#adds both lists together in order to search for dups later
df = civil_pending_notes.append(pd.DataFrame(pending_cause_number_df, columns=['cause_number']), ignore_index=True)
    #drops the duplicated cause numbers and reindexes the dataframe
    #resets the index and drops the output index
    #fills in the na with an empty space to avoid error
df = df.drop_duplicates('cause_number').reset_index(drop=True).fillna(' ')

#Clears the google spreadsheet for the update
civil_pending_notes_tab.clear()
#updates the google sheet with the new list of pending cases
civil_pending_notes_tab.update([df.columns.values.tolist()] + df.values.tolist())
