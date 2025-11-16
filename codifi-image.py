import os
import sys
import requests
from PIL import Image
import zlib
import base64
import io

def image_to_ooo(image_path, output_dir):
    try:
        img = Image.open(image_path)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_byte_arr = img_byte_arr.getvalue()

        compressed_data = zlib.compress(img_byte_arr)
        encoded_data = base64.b64encode(compressed_data).decode('utf-8')

        original_name = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(output_dir, f"{original_name}.ooo")

        with open(output_path, 'w') as f:
            f.write(encoded_data)
        print(f"Image converted and saved to {output_path}")

    except Exception as e:
        print(f"Error processing {image_path}: {e}")

def download_and_convert_image(url, output_dir):
    try:
        print(f"Downloading image from: {url}")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        img = Image.open(io.BytesIO(response.content))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_byte_arr = img_byte_arr.getvalue()

        compressed_data = zlib.compress(img_byte_arr)
        encoded_data = base64.b64encode(compressed_data).decode('utf-8')

        filename = url.split('/')[-1].split('?')[0]
        original_name = os.path.splitext(filename)[0] if '.' in filename else 'downloaded_image'
        output_path = os.path.join(output_dir, f"{original_name}.ooo")

        with open(output_path, 'w') as f:
            f.write(encoded_data)
        
        print(f"Image downloaded and converted successfully to {output_path}")
        return output_path

    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
    except Exception as e:
        print(f"Error processing image: {e}")

def process_input(input_path):
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.join(script_dir, "src")
        if not os.path.exists(src_dir):
            os.makedirs(src_dir)

        # Check if input is a URL
        if input_path.startswith(('http://', 'https://')):
            download_and_convert_image(input_path, src_dir)
            return

        # Check if input is a file or directory
        if os.path.isfile(input_path):
            if input_path.lower().endswith((".webp", ".jpg", ".png", ".jpeg")):
                image_to_ooo(input_path, src_dir)
            else:
                print("Unsupported file format. Use: .webp, .jpg, .png, .jpeg")

        elif os.path.isdir(input_path):
            folder_name = os.path.basename(os.path.normpath(input_path))
            output_dir = os.path.join(src_dir, folder_name)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            supported_formats = (".webp", ".jpg", ".png", ".jpeg")
            converted_count = 0

            for filename in os.listdir(input_path):
                if filename.lower().endswith(supported_formats):
                    image_path = os.path.join(input_path, filename)
                    image_to_ooo(image_path, output_dir)
                    converted_count += 1

            print(f"Conversion completed. {converted_count} images converted to {output_dir}")

        else:
            print("Error: The provided path does not exist.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ooo_encoder.py <image_path|folder_path|image_url>")
        print("\nExamples:")
        print("  Single file: python ooo_encoder.py \"image.jpg\"")
        print("  Folder:      python ooo_encoder.py \"C:\\Photos\"")
        print("  URL:         python ooo_encoder.py \"https://example.com/image.jpg\"")
    else:
        input_path = sys.argv[1]
        process_input(input_path)