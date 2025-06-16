from PIL import Image
import os

# Settings
target_size = (604, 729)
input_folder = '.'  # Current folder
output_folder = './converted_pngs'

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Loop through all .jpg files in the folder
for filename in os.listdir(input_folder):
    if filename.lower().endswith('.jpg'):
        jpg_path = os.path.join(input_folder, filename)
        
        with Image.open(jpg_path) as img:
            # Resize to 604x729
            resized_img = img.resize(target_size, Image.ANTIALIAS)
            
            # Convert to RGBA (for PNG support)
            png_img = resized_img.convert('RGBA')
            
            # Create new filename
            base_name = os.path.splitext(filename)[0]
            png_path = os.path.join(output_folder, f'{base_name}.png')
            
            # Save as PNG
            png_img.save(png_path)

print("✅ All JPGs converted to PNG (604x729) and saved in 'converted_pngs/' folder.")
