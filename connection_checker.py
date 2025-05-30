from comms.connection_check import *
from comms.updateJSON import *
from time import sleep

### TO RUN ON PI A ###
PIB_IP = "10.42.0.60"
if __name__ == "__main__":
    try: 
        while True:
            # Check and update internet connection
            if check_connection():
                updateInternetconnection(CONFIGURATION_FILE_PATH,True)
            else:
                updateInternetconnection(CONFIGURATION_FILE_PATH,False)

            # Check and update connection to PiB 
            if check_connection(PIB_IP, port=22):
                updatePiConnection(CONFIGURATION_FILE_PATH, True)
            else:
                updatePiConnection(CONFIGURATION_FILE_PATH, False)

            sleep(3)
    except KeyboardInterrupt:
        print("\nFinished Connection")