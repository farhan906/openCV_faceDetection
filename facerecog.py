import cv2
import numpy as np
import os
from flask import Flask, render_template, jsonify, Response, Blueprint
import mysql.connector
from datetime import datetime
from deepface import DeepFace
from sklearn.metrics.pairwise import cosine_similarity
import face_recognition

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

def load_known_faces():
    known_faces = []
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    mycursor.execute("SELECT prs_name, prs_occup, img_person FROM img_dataset")
    results = mycursor.fetchall()
    
    for prs_name, prs_occup, img_person in results:
        image_bgr = cv2.imread(img_person)
        face_encoding = DeepFace.represent(image_bgr, model_name="Facenet", enforce_detection=False)
        
        if face_encoding:
            face_encoding = face_encoding[0]["embedding"]
            known_faces.append((prs_name, prs_occup, face_encoding))
        else:
            print(f"No face detected for image: {img_person}")
    
    mycursor.close()
    mydb.close()
    return known_faces


known_faces = load_known_faces()

def compare_faces(known_faces, live_face_encoding):
    best_match_name = None
    best_match_occup = None
    best_similarity = 0  # Initialize the best similarity as 0

    for prs_name, prs_occup, stored_face_encoding in known_faces:
        similarity = cosine_similarity([stored_face_encoding], [live_face_encoding])[0][0]
        
        # Keep track of the best match found
        if similarity > best_similarity:
            best_similarity = similarity
            best_match_name = prs_name
            best_match_occup = prs_occup
    
    # Only return the best match if it exceeds a threshold
    if best_similarity > 0.65:  # Adjust the threshold as needed
        return best_match_name, best_match_occup
    else:
        return None, None


def generate_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    # Lower the resolution to speed up processing
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            faces = [frame[top:bottom, left:right] for top, right, bottom, left in face_locations]

            for face, face_location in zip(faces, face_locations):
                # Skip small faces to increase speed
                if face.shape[0] < 20 or face.shape[1] < 20:
                    continue

                face_encoding = DeepFace.represent(face, model_name="Facenet", enforce_detection=False)
                
                if face_encoding:
                    face_encoding = face_encoding[0]["embedding"]
                    prs_name, prs_occup = compare_faces(known_faces, face_encoding)

                    top, right, bottom, left = face_location
                    cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)

                    if prs_name and prs_name not in recognized_persons:
                        recognized_persons.add(prs_name)
                        registered_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        mydb = get_db_connection()
                        mycursor = mydb.cursor()
                        mycursor.execute("INSERT INTO atten_hist (prs_name, prs_occup, registered) VALUES (%s, %s, %s)",
                                         (prs_name, prs_occup, registered_datetime))
                        mydb.commit()
                        mycursor.close()
                        mydb.close()

            # Encode the frame as a JPEG and yield it
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
    # Limit the number of records to improve performance (you can adjust the limit as needed)
    mycursor.execute("SELECT prs_name, prs_occup, registered FROM atten_hist ORDER BY registered DESC LIMIT 100")
    data = mycursor.fetchall()
    mycursor.close()
    mydb.close()
    return jsonify(data)
