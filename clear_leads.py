import requests

# כתובת השרת הציבורית שלך (החלף ב-IP או בדומיין של השרת)
SERVER_URL = "http://YOUR_SERVER_IP:5000/api/clear-leads"

def clear_cloud_leads():
    try:
        response = requests.post(SERVER_URL, json={"clear": True})
        if response.status_code == 200:
            print("✅ הטבלה בשרת הענן רוקנה בהצלחה!")
        else:
            print(f"❌ שגיאה מהשרת: {response.status_code}")
    except Exception as e:
        print(f"❌ שגיאה בהתחברות לשרת: {e}")

if __name__ == "__main__":
    clear_cloud_leads()