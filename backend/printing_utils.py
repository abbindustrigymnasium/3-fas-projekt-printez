import zipfile

def extract_bambulab_estimated_time(printfile_filepath:str) -> int | list[None, str]:
    """
    Function to get the total time (prep and printing) for a 3mf file to print. Bambustudio and maybe other slicer make a comment somewhere at the top of the 3mf-file's gcode file
    with an estimate for the amount of time it will take to print a file. It's known that this is a bad way to do it, since a user can simply extract the
    3mf-file and manually set the time to some low number, negative even, in order to skip the queue. So just keep quiet about it.

    Params:
        - str:
            printfile_filepath: Path to the file which time is supposed to be collected.

    Returns:
        - int:
            an estimation for the total amount of seconds it will take to print the file
    """

    try:
        with zipfile.ZipFile(printfile_filepath, 'r') as archive:
            files = archive.namelist()
            gcode_files = [f for f in files if f.endswith('.gcode')]
            
            if not gcode_files:
                return None, "No gcode_file found"
            
            gcode_file = gcode_files[0] # Please, oh please, don't let this come and bite me in the ass
            
            # Read at most the first 50 lines of file
            with archive.open(gcode_file, 'r') as gcode:
                for _ in range(50):
                    line = gcode.readline()
                    line = line.decode('utf-8').strip()

                    if "total estimated time:" in line.lower():
                        estimated_time = parse_estimated_time_line(line)
                        return estimated_time

        
    except zipfile.BadZipFile:
        return None, "The provided file is not a valid .3mf archive."

    except Exception as e:
        return None, f"Error: {e}"
    


def parse_estimated_time_line(line: str):
    """
    Simple function to parse time from a string of "{num_hs}h {num_mins}m {num_secs}s" to an int of number of seconds

    Params:
        - str:
            line: the line to parse

    Return:
        - int:
            total_seconds: the total amount of seconds to print including preparations
    """

    time_string = line.split("total estimated time: ")[1]
    
    total_seconds = 0
    if "h" in time_string:
        hours = int(time_string.split("h")[0].strip())
        total_seconds += hours * 3600
        time_string = time_string.split("h")[1].strip()

    if "m" in time_string:
        minutes = int(time_string.split("m")[0].strip())
        total_seconds += minutes * 60
        time_string = time_string.split("m")[1].strip()
    
    if "s" in time_string:
        seconds = int(time_string.split("s")[0].strip())
        total_seconds += seconds

    if total_seconds == 0:
        raise Exception("Unable to parse time")

    return total_seconds



if __name__ == "__main__":
    three_mf_filepath = "backend/uploads/gear_crank.gcode.3mf" 
    
    print(extract_bambulab_estimated_time(three_mf_filepath))