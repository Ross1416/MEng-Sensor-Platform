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
    #       imgRef: './img
    #       objects: [
    #           {
    #           pixel_coords: [x y]
    #           RGB_classifcation: string
    #           HS_classification: string
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
        "pins": []
    }
    try: 
        with open(file_path, "w") as file:
            json.dump(blank_data, file, indent=4)
        print("JSON file updated successfully.")
    except Exception as e:
        print(f"An error occurred whilst resetting JSON: {e}")
    

# Save images to front-end, then update JSON with latest data
def updateJSON(uid, lon, lat, objects,image):
    # try:
    # Specify panorama path
    save_path = './user-interface/public/images/img' + uid + '.jpg'
    # Write image
    cv2.imwrite(save_path, image)
    # pass
    # except Exception as e:
    #         print(f"An error occurred whilst saving images: {e}")

    # try:    
    # Specify JSON path and read data
    file_path = "./user-interface/api/data.json"
    with open(file_path, "r") as file:
        data = json.load(file)

    # Construct dictionary with new data
    newPin = {
        "geo_coords": [lon, lat],
        "panorama_ref": "./images/img" + uid + ".jpg",
        "objects": format_results(objects)
    }

    # Append update
    data["pins"].append(newPin)

    # Write to file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    print("JSON file updated successfully.")

    # except Exception as e:
    #         print(f"An error occurred whilst updating JSON: {e}")


# Populate the JSON file with dummy data
def dummydataJSON():
    file_path = "../user-interface/api/data.json"
    dummy_data = {
        "location": "Glasgow",
        "pins": [{
            "geo_coords": [55.88,-4.32],
            "panorama_ref": "./images/img1.jpg",
            "objects": [{
                "pixel_coords": ["300px","150px", "200px", "200px"], # top, left, width, height
                "RGB_classification": "Building",
                "HS_classification": {
                    "wood": '20',
                    "plastic": '70',
                    "stone": '10'
                }
            }]
        }]
    }
    try: 
        with open(file_path, "w") as file:
            json.dump(dummy_data, file, indent=4)
        print("JSON file updated successfully.")
    except Exception as e:
        print(f"An error occurred whilst resetting JSON: {e}")

def format_results(object_detection):
    # TODO: Add HS results and distance
    print(f"object detection arg {object_detection}")
    results_dict_arr = []
    for i in range(len(object_detection)):
        for res in object_detection:
            print(f"individual res: {res}")
            results_dict_arr.append({"x":res[i][1][0],
                                "y":res[i][1][1],
                                "w":res[i][1][2],
                                "h":res[i][1][3],
                                "RGB_classification":res[i][0],
                                "RGB_confidence":res[i][2],
                                "HS_classification":{"wood":0.4,"stone":0.3,"metal":0.3},
                                "HS_confidence":0.7,
                                "distance":10})
        
    return results_dict_arr

if __name__ == "__main__":
    dummydataJSON()
