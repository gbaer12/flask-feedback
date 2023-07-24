from flask import Flask, request, render_template, redirect, session, jsonify, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Feedback
from forms import UserForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///feedback_db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = 'secretysecret1234'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
debug = DebugToolbarExtension(app)

connect_db(app)

@app.route('/')
def go_to_register():
    """Sends user to Homepage."""

    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def show_register_form():
    """Shows user registration form."""
    if 'username' in session:
        flash('You are already logged in.', 'danger')
        return redirect(f"/users/{session['username']}")
    
    form = UserForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        
        user = User.register(username, password, email, first_name, last_name)

        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('This username has already been created. Please create a different one.')

            return render_template('register.html', form=form)

        session['username'] = user.username
        flash('Welcome! Account created!', 'success')

        return redirect(f"/users/{user.username}")
    else:
        return render_template('register.html', form=form)
    

    
@app.route('/login', methods=['GET', 'POST'])
def login_user():
    """Login the user."""
    if 'username' in session:
        flash('You are already logged in.', 'danger')
        return redirect(f"/users/{session['username']}")
    
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        # <User> or False
        if user:
            session['username'] = user.username
            flash(f'Welcome Back, {user.username}!', 'info')
            return redirect(f"/users/{user.username}")
        else:
            form.username.errors = ['Invalid username/password.']
            return render_template('login.html', form=form)

    return render_template('login.html', form=form)

@app.route('/logout')
def logout_user():
    session.pop('username')
    flash('Goodbye!', 'info')

    return redirect('/')

@app.route('/secret')
def show_secret_page():
    """Show secret page after successful login."""
    
    if 'username' not in session:
        flash('Please login.', 'danger')
        return redirect('/login')
    else:
        return render_template('secret_page.html')


@app.route('/users/<username>')
def user_page(username):
    """Display user info."""
    if 'username' not in session or username != session['username']:
        flash('Please login.', 'danger')
        return redirect('/login')
    
    user = User.query.get(username)

    return render_template('user_info.html', user=user)

@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    """Delete user from the database permanently."""
    user = User.query.get(username)

    if 'username' not in session or username != session['username']:
        flash('Please login.', 'danger')
        return redirect('/login')

    session.pop('username')

    db.session.delete(user)
    db.session.commit()
    

    flash('User deleted.', 'danger')

    return redirect('/')

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def create_feedback(username):
    """Show feedback form and create feedback."""
    if 'username' not in session or username != session['username']:
        flash('Please login.', 'danger')
        return redirect('/login')
    
    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feedback = Feedback(title=title, content=content, username=username)

        db.session.add(feedback)
        db.session.commit()

        return redirect(f'/users/{feedback.username}')
    
    else:
        return render_template('feedback_form.html', form=form)
    
@app.route('/feedback/<int:feedback_id>/update', methods=['GET', 'POST'])
def update_feedback(feedback_id):
    """Show feedback and updated it."""
    feedback = Feedback.query.get(feedback_id)

    if 'username' not in session or feedback.username != session['username']:
        flash('Please login.', 'danger')
        return redirect('/login')
    
    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db. session.commit()

        return redirect(f"/users/{feedback.username}")
    
    return render_template('/feedback_edit.html', form=form, feedback=feedback)

@app.route('/feedback/<int:feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):
    """Delete a feedback entry."""
    feedback = Feedback.query.get(feedback_id)

    if 'username' not in session or feedback.username != session['username']:
        flash('Please login.', 'danger')
        return redirect('/login')
    
    db.session.delete(feedback)
    db.session.commit()

    return redirect(f"/users/{feedback.username}")