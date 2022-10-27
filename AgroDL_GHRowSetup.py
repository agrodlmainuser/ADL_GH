import PIL
from ADL_classes import ADL_EXIF
from ADL_classes import ADL_gh
from ADL_classes import ADL_Read_XML
from ADL_classes import ADL_img_gh
import xml.etree.ElementTree as ET
import os
import pandas as pd
import re
import pickle 
import re
import imaplib
import email
import shutil
import sys
import subprocess #for !python linux command
from zipfile import ZipFile #for !unzip linux command

script_params = ADL_Read_XML("AgroDL_GHRowSetup_0000")

# function for saving the gh object later
def save_object(obj, filename):
    with open(filename, 'wb') as outp:
        pickle.dump(obj, outp, pickle.HIGHEST_PROTOCOL)

#credentials
username ="agromltlv@gmail.com"
#generated app password
app_password= "qlmgpjmmulrbsmco"
# https://www.systoolsgroup.com/imap/
gmail_host= 'imap.gmail.com'
#set connection
mail = imaplib.IMAP4_SSL(gmail_host)
#login
mail.login(username, app_password)
#select inbox
mail.select("INBOX")
#select specific mails
_, selected_mails = mail.search(None, '(TO "gh_data@agrodl.com")')
#total number of mails from specific user
print("Total Messages from gh_data@agrodl.com:" , len(selected_mails[0].split()))
# save every email from the client seperatly to be able to extract certain data later on
email_messages = []
messages = []
for num in selected_mails[0].split():
    _, data = mail.fetch(num , '(RFC822)')
    _, bytes_data = data[0]
    #convert the byte data to message
    email_message = email.message_from_bytes(bytes_data)
    print("\n===========================================")
    if "ROWS SETUP" not in email_message["subject"]:
      continue
    #access data
    print("Subject: ",email_message["subject"])
    print("To:", email_message["to"])
    print("From: ",email_message["from"])
    print("Date: ",email_message["date"])
    for part in email_message.walk():
        if part.get_content_type()=="text/plain" or part.get_content_type()=="text/html":
            message = part.get_payload(decode=True)
            print("Message: \n", message.decode())
            print("==========================================\n")
            email_messages.append(email_message)
            messages.append(message)
            break
            
gh_setup_dir_list = []
for i, email in enumerate(email_messages):
  if email["subject"].find("AgroDL ROWS SETUP") != -1:
    index = i
    email_str = messages[index].decode()
    # extracting fields of interest from the str email
    grower_email = email_str.split("Grower Email Address:")[1].split("\r")[0][2:-1]
    if grower_email.endswith("]"):
      grower_email = grower_email[0:-1]
    gh_unique_name = email_str.split("GH unique name:")[1].split("\r")[0][2:-1]
    if gh_unique_name.endswith("]"):
      gh_unique_name = gh_unique_name[0:-1]
    link = email_str.split("Download link:")[1].split("\r\r\n")[1]
    # reading the right directory from the XML file
    gh_setup_path = script_params.get_params("gh_setup_path_t")
    gh_dir = f"{gh_setup_path}/{grower_email}/{gh_unique_name}"
    if not os.path.exists(gh_dir):
      gh_setup_path = script_params.get_params("gh_setup_path_p")
      gh_dir = f"{gh_setup_path}/{grower_email}/{gh_unique_name}"
    # in case the GH hasn't been set prior trying setting the rows
    if not os.path.exists(gh_dir):
      print(f"Can't recognize the following GH: {gh_unique_name} of {grower_email}. Please set the GH first before the rows")
      sys.exit()
    rows_folder = f"{gh_dir}/rows_images"
    try:
      os.mkdir(rows_folder)
    except:
      print("rows images folder is already existing checking next GH")
    # extracting content from the wetranfer folder
    os.chdir("/content/drive/MyDrive/Colab_Notebooks/AgroML_Test_System/transferwee")
    subprocess.call(['python', 'transferwee.py', 'download', f'{link}'])
    # get the name of the zip folder which is located last within the dir
    for folder_to_unzip in os.listdir():
      pass
    # extracting downloaded zip file
    wetransfer_dir = os.getcwd()
    path_to_unzip = f"{wetransfer_dir}/{folder_to_unzip}"
    with ZipFile(path_to_unzip , 'r') as zObject:
      zObject.extractall(path=f"{wetransfer_dir}")
    # get the unzipped folder name
    for unzipped_folder in os.listdir():
      pass
    for image in os.listdir(unzipped_folder):
      if os.path.exists(f"{rows_folder}/{image}"):
        os.remove(f"{rows_folder}/{image}")
      shutil.move(f"{wetransfer_dir}/{unzipped_folder}/{image}", rows_folder)
    # remove the zipped file and the image folder
    os.remove(folder_to_unzip)
    os.rmdir(unzipped_folder)
    os.chdir("/content/drive/MyDrive/Colab_Notebooks")
    # load gh object to store and sort the beggining of rows coordinates
    file1 = open(f'{gh_dir}/gh_details/{gh_unique_name}.pkl', 'rb')
    gh_object = pickle.load(file1)
    # reading EXIF GPS data from the images
    row_images_cor = []
    for row_image in os.listdir(rows_folder):
      exif_obj = ADL_EXIF(f"{rows_folder}/{row_image}")
      image_cor = exif_obj.read_exif()
      row_images_cor.append(image_cor)
    # calculating the order of the lines
    gh_object.line_mapping(row_images_cor)
    # update the onject with the new attribute of the rowes
    save_object(gh_object, f'{gh_dir}/gh_details/{gh_unique_name}.pkl')
    
# delete email
_, selected_mails = mail.search(None, '(TO "gh_data@agrodl.com")')
#total number of mails from specific user
print("Total Messages from gh_data@agrodl.com:" , len(selected_mails[0].split()))
email_messages = []
messages = []

for num in selected_mails[0].split():
    _, data = mail.fetch(num , '(RFC822)')
    _, bytes_data = data[0]
    import email
    #convert the byte data to message
    email_message = email.message_from_bytes(bytes_data)
    print("\n===========================================")
    if "ROWS SETUP" in email_message["subject"]:
      mail.store(num, "+FLAGS", "\\Deleted")
    
    




