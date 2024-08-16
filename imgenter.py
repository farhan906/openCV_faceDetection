import cv2
import os
import base64
import mysql.connector
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, flash, Blueprint

imgenter = Blueprint('imgenter', __name__)

# Ensure the dataset directory exists
if not os.path.exists('dataset'):
    os.makedirs('dataset')

# Load the pre-trained Caffe model for face detection
prototxt_path = "C:/Users/FARHAN/Desktop/vscode@/architecture.txt"
caffemodel_path = "C:/Users/FARHAN/Desktop/vscode@/weights.caffemodel"
net = cv2.dnn.readNetFromCaffe(prototxt_path, caffemodel_path)

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

# Function to detect faces using the Caffe model
def detect_face(image_path):
    image = cv2.imread(image_path)
    (h, w) = image.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
    
    net.setInput(blob)
    detections = net.forward()

    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
            face = image[startY:endY, startX:endX]
            return face
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
        return "Error: All fields are required.", 400

    file_name_path = save_image(image_base64, person_name)

    # Detect face from the saved image
    face = detect_face(file_name_path)
    if face is not None:
        # Save the cropped face image
        face_path = f"dataset/{person_name}_face.jpg"
        cv2.imwrite(face_path, face)
    else:
        return "No face detected.", 400

    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()
        mycursor.execute("INSERT INTO img_dataset (prs_name, prs_occup, img_person) VALUES (%s, %s, %s)", 
                         (person_name, occupation, face_path))
        mydb.commit()
        mycursor.close()
        mydb.close()
        return f"Image saved successfully as {face_path}", 200
    except Exception as e:
        return f"Error inserting into database: {e}", 500
