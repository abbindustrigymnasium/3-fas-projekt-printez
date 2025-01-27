# PrintEz
## Description
PrintEz is a 3d-printer-managing website with a focus on printers from Bambu labs, specifically the P1S.


## Planing and design
Our preliminary design and plans for this project: https://www.figma.com/design/BtAkAuIYfR6WDcD6cwmRW5/Printez?node-id=0-1&t=6FW0GLqrLv2Yiv9I-1

## Installation
### 1. Clone the repo
```bash
git clone https://github.com/abbindustrigymnasium/3-fas-projekt-printez.git {path_to_folder_of_project}
```
### 2. Cd into directory
```bash
cd {path_to_folder_of_project}
```
### 3. Install needed libraries
```bash
pip install -r requirements.txt
```
Note that there probably are some unnecessary libraries that have yet to be removed.
### 4. Necessary changes to bambuprintermanager lib
Follow the steps in libchanges/file_changes.md to update the bambuprintermanager this will hopefully be made into a module at some point when there's time.
### 5. Fix your .env file
Create a file in you project directory called .env, and fill it with all the information detailed in example.env.
Note that if any of your printer_names include underscores it might screw with the things since all spaces sometimes get converted to underscores and underscores to spaces.

### 6. Run app.py to start server
```bash
python backend/app.py
```
