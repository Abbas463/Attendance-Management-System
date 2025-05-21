import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import webbrowser
import threading
from time import sleep

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flashing messages

# Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',  # Change if needed
        password='',  # Change if needed
        database='ILA_CLASS_B'
    )

# Create Database and Tables
def create_db():
    connection = mysql.connector.connect(host='localhost', user='root', password='')
    cursor = connection.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS ILA_CLASS_B")
    cursor.close()
    connection.close()

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS students (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100),
        father_name VARCHAR(100)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT,
        date DATE,
        status VARCHAR(10),
        FOREIGN KEY (student_id) REFERENCES students(id)
    )""")

    connection.commit()
    cursor.close()
    connection.close()

# Home Page
@app.route('/')
def home():
    return render_template('base.html')

# Add Student Page
@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        father_name = request.form['father_name']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO students (name, father_name) VALUES (%s, %s)", (name, father_name))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Student added successfully!', 'success')
        return redirect(url_for('add_student'))
    return render_template('add_student.html')

# Take Attendance Page
@app.route('/take_attendance', methods=['GET', 'POST'])
def take_attendance():
    connection = get_db_connection()
    cursor = connection.cursor()

    # Get selected date (default: today)
    selected_date = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))

    # Get list of all students
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    # Handle POST request (attendance submission)
    if request.method == 'POST':
        date = request.form['date']
        student_ids = request.form.getlist('students')  # List of student IDs marked present

        # Delete previous attendance records for the selected date
        cursor.execute("DELETE FROM attendance WHERE date = %s", (date,))
        connection.commit()

        # Insert new attendance data for the selected date
        all_student_ids = [student[0] for student in students]  # Get all student IDs

        for student_id in all_student_ids:
            # Check if the student is present
            if str(student_id) in student_ids:
                cursor.execute("INSERT INTO attendance (student_id, date, status) VALUES (%s, %s, %s)",
                               (student_id, date, 'Present'))
            else:
                cursor.execute("INSERT INTO attendance (student_id, date, status) VALUES (%s, %s, %s)",
                               (student_id, date, 'Absent'))

        connection.commit()
        flash('Attendance submitted successfully!', 'success')

        # Redirect to the same page with the updated date as a query parameter
        return redirect(url_for('take_attendance', date=date))

    # Get attendance records for the selected date (including both Present and Absent)
    cursor.execute("SELECT student_id, status FROM attendance WHERE date = %s", (selected_date,))
    attendance_records = {row[0]: row[1] for row in cursor.fetchall()}  # Store attendance in a dictionary

    cursor.close()
    connection.close()

    # Pass the selected date as a query parameter when navigating to a different date
    return render_template('take_attendance.html', students=students, attendance_records=attendance_records, selected_date=selected_date)

# View Attendance Page
@app.route('/view_attendance')
def view_attendance():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT students.name, 
               COUNT(CASE WHEN attendance.status = 'Present' THEN 1 END) AS present, 
               COUNT(CASE WHEN attendance.status = 'Absent' THEN 1 END) AS absent 
        FROM students 
        LEFT JOIN attendance ON students.id = attendance.student_id 
        GROUP BY students.id
    """)
    students_attendance = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('view_attendance.html', students_attendance=students_attendance)

# Function to open the browser automatically
def open_browser():
    sleep(2)  # Wait for Flask to start
    webbrowser.open("http://127.0.0.1:5000")  # Open the Flask app in the default web browser

if __name__ == '__main__':
    create_db()

    # Start the Flask app in a new thread
    threading.Thread(target=app.run, kwargs={'debug': True, 'use_reloader': False}).start()

    # Open the browser in a new thread
    threading.Thread(target=open_browser).start()
