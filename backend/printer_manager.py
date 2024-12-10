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

        This function doesnt work, problem is believed to be that cloud connection is needed.
        """
        return self.printers[printer_name].start_print(file_name, 0)

    def get_printer_info(self, printer_name):
        pass

    def disconnect_printers(self, printer_names:list[str] = None):
        if printer_names == None:
            printer_names = list(self.printers.keys())
        for printer_name in printer_names:
            self.printers[printer_name].disconnect()


if __name__ == "__main__":
    import time
    p_man = printer_manager()
    time.sleep(2)

    # # Get the printer status
    # states = p_man.print_states()
    # print(list(p_man.printers.keys())[0])
    printer_names = list(p_man.printers.keys())
    # with open("prints/fan2.3mf", "rb") as file:
    #     print(file.read())
    # print("Uploading")
    # p_man.upload_print(printer_names[0], "prints/fan4.gcode")
    # print("Finished upload")
    # time.sleep(2)
    printer_1 = list(p_man.printers.keys())[0]
    # print(p_man.printers[printer_1])
    # print(p_man.printers[printer_1].PrintStatus.PRINTING)

    # print(p_man.printers[printer_1].get_file_name())
    # print("Trying to start print")
    # p_man.printers[printer_1].start_print("fan3.gcode.3mf", 1)
    # print("Command sent, hopefully")

    p_man.printers[printer_1].turn_light_on()
    time.sleep(3)
    frame = p_man.printers[printer_1].get_camera_frame()
    with open("tests/image_frame.html", "w") as frame_file:
        frame_txt = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Display Base64 Image</title>
</head>
<body>
    <h1>Displaying Base64 Image</h1>
    <img src="data:image/png;base64,{frame}" alt="Base64 Image" />
</body>
</html>
"""
        frame_file.write(frame_txt)


    # print(f'Printer status: {states}')
    # print("Starting print")
    # print(p_man.start_print(list(p_man.printers.keys())[0], "fan4.gcode"))
    # print("here")
    # p_man.disconnect_printers()

