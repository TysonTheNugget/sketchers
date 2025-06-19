"""
app.py — intuitive Tkinter randomizer with left preview, right trait panel,
and new collage editor with resizable background and draggable composites.

Dependencies:
    pip install pillow

Layout:
    app.py
    static/
        background/*.png
        accessories2/*.png
        bodies/*.png
        eyes/*.png
        mouth/*.png
        shirts/*.png
        hairs/*.png
        toys/*.png
        accessories/*.png
        health/*.png

Run:
    python app.py
"""
import os
import random
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

# Configuration
IMAGE_SIZE = (790, 875)  # Original size for output images
PREVIEW_SCALE = 0.4  # Smaller preview for compact UI
STATIC_PATH = os.path.join(os.getcwd(), "static")
LAYER_ORDER = [
    'background', 'accessories2', 'bodies', 'eyes', 'mouth',
    'shirts', 'hairs', 'toys', 'accessories', 'health'
]

class MyMilliosApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mymillios Randomizer & Collage Editor")
        self.root.geometry("900x600")  # Compact initial window size
        self.root.resizable(True, True)
        self.preview_size = (
            int(IMAGE_SIZE[0] * PREVIEW_SCALE),
            int(IMAGE_SIZE[1] * PREVIEW_SCALE)
        )
        self.layer_files = {}
        self.preview_cache = {}
        self.noise_enabled = {layer: tk.BooleanVar(value=True) for layer in LAYER_ORDER}
        self.noise_levels = {layer: tk.DoubleVar(value=0.4) for layer in LAYER_ORDER}  # Per-layer noise level
        self.manual_selection = []
        self.rename_map = {}
        self.bg_image = None
        self.bg_tk = None
        self.bg_scale = 1.0
        self.composites = []
        self.current_composite = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.load_images()
        self._build_ui()
        self.randomize()
        self.root.mainloop()

    def load_images(self):
        """Load or reload images from static folders."""
        self.layer_files.clear()
        self.preview_cache.clear()
        for layer in LAYER_ORDER:
            folder = os.path.join(STATIC_PATH, layer)
            self.layer_files[layer] = sorted(
                f for f in os.listdir(folder) if f.lower().endswith('.png')
            ) if os.path.isdir(folder) else []
            cache = []
            for fname in self.layer_files[layer]:
                full = Image.open(os.path.join(STATIC_PATH, layer, fname)).convert('RGBA')
                preview = full.resize(self.preview_size, Image.LANCZOS)
                cache.append((full, fname, preview))
            self.preview_cache[layer] = cache
        # Update OptionMenus if UI is built
        if hasattr(self, 'controls'):
            for layer, (var, ent, menu, _, _) in self.controls.items():
                menu['menu'].delete(0, tk.END)
                opts = [fname for _, fname, _ in self.preview_cache[layer]]
                for opt in opts:
                    menu['menu'].add_command(label=opt, command=tk._setit(var, opt))
                var.set('')

    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Randomizer Tab
        randomizer_tab = tk.Frame(self.notebook)
        self.notebook.add(randomizer_tab, text="Randomizer")

        # Main container
        container = tk.Frame(randomizer_tab)
        container.pack(fill='both', expand=True, padx=5, pady=5)

        # Left: Preview Canvas
        left = tk.Frame(container, relief='solid', borderwidth=1)
        left.pack(side='left', fill='y', padx=5, pady=5)
        self.canvas = tk.Canvas(
            left, width=self.preview_size[0], height=self.preview_size[1],
            highlightthickness=0, bg='white'
        )
        self.canvas.pack(padx=5, pady=5)
        self.canvas_image = self.canvas.create_image(0, 0, anchor='nw')

        # Right: Trait Panel and Buttons
        right = tk.Frame(container)
        right.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # Trait Canvas for scrolling
        trait_canvas = tk.Canvas(right, highlightthickness=0)
        vbar = ttk.Scrollbar(right, orient='vertical', command=trait_canvas.yview)
        vbar.pack(side='right', fill='y')
        trait_canvas.pack(side='left', fill='both', expand=True)
        trait_canvas.configure(yscrollcommand=vbar.set)
        controls_frame = tk.Frame(trait_canvas)
        trait_window = trait_canvas.create_window((0, 0), window=controls_frame, anchor='nw')

        def update_scroll_region(event=None):
            trait_canvas.configure(scrollregion=trait_canvas.bbox('all'))
        controls_frame.bind('<Configure>', update_scroll_region)

        def on_mouse_wheel(event):
            if event.delta != 0:
                trait_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        trait_canvas.bind_all("<MouseWheel>", on_mouse_wheel)

        self.controls = {}
        for idx, layer in enumerate(LAYER_ORDER):
            # Layer Label
            tk.Label(
                controls_frame, text=layer.capitalize(), font=('Arial', 9), width=10
            ).grid(row=idx, column=0, padx=2, pady=2, sticky='e')

            # OptionMenu
            var = tk.StringVar(value='')
            opts = [fname for _, fname, _ in self.preview_cache[layer]]
            menu = ttk.OptionMenu(controls_frame, var, None, *opts)
            menu.config(width=12)
            menu.grid(row=idx, column=1, padx=2, pady=2, sticky='w')

            # Rename Entry
            ent = tk.Entry(controls_frame, width=12, font=('Arial', 9))
            ent.grid(row=idx, column=2, padx=2, pady=2, sticky='w')

            # Noise Checkbox
            noise_cb = tk.Checkbutton(
                controls_frame, text="Noise", variable=self.noise_enabled[layer],
                font=('Arial', 9)
            )
            noise_cb.grid(row=idx, column=3, padx=2, pady=2, sticky='w')

            # Noise Slider
            tk.Scale(
                controls_frame, from_=0.0, to=0.5, resolution=0.01, orient='horizontal',
                variable=self.noise_levels[layer], length=100, width=10,
                font=('Arial', 8)
            ).grid(row=idx, column=4, padx=2, pady=2, sticky='w')

            # Set Button
            tk.Button(
                controls_frame, text="Set", font=('Arial', 9), width=4,
                command=lambda l=layer, v=var, e=ent: self.set_layer(l, v.get(), e.get())
            ).grid(row=idx, column=5, padx=2, pady=2, sticky='w')

            # Rename Button
            tk.Button(
                controls_frame, text="Ren", font=('Arial', 9), width=4,
                command=lambda l=layer, v=var, e=ent: self.rename_layer(l, v.get(), e.get())
            ).grid(row=idx, column=6, padx=2, pady=2, sticky='w')

            self.controls[layer] = (var, ent, menu, noise_cb, self.noise_levels[layer])

        # Bottom Buttons
        bottom = tk.Frame(randomizer_tab)
        bottom.pack(fill='x', pady=5)
        buttons = [
            ("Apply All", self.apply_all),
            ("Randomize", self.randomize),
            ("Download Image", self.download_image),
            ("Download Layers", self.download_all_layers),
            ("Copy to Collage", self.copy_to_collage),
            ("Refresh Images", self.load_images)
        ]
        for text, cmd in buttons:
            tk.Button(
                bottom, text=text, font=('Arial', 9), command=cmd
            ).pack(side='left', padx=5)

        # Collage Tab
        collage_tab = tk.Frame(self.notebook)
        self.notebook.add(collage_tab, text="Collage Editor")

        collage_container = tk.Frame(collage_tab)
        collage_container.pack(fill='both', expand=True, padx=5, pady=5)

        # Collage Controls
        collage_controls = tk.Frame(collage_container, relief='raised', borderwidth=1)
        collage_controls.pack(side='left', fill='y', padx=5, pady=5)
        tk.Button(
            collage_controls, text="Load Background", font=('Arial', 9),
            command=self.load_background
        ).pack(fill='x', padx=5, pady=2)
        tk.Label(collage_controls, text="Background Scale:", font=('Arial', 9)).pack(anchor='w', padx=5, pady=2)
        self.bg_scale_var = tk.DoubleVar(value=1.0)
        tk.Scale(
            collage_controls, from_=0.1, to=2.0, resolution=0.1, orient='horizontal',
            variable=self.bg_scale_var, command=self.update_background, length=150
        ).pack(fill='x', padx=5, pady=2)
        tk.Label(collage_controls, text="Composite Scale:", font=('Arial', 9)).pack(anchor='w', padx=5, pady=2)
        self.comp_scale_var = tk.DoubleVar(value=1.0)
        tk.Scale(
            collage_controls, from_=0.1, to=2.0, resolution=0.1, orient='horizontal',
            variable=self.comp_scale_var, command=self.update_composite_scale, length=150
        ).pack(fill='x', padx=5, pady=2)
        tk.Button(
            collage_controls, text="Save Collage", font=('Arial', 9),
            command=self.save_collage
        ).pack(fill='x', padx=5, pady=2)
        tk.Button(
            collage_controls, text="Clear Composites", font=('Arial', 9),
            command=self.clear_composites
        ).pack(fill='x', padx=5, pady=2)

        # Collage Canvas
        collage_right = tk.Frame(collage_container, relief='sunken', borderwidth=1)
        collage_right.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        self.collage_canvas = tk.Canvas(collage_right, highlightthickness=0, bg='gray')
        self.collage_canvas.pack(fill='both', expand=True, padx=5, pady=5)
        self.bg_image_id = None
        self.collage_canvas.bind("<Button-1>", self.place_composite)
        self.collage_canvas.bind("<B1-Motion>", self.drag_composite)
        self.collage_canvas.bind("<ButtonRelease-1>", self.stop_drag)
        self.collage_canvas.bind("<Button-3>", self.select_composite)

    def load_background(self):
        path = filedialog.askopenfilename(
            title="Select Background Image",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if not path:
            return
        self.bg_image = Image.open(path).convert('RGBA')
        self.bg_scale = 1.0
        self.bg_scale_var.set(1.0)
        self.update_background()
        messagebox.showinfo("Loaded", f"Background loaded: {os.path.basename(path)}")

    def update_background(self, *args):
        if not self.bg_image:
            return
        self.bg_scale = self.bg_scale_var.get()
        new_size = (int(self.bg_image.width * self.bg_scale), int(self.bg_image.height * self.bg_scale))
        scaled_bg = self.bg_image.resize(new_size, Image.LANCZOS)
        self.bg_tk = ImageTk.PhotoImage(scaled_bg)
        if self.bg_image_id:
            self.collage_canvas.delete(self.bg_image_id)
        self.bg_image_id = self.collage_canvas.create_image(0, 0, image=self.bg_tk, anchor='nw')
        for _, _, _, _, canvas_id, _ in self.composites:
            self.collage_canvas.tag_raise(canvas_id, self.bg_image_id)
        self.collage_canvas.config(scrollregion=(0, 0, new_size[0], new_size[1]))

    def copy_to_collage(self):
        if not self.bg_image:
            messagebox.showwarning("Warning", "Load a background image first.")
            return
        comp = Image.new('RGBA', IMAGE_SIZE, (0, 0, 0, 0))
        for layer, img, fname in self.current:
            if layer not in ['background', 'health']:
                im = img.copy()
                if self.noise_enabled[layer].get():
                    im = self.add_noise(im, self.noise_levels[layer].get())
                comp.paste(im, (0, 0), im)
        canvas_w = self.collage_canvas.winfo_width()
        canvas_h = self.collage_canvas.winfo_height()
        x = canvas_w // 2
        y = canvas_h // 2
        scale = 1.0
        tk_img = ImageTk.PhotoImage(comp)
        canvas_id = self.collage_canvas.create_image(x, y, image=tk_img, anchor='center')
        self.composites.append((comp, x, y, scale, canvas_id, tk_img))
        self.current_composite = len(self.composites) - 1
        self.comp_scale_var.set(1.0)
        self.update_composite_scale()

    def place_composite(self, event):
        if not self.composites:
            return
        x, y = self.collage_canvas.canvasx(event.x), self.collage_canvas.canvasy(event.y)
        items = self.collage_canvas.find_overlapping(x, y, x, y)
        for idx, (_, _, _, _, canvas_id, _) in enumerate(self.composites):
            if canvas_id in items:
                self.current_composite = idx
                self.comp_scale_var.set(self.composites[idx][3])
                self.drag_data["item"] = canvas_id
                self.drag_data["x"] = x
                self.drag_data["y"] = y
                break

    def drag_composite(self, event):
        if not self.drag_data["item"]:
            return
        x, y = self.collage_canvas.canvasx(event.x), self.collage_canvas.canvasy(event.y)
        dx = x - self.drag_data["x"]
        dy = y - self.drag_data["y"]
        self.collage_canvas.move(self.drag_data["item"], dx, dy)
        idx = self.current_composite
        comp, old_x, old_y, scale, canvas_id, tk_img = self.composites[idx]
        self.composites[idx] = (comp, old_x + dx, old_y + dy, scale, canvas_id, tk_img)
        self.drag_data["x"] = x
        self.drag_data["y"] = y

    def stop_drag(self, event):
        self.drag_data["item"] = None

    def select_composite(self, event):
        x, y = self.collage_canvas.canvasx(event.x), self.collage_canvas.canvasy(event.y)
        items = self.collage_canvas.find_overlapping(x, y, x, y)
        for idx, (_, _, _, _, canvas_id, _) in enumerate(self.composites):
            if canvas_id in items:
                self.current_composite = idx
                self.comp_scale_var.set(self.composites[idx][3])
                break

    def update_composite_scale(self, *args):
        if self.current_composite is None or not self.composites:
            return
        scale = self.comp_scale_var.get()
        idx = self.current_composite
        comp, x, y, _, canvas_id, _ = self.composites[idx]
        new_size = (int(comp.width * scale), int(comp.height * scale))
        scaled_img = comp.resize(new_size, Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(scaled_img)
        self.collage_canvas.itemconfig(canvas_id, image=tk_img)
        self.composites[idx] = (comp, x, y, scale, canvas_id, tk_img)

    def save_collage(self):
        if not self.bg_image:
            messagebox.showwarning("Warning", "No background image loaded.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension='.png', filetypes=[('PNG', '*.png')]
        )
        if not path:
            return
        bg_size = (int(self.bg_image.width * self.bg_scale), int(self.bg_image.height * self.bg_scale))
        collage = self.bg_image.resize(bg_size, Image.LANCZOS).convert('RGBA')
        for comp, x, y, scale, _, _ in self.composites:
            comp_size = (int(comp.width * scale), int(comp.height * scale))
            scaled_comp = comp.resize(comp_size, Image.LANCZOS)
            paste_x = int(x - comp_size[0] / 2)
            paste_y = int(y - comp_size[1] / 2)
            collage.paste(scaled_comp, (paste_x, paste_y), scaled_comp)
        collage.save(path)
        messagebox.showinfo("Saved", f"Collage saved: {path}")

    def clear_composites(self):
        for _, _, _, _, canvas_id, _ in self.composites:
            self.collage_canvas.delete(canvas_id)
        self.composites = []
        self.current_composite = None
        self.comp_scale_var.set(1.0)

    def _rename_file(self, layer, old_name, new_name):
        if not old_name or not new_name:
            return False
        new_name = new_name if new_name.lower().endswith('.png') else new_name + '.png'
        old_path = os.path.join(STATIC_PATH, layer, old_name)
        new_path = os.path.join(STATIC_PATH, layer, new_name)
        if os.path.exists(new_path):
            messagebox.showerror("Error", f"File '{new_name}' already exists in {layer} folder.")
            return False
        try:
            os.rename(old_path, new_path)
            idx = self.layer_files[layer].index(old_name)
            self.layer_files[layer][idx] = new_name
            self.layer_files[layer].sort()
            for i, (full, fname, prev) in enumerate(self.preview_cache[layer]):
                if fname == old_name:
                    self.preview_cache[layer][i] = (full, new_name, prev)
                    break
            for i, (l, full, fname, prev) in enumerate(self.manual_selection):
                if l == layer and fname == old_name:
                    self.manual_selection[i] = (layer, full, new_name, prev)
                    break
            self.rename_map[(layer, old_name)] = new_name
            return True
        except OSError as e:
            messagebox.showerror("Error", f"Failed to rename file: {e}")
            return False

    def set_layer(self, layer, fname, new_name):
        if not fname:
            return
        for full, f, prev in self.preview_cache[layer]:
            if f == fname:
                # Remove existing selection for this layer
                self.manual_selection = [(l, img, n, p) for l, img, n, p in self.manual_selection if l != layer]
                self.manual_selection.append((layer, full, fname, prev))
                break
        if new_name.strip():
            if self._rename_file(layer, fname, new_name):
                var, _, menu, _, _ = self.controls[layer]
                menu['menu'].delete(0, tk.END)
                opts = [f for _, f, _ in self.preview_cache[layer]]
                for opt in opts:
                    menu['menu'].add_command(label=opt, command=tk._setit(var, opt))
                var.set(self.rename_map.get((layer, fname), fname))
        self.randomize()

    def rename_layer(self, layer, fname, new_name):
        if not fname or not new_name.strip():
            return
        if self._rename_file(layer, fname, new_name):
            var, _, menu, _, _ = self.controls[layer]
            menu['menu'].delete(0, tk.END)
            opts = [f for _, f, _ in self.preview_cache[layer]]
            for opt in opts:
                menu['menu'].add_command(label=opt, command=tk._setit(var, opt))
            new_fname = new_name if new_name.lower().endswith('.png') else new_name + '.png'
            var.set(new_fname)
        self.randomize()

    def apply_all(self):
        for layer, (var, ent, _, _, _) in self.controls.items():
            fname = var.get()
            new_name = ent.get().strip()
            if fname:
                for full, f, prev in self.preview_cache[layer]:
                    if f == fname:
                        self.manual_selection = [(l, img, n, p) for l, img, n, p in self.manual_selection if l != layer]
                        self.manual_selection.append((layer, full, fname, prev))
                        break
            if new_name:
                if self._rename_file(layer, fname, new_name):
                    var, _, menu, _, _ = self.controls[layer]
                    menu['menu'].delete(0, tk.END)
                    opts = [f for _, f, _ in self.preview_cache[layer]]
                    for opt in opts:
                        menu['menu'].add_command(label=opt, command=tk._setit(var, opt))
                    new_fname = new_name if new_name.lower().endswith('.png') else new_name + '.png'
                    var.set(new_fname)
        self.randomize()

    def add_noise(self, img, level):
        px = img.load()
        for x in range(img.width):
            for y in range(img.height):
                r, g, b, a = px[x, y]
                noise = int((random.random() - 0.5) * level * 255)
                px[x, y] = (
                    max(0, min(255, r + noise)),
                    max(0, min(255, g + noise)),
                    max(0, min(255, b + noise)),
                    a
                )
        return img

    def randomize(self):
        comp = Image.new('RGBA', self.preview_size, (0, 0, 0, 0))
        self.current = []
        manual_layers = {layer for layer, _, _, _ in self.manual_selection}
        for layer in LAYER_ORDER:
            if layer in manual_layers:
                for l, full, fname, prev in self.manual_selection:
                    if l == layer:
                        img = prev.copy()
                        if self.noise_enabled[layer].get():
                            img = self.add_noise(img, self.noise_levels[layer].get())
                        comp.paste(img, (0, 0), img)
                        self.current.append((layer, full, fname))
                        break
            else:
                full, fname, prev = random.choice(self.preview_cache[layer])
                img = prev.copy()
                if self.noise_enabled[layer].get():
                    img = self.add_noise(img, self.noise_levels[layer].get())
                comp.paste(img, (0, 0), img)
                self.current.append((layer, full, fname))
        self.tkcomp = ImageTk.PhotoImage(comp)
        self.canvas.itemconfig(self.canvas_image, image=self.tkcomp)

    def download_image(self):
        path = filedialog.asksaveasfilename(
            defaultextension='.png', filetypes=[('PNG', '*.png')]
        )
        if not path:
            return
        full = Image.new('RGBA', IMAGE_SIZE, (0, 0, 0, 0))
        for layer, img, fname in self.current:
            im = img.copy()
            if self.noise_enabled[layer].get():
                im = self.add_noise(im, self.noise_levels[layer].get())
            full.paste(im, (0, 0), im)
        full.save(path)

    def download_all_layers(self):
        d = filedialog.askdirectory()
        if not d:
            return
        for layer, img, fname in self.current:
            save_name = self.rename_map.get((layer, fname), fname)
            im = img.copy()
            if self.noise_enabled[layer].get():
                im = self.add_noise(im, self.noise_levels[layer].get())
            im.save(os.path.join(d, save_name))

if __name__ == '__main__':
    app = MyMilliosApp()