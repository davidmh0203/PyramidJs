from flask import Flask, render_template, request, redirect, session, url_for
from utils.genie_scraper import scrape_genie_playlist
from utils.youtube_api import get_authenticated_service, search_video, create_playlist, add_to_playlist
from google_auth_oauthlib.flow import Flow
import os

app = Flask(__name__)
app.secret_key = "your-secret-key"
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/youtube"]
REDIRECT_URI = "http://localhost:5000/auth/callback"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session["state"] = state
    return redirect(authorization_url)

@app.route("/auth/callback")
def oauth2callback():
    state = session["state"]
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    session["credentials"] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    return redirect(url_for("dashboard"))

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "credentials" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        genie_url = request.form.get("genie_url")
        playlist_name = request.form.get("playlist_name")
        songs = scrape_genie_playlist(genie_url)

        service = get_authenticated_service(session["credentials"])
        playlist_id = create_playlist(service, playlist_name)

        for song in songs:
            video_id = search_video(service, song)
            if video_id:
                add_to_playlist(service, playlist_id, video_id)

        return render_template("success.html", playlist_id=playlist_id)

    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)
