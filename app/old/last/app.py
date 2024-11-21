from flask import Flask, request, make_response, jsonify
import random, time, os, threading, requests, json

app = Flask(__name__)



@app.route('/last')
def last():
    try:
        with open('last.txt', 'r') as f:
            return make_response(jsonify(s=f.read()), 200)
    except FileNotFoundError:
        return make_response('No operations yet\n', 404)



@app.route('/notify', methods =['POST'])
def handle_json():
    if request.method == 'POST':

        data = request.get_json()

        if data:
            try:
                # Define the file path where you want to save the JSON data
                # Write JSON data to file
                with open("last.txt", 'w') as json_file:
                    json.dump(data, json_file, indent=4)  # Format with indent for readability

            except Exception as e:
                return jsonify({"error": str(e)}), 500
        else:
            return jsonify({"error": "No JSON payload received"}), 400



            
if __name__ == '__main__':
    app.run(debug=True)
