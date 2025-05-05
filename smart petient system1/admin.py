from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["smart_patient_system"]

# 🧹 Delete old admin entries without hospitalname
result = db.admins.delete_many({ "hospitalname": { "$exists": False } })
print(f"🧹 Deleted {result.deleted_count} outdated admin(s) without hospital name.")

# 🔍 Show current clean list
for admin in db.admins.find():
    print(admin)
