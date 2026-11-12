"""
GitHub Profile Sync Application
================================
A beginner-friendly Python web application using Flask and requests.
Authenticates users via GitHub OAuth (GitHub App), fetches live user
profile data from GitHub's REST API, and syncs profile completion details.
"""

import os
import secrets
from urllib.parse import urlencode
from dotenv import load_dotenv
from flask import Flask, render_to_status, redirect, render_template, request, session, url_for, flash

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Application Configuration
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-key-for-development")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/callback")

# GitHub OAuth Endpoints
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API_URL = "https://api.github.com/user"


@app.route("/")
def index():
    """
    Renders the login landing page.
    Checks whether .env credentials are properly configured and displays
    a helpful warning banner if placeholder values are still detected.
    """
    config_warning = None
    if not GITHUB_CLIENT_ID or GITHUB_CLIENT_ID == "your-github-app-client-id":
        config_warning = "GITHUB_CLIENT_ID is not configured in .env."
    elif not GITHUB_CLIENT_SECRET or GITHUB_CLIENT_SECRET == "PASTE_YOUR_GITHUB_CLIENT_SECRET_HERE":
        config_warning = "GITHUB_CLIENT_SECRET contains placeholder text. Please update .env with your real secret."

    # If user is already authenticated in session, redirect directly to profile
    if "github_profile" in session:
        return redirect(url_for("profile"))

    return render_template("login.html", config_warning=config_warning)


@app.route("/login")
def login():
    """
    Initiates GitHub OAuth flow.
    Generates a secure random state token to prevent CSRF attacks,
    saves it into the Flask session, and redirects user to GitHub's authorization page.
    Note: As this is a GitHub App, no 'scope' parameter is passed.
    """
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state

    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "state": state
    }

    authorization_url = f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
    return redirect(authorization_url)


@app.route("/logout")
def logout():
    """
    Logs out the user by clearing the session and redirects to the login page.
    """
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Run development server on localhost:8000
    app.run(host="localhost", port=8000, debug=True)
