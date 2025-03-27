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
def updateJSON(uid, lon, lat, objects, image, activeFile):

    # Specify panorama path
    save_path = (
        "./user-interface/public/images/" + activeFile[:-5] + "/img" + uid + ".jpg"
    )

    # Write image
    cv2.imwrite(save_path, image)

    # try:
    # Specify JSON path and read data
    file_path = "./user-interface/api/scans/" + activeFile
    with open(file_path, "r") as file:
        data = json.load(file)

    # Construct dictionary with new data
    newPin = {
        "geo_coords": [lon, lat],
        "panorama_ref": "/img" + uid + ".jpg",
        "objects": format_results(objects, image.shape),
    }

    # Append update
    data["pins"].append(newPin)

    # Write to file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    print("JSON file updated successfully.")


def updateJSON_HS(
    filtered_objects, class_ref, ndvi_ref, materials, lon, lat, activeFile
):
    file_path = "./user-interface/api/scans/" + activeFile
    with open(file_path, "r") as file:
        data = json.load(file)

    # Construct dictionary with new data
    for pin in data["pins"]:
        if pin["geo_coords"] == [lon, lat]:
            for j, obj in enumerate(pin["objects"]):
                for i, detection in enumerate(filtered_objects):
                    if obj["id"] == detection[3]:
                        obj["HS_classification_ref"] = class_ref[i]
                        obj["HS_ndvi_ref"] = ndvi_ref[i]
                        # obj["HS_materials"] = materials[j]

    # Write to file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    print("JSON file updated successfully.")


# Populate the JSON file with dummy data
def dummydataJSON():
    file_path = "../user-interface/api/data.json"
    dummy_data = {
        "location": "Glasgow",
        "pins": [
            {
                "geo_coords": [55.88, -4.32],
                "panorama_ref": "./images/img1.jpg",
                "objects": [
                    {
                        "x1": 100,
                        "y1": 100,
                        "x2": 400,
                        "y2": 400,
                        "RGB_classification": "dog",
                        "RGB_confidence": 0.8,
                        "HS_classification": {"wood": 0.4, "stone": 0.3, "metal": 0.3},
                        "HS_confidence": 0.7,
                        "distance": 10,
                    }
                ],
            }
        ],
    }
    try:
        with open(file_path, "w") as file:
            json.dump(dummy_data, file, indent=4)
        print("JSON file updated successfully.")
    except Exception as e:
        print(f"An error occurred whilst resetting JSON: {e}")


def format_results(objects, image_shape):
    # TODO: Add HS results and distance
    print(f"object detection arg {objects}")
    results_dict_arr = []
    for obj in objects:
        # print(f"individual res: {res}")
        x, y, w, h = obj.get_xywh(
            centre_relative=True, img_width=image_shape[1], img_height=image_shape[0]
        )
        results_dict_arr.append(
            {
                "id": obj.id,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "RGB_classification": obj.label,
                "RGB_confidence": obj.conf,
                "HS_materials": obj.hs_materals,
                "HS_classification_ref": "",
                "HS_ndvi_ref": "",
                "distance": obj.distance,
            }
        )

    return results_dict_arr


def setStatusMessage(msg):
    file_path = "./user-interface/api/sensorConfiguration.json"
    try:
        with open(file_path, "r") as file:
            data = json.load(file)

        # Construct dictionary with new data
        data["status-message"] = msg

        # Write to file
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
    except:
        print("error opening json")


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
