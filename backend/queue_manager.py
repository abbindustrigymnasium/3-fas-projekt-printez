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
        self.start_of_day_hour = 8
        self.end_of_day_hour = 16

    def get_uuid(self):
        return uuid4()

    def add_new_print(self, owner:str, filepath:str, estim_time:int, print_id: uuid4 = uuid4()):
        """
        Function to add new print to prints.
        
        Params: 
            owner (string) - owner of print,
            file_path (string) - path to print file,
            estim_time (int) - estimate for how long the print will take in seconds
            print_id (uuid4) - Unique identifier for print in queue, can be gotten through self.get_uuid(), defaults to a random uuid as it should.
                               The primary function of having this as a param is that it allows one to save a file with a unique name, before adding 
                               the corresponding print to the queue 

        Return:
            print_id (uuid4) - same as the param, but in case one didn't choose one
            successful (bool) - whether print was added
        """
        self.update_print_times()
        wait_to_end_of_day = estim_time > self.max_time_during_day
        filepath_parts = filepath.split('.', 2)  # Split into at most 3 parts
        filepath_with_uuid = f".{filepath_parts[1]}_{str(print_id)}.{filepath_parts[2]}"

        self.prints[print_id] = {
            "owner": owner,
            "file_path": filepath_with_uuid,
            "estimated_time_to_print": estim_time,
            "time_waited": 0,
            "wait_to_end_of_day": wait_to_end_of_day,
            "time_diff": estim_time
        }


        successful = True if self.prints[print_id] else False
        return print_id, successful

    def remove_print(self, print_to_remove: str):
        """
        Remove print from prints by the id.
        Params: 
            print_to_remove (uuid4) - uuid of the print to remove

        Return: 
            bool:
                whether removing was successful
            
            str:
                reason for failure (if known), empty string on success
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

        params:
            None

        return:
            None
        """
        now_time = int(datetime.now().timestamp())
        for print_id in self.prints:
            self.prints[print_id]["time_waited"] += now_time - self.last_added_time
            self.prints[print_id]["time_diff"] = self.prints[print_id]["estimated_time_to_print"] - self.prints[print_id]["time_waited"]
            

        self.last_added_time = now_time

    def get_next_print(self):
        """
        Function to get the next print to print based on the expected time to print and for how long it has been waiting.

        params:
            None

        return: 
            if queue_manager.prints is empty:
                None

            else:
                uuid/string - uuid of print to print 
        """
        self.update_print_times()
        if datetime.now().hour < 16: 
            filtered_prints = [
                (print_name, print_info)
                for print_name, print_info in self.prints.items()
                if not print_info.get('wait_to_end_of_day', True)
            ]
        else:
            filtered_prints = [
                (print_name, print_info) 
                for print_name, print_info in self.prints.items()
            ]

        
        if not filtered_prints:
            filtered_prints = self.prints

        next_print = min(filtered_prints, key=lambda x: x[1]['time_diff'])

        if next_print:
            return next_print[0]

        return None

    
    def get_prelim_queue(self, current_prints: dict[str:int]):
        """
        Function to sort prints in que in order of time diff to give an estimation of queue order
        """
        try:
            sorted_queue = dict(sorted(self.prints.items(), key=lambda x: x[1]['time_diff']))
            time_waited_total = 0
            _printers = {key:val*60 for key, val in current_prints.items()}
            prelim_queue = []
            # Should be revised to use a while loop to skip prints based on the estimated_time of day
            for next_uuid, next_values in sorted_queue.items():
                next_print_to_finish = min(_printers.items(), key=lambda x: x[1])

                time_waited_since_swap = next_print_to_finish[1]
                time_waited_total += next_print_to_finish[1]

                prelim_queue.append({str(next_uuid):{"estimated_time_to_completion": (next_values["estimated_time_to_print"] + time_waited_total)//60, "file_name": next_values["file_path"]}})

                sorted_queue[next_uuid] = float("inf")
                _printers[next_print_to_finish[0]] = next_values["estimated_time_to_print"]

                _printers = {key:val-time_waited_since_swap for key, val in _printers.items()}
        except Exception as e:
            print("Something is fucked", str(e))
        return prelim_queue


# #BadTestingRules
if __name__ == "__main__":
    from time import sleep
    q_man = queue_manager()
    print_id1, succ_1 = q_man.add_new_print("1", "", 3600)
    sleep(3)
    print("1")
    print_id2, succ_2 = q_man.add_new_print("2", "", 1800)
    sleep(2)
    print("2")
    print_id3, succ_3 = q_man.add_new_print("3", "", 1800)
    sleep(1)
    print("3")
    print_id4, succ_4 = q_man.add_new_print("4", "", 1800, 0)
    sleep(5)
    print("4")
    print_id5, succ_5 = q_man.add_new_print("5", "", 2701)
    # print_id = q_man.get_next_print()
    q_man.get_prelim_queue({"1": 5, "2": 3, "3": 1})
    # print(q_man.prints)
    # print(print_id)

    