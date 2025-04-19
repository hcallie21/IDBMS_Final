import oracledb

# ✅ Initialize Oracle Instant Client path
oracledb.init_oracle_client(lib_dir=r"C:\Users\dylan\Downloads\instantclient-basic-windows.x64-23.7.0.25.01\instantclient_23_7")

# ✅ Your Oracle DB connection info
USERNAME = "SYSTEM"
PASSWORD = "Dylang134"
HOST = "localhost"
PORT = 1521
SERVICE = "XEPDB1"

def get_connection():
    return oracledb.connect(
        user=USERNAME,
        password=PASSWORD,
        dsn="10.0.0.99:1521/xepdb1"
    )

# ✅ Test the DB connection
def test_connection():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 'Connection Successful' FROM dual")
        result = cur.fetchone()
        print(f"✅ {result[0]}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

# ✅ Insert a student
def insert_student(student_id, name, year):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Students (Student_ID, Name, academic_year)
            VALUES (:1, :2, :3)
        """, (student_id, name, year))
        conn.commit()
        print(f"✅ Inserted student {name}")
    except Exception as e:
        print(f"❌ Insert error: {e}")
    finally:
        cur.close()
        conn.close()

# ✅ Delete a student
def delete_student(student_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM Students WHERE Student_ID = :1
        """, (student_id,))
        conn.commit()
        print(f"🗑️ Deleted student with ID {student_id}")
    except Exception as e:
        print(f"❌ Delete error: {e}")
    finally:
        cur.close()
        conn.close()

# ✅ Update a student
def update_student(student_id, new_name, new_year):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE Students
            SET Name = :1, academic_year = :2
            WHERE Student_ID = :3
        """, (new_name, new_year, student_id))
        conn.commit()
        print(f"✏️ Updated student {student_id}")
    except Exception as e:
        print(f"❌ Update error: {e}")
    finally:
        cur.close()
        conn.close()
# ✅ Insert a section
def insert_section(crn, avg_gpa, bld, rm, days, time, tid):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Section (CRN, AVG_GPA, BLD, RM, DAYS, TIME, TID)
            VALUES (:1, :2, :3, :4, :5, :6, :7)
        """, (crn, avg_gpa, bld, rm, days, time, tid))
        conn.commit()
        print(f"✅ Inserted section {crn}")
    except Exception as e:
        print(f"❌ Insert error: {e}")
    finally:
        cur.close()
        conn.close()

# ✅ Delete a section
def delete_section(crn):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Section WHERE CRN = :1", (crn,))
        conn.commit()
        print(f"🗑️ Deleted section {crn}")
    except Exception as e:
        print(f"❌ Delete error: {e}")
    finally:
        cur.close()
        conn.close()

# ✅ Update a section (example: just updating RM & TIME)
def update_section(crn, new_room, new_time):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE Section
            SET RM = :1, TIME = :2
            WHERE CRN = :3
        """, (new_room, new_time, crn))
        conn.commit()
        print(f"✏️ Updated section {crn}")
    except Exception as e:
        print(f"❌ Update error: {e}")
    finally:
        cur.close()
        conn.close()

def test_insert_section():
    try:
        conn = get_connection()
        cur = conn.cursor()

        crn = 999
        avg_gpa = 3.2
        bld = 'TEST'
        rm = 999
        days = 'MWF'
        time = '11:00'
        tid = 123

        print("🚀 Inserting test section with values:")
        print(f"   CRN: {crn}, GPA: {avg_gpa}, BLD: {bld}, RM: {rm}, DAYS: {days}, TIME: {time}, TID: {tid}")

        try:
            cur.execute("""
                INSERT INTO Section (CRN, AVG_GPA, BLD, RM, DAYS, TIME, TID)
                VALUES (:1, :2, :3, :4, :5, :6, :7)
            """, (crn, avg_gpa, bld, rm, days, time, tid))
        except Exception as inner:
            print("🛑 Error during cur.execute():")
            print(inner)
            raise  # Re-raise so outer finally still runs

        conn.commit()
        print("✅ Successfully inserted and committed section 999")

        cur.execute("SELECT * FROM Section WHERE CRN = :1", (crn,))
        row = cur.fetchone()
        print("🔍 Row in DB:", row)

    except Exception as e:
        print("❌ Insert failed with error:")
        print(e)

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

# 🔁 Test here
if __name__ == "__main__":
    test_connection()
    test_insert_section()
