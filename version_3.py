import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session


app = Flask(__name__)
# Set a secret key for session management
app.secret_key = 'your_secret_key_here'


def initialize_databases():
    db_name = "school.db"

    # Check if the database file already exists
    if os.path.exists(db_name):
        print("Database already exists.")
        return

    # Connect to the SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create the 'users' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key INTEGER NOT NULL,
            name TEXT NOT NULL,
            surname TEXT NOT NULL,
            password TEXT NOT NULL,
            class TEXT
        )
    ''')

    # Create the 'grades' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            key INTEGER NOT NULL,
            class TEXT NOT NULL,
            note TEXT DEFAULT '0',
            FOREIGN KEY (key) REFERENCES users (id)
        )
    ''')

    # Insert the default admin account
    cursor.execute('''
        INSERT INTO users (key, name, surname, password, class)
        VALUES (1, 'admin', 'admin', '123', NULL)
    ''')
    print("Admin account created.")

    # Commit changes and close the connection
    conn.commit()
    conn.close()


@app.route('/')
def home(): 
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        password = request.form['password']

        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM users WHERE name = ? AND surname = ? AND password = ?
        ''', (name, surname, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]
            session['user_key'] = user[1]
            session['user_name'] = user[2]
            session['user_surname'] = user[3]

            if user[1] == 1:
                return redirect(url_for('admin_dashboard'))
            elif user[1] == 2:
                return redirect(url_for('teacher_dashboard'))
            elif user[1] == 3:
                return redirect(url_for('student_dashboard'))
        else:
            return "Invalid credentials. Please try again."

    return render_template('login.html')


@app.route('/admin/change_user_role/<int:user_id>', methods=['GET', 'POST'])
def change_user_role(user_id):
    if 'user_id' not in session or session['user_key'] != 1:
        return redirect(url_for('login'))

    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        new_role = request.form['role']
        new_class = request.form.get('class')  # Get class if it's a teacher
        cursor.execute(
            '''UPDATE users SET key = ? WHERE id = ?''', (new_role, user_id))

        if new_role == '2':  # If role set to 'Teacher', update class
            cursor.execute(
                '''UPDATE users SET class = ? WHERE id = ?''',
                (new_class, user_id))

        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))

    cursor.execute('''SELECT * FROM users WHERE id = ?''', (user_id,))
    user = cursor.fetchone()

    conn.close()

    return render_template('change_user_role.html', user=user)


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['user_key'] != 1:
        return redirect(url_for('login'))

    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    # Sort users by their role: Admin (1), Teacher (2), Student (3)
    users.sort(key=lambda user: user[1])

    # Fetch grades for all users
    cursor.execute('''
        SELECT users.name, users.surname, grades.class, grades.note
        FROM grades
        INNER JOIN users ON grades.key = users.id
    ''')
    grades = cursor.fetchall()

    conn.close()
    return render_template('admin_dashboard.html', users=users, grades=grades)


@app.route('/teacher/change_grade/<int:student_id>/<class_name>', methods=['GET', 'POST'])
def change_grade(student_id, class_name):
    
    if 'user_id' not in session or session['user_key'] != 2:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()

    # Fetch the teacher's class (subject)
    cursor.execute('''SELECT class FROM users WHERE id = ?''', (user_id,))
    teacher_class = cursor.fetchone()[0]

    # Check if the teacher's class matches the class being edited
    if teacher_class != class_name:
        return "You can only change grades for students in your class."

    # Fetch the grade record for the student and class
    cursor.execute('''
        SELECT grades.note FROM grades
        INNER JOIN users ON grades.key = users.id
        WHERE grades.key = ? AND grades.class = ?
    ''', (student_id, class_name))
    grade = cursor.fetchone()

    if request.method == 'POST':
        new_grade = request.form['grade']
        cursor.execute('''UPDATE grades SET note = ? WHERE key = ? AND class = ?''',
                       (new_grade, student_id, class_name))
        conn.commit()
        conn.close()
        return redirect(url_for('teacher_dashboard'))

    conn.close()
    return render_template('change_grade.html', student_id=student_id,
                           class_name=class_name, grade=grade)


@app.route('/teacher_dashboard')
def teacher_dashboard():
    
    if 'user_id' not in session or session['user_key'] != 2:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()

    # Fetch the class (subject) of the logged-in teacher
    cursor.execute('''SELECT class FROM users WHERE id = ?''', (user_id,))
    class_name = cursor.fetchone()[0]

    # Fetch the teacher's name and surname
    cursor.execute(
        '''SELECT name, surname FROM users WHERE id = ?''', (user_id,))
    teacher_name, teacher_surname = cursor.fetchone()

    # Fetch students who are enrolled in the teacher's class (subject)
    cursor.execute('''
        SELECT users.id, users.name, users.surname, grades.note
        FROM grades
        INNER JOIN users ON grades.key = users.id
        WHERE grades.class = ? AND users.key = 3
    ''', (class_name,))
    students = cursor.fetchall()

    conn.close()

    # Pass teacher's name and students data to the template
    return render_template('teacher_dashboard.html', teacher_name=teacher_name,
                           teacher_surname=teacher_surname,
                           class_name=class_name, students=students)


@app.route('/student_dashboard')
def student_dashboard():
    
    if 'user_id' not in session or session['user_key'] != 3:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT class, note FROM grades WHERE key = ?''', (user_id,))
    grades = cursor.fetchall()

    # Calculate average grade
    if grades:
        total = sum([float(grade[1]) for grade in grades])
        average = total / len(grades)
    else:
        average = None

    conn.close()
    return render_template('student_dashboard.html', grades=grades,
                           average=average)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        password = request.form['password']

        conn = sqlite3.connect('school.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM users WHERE name = ? AND surname = ?
        ''', (name, surname))
        user = cursor.fetchone()

        if user:
            return "An account with this name and surname already exists."
        else:
            cursor.execute('''
                INSERT INTO users (key, name, surname, password, class)
                VALUES (3, ?, ?, ?, NULL)
            ''', (name, surname, password))
            user_id = cursor.lastrowid

            # Add initial grades for the new student
            classes = ["History", "Math", "English", "Philosophy"]
            for subject in classes:
                cursor.execute('''
                    INSERT INTO grades (key, class, note)
                    VALUES (?, ?, '0')
                ''', (user_id, subject))

            conn.commit()
            conn.close()
            return redirect(url_for('login'))

    return render_template('create_account.html')


if __name__ == "__main__":
    initialize_databases()
    app.run(debug=False)
