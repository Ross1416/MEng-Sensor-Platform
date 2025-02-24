from flask import Flask, send_file, request, jsonify
import json
import requests
import os
import json
import uuid

app = Flask(__name__)

# Retrieve data from then user-selected enviroment
@app.route('/getData', methods=["POST"])
def getData():
    # Extract parameter from request
    data = request.json
    file = data.get("file")  

    # Specify file path
    filePath = "scans/" + file 

    # Open and read the JSON file
    with open(filePath, "r") as file:
        data = json.load(file)
    
    # Return datta
    return data

# Retrieve the JSON files in the directory (one for each enviroment)
@app.route("/getJSONfilenames")
def getJSONfilenames():
    try:
        files = os.listdir('./scans')
        json_files = [file for file in files if file.lower().endswith('.json')]
        location_names = []
        for f in json_files:
            path = './scans/'+f
            with open(path, "r") as file:
                data = json.load(file)
            location_names.append(data.get("location"))
        combined = [{"location": k, "filename": v} for k, v in zip(location_names, json_files)]
    except Exception as e:
        print('Error reading directory:', e)
    return combined

# Change the status of the platform
@app.route("/updatePlatformActiveStatus", methods=["POST"])
def updatePlatformActiveStatus():
    data = request.json
    status = data.get("status")  # Extract parameter from request
    
    filePath = "./sensorConfiguration.json"
    with open(filePath, "r") as file:
        data = json.load(file)

    # Update location
    data["status"] = status

    # Write to file
    with open(filePath, "w") as file:
        json.dump(data, file, indent=4)

    return 'Succesful update'

# Create a new enviroment for exploration
@app.route("/createNewEnviroment", methods=["POST"])
def createNewEnviroment():
    data = request.json
    locationName = data.get("location")

    uid = uuid.uuid4()

    filePath = "scans/" + str(uid) + '.json'
    newData = {
        "location": locationName,
        "pins": [],
    }

    with open(filePath, "w") as file:
        json.dump(newData, file, indent=4)
        print("JSON file updated successfully.")

    os.makedirs('../public/images/'+str(uid), exist_ok=True)

    return 'Succesful update'


# Change the enviroment 
@app.route("/updateActiveEnviroment", methods=["POST"])
def updateActiveEnviroment():
    data = request.json
    filename = data.get("file")

    filePath = "./sensorConfiguration.json"
    with open(filePath, "r") as file:
        data = json.load(file)

    # Update location
    data["activeFile"] = filename

    # Write to file
    with open(filePath, "w") as file:
        json.dump(data, file, indent=4)

    return 'Succesful update'

if __name__ == "__main__":
    app.run(debug=True)

