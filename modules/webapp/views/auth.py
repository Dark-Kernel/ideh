from flask import Blueprint, redirect, render_template, url_for, flash, session
from flask_dance.contrib.google import make_google_blueprint, google
# from modules.webapp.models import db, User
from ..models.models import db, User
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def create_google_blueprint(app):
    """Create Google OAuth blueprint with app config."""
    return make_google_blueprint(
        client_id=app.config.get('GOOGLE_OAUTH_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_OAUTH_CLIENT_SECRET'),
        scope=[ "openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
        redirect_to='auth.login_callback', 
        login_url='/login/google',         
        )

@auth_bp.route('/')
def home():
    return render_template('index.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_info' not in session:
            # If not, redirect to login
            return redirect(url_for('auth.login'))
        # if not google.authorized:
        #     return redirect(url_for('google.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login')
def login():
    if not google.authorized:
        print("NOT GOOLE AUTHORIZED")
        return redirect(url_for('google.login'))
    print("GOOGLE AUTHORIZED")
    # Store user information in the session
    user_info = google.get('/oauth2/v1/userinfo').json()  # This gets the authenticated user's info
    print("USER_INFO: ", user_info)
    session['user_info'] = user_info  # Store the user info in the session (e.g., email, name, etc.)

    return redirect(url_for('dashboard.index'))

@auth_bp.route('/login/callback')
def login_callback():
    if not google.authorized:
        flash('Failed to log in.', 'error')
        return redirect(url_for('auth.login'))

    resp = google.get('/oauth2/v1/userinfo')
    if not resp.ok:
        flash('Failed to get user info.', 'error')
        return redirect(url_for('auth.login'))

    user_info = resp.json()
    user = User.query.filter_by(email=user_info['email']).first()

    if not user:
        user = User(
            name=user_info['name'],
            email=user_info['email'],
            social_login_provider='google',
            profile_picture=user_info.get('picture')
        )
        db.session.add(user)
        db.session.commit()

    session['user_id'] = user.id
    flash('Successfully logged in!', 'success')
    return redirect(url_for('dashboard.index'))

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth.home'))
