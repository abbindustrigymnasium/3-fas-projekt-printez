"""
File: printer_manager.py
Author: Samuel Olsson (fdABB-Gym-Samuel)
Date Created: 2024-11-26
Description: Module with a class used to manage multiple printers (made for P1S by bambulabs)
"""


from bambulabs_api import *
from dotenv import load_dotenv
import os

class printer_manager():
    def __init__(self):
        load_dotenv()

        # Get environment variables for printers
        self.NAMEs = os.getenv("Printer_NAMEs").split(",")
        self.IPs = os.getenv("Printer_IPs").split(",")
        self.SERIALs = os.getenv("Printer_SERIALs").split(",")
        self.ACCESS_CODEs = os.getenv("Printer_ACCESS_CODEs").split(",")

        self.printers = {}

        # Add printers to the printer_managers "printers" dictionary, with its name as the key and the printer of class Printer as value
        # Then connects to the printer
        for name, ip, serial, access_code in zip(self.NAMEs, self.IPs, self.SERIALs, self.ACCESS_CODEs):
            print(f"name: {name}\nip: {ip}\nserial: {serial}\naccess_code: {access_code}")
            self.printers[name] = Printer(ip, access_code, serial)
            self.printers[name].connect()

         
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
    
    def upload_print(self, printer_name:str, file_path:str):
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
        if file_path.split(".")[-1] != "gcode" and file_path.split(".")[-1] != "3mf":
            return "Invalid file extension"

        with open(file_path, "rb") as file:
            file_name = file_path.split("/")[-1]
            return self.printers[printer_name].upload_file(file, file_name)

    def start_print(self, printer_name:str, file_name:str):
        """
        Function to start a print on a printer
        params:
            printer_name: str - Name of the printer to print on, same as specified in .env
            file_name: str - Name of file to print

        return:
            bool:
                Whether successful

        Possible problems: "plate_number" prameter is always set to 1, I have no idea what it is or if it should be changed depending on the print
        THIS FUNCTION HAS YET TO BE TESTED!!!
        """
        return self.printers[printer_name].start_print(file_name, 1)

    def get_printer_info(self, printer_name):
        pass


if __name__ == "__main__":
    import time
    p_man = printer_manager()
    time.sleep(2)

    # # Get the printer status
    states = p_man.print_states()
    # print(list(p_man.printers.keys())[0])
    # printer_names = list(p_man.printers.keys())
    # with open("prints/fan2.3mf", "rb") as file:
    #     print(file.read())
    # p_man.upload_print(printer_names[0], "prints/fan2.3mf")

    print(f'Printer status: {states}')

