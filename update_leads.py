import os
import json
import git
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# הרשאות גישה ל-Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    """התחברות ל-Google Drive API"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def update_drive_file(json_file_path, drive_file_name="leads_database.json"):
    """מעדכן או יוצר את קובץ ה-JSON ב-Google Drive"""
    service = get_drive_service()
    query = f"name = '{drive_file_name}' and trashed = false"
    results = service.files().list(q=query, spaces='drive', fields="files(id, name)").execute()
    files = results.get('files', [])
    
    media = MediaFileUpload(json_file_path, mimetype='application/json', resumable=True)

    if files:
        file_id = files[0]['id']
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"✅ הקובץ עודכן בהצלחה ב-Google Drive.")
    else:
        file_metadata = {'name': drive_file_name, 'mimeType': 'application/json'}
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"✅ קובץ חדש נוצר ב-Google Drive.")

def generate_html_file(leads, html_filename="index.html"):
    """מזריק את ה-JSON לתוך ה-HTML ומייצר קובץ מעודכן"""
    html_content = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
    <meta http-equiv="Pragma" content="no-cache" />
    <meta http-equiv="Expires" content="0" />
    <title>ניהול לידים אוטומטי - היתרי עובדים זרים 2026</title>
    <style>
        :root {{
            --primary: #2c3e50; --secondary: #34495e; --accent: #3498db;
            --success: #27ae60; --danger: #c0392b; --bg: #f8f9fa;
            --card-bg: #ffffff; --text: #333333; --border: #e1e8ed;
        }}
        body {{ font-family: system-ui, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 20px; direction: rtl; }}
        .container {{ max-width: 1500px; margin: 0 auto; }}
        header {{ text-align: center; margin-bottom: 25px; }}
        h1 {{ color: var(--primary); margin-bottom: 8px; font-size: 26px; }}
        .controls {{ display: flex; justify-content: space-between; align-items: center; background: var(--card-bg); padding: 15px 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; gap: 15px; flex-wrap: wrap; }}
        .search-box {{ flex: 1; min-width: 280px; padding: 12px 16px; font-size: 15px; border: 1px solid var(--border); border-radius: 8px; outline: none; }}
        .filter-btn {{ padding: 12px 20px; background-color: var(--secondary); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; }}
        .filter-btn.active {{ background-color: var(--success); }}
        .table-container {{ background: var(--card-bg); border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow-x: auto; max-height: 75vh; }}
        table {{ width: 100%; border-collapse: collapse; text-align: right; white-space: nowrap; }}
        th, td {{ padding: 12px 15px; border-bottom: 1px solid var(--border); font-size: 13.5px; }}
        th {{ background-color: var(--primary); color: white; position: sticky; top: 0; z-index: 10; cursor: pointer; }}
        tr:hover {{ background-color: #f1f4f8; }}
        tr.called-row {{ background-color: #e8f8f5 !important; opacity: 0.65; }}
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 11.5px; font-weight: 700; }}
        .badge-green {{ background-color: #e8f8f5; color: var(--success); }}
        .badge-red {{ background-color: #fdebd0; color: var(--danger); }}
        a.phone-link, a.email-link {{ color: var(--accent); text-decoration: none; font-weight: 600; }}
        input.notes-input {{ width: 100%; min-width: 140px; border: 1px solid transparent; background: transparent; padding: 6px; font-size: 13.5px; border-radius: 4px; }}
        input.notes-input:focus {{ border-color: var(--accent); background: #fff; outline: none; }}
        .call-checkbox {{ width: 18px; height: 18px; cursor: pointer; accent-color: var(--success); }}
    </style>
</head>
<body>
<div class="container">
    <header><h1>📊 ניהול לידים צוותי - היתרי עובדים זרים 2026</h1></header>
    <div class="controls">
        <input type="text" id="searchInput" class="search-box" placeholder="חיפוש חופשי..." onkeyup="filterTable()">
        <button id="filterUncalledBtn" class="filter-btn" onclick="toggleUncalledFilter()">הצג רק כאלה שעוד לא התקשרתי</button>
    </div>
    <div class="table-container">
        <table id="leadsTable">
            <thead>
                <tr>
                    <th style="width: 50px; text-align: center;">התקשרתי 📞</th>
                    <th>סטטוס ליד</th>
                    <th>שם חברה</th>
                    <th>ח.פ. / עוסק</th>
                    <th>יתרת היתרים</th>
                    <th>טלפון לחיץ 📞</th>
                    <th>מייל ✉️</th>
                    <th>סטטוס ייצוג</th>
                    <th>הערות צוות 📝</th>
                </tr>
            </thead>
            <tbody id="tableBody"></tbody>
        </table>
    </div>
</div>
<script>
    const leadsData = {json.dumps(leads, ensure_ascii=False)};

    function renderTable() {{
        const tbody = document.getElementById("tableBody");
        tbody.innerHTML = "";
        
        if (leadsData.length === 0) {{
            localStorage.clear();
        }}

        leadsData.forEach((lead, index) => {{
            const id = index + 1;
            const isGreen = lead.type === "green";
            const badgeClass = isGreen ? "badge-green" : "badge-red";
            const badgeText = isGreen ? "🟢 ליד חם (ישיר)" : "🔴 מיוצג / לא רלוונטי";
            const phoneDisplay = lead.phone ? `<a href="tel:${{lead.phone}}" class="phone-link">${{lead.phone}}</a>` : `<a href="tel:" class="phone-link">הוסף טלפון</a>`;

            const tr = document.createElement("tr");
            tr.setAttribute("data-id", id);
            tr.innerHTML = `
                <td style="text-align: center;"><input type="checkbox" class="call-checkbox" onchange="updateRowStatus(this)"></td>
                <td><span class="badge ${{badgeClass}}">${{badgeText}}</span></td>
                <td>${{lead.name}}</td>
                <td>${{lead.hp}}</td>
                <td>${{lead.quota}}</td>
                <td>${{phoneDisplay}}</td>
                <td><a href="mailto:${{lead.email}}" class="email-link">${{lead.email}}</a></td>
                <td>${{lead.source}}</td>
                <td><input type="text" class="notes-input" placeholder="הקלד הערה..." oninput="saveNote(this)"></td>
            `;
            tbody.appendChild(tr);
        }});
        loadSavedState();
    }}

    let showOnlyUncalled = false;
    function loadSavedState() {{
        document.querySelectorAll("#leadsTable tbody tr").forEach(row => {{
            let id = row.getAttribute("data-id");
            let isChecked = localStorage.getItem("call_" + id) === "true";
            let cb = row.querySelector(".call-checkbox");
            if (cb) cb.checked = isChecked;
            if (isChecked) row.classList.add("called-row");
            let note = localStorage.getItem("note_" + id);
            if (note) row.querySelector(".notes-input").value = note;
        }});
    }}

    function updateRowStatus(cb) {{
        let row = cb.closest("tr");
        let id = row.getAttribute("data-id");
        localStorage.setItem("call_" + id, cb.checked);
        if (cb.checked) row.classList.add("called-row");
        else row.classList.remove("called-row");
        applyFilters();
    }}

    function saveNote(input) {{
        localStorage.setItem("note_" + input.closest("tr").getAttribute("data-id"), input.value);
    }}

    function toggleUncalledFilter() {{
        showOnlyUncalled = !showOnlyUncalled;
        let btn = document.getElementById("filterUncalledBtn");
        btn.classList.toggle("active", showOnlyUncalled);
        btn.innerText = showOnlyUncalled ? "מציג רק כאלה שעוד לא התקשרתי" : "הצג רק כאלה שעוד לא התקשרתי";
        applyFilters();
    }}

    function filterTable() {{ applyFilters(); }}

    function applyFilters() {{
        let filter = document.getElementById("searchInput").value.toLowerCase();
        document.querySelectorAll("#leadsTable tbody tr").forEach(row => {{
            let text = row.innerText + " " + row.querySelector(".notes-input").value;
            let isChecked = row.querySelector(".call-checkbox").checked;
            let matches = text.toLowerCase().includes(filter) && (!showOnlyUncalled || !isChecked);
            row.style.display = matches ? "" : "none";
        }});
    }}

    window.onload = () => renderTable();
</script>
</body>
</html>
    """
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_content)

def push_to_github(repo_path="."):
    """מעלה את index.html ל-GitHub Pages"""
    try:
        repo = git.Repo(repo_path)
        repo.index.add(["index.html"])
        repo.index.commit("Update leads dashboard")
        repo.remote(name='origin').push()
        print("🌐 ה-HTML עודכן בהצלחה ב-GitHub Pages!")
    except Exception as e:
        print(f"שגיאה בעדכון ה-Git: {e}")

if __name__ == "__main__":
    json_path = "leads_update.json"
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            leads_data = json.load(f)
            
        # 1. עדכון קובץ ה-HTML ב-GitHub Pages
        generate_html_file(leads_data, "index.html")
        push_to_github()

        # 2. גיבוי קובץ ה-JSON ב-Google Drive
        update_drive_file(json_path)
    else:
        print(f"שגיאה: הקובץ '{json_path}' לא נמצא.")