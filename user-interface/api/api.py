# TO START BACKEND: 
# % . venv/bin/activate
# flask run

from flask import Flask, send_file, request, jsonify
import json
import requests


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
    data = request.get_json()
    print(data)
    location = data.get("location")  # Extract parameter from request
    print(location)
    if not location:
        return jsonify({"error": "No parameter provided"}), 400
    
    file_path = "./api/data.json"
    with open(file_path, "r") as file:
        data = json.load(file)

    # Append update
    data["location"] = location

    # Write to file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

    print("JSON file updated successfully.")
    

    

# @app.route('/api/photo')
# def getPhoto():
#     # Path to your image
#     photoPath = "testImage.jpg"
#     return send_file(photoPath, mimetype='image/jpeg')

if __name__ == "__main__":
    app.run(debug=True)

