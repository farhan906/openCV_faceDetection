import cv2
import os
import mysql.connector
from flask import Flask, Response, render_template, request, redirect, url_for, flash

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

# Function to capture and save a single image
def capture_and_save_image(person_name, occupation):
    face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def face_cropped(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray, 1.3, 5)
        if len(faces) == 0:
            return None
        for (x, y, w, h) in faces:
            cropped_face = img[y:y + h, x:x + w]
            return cropped_face
        return None

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "Error: Could not open video capture device."

    ret, img = cap.read()
    cap.release()
    
    if not ret:
        return "Error: Failed to capture image."

    cropped_face = face_cropped(img)
    if cropped_face is not None:
        face = cv2.resize(cropped_face, (200, 200))
        face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)

        # Save the image in a sequential manner
        img_id = 1
        while os.path.exists(f"dataset/{person_name}.{img_id}.jpg"):
            img_id += 1
        file_name_path = f"dataset/{person_name}.{img_id}.jpg"
        cv2.imwrite(file_name_path, face)

        try:
            mydb = get_db_connection()
            mycursor = mydb.cursor()
            mycursor.execute("INSERT INTO img_dataset (prs_name, prs_occup, img_person) VALUES (%s, %s, %s)", 
                             (person_name, occupation, file_name_path))
            mydb.commit()
            mycursor.close()
            mydb.close()
            return f"Image saved successfully as {file_name_path}"
        except Exception as e:
            return f"Error inserting into database: {e}"
    else:
        return "No face detected."

@imgenter.route('/')
def home():
    return render_template('imgent.html')

@imgenter.route('/start_capture', methods=['POST'])
def start_capture():
    person_name = request.form.get('person_name')
    occupation = request.form.get('occupation')
    if not person_name or not occupation:
        flash('Person name and occupation are required!')
        return redirect(url_for('home'))
    result = capture_and_save_image(person_name, occupation)
    flash(result)
    return redirect(url_for('home'))

if __name__ == "__main__":
    imgenter.run(host='127.0.0.1', port=5000, debug=True)
