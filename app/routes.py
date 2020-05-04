from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, RecipeForm, EditRecipeForm
from app.models import User, Recipe

@app.route('/')
@app.route('/index')
@login_required
def index():
    recipes = Recipe.query.all()
    return render_template('index.html', title='Home', recipes=recipes)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(f'Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Congratulations, you are now a registered user.')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    recipes = [
        {'name': 'Pasta Bolognese', 'description': 'A great dish'},
        {'name': 'Dumplings', 'description': 'A little work but stunning in the mouth'},
    ]
    return render_template('user.html', user=user, recipes=recipes)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@app.route('/recipe/<recipe_name>')
@login_required
def recipe(recipe_name):
    recipe = Recipe.query.filter_by(name=recipe_name).first()
    return render_template('recipe.html', title=recipe.name, recipe=recipe)

@app.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        recipe = Recipe(
            name=form.recipe.data,
            description=form.description.data,
            author=current_user,
            servings=form.servings.data,
            comments=form.comments.data,
            source=form.source.data
        )
        db.session.add(recipe)
        db.session.commit()
        flash('Recipe added')
        return redirect(url_for('index'))
    return render_template('edit_recipe.html', title='Add recipe', form=form)

@app.route('/edit_recipe/<recipe_name>', methods=['GET','POST'])
@login_required
def edit_recipe(recipe_name):
    recipe = Recipe.query.filter_by(name=recipe_name).first()
    form = EditRecipeForm(recipe.name)
    if form.validate_on_submit():
        recipe.name = form.recipe.data
        recipe.description = form.description.data
        recipe.servings = form.servings.data
        recipe.comments = form.comments.data
        recipe.source = form.source.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('recipe', recipe_name=recipe.name))
    elif request.method == 'GET':
        form.recipe.data = recipe.name
        form.description.data = recipe.description
        form.servings.data = recipe.servings
        form.comments.data = recipe.comments
        form.source.data = recipe.source
    return render_template('edit_recipe.html', title=f'Edit Recipe - {recipe.name}', form=form)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
