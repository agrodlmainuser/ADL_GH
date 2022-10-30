Conseptual Design:


This repository is in charge of the setup process of a GH. When a grower want to start add a new gh to the system and start to get detections, the GH to be detected should be defined in the system. Every GH is defined under the grower's email, therefore, every grower may have various GH's from different types. the path to every grower directory is as following: agrodl/agrodl_data/Input/*task*/*pepper_or_tomato*/*grower's email*/*gh* note that as long as the type of the crop is either tomato or pepper, all gh types may be under the same directory. Tomatoes and peppers can't be mixed though and are seperated in directories.

input from the user: a set of 3/4 photos of the gh corners, a set of photos of every row beggining, description of the gh in the following format:

Grower Name: [name of the grower]
Grower Address: [address of the grower]
Grower Email Address: [grower’s email address]
Plant: [pepper or tomato]
GH unique name: [the unique name of the gh]
Tel: [grower’s telephone]

Note that all images should contain EXIF GPS data.

the program will create the main gh directory and will add 3 sub-directories as follows:

- gh dir
  - corners (image of every corner)
  - row_images (image of every row beggining)
  - details (csv file with the details + gh object with the abillity to detect whether an image is from the gh or not)


Technical Description:

the repository contains 3 main scripts: 

first_gh_setup.py - This script is in charge of the very first setup of the GH. The program is scanning the inbox of agromltlv@gmail.com email to find a match to "GH SETUP" phrase. 
