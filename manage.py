import os
import sys

from flask import Flask, render_template, request, redirect, url_for, session
import subprocess

app = Flask(__name__)
app.secret_key = 'charan@11'


@app.route('/')
def index():
    image_path = url_for('static', filename='abandoned_object.jpg')
    return render_template('index.html', image=image_path)


@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        email = request.form['email']
        trigger_emails = session.get('trigger_emails', [])
        trigger_emails.append(email)
        session['trigger_emails'] = trigger_emails
        print("Email submitted:", email)
    return redirect(url_for('index'))


@app.route('/trigger_window')
def trigger_window():
    trigger_emails = session.get('trigger_emails', [])
    script_path = os.path.join(os.path.dirname(__file__), 'dev.py')
    python_interpreter = sys.executable
    if trigger_emails:
        email_str = ','.join(trigger_emails)
        subprocess.Popen([python_interpreter, script_path, email_str])
        session.pop('trigger_emails')
    else:
        subprocess.Popen([python_interpreter, script_path])
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
