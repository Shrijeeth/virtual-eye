import datetime
from flask import Flask, render_template, request, redirect, session, url_for
from flask_caching import Cache
from ibmcloudant.cloudant_v1 import CloudantV1, Document
import hashlib
import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To, Email
import string
import random
import torch
import cv2
import time
import numpy as np
from playsound import playsound
import matplotlib.pyplot as plt


load_dotenv("./.env")
app = Flask(__name__)
app.config["SECRET_KEY"] = "r3qwrqweqq2r324ewf"
app.config["CACHE_TYPE"] = "SimpleCache"
cache = Cache(app)


service = CloudantV1.new_instance()
user_id = int(service.get_database_information(db=os.getenv("USER_DB")).get_result()['doc_count']) + 1
model = torch.hub.load("ultralytics/yolov5", "yolov5m")


def user_exists(email_id):
    query = {"email": email_id}
    result = service.post_find(os.getenv("USER_DB"), selector=query).get_result()['docs']
    return len(result) == 1, result


def hash_text(text, start_salt="123", end_salt="789"):
    original_text = start_salt + text + end_salt
    return hashlib.sha256(original_text.encode()).hexdigest()


def hash_password(email, password):
    return hash_text(
        password,
        hash_text(email, os.getenv("VIRTUAL_EYE_START_SALT"), os.getenv("VIRTUAL_EYE_END_SALT")),
        hash_text(email, os.getenv("VIRTUAL_EYE_START_SALT"), os.getenv("VIRTUAL_EYE_END_SALT"))
    )


def send_registration_mail(email, username):
    from_email = Email(email=os.getenv("SENDGRID_FROM_MAIL"))
    to_emails = [To(email=email, dynamic_template_data={"first_name": username})]
    message = Mail(from_email=from_email, to_emails=to_emails)
    message.template_id = os.getenv("SENDGRID_REGISTER_TEMPLATE_ID")
    try:
        sendgrid_client = SendGridAPIClient(os.getenv("SENDGRID_APIKEY"))
        response = sendgrid_client.send(message)
        return response.status_code == 202
    except Exception as e:
        print(e)
        return False


def send_forgot_password_mail(email, pass_code):
    from_email = Email(email=os.getenv("SENDGRID_FROM_MAIL"))
    to_emails = [To(email=email, dynamic_template_data={"password_code": pass_code})]
    message = Mail(from_email=from_email, to_emails=to_emails)
    message.template_id = os.getenv("SENDGRID_FORGOT_PASSWORD_TEMPLATE_ID")
    try:
        sendgrid_client = SendGridAPIClient(os.getenv("SENDGRID_APIKEY"))
        response = sendgrid_client.send(message)
        return response.status_code == 202
    except Exception as e:
        print(e)
        return False


def generate_passcode():
    code = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=6))
    return str(code)


def detect_person(image):
    detection_results = model(image)
    persons = []
    for detections in detection_results.xyxy[0]:
        if detections[-1] == 0:
            persons.append(detections[:-1])
    return persons


def is_above_threshold(person_bbox, center0, threshold=10):
    center = [(person_bbox[0] + person_bbox[2]) / 2, (person_bbox[1] + person_bbox[3]) / 2]
    hmov = abs(center[0] - center0[0])
    vmov = abs(center[1] - center0[1])
    if (hmov > threshold) or (vmov > threshold):
        return True, center
    return False, center


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = hash_password(email, request.form.get("password"))
        exist, result = user_exists(email)
        if exist:
            if result[0]['password'] == password:
                session['username'] = result[0]['username']
                return redirect(url_for("prediction", username=session['username']))
            return render_template("login.html", alert_message="Wrong Password, Please try again")
        return render_template("login.html", alert_message="Invalid User")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        global user_id
        username = request.form.get("username")
        email = request.form.get("email")
        password = hash_password(email, request.form.get("password"))
        confirm_password = hash_password(email, request.form.get("confirm_password"))
        if password == confirm_password:
            user_data = Document(username=username, email=email, password=password)
            exist, _ = user_exists(email)
            if exist:
                return render_template("login.html", alert_message="User already exists, Please Login")
            response = service.put_document(db=os.getenv("USER_DB"), document=user_data, doc_id=str(user_id))
            if response:
                user_id += 1
                result = send_registration_mail(email, username)
                if not result:
                    result = send_registration_mail(email, username)
                return render_template("login.html", success_message="Registration Success")
            return render_template("register.html", alert_message="Registration Failure, Please try again")
        return render_template("register.html", alert_message="Passwords does not match")
    return render_template("register.html")


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        pass_code = request.form.get("password_code")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        if new_password:
            new_password = hash_password(email, new_password)
        if confirm_password:
            confirm_password = hash_password(email, confirm_password)
        if not pass_code:
            exist, _ = user_exists(email)
            if exist:
                original_code = generate_passcode()
                result = send_forgot_password_mail(email, original_code)
                if not result:
                    result = send_forgot_password_mail(email, original_code)
                cache.set(email, original_code)
                return render_template("forgot_password.html", success_message="Verification Code sent to your email", email=email)
            return render_template("forgot_password.html", alert_message="Invalid User")
        original_code = cache.get(email)
        cache.delete(email)
        if original_code != pass_code:
            return render_template("forgot_password.html", alert_message="Invalid Verification Code")
        if new_password == confirm_password:
            _, user = user_exists(email)
            user_data = Document(id=user[0]["_id"], rev=user[0]["_rev"], username=user[0]["username"], email=user[0]["email"], password=new_password)
            response = service.post_document(db=os.getenv("USER_DB"), document=user_data)
            if response:
                return render_template("login.html", success_message="Password Changed Successfully")
            return render_template("forgot_password.html", alert_message="Password Change Failed, Please try again")
        return render_template("forgot_password.html", alert_message="Passwords does not match")
    return render_template("forgot_password.html")


@app.route("/prediction", methods=["GET", "POST"])
def prediction():
    if request.method == "POST":
        webcam = cv2.VideoCapture("sample_drowning.mp4")
        if not webcam.isOpened():
            print("Could not open webcam")
            return redirect(url_for("login", alert_message="Webcam Not detected! Please Try after sometime"))
        t0 = dict()
        isDrowning = dict()
        center0 = dict()
        center = dict()
        start = time.time()
        while webcam.isOpened():
            limit = time.time() - start
            status, frame = webcam.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (640, 640))
            persons = detect_person(frame)
            for ind,person in enumerate(persons):
                person = list(map(int, person.cpu().numpy().round().tolist()))
                if limit % 60 == 0:
                    t0[ind] = time.time()
                    isDrowning[ind] = False
                    center0[ind] = [0, 0]
                bbox = person.copy()
                x = time.time()
                aboveThresh, center = is_above_threshold(bbox, center0[ind])
                if aboveThresh:
                    t0[ind] = time.time()
                    isDrowning[ind] = False
                else:
                    if time.time() - t0[ind] > 10:
                        isDrowning[ind] = True
                center0[ind] = center
                start_point = (person[0], person[1])
                end_point = (person[2], person[3])
                if isDrowning[ind]:
                    color = (255, 0, 0)
                else:
                    color = (0, 0, 255)
                thickness = 2
                frame = cv2.rectangle(frame, start_point, end_point, color, thickness)
                plt.imshow(frame)
                plt.savefig("./static/prediction/drowning.png")
            for person_id, drown_status in isDrowning.items():
                if drown_status:
                    print(f"Drowning Detected on {datetime.datetime.now()}")
                    playsound("./static/sounds/alarm.mp3.wav")
    if session.get('username'):
        return render_template("prediction.html", username=session['username'])
    return redirect("/login")


@app.route("/logout")
def logout():
    session.pop('username')
    return render_template("logout.html")


if __name__ == '__main__':
    app.run()
