import PIL
from ADL_classes import ADL_EXIF
from ADL_classes import ADL_gh
from ADL_classes import ADL_Read_XML
import xml.etree.ElementTree as ET
import os
import pandas as pd
import re
import pickle 
import imaplib
import email
import os
from imbox import Imbox # pip install imbox
import traceback

#for reading the corners photos from the email
!pip install imbox
# reading directories from xml file
gh_setup_dir_list = []
script_params = ADL_Read_XML("AgroDL_GHsetup_0000")
# for the pickle class 
def save_object(obj, filename):
    with open(filename, 'wb') as outp:
        pickle.dump(obj, outp, pickle.HIGHEST_PROTOCOL)

#credentials - emails from growers are sent to gh_data@agrodl.com and are redirected to agromltlv
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
    if "GH SETUP" not in email_message["subject"]:
      continue
    #access data
    print("Subject: ",email_message["subject"])
    print("To:", email_message["to"])
    print("From: ",email_message["from"])
    print("Date: ",email_message["date"])
    for part in email_message.walk():
        if part.get_content_type()=="text/plain" or part.get_content_type()=="text/html":
            message = part.get_payload(decode=True)
            email_messages.append(email_message)
            messages.append(message)
            print("Message: \n", message.decode())
            print("==========================================\n")
            break
# extraction of relevant emails
gh_setup_dir_list = []
for i, email in enumerate(email_messages):
    if email["subject"].find("GH SETUP") != -1:
        index = i
        email_str = messages[index].decode()
        # extracting fields of interest from the str email
        dict1 = {}
        plant_gh = email_str.split("Plant:")[1].split("\r")[0]
        grower_name = email_str.split("Grower Name:")[1].split("\r")[0]
        grower_address = email_str.split("Grower Address:")[1].split("\r")[0]
        grower_tel = email_str.split("Tel:")[1].split("\r")[0]
        grower_email = email_str.split("Grower Email Address:")[1].split("\r")[0]
        gh_unique_name = email_str.split("GH unique name:")[1].split("\r")[0]
        # adding the fields into the dictionary
        dict1["plant_gh"] = plant_gh[2:-1]
        dict1["grower_name"] = [grower_name]
        dict1["grower_address"] = [grower_address]
        dict1["grower_tel"] = [grower_tel]
        dict1["grower_email"] = grower_email[2:-1]
        dict1["gh_unique_name"] = gh_unique_name[2:-1]
        # reading the right directory from the XML file
        if plant_gh[2:-1] == "tomato" or plant_gh[2:-1] == "tometo":
            gh_setup_path = script_params.get_params("gh_setup_path_t")
        elif plant_gh[2:-1] == "pepper":
            gh_setup_path = script_params.get_params("gh_setup_path_p")
        # creating a pd df
        df1 = pd.DataFrame.from_dict(dict1)
        # Save into csv, if GH has already been set, we will skip to the next iteration
        # to re-check if the new GH setup email is our system or not
        grower_email = grower_email[2:-1].lower()
        gh_unique_name = gh_unique_name[2:-1].lower()
        grower_dir = f"{gh_setup_path}/{grower_email}"
        gh_dir = f"{grower_dir}/{gh_unique_name}"
        gh_setup_dir_list.append(gh_dir)
        try:
            os.mkdir(grower_dir)
        except:
            print("sub dir already exists, checking if the client's GH has already been set in the past")
        try:
            os.mkdir(gh_dir)
        except:
            print(f"{gh_unique_name} GH of {grower_email} is already saved in the system, system will check the next GH setup email")
            continue
        try:
            os.mkdir(f"{gh_dir}/gh_details")
        except:
            print(f"{gh_dir}/gh_details path is already existed")
        df1.to_csv(f"{gh_dir}/gh_details/{gh_unique_name}.csv")

# extracting the corners images from the email and send them to the gh directory
mail_imbox = Imbox(gmail_host, username=username, password=app_password, ssl=True, ssl_context=None, starttls=False)
#messages = mail_imbox.messages() # defaults to inbox
messages = mail_imbox.messages(subject='GH SETUP')
for i, (uid, message) in enumerate(messages):
    print("extracting corner images from GH SETUP email")
    mail_imbox.mark_seen(uid) # optional, mark message as read
    try:
      corners_folder = f"{gh_setup_dir_list[i]}/corners_images"
      os.mkdir(corners_folder)
    except:
      corners_folder = f"{gh_setup_dir_list[i]}/corners_images"
      print(f"{corners_folder} dir already exists")
    download_folder = corners_folder
    for idx, attachment in enumerate(message.attachments):
        try:
            att_fn = attachment.get('filename')
            download_path = f"{download_folder}/{att_fn}"
            print(download_path)
            with open(download_path, "wb") as fp:
                fp.write(attachment.get('content').read())
        except:
            print(traceback.print_exc())
mail_imbox.logout()

#Read the GPS data from the gh corners images

for gh_cor_images_path in gh_setup_dir_list:
    images_cor = []
    for image in os.listdir(f"{gh_cor_images_path}/corners_images"):
        if not image.endswith("jpg"):
            continue
        else:
            try:
                exif_obj = ADL_EXIF(f"{gh_cor_images_path}/corners_images/{image}")
                image_cor = exif_obj.read_exif()
                images_cor.append(image_cor)
            except:
                print(f"GPS of the following image {image} is missing")
                continue
  # defining gh object
    gh = ADL_gh(images_cor)
    try:
        gh_name = gh_cor_images_path.split(".com/")[1]
    except:
        pass
    try:
        gh_name = gh_cor_images_path.split(".il/")[1]
    except:
        pass
    try:
        gh_name = gh_cor_images_path.split(">/")[1]
    except:
        pass
    # Calculating 4th corner + naming all corners_images
    try:
        gh.setup()
        save_object(gh, f'{gh_cor_images_path}/gh_details/{gh_name}.pkl')
        print(f"GH object for {gh_name} has been seccessfully created")
    except:
        print(f"couldn't create gh object for the following gh: {gh_name}")


#Delete setup messages from inbox

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
    if "GH SETUP" in email_message["subject"]:
      mail.store(num, "+FLAGS", "\\Deleted")

