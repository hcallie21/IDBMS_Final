# Updated app.py with student_dashboard route and login redirect fix
from flask import Flask, render_template, redirect, url_for, request, session, flash
from db_operations import (
    insert_section,
    delete_section,
    update_section,
    get_student_name,
    get_teacher_name
)
import oracledb

app = Flask(__name__)
app.secret_key = 'your-secret-key'

def get_connection():
    return oracledb.connect(
        user="SYSTEM",
        password="Dylang134",
        dsn=oracledb.makedsn("localhost", 1521, service_name="XEPDB1")
    )

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        email = request.form.get('email')
        password = request.form.get('password')

        query = f"SELECT name FROM {role} WHERE email = :1 AND password = :2"

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(query, (email, password))
            result = cur.fetchone()
            cur.close()
            conn.close()

            if result:
                session['role'] = role
                session['name'] = result[0]

                # 🔁 Redirect based on role
                if role == "STUDENTS":
                    return redirect(url_for('student_dashboard'))
                else:
                    return redirect(url_for('home'))  # placeholder for other roles
            else:
                flash('Invalid username or password.')
        except Exception as e:
            print(f"Login error: {e}")
            flash("Something went wrong. Try again.")

    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        year = request.form.get('year')

        if len(password) <= 5:
            flash("Password must be longer than 5 characters.")
            return redirect(url_for('register'))

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM STUDENTS WHERE email = :1", (email,))
            if cur.fetchone():
                flash("Email already registered.")
                cur.close()
                conn.close()
                return redirect(url_for('register'))

            cur.execute("INSERT INTO STUDENTS (STUDENT_ID, name, email, password, academic_year) VALUES (student_id_seq.NEXTVAL, :1, :2, :3, :4)",
                        (name, email, password, year))
            conn.commit()
            cur.close()
            conn.close()
            flash("Account created. You may now log in.")
            return redirect(url_for('login'))

        except Exception as e:
            print(f"Registration error: {e}")
            flash("Something went wrong. Try again.")

    return render_template("register.html")

@app.route('/student_dashboard')
def student_dashboard():
    if 'role' in session and session['role'] == 'STUDENTS':
        return render_template("student_dashboard.html", name=session.get('name'))
    else:
        flash("You must be logged in as a student to view this page.")
        return redirect(url_for('login'))

@app.route('/content', methods=['POST'])
def content():
    crn = request.form.get('crn')
    action = request.form.get('action')

    if action == "insert":
        avg_gpa = request.form.get('avg_gpa')
        bld = request.form.get('bld')
        rm = request.form.get('rm')
        days = request.form.get('days')
        time = request.form.get('time')
        tid = request.form.get('tid')

        insert_section(int(crn), float(avg_gpa), bld, int(rm), days, time, int(tid))

    elif action == "delete":
        delete_section(int(crn))

    elif action == "update":
        update_section(int(crn), 999, "12:00")

    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
