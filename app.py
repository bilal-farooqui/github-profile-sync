import os
import json
import secrets
from datetime import datetime, timezone
from urllib.parse import urlencode
from dotenv import load_dotenv
import requests
from flask import Flask, redirect, render_template, request, session, url_for, flash

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-key-for-development")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/callback")

PROFILES_FILE = os.path.join(os.path.dirname(__file__), "profiles.json")

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API_URL = "https://api.github.com/user"


def load_saved_profiles() -> dict:
    if not os.path.exists(PROFILES_FILE):
        return {}
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def save_profile(user_id: str, profile_data: dict) -> None:
    profiles = load_saved_profiles()
    profiles[str(user_id)] = profile_data
    with open(PROFILES_FILE, "w", encoding="utf-8") as file:
        json.dump(profiles, file, indent=2, ensure_ascii=False)


@app.route("/")
def index():
    config_warning = None
    if not GITHUB_CLIENT_ID or GITHUB_CLIENT_ID == "your-github-app-client-id":
        config_warning = "GITHUB_CLIENT_ID is not configured in .env."
    elif not GITHUB_CLIENT_SECRET or GITHUB_CLIENT_SECRET == "PASTE_YOUR_GITHUB_CLIENT_SECRET_HERE":
        config_warning = "GITHUB_CLIENT_SECRET contains placeholder text. Please update .env with your real secret."

    if "github_profile" in session:
        return redirect(url_for("profile"))

    return render_template("login.html", config_warning=config_warning)


@app.route("/login")
def login():
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
    returned_state = request.args.get("state")
    expected_state = session.pop("oauth_state", None)

    if not returned_state or returned_state != expected_state:
        flash("State verification failed (possible CSRF attack). Please try logging in again.", "error")
        return redirect(url_for("index"))

    error = request.args.get("error")
    if error:
        error_description = request.args.get("error_description", "Unknown authorization error.")
        flash(f"GitHub Authorization Error: {error_description}", "error")
        return redirect(url_for("index"))

    code = request.args.get("code")
    if not code:
        flash("Authorization code missing from GitHub callback response.", "error")
        return redirect(url_for("index"))

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

    session["github_profile"] = github_profile
    session["access_token"] = access_token

    flash("Successfully authenticated with GitHub!", "info")
    return redirect(url_for("profile"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    github_profile = session.get("github_profile")
    if not github_profile:
        flash("Please sign in with GitHub to view your profile.", "error")
        return redirect(url_for("index"))

    user_id = str(github_profile.get("id"))
    all_saved_profiles = load_saved_profiles()
    existing_saved = all_saved_profiles.get(user_id)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip() or github_profile.get("name") or github_profile.get("login")
        email = request.form.get("email", "").strip() or github_profile.get("email") or ""
        headline = request.form.get("headline", "").strip()
        location = request.form.get("location", "").strip() or github_profile.get("location") or ""
        portfolio_url = request.form.get("portfolio_url", "").strip() or github_profile.get("blog") or ""
        bio = request.form.get("bio", "").strip() or github_profile.get("bio") or ""
        skills_raw = request.form.get("skills", "").strip()
        skills_list = [s.strip() for s in skills_raw.split(",") if s.strip()] if skills_raw else []

        merged_profile = {
            "github_id": github_profile.get("id"),
            "username": github_profile.get("login"),
            "full_name": full_name,
            "email": email,
            "headline": headline,
            "location": location,
            "bio": bio,
            "skills": skills_list,
            "portfolio_url": portfolio_url,
            "avatar_url": github_profile.get("avatar_url"),
            "github_profile_url": github_profile.get("html_url"),
            "public_repos": github_profile.get("public_repos"),
            "followers": github_profile.get("followers"),
            "synced_at": datetime.now(timezone.utc).isoformat()
        }

        save_profile(user_id, merged_profile)
        flash("Profile completed and successfully saved to profiles.json!", "success")
        existing_saved = merged_profile

    form_data = {
        "full_name": (existing_saved.get("full_name") if existing_saved else github_profile.get("name")) or github_profile.get("login") or "",
        "email": (existing_saved.get("email") if existing_saved else github_profile.get("email")) or "",
        "headline": (existing_saved.get("headline") if existing_saved else "") or "",
        "location": (existing_saved.get("location") if existing_saved else github_profile.get("location")) or "",
        "portfolio_url": (existing_saved.get("portfolio_url") if existing_saved else github_profile.get("blog")) or "",
        "bio": (existing_saved.get("bio") if existing_saved else github_profile.get("bio")) or "",
        "skills": ", ".join(existing_saved.get("skills", [])) if existing_saved and isinstance(existing_saved.get("skills"), list) else ""
    }

    raw_github_json = json.dumps(github_profile, indent=2)
    saved_profile_json = json.dumps(existing_saved, indent=2) if existing_saved else None

    return render_template(
        "profile.html",
        profile=github_profile,
        form_data=form_data,
        saved_profile=existing_saved,
        saved_profile_json=saved_profile_json,
        raw_github_json=raw_github_json
    )


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="localhost", port=8000, debug=True)
