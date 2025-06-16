import os, random, base64, re
from flask import Flask, render_template, request, redirect, send_file, flash, session
from PIL import Image
from io import BytesIO
import requests

app = Flask(__name__)
app.secret_key = "secret-key"

# ─── CONFIG ─────────────────────────────────────────────────────
IMAGE_SIZE      = (790, 875)
ALLOWED_EXTENSIONS = {'png'}
STATIC_PATH     = 'static'
LAYER_ORDER = [
    'background',
    'bodies',
    'eyes',
    'mouth',
    'shirts',
    'hairs',
    'toys'
]
EDITABLE_LAYERS = {'bodies', 'eyes', 'mouth', 'hairs', 'shirts'}
# ─────────────────────────────────────────────────────────────────

# ─── JSONBin® INTEGRATION ───────────────────────────────────────
JSONBIN_BIN_ID    = "684fd2d68561e97a50250f37"
JSONBIN_API_KEY   = "$2a$10$yoewvl71P1ONRAxG15RUiu/RLCoqIHwP3bi9ig.kA3pWUyUtaTYci"
HIDE_PASSWORD     = "samsage"
MASTER_PASSWORD   = "UltraSecretMasterPwd!123"

JSONBIN_BASE_URL  = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
JSONBIN_HEADERS   = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_API_KEY
}

def fetch_hidden_traits():
    resp = requests.get(f"{JSONBIN_BASE_URL}/latest", headers=JSONBIN_HEADERS)
    resp.raise_for_status()
    return resp.json().get("record", {})

def save_hidden_traits(hidden_map):
    resp = requests.put(JSONBIN_BASE_URL, headers=JSONBIN_HEADERS, json=hidden_map)
    resp.raise_for_status()
# ─────────────────────────────────────────────────────────────────

def allowed_file(fn):
    return '.' in fn and fn.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def has_transparency(img):
    if img.mode != "RGBA":
        return False
    alpha = img.getchannel("A")
    return sum(1 for p in alpha.getdata() if p < 255) > 10

@app.route('/')
def index():
    return render_template('index.html', folders=LAYER_ORDER)

@app.route('/generate')
def generate():
    hidden = fetch_hidden_traits()
    base = Image.new('RGBA', IMAGE_SIZE)

    for layer in LAYER_ORDER:
        folder = os.path.join(STATIC_PATH, layer)
        all_opts = [f for f in os.listdir(folder) if f.lower().endswith('.png')]

        if not session.get('unlocked'):
            opts = [f for f in all_opts if not hidden.get(f"{layer}/{f}", False)]
        else:
            opts = all_opts

        if not opts:
            continue

        img = Image.open(os.path.join(folder, random.choice(opts))).convert('RGBA')
        base.alpha_composite(img)

    buf = BytesIO()
    base.convert('RGB').save(buf, 'PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash("No file part.")
        return redirect('/')
    file = request.files['file']
    folder = request.form.get('folder')
    if not file or file.filename == '':
        flash("No file selected.")
        return redirect('/')
    if folder not in LAYER_ORDER:
        flash("Invalid folder.")
        return redirect('/')
    if not allowed_file(file.filename):
        flash("Only PNG allowed.")
        return redirect('/')

    try:
        img = Image.open(file).convert("RGBA")
    except:
        flash("Cannot open image.")
        return redirect('/')

    if folder in EDITABLE_LAYERS:
        if not has_transparency(img):
            flash("Must have at least 10 transparent pixels.")
            return redirect('/')
        img.save(os.path.join(STATIC_PATH, 'temp_upload.png'))
        return render_template('edit.html', folder=folder)

    if folder == 'toys':
        if not has_transparency(img):
            flash("Must have ≥10 transparent pixels to upload here.")
            return redirect('/')

    img = img.resize(IMAGE_SIZE)
    dst = os.path.join(STATIC_PATH, folder)
    os.makedirs(dst, exist_ok=True)
    names = [f for f in os.listdir(dst) if f.lower().endswith('.png') and f.startswith(folder)]
    nums = [
        int(f.replace(folder,'').replace('.png',''))
        for f in names
        if f.replace(folder,'').replace('.png','').isdigit()
    ]
    nxt = max(nums) + 1 if nums else 1
    out_fn = f"{folder}{nxt}.png"
    img.save(os.path.join(dst, out_fn))
    flash(f"Saved as {out_fn}")
    return redirect('/')

@app.route('/hide_trait', methods=['POST'])
def hide_trait():
    layer    = request.form.get('layer')
    filename = request.form.get('filename')
    pwd      = request.form.get('password', "")

    if pwd != HIDE_PASSWORD:
        flash("Wrong hide password.")
        return redirect('/')

    hidden = fetch_hidden_traits()
    hidden[f"{layer}/{filename}"] = True
    save_hidden_traits(hidden)
    flash(f"Hid {layer}/{filename}")
    return redirect('/')

@app.route('/unlock', methods=['GET','POST'])
def unlock():
    if request.method == 'POST':
        if request.form.get('master_password') == MASTER_PASSWORD:
            session['unlocked'] = True
            flash("Unlocked hidden traits!")
            return redirect('/')
        else:
            flash("Bad master password.")
            return redirect('/unlock')
    return render_template('unlock.html')

if __name__ == '__main__':
    app.run(debug=True)
