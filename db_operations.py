import oracledb

# Initialize Oracle Instant Client (adjust path if needed)
oracledb.init_oracle_client(lib_dir=r"C:\Users\dylan\Downloads\instantclient-basic-windows.x64-23.7.0.25.01\instantclient_23_7")

# Connection settings
USERNAME = "SYSTEM"
PASSWORD = "Dylang134"
HOST = "localhost"
PORT = 1521
SERVICE = "XEPDB1"

def get_connection():
    return oracledb.connect(
        user=USERNAME,
        password=PASSWORD,
        dsn=oracledb.makedsn(HOST, PORT, service_name=SERVICE)
    )

# Insert a section
def insert_section(crn, avg_gpa, bld, rm, days, time, tid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Section (CRN, AVG_GPA, BLD, RM, DAYS, TIME, TID)
        VALUES (:1, :2, :3, :4, :5, :6, :7)
    """, (crn, avg_gpa, bld, rm, days, time, tid))
    conn.commit()
    cur.close()
    conn.close()

# Delete a section
def delete_section(crn):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Section WHERE CRN = :1", (crn,))
    conn.commit()
    cur.close()
    conn.close()

# Update a section (room and time)
def update_section(crn, new_room, new_time):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE Section
        SET RM = :1, TIME = :2
        WHERE CRN = :3
    """, (new_room, new_time, crn))
    conn.commit()
    cur.close()
    conn.close()

# Get student name by ID
def get_student_name(student_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT Name FROM Students WHERE Student_ID = :1", (student_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None

# Get teacher name by ID
def get_teacher_name(teacher_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT Name FROM Teacher WHERE Teacher_ID = :1", (teacher_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None
