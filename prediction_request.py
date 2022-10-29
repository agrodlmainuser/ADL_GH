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
import imaplib
import email
from imbox import Imbox # pip install imbox
import traceback
import sys

script_params = ADL_Read_XML("AgroDL_GH_Crop_Estimation_0000")
GH_CHECKER = ADL_img_gh()


#credentials
username ="agromltlv@gmail.com"
#generated app password
app_password= "qlmgpjmmulrbsmco"
# https://www.systoolsgroup.com/imap/
gmail_host= 'imap.gmail.com'
#set connection
mailbox = imaplib.IMAP4_SSL(gmail_host)
#login
mailbox.login(username, app_password)
#select inbox
mailbox.select("INBOX")
#select specific mails
_, selected_mails = mailbox.search(None, '(TO "gh_data@agrodl.com")')
#total number of mails from specific user
print("Total Messages from gh_data@agrodl.com:" , len(selected_mails[0].split()))
# save every email from the client seperatly to be able to extract certain data later on
email_messages = []
messages = []

for num in selected_mails[0].split():
    _, data = mailbox.fetch(num , '(RFC822)')
    _, bytes_data = data[0]

    #convert the byte data to message
    email_message = email.message_from_bytes(bytes_data)
    print("\n===========================================")
    if "CROP ESTIMATION" not in email_message["subject"]:
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
grower_list_dir = []
for i, email in enumerate(email_messages):
  if email["subject"].find("CROP ESTIMATION") != -1 or email["subject"].find("GH CROP ESTIMATION") != -1:
    index = i
    email_str = messages[index].decode()
    # extracting fields of interest from the str email
    grower_email = email_str.split("Grower Email Address:")[1].split("\r")[0][2:-1].lower()
    gh_unique_name = email_str.split("GH unique name:")[1].split("\r")[0][2:-1].lower()
    # reading the right directory from the XML file
    gh_setup_path = script_params.get_params("gh_setup_path_t")
    grower_dir = f"{gh_setup_path}/{grower_email}"
    gh_dir = f"{grower_dir}/{gh_unique_name}"
    if not os.path.exists(gh_dir):
      gh_setup_path = script_params.get_params("gh_setup_path_p")
      gh_dir = f"{gh_setup_path}/{grower_email}/{gh_unique_name}"
    # in case no GH is found in the system
    if not os.path.exists(gh_dir):
      print(f"Can't recognize the following GH: {gh_unique_name} of {grower_email}. Please set the GH first")
      sys.exit()
    grower_list_dir.append(grower_dir)
    gh_setup_dir_list.append(gh_dir)

mail = Imbox(gmail_host, username=username, password=app_password, ssl=True, ssl_context=None, starttls=False)
#messages = mail.messages() # defaults to inbox
messages = mail.messages(subject='CROP ESTIMATION')
for i, (uid, message) in enumerate(messages):
    print(i)
    mail.mark_seen(uid) # optional, mark message as read
    download_folder = gh_setup_dir_list[i]
    current_grower_dir = grower_list_dir[i]
    for idx, attachment in enumerate(message.attachments):
        try:
            att_fn = attachment.get('filename')
            download_path = f"{download_folder}/{att_fn}"
            print(download_path)
            with open(download_path, "wb") as fp:
                fp.write(attachment.get('content').read())
        except:
            print(traceback.print_exc())
            continue
    # checking if the coordinates matched the selected gh
    gh_checking_obj = ADL_img_gh()
    in_right_path = gh_checking_obj.check_in_current_gh(download_folder, download_path)
    if in_right_path:
      continue
    else:
      new_gh = gh_checking_obj.check_in_grower_dir(current_grower_dir, download_path)
      if not new gh:
        print("check with the grower for clarification")
      else:
        new_gh_dir = f"{current_grower_dir}/{new_gh}"
        shutil.move(download_path, f"{new_gh_dir}/{att_fn}")

mail.logout()

#delete email from inbox 
import email
_, selected_mails = mailbox.search(None, '(TO "gh_data@agrodl.com")')
#total number of mails from specific user
print("Total Messages from gh_data@agrodl.com:" , len(selected_mails[0].split()))
# save every email from the client seperatly to be able to extract certain data later on
email_messages = []
messages = []

for num in selected_mails[0].split():
    _, data = mailbox.fetch(num , '(RFC822)')
    _, bytes_data = data[0]

    #convert the byte data to message
    email_message = email.message_from_bytes(bytes_data)
    print("\n===========================================")
    if "CROP ESTIMATION" in email_message["subject"]:
      mailbox.store(num, "+FLAGS", "\\Deleted")
