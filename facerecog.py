import cv2
from flask import Flask, render_template, jsonify, Response, Blueprint
import mysql.connector
from datetime import datetime
from deepface import DeepFace
from sklearn.metrics.pairwise import cosine_similarity
import time

facerecog = Blueprint('facerecog', __name__)

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
        face_encoding = DeepFace.represent(image_bgr, model_name="Facenet512", enforce_detection=False)
        
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
    best_similarity = 0

    for prs_name, prs_occup, stored_face_encoding in known_faces:
        similarity = cosine_similarity([stored_face_encoding], [live_face_encoding])[0][0]
        
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_match_name = prs_name
            best_match_occup = prs_occup
    
    
    if best_similarity > 0.7:  # Adjust the threshold as needed
        return best_match_name, best_match_occup
    else:
        return None, None

def generate_frames():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    last_update = time.time()
    update_interval = 120  # Reload known faces every 60 seconds

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break

            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_locations = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            # Reload known faces if the interval has passed
            if time.time() - last_update > update_interval:
                global known_faces
                known_faces = load_known_faces()
                last_update = time.time()

            for (x, y, w, h) in face_locations:
                face = frame[y:y+h, x:x+w]

                if face.shape[0] < 20 or face.shape[1] < 20:
                    continue

                face_encoding = DeepFace.represent(face, model_name="Facenet512", enforce_detection=False)

                if face_encoding:
                    face_encoding = face_encoding[0]["embedding"]
                    prs_name, prs_occup = compare_faces(known_faces, face_encoding)

                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

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

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    finally:
        cap.release()
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
    mycursor.execute("SELECT prs_name, prs_occup, registered FROM atten_hist ORDER BY registered DESC LIMIT 100")
    data = mycursor.fetchall()
    mycursor.close()
    mydb.close()
    return jsonify(data)




