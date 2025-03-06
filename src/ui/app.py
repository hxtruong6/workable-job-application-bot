from flask import Flask, render_template, request, jsonify
import json
from pathlib import Path
import asyncio

# from src.core.job_application import apply_to_job
# from src.config.settings import settings

app = Flask(__name__)


# Load metadata template
def load_metadata():
    try:
        with open("data/user_metadata.json", "r") as f:
            return json.load(f)
    except:
        return {}


def save_metadata(data):
    with open("data/user_metadata.json", "w") as f:
        json.dump(data, f, indent=2)


@app.route("/", methods=["GET", "POST"])
def index():
    metadata = load_metadata()
    message = None
    if request.method == "POST":
        if "save_metadata" in request.form:
            # Handle metadata update
            try:
                new_metadata = {
                    "name": request.form.get("name"),
                    "contact_information": {
                        "email": request.form.get("email"),
                        "phone": request.form.get("phone"),
                        "current_address": {
                            "city": request.form.get("city"),
                            "state": request.form.get("state"),
                            "country": request.form.get("country"),
                            "zip_code": request.form.get("zip_code"),
                        },
                        "linkedin": request.form.get("linkedin"),
                    },
                    "years_of_experience": request.form.get("years_of_experience"),
                    "skills": request.form.get("skills").split(","),
                    "education": [
                        {
                            "degree": request.form.get("degree"),
                            "field_of_study": request.form.get("field_of_study"),
                            "institution": request.form.get("institution"),
                            "graduation_date": request.form.get("graduation_date"),
                        }
                    ],
                }
                save_metadata(new_metadata)
                message = "Profile updated successfully!"
                metadata = new_metadata
            except Exception as e:
                message = f"Error saving profile: {str(e)}"
        else:
            # Handle job application
            job_url = request.form["job_url"]
            try:
                # await apply_to_job(job_url, str(settings.USER_METADATA_PATH))
                message = "Application submitted successfully!"
            except Exception as e:
                message = f"Error: {str(e)}"

    return render_template("index.html", message=message, metadata=metadata)


def run_app():
    app.run(debug=True, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    run_app()
