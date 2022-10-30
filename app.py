from flask import Flask, render_template, request
from ibmcloudant.cloudant_v1 import CloudantV1, Document
import hashlib
import os
from dotenv import load_dotenv


load_dotenv("./.env")
app = Flask(__name__)


service = CloudantV1.new_instance()
user_id = int(service.get_database_information(db=os.getenv("USER_DB")).get_result()['doc_count']) + 1


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
                return render_template("login.html", alert_message="Login Success") # Should link to predict page
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
                return render_template("login.html", success_message="Registration Success")
            render_template("register.html", alert_message="Registration Failure, Please try again")
        return render_template("register.html", alert_message="Passwords does not match")
    return render_template("register.html")


if __name__ == '__main__':
    app.run()
