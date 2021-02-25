from application import app, db
from application.models import User, Recipe
from application.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, \
    ResetPasswordForm, EmptyForm, EditProfileForm, NewRecipeForm
from application.email import send_password_reset_email
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse


@app.route('/')
@app.route('/home')
@login_required
def home():
    recipes = current_user.get_recipes()
    return render_template('home.html', title='Home page', recipes=recipes)


@app.route('/explore')
# @login_required
def explore():
    return render_template('home.html', title='Explore')


@app.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    form = NewRecipeForm()
    if form.validate_on_submit():
        # how to add ingredients to recipe creation?
        recipe = Recipe(title=form.title.data, author=current_user, description=form.description.data,
                        cooking_time=form.cooking_time.data, )
        db.session.add(recipe)
        db.session.commit()
        flash('recipe submitted')
        return redirect(url_for('home'))

    return render_template('add_recipe.html', title='Add recipe', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # retrieve matching User from the database
        user = User.query.filter_by(email=form.email.data).first()

        # if the username doesn't exist, or the password is incorrect
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        # log the user in. This sets the current_user variable
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')

        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(url_for('home'))
    return render_template('login.html', title='Sign in', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    # if user is already logged in, redirect them  back to the index
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        # get current user from entered email
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # verify token is valid and not expired (this function returns the User object)
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        # update password in db
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    form = EmptyForm()
    # first_or404 will return a 404 error if first() returns None
    user = User.query.filter_by(username=username).first_or_404()

    return render_template('user.html', user=user, form=form)

@app.route('/recipe/<id>')
def recipe(id):
    recipe = Recipe.query.filter_by(id=id).first_or_404()
    return render_template('recipe.html', recipe=recipe)



@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    # if form is requested for the first time (GET), fill in form with current data
    if request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    # if form is submitted without errors, copy data from form into database
    elif form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash('Your changes have been saved')
        redirect(url_for('edit_profile'))

    return render_template('edit_profile.html', title='Edit Profile', form=form)


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    # if form filled correctly (only a simple button so should be true in all cases)
    if form.validate_on_submit():
        # get user to be followed
        user = User.query.filter_by(username=username).first()
        # error handling
        if user is None:
            flash('User {} not found'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('home'))

        # follow user
        current_user.follow(user)
        db.session.commit()
        flash('You are now following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('home'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('home'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('home'))
