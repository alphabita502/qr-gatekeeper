from flask import Flask, request, render_template_string, redirect, url_for, make_response
import time

app = Flask(__name__)

# ================= CONFIGURATION =================
# 1. ONE PASSWORD FOR EVERYTHING
MASTER_PASSWORD = "baps@1234"

# 2. SIMPLIFIED LINK LIST (Just ID and URL)
LINKS = {
    "AP_PC": "https://drive.google.com/file/d/1vVE08gtDkODkG0RbbdOsRzR45SKh44vd/view?usp=drive_link",
    "AP_AD": "https://drive.google.com/file/d/1YKAEgqRvXAFQINOOlngtKhD6fQXGRlhs/view?usp=drive_link",
    "BKT_PC": "https://drive.google.com/file/d/12F56UX_8atdZP6tV-sIYMs_Vh60d9u7q/view?usp=drive_link",
    "GNSYM_PC": "https://drive.google.com/file/d/1BtAsAlCELOH3WCJaV5pPyEr6XTbq2COb/view?usp=drive_link",
    "HRKSN_PC": "https://drive.google.com/file/d/1zApsjwI2MKMOzt90qCY7Pyft445f00yi/view?usp=drive_link",
    "PRMVT_PC": "https://drive.google.com/file/d/1n2X0HDzCOLQZbIgUPu0pHtc85aQ6lIo3/view?usp=drive_link",
    "SHJ_PC": "https://drive.google.com/file/d/1AlYVlKS5YWhNPzvUA-VPSGOpUQiiGH6c/view?usp=drive_link",
    "SHJ_AD": "https://drive.google.com/file/d/19W9UydwbGz_1vDT7ax2pU44Q19CcQBCq/view?usp=drive_link",
    "SUVSN_PC": "https://drive.google.com/file/d/1xOr8qfGX3wcdUpMTb7cxl_66BTH5LOOx/view?usp=drive_link",
    "SQ7_Refrence_Manual": "https://drive.google.com/file/d/1ipQWPTNu3aSJ5yR1BZvxu4H4qZg9E9TY/view?usp=drive_link",
    "N_Labs_XP48": "https://www.n-labs.co.in/database/media/pdf/Catlouge%202024.pdf",
    "PX10_PX3_Refrence_Manual": "https://usa.yamaha.com/files/download/other_assets/8/792728/px10_en_rm_f0.pdf",
    "NXAMP4x4_Data_Sheet": "https://www.nexo-sa.com/wp-content/uploads/NXAMP4x4mk2_datasheet_v1.3.pdf",
    "NXAMP4x2_Data_Sheet": "https://www.nexo-sa.com/wp-content/uploads/NXAMP4x2mk2_datasheet_v1.8.pdf",
    "MRX7D_Data_Sheet": "https://drive.google.com/file/d/1wF-nrEa7wsPJGsYypX-TriQDVwRLW9vs/view?usp=drive_link",
    "MA2120_Data_Sheet": "https://drive.google.com/file/d/1Od3_hdQS6uOzjT68FKW335BuTAh9hvIA/view?usp=drive_link",
}

LOGO_FILENAME = "logo.png"
BRAND_TEXT = "SNR.AUDIO"

# RATE LIMIT SETTINGS
MAX_RETRIES = 5
BAN_TIME_SECONDS = 300
# =================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Access</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; background: #2c3e50; color: white;}
        .card { background: #34495e; padding: 2rem; border-radius: 12px; box-shadow: 0 10px 20px rgba(0,0,0,0.3); text-align: center; max-width: 90%; width: 350px; }
        input { padding: 12px; width: 85%; margin: 15px 0; border: none; border-radius: 6px; }
        button { padding: 12px 25px; background: #27ae60; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; transition: 0.3s; }
        button:hover { background: #2ecc71; }
        .error { color: #e74c3c; margin-top: 15px; font-weight: bold; }
        .blocked { color: #f39c12; margin-bottom: 15px; font-weight: bold; border: 1px solid #f39c12; padding: 10px; border-radius: 5px; background: rgba(243, 156, 18, 0.1); }
        .logo { max-width: 150px; max-height: 100px; width: auto; height: auto; margin-bottom: 5px; border-radius: 4px; }
        .brand-name { color: #bdc3c7; font-size: 0.85rem; font-weight: 700; letter-spacing: 2px; margin-bottom: 25px; text-transform: uppercase; }
    </style>
</head>
<body>
    <div class="card">
        <img src="{{ url_for('static', filename=logo_file) }}" alt="Logo" class="logo">
        <div class="brand-name">{{ brand_text }}</div>
        <h2>🔒 Restricted Link</h2>
        
        {% if blocked %}
            <div class="blocked">⛔ Too many attempts.<br>Please wait 5 minutes.</div>
        {% else %}
            <form method="POST" action="/?id={{ link_id }}">
                <input type="password" name="password" placeholder="Enter Access Code" required autofocus>
                <button type="submit">Unlock</button>
            </form>
        {% endif %}
        
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def gatekeeper():
    link_id = request.args.get('id')
    if not link_id or link_id not in LINKS:
        return "❌ Error: Invalid or missing Link ID."

    # Get the destination URL directly from the simple dictionary
    destination_url = LINKS[link_id]
    
    # Cookie Logic
    cookie_name = f"failures_{link_id}"
    try:
        failures = int(request.cookies.get(cookie_name, 0))
    except:
        failures = 0

    render_args = {
        'link_id': link_id, 
        'logo_file': LOGO_FILENAME, 
        'brand_text': BRAND_TEXT,
        'blocked': False
    }

    if failures >= MAX_RETRIES:
        render_args['blocked'] = True
        return render_template_string(HTML_TEMPLATE, **render_args)

    if request.method == 'POST':
        user_input = request.form.get('password')

        # === CHANGED: CHECK AGAINST MASTER PASSWORD ===
        if user_input == MASTER_PASSWORD:
            resp = make_response(redirect(destination_url))
            resp.set_cookie(cookie_name, '0', max_age=0)
            return resp
        else:
            failures += 1
            render_args['error'] = f"❌ Incorrect. {MAX_RETRIES - failures} attempts left."
            
            if failures >= MAX_RETRIES:
                render_args['blocked'] = True
                render_args['error'] = None
            
            resp = make_response(render_template_string(HTML_TEMPLATE, **render_args))
            resp.set_cookie(cookie_name, str(failures), max_age=BAN_TIME_SECONDS)
            return resp

    return render_template_string(HTML_TEMPLATE, **render_args)
