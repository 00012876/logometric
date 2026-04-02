from flask import send_file
from reportlab.pdfgen import canvas
from io import BytesIO
from analyzer import analyze_logo
import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, LogoAnalysis


app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///logometric.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("This email is already registered.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    analyses = LogoAnalysis.query.filter_by(user_id=current_user.id).order_by(LogoAnalysis.created_at.desc()).all()

    total_analyses = len(analyses)
    average_score = 0
    last_upload = "No uploads yet"
    last_upload_image = None

    overall_scores = []
    contrast_scores = []
    complexity_scores = []
    balance_scores = []
    labels = []

    if analyses:
        latest_analysis = analyses[0]
        last_upload = latest_analysis.filename
        last_upload_image = latest_analysis.filename

        for analysis in analyses[:7]:
            lines = analysis.result.splitlines()

            overall = 0
            contrast = 0
            complexity = 0
            balance = 0

            for line in lines:
                if "Overall Score:" in line:
                    try:
                        overall = int(line.split(":")[1].strip())
                    except:
                        pass
                elif "Visual Contrast Score:" in line:
                    try:
                        contrast = int(line.split(":")[1].strip())
                    except:
                        pass
                elif "Visual Simplicity Score:" in line:
                    try:
                        complexity = int(line.split(":")[1].strip())
                    except:
                        pass
                elif "Visual Balance Score:" in line:
                    try:
                        balance = int(line.split(":")[1].strip())
                    except:
                        pass

            overall_scores.append(overall)
            contrast_scores.append(contrast)
            complexity_scores.append(complexity)
            balance_scores.append(balance)
            labels.append(analysis.filename[:12])

        if overall_scores:
            average_score = round(sum(overall_scores) / len(overall_scores), 1)

        # reverse so charts show older → newer
        overall_scores.reverse()
        contrast_scores.reverse()
        complexity_scores.reverse()
        balance_scores.reverse()
        labels.reverse()

    return render_template(
        "dashboard.html",
        total_analyses=total_analyses,
        average_score=average_score,
        last_upload=last_upload,
        labels=labels,
        overall_scores=overall_scores,
        contrast_scores=contrast_scores,
        complexity_scores=complexity_scores,
        balance_scores=balance_scores,
        last_upload_image=last_upload_image
    )

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files["logo"]

        if file:
            filename = secure_filename(file.filename)
            allowed_extensions = ["png", "jpg", "jpeg"]
            ext = filename.split(".")[-1].lower()

            if ext not in allowed_extensions:
                flash("Only PNG, JPG and JPEG files are allowed.", "danger")
                return redirect(url_for("upload"))
                return redirect(url_for("upload"))

            upload_folder = os.path.join("static", "uploads")
            filepath = os.path.join(upload_folder, filename)

            file.save(filepath)

            analysis_result = analyze_logo(filepath)

            result_text = f"""
            Overall Score: {analysis_result['overall_score']}
            Logo Suitability Score: {analysis_result['logo_suitability_score']}
            Visual Contrast Score: {analysis_result['contrast_score']}
            Visual Simplicity Score: {analysis_result['complexity_score']}
            Visual Balance Score: {analysis_result['balance_score']}
            Logo Likelihood Score: {analysis_result['logo_likelihood_score']}
            Logo Classification: {analysis_result['logo_class']}
            Feedback: {analysis_result['feedback']}
            """

            new_analysis = LogoAnalysis(
                filename=filename,
                result=result_text,
                user_id=current_user.id
            )

            db.session.add(new_analysis)
            db.session.commit()

            return redirect(url_for("dashboard"))

    return render_template("upload.html")

@app.route("/history")
@login_required
def history():
    search_query = request.args.get("search", "").strip()
    min_score = request.args.get("min_score", "").strip()

    analyses = LogoAnalysis.query.filter_by(user_id=current_user.id).order_by(LogoAnalysis.created_at.desc()).all()

    filtered_analyses = []

    for analysis in analyses:
        include = True

        # search by filename
        if search_query:
            if search_query.lower() not in analysis.filename.lower():
                include = False

        # filter by minimum overall score
        if min_score:
            try:
                min_score_value = int(min_score)
                overall_score = 0

                lines = analysis.result.splitlines()
                for line in lines:
                    if "Overall Score:" in line:
                        try:
                            overall_score = int(line.split(":")[1].strip())
                        except:
                            pass

                if overall_score < min_score_value:
                    include = False
            except:
                pass

        if include:
            filtered_analyses.append(analysis)

    return render_template(
        "history.html",
        analyses=filtered_analyses,
        search_query=search_query,
        min_score=min_score, 
    )

@app.route("/delete/<int:analysis_id>")
@login_required
def delete_analysis(analysis_id):
    analysis = LogoAnalysis.query.get_or_404(analysis_id)

    if analysis.user_id != current_user.id:
        return redirect(url_for("history"))

    db.session.delete(analysis)
    db.session.commit()
    return redirect(url_for("history"))

@app.route("/result/<int:analysis_id>")
@login_required
def view_result(analysis_id):
    analysis = LogoAnalysis.query.get_or_404(analysis_id)

    if analysis.user_id != current_user.id:
        return redirect(url_for("history"))

    logo_suitability_score = None
    logo_classification = None

    for line in analysis.result.splitlines():
        if "Logo Suitability Score:" in line:
            try:
                logo_suitability_score = int(line.split(":")[1].strip())
            except:
                logo_suitability_score = None
        elif "Logo Classification:" in line:
            logo_classification = line.split(":", 1)[1].strip()

    if logo_classification == "Likely Logo":
        summary_color = "success"
    elif logo_classification == "Possibly Logo":
        summary_color = "warning"
    else:
        summary_color = "danger"

    return render_template(
        "result.html",
        analysis=analysis,
        logo_suitability_score=logo_suitability_score,
        logo_classification=logo_classification,
        summary_color=summary_color
    )

@app.route("/export_pdf/<int:analysis_id>")
@login_required
def export_pdf(analysis_id):
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader, simpleSplit
    from io import BytesIO
    import os

    analysis = LogoAnalysis.query.get_or_404(analysis_id)

    if analysis.user_id != current_user.id:
        return redirect(url_for("history"))

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    page_width, page_height = 595, 842  # A4
    y = 800

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "LogoMetric Analysis Report")

    y -= 35
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"Filename: {analysis.filename}")

    y -= 22
    pdf.drawString(50, y, f"Created At: {analysis.created_at}")

    # Add image 
    image_path = os.path.join("static", "uploads", analysis.filename)
    try:
        if os.path.exists(image_path):
            img = ImageReader(image_path)
            img_width, img_height = img.getSize()

            max_width = 220
            max_height = 160

            ratio = min(max_width / img_width, max_height / img_height)
            draw_width = img_width * ratio
            draw_height = img_height * ratio

            y -= 20
            pdf.drawImage(img, 50, y - draw_height, width=draw_width, height=draw_height, preserveAspectRatio=True, mask='auto')
            y -= draw_height + 25
    except:
        y -= 15

    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(50, y, "Analysis Result:")
    y -= 25

    pdf.setFont("Helvetica", 11)
    max_text_width = 480

    for line in analysis.result.splitlines():
        if line.strip():
            wrapped_lines = simpleSplit(line.strip(), "Helvetica", 11, max_text_width)

            for wrapped_line in wrapped_lines:
                pdf.drawString(50, y, wrapped_line)
                y -= 18

                if y < 60:
                    pdf.showPage()
                    y = 800
                    pdf.setFont("Helvetica", 11)

            y -= 4

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"analysis_{analysis.id}.pdf",
        mimetype="application/pdf"
    )

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)