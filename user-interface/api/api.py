from flask import Flask, send_file, request, jsonify
import json
import requests
import os
import json

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

# Update the enviroment with a new name
@app.route("/updateLocationName", methods=["POST"])
def updateLocationName():

    # Extract paramaters
    data = request.json
    location = data.get("location") 
    file = data.get("file")  

    if not location or not file:
        return jsonify({"error": "No parameter provided"}), 400
    
    filePath = "scans/" + file 
    with open(filePath, "r") as file:
        data = json.load(file)

    # Update location
    data["location"] = location

    # Write to file
    with open(filePath, "w") as file:
        json.dump(data, file, indent=4)

    return 'Succesful update'

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


@app.route("/updatePlatformActiveStatus", methods=["POST"])
def updatePlatformActiveStatus():
    data = request.json
    status = data.get("status")  # Extract parameter from request
    file = data.get("file")
    
    filePath = "scans/"+file
    with open(filePath, "r") as file:
        data = json.load(file)

    # Update location
    data["status"] = status

    # Write to file
    with open(filePath, "w") as file:
        json.dump(data, file, indent=4)

    return 'Succesful update'


@app.route("/createNewEnviroment", methods=["POST"])
def createNewEnviroment():
    data = request.json
    file = data.get("file")
    locationName = data.get("location")

    filePath = "scans/" + file
    newData = {
        "location": locationName,
        "pins": [],
        "state": 1, # 0 for deactive, 1 for active, 2 for test
    }

    with open(filePath, "w") as file:
        json.dump(newData, file, indent=4)
        print("JSON file updated successfully.")

    return 'Succesful update'

if __name__ == "__main__":
    app.run(debug=True)

