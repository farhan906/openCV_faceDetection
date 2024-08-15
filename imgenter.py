import cv2
import os
import base64
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash

# Ensure the dataset directory exists
if not os.path.exists('dataset'):
    os.makedirs('dataset')

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="",
        database="flask_db"
    )

imgenter = Flask(__name__)
imgenter.secret_key = 'supersecretkey'  # For flashing messages

# Function to decode base64 image and save it
def save_image(image_base64, person_name):
    image_data = base64.b64decode(image_base64.split(',')[1])
    img_id = 1
    while os.path.exists(f"dataset/{person_name}.{img_id}.jpg"):
        img_id += 1
    file_name_path = f"dataset/{person_name}.{img_id}.jpg"
    with open(file_name_path, 'wb') as f:
        f.write(image_data)
    return file_name_path

@imgenter.route('/')
def home():
    return render_template('imgent.html')

@imgenter.route('/start_capture', methods=['POST'])
def start_capture():
    person_name = request.form.get('person_name')
    occupation = request.form.get('occupation')
    image_base64 = request.form.get('image')

    if not person_name or not occupation or not image_base64:
        return "Error: All fields are required.", 400

    file_name_path = save_image(image_base64, person_name)

    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()
        mycursor.execute("INSERT INTO img_dataset (prs_name, prs_occup, img_person) VALUES (%s, %s, %s)", 
                         (person_name, occupation, file_name_path))
        mydb.commit()
        mycursor.close()
        mydb.close()
        return f"Image saved successfully as {file_name_path}", 200
    except Exception as e:
        return f"Error inserting into database: {e}", 500


if __name__ == "__main__":
    imgenter.run(host='127.0.0.1', port=5000, debug=True)
