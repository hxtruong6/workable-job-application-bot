import sys

sys.path.append("..")
sys.path.append(".")

from flask import Flask, render_template, request, jsonify
import json
import os
from pathlib import Path
from src.config.settings import settings

app = Flask(__name__)

# Update path to use settings
USER_METADATA_FILE = str(settings.USER_METADATA_PATH)


# Load user metadata
def load_metadata():
    if not os.path.exists(USER_METADATA_FILE):
        return {}
    try:
        with open(USER_METADATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


# Save metadata to file
def save_metadata(data):
    with open(USER_METADATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def apply_to_job(job_url):
    print(f"Applying to job: {job_url}")
    return "Application submitted successfully!"


def process_metadata(form_data, existing_metadata=None):
    """Process form data while preserving existing metadata"""
    if existing_metadata is None:
        existing_metadata = {}

    new_metadata = {
        "name": form_data.get("name", "").strip(),
        "contact_information": {
            "email": form_data.get("email", "").strip(),
            "phone": form_data.get("phone", "").strip(),
            "current_address": {
                "city": form_data.get("city", "").strip(),
                "state": form_data.get("state", "").strip(),
                "country": form_data.get("country", "").strip(),
                "zip_code": form_data.get("zip_code", "").strip(),
            },
            "linkedin": form_data.get("linkedin", "").strip(),
        },
        "years_of_experience": form_data.get("years_of_experience", "").strip(),
        "skills": [
            skill.strip()
            for skill in form_data.get("skills", "").split(",")
            if skill.strip()
        ],
        "education": existing_metadata.get("education", []),
        "certifications": (
            [
                cert.strip()
                for cert in form_data.get("certifications", "").split(",")
                if cert.strip()
            ]
            if form_data.get("certifications")
            else existing_metadata.get("certifications", [])
        ),
        "projects": (
            [
                project.strip()
                for project in form_data.get("projects", "").split(",")
                if project.strip()
            ]
            if form_data.get("projects")
            else existing_metadata.get("projects", [])
        ),
        "languages": (
            [
                lang.strip()
                for lang in form_data.get("languages", "").split(",")
                if lang.strip()
            ]
            if form_data.get("languages")
            else existing_metadata.get("languages", [])
        ),
        "industries": (
            [
                industry.strip()
                for industry in form_data.get("industries", "").split(",")
                if industry.strip()
            ]
            if form_data.get("industries")
            else existing_metadata.get("industries", [])
        ),
        "relevant_job_titles": existing_metadata.get("relevant_job_titles", []),
        "user_salary": form_data.get(
            "user_salary", existing_metadata.get("user_salary", "")
        ),
        "experience": [],
    }

    # Process work experience
    experience_count = int(form_data.get("experience_count", 0))
    for i in range(experience_count):
        job_title = form_data.get(f"job_title_{i}", "").strip()
        company = form_data.get(f"company_{i}", "").strip()

        if job_title and company:  # Only add if essential fields are present
            new_metadata["experience"].append(
                {
                    "job_title": job_title,
                    "company": company,
                    "location": form_data.get(f"location_{i}", "").strip(),
                    "start_date": form_data.get(f"start_date_{i}", "").strip(),
                    "end_date": form_data.get(f"end_date_{i}", "").strip(),
                    "responsibilities": [
                        resp.strip()
                        for resp in form_data.get(f"responsibilities_{i}", "").split(
                            "\n"
                        )
                        if resp.strip()
                    ],
                }
            )

    # If no new experience was added, preserve existing experience
    if not new_metadata["experience"] and "experience" in existing_metadata:
        new_metadata["experience"] = existing_metadata["experience"]

    # Update education if form contains education data
    if form_data.get("degree"):
        education_entry = {
            "degree": form_data.get("degree", "").strip(),
            "field_of_study": form_data.get("field_of_study", "").strip(),
            "institution": form_data.get("institution", "").strip(),
            "graduation_date": form_data.get("graduation_date", "").strip(),
        }
        if any(education_entry.values()):  # Only add if at least one field is filled
            new_metadata["education"] = [education_entry] + new_metadata["education"][
                1:
            ]

    # Update industries if provided in form
    if form_data.get("industries"):
        new_metadata["industries"] = [
            industry.strip()
            for industry in form_data.get("industries", "").split(",")
            if industry.strip()
        ]

    return new_metadata


@app.route("/", methods=["GET", "POST"])
def index():
    metadata = load_metadata()
    message = None
    message_type = "success"

    if request.method == "POST":
        if "save_metadata" in request.form:
            try:
                # Process the form data while preserving existing metadata
                new_metadata = process_metadata(request.form, metadata)
                save_metadata(new_metadata)
                metadata = new_metadata
                message = "Profile updated successfully!"
            except Exception as e:
                message = f"Error saving profile: {str(e)}"
                message_type = "danger"

        elif "job_url" in request.form:
            # Handle job application submission
            job_url = request.form.get("job_url", "").strip()
            if job_url:
                try:
                    print(f"Applying to job: {job_url}")
                    message = "Application submitted successfully!"
                except Exception as e:
                    message = f"Error: {str(e)}"
                    message_type = "danger"
            else:
                message = "Please enter a valid job URL."
                message_type = "danger"

    return render_template(
        "index.html", message=message, message_type=message_type, metadata=metadata
    )


def run_app():
    app.run(debug=True, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    run_app()
