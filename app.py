from flask import Flask, render_template, redirect, url_for, request, session
from db_operations import insert_section, delete_section, update_section

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Needed for session usage

# Temporary variable
counter = 0

@app.route('/', methods=['GET', 'POST'])
def index(): 
    if request.method == 'POST':
        # Handles role selection form
        role = request.form.get('role')
        session['role'] = role
        return render_template('index.html', role=role, user_id=None)
    
    # Default landing page (GET request)
    role = session.get('role')
    user_id = session.get('user_id')
    return render_template('index.html', role=role, user_id=user_id)

@app.route('/verify_id', methods=['POST'])
def verify_id():
    # Handle ID form submission
    role = request.form.get('role')
    user_id = request.form.get('user_id')

    # Optional: Validate ID here
    session['role'] = role
    session['user_id'] = user_id

    return render_template('index.html', role=role, user_id=user_id)

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

        print(f"Inserting CRN: {crn}")
        insert_section(int(crn), float(avg_gpa), bld, int(rm), days, time, int(tid))

    elif action == "delete":
        print(f"Deleting CRN: {crn}")
        delete_section(int(crn))

    elif action == "update":
        print(f"Updating CRN: {crn}")
        update_section(int(crn), 999, "12:00")  # Placeholder

    return redirect(url_for('index'))

@app.route('/update', methods=['POST'])
def update(): 
    global counter 
    counter = 0
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
