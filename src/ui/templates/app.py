from flask import Flask, render_template, request
from main import apply_to_job

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        job_url = request.form["job_url"]
        metadata_path = "data/user_metadata.json"
        try:
            apply_to_job(job_url, metadata_path)
            return render_template(
                "index.html", message="Application submitted successfully!"
            )
        except Exception as e:
            return render_template("index.html", message=f"Error: {str(e)}")
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
