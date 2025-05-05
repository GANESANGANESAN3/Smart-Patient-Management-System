from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os
import random
import re
from werkzeug.utils import secure_filename
from flask import send_file
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


# Initialize Flask App
app = Flask(__name__)
CORS(app)

# File Upload Configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["smart_patient_system"]

# -----------------------------
# 🌐 PAGE ROUTES
# -----------------------------

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/adminsignin')
def admin_signin():
    return render_template("adminsignin.html")

@app.route('/adminaccess')
def admin_access():
    return render_template("adminaccess.html")

@app.route('/patientregister')
def patient_register():
    return render_template("patientregister.html")

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/diseaseupload')
def disease_upload():
    return render_template('diseaseupload.html')

@app.route('/hospitalreport')
def hospital_report_page():
    return render_template('hospitalreport.html')

@app.route('/upload-success')
def upload_success():
    return render_template('uploadsuccess.html')

@app.route('/viewreport')
def view_report():
    return render_template('viewreport.html')
    

# -----------------------------
# 🔐 BACKEND APIs
# -----------------------------

@app.route('/api/admin-login', methods=['POST'])
def admin_login():
    data = request.get_json()
    userid = data.get("userid")
    password = data.get("password")
    hospitalname = data.get("hospitalname")

    admin = db.admins.find_one({
        "userid": userid,
        "password": password,
        "hospitalname": hospitalname
    })

    if admin:
        db.login_logs.insert_one({
            "userid": userid,
            "hospitalname": hospitalname,
            "timestamp": datetime.now()
        })
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Invalid credentials or hospital name"})

@app.route('/api/register-patient', methods=['POST'])
def register_patient():
    data = request.get_json()
    barcode = ''.join([str(random.randint(0, 9)) for _ in range(12)])
    data['barcode'] = barcode

    if data.get("hospitalname"): data["hospitalname"] = data["hospitalname"]
    if data.get("userid"): data["userid"] = data["userid"]

    db.patients.insert_one(data)
    return jsonify({
        "success": True,
        "message": f"Patient registered successfully! Barcode: {barcode}",
        "barcode": barcode
    })

@app.route('/api/dashboard-stats')
def dashboard_stats():
    return jsonify({
        "totalPatients": db.patients.count_documents({}),
        "totalAdmins": db.admins.count_documents({})
    })

@app.route('/api/patients', methods=['GET'])
def get_patients():
    return jsonify(list(db.patients.find({}, {"_id": 0, "aadhaar": 1, "name": 1})))

# --- 🔄 Disease Upload with File ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload-disease', methods=['POST'])
def upload_disease():
    try:
        # Get form data
        aadhaar = request.form.get("aadhaar")
        hospitalname = request.form.get("hospitalname")
        disease = request.form.get("disease")
        symptoms = request.form.get("symptoms")
        treatment = request.form.get("treatment")
        medication = request.form.get("medication")
        patienttype = request.form.get("patienttype")
        timestamp = request.form.get("timestamp")
        userid = request.form.get("userid")

        # Validate required fields
        required = [aadhaar, hospitalname, disease, symptoms, treatment, medication, patienttype, timestamp, userid]
        if not all(required):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        # Handle file upload
        file = request.files.get('report')
        report_filename = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            report_filename = f"{aadhaar}_{int(datetime.now().timestamp())}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], report_filename))

        # Insert to DB
        disease_data = {
            "aadhaar": aadhaar,
            "hospitalname": hospitalname,
            "disease": disease,
            "symptoms": symptoms,
            "treatment": treatment,
            "medication": medication,
            "patienttype": patienttype,
            "userid": userid,
            "timestamp": datetime.fromisoformat(timestamp),
            "report_filename": report_filename
        }

        db.diseases.insert_one(disease_data)
        return jsonify({"success": True, "message": "Disease info uploaded successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
@app.route('/api/patient-details', methods=['POST'])
def patient_details():
    data = request.get_json()
    print("Request data:", data)  # Debug log

    hospitalname = data.get('hospitalname')
    userid = data.get('userid')
    patient_type = data.get('patienttype')  # Make sure key is correct!

    disease_entries = list(db.diseases.find({
        'hospitalname': hospitalname,
        'userid': userid,
        'patienttype': patient_type
    }))

    print("Found", len(disease_entries), "disease records")  # Debug log

    patients = []
    for entry in disease_entries:
        patient = db.patients.find_one({'aadhaar': entry['aadhaar']}, {'_id': 0})
        if patient:
            patient.update({
                'disease': entry.get('disease'),
                'symptoms': entry.get('symptoms'),
                'treatment': entry.get('treatment'),
                'medication': entry.get('medication'),
                'patienttype': entry.get('patienttype'),
                'timestamp': entry.get('timestamp'),
                'report_filename': entry.get('report_filename')
            })
            patients.append(patient)

    return jsonify({'success': True, 'patients': patients})


@app.route('/api/get-patients', methods=['POST'])
def alias_get_patients():
    return patient_details()

@app.route('/api/patient-full-details', methods=['POST'])
def get_patient_and_disease():
    data = request.get_json()
    aadhaar = data.get("aadhaar")
    name = data.get("name")
    barcode = data.get("barcode")

    patient = None

    if barcode:
        patient = db.patients.find_one({"barcode": barcode})
    elif aadhaar and name:
        patient = db.patients.find_one({
            "aadhaar": aadhaar,
            "name": re.compile(f"^{re.escape(name)}$", re.IGNORECASE)
        })
    else:
        return jsonify({"success": False, "message": "Please provide Aadhaar and Name or Barcode"}), 400

    if not patient:
        return jsonify({"success": False, "message": "Patient not found"}), 404

    diseases = list(db.diseases.find({"aadhaar": patient.get("aadhaar")}))
    for d in diseases:
        d["_id"] = str(d["_id"])
        if isinstance(d.get("timestamp"), datetime):
            d["timestamp"] = d["timestamp"].isoformat()

    patient["_id"] = str(patient["_id"])

    return jsonify({
        "success": True,
        "patient": {
            "name": patient.get("name"),
            "aadhaar": patient.get("aadhaar"),
            "age": patient.get("age"),
            "gender": patient.get("gender"),
            "phone": patient.get("phone")
        },
        "diseases": diseases
    })
@app.route('/api/hospital-report', methods=['POST'])
def hospital_report():
    data = request.get_json()
    hospitalname = data.get("hospitalname")
    userid = data.get("userid")
    password = data.get("password")  # Optional: only if password is needed

    print("Received data:", data)  # 👈 Debug log

    # Optional password check
    if password:
        admin = db.admins.find_one({
            "hospitalname": hospitalname,
            "userid": userid,
            "password": password
        })
        if not admin:
            print("Admin not found!")  # 👈 Debug log
            return jsonify({"success": False, "message": "Invalid credentials"}), 401

    # Fetch counts
    total_patients = db.diseases.count_documents({"hospitalname": hospitalname, "userid": userid})
    inpatients = db.diseases.count_documents({"hospitalname": hospitalname, "userid": userid, "patienttype": "inpatient"})
    outpatients = db.diseases.count_documents({"hospitalname": hospitalname, "userid": userid, "patienttype": "outpatient"})

    return jsonify({
        "success": True,
        "totalPatients": total_patients,   # 👈 camelCase for frontend match
        "inpatients": inpatients,
        "outpatients": outpatients
    })


@app.route('/api/hospital-patient-details', methods=['POST'])
def hospital_patient_details():
    data = request.get_json()
    hospitalname = data.get("hospitalname")
    patienttype = data.get("patienttype")
    userid = data.get("userid")

    details = list(db.diseases.find({
        "hospitalname": hospitalname,
        "patienttype": patienttype,
        "userid": userid
    }, {"_id": 0}))

    return jsonify(details)

# Serve uploaded reports
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/download-report', methods=['POST'])
def download_report():
    data = request.get_json()
    hospitalname = data.get('hospitalname')
    userid = data.get('userid')
    patient_type = data.get('patienttype')

    disease_entries = list(db.diseases.find({
        'hospitalname': hospitalname,
        'userid': userid,
**({'patienttype': patient_type} if patient_type else {})
    }))

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, f"{(patient_type.title() if patient_type else 'All Patients')} Report - {hospitalname}")

    p.setFont("Helvetica", 10)
    y = height - 80

    for i, entry in enumerate(disease_entries, 1):
        line = f"{i}. Aadhaar: {entry.get('aadhaar', 'N/A')} | Disease: {entry.get('disease', 'N/A')} | Type: {entry.get('patienttype', 'N/A')}"
        p.drawString(50, y, line)
        y -= 15
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 10)
            y = height - 50

    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{patient_type}_report.pdf", mimetype='application/pdf')

# -----------------------------
# ▶️ Run the App
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
