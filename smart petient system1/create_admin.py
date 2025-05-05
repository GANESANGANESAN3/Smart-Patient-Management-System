from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["smart_patient_system"]
admin_collection = db["admins"]

# List of admin users to insert with hospital names
admin_list = [
    {"userid": "admin001", "password": "secure123", "hospitalname": "City Hospital"},
    {"userid": "admin002", "password": "pass456", "hospitalname": "Sunrise Clinic"},
    {"userid": "admin003", "password": "admin789", "hospitalname": "Green Valley Hospital"},
    {"userid": "admin004", "password": "admin000", "hospitalname": "Metro Health Center"},
    {"userid": "admin005", "password": "mypassword", "hospitalname": "Riverfront Medical"}
]

# Insert each admin if not already present for that hospital
for admin_data in admin_list:
    query = {"userid": admin_data["userid"], "hospitalname": admin_data["hospitalname"]}
    if not admin_collection.find_one(query):
        admin_collection.insert_one(admin_data)
        print(f"✅ Inserted: {admin_data['userid']} ({admin_data['hospitalname']})")
    else:
        print(f"⚠️ Already exists: {admin_data['userid']} ({admin_data['hospitalname']})")

# Show all admins
print("\n🔍 Admins in the database:")
for admin in admin_collection.find():
    print(admin)
