"""
A Flask web application for managing users, grades, and roles in a school system.

This application provides the following features:
1. **User Authentication**: Users can log in with their name, surname, and password. 
   - Roles include Admin (key=1), Teacher (key=2), and Student (key=3).

2. **Admin Dashboard**: Admins can manage users, view grades, and change user roles.

3. **Teacher Dashboard**: Teachers can view and update grades for students within their class.

4. **Student Dashboard**: Students can view their grades and calculate their average grade.

5. **Account Management**: New users can create student accounts,
    admins can change roles and assign classes to teachers.

6. **SQLite Database**: The application uses SQLite as its backend to store user data and grades.
   - The 'users' table stores user information including roles (Admin, Teacher, Student).
   - The 'grades' table stores grades for students, with foreign keys to the users table.

This application includes the following routes:
- **/login**: Login page for authentication.
- **/admin_dashboard**: Dashboard for the admin to view users and their grades.
- **/teacher_dashboard**: Dashboard for the teacher to view and update student grades.
- **/student_dashboard**: Dashboard for the student to view their grades and average.
- **/create_account**: Page for creating a new student account.
- **/admin/change_user_role/<user_id>**: Page to change the role or class of a user (admin only).
- **/teacher/change_grade/<student_id>/<class_name>**: Page to change a student's grade
                                                       (teacher only).
- **/logout**: Logout the current user.

The application initializes the SQLite database when run for the first time,
creating necessary tables and inserting a default admin account.

Requirements:
- Flask
- SQLite3

"""
import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
# Set a secret key for session management
app.secret_key = 'your_secret_key_here'


def initialize_databases():
    """
    Initializes the SQLite database and creates the necessary tables 
    for the school management system. If the database already exists, 
    it will not create a new one. The function also inserts a default 
    admin user into the 'users' table.

    Steps performed:
    1. Checks if the database file (`school.db`) already exists.
    2. Creates a new database if it does not exist.
    3. Creates the 'users' table to store user information
       (id, key, name, surname, password, class).
    4. Creates the 'grades' table to store grade information (key, class, note).
    5. Inserts a default admin account with a hardcoded password ('123').
    6. Commits changes and closes the connection to the database.

    Returns:
        None
    """
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
    """
    Redirects the user to the login page.

    This route is the default landing page of the application. When
    accessed, it immediately redirects the user to the 'login' route.

    Returns:
        Response: A redirect response to the login page.
    """
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles the login process for users.

    This route accepts both GET and POST requests. On a GET request, 
    it renders the login page. On a POST request, it retrieves the 
    user's credentials (name, surname, and password) from the form, 
    validates them against the database, and if they are correct, 
    it sets the user session and redirects them to the appropriate dashboard 
    based on their user role (admin, teacher, or student).

    If the credentials are incorrect, it returns an error message.

    Returns:
        Response: A rendered login page for GET requests or a redirect 
                  to the appropriate dashboard for POST requests if credentials are valid. 
                  Otherwise, returns an error message for invalid credentials.
    """
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
    """
    Allows the admin to change a user's role and class (if applicable).

    This route is protected by an admin check, ensuring only users with
    an admin role (key = 1) can access it. On a GET request, it fetches
    the user's current details and renders a form for changing their role.
    On a POST request, it updates the user's role in the database and, 
    if the role is set to 'Teacher', it also updates the teacher's class.

    Parameters:
        user_id (int): The ID of the user whose role is being changed.

    Returns:
        Response: A redirect to the admin dashboard after a successful update,
                  or renders the 'change_user_role.html' template with the user's
                  current details if it's a GET request.
    """
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
    """
    Displays the admin dashboard with a list of users and their grades.

    This route is protected by an admin check, ensuring only users with
    an admin role (key = 1) can access it. Upon access, the admin dashboard
    displays a list of all users sorted by their roles (Admin, Teacher, Student),
    as well as the grades associated with each user.

    It performs the following:
    1. Ensures the user is an admin by checking the session.
    2. Fetches all users from the 'users' table and sorts them by their role.
    3. Retrieves the grades for each user by joining the 'grades' table with the 'users' table.
    4. Renders the 'admin_dashboard.html' template with the user and grade data.

    Returns:
        Response: Renders the 'admin_dashboard.html' template with sorted user data and grades.
    """
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
    """
    Allows a teacher to change a student's grade in a specific class.

    This route is protected by a teacher check, ensuring only users with
    a teacher role (key = 2) can access it. On a GET request, it displays
    the current grade of the student in the specified class. On a POST request,
    it allows the teacher to update the student's grade in the database, provided
    the teacher is assigned to the same class as the student.

    It performs the following:
    1. Ensures the user is a teacher by checking the session.
    2. Fetches the teacher's assigned class from the 'users' table.
    3. Verifies the teacher is attempting to change the grade for a student in their class.
    4. Retrieves the current grade for the student in the specified class.
    5. Allows the teacher to update the grade on a POST request.
    6. Redirects the teacher to the teacher dashboard after updating the grade.

    Parameters:
        student_id (int): The ID of the student whose grade is being changed.
        class_name (str): The name of the class for which the grade is being changed.

    Returns:
        Response: A rendered form for GET requests displaying the current grade,
                  or a redirect to the teacher dashboard after updating the grade for POST requests.
    """
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
    """
    Displays the teacher's dashboard with a list of students and their grades.

    This route is protected by a teacher check, ensuring only users with
    a teacher role (key = 2) can access it. Upon access, the teacher dashboard
    displays the teacher's name, the class they teach, and a list of students
    enrolled in that class along with their grades.

    It performs the following:
    1. Ensures the user is a teacher by checking the session.
    2. Fetches the teacher's assigned class (subject) from the 'users' table.
    3. Retrieves the teacher's name and surname.
    4. Fetches the list of students enrolled in the teacher's class, along with their grades.
    5. Renders the 'teacher_dashboard.html' template with the teacher's and student data.

    Returns:
        Response: Renders the 'teacher_dashboard.html' template with the teacher's data 
                  and a list of students and their grades.
    """
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
    """
    Displays the student's dashboard with their grades and average score.

    This route is protected by a student check, ensuring only users with
    a student role (key = 3) can access it. Upon access, the student dashboard
    displays the student's grades for each class they are enrolled in, as well as
    their average grade across all classes.

    It performs the following:
    1. Ensures the user is a student by checking the session.
    2. Retrieves the student's grades for all classes they are enrolled in.
    3. Calculates the student's average grade based on the retrieved grades.
    4. Renders the 'student_dashboard.html' template with the student's grades and average score.

    Returns:
        Response: Renders the 'student_dashboard.html' template with the student's grades
                  and their calculated average grade.
    """
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
    """
    Logs out the current user by clearing the session.

    This route clears all session data, effectively logging the user out of the application.
    After logging out, the user is redirected to the login page.

    Returns:
        Response: A redirect to the login page after clearing the session data.
    """
    session.clear()
    return redirect(url_for('login'))


@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    """
    Allows a new student to create an account.

    This route handles both GET and POST requests for creating a new student account. 
    On a GET request, it renders the account creation form. On a POST request, it 
    validates if the student’s name and surname already exist in the system. If they 
    don't, the function creates a new student account with a default role (student), 
    assigns an initial set of grades, and redirects the user to the login page.

    It performs the following:
    1. Validates if a user with the same name and surname already exists.
    2. Creates a new student record in the 'users' table if no existing account is found.
    3. Adds initial grades (with a default score of '0') for the student in various subjects.
    4. Redirects the user to the login page after successfully creating the account.

    Returns:
        Response: Renders the account creation form for GET requests or a redirect to the login page 
                  after successfully creating the account for POST requests.
    """
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