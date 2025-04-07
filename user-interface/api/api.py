# This file specifies Flask APIs to enable Python back-end and 
# JavaScript front-end to communicate


# Imports
from flask import Flask, send_file, request, jsonify
import json
import requests
import os
import json
import uuid

app = Flask(__name__)

### Retrieve enviroment data from the user-specified file ###
@app.route('/getData', methods=["POST"])
def getData():
    
    # Extract file from request
    data = request.json
    file = data.get("file")  

    # Open and read the JSON file
    with open("scans/" + file, "r") as file:
        data = json.load(file)
    
    # Return data
    return data

### Retrieve the JSON files in the directory (one for each enviroment) ###
@app.route("/getJSONfilenames")
def getJSONfilenames():
    try:
        # Read the files that end with json
        files = os.listdir('./scans')
        json_files = [file for file in files if file.lower().endswith('.json')]
        
        # Extract each file's correspnding location 
        location_names = []
        for f in json_files:
            path = './scans/'+f
            with open(path, "r") as file:
                data = json.load(file)
            location_names.append(data.get("location"))
        
        # Combine data and return
        combined = [{"location": k, "filename": v} for k, v in zip(location_names, json_files)]
        return combined
    except Exception as e:
        print('Error reading directory:', e)

### Get the active file ###
@app.route("/getActiveFile")
def getActiveFile():
    try: 
        filePath = "./sensorConfiguration.json"
        with open(filePath, "r") as file:
            data = json.load(file)
        print('Search Objects:', data['search-objects'])
        return {'activeFile': data['activeFile'], 'searchObjects': data['search-objects']}
    except Exception as e: 
        return -1

### Update the status of the platfor ###
@app.route("/updatePlatformActiveStatus", methods=["POST"])
def updatePlatformActiveStatus():
    # Extract parameter from request
    data = request.json
    status = data.get("status")  
    
    # Read current data
    filePath = "./sensorConfiguration.json"
    with open(filePath, "r") as file:
        data = json.load(file)

    # Update data
    data["status"] = status

    # Write to file
    with open(filePath, "w") as file:
        json.dump(data, file, indent=4)

    return 'Succesful update'

### Create a new enviroment for exploration ###
@app.route("/createNewEnviroment", methods=["POST"])
def createNewEnviroment():
    # Read file title from request
    data = request.json
    locationName = data.get("location")

    # Create a unique identifier
    uid = uuid.uuid4()

    # Create default data
    filePath = "./scans/" + str(uid) + '.json'
    newData = {
        "location": locationName,
        "pins": [],
    }

    # Write data to file
    with open(filePath, "w") as file:
        json.dump(newData, file, indent=4)
        print("JSON file updated successfully.")

    # Create a folder for images
    os.makedirs('../public/images/'+str(uid), exist_ok=True)

    return 'Succesful update'


### Update the active file ###
@app.route("/updateActiveEnviroment", methods=["POST"])
def updateActiveEnviroment():
    # Read filename from API request
    data = request.json
    filename = data.get("file")

    # Specify the save path
    filePath = "./sensorConfiguration.json"
    with open(filePath, "r") as file:
        data = json.load(file)

    # Update current active file, so backend knows where to save
    data["activeFile"] = filename

    # Write to file
    with open(filePath, "w") as file:
        json.dump(data, file, indent=4)

    return 'Succesful update'


### Get the platforms current status, and connection statuses ###
@app.route("/getPlatformStatus", methods=["GET"])
def getPlatformStatus():
    # Specify the save path
    filePath = "./sensorConfiguration.json"
    with open(filePath, "r") as file:
        data = json.load(file)

    return [data['status-message'], data['pi-connection'], data['gps-connection'], data['wifi-connection']]


### Update the objects that the user searches for ###
@app.route("/updateObjects", methods=["POST"])
def updateObjects():
    data = request.json
    objects = data.get("objects")
    hsiManualScan = data.get("hsiManualScan")

    filePath = "./sensorConfiguration.json"
    with open(filePath, "r") as file:
        data = json.load(file)

    # Update current active file, so backend knows where to save
    data["search-objects"] = objects
    data["hsi_manual_scan"] = hsiManualScan

    # Write to file
    with open(filePath, "w") as file:
        json.dump(data, file, indent=4)

    return 'Success'


if __name__ == "__main__":
    app.run(debug=True)

