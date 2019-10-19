from flask import render_template, flash, redirect, request, url_for
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import Post, User, followers
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime
from app.email import send_password_reset_email


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    if posts.has_next:
        next_url = url_for('index', page=posts.next_num)
    else:
        next_url = None
    if posts.has_prev:
        prev_url = url_for('index', page=posts.prev_num)
    else:
        prev_url = None
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post has been published to the world")
        return redirect(url_for('index'))
    return render_template('index.html', title='Home', posts=posts.items, form=form, next_url=next_url, prev_url=prev_url)


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
        flash("Congratulations, You are now a registered user")
        return redirect(url_for('login'))
    return render_template('register.html', title="Register Now", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    form.username(style='color:red')
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if next_page is None or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect((next_page))
    return render_template('login.html', form=form, title="Sign In")


@app.route('/user/<username>')
@login_required
def user(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    if posts.has_next:
        next_url = url_for('index', page=posts.next_num)
    else:
        next_url = None
    if posts.has_prev:
        prev_url = url_for('index', page=posts.prev_num)
    else:
        prev_url = None
    return render_template('user.html', title=username, posts=posts.items, user=user, prev_url=prev_url, next_url=next_url)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your Changes have been Added")
        return redirect(url_for('user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("The requested user {} doesnt exist".format(username))
        return redirect(url_for('index'))
    if current_user.username == username:
        flash("You cannot follow yourself")
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash("You are following {}".format(username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("The requested user {} doesnt exist".format(username))
        return redirect(url_for('index'))
    if current_user.username == username:
        flash("You cannot unfollow yourself")
        return redirect(url_for('user', username=username))
    if current_user.followed.filter(followers.c.followed_id == user.id).first():
        current_user.followed.remove(user)
        db.session.commit()
        flash("Congratulations.You are unfollowing {}".format(username))
        return redirect(url_for('user', username=username))
    flash("You dont follow {}".format(username))
    return redirect(url_for('index'))


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    if posts.has_next:
        next_url = url_for('index', page=posts.next_num)
    else:
        next_url = None
    if posts.has_prev:
        prev_url = url_for('index', page=posts.prev_num)
    else:
        prev_url = None
    return render_template('index.html', title="Explore", posts=posts.items, prev_url=prev_url, next_url=next_url)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', form=form, title='Reset Password')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your Password has been reset')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)
