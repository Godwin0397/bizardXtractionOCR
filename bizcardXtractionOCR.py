# Import Required Packages
import easyocr
import numpy as np
import pandas as pd
import PIL
from PIL import Image
import re
import streamlit as st
from streamlit_option_menu import option_menu
import io
import sqlite3


# creating a database in sqlite3
conn = sqlite3.connect('bizardX.db')
cursor = conn.cursor() #creating a cursor to execute a queries

# Function to Extract a data from Image
def extractingDataFromImage(path):
    image = Image.open(path)
    imageArr = np.array(image)
    extractingImage = easyocr.Reader(['en'])
    textValue = extractingImage.readtext(imageArr, detail=0)
    return textValue, image

text, image = extractingDataFromImage("C:/Users/Godveen/Guvi/capstoneProjects/images/1.png")


# Function to create a dictionary from extarcted text
def dictCreationFromTextData(text):
    textvaluesDict = {'name':[], 'designation':[], 'mobileNumber':[], 'website':[], 'email':[], 'address':[], 'pincode':[], 'companyName':[]}
    textvaluesDict['name'].append(text[0])
    textvaluesDict['designation'].append(text[1])
    for i in range(2, len(text)):
        if text[i].startswith('+') or ('-' in text[i] and text[i].replace('-', '').isdigit()):
            textvaluesDict['mobileNumber'].append(text[i])
        elif 'www' in text[i] or 'WWW' in text[i] or 'wWw' in text[i] or 'Www' in text[i] or 'wwW' in text[i] or 'WWw' in text[i] or 'wWW' in text[i] or 'WwW' in text[i]:
            textvaluesDict['website'].append(text[i])
        elif '@' in text[i] and '.com' in text[i]:
            emailid = text[i].lower()
            textvaluesDict['email'].append(emailid)
        elif 'TamilNadu' in text[i] or 'Tamil Nadu' in text[i] or text[i].isdigit():
            textvaluesDict['pincode'].append(text[i])
        elif re.match(r'^[A-Za-z]', text[i]):
            textvaluesDict['companyName'].append(text[i])
        else:
            removeColon = re.sub(r'[,:]', '', text[i])
            textvaluesDict['address'].append(removeColon)
    for key, value in textvaluesDict.items():
        if len(value)>0:
            concatValue = ' '.join(value)
            textvaluesDict[key] = [concatValue]
        else:
            value = 'NA'
            textvaluesDict[key] = [value]
    return textvaluesDict


# converting a image to a byte format
def convertingImageToBytesFormat(image):
    imageToBytes = io.BytesIO()
    image.save(imageToBytes, format='PNG')
    imageBytesData = imageToBytes.getvalue()
    imageBytesDataDict = {'image': [imageBytesData]}
    imageBytesDatadf = pd.DataFrame(imageBytesDataDict)
    return imageBytesDatadf


def tableCreation():
    tableCreation = '''create table if not exists
        imageData(name varchar(255), designation varchar(255), mobileNumber varchar(255), website varchar(255),
        email varchar(255), address varchar(255), pincode varchar(255), companyName varchar(255), image text)'''
    cursor.execute(tableCreation)
    conn.commit()
    return "Table Created Successfully"

def insertDataToTable(concatdf):
    dataInsertionTable = '''insert into imageData(name, designation, mobileNumber, website, email,
           address, pincode, companyName, image)
            values(?, ?, ?, ?, ?, ?, ?, ?, ?)'''
    concatdfValues = concatdf.values.tolist()
    cursor.executemany(dataInsertionTable, concatdfValues)
    conn.commit()
    return "Successfully Saved/Modified"

def deleteData(val):
    if len(val)>1:
        deleteQuery = f"delete from imageData where name = '{val[0]}' and designation = '{val[1]}'"
        cursor.execute(deleteQuery)
        conn.commit()
    else:
        deleteQuery = f"delete from imageData where name = '{val[0]}'"
        cursor.execute(deleteQuery)
        conn.commit()



# Streamlit Part
st.set_page_config(layout='wide')
st.title("BizCardX: Extracting Business Card Data with OCR")

with st.sidebar:
    select = option_menu("Main Menu",["Home", "Upload or Modify Image", "Delete Image"])
    
if select == "Home":
    
    st.markdown("### :blue[**Technologies Used :**] Python,easy OCR, Streamlit, SQL, Pandas")
    st.write(
            "### :green[**About :**] Bizcard is a Python application designed to extract information from business cards.")
    st.write(
            '### The main purpose of Bizcard is to automate the process of extracting key details from business card images, such as the name, designation, company, contact information, and other relevant data. By leveraging the power of OCR (Optical Character Recognition) provided by EasyOCR, Bizcard is able to extract text from the images.')
    
elif select == 'Upload or Modify Image':
    img = st.file_uploader('Upload the Image', type=['png', 'jpg', 'jpeg'])
    if img is not None:
        
        st.image(img, width = 300)
        
#       converting the image to text
        text, image = extractingDataFromImage(img)
    
#       creating a dictionary fron the extracted text
        dictVal = dictCreationFromTextData(text)
        if dictVal:
            
            st.success("Text Extracted Successfully")
        textdf = pd.DataFrame(dictVal)
    
#       convering a image to byte format
        imageBytedf = convertingImageToBytesFormat(image)
        
#       concatinating the dataframes
        concatdf = pd.concat([textdf, imageBytedf], axis = 1)
        st.dataframe(concatdf)
        saveButton = st.button('Save', use_container_width = True)
        if saveButton:
            tableCreationObj = tableCreation()
            insertDataToTableObj = insertDataToTable(concatdf)
            st.success("Saved Successfully")
    
    method = st.radio("Select the Method", ["None", "Preview", "Modify"])
    if method == 'None':
        pass

    elif method == 'Preview':  
        
        cursor.execute('select * from imageData')
        conn.commit()
        tableDate = cursor.fetchall()
        tableDateDf = pd.DataFrame(tableDate, columns=['name', 'designation', 'mobileNumber', 'website', 'email',
               'address', 'pincode', 'companyName', 'image'])
        st.dataframe(tableDateDf)
        
    elif method == 'Modify':
        
        cursor.execute('select * from imageData')
        conn.commit()
        tableDate = cursor.fetchall()
        tableDateDf = pd.DataFrame(tableDate, columns=['name', 'designation', 'mobileNumber', 'website', 'email',
               'address', 'pincode', 'companyName', 'image'])
        col1, col2 = st.columns(2)
        with col1:
            selectedName = st.selectbox("Select the Name", tableDateDf['name'])
        df = tableDateDf[tableDateDf['name']==selectedName]
        df1 = df.copy()
        
        col1, col2 = st.columns(2)
        with col1:
            modifyName = st.text_input("Name", df1['name'].unique()[0])
            modifyDesignation = st.text_input("Designation", df1['designation'].unique()[0])
            modifyMobileNumber = st.text_input("Mobile Number", df1['mobileNumber'].unique()[0])
            modifyWebsite = st.text_input("Website", df1['website'].unique()[0])
            modifyEmail = st.text_input("Email", df1['email'].unique()[0])
            
            df1['name'] = modifyName
            df1['designation'] = modifyDesignation
            df1['mobileNumber'] = modifyMobileNumber
            df1['website'] = modifyWebsite
            df1['email'] = modifyEmail
            
        with col2:
            modifyAddress = st.text_input("Address", df1['address'].unique()[0])
            modifyPincode = st.text_input("Pincode", df1['pincode'].unique()[0])
            modifyCompanyName = st.text_input("Company Name", df1['companyName'].unique()[0])
            modifyImage = st.text_input("Image Byte Format", df1['image'].unique()[0])
            
            df1['address'] = modifyAddress
            df1['pincode'] = modifyPincode
            df1['companyName'] = modifyCompanyName
            df1['image'] = modifyImage
            

        modifyButton = st.button('Modify', use_container_width = True)
        if modifyButton:
            deleteDataObj = deleteData([selectedName])
            insertDataToTableObj = insertDataToTable(df1)
            st.success("Updated Successfully")
        
        st.dataframe(df1)

elif select == 'Delete Image':
    
    cursor.execute('select name from imageData')
    conn.commit()
    tableDate = cursor.fetchall()
    name=[]
    for i in tableDate:
        name.append(i[0])
    col1, col2 = st.columns(2)
    with col1:
        selectedName = st.selectbox("Select the Name", name)
    
    with col2:
        selectQuery = f"select designation from imageData where name = '{selectedName}'"
        cursor.execute(selectQuery)
        conn.commit()
        designation=[]
        selectQueryData = cursor.fetchall()
        for j in selectQueryData:
            designation.append(j[0])
        selectedDesignation = st.selectbox("Select the Designation", designation)
    
    if selectedName and selectedDesignation:
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Selected Name: {selectedName}")
        with col2:
            st.write(f"Selected Designation: {selectedDesignation}")
    
    deleteButton = st.button('Delete', use_container_width = True)
    if deleteButton:
        deleteDataObj = deleteData([selectedName, selectedDesignation])
        st.warning("Deleted Successfully")