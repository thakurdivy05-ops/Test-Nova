from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timezone, timedelta
from sqlalchemy import inspect, text


# ==========================================================
# FLASK APPLICATION
# ==========================================================

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)


# ==========================================================
# USER MODEL
# ==========================================================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False)

    tests = db.relationship(
        "Test",
        backref="teacher",
        lazy=True,
        cascade="all, delete-orphan"
    )

    results = db.relationship(
        "TestResult",
        backref="student",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


# ==========================================================
# TEST MODEL
# ==========================================================

class Test(db.Model):
    __tablename__ = "tests"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    subject = db.Column(db.String(100), nullable=False)

    category = db.Column(db.String(100), nullable=False)

    description = db.Column(db.Text, nullable=True)

    time_limit = db.Column(db.Integer, nullable=False)

    total_marks = db.Column(db.Integer, nullable=False)

    passing_marks = db.Column(db.Integer, nullable=False)

    published = db.Column(db.Boolean, default=False)

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    questions = db.relationship(
        "Question",
        backref="test",
        lazy=True,
        cascade="all, delete-orphan"
    )

    results = db.relationship(
        "TestResult",
        backref="test",
        lazy=True,
        cascade="all, delete-orphan"
    )


# ==========================================================
# QUESTION MODEL
# ==========================================================

class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)

    question_text = db.Column(db.Text, nullable=False)

    marks = db.Column(
        db.Integer,
        default=1,
        nullable=False
    )

    test_id = db.Column(
        db.Integer,
        db.ForeignKey("tests.id"),
        nullable=False
    )

    options = db.relationship(
        "Option",
        backref="question",
        lazy=True,
        cascade="all, delete-orphan"
    )

    answers = db.relationship(
        "Answer",
        backref="question",
        lazy=True,
        cascade="all, delete-orphan"
    )


# ==========================================================
# OPTION MODEL
# ==========================================================

class Option(db.Model):
    __tablename__ = "options"

    id = db.Column(db.Integer, primary_key=True)

    option_text = db.Column(
        db.String(500),
        nullable=False
    )

    option_label = db.Column(
        db.String(1),
        nullable=False
    )

    is_correct = db.Column(
        db.Boolean,
        default=False
    )

    question_id = db.Column(
        db.Integer,
        db.ForeignKey("questions.id"),
        nullable=False
    )

    answers = db.relationship(
        "Answer",
        backref="selected_option",
        lazy=True
    )


# ==========================================================
# TEST RESULT MODEL
# ==========================================================

class TestResult(db.Model):
    __tablename__ = "test_results"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    test_id = db.Column(
        db.Integer,
        db.ForeignKey("tests.id"),
        nullable=False
    )

    total_questions = db.Column(
        db.Integer,
        nullable=False
    )

    attempted = db.Column(
        db.Integer,
        default=0
    )

    correct = db.Column(
        db.Integer,
        default=0
    )

    wrong = db.Column(
        db.Integer,
        default=0
    )

    marks_obtained = db.Column(
        db.Integer,
        default=0
    )

    total_marks = db.Column(
        db.Integer,
        nullable=False
    )

    percentage = db.Column(
        db.Float,
        default=0
    )

    passed = db.Column(
        db.Boolean,
        default=False
    )

    completed_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    answers = db.relationship(
        "Answer",
        backref="result",
        lazy=True,
        cascade="all, delete-orphan"
    )


# ==========================================================
# ANSWER MODEL
# ==========================================================

class Answer(db.Model):
    __tablename__ = "answers"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    result_id = db.Column(
        db.Integer,
        db.ForeignKey("test_results.id"),
        nullable=False
    )

    question_id = db.Column(
        db.Integer,
        db.ForeignKey("questions.id"),
        nullable=False
    )

    selected_option_id = db.Column(
        db.Integer,
        db.ForeignKey("options.id"),
        nullable=True
    )


# ==========================================================
# LOGIN PROTECTION
# ==========================================================

def login_required(view_function):

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login first.",
                "warning"
            )

            return redirect(
                url_for("index")
            )

        return view_function(
            *args,
            **kwargs
        )

    return wrapped_view


def role_required(required_role):

    def decorator(view_function):

        @wraps(view_function)
        def wrapped_view(*args, **kwargs):

            if "user_id" not in session:

                flash(
                    "Please login first.",
                    "warning"
                )

                return redirect(
                    url_for("index")
                )

            if session.get("role") != required_role:

                flash(
                    "You are not authorized to access this page.",
                    "danger"
                )

                return redirect(
                    url_for("index")
                )

            return view_function(
                *args,
                **kwargs
            )

        return wrapped_view

    return decorator


# ==========================================================
# HOME PAGE
# ==========================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ==========================================================
# STUDENT REGISTRATION
# ==========================================================

@app.route(
    "/student/register",
    methods=["GET", "POST"]
)
def student_register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not name or not email or not password:

            flash(
                "All fields are required.",
                "danger"
            )

            return redirect(
                url_for("student_register")
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("student_register")
            )

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "An account with this email already exists.",
                "danger"
            )

            return redirect(
                url_for("student_register")
            )

        student = User(
            name=name,
            email=email,
            role="student"
        )

        student.set_password(password)

        db.session.add(student)
        db.session.commit()

        flash(
            "Student account created successfully. Please login.",
            "success"
        )

        return redirect(
            url_for("student_login")
        )

    return render_template(
        "auth/student_register.html"
    )


# ==========================================================
# STUDENT LOGIN
# ==========================================================

@app.route(
    "/student/login",
    methods=["GET", "POST"]
)
def student_login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            email=email,
            role="student"
        ).first()

        if user and user.check_password(password):

            session.clear()

            session["user_id"] = user.id
            session["user_name"] = user.name
            session["role"] = user.role

            flash(
                "Welcome back, " + user.name + "!",
                "success"
            )

            return redirect(
                url_for("student_dashboard")
            )

        flash(
            "Invalid student email or password.",
            "danger"
        )

    return render_template(
        "auth/student_login.html"
    )


# ==========================================================
# TEACHER REGISTRATION
# ==========================================================

@app.route(
    "/teacher/register",
    methods=["GET", "POST"]
)
def teacher_register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not name or not email or not password:

            flash(
                "All fields are required.",
                "danger"
            )

            return redirect(
                url_for("teacher_register")
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("teacher_register")
            )

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "An account with this email already exists.",
                "danger"
            )

            return redirect(
                url_for("teacher_register")
            )

        teacher = User(
            name=name,
            email=email,
            role="teacher"
        )

        teacher.set_password(password)

        db.session.add(teacher)
        db.session.commit()

        flash(
            "Teacher account created successfully. Please login.",
            "success"
        )

        return redirect(
            url_for("teacher_login")
        )

    return render_template(
        "auth/teacher_register.html"
    )


# ==========================================================
# TEACHER LOGIN
# ==========================================================

@app.route(
    "/teacher/login",
    methods=["GET", "POST"]
)
def teacher_login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            email=email,
            role="teacher"
        ).first()

        if user and user.check_password(password):

            session.clear()

            session["user_id"] = user.id
            session["user_name"] = user.name
            session["role"] = user.role

            flash(
                "Welcome back, " + user.name + "!",
                "success"
            )

            return redirect(
                url_for("teacher_dashboard")
            )

        flash(
            "Invalid teacher email or password.",
            "danger"
        )

    return render_template(
        "auth/teacher_login.html"
    )


# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("index")
    )


# ==========================================================
# STUDENT DASHBOARD
# ==========================================================

@app.route("/student/dashboard")
@role_required("student")
def student_dashboard():

    tests = Test.query.filter_by(
        published=True
    ).order_by(
        Test.id.desc()
    ).all()

    results = TestResult.query.filter_by(
        student_id=session["user_id"]
    ).order_by(
        TestResult.id.desc()
    ).all()

    total_attempted = len(results)

    passed_tests = sum(
        1
        for result in results
        if result.passed
    )

    failed_tests = (
        total_attempted -
        passed_tests
    )

    if total_attempted > 0:

        average_percentage = (
            sum(
                result.percentage
                for result in results
            )
            / total_attempted
        )

    else:

        average_percentage = 0

    return render_template(
        "student/dashboard.html",
        tests=tests,
        results=results,
        total_attempted=total_attempted,
        passed_tests=passed_tests,
        failed_tests=failed_tests,
        average_percentage=average_percentage
    )


# ==========================================================
# STUDENT PROFILE
# ==========================================================

@app.route("/student/profile")
@role_required("student")
def student_profile():

    student = User.query.get_or_404(
        session["user_id"]
    )

    results = TestResult.query.filter_by(
        student_id=student.id
    ).all()

    total_attempted = len(results)

    passed_tests = sum(
        1
        for result in results
        if result.passed
    )

    failed_tests = (
        total_attempted -
        passed_tests
    )

    if total_attempted > 0:

        average_percentage = (
            sum(
                result.percentage
                for result in results
            )
            / total_attempted
        )

    else:

        average_percentage = 0

    return render_template(
    "student/profile.html",
    student=student,
    results=results,
    total_attempted=total_attempted,
    passed_tests=passed_tests,
    failed_tests=failed_tests,
    average_percentage=average_percentage
)
# ==========================================================
# CHANGE PASSWORD - STUDENT & TEACHER
# ==========================================================

@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():

    user = User.query.get_or_404(session["user_id"])

    # Allow only students and teachers
    if user.role not in ["student", "teacher"]:
        flash("You are not authorized to change your password.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":

        current_password = request.form.get(
            "current_password",
            ""
        ).strip()

        new_password = request.form.get(
            "new_password",
            ""
        ).strip()

        confirm_password = request.form.get(
            "confirm_password",
            ""
        ).strip()

        # Check current password
        if not check_password_hash(
            user.password,
            current_password
        ):
            flash(
                "Current password is incorrect.",
                "danger"
            )
            return redirect(
                url_for("change_password")
            )

        # Check new password length
        if len(new_password) < 6:
            flash(
                "New password must contain at least 6 characters.",
                "danger"
            )
            return redirect(
                url_for("change_password")
            )

        # Check password confirmation
        if new_password != confirm_password:
            flash(
                "New password and confirm password do not match.",
                "danger"
            )
            return redirect(
                url_for("change_password")
            )

        # Prevent using the same password
        if check_password_hash(
            user.password,
            new_password
        ):
            flash(
                "New password must be different from your current password.",
                "warning"
            )
            return redirect(
                url_for("change_password")
            )

        # Update password securely
        user.password = generate_password_hash(
            new_password
        )

        db.session.commit()

        flash(
            "Your password has been changed successfully.",
            "success"
        )

        # Return to the correct profile page
        if user.role == "teacher":
            return redirect(
                url_for("teacher_profile")
            )

        return redirect(
            url_for("student_profile")
        )

    return render_template(
        "student/change_password.html"
    )

# ==========================================================
# START STUDENT TEST
# ==========================================================

@app.route(
    "/student/tests/<int:test_id>/start"
)
@role_required("student")
def start_test(test_id):

    test = Test.query.filter_by(
        id=test_id,
        published=True
    ).first_or_404()

    existing_result = TestResult.query.filter_by(
        student_id=session["user_id"],
        test_id=test.id
    ).first()

    if existing_result:

        flash(
            "You have already attempted this test. You cannot attempt it again.",
            "warning"
        )

        return redirect(
            url_for("student_dashboard")
        )

    if len(test.questions) == 0:

        flash(
            "This test does not contain any questions.",
            "warning"
        )

        return redirect(
            url_for("student_dashboard")
        )

    return render_template(
        "student/take_test.html",
        test=test
    )


# ==========================================================
# SUBMIT STUDENT TEST
# ==========================================================

@app.route(
    "/student/tests/<int:test_id>/submit",
    methods=["POST"]
)
@role_required("student")
def submit_test(test_id):

    test = Test.query.filter_by(
        id=test_id,
        published=True
    ).first_or_404()

    existing_result = TestResult.query.filter_by(
        student_id=session["user_id"],
        test_id=test.id
    ).first()

    if existing_result:

        flash(
            "You have already submitted this test. You cannot attempt it again.",
            "warning"
        )

        return redirect(
            url_for(
                "result_page",
                result_id=existing_result.id
            )
        )

    questions = test.questions

    total_questions = len(questions)

    attempted = 0
    correct = 0
    wrong = 0
    marks_obtained = 0

    result = TestResult(
        student_id=session["user_id"],
        test_id=test.id,
        total_questions=total_questions,
        total_marks=test.total_marks,
        completed_at=datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    )

    db.session.add(result)
    db.session.flush()

    for question in questions:

        selected_option_id = request.form.get(
            f"question_{question.id}"
        )

        selected_option = None

        if selected_option_id:

            try:

                selected_option_id = int(
                    selected_option_id
                )

                selected_option = Option.query.filter_by(
                    id=selected_option_id,
                    question_id=question.id
                ).first()

            except (ValueError, TypeError):

                selected_option = None

        if selected_option:

            attempted += 1

            if selected_option.is_correct:

                correct += 1

                marks_obtained += question.marks

            else:

                wrong += 1

        answer = Answer(
            result_id=result.id,
            question_id=question.id,
            selected_option_id=(
                selected_option.id
                if selected_option
                else None
            )
        )

        db.session.add(answer)

    result.attempted = attempted
    result.correct = correct
    result.wrong = wrong
    result.marks_obtained = marks_obtained

    if test.total_marks > 0:

        result.percentage = (
            marks_obtained /
            test.total_marks
        ) * 100

    else:

        result.percentage = 0

    # Passing marks are stored as actual marks.
    result.passed = (
        marks_obtained >= test.passing_marks
    )

    db.session.commit()

    return redirect(
        url_for(
            "result_page",
            result_id=result.id
        )
    )


# ==========================================================
# STUDENT RESULT
# ==========================================================

@app.route(
    "/student/results/<int:result_id>"
)
@role_required("student")
def result_page(result_id):

    result = TestResult.query.filter_by(
        id=result_id,
        student_id=session["user_id"]
    ).first_or_404()

    return render_template(
        "student/result.html",
        result=result
    )


# ==========================================================
# STUDENT LEADERBOARD
# ==========================================================

@app.route("/student/leaderboard")
@role_required("student")
def student_leaderboard():

    students = User.query.filter_by(role="student").all()

    leaderboard = []

    for student in students:
        student_results = TestResult.query.filter_by(
            student_id=student.id
        ).all()

        if not student_results:
            continue

        total_attempts = len(student_results)

        average_percentage = (
            sum(result.percentage for result in student_results)
            / total_attempts
        )

        best_percentage = max(
            result.percentage for result in student_results
        )

        passed_tests = sum(
            1
            for result in student_results
            if result.passed
        )

        leaderboard.append({
            "student": student,
            "total_attempts": total_attempts,
            "average_percentage": average_percentage,
            "best_percentage": best_percentage,
            "passed_tests": passed_tests
        })

    # Sort by average percentage, then best score, then number of tests.
    leaderboard.sort(
        key=lambda item: (
            item["average_percentage"],
            item["best_percentage"],
            item["total_attempts"]
        ),
        reverse=True
    )

    return render_template(
        "student/leaderboard.html",
        leaderboard=leaderboard
    )


# ==========================================================
# TEACHER DASHBOARD
# ==========================================================

@app.route("/teacher/dashboard")
@role_required("teacher")
def teacher_dashboard():

    teacher_id = session["user_id"]

    tests = Test.query.filter_by(
        teacher_id=teacher_id
    ).order_by(
        Test.id.desc()
    ).all()

    total_tests = len(tests)

    published_tests = Test.query.filter_by(
        teacher_id=teacher_id,
        published=True
    ).count()

    total_questions = Question.query.join(
        Test
    ).filter(
        Test.teacher_id == teacher_id
    ).count()

    return render_template(
        "teacher/dashboard.html",
        tests=tests,
        total_tests=total_tests,
        published_tests=published_tests,
        total_questions=total_questions
    )


# ==========================================================
# TEACHER PROFILE
# ==========================================================

@app.route("/teacher/profile")
@role_required("teacher")
def teacher_profile():

    teacher = User.query.get_or_404(
        session["user_id"]
    )

    tests = Test.query.filter_by(
        teacher_id=teacher.id
    ).all()

    total_tests = len(tests)

    published_tests = sum(
        1
        for test in tests
        if test.published
    )

    total_questions = sum(
        len(test.questions)
        for test in tests
    )

    return render_template(
        "teacher/profile.html",
        teacher=teacher,
        total_tests=total_tests,
        published_tests=published_tests,
        total_questions=total_questions
    )


# ==========================================================
# CREATE TEST
# ==========================================================

@app.route(
    "/teacher/tests/create",
    methods=["GET", "POST"]
)
@role_required("teacher")
def create_test():

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        subject = request.form.get(
            "subject",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        try:

            time_limit = int(
                request.form.get(
                    "time_limit",
                    0
                )
            )

            total_marks = int(
                request.form.get(
                    "total_marks",
                    0
                )
            )

            passing_marks = int(
                request.form.get(
                    "passing_marks",
                    0
                )
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Please enter valid numbers.",
                "danger"
            )

            return render_template(
                "teacher/create_test.html"
            )

        if not title or not subject or not category:

            flash(
                "Please fill in all required fields.",
                "danger"
            )

            return render_template(
                "teacher/create_test.html"
            )

        if time_limit <= 0:

            flash(
                "Time limit must be greater than 0.",
                "danger"
            )

            return render_template(
                "teacher/create_test.html"
            )

        if total_marks <= 0:

            flash(
                "Total marks must be greater than 0.",
                "danger"
            )

            return render_template(
                "teacher/create_test.html"
            )

        if passing_marks < 0 or passing_marks > total_marks:

            flash(
                "Passing marks must be between 0 and total marks.",
                "danger"
            )

            return render_template(
                "teacher/create_test.html"
            )

        new_test = Test(
            title=title,
            subject=subject,
            category=category,
            description=description,
            time_limit=time_limit,
            total_marks=total_marks,
            passing_marks=passing_marks,
            published=False,
            teacher_id=session["user_id"]
        )

        db.session.add(new_test)
        db.session.commit()

        flash(
            "Test created successfully! Now add questions.",
            "success"
        )

        return redirect(
            url_for(
                "add_question",
                test_id=new_test.id
            )
        )

    return render_template(
        "teacher/create_test.html"
    )


# ==========================================================
# EDIT TEST DETAILS
# ==========================================================

@app.route(
    "/teacher/tests/<int:test_id>/edit",
    methods=["GET", "POST"]
)
@role_required("teacher")
def edit_test(test_id):

    test = Test.query.filter_by(
        id=test_id,
        teacher_id=session["user_id"]
    ).first_or_404()

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        subject = request.form.get(
            "subject",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        try:

            time_limit = int(
                request.form.get(
                    "time_limit",
                    0
                )
            )

            passing_marks = int(
                request.form.get(
                    "passing_marks",
                    0
                )
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Please enter valid numbers.",
                "danger"
            )

            return render_template(
                "teacher/edit_test.html",
                test=test
            )

        if not title or not subject or not category:

            flash(
                "Title, subject and category are required.",
                "danger"
            )

            return render_template(
                "teacher/edit_test.html",
                test=test
            )

        if time_limit <= 0:

            flash(
                "Time limit must be greater than 0.",
                "danger"
            )

            return render_template(
                "teacher/edit_test.html",
                test=test
            )

        if passing_marks < 0:

            flash(
                "Passing marks cannot be negative.",
                "danger"
            )

            return render_template(
                "teacher/edit_test.html",
                test=test
            )

        # Recalculate total marks from questions.
        calculated_total_marks = sum(
            question.marks
            for question in test.questions
        )

        # If no questions exist, keep the existing total marks.
        if calculated_total_marks > 0:

            test.total_marks = calculated_total_marks

        if passing_marks > test.total_marks:

            flash(
                "Passing marks cannot be greater than total marks.",
                "danger"
            )

            return render_template(
                "teacher/edit_test.html",
                test=test
            )

        test.title = title
        test.subject = subject
        test.category = category
        test.description = description
        test.time_limit = time_limit
        test.passing_marks = passing_marks

        db.session.commit()

        flash(
            "Test updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "teacher_dashboard"
            )
        )

    return render_template(
        "teacher/edit_test.html",
        test=test
    )


# ==========================================================
# ADD QUESTIONS
# ==========================================================

@app.route(
    "/teacher/tests/<int:test_id>/questions/add",
    methods=["GET", "POST"]
)
@role_required("teacher")
def add_question(test_id):

    test = Test.query.filter_by(
        id=test_id,
        teacher_id=session["user_id"]
    ).first_or_404()

    if request.method == "POST":

        question_text = request.form.get(
            "question_text",
            ""
        ).strip()

        option_a = request.form.get(
            "option_a",
            ""
        ).strip()

        option_b = request.form.get(
            "option_b",
            ""
        ).strip()

        option_c = request.form.get(
            "option_c",
            ""
        ).strip()

        option_d = request.form.get(
            "option_d",
            ""
        ).strip()

        correct_option = request.form.get(
            "correct_option"
        )

        try:

            marks = int(
                request.form.get(
                    "marks",
                    1
                )
            )

        except (
            ValueError,
            TypeError
        ):

            marks = 1

        if not question_text:

            flash(
                "Please enter the question.",
                "danger"
            )

            return redirect(
                url_for(
                    "add_question",
                    test_id=test.id
                )
            )

        if (
            not option_a
            or not option_b
            or not option_c
            or not option_d
        ):

            flash(
                "Please enter all four options.",
                "danger"
            )

            return redirect(
                url_for(
                    "add_question",
                    test_id=test.id
                )
            )

        if correct_option not in [
            "A",
            "B",
            "C",
            "D"
        ]:

            flash(
                "Please select the correct answer.",
                "danger"
            )

            return redirect(
                url_for(
                    "add_question",
                    test_id=test.id
                )
            )

        if marks <= 0:

            flash(
                "Marks must be greater than 0.",
                "danger"
            )

            return redirect(
                url_for(
                    "add_question",
                    test_id=test.id
                )
            )

        question = Question(
            question_text=question_text,
            marks=marks,
            test_id=test.id
        )

        db.session.add(question)
        db.session.flush()

        options = [
            ("A", option_a),
            ("B", option_b),
            ("C", option_c),
            ("D", option_d)
        ]

        for label, text in options:

            option = Option(
                option_label=label,
                option_text=text,
                is_correct=(
                    label == correct_option
                ),
                question_id=question.id
            )

            db.session.add(option)

        db.session.commit()

        # Automatically calculate total marks.
        test.total_marks = sum(
            q.marks
            for q in test.questions
        )

        # Make sure passing marks doesn't exceed total marks.
        if test.passing_marks > test.total_marks:

            test.passing_marks = test.total_marks

        db.session.commit()

        flash(
            "Question added successfully!",
            "success"
        )

        return redirect(
            url_for(
                "add_question",
                test_id=test.id
            )
        )

    questions = Question.query.filter_by(
        test_id=test.id
    ).order_by(
        Question.id.asc()
    ).all()

    return render_template(
        "teacher/add_question.html",
        test=test,
        questions=questions
    )


# ==========================================================
# EDIT QUESTION
# ==========================================================

@app.route(
    "/teacher/tests/<int:test_id>/questions/<int:question_id>/edit",
    methods=["GET", "POST"]
)
@role_required("teacher")
def edit_question(
    test_id,
    question_id
):

    test = Test.query.filter_by(
        id=test_id,
        teacher_id=session["user_id"]
    ).first_or_404()

    question = Question.query.filter_by(
        id=question_id,
        test_id=test.id
    ).first_or_404()

    if request.method == "POST":

        question_text = request.form.get(
            "question_text",
            ""
        ).strip()

        option_a = request.form.get(
            "option_a",
            ""
        ).strip()

        option_b = request.form.get(
            "option_b",
            ""
        ).strip()

        option_c = request.form.get(
            "option_c",
            ""
        ).strip()

        option_d = request.form.get(
            "option_d",
            ""
        ).strip()

        correct_option = request.form.get(
            "correct_option"
        )

        try:

            marks = int(
                request.form.get(
                    "marks",
                    1
                )
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Marks must be a valid number.",
                "danger"
            )

            return render_template(
                "teacher/edit_question.html",
                test=test,
                question=question
            )

        if not question_text:

            flash(
                "Question text is required.",
                "danger"
            )

            return render_template(
                "teacher/edit_question.html",
                test=test,
                question=question
            )

        if (
            not option_a
            or not option_b
            or not option_c
            or not option_d
        ):

            flash(
                "All four options are required.",
                "danger"
            )

            return render_template(
                "teacher/edit_question.html",
                test=test,
                question=question
            )

        if correct_option not in [
            "A",
            "B",
            "C",
            "D"
        ]:

            flash(
                "Please select the correct answer.",
                "danger"
            )

            return render_template(
                "teacher/edit_question.html",
                test=test,
                question=question
            )

        if marks <= 0:

            flash(
                "Marks must be greater than 0.",
                "danger"
            )

            return render_template(
                "teacher/edit_question.html",
                test=test,
                question=question
            )

        question.question_text = question_text
        question.marks = marks

        # Existing options
        options_by_label = {
            option.option_label: option
            for option in question.options
        }

        option_values = {
            "A": option_a,
            "B": option_b,
            "C": option_c,
            "D": option_d
        }

        for label, text in option_values.items():

            if label in options_by_label:

                options_by_label[label].option_text = text

                options_by_label[label].is_correct = (
                    label == correct_option
                )

            else:

                new_option = Option(
                    option_label=label,
                    option_text=text,
                    is_correct=(
                        label == correct_option
                    ),
                    question_id=question.id
                )

                db.session.add(new_option)

        # Recalculate total marks.
        test.total_marks = sum(
            q.marks
            for q in test.questions
        )

        if test.passing_marks > test.total_marks:

            test.passing_marks = test.total_marks

        db.session.commit()

        flash(
            "Question updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "add_question",
                test_id=test.id
            )
        )

    return render_template(
        "teacher/edit_question.html",
        test=test,
        question=question
    )


# ==========================================================
# DELETE QUESTION
# ==========================================================

@app.route(
    "/teacher/tests/<int:test_id>/questions/<int:question_id>/delete",
    methods=["POST"]
)
@role_required("teacher")
def delete_question(
    test_id,
    question_id
):

    test = Test.query.filter_by(
        id=test_id,
        teacher_id=session["user_id"]
    ).first_or_404()

    question = Question.query.filter_by(
        id=question_id,
        test_id=test.id
    ).first_or_404()

    db.session.delete(question)
    db.session.flush()

    # Recalculate total marks after deletion.
    remaining_questions = Question.query.filter_by(
        test_id=test.id
    ).all()

    test.total_marks = sum(
        question.marks
        for question in remaining_questions
    )

    if test.total_marks <= 0:

        test.total_marks = 1

    if test.passing_marks > test.total_marks:

        test.passing_marks = test.total_marks

    db.session.commit()

    flash(
        "Question deleted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "add_question",
            test_id=test.id
        )
    )


# ==========================================================
# PUBLISH TEST
# ==========================================================

@app.route(
    "/teacher/tests/<int:test_id>/publish"
)
@role_required("teacher")
def publish_test(test_id):

    test = Test.query.filter_by(
        id=test_id,
        teacher_id=session["user_id"]
    ).first_or_404()

    if len(test.questions) == 0:

        flash(
            "Add at least one question before publishing the test.",
            "warning"
        )

        return redirect(
            url_for(
                "add_question",
                test_id=test.id
            )
        )

    # Recalculate total marks before publishing.
    test.total_marks = sum(
        question.marks
        for question in test.questions
    )

    if test.total_marks <= 0:

        flash(
            "Test must have valid question marks.",
            "danger"
        )

        return redirect(
            url_for(
                "add_question",
                test_id=test.id
            )
        )

    if test.passing_marks > test.total_marks:

        test.passing_marks = test.total_marks

    test.published = True

    db.session.commit()

    flash(
        "Test published successfully!",
        "success"
    )

    return redirect(
        url_for("teacher_dashboard")
    )


# ==========================================================
# DELETE TEST
# ==========================================================

@app.route(
    "/teacher/tests/<int:test_id>/delete",
    methods=["POST"]
)
@role_required("teacher")
def delete_test(test_id):

    test = Test.query.filter_by(
        id=test_id,
        teacher_id=session["user_id"]
    ).first_or_404()

    db.session.delete(test)

    db.session.commit()

    flash(
        "Test deleted successfully.",
        "success"
    )

    return redirect(
        url_for("teacher_dashboard")
    )


# ==========================================================
# TEACHER TEST RESULTS
# ==========================================================

@app.route(
    "/teacher/tests/<int:test_id>/results"
)
@role_required("teacher")
def teacher_test_results(test_id):

    test = Test.query.filter_by(
        id=test_id,
        teacher_id=session["user_id"]
    ).first_or_404()

    results = TestResult.query.filter_by(
        test_id=test.id
    ).order_by(
        TestResult.id.desc()
    ).all()

    # Summary statistics
    total_attempts = len(results)

    passed_count = sum(
        1
        for result in results
        if result.passed
    )

    failed_count = (
        total_attempts -
        passed_count
    )

    if total_attempts > 0:

        average_percentage = (
            sum(
                result.percentage
                for result in results
            )
            / total_attempts
        )

    else:

        average_percentage = 0

    total_marks_obtained = sum(
        result.marks_obtained
        for result in results
    )

    return render_template(
        "teacher/results.html",
        test=test,
        results=results,
        total_attempts=total_attempts,
        passed_count=passed_count,
        failed_count=failed_count,
        average_percentage=average_percentage,
        total_marks_obtained=total_marks_obtained
    )


# ==========================================================
# CREATE DATABASE
# ==========================================================

with app.app_context():

    db.create_all()

    # Add new columns to an existing SQLite database without deleting data.
    inspector = inspect(db.engine)
    test_result_columns = [
        column["name"]
        for column in inspector.get_columns("test_results")
    ]

    if "completed_at" not in test_result_columns:
        db.session.execute(
            text(
                "ALTER TABLE test_results "
                "ADD COLUMN completed_at DATETIME"
            )
        )
        db.session.commit()


# ==========================================================
# RUN APPLICATION
# ==========================================================

if __name__ == "__main__":

    app.run(debug=True)