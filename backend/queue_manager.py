"""
File for queue_manager. The class that should handle the queue of prints with functions to add, remove and get prints.
"""

"""
Structure for a print_dict:
print_id = {
    "owner": owner_of_print:str,
    "file_path": file_path:str,
    "Estimated_time_to_print": est_time:int,
    "Time_waited": time_waited:int,
    "wait_to_end_of_day": wait_to_end_of_day:bool 
}
"""
from uuid import uuid4
from datetime import datetime

class queue_manager():
    def __init__(self):
        self.prints = {}
        self.max_time_during_day = 60*45
        self.last_added_time = int(datetime.now().timestamp())

    def add_new_print(self, owner:str, file_path:str, estim_time:int):
        """
        Function to add new print to prints.
        Params: 
            owner (string) - owner of print,
            file_path (string) - path to print file,
            estim_time (int) - estimate for how long the print will take in seconds

        Return:
            print_id (uuid) - an id to tie to user, for accessing the print
            successful (bool) - whether print was added
        """
        self.update_print_times()
        wait_to_end_of_day = True if estim_time > self.max_time_during_day else False
        print_id = uuid4()
        self.prints[print_id] = {
            "owner": owner,
            "file_path": file_path,
            "estimated_time_to_print": estim_time,
            "time_waited": 0,
            "wait_to_end_of_day": wait_to_end_of_day
        }

        successful = True if self.prints[print_id] else False
        return print_id, successful

    def remove_print(self, print_to_remove: str):
        """
        Remove print from prints by the id.
        Params: 
            print_to_remove (string) - uuid of the print to remove

        Return: 
            Successful (bool) - whether removing was successful,
            Reason (string) - reason for failure (if known), empty string on success
        """ 
        try:
            self.prints.pop(print_to_remove)
        except KeyError:
            return False, "print_not_found"
        except Exception as e:
            return False, str(e)
        
        successful = True if print_to_remove not in self.prints else False
        return successful, ""
        

    def update_print_times(self):
        """
        Update the times for all prints in the list, based on how much time has passed since the last update.
        """
        now_time = int(datetime.now().timestamp())
        for print_id in self.prints:
            self.prints[print_id]["time_waited"] += now_time - self.last_added_time

        self.last_added_time = now_time

    def get_next_print(self):
        """
        Function to get the next print to print based on the expected time to print and for how long it has been waiting.

        Return: 
            uuid (uuid/string) - uuid of print to print, None if prints is empty 
        """
        self.update_print_times()
        current_shortest_print = [None, float("inf")]
        
        for print_id in self.prints:
            time_diff = self.prints[print_id]["estimated_time_to_print"] - self.prints[print_id]["time_waited"]
            if self.prints[print_id]["wait_to_end_of_day"] and datetime.now().hour <= 16:
                continue

            if current_shortest_print[0] == None:
                current_shortest_print = [print_id, time_diff]
                continue
            
            if time_diff < current_shortest_print[1]:
                current_shortest_print = [print_id, time_diff]

        return current_shortest_print[0]


# #BadTestingRules
if __name__ == "__main__":
    from time import sleep
    q_man = queue_manager()
    print_id1, succ_1 = q_man.add_new_print("1", "", 3600)
    sleep(15)
    print("1")
    print_id2, succ_2 = q_man.add_new_print("2", "", 1800)
    sleep(10)
    print("2")
    print_id3, succ_3 = q_man.add_new_print("3", "", 1800)
    sleep(20)
    print("3")
    print_id4, succ_4 = q_man.add_new_print("4", "", 1800)
    sleep(5)
    print("4")
    print_id5, succ_5 = q_man.add_new_print("5", "", 2701)
    print_id = q_man.get_next_print()
    print(q_man.prints)
    print(print_id)

    