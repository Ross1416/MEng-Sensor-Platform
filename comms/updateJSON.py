import json
import cv2
import numpy as np
import requests

# PROPOSED JSON STRUCTURE
    # {
    # location: string
    # pins: [
    #   {
    #       geo_coords: [lon, lat]
    #       panorama_ref: './imgref'
    #       objects: [
    #           {
    #           x1: int
    #           y1: int
    #           x2: int
    #           y2: int   
    #           RGB_classification: string
    #           RGB_confidence: float
    #           HS_classification: {
    #               material1: percentage
    #               material2: percentage
    #           }        
    #           HS_classification: string
    #           HS_confidence: float
    #           distance: double
    #           } ...
    #       ]
    #   }
    # ]...
    # }


# Reset the JSON file script
def resetJSON(filename="New Scan"):
    file_path = "../user-interface/api/data.json"
    blank_data = {
        "location": filename,
        "pins": [],
    }
    try: 
        with open(file_path, "w") as file:
            json.dump(blank_data, file, indent=4)
        print("JSON file updated successfully.")
    except Exception as e:
        print(f"An error occurred whilst resetting JSON: {e}")
    

# Save images to front-end, then update JSON with latest data
def updateJSON(uid, lon, lat, objects,image, activeFile):

    # Specify panorama path
    save_path = './user-interface/public/images/' +  activeFile[:-5] +'/img' + uid + '.jpg'

    # Write image
    cv2.imwrite(save_path, image)

    # try:    
    # Specify JSON path and read data
    file_path = "./user-interface/api/scans/"+activeFile
    with open(file_path, "r") as file:
        data = json.load(file)

    # Construct dictionary with new data
    newPin = {
        "geo_coords": [lon, lat],
        "panorama_ref": "/img" + uid + ".jpg",
        "objects": format_results(objects)
    }

    # Append update
    data["pins"].append(newPin)

    # Write to file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    print("JSON file updated successfully.")


# Populate the JSON file with dummy data
def dummydataJSON():
    file_path = "../user-interface/api/data.json"
    dummy_data = {
        "location": "Glasgow",
        "pins": [{
            "geo_coords": [55.88,-4.32],
            "panorama_ref": "./images/img1.jpg",
            "objects": [{
                "x1": 100,
                "y1": 100,
                "x2": 400,
                "y2": 400,
                "RGB_classification": 'dog',
                "RGB_confidence": 0.8,
                "HS_classification":{"wood":0.4,"stone":0.3,"metal":0.3},
                "HS_confidence":0.7,
                "distance":10}
            ]}]
        }
    try: 
        with open(file_path, "w") as file:
            json.dump(dummy_data, file, indent=4)
        print("JSON file updated successfully.")
    except Exception as e:
        print(f"An error occurred whilst resetting JSON: {e}")

def format_results(objects):
    # TODO: Add HS results and distance
    print(f"object detection arg {objects}")
    results_dict_arr = []
    for obj in objects:
        # print(f"individual res: {res}")
        results_dict_arr.append({"x":obj[1][0],
                            "y":obj[1][1],
                            "w":obj[1][2],
                            "h":obj[1][3],
                            "RGB_classification":obj[0],
                            "RGB_confidence":obj[2],
                            "HS_classification":{"wood":0.4,"stone":0.3,"metal":0.3},
                            "HS_confidence":0.7,
                                "distance":10})

    return results_dict_arr

def setStatusMessage(msg):
    file_path = "./user-interface/api/sensorConfiguration.json"
    with open(file_path, "r") as file:
        data = json.load(file)

    # Construct dictionary with new data
    data["status-message"] = msg

    # Write to file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

def getPlatformStatus():
    file_path = "./user-interface/api/sensorConfiguration.json"
    with open(file_path, "r") as file:
        data = json.load(file)

    status = data["status"]
    activeFile = data["activeFile"]

    return status, activeFile
        
def setPlatformStatus(status):
    
    file_path = "./user-interface/api/sensorConfiguration.json"
    with open(file_path, "r") as file:
        data = json.load(file)

    # Construct dictionary with new data
    data["status"] = status

    # Write to file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

def updateInternetconnection(file_path, status):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)

        # Construct dictionary with new data
        data["wifi-connection"] = status

        # Write to file
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

    except (OSError, PermissionError) as e:
        print(f"Failed to update file: {e}")
    except Exception as e:
        print(f"Failed to update file: {e}")

def updatePiConnection(file_path, status):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)

        # Construct dictionary with new data
        data["pi-connection"] = status

        # Write to file
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

    except (OSError, PermissionError) as e:
        print(f"Failed to update file: {e}")
    except Exception as e:
        print(f"Failed to update file: {e}")

def updateGPSConnection(file_path, status):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)

        # Construct dictionary with new data
        data["gps-connection"] = status

        # Write to file
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

    except (OSError, PermissionError) as e:
        print(f"Failed to update file: {e}")
    except Exception as e:
        print(f"Failed to update file: {e}")


CONFIGURATION_FILE_PATH = "./user-interface/api/sensorConfiguration.json"
if __name__ == "__main__":
    # dummydataJSON()
    updateInternetconnection(CONFIGURATION_FILE_PATH, "Connected")
    updatePiConnection(CONFIGURATION_FILE_PATH, "Disconnected")
