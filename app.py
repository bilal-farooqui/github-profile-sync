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
import requests
from flask import Flask, redirect, render_template, request, session, url_for, flash

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


@app.route("/callback")
def callback():
    """
    Handles the OAuth callback from GitHub.
    1. Verifies the returned CSRF 'state' against session["oauth_state"].
    2. Exchanges the temporary authorization 'code' for an access token via POST.
    3. Fetches live user profile data from GitHub REST API via GET.
    4. Stores the profile data in session and redirects to /profile.
    """
    returned_state = request.args.get("state")
    expected_state = session.pop("oauth_state", None)

    # 1. CSRF State Verification
    if not returned_state or returned_state != expected_state:
        flash("State verification failed (possible CSRF attack). Please try logging in again.", "error")
        return redirect(url_for("index"))

    # Check for authorization errors returned by GitHub
    error = request.args.get("error")
    if error:
        error_description = request.args.get("error_description", "Unknown authorization error.")
        flash(f"GitHub Authorization Error: {error_description}", "error")
        return redirect(url_for("index"))

    code = request.args.get("code")
    if not code:
        flash("Authorization code missing from GitHub callback response.", "error")
        return redirect(url_for("index"))

    # 2. Token Exchange via requests.post
    token_payload = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": GITHUB_REDIRECT_URI
    }
    token_headers = {
        "Accept": "application/json"
    }

    try:
        token_response = requests.post(
            GITHUB_TOKEN_URL,
            data=token_payload,
            headers=token_headers,
            timeout=10
        )
    except requests.RequestException as exc:
        flash(f"Network error while connecting to GitHub Token URL: {exc}", "error")
        return redirect(url_for("index"))

    if token_response.status_code != 200:
        flash(f"Failed to exchange token. HTTP Status: {token_response.status_code}", "error")
        return redirect(url_for("index"))

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        error_msg = token_data.get("error_description", token_data.get("error", "No access token received."))
        flash(f"Token exchange error: {error_msg}", "error")
        return redirect(url_for("index"))

    # 3. Live User Profile Fetch via requests.get
    user_headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json"
    }

    try:
        user_response = requests.get(
            GITHUB_USER_API_URL,
            headers=user_headers,
            timeout=10
        )
    except requests.RequestException as exc:
        flash(f"Network error while fetching profile from GitHub API: {exc}", "error")
        return redirect(url_for("index"))

    if user_response.status_code != 200:
        flash(f"Failed to fetch user profile. HTTP Status: {user_response.status_code}", "error")
        return redirect(url_for("index"))

    github_profile = user_response.json()

    # Store profile and access token in session
    session["github_profile"] = github_profile
    session["access_token"] = access_token

    flash("Successfully authenticated with GitHub!", "info")
    return redirect(url_for("profile"))


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
