from flask import Flask, request, render_template, send_file
import pdfplumber
import spacy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Check if file is uploaded
        if "resume" not in request.files:
            return "No file uploaded", 400
        file = request.files["resume"]
        if file.filename == "":
            return "No file selected", 400

        # Save file securely
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        # Extract text from PDF
        try:
            with pdfplumber.open(file_path) as pdf:
                text = "".join(page.extract_text() or "" for page in pdf.pages)
        except Exception as e:
            os.remove(file_path)
            return f"Error processing PDF: {str(e)}", 500

        # Parse resume with spaCy
        doc = nlp(text)
        data = {
            "name": "",
            "summary": "",
            "experience": [],
            "skills": [],
            "contact": ""
        }
        for ent in doc.ents:
            if ent.label_ == "PERSON" and not data["name"]:
                data["name"] = ent.text
            elif ent.label_ == "ORG":
                data["experience"].append({"company": ent.text, "role": ""})
            elif ent.label_ == "EMAIL":
                data["contact"] = ent.text

        # Extract skills (simple keyword-based, improve with a custom list)
        skill_keywords = ["python", "javascript", "sql", "communication", "leadership"]
        data["skills"] = [token.text for token in doc if token.text.lower() in skill_keywords]
        data["summary"] = text[:200] + "..."  # Truncate for demo

        # Delete uploaded file (privacy)
        os.remove(file_path)

        # Render portfolio
        return render_template("portfolio.html", data=data)

    return render_template("index.html")

@app.route("/download")
def download_portfolio():
    # For simplicity, serve the rendered portfolio as HTML
    # In production, generate and save the static HTML
    return send_file("templates/portfolio.html", as_attachment=True, download_name="portfolio.html")

if __name__ == "__main__":
    app.run(debug=True)