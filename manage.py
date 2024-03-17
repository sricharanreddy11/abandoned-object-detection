import os
import sys

from flask import Flask, render_template, request, redirect, url_for
import subprocess

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    email = request.form['email']
    # Process the email, you can store it or send it wherever needed
    print("Email submitted:", email)
    return redirect(url_for('index'))


@app.route('/trigger_window')
def trigger_window():
    # Path to your Python script within the Flask app directory
    script_path = os.path.join(os.path.dirname(__file__), 'dev.py')

    # Get the path to the Python interpreter of the virtual environment
    python_interpreter = sys.executable

    # Run the Python script using the virtual environment's Python interpreter
    subprocess.Popen([python_interpreter, script_path])

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
