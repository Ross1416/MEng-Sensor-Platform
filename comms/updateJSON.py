import json
import cv2
import numpy as np
import requests
import logging

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
def updateJSON(uid, lat, lon, objects, image, activeFile):
    logging.debug("Updating ui json")
    # Specify panorama path
    save_path = (
        "./user-interface/public/images/" + activeFile[:-5] + "/img" + uid + ".jpg"
    )

    # Write image
    cv2.imwrite(save_path, image)

    # Specify JSON path and read data
    file_path = "./user-interface/api/scans/" + activeFile
    with open(file_path, "r") as file:
        data = json.load(file)

    # Construct dictionary with new data
    newPin = {
        "geo_coords": [lat, lon],
        "panorama_ref": "/img" + uid + ".jpg",
        "objects": format_results(objects, image.shape),
    }

    # Append update
    data["pins"].append(newPin)

    # Write to file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    print("JSON file updated successfully.")

    logging.debug("finished updating ui json")


def updateJSON_HS(
    filtered_objects,
    lat,
    lon,
    activeFile,
    hs_classifcation_ref=None,
    hs_ndvi_ref=None,
    hs_msavi_ref=None,
    hs_custom2_ref=None,
    hs_artificial_ref=None,
    hs_materials_ref=None,
    hs_rgb_ref=None,
):
    logging.debug("Updating ui json with hyperspectral results")
    file_path = "./user-interface/api/scans/" + activeFile
    with open(file_path, "r") as file:
        data = json.load(file)

    # Construct dictionary with new data
    for pin in data["pins"]:
        if pin["geo_coords"] == [lat, lon]:
            if hs_classifcation_ref:
                pin["hsi_ref"] = hs_classifcation_ref
                pin["ndvi_ref"] = hs_ndvi_ref
                pin["msavi_ref"] = hs_msavi_ref
                pin["custom2_ref"] = hs_custom2_ref
                pin["artificial_ref"] = hs_artificial_ref
                pin["rgb_ref"] = hs_rgb_ref
                pin["materials_ref"] = hs_materials_ref
            else:
                for i, json_obj in enumerate(pin["objects"]):
                    for j, detect_obj in enumerate(filtered_objects):
                        if json_obj["id"] == detect_obj.id:
                            json_obj["HS_classification_ref"] = (
                                detect_obj.hs_classification_ref
                            )
                            json_obj["HS_ndvi_ref"] = detect_obj.hs_ndvi_ref
                            json_obj["HS_msavi_ref"] = detect_obj.hs_msavi_ref
                            json_obj["HS_custom2_ref"] = detect_obj.hs_custom2_ref
                            json_obj["HS_artificial_ref"] = detect_obj.hs_artificial_ref
                            json_obj["HS_rgb_ref"] = detect_obj.hs_rgb_ref
                            json_obj["HS_materials"] = detect_obj.hs_materials

    # Write to file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    print("JSON file updated successfully.")

    logging.debug("Finished updating ui json with hyperspectral results")


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
                "HS_materials": obj.hs_materials,
                "HS_classification_ref": "",
                "HS_ndvi_ref": "",
                "HS_msavi_ref": "",
                "HS_custom2_ref": "",
                "HS_artificial_ref": "",
                "HS_rgb_ref": "",
                "distance": obj.distance,
            }
        )

    return results_dict_arr


def setStatusMessage(msg):
    file_path = "./user-interface/api/sensorConfiguration.json"
    error = True
    while error:
        try:
            with open(file_path, "r") as file:
                data = json.load(file)

            # Construct dictionary with new data
            data["status-message"] = msg

            # Write to file
            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)
            error = False
        except:
            print("error opening json")


def getPlatformStatus():
    file_path = "./user-interface/api/sensorConfiguration.json"
    with open(file_path, "r") as file:
        data = json.load(file)

    status = data["status"]
    activeFile = data["activeFile"]
    hsi_manual = data["hsi_manual_scan"]

    return status, activeFile, hsi_manual


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


def getUserRequestedClasses():
    logging.debug("Getting object of interests from ui")
    file_path = "./user-interface/api/sensorConfiguration.json"
    with open(file_path, "r") as file:
        data = json.load(file)

    # Construct dictionary with new data
    data = data["search-objects"]
    classes = {item["object"]: item["hsi"] for item in data}

    # New format {
    # person: True
    # }

    return classes


CONFIGURATION_FILE_PATH = "./user-interface/api/sensorConfiguration.json"
if __name__ == "__main__":
    # dummydataJSON()
    updateInternetconnection(CONFIGURATION_FILE_PATH, "Connected")
    updatePiConnection(CONFIGURATION_FILE_PATH, "Disconnected")
