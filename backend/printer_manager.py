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

        self.devices = {}
        self.printers = {}
        self.files = {}

        self.cloud_host = "https://api.bambulab.com"

    def get_devices(self):
        """
        Gets all devices connected to cloud user.

        Params:
            No Params

        Return:
            - dict[str: str | float]
                Dict of devices with info about each printer
                Example output:
                    [
                        {
                            "dev_id": {PRINTER_SERIAL_NUMBER: str},
                            "name": {PRINTER_NAME: str},
                            "online": {IS_ONLINE: bool},
                            "print_status": {STATUS: str},
                            "dev_model_name": {MODEL: str},
                            "dev_product_name": {PRODUCT_NAME: str},
                            "dev_access_code": {ACCESS_CODE: str},
                            "nozzle_diameter": {DIAMETER: float},
                            "dev_structure": {STRUCTURE: str}
                        },
                        ...]

        Exceptions:
            - Unable to get devices
                request to the endpoint resulted in res.ok being false, wont return anything
        """

        endpoint = "/v1/iot-service/api/user/bind"
        # User agent needs to be specified to something, ohterwise bambulabs blocks it for some reason?!??!?!
        headers = {"Authorization": f"Bearer {self.access_token}",
                   "User-Agent": "curl/7.68.0"}
        res = requests.get(f"{self.cloud_host}{endpoint}", headers=headers)

        if not res.ok:
            print(f"ERROR got response {res}")
            raise Exception("Unable to get devices")
        elif res.status_code == 401:
            print(f"Status from get devices is {res}, this probably means that your access token is invalid, please check it")
        else:
            self.devices = res.json()["devices"]
            return res.json()["devices"]

    def connect_printers(self, printers_to_connect: list[str]):
        """
        Connects to all printers with the names of the printers. It is recommeded to use some sleeping function after calling this

        Params:
            - list[str]
                - printers_to_connect: List of names of the printers to connect to, these names can be gotten with self.get_devices

        Returns:
            - None

        example usage: printer_manager.connect_printers(["my_printer_1", "my_printer_2", "my_printer_3"])
        """

        for printer in printers_to_connect:
            try: 
                printer_ip = os.getenv(printer["name"].replace(" ", "_"))
            except KeyError:
                print("Printer Name and IP not found in .env")
            
            if not self.access_token or not self.cloud_username:
                print("***WARNING***")
                print("access_token and cloud_username need to be defined to use cloud services")
                print("***WARNING***")


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
                print(f"Recieved exception: {e}")
                print("***WARNING***")

    def pushall(self, printers_to_push: list[str] | None = None):
        """
        Function to push all informatino of all printers. This will resend it from the printer. To use the information that exists in memory, use to_json().
        It is also necessary to call to_json() after

        Params:
            - list[str]
                - printers_to_push: The names of all printers which complete states should be refreshed
        
        Returns:
            - None
        """
        if printers_to_push == None:
            printers_to_push = list(self.printers.keys())

        for printer_name in printers_to_push:
            try:
                self.printers[printer_name].refresh() 
            except KeyError:
                print("Printer name not found in among printers") 
            
    def get_tasks_info(self, states_to_print:list[str] = None):
        """
        Function to get the states of specified printers.

        Params:
            states_to_print: list[str] | None - The names of all the printers to get states from, if not specified it will print states for all printers
        Return:
            dict[str: str]:
                The states of specified printers in a dict with names as keys and the states as values
        """
        if states_to_print == None:
            states_to_print = list(self.printers.keys())
        
        states = {}
        for name in states_to_print:
            
            states[name] = {"time_remaining": self.printers[name]._time_remaining,
                            "subtask_name": self.printers[name]._subtask_name,
                            "total_layers": self.printers[name]._layer_count,
                            "current_layer": self.printers[name]._current_layer,
                            "current_stage": self.printers[name]._current_stage,
                            "current_stage_text": self.printers[name]._current_stage_text,
                            "gcode_state": self.printers[name].gcode_state,
                            "percentage_complete": self.printers[name]._percent_complete}

        return states
    
    def get_printer_states(self, printers: list[str] | None = None):
        """
        Function to get the gcode_state (can be something like "RUNNING", "FINISHED", "FAILED" or "PREPARING")

        Params:
            - list[str]
                -printers: The names of all the printers which g_code_states to get, if set to None or not set at all will default to all printers currently registered to printer_manager

        Returns:
            -dict[str: str]
                - states: Dict with printer_names as keys and the states as values
        """
        if printers == None:
            printers = list(self.printers.keys())

        states = {}
        for printer in printers:
            states[printer] = self.printers[printer].gcode_state
    
    def to_json(self, printers: list[str] | None = None):
        """
        Function to get all information stored about a specific printer.

        Params:
            - list[str]
                - printers: Names of printers to get states of. If set to None or not set at all it will default to all printers currently registered to the printer_manager

        Returns:
            - dict[str: dict]
                - infos: The complete information on all printers requested. The names of the printers being the keys and the infos (dicts themselves) being the info on a specific printer 
        """
        if printers == None:
            printers = self.printers

        infos = {}
        for printer in printers:
            infos[printer] = self.printers[printer].toJson()

        return infos
    
    def get_sdcard_files(self, printers: list | None = None, only_3mf_files: bool = True, get_from_printer = True):
        """
        Function to return get the files of all the printers specified, this uses ftps and needs to be done when connected to the same wifi as the printers
        """
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
    
    def upload_print(self, printer_name:str, local_file_path:str, printer_file_path:str):
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
            return self.printers[printer_name].print_3mf_file(filename, 1, PlateType.TEXTURED_PLATE, False)
        
    def stop_print_on_printers(self, printer_names:list[str] = None):
        """
        Function to stop printing on printers

        Params:
            - list[str]
                printer_names: List containing the printers that should stop printing
        
        Returns:
            - dict[str: bool]
                plates_clean: Dict with the printer_names as keys and whether there plates are clean as the values.
        """
        if printer_names is None:
            printer_names = list(self.printers.keys())

        plates_clean = {}
        for printer_name in printer_names:
            printer_gcode_state = self.printers[printer_name].gcode_state
            plates_clean[printer_name] = True if printer_gcode_state == "IDLE" or printer_gcode_state == "PREPARING" else False
            self.printers[printer_name].stop_printing()

        return plates_clean
    
    def id_is_printing(self, print_id):
        """
        Function to get if a print_id is being printed on a printer

        params:
            uuid4:
                print_id: Id of print, generated by printer_manager

        returns:
            If it is pringting
            str:
                printer_name: Name of printer printing the print
            
            dict:
                currently_printing: dict in the format of {"print_id": {print_id of print, uuid}, "owner": {owner of print should be from JWT, but unknown at this stage as im not sure what information it has}, "filename": {name of file, this inlcudes the uuid}}
            
            str:
                gcode_state: The current state of the gcode, i.e whether it is printing, idle or finished


            If print_id isn't printing
            bool:
                False   

            as well as two empty strings to allow for unpacking     
        """
        for printer_name, printer in self.printers.items():
            if printer.currently_printing["print_id"] == print_id:
                return printer_name, printer.currently_printing, printer.gcode_state
            
        return False, "", ""

    def disconnect_printers(self, printer_names:list[str] = None):
        if printer_names == None:
            printer_names = list(self.printers.keys())

        for printer_name in printer_names:
            self.printers[printer_name].quit()


if __name__ == "__main__":

    load_dotenv()

    UID = os.getenv("UID")
    ACCESS_TOKEN = os.getenv("CLOUD_ACCESS_TOKEN")
    REGION = os.getenv("REGION")

    p_man = printer_manager(UID, ACCESS_TOKEN, REGION)


    devices = p_man.get_devices()
    # print(devices)
    printers_to_connect_to = []
    # Chooses a single printer
    for printer in devices:
        if printer["name"][0] == "S" and printer["name"][1] != "6":
            printers_to_connect_to.append(printer)

    p_man.connect_printers(printers_to_connect_to)
    # Need to sleep for a small amount of time after connect
    time.sleep(2)

    # p_man.pushall()

    # for printer_name, printer in p_man.printers.items():
    p_man.to_json(["S2. Daenerys Targaryen"])

    time.sleep(5)
    print(p_man.get_tasks_info())

    # p_man.start_print_on_printer("Printer_name", "/cache/file_on_printer.gcode.3mf")

    # with open("devices.json", "w") as devices_file:
    #     devices_file.write(json.dumps(devices, indent=4))

    # # Writes all printer files from all current printers to "printer_files.json"
    # files = p_man.get_sdcard_files()
    # with open("printer_files.json", "w") as file:
    #     file.write(json.dumps(files, indent=4))


    p_man.disconnect_printers()