# LogoMetric

LogoMetric is a web-based system designed to evaluate logo designs using automated visual analysis.

The system analyzes uploaded images and provides structured feedback based on key design principles such as contrast, simplicity, balance, and overall visual effectiveness.

It also includes logic to determine whether an uploaded image resembles a logo or not.

## Features
- Logo evaluation based on:
  - Contrast
  - Simplicity (complexity)
  - Balance
- Logo likelihood detection (logo vs non-logo)
- Dynamic feedback generation
- User authentication (register/login)
- Analysis history tracking
- PDF export of results
- Interactive dashboard with statistics


## Technologies Used
- **Backend:** Python (Flask)
- **Database:** SQLite
- **Frontend:** HTML, CSS, Bootstrap
- **Image Processing:** OpenCV, NumPy
- **PDF Generation:** ReportLab
- **Deployment:** Render
- **Version Control:** GitHub


## ⚙️ How to Run Locally
### 1. Clone the repository
```bash
git clone https://github.com/00012876/logometric.git
cd logometric
2. Create virtual environment
python -m venv venv

Activate it:
venv\Scripts\activate   # Windows
3. Install dependencies
pip install -r requirements.txt
4. Run the application
python app.py
5. Open in browser
http://127.0.0.1:5000


Live Demo(can lag sometimes better use local version)
https://logometric.onrender.com

Project Purpose:
The goal of this system is to provide a structured and semi-automated way to evaluate logo designs.
Logo evaluation is typically subjective. This system introduces measurable criteria to support designers and businesses in making more informed decisions.


Limitations

The system uses heuristic-based analysis rather than a trained AI model
Accuracy may vary depending on image type
Complex images may still be partially misclassified
🔮 Future Improvements
Integration of machine learning model
Improved classification accuracy
More advanced visual analysis
User feedback system


Author

Student 00012876
BSc (Hons) Business Information Systems
Westminster International University in Tashkent


License

This project is created for educational purposes.