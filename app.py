import os
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

# ─── CONFIG ─────────────────────────────────────────────────────
IMAGE_SIZE  = (790, 875)
STATIC_PATH = 'static'
LAYER_ORDER = ['background', 'bodies', 'eyes', 'mouth', 'shirts', 'hairs', 'toys']
# ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    # gather PNGs per layer
    layer_files = {}
    for layer in LAYER_ORDER:
        folder = os.path.join(STATIC_PATH, layer)
        try:
            files = [f for f in os.listdir(folder) if f.lower().endswith('.png')]
        except FileNotFoundError:
            files = []
        layer_files[layer] = files

    return render_template(
        'index.html',
        layers=LAYER_ORDER,
        layer_files=layer_files
    )

# serve static files
@app.route('/static/<path:path>')
def static_proxy(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')