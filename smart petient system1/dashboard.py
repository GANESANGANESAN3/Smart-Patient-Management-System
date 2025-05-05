from flask import Blueprint, jsonify
from pymongo import MongoClient
from datetime import datetime

dashboard_api = Blueprint('dashboard_api', __name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["your_database_name"]

@dashboard_api.route('/api/dashboard-stats')
def dashboard_stats():
    total_logins = db.admin_logins.count_documents({})
    total_patients = db.patients.count_documents({})
    return jsonify({
        "totalLogins": total_logins,
        "totalPatients": total_patients
    })
