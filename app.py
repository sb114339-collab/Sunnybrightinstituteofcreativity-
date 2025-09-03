from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change this for production

# =====================
# Database helper
# =====================
def get_db():
    conn = sqlite3.connect("school.db")
    conn.row_factory = sqlite3.Row
    return conn

# =====================
# Admin credentials
# =====================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# =====================
# Home page
# =====================
@app.route("/")
def home():
    return render_template("landing.html")

# =====================
# Student Admission Form
# =====================
@app.route("/admissions", methods=["GET", "POST"])
def admissions():
    conn = get_db()
    courses = conn.execute("SELECT * FROM courses").fetchall()

    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        course_id = request.form["course_id"]
        password = request.form["password"]

        conn.execute(
            "INSERT INTO students (fullname, email, phone, course_id, password, status) VALUES (?,?,?,?,?,?)",
            (fullname, email, phone, course_id, password, "Pending"),
        )
        conn.commit()
        flash("Application submitted successfully!", "success")
        return redirect(url_for("student_login"))

    return render_template("admissions_form.html", courses=courses)

# =====================
# Student Login
# =====================
@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        student = conn.execute(
            "SELECT s.id, s.fullname, s.email, s.phone, s.password, c.title as course "
            "FROM students s JOIN courses c ON s.course_id = c.id WHERE email=?",
            (email,),
        ).fetchone()

        if student and student["password"] == password:
            session["student_id"] = student["id"]
            flash("Login successful!", "success")
            return redirect(url_for("student_dashboard"))
        else:
            flash("Invalid email or password", "error")

    return render_template("student_login.html")

# =====================
# Student Dashboard
# =====================
@app.route("/student/dashboard")
def student_dashboard():
    if not session.get("student_id"):
        flash("Please login first", "error")
        return redirect(url_for("student_login"))

    conn = get_db()
    student = conn.execute(
        "SELECT s.fullname, s.email, s.phone, c.title as course "
        "FROM students s JOIN courses c ON s.course_id = c.id WHERE s.id=?",
        (session["student_id"],),
    ).fetchone()

    return render_template("student_dashboard.html", student=student)

# =====================
# Admin Login
# =====================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            flash("Welcome, Admin!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid login details", "error")

    return render_template("admin_login.html")

# =====================
# Admin Dashboard
# =====================
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        flash("You must log in as admin first", "error")
        return redirect(url_for("admin_login"))

    conn = get_db()
    applicants = conn.execute(
        "SELECT s.id, s.fullname, s.email, c.title as course_title, s.status "
        "FROM students s JOIN courses c ON s.course_id = c.id"
    ).fetchall()

    courses = conn.execute("SELECT * FROM courses").fetchall()

    phone = "08120108997"
    support = "Support Team"

    return render_template("admin_applicants.html", applicants=applicants, courses=courses, phone=phone, support=support)

# =====================
# Admin Add Course
# =====================
@app.route("/admin/add_course", methods=["POST"])
def admin_add_course():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    title = request.form["title"]
    description = request.form["description"]

    conn = get_db()
    conn.execute("INSERT INTO courses (title, description) VALUES (?,?)", (title, description))
    conn.commit()

    flash("Course added!", "success")
    return redirect(url_for("admin_dashboard"))

# =====================
# Admin Delete Course
# =====================
@app.route("/admin/delete_course/<int:course_id>", methods=["POST"])
def admin_delete_course(course_id):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    conn = get_db()
    conn.execute("DELETE FROM courses WHERE id=?", (course_id,))
    conn.commit()

    flash("Course deleted!", "info")
    return redirect(url_for("admin_dashboard"))

# =====================
# Approve / Reject / Delete Applicants
# =====================
@app.route("/admin/approve/<int:student_id>")
def admin_approve(student_id):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    conn = get_db()
    conn.execute("UPDATE students SET status='Approved' WHERE id=?", (student_id,))
    conn.commit()
    flash("Applicant approved!", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/reject/<int:student_id>")
def admin_reject(student_id):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    conn = get_db()
    conn.execute("UPDATE students SET status='Rejected' WHERE id=?", (student_id,))
    conn.commit()
    flash("Applicant rejected!", "warning")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete/<int:student_id>", methods=["POST"])
def admin_delete(student_id):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    conn = get_db()
    conn.execute("DELETE FROM students WHERE id=?", (student_id,))
    conn.commit()
    flash("Applicant deleted!", "danger")
    return redirect(url_for("admin_dashboard"))

# =====================
# Logout
# =====================
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for("home"))

# =====================
# Run app
# =====================
if __name__ == "__main__":
    # Create tables if not exist
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, description TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, fullname TEXT, email TEXT, phone TEXT, course_id INTEGER, password TEXT, status TEXT)")
    conn.commit()
    conn.close()

    app.run(debug=True)
        