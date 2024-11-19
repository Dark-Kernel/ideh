from flask import Blueprint, redirect, render_template, url_for, flash, session
from flask_dance.contrib.google import make_google_blueprint, google
from ..models.models import db, User
from functools import wraps
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

def create_google_blueprint(app):
    """Create Google OAuth blueprint with app config."""
    return make_google_blueprint(
        client_id=app.config.get('GOOGLE_OAUTH_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_OAUTH_CLIENT_SECRET'),
        scope=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email"
        ],
        redirect_to='auth.login_callback',
        login_url='/login/google',
    )

@auth_bp.route('/')
def home():
    return render_template('index.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    
    if not google.authorized:
        logger.info("Redirecting to Google login")
        return redirect(url_for('google.login'))
    
    return redirect(url_for('auth.login_callback'))

@auth_bp.route('/login/callback')
def login_callback():
    if not google.authorized:
        flash('Failed to log in.', 'error')
        return redirect(url_for('auth.login'))

    try:
        resp = google.get('/oauth2/v1/userinfo')
        if not resp.ok:
            flash('Failed to get user info.', 'error')
            return redirect(url_for('auth.login'))

        user_info = resp.json()
        logger.info(f"Received user info: {user_info.get('email')}")

        # Find or create user
        user = User.query.filter_by(email=user_info['email']).first()
        if not user:
            user = User(
                id=user_info['id'],  # Use Google's ID as user ID
                name=user_info['name'],
                email=user_info['email'],
                social_login_provider='google',
                profile_picture=user_info.get('picture')
            )
            db.session.add(user)
            try:
                db.session.commit()
                logger.info(f"Created new user: {user.email}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating user: {str(e)}")
                flash('An error occurred during registration.', 'error')
                return redirect(url_for('auth.login'))

        # Set session data
        session['user_id'] = user.id
        session['user_info'] = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'profile_picture': user.profile_picture
        }

        flash('Successfully logged in!', 'success')
        return redirect(url_for('dashboard.index'))

    except Exception as e:
        logger.error(f"Error in login callback: {str(e)}")
        flash('An error occurred during login.', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    # Clear all session data
    session.clear()
    
    # Token revocation if needed
    if google.authorized:
        try:
            token = google.token['access_token']
            resp = google.post(
                'https://accounts.google.com/o/oauth2/revoke',
                params={'token': token},
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")

    flash('Successfully logged out.', 'success')
    return redirect(url_for('auth.home'))
