# Finalized app.py with section-based class search
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

        id_column = f"{role[:-1]}_ID"
        query = f"SELECT {id_column}, name FROM {role} WHERE email = :1 AND password = :2"

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(query, (email, password))
            result = cur.fetchone()
            cur.close()
            conn.close()

            if result:
                session['role'] = role
                session['user_id'] = result[0]
                session['name'] = result[1]

                if role == "STUDENTS":
                    return redirect(url_for('student_dashboard'))
                else:
                    return redirect(url_for('home'))
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

@app.route('/search_classes', methods=['GET'])
def search_classes():
    major = request.args.get('major', '').strip().upper()
    course_num = request.args.get('course_num', '').strip()
    results = []

    print(f"🔍 Received search request - Major: '{major}', Course Num: '{course_num}'")

    if major:
        try:
            conn = get_connection()
            cur = conn.cursor()

            query = """
                SELECT c.MJ_ABV, c.COURSE_NUM, c.COURSE_NAME, c.CREDIT, c.SEM, c.DESCRIPTION,
                       s.CRN, s.AVG_GPA, s.BLD, s.RM, s.DAYS, s.TIME
                FROM Class c
                JOIN Has_Sections hs ON UPPER(c.MJ_ABV) = UPPER(hs.MJ_ABV) AND c.COURSE_NUM = hs.COURSE_NUM
                JOIN Section s ON hs.CRN = s.CRN
                WHERE UPPER(c.MJ_ABV) = :major
            """
            params = {"major": major}

            if course_num.isdigit():
                query += " AND c.COURSE_NUM = :course_num"
                params["course_num"] = int(course_num)

            print("🧪 Executing query:")
            print(query)
            print("📦 With parameters:", params)

            cur.execute(query, params)
            columns = [col[0] for col in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            print(f"✅ Found {len(results)} result(s).")

            cur.close()
            conn.close()
        except Exception as e:
            print(f"❌ Search error: {e}")
            flash("Could not search classes. Try again later.")
    else:
        flash("Please enter a major to search.")

    return render_template("search_classes.html", results=results)


@app.route('/add_to_schedule', methods=['POST'])
def add_to_schedule():
    student_id = session.get('user_id')
    crn = request.form.get('crn')

    print(f"📥 Attempting to add CRN {crn} for student ID {student_id}")

    try:
        conn = get_connection()
        cur = conn.cursor()

        # Check if this CRN is already in the student's schedule
        cur.execute("""
            SELECT 1 FROM Completed_Courses WHERE SID = :sid AND CRN = :crn
        """, {"sid": student_id, "crn": crn})
        exists = cur.fetchone()
        if exists:
            print("⚠️ CRN already exists in Completed_Courses — skipping insert.")
            flash("⚠️ You’ve already added this class section.")
        else:
            cur.execute("""
                INSERT INTO Completed_Courses (SID, CRN)
                VALUES (:sid, :crn)
            """, {"sid": student_id, "crn": crn})
            conn.commit()
            print("✅ Successfully inserted into Completed_Courses.")
            flash("✅ Class section added to schedule!")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Add to schedule error: {e}")
        flash("❌ Failed to add class section. Maybe it's already in your schedule.")

    return redirect(url_for('search_classes'))


@app.route('/view_schedule')
def view_schedule():
    if 'role' not in session or session['role'] != 'STUDENTS':
        flash("Please log in as a student to view your schedule.")
        return redirect(url_for('login'))

    student_id = session.get('user_id')
    schedule = []
    total_credits = 0

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT c.MJ_ABV, c.COURSE_NUM, c.COURSE_NAME, c.CREDIT, c.SEM, c.DESCRIPTION,
                   s.CRN, s.AVG_GPA, s.BLD, s.RM, s.DAYS, s.TIME
            FROM Completed_Courses cc
            JOIN Section s ON cc.CRN = s.CRN
            JOIN Has_Sections hs ON s.CRN = hs.CRN
            JOIN Class c ON hs.MJ_ABV = c.MJ_ABV AND hs.COURSE_NUM = c.COURSE_NUM
            WHERE cc.SID = :sid
        """, {"sid": student_id})

        columns = [col[0] for col in cur.description]
        schedule = [dict(zip(columns, row)) for row in cur.fetchall()]

        total_credits = sum(row['CREDIT'] for row in schedule)

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Schedule error: {e}")
        flash("Could not retrieve schedule.")

    return render_template("view_schedule.html", schedule=schedule, total_credits=total_credits)

@app.route('/drop_class', methods=['POST'])
def drop_class():
    student_id = session.get('user_id')
    crn = request.form.get('crn')

    if not student_id or not crn:
        flash("❌ Could not process drop request.")
        return redirect(url_for('view_schedule'))

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM Completed_Courses
            WHERE SID = :sid AND CRN = :crn
        """, {"sid": student_id, "crn": crn})

        conn.commit()
        cur.close()
        conn.close()

        flash("✅ Class dropped from schedule.")
    except Exception as e:
        print(f"❌ Drop error: {e}")
        flash("❌ Could not drop the class. Try again later.")

    return redirect(url_for('view_schedule'))

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
