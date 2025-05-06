# Finalized app.py with section-based class search
from flask import Flask, render_template, redirect, url_for, request, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

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
        raw_password = request.form.get('password')

        id_column = {
            "STUDENTS": "STUDENT_ID",
            "TEACHER": "TID",
            "ADVISOR": "AID",
            "IT_STAFF": "IT_ID"
        }.get(role)

        query = f"SELECT {id_column}, name, password FROM {role} WHERE email = :1"

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(query, (email,))
            result = cur.fetchone()
            cur.close()
            conn.close()

            if result and check_password_hash(result[2], raw_password):
                session['role'] = role
                session['user_id'] = result[0]
                session['name'] = result[1]

                if role == "STUDENTS":
                    return redirect(url_for('student_dashboard'))
                elif role == "IT_STAFF":
                    return redirect(url_for('admin_dashboard'))
                elif role == "TEACHER":
                    return redirect(url_for('teacher_dashboard'))
                elif role == "ADVISOR":
                    return redirect(url_for('advisor_dashboard'))
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
        raw_password = request.form.get('password')
        password = generate_password_hash(raw_password)
        year = request.form.get('year')

        if len(raw_password) <= 5:
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

            cur.execute("""
                INSERT INTO STUDENTS (STUDENT_ID, name, email, password, academic_year)
                VALUES (student_id_seq.NEXTVAL, :1, :2, :3, :4)
            """, (name, email, password, year))

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

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'role' in session and session['role'] == 'IT_STAFF':
        try:
            conn = get_connection()
            cur = conn.cursor()

            # Get all classes
            cur.execute("SELECT MJ_ABV, COURSE_NUM, COURSE_NAME FROM Class")
            classes = [
                {"MJ_ABV": row[0], "COURSE_NUM": row[1], "COURSE_NAME": row[2]}
                for row in cur.fetchall()
            ]

            # Get all pending role requests
            cur.execute("SELECT * FROM Pending_Requests")
            colnames = [desc[0] for desc in cur.description]
            requests = [dict(zip(colnames, row)) for row in cur.fetchall()]

            # High-level overview stats
            cur.execute("SELECT COUNT(*) FROM STUDENTS")
            total_students = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM TEACHER")
            total_teachers = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM CLASS")
            total_classes = cur.fetchone()[0]

            cur.execute("SELECT AVG(AVG_GPA) FROM SECTION")
            avg_gpa = cur.fetchone()[0]

            overview = {
                "total_students": total_students,
                "total_teachers": total_teachers,
                "total_classes": total_classes,
                "average_gpa": round(avg_gpa, 2) if avg_gpa else 0
            }

            # All teachers for reports
            cur.execute("SELECT TID, NAME, EMAIL FROM Teacher")
            teachers = [{"TID": row[0], "NAME": row[1], "EMAIL": row[2]} for row in cur.fetchall()]

            # All sections for reports
            cur.execute("SELECT CRN FROM Section")
            sections = [r[0] for r in cur.fetchall()]

            # Optional: Check for selected teacher or section for reporting
            selected_teacher = request.args.get('tid')
            selected_crn = request.args.get('crn')
            teacher_stats = []
            section_stats = []

            if selected_teacher:
                cur.execute("""
                    SELECT 
                        s.CRN,
                        COUNT(cc.SID),
                        ROUND(AVG(s.AVG_GPA), 2)
                    FROM 
                        Section s
                    LEFT JOIN 
                        Completed_Courses cc ON s.CRN = cc.CRN
                    WHERE 
                        s.TID = :tid
                    GROUP BY 
                        s.CRN
    """, {"tid": selected_teacher})
                teacher_stats = cur.fetchall()

            if selected_crn:
                cur.execute("""
                    SELECT stu.NAME, stu.ACADEMIC_YEAR
                    FROM Completed_Courses cc
                    JOIN STUDENTS stu ON cc.SID = stu.STUDENT_ID
                    WHERE cc.CRN = :crn
                """, {"crn": selected_crn})
                section_stats = cur.fetchall()

            cur.close()
            conn.close()

            return render_template(
                "admin_dashboard.html",
                name=session.get('name'),
                classes=classes,
                requests=requests,
                overview=overview,
                teachers=teachers,
                sections=sections,
                selected_teacher=selected_teacher,
                selected_crn=selected_crn,
                teacher_stats=teacher_stats,
                section_stats=section_stats
            )

        except Exception as e:
            print("Dashboard error:", e)
            flash("Error loading admin dashboard.")
            return redirect(url_for('home'))

    flash("You must be logged in as IT Staff.")
    return redirect(url_for('login'))

@app.route('/admin/remove_class', methods=['POST'])
def remove_class():
    if 'role' not in session or session['role'] != 'IT_STAFF':
        return "Access denied", 403

    class_id = request.form.get('class_id')
    if not class_id or ':' not in class_id:
        flash("Invalid class selected.")
        return redirect(url_for('admin_dashboard'))

    major, course_num = class_id.split(':')

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM Class WHERE MJ_ABV = :major AND COURSE_NUM = :course_num
        """, {"major": major, "course_num": course_num})
        conn.commit()
        cur.close()
        conn.close()
        flash("✅ Class removed.")
    except Exception as e:
        print("Remove class error:", e)
        flash("❌ Failed to remove class.")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/approve_request', methods=['POST'])
def approve_request():
    if session.get('role') != 'IT_STAFF':
        return "Access Denied", 403

    request_id = request.form.get('request_id')

    try:
        conn = get_connection()
        cur = conn.cursor()

        # Get the request
        cur.execute("SELECT * FROM Pending_Requests WHERE request_id = :id", {"id": request_id})
        req = cur.fetchone()
        if not req:
            flash("Request not found.")
            return redirect(url_for('admin_dashboard'))

        name, email, password, role, dept = req[1], req[2], req[3], req[4], req[5]

        if role == "TEACHER":
            cur.execute("""
                INSERT INTO Teacher (TID, NAME, EMAIL, PASSWORD)
                VALUES (teacher_id_seq.NEXTVAL, :name, :email, :password)
            """, {"name": name, "email": email, "password": password})

        elif role == "ADVISOR":
            cur.execute("""
                INSERT INTO Advisor (AID, NAME, EMAIL, DEPT, PASSWORD)
                VALUES (advisor_id_seq.NEXTVAL, :name, :email, :dept, :password)
            """, {"name": name, "email": email, "dept": dept, "password": password})

        elif role == "IT_STAFF":
            cur.execute("""
                INSERT INTO IT_Staff (IT_ID, NAME, EMAIL, T_ACC, US_ACC_M, SYST_CONFIG, PASSWORD)
                VALUES (it_id_seq.NEXTVAL, :name, :email, 'Y', 'Y', 'Y', :password)
            """, {"name": name, "email": email, "password": password})

        # Remove from requests
        cur.execute("DELETE FROM Pending_Requests WHERE request_id = :id", {"id": request_id})

        conn.commit()
        cur.close()
        conn.close()

        flash(f"✅ Approved and added {name} as {role}.")
    except Exception as e:
        print("Approval error:", e)
        flash("❌ Failed to approve request.")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/decline_request', methods=['POST'])
def decline_request():
    if session.get('role') != 'IT_STAFF':
        return "Access Denied", 403

    request_id = request.form.get('request_id')

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Pending_Requests WHERE request_id = :id", {"id": request_id})
        conn.commit()
        cur.close()
        conn.close()
        flash("❌ Request declined.")
    except Exception as e:
        print("Decline error:", e)
        flash("❌ Failed to decline request.")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_class', methods=['POST'])
def add_class():
    if 'role' not in session or session['role'] != 'IT_STAFF':
        return "Access denied", 403

    try:
        class_data = {
            "major": request.form.get('major').strip().upper(),
            "course_num": request.form.get('course_num').zfill(2),
            "semester": int(request.form.get('semester')),
            "credit": int(request.form.get('credit')),
            "name": request.form.get('name').strip(),
            "description": request.form.get('description').strip()
        }

        print("📦 Inserting class:", class_data)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Class (MJ_ABV, COURSE_NUM, SEM, CREDIT, COURSE_NAME, DESCRIPTION)
            VALUES (:major, :course_num, :semester, :credit, :name, :description)
        """, class_data)
        conn.commit()
        cur.close()
        conn.close()
        flash("✅ Class added successfully!")
    except Exception as e:
        print("❌ Add class error:", e)
        flash("❌ Failed to add class. Check your inputs.")

    return redirect(url_for('admin_dashboard'))

@app.route('/request_role', methods=['GET', 'POST'])
def request_role():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        raw_password = request.form.get('password')
        password = generate_password_hash(raw_password)
        role = request.form.get('role')
        dept = request.form.get('dept') if role == 'ADVISOR' else None

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO Pending_Requests (name, email, password, requested_role, dept)
                VALUES (:name, :email, :password, :role, :dept)
            """, {
                "name": name,
                "email": email,
                "password": password,
                "role": role,
                "dept": dept
            })
            conn.commit()
            cur.close()
            conn.close()
            flash("✅ Request submitted. Please check with IT Staff to have your request approved.")
            return redirect(url_for('login'))
        except Exception as e:
            print("❌ Role request error:", e)
            flash("❌ Something went wrong. Try again.")

    return render_template("request_role.html")


@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'role' not in session or session['role'] != 'TEACHER':
        flash("Access denied.")
        return redirect(url_for('login'))

    tid = session.get('user_id')
    sections = []
    section_count = 0

    try:
        conn = get_connection()
        cur = conn.cursor()

        # Get sections this teacher teaches
        cur.execute("""
            SELECT s.CRN, s.BLD, s.RM, s.DAYS, s.TIME, s.AVG_GPA,
                   c.MJ_ABV, c.COURSE_NUM, c.COURSE_NAME
            FROM Section s
            JOIN Has_Sections hs ON s.CRN = hs.CRN
            JOIN Class c ON hs.MJ_ABV = c.MJ_ABV AND hs.COURSE_NUM = c.COURSE_NUM
            WHERE s.TID = :tid
        """, {"tid": tid})

        results = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

        for row in results:
            section = dict(zip(columns, row))

            # Get students enrolled in this section
            cur.execute("""
                SELECT stu.NAME, stu.ACADEMIC_YEAR
                FROM Completed_Courses cc
                JOIN STUDENTS stu ON cc.SID = stu.STUDENT_ID
                WHERE cc.CRN = :crn
            """, {"crn": section["CRN"]})
            section["students"] = [
                {"NAME": r[0], "ACADEMIC_YEAR": r[1]} for r in cur.fetchall()
            ]

            sections.append(section)

        section_count = len(sections)

        cur.close()
        conn.close()
    except Exception as e:
        print("Teacher dashboard error:", e)
        flash("❌ Failed to load your dashboard.")

    return render_template("teacher_dashboard.html", name=session.get('name'), sections=sections, section_count=section_count)
@app.route('/teacher/add_section', methods=['POST'])
def add_section():
    if session.get('role') != 'TEACHER':
        return "Access Denied", 403

    try:
        crn = int(request.form.get('crn'))
        major = request.form.get('major').upper().strip()
        course_num = request.form.get('course_num').zfill(2)
        days = request.form.get('days')
        time = request.form.get('time')
        bld = request.form.get('bld')
        rm = int(request.form.get('rm'))
        avg_gpa = float(request.form.get('avg_gpa'))
        tid = session.get('user_id')

        conn = get_connection()
        cur = conn.cursor()

        # Insert into Section
        cur.execute("""
            INSERT INTO Section (CRN, AVG_GPA, BLD, RM, DAYS, TIME, TID)
            VALUES (:crn, :avg_gpa, :bld, :rm, :days, :time, :tid)
        """, {
            "crn": crn, "avg_gpa": avg_gpa, "bld": bld,
            "rm": rm, "days": days, "time": time, "tid": tid
        })

        # Link to Class
        cur.execute("""
            INSERT INTO Has_Sections (MJ_ABV, COURSE_NUM, CRN)
            VALUES (:major, :course_num, :crn)
        """, {"major": major, "course_num": course_num, "crn": crn})

        conn.commit()
        cur.close()
        conn.close()
        flash("✅ Section added successfully.")
    except Exception as e:
        print("Add section error:", e)
        flash("❌ Failed to add section.")

    return redirect(url_for('teacher_dashboard'))
@app.route('/teacher/remove_section', methods=['POST'])
def remove_section():
    if session.get('role') != 'TEACHER':
        return "Access Denied", 403

    crn = request.form.get('crn')

    try:
        conn = get_connection()
        cur = conn.cursor()

        # Delete from Has_Sections and Section
        cur.execute("DELETE FROM Has_Sections WHERE CRN = :crn", {"crn": crn})
        cur.execute("DELETE FROM Section WHERE CRN = :crn", {"crn": crn})

        conn.commit()
        cur.close()
        conn.close()
        flash("✅ Section removed.")
    except Exception as e:
        print("Remove section error:", e)
        flash("❌ Failed to remove section.")

    return redirect(url_for('teacher_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Signed out successfully.")
    return redirect(url_for('home'))

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session or 'role' not in session:
        flash("You must be logged in to change your password.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        current_pw = request.form.get('current_password')
        new_pw = request.form.get('new_password')
        user_id = session['user_id']
        role = session['role']

        id_column = {
            "STUDENTS": "STUDENT_ID",
            "TEACHER": "TID",
            "ADVISORS": "AID",
            "IT_STAFF": "IT_ID"
        }.get(role)

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(f"SELECT PASSWORD FROM {role} WHERE {id_column} = :id", {"id": user_id})
            result = cur.fetchone()

            if result and check_password_hash(result[0], current_pw):
                hashed_new_pw = generate_password_hash(new_pw)
                cur.execute(f"UPDATE {role} SET PASSWORD = :new_pw WHERE {id_column} = :id", {
                    "new_pw": hashed_new_pw,
                    "id": user_id
                })
                conn.commit()
                flash("✅ Password updated successfully. Please log in again.")
                session.clear()
                return redirect(url_for('login'))
            else:
                flash("❌ Incorrect current password.")
            cur.close()
            conn.close()
        except Exception as e:
            print("Password change error:", e)
            flash("❌ Failed to change password. Please try again.")

    return render_template("change_password.html")

@app.route('/advisor_dashboard')
def advisor_dashboard():
    if 'role' not in session or session['role'] != 'ADVISOR':
        flash("Access denied.")
        return redirect(url_for('login'))

    aid = session.get('user_id')
    selected_sid = request.args.get('sid')
    advisees = []
    student_schedule = []

    try:
        conn = get_connection()
        cur = conn.cursor()

        # 🔍 Get all students advised by this advisor
        cur.execute("""
            SELECT s.STUDENT_ID, s.NAME
            FROM STUDENTS s
            JOIN ADVISES a ON s.STUDENT_ID = a.SID
            WHERE a.AID = :aid
        """, {"aid": aid})
        advisees = cur.fetchall()

        if selected_sid:
            cur.execute("""
                SELECT c.MJ_ABV, c.COURSE_NUM, c.COURSE_NAME, c.CREDIT,
                       s.CRN, s.BLD, s.RM, s.DAYS, s.TIME
                FROM Completed_Courses cc
                JOIN Section s ON cc.CRN = s.CRN
                JOIN Has_Sections hs ON s.CRN = hs.CRN
                JOIN Class c ON hs.MJ_ABV = c.MJ_ABV AND hs.COURSE_NUM = c.COURSE_NUM
                WHERE cc.SID = :sid
            """, {"sid": selected_sid})
            student_schedule = cur.fetchall()

        cur.close()
        conn.close()
    except Exception as e:
        print("Advisor dashboard error:", e)
        flash("Could not load advisor dashboard.")

    return render_template(
        "advisor_dashboard.html",
        name=session.get('name'),
        advisees=advisees,
        selected_sid=selected_sid,
        student_schedule=student_schedule
    )



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
