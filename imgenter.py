import cv2
import os
import base64
import numpy as np
import face_recognition
from flask import Flask, render_template, request, redirect, url_for, flash, Blueprint
import mysql.connector

imgenter = Blueprint('imgenter', __name__)

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

# Function to detect faces using face_recognition
def detect_face(image_path, person_name):
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    
    if face_locations:
        # Crop the first detected face
        top, right, bottom, left = face_locations[0]
        face = image[top:bottom, left:right]
        # Convert the face to BGR format for saving with OpenCV
        face_bgr = cv2.cvtColor(face, cv2.COLOR_RGB2BGR)
        
        # Save the cropped face image using the consistent naming convention
        img_id = 1
        while os.path.exists(f"dataset/{person_name}_face.{img_id}.jpg"):
            img_id += 1
        face_path = f"dataset/{person_name}_face.{img_id}.jpg"
        cv2.imwrite(face_path, face_bgr)
        return face_path
    return None

@imgenter.route('/')
def home():
    return render_template('imgent.html')

@imgenter.route('/start_capture', methods=['POST'])
def start_capture():
    person_name = request.form.get('person_name')
    occupation = request.form.get('occupation')
    image_base64 = request.form.get('image')

    if not person_name or not occupation or not image_base64:
        return render_template('imgent.html', message="Error: All fields are required.")

    file_name_path = save_image(image_base64, person_name)

    # Detect face from the saved image and save with consistent naming
    face_path = detect_face(file_name_path, person_name)
    if face_path is not None:
        try:
            mydb = get_db_connection()
            mycursor = mydb.cursor()
            mycursor.execute("INSERT INTO img_dataset (prs_name, prs_occup, img_person) VALUES (%s, %s, %s)", 
                             (person_name, occupation, face_path))
            mydb.commit()
            mycursor.close()
            mydb.close()
            return render_template('imgent.html', message=f"Image saved successfully as {face_path}")
        except Exception as e:
            return render_template('imgent.html', message=f"Error inserting into database: {e}")
    else:
        return render_template('imgent.html', message="No face detected.")
