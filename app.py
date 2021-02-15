import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.errorhandler(404)
def page_not_found(e):
    """
    Displays page not found error
    """
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    """
    Displays internal server error
    """
    return render_template("500.html"), 500


@app.errorhandler(403)
def page_note_found(e):
    """
    Displays forbidden page error
    """
    return render_template("403.html"), 403


@app.route("/")
@app.route("/home")
def home():
    """
    Renders home page template, showing the 2 most recent jobs posted
    """
    jobs = list(mongo.db.jobs.find().sort("_id", -1).limit(2))
    return render_template("index.html", jobs=jobs)


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Register page - allows users to register an account if username not taken
    """
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        # Inserts new users in to DB
        mongo.db.users.insert_one(register)

        # Put new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))
    return render_template("register.html")


@app.route("/sign_in", methods=["GET", "POST"])
def sign_in():
    """
    Sign In page - allows users to sign in if they have an account
    """
    if request.method == "POST":
        # Check if username exists in DB
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # Ensure hashed password matches user input
            if check_password_hash(
             existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(request.form.get("username")))
                return redirect(url_for("profile", username=session["user"]))

            else:
                # Invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("sign_in"))

        else:
            # Username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("sign_in"))
    return render_template("sign_in.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    """
    Profile page - Shows users their profile page and jobs they have posted
    """
    # Get the session user's username from the DB
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    # Shows all jobs posted by the 'user' and sorts them by most recent first
    if session["user"]:
        jobs = list(mongo.db.jobs.find().sort("_id", -1))

        return render_template("profile.html", username=username, jobs=jobs)

    return redirect(url_for("sign_in"))


@app.route("/sign_out")
def sign_out():
    """
    Sign Out page - Allows user to sign out and removes session cookies
    """
    flash("You have been logged out")
    session.clear()
    return redirect(url_for("sign_in"))


@app.route("/get_jobs")
def get_jobs():
    """
    Jobs page - Shows all jobs that have been posted, with most recent first
    """
    jobs = list(mongo.db.jobs.find().sort("_id", -1))
    return render_template("jobs.html", jobs=jobs)


@app.route("/search", methods=["GET", "POST"])
def search():
    """
    Search - Allows users to search for jobs via job_title or job_location
    """
    query = request.form.get("query")
    jobs = list(mongo.db.jobs.find({"$text": {"$search": query}}))
    return render_template("jobs.html", jobs=jobs)


@app.route("/add_job", methods=["GET", "POST"])
def add_job():
    """
    Add Job page - Allows users to post new jobs
    """
    if request.method == "POST":
        job = {
            "job_title": request.form.get("job_title"),
            "company_name": request.form.get("company_name"),
            "role_type": request.form.get("role_type"),
            "job_location": request.form.get("job_location"),
            "job_salary": request.form.get("job_salary"),
            "job_overview": request.form.get("job_overview"),
            "job_description": request.form.get("job_description"),
            "date_posted": datetime.today().strftime('%d-%m-%y'),
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
    """
    Edit Job page - Allows users to edit jobs they have posted
    """
    if request.method == "POST":
        submit = {
            "job_title": request.form.get("job_title"),
            "company_name": request.form.get("company_name"),
            "role_type": request.form.get("role_type"),
            "job_location": request.form.get("job_location"),
            "job_salary": request.form.get("job_salary"),
            "job_overview": request.form.get("job_overview"),
            "job_description": request.form.get("job_description"),
            "date_posted": datetime.today().strftime('%d-%m-%y'),
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
    """
    Delete - Allows users to delete jobs they have posted using job_id
    """
    mongo.db.jobs.remove({"_id": ObjectId(job_id)})
    flash("Job Successfully Deleted")
    return redirect(url_for("get_jobs"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
