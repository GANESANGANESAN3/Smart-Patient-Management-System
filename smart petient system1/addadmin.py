from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["smart_patient_system"]
admin_collection = db["admins"]

# Admin credentials to insert (with hospital name)
admin_data = {
    "hospitalname": "City Hospital",   # ✅ Add hospital name here
    "userid": "admin001",
    "password": "secure123"
}

# Check if admin already exists for the same hospital
existing_admin = admin_collection.find_one({
    "userid": admin_data["userid"],
    "hospitalname": admin_data["hospitalname"]
})

if not existing_admin:
    admin_collection.insert_one(admin_data)
    print("✅ Admin inserted successfully.")
else:
    print("⚠️ Admin already exists for this hospital.")
