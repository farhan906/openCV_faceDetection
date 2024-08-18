import cv2
import numpy as np
import os
import face_recognition
from datetime import datetime
from flask import Flask, render_template, jsonify, Response, Blueprint
import mysql.connector

facerecog = Blueprint('facerecog', __name__)

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="",
        database="flask_db"
    )

recognized_persons = set()

def compare_faces(stored_face_path, live_face_encoding):
    stored_image = face_recognition.load_image_file(stored_face_path)
    stored_face_encoding = face_recognition.face_encodings(stored_image)

    if not stored_face_encoding:
        return False
    
    stored_face_encoding = stored_face_encoding[0]
    matches = face_recognition.compare_faces([stored_face_encoding], live_face_encoding)
    return matches[0]

def generate_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for face_encoding, face_location in zip(face_encodings, face_locations):
                top, right, bottom, left = face_location
                cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)

                mydb = get_db_connection()
                mycursor = mydb.cursor()
                mycursor.execute("SELECT prs_name, prs_occup, img_person FROM img_dataset")
                results = mycursor.fetchall()

                for (prs_name, prs_occup, img_person) in results:
                    if prs_name not in recognized_persons and compare_faces(img_person, face_encoding):
                        recognized_persons.add(prs_name)
                        registered_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        mycursor.execute("INSERT INTO atten_hist (prs_name, prs_occup, registered) VALUES (%s, %s, %s)",
                                         (prs_name, prs_occup, registered_datetime))
                        mydb.commit()
                        break  # Stop after the first match

                mycursor.close()
                mydb.close()

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        recognized_persons.clear()


@facerecog.route('/')
def home():
    return render_template('facerecg.html')

@facerecog.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@facerecog.route('/attendance_history', methods=['GET'])
def attendance_history():
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    mycursor.execute("SELECT prs_name, prs_occup, registered FROM atten_hist")
    data = mycursor.fetchall()
    mycursor.close()
    mydb.close()
    return jsonify(data)