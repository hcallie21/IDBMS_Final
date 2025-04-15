##PURPOSE: just doing front end stuff to get insert, update,
#  delete functionality for P5

#Imports 
from flask import Flask, render_template, redirect, url_for, request
#from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

#counter var - will get replaced w/ database logic 
counter = 0

@app.route('/')
def index(): 

    return render_template('index.html', counter = counter)


@app.route('/content', methods=['POST'])
def content(): 
    global counter
    crn = request.form.get('crn')
    action = request.form.get('action') #ins or delete

    if not crn: 
        return "CRN required", 400
    
    if action =="insert": 
        print(f"Inserting CRN: {crn}")
        #TODO insert logic here
    elif action == "delete": 
        print(f"Deleting CRN: {crn}")
        #TODO del logic here
    elif action =="update": 
        print(f"updating")
    return redirect(url_for('index'))


@app.route('/update', methods = ['POST'])
def update(): 
    global counter 
    counter = 0
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug = True, host='0.0.0.0', port =8080)
