import os
from PIL import Image

STATIC_PATH = 'static'
ORIG_SIZE   = (725, 875)
NEW_SIZE    = (790, 875)
SHIFT_RIGHT = 30  # uniform rightward shift for all non-background layers

# find all layer folders under static/
LAYER_DIRS = [
    d for d in os.listdir(STATIC_PATH)
    if os.path.isdir(os.path.join(STATIC_PATH, d))
]

for layer in LAYER_DIRS:
    folder = os.path.join(STATIC_PATH, layer)
    print(f"Processing layer: {layer}")
    for fn in os.listdir(folder):
        if not fn.lower().endswith('.png'):
            continue

        path = os.path.join(folder, fn)
        img  = Image.open(path).convert('RGBA')

        if layer == 'background':
            # stretch backgrounds to exactly NEW_SIZE
            out = img.resize(NEW_SIZE, Image.LANCZOS)

        else:
            # base center-X and bottom-align Y
            base_x = (NEW_SIZE[0] - ORIG_SIZE[0]) // 2
            base_y = NEW_SIZE[1] - ORIG_SIZE[1]

            # apply the uniform right-shift
            offset_x = base_x + SHIFT_RIGHT
            offset_y = base_y

            # compose onto a transparent canvas
            canvas = Image.new('RGBA', NEW_SIZE, (0, 0, 0, 0))
            canvas.paste(img, (offset_x, offset_y), img)
            out = canvas

        # overwrite the original file
        out.save(path)

    print(f" → done with {layer}\n")
