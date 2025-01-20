
"""
File: printer_manager.py
Author: Samuel Olsson (fdABB-Gym-Samuel)
Date Created: 2024-11-26
Description: Module with a class used to manage multiple printers (made for P1S by bambulabs)
"""


# from bambulabs_api import *
import time
import sys

import requests
# from pathlib import Path
# sys.path.append(str(Path(__file__).resolve().parent.parent))
# from bambu_api_cloud.bambulabs_api import cloud2, client
from bpm.bambuconfig import BambuConfig
from bpm.bambuprinter import BambuPrinter
from bpm.bambutools import PrinterState, PlateType
from bpm.bambutools import parseStage
from bpm.bambutools import parseFan

import json

from dotenv import load_dotenv
import os

class printer_manager():
    def __init__(self, uid: str, access_token: str, region: str = "Europe"):
        load_dotenv()

        # Get environment variables for printers
        self.uid = uid
        self.cloud_username = f"u_{self.uid}"

        self.access_token = access_token
        self.region = region

        self.printers = {}
        self.files = {}

        self.cloud_host = "https://api.bambulab.com"

    def get_devices(self):
        endpoint = "/v1/iot-service/api/user/bind"
        # User agent needs to be specified to something, ohterwise bambulabs blocks it for some reason?!??!?!
        headers = {"Authorization": f"Bearer {self.access_token}",
                   "User-Agent": "curl/7.68.0"}
        res = requests.get(f"{self.cloud_host}{endpoint}", headers=headers)

        if not res.ok:
            print(f"ERROR got response {res}")
            raise Exception("Unable to get devices")
        else:
            return res.json()["devices"]


    def connect_printers(self, printers_to_connect):

        for printer in printers_to_connect:
            print(printer)
            try: 
                printer_ip = os.getenv(printer["name"].replace(" ", "_"))
            except KeyError:
                print("Printer Name and IP not found in .env")
            

            config = BambuConfig(ip=printer_ip, 
                                 access_code=printer["dev_access_code"], 
                                 mqtt_auth_token=self.access_token,
                                 serial_number=printer["dev_id"],
                                 mqtt_username_cloud=self.cloud_username)
            printer_instance = BambuPrinter(config=config)

            self.printers[printer["name"]] = printer_instance
            try: 
                self.printers[printer["name"]].start_session()
            except Exception as e:
                print("***WARNING***")
                print("Failed to connect to printer")
                print("***WARNING***")


            
         
    def print_states(self, states_to_print:list[str] = None):
        """
        Function to get the states of specified printers.

        Params:
            states_to_print: list[str] - The names of all the printers to get states from, if not specified it will print states for all printers
        Return:
            dict[str: str]:
                The states of specified printers in a dict with names as keys and the states as values
        """
        states = {}
        if states_to_print == None:
            states_to_print = self.NAMEs

        for name in states_to_print:
            
            states[name] = self.printers[name].get_state()

        return states
    
    def get_sdcard_files(self, printers: list | None = None, only_3mf_files: bool = True, get_from_printer = True):
        if printers == None:
            printers = list(self.printers.keys())
        printer_files = {}
        for printer in printers:
            if not get_from_printer:
                if not only_3mf_files:
                    printer_files[printer] = self.printers[printer]._sdcard_contents

                else:
                    printer_files[printer] = self.printers[printer].get_sdcard_3mf_files()


            else:    
                printer_files[printer] = self.printers[printer].get_sdcard_contents()

        self.files = printer_files
        return printer_files    
    
    def upload_print(self, printer_name:str, local_file_path:str, printer_file_path):
        """
        Function to upload file to printer (.gcode or .3mf)

        params:
            printer_name: str - Name of the printer to upload to, same as specified in .env
            file_path: str - Local path to file

        Return:
            str:
                Success:
                    file_path to uploaded file

                OnError:
                    "Invalid file extension" if extension isn't .gcode or .3mf
                    or
                    "No file uploaded." if an error occured during upload (will also raise exception)
        """
        return self.printers[printer_name].upload_sdcard_file(local_file_path, printer_file_path)


    def start_print_on_printer(self, printer_name:str, filename:str):
        """
        Function to start a print on a printer
        params:
            printer_name: str - Name of the printer to print on, same as specified in .env
            file_name: str - Name of file to print

        return:
            bool:
                Whether successful

        This function doesnt work, problem is believed to be that cloud connection is needed.
        """
        if filename.split(".")[-1] == "3mf":
            return self.printers[printer_name].start_print(filename, 1, False)



    def get_printer_info(self, printer_name):
        pass

    def disconnect_printers(self, printer_names:list[str] = None):
        if printer_names == None:
            printer_names = list(self.printers.keys())
            print(printer_names)

        print(self.printers)
        for printer_name in printer_names:
            self.printers[printer_name].quit()


if __name__ == "__main__":

    load_dotenv()

    UID = os.getenv("UID")
    ACCESS_TOKEN = os.getenv("CLOUD_ACCESS_TOKEN")
    REGION = os.getenv("REGION")

    p_man = printer_manager(UID, ACCESS_TOKEN, REGION)


    devices = p_man.get_devices()
    printers_to_connect_to = []
    # Chooses a single printer
    for printer in devices:
        if printer["name"] == "S2. Daenerys Targaryen":
            printers_to_connect_to.append(printer)

    p_man.connect_printers(printers_to_connect_to)
    # Need to sleep for a small amount of time after connect
    time.sleep(1)

    # Writes all printer files from all current printers to "printer_files.json"
    files = p_man.get_sdcard_files()
    with open("printer_files.json", "w") as file:
        file.write(json.dumps(files, indent=4))


    p_man.disconnect_printers()
