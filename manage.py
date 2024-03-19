import os
import sys

from flask import Flask, render_template, request, redirect, url_for, session
import subprocess

app = Flask(__name__)
app.secret_key = 'charan@11'


@app.route('/')
def index():
    image_files = []
    current_directory = os.getcwd()
    folder_path = os.path.join(current_directory, "static")
    for filename in os.listdir(folder_path):
        if filename.startswith("abandoned_object") and filename.endswith(".jpg"):
            image_files.append(filename)
    image_files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)), reverse=True)
    display_images = image_files[:3]
    image_path1 = f"/static/{display_images[0]}"
    image_path2 = f"/static/{display_images[1]}"
    image_path3 = f"/static/{display_images[2]}"
    return render_template('index.html', image1=image_path1, image2=image_path2, image3=image_path3)


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
