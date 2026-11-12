# GitHub Profile Sync (Python + Flask + Requests)

A beginner-friendly, robust Python web application that authenticates users via **GitHub OAuth (GitHub App)**, fetches their live user profile from the **GitHub REST API** (`GET https://api.github.com/user`) using Python's `requests` library, displays a pre-filled profile completion form, and saves the synchronized profile locally to `profiles.json`.

> **Note on Repository Name:** While this repository and folder are named `linkedin-profile-sync` for assignment continuity, the application implements full **GitHub OAuth 2.0 (GitHub App)** integration and live GitHub REST API data synchronization.

---

## Features

- **GitHub OAuth 2.0 (GitHub App):** Secure authorization code flow with CSRF `state` parameter validation.
- **Robust HTTP Practices:** Every network call via `requests.post()` and `requests.get()` implements:
  - Explicit `timeout=10`
  - Strict HTTP status code verification (`status_code == 200`)
  - Exception handling (`try ... except requests.RequestException`) preventing server crashes.
- **Live GitHub Profile Fetch:** Retrieves `login`, `name`, `email`, `avatar_url`, `bio`, `location`, `public_repos`, `followers`, and `html_url`.
- **Profile Completion & Merge:** Auto-fills fetched GitHub details and lets users complete additional professional fields (`headline`, `skills`, `portfolio_url`).
- **Local JSON Storage:** Saves completed profiles to `profiles.json` keyed by GitHub user ID.
- **Modern Dark-Mode UI:** Pure CSS design (`#0f172a` canvas, `#1e293b` cards) with responsive layout, raw JSON inspection panels, and interactive alerts.

---

## Project Structure

```text
linkedin-profile-sync/
├── .env                 # Local secrets (ignored by Git)
├── .env.example         # Safe environment template committed to Git
├── .gitignore           # Ignores .venv/, __pycache__/, .env, profiles.json
├── requirements.txt     # Python dependencies (flask, requests, python-dotenv)
├── app.py               # Main Flask application and OAuth routes
├── templates/
│   ├── login.html       # Dark-mode login landing page with GitHub Sign-In
│   └── profile.html     # Profile dashboard, completion form & JSON viewers
└── README.md            # Complete project documentation & sample outputs
```

---

## Step-by-Step Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/bilal-farooqui/linkedin-profile-sync.git
cd linkedin-profile-sync
```

### 2. Create and Activate a Virtual Environment

**On Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (`.env`)
Copy the provided `.env.example` template to `.env`:

```bash
cp .env.example .env
```

Open `.env` and fill in your GitHub App credentials:

```env
FLASK_SECRET_KEY=bilal-github-profile-sync-2026
GITHUB_CLIENT_ID=Ov23liF4ue0keyhn2xrF
GITHUB_CLIENT_SECRET=YOUR_ACTUAL_GITHUB_CLIENT_SECRET
GITHUB_REDIRECT_URI=http://localhost:8000/callback
```

> **Important:** `.env` is listed in `.gitignore` and is **never** committed to version control.

---

## GitHub App Configuration

When configuring your GitHub App on GitHub:
1. Navigate to **GitHub Settings &rarr; Developer Settings &rarr; GitHub Apps**.
2. Set **Callback URL** to: `http://localhost:8000/callback`
3. Generate a **Client secret** and copy it into your local `.env`.
4. Under permissions, ensure **Read-only** access to User Profile data.

---

## Running the Application

Start the Flask development server:

```bash
python app.py
```

The application will run locally at:
👉 **[http://localhost:8000](http://localhost:8000)**

### Application Workflow:
1. Open `http://localhost:8000` in your browser (use an Incognito/Private window for fresh OAuth testing).
2. Click **"Sign in with GitHub"**.
3. Authorize the application on GitHub.
4. GitHub redirects back to `/callback`, which securely exchanges the code for an access token and fetches user data.
5. You are redirected to `/profile` with your GitHub avatar, repository stats, follower count, and pre-filled form.
6. Add your professional headline, skills, and portfolio URL, then click **"Save Completed Profile"** to persist to `profiles.json`.

---

## Sample API Output & Data Structures

### 1. Raw Response from `GET https://api.github.com/user`

```json
{
  "login": "octocat",
  "id": 583231,
  "node_id": "MDQ6VXNlcjU4MzIzMQ==",
  "avatar_url": "https://avatars.githubusercontent.com/u/583231?v=4",
  "gravatar_id": "",
  "url": "https://api.github.com/users/octocat",
  "html_url": "https://github.com/octocat",
  "followers_url": "https://api.github.com/users/octocat/followers",
  "following_url": "https://api.github.com/users/octocat/following{/other_user}",
  "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
  "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
  "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
  "organizations_url": "https://api.github.com/users/octocat/orgs",
  "repos_url": "https://api.github.com/users/octocat/repos",
  "events_url": "https://api.github.com/users/octocat/events{/privacy}",
  "received_events_url": "https://api.github.com/users/octocat/received_events",
  "type": "User",
  "user_view_type": "public",
  "site_admin": false,
  "name": "The Octocat",
  "company": "@github",
  "blog": "https://github.blog",
  "location": "San Francisco",
  "email": "octocat@github.com",
  "hireable": null,
  "bio": "Building the future of software development.",
  "twitter_username": null,
  "public_repos": 8,
  "public_gists": 8,
  "followers": 16420,
  "following": 9,
  "created_at": "2011-01-25T18:44:36Z",
  "updated_at": "2026-11-12T12:00:00Z"
}
```

---

### 2. Saved Record in `profiles.json`

```json
{
  "583231": {
    "github_id": 583231,
    "username": "octocat",
    "full_name": "The Octocat",
    "email": "octocat@github.com",
    "headline": "Lead Open Source Ambassador & Full-Stack Developer",
    "location": "San Francisco",
    "bio": "Building the future of software development.",
    "skills": [
      "Python",
      "Flask",
      "REST APIs",
      "Requests",
      "Git",
      "OAuth 2.0"
    ],
    "portfolio_url": "https://github.blog",
    "avatar_url": "https://avatars.githubusercontent.com/u/583231?v=4",
    "github_profile_url": "https://github.com/octocat",
    "public_repos": 8,
    "followers": 16420,
    "synced_at": "2026-11-12T14:30:00.000000+00:00"
  }
}
```

---

## License

This project is created for educational purposes as part of the Web Development & API Integration Course Assignment.
