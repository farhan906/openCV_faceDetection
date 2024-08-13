import cv2
import numpy as np
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import mysql.connector
from threading import Lock

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="",
        database="flask_db"
    )

app = Flask(__name__)

# Load the face recognizer model
recognizer = cv2.face.LBPHFaceRecognizer_create()
model_path = "C:/Users/FARHAN/Desktop/vscode@/face_recognizer_model.yml"
if os.path.isfile(model_path):
    recognizer.read(model_path)
else:
    raise FileNotFoundError(f"Model file '{model_path}' does not exist.")

# Load the label dictionary
label_dict_path = "C:/Users/FARHAN/Desktop/vscode@/label_dict.npy"
if os.path.isfile(label_dict_path):
    with open(label_dict_path, "rb") as f:
        label_dict = np.load(f, allow_pickle=True).item()
        label_dict_inv = {v: k for k, v in label_dict.items()}
else:
    raise FileNotFoundError(f"Label dictionary file '{label_dict_path}' does not exist.")

def recognize_face(face):
    label, confidence = recognizer.predict(face)
    if confidence < 100:  # Adjust confidence threshold as needed
        return label_dict_inv.get(label)
    return None

@app.route('/')
def home():
    return render_template('facerecg.html')

camera_lock = Lock()

@app.route('/capture_and_recognize', methods=['POST'])
def capture_and_recognize():
    with camera_lock:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return jsonify({'error': 'Could not open video capture device.'})
        
        face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        while True:
            ret, frame = cap.read()
            if not ret:
                return jsonify({'error': 'Failed to capture image.'})

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_classifier.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Draw rectangle around face
                cropped_face = cv2.resize(gray[y:y + h, x:x + w], (200, 200))
                person_name = recognize_face(cropped_face)
                
                if person_name:
                    mydb = get_db_connection()
                    mycursor = mydb.cursor()
                    mycursor.execute("SELECT prs_name, prs_occup FROM img_dataset WHERE prs_name = %s", (person_name,))
                    result = mycursor.fetchone()
                    if result:
                        prs_name, prs_occup = result
                        registered_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        mycursor.execute("INSERT INTO atten_hist (prs_name, prs_occup, registered) VALUES (%s, %s, %s)",
                                        (prs_name, prs_occup, registered_datetime))
                        mydb.commit()
                        mycursor.close()
                        mydb.close()
                        cap.release()
                        cv2.destroyAllWindows()
                        return jsonify({'prs_name': prs_name, 'prs_occup': prs_occup, 'registered_datetime': registered_datetime})
                    mycursor.close()
                    mydb.close()

            cv2.imshow('Camera Feed', frame)  # Display the raw camera feed
            cv2.imshow('Grayscale Image', gray)  # Display the grayscale image

            # Press 'q' to exit the loop and close the camera
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        return jsonify({'error': 'Face not recognized.'})

@app.route('/attendance_history', methods=['GET'])
def attendance_history():
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    mycursor.execute("SELECT prs_name, prs_occup, registered FROM atten_hist")
    data = mycursor.fetchall()
    mycursor.close()
    mydb.close()
    return jsonify(data)

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)
