import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/home")
def home():
    jobs = list(mongo.db.jobs.find().sort("_id", -1).limit(2))
    return render_template("index.html", jobs=jobs)


# Register Page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Check if username already exists in DB
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # Put new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))
    return render_template("register.html")


# Sign In Page
@app.route("/sign_in", methods=["GET", "POST"])
def sign_in():
    if request.method == "POST":
        # Check if username exists in DB
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # Ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "profile", username=session["user"]))

            else:
                # Invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("sign_in"))

        else:
            # Username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("sign_in"))
    return render_template("sign_in.html")


# Profile Page
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # Get the session user's username from the DB
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    if session["user"]:
        jobs = list(mongo.db.jobs.find().sort("_id", -1))

        return render_template("profile.html", username=username, jobs=jobs)

    return redirect(url_for("sign_in"))


# Sign Out
@app.route("/sign_out")
def sign_out():
    # Remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("sign_in"))


# Jobs Page
@app.route("/get_jobs")
def get_jobs():
    jobs = list(mongo.db.jobs.find().sort("_id", -1))
    return render_template("jobs.html", jobs=jobs)


# Add Job Page
@app.route("/add_job", methods=["GET", "POST"])
def add_job():
    if request.method == "POST":
        job = {
            "job_title": request.form.get("job_title"),
            "company_name": request.form.get("company_name"),
            "role_type": request.form.get("role_type"),
            "job_location": request.form.get("job_location"),
            "job_salary": request.form.get("job_salary"),
            "job_start_date": request.form.get("job_start_date"),
            "job_overview": request.form.get("job_overview"),
            "job_description": request.form.get("job_description"),
            "posted_by": session["user"]
        }
        job_responsibilities = {
            "job_responsibilities": request.form.get(
                "job_responsibilities[]").split('\n')
        }
        job_requirements = {
            "job_requirements": request.form.get(
                "job_requirements[]").split('\n')
        }
        job_benefits = {
            "job_benefits": request.form.get("job_benefits[]").split('\n')
        }
        job.update(job_responsibilities)
        job.update(job_requirements)
        job.update(job_benefits)

        mongo.db.jobs.insert_one(job)
        flash("Job Successfully Posted")
        return redirect(url_for("get_jobs"))

    jobs = list(mongo.db.jobs.find().sort("_id", -1))
    return render_template("add_job.html", jobs=jobs)


@app.route("/edit_job/<job_id>", methods=["GET", "POST"])
def edit_job(job_id):
    if request.method == "POST":
        submit = {
            "job_title": request.form.get("job_title"),
            "company_name": request.form.get("company_name"),
            "role_type": request.form.get("role_type"),
            "job_location": request.form.get("job_location"),
            "job_salary": request.form.get("job_salary"),
            "job_start_date": request.form.get("job_start_date"),
            "job_overview": request.form.get("job_overview"),
            "job_description": request.form.get("job_description"),
            "posted_by": session["user"]
        }
        job_responsibilities = {
            "job_responsibilities": request.form.get(
                "job_responsibilities[]").split('\n')
        }
        job_requirements = {
            "job_requirements": request.form.get(
                "job_requirements[]").split('\n')
        }
        job_benefits = {
            "job_benefits": request.form.get("job_benefits[]").split('\n')
        }
        submit.update(job_responsibilities)
        submit.update(job_requirements)
        submit.update(job_benefits)

        mongo.db.jobs.update({"_id": ObjectId(job_id)}, submit)
        flash("Job Successfully Updated")

    job = mongo.db.jobs.find_one({"_id": ObjectId(job_id)})

    return render_template("edit_job.html", job=job)


@app.route("/delete_job/<job_id>")
def delete_job(job_id):
    mongo.db.jobs.remove({"_id": ObjectId(job_id)})
    flash("Job Successfully Deleted")
    return redirect(url_for("get_jobs"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
