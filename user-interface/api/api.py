# TO START BACKEND: 
# % . venv/bin/activate
# flask run

from flask import Flask, send_file, request, jsonify
import json
import requests
import os


app = Flask(__name__)
import json
# import cv2

@app.route('/getData')
def getData():

    file_path = "data.json"

    # Open and read the JSON file
    with open(file_path, "r") as file:
        data = json.load(file)
    
    return data

@app.route("/updateLocationName", methods=["POST"])
def updateLocationName():

    data = request.json
    location = data.get("location")  # Extract parameter from request

    if not location:
        return jsonify({"error": "No parameter provided"}), 400
    
    file_path = "./data.json"
    with open(file_path, "r") as file:
        data = json.load(file)

    # Update location
    data["location"] = location

    # Write to file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

    return 'Succesful update'

@app.route("/getJSONfilenames")
def getJSONfilenames():
    try:
        files = os.listdir('./scans')
        json_files = [file for file in files if file.lower().endswith('.json')]
        print('JSON files in directory:', json_files)
    except Exception as e:
        print('Error reading directory:', e)
    return json_files


@app.route("/updatePlatformActiveStatus", methods=["POST"])
def updatePlatformActiveStatus():
    data = request.json
    status = data.get("status")  # Extract parameter from request
    
    file_path = "./data.json"
    with open(file_path, "r") as file:
        data = json.load(file)

    # Update location
    data["status"] = status

    # Write to file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

    return 'Succesful update'

if __name__ == "__main__":
    app.run(debug=True)

