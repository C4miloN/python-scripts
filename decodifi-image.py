import os
import sys
from PIL import Image, ImageEnhance, ImageFilter
import zlib
import base64
import io

def enhance_image(img):
    """Mejora la imagen aplicando diferentes filtros y ajustes"""
    try:
        # Mejorar nitidez
        img = img.filter(ImageFilter.SHARPEN)
        
        # Mejorar contraste
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        # Mejorar brillo
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        
        # Mejorar saturación
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.15)
        
        # Reducir ruido
        img = img.filter(ImageFilter.SMOOTH)
        
        return img
    except Exception as e:
        print(f"Warning: Could not enhance image: {e}")
        return img

def ooo_to_image(input_path, output_dir, enhance=False):
    try:
        with open(input_path, 'r') as f:
            encoded_data = f.read()

        decoded_data = base64.b64decode(encoded_data)
        decompressed_data = zlib.decompress(decoded_data)

        img = Image.open(io.BytesIO(decompressed_data))
        
        # Mejorar la imagen si se solicita
        if enhance:
            print("Enhancing image quality...")
            img = enhance_image(img)

        original_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(output_dir, f"{original_name}.png")

        img.save(output_path, format="PNG")
        print(f"File converted and saved to {output_path}")

    except Exception as e:
        print(f"Error processing {input_path}: {e}")

def process_ooo_files(input_path, enhance=False):
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.join(script_dir, "src")
        if not os.path.exists(src_dir):
            os.makedirs(src_dir)

        if os.path.isfile(input_path):
            if input_path.lower().endswith(".ooo"):
                ooo_to_image(input_path, src_dir, enhance)
            else:
                print("Unsupported file format. Use: .ooo")

        elif os.path.isdir(input_path):
            folder_name = os.path.basename(os.path.normpath(input_path))
            output_dir = os.path.join(src_dir, folder_name)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            converted_count = 0

            for filename in os.listdir(input_path):
                if filename.lower().endswith(".ooo"):
                    ooo_path = os.path.join(input_path, filename)
                    ooo_to_image(ooo_path, output_dir, enhance)
                    converted_count += 1

            print(f"Conversion completed. {converted_count} files converted to {output_dir}")

        else:
            print("Error: The provided path does not exist.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ooo_decoder.py <ooo_file_or_folder> [--enhance]")
        print("\nExamples:")
        print("  Single file:          python ooo_decoder.py \"image.ooo\"")
        print("  Single file enhanced: python ooo_decoder.py \"image.ooo\" --enhance")
        print("  Folder:               python ooo_decoder.py \"C:\\EncodedImages\"")
        print("  Folder enhanced:      python ooo_decoder.py \"C:\\EncodedImages\" --enhance")
    else:
        input_path = sys.argv[1]
        enhance = "--enhance" in sys.argv
        process_ooo_files(input_path, enhance)