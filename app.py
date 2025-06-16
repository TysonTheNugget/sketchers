import os
from flask import Flask, render_template

app = Flask(__name__)

# ─── CONFIG ─────────────────────────────────────────────────────
IMAGE_SIZE   = (790, 875)
STATIC_PATH  = 'static'
LAYER_ORDER  = ['background', 'bodies', 'eyes', 'mouth', 'shirts', 'hairs', 'toys']
# ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    # Build a dict: layer name → list of filenames in static/<layer>/
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
        layer_files=layer_files,
        img_width=IMAGE_SIZE[0],
        img_height=IMAGE_SIZE[1]
    )

if __name__ == '__main__':
    app.run(debug=True)
