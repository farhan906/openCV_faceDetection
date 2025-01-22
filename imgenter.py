
import os
import base64
from flask import Flask, render_template, request, redirect, url_for, flash, Blueprint
import mysql.connector

imgenter = Blueprint('imgenter', __name__)


if not os.path.exists('dataset'):
    os.makedirs('dataset')


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="",
        database="flask_db"
    )


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
        return render_template('imgent.html', message="Error: All fields are required.")

    
    file_name_path = save_image(image_base64, person_name)

    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()
        mycursor.execute("INSERT INTO img_dataset (prs_name, prs_occup, img_person) VALUES (%s, %s, %s)", 
                         (person_name, occupation, file_name_path))
        mydb.commit()
        mycursor.close()
        mydb.close()
        return render_template('imgent.html', message=f"Image saved successfully as {file_name_path}")
    except Exception as e:
        return render_template('imgent.html', message=f"Error inserting into database: {e}")
