import cv2
import base64
import json
import os
import numpy as np
from pathlib import Path
import glob

class VideoEnhancer:
    def __init__(self):
        self.enhancement_presets = {
            'original': {'brightness': 0, 'contrast': 1.0, 'sharpness': 1.0, 'saturation': 1.0},
            'standard': {'brightness': 15, 'contrast': 1.3, 'sharpness': 1.8, 'saturation': 1.2},
            'vivid': {'brightness': 20, 'contrast': 1.5, 'sharpness': 2.2, 'saturation': 1.4},
            'cinematic': {'brightness': 10, 'contrast': 1.4, 'sharpness': 2.0, 'saturation': 1.1},
            'bright': {'brightness': 25, 'contrast': 1.2, 'sharpness': 1.5, 'saturation': 1.3},
            'crisp': {'brightness': 12, 'contrast': 1.6, 'sharpness': 2.5, 'saturation': 1.0},
            'custom': {'brightness': 15, 'contrast': 1.3, 'sharpness': 1.8, 'saturation': 1.2}
        }
    
    def adjust_brightness_contrast(self, frame, brightness=0, contrast=1.0):
        if brightness == 0 and contrast == 1.0:
            return frame
        frame = frame.astype(np.float32)
        frame = frame * contrast + brightness
        frame = np.clip(frame, 0, 255)
        return frame.astype(np.uint8)
    
    def adjust_saturation(self, frame, saturation=1.0):
        if saturation == 1.0:
            return frame
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = hsv[:, :, 1] * saturation
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    def enhance_sharpness(self, frame, strength=1.5):
        if strength == 1.0:
            return frame
        kernel = np.array([[-1, -1, -1],
                          [-1, 9.5 * strength, -1],
                          [-1, -1, -1]])
        kernel = kernel / np.sum(np.abs(kernel))
        return cv2.filter2D(frame, -1, kernel)
    
    def reduce_noise(self, frame):
        return cv2.bilateralFilter(frame, 11, 75, 75)
    
    def auto_white_balance(self, frame):
        try:
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            avg_a = np.mean(lab[:, :, 1])
            avg_b = np.mean(lab[:, :, 2])
            lab[:, :, 1] = lab[:, :, 1] - ((avg_a - 128) * (lab[:, :, 0] / 255.0) * 1.2)
            lab[:, :, 2] = lab[:, :, 2] - ((avg_b - 128) * (lab[:, :, 0] / 255.0) * 1.2)
            lab[:, :, 1] = np.clip(lab[:, :, 1], 0, 255)
            lab[:, :, 2] = np.clip(lab[:, :, 2], 0, 255)
            return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
        except:
            return frame
    
    def enhance_contrast_adaptive(self, frame):
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    def enhance_frame(self, frame, preset='original'):
        if preset not in self.enhancement_presets:
            preset = 'original'
        
        config = self.enhancement_presets[preset]
        
        if preset == 'original':
            return frame
        
        try:
            enhanced = frame.copy()
            enhanced = self.auto_white_balance(enhanced)
            enhanced = self.enhance_contrast_adaptive(enhanced)
            enhanced = self.adjust_brightness_contrast(
                enhanced, 
                brightness=config['brightness'], 
                contrast=config['contrast']
            )
            enhanced = self.adjust_saturation(enhanced, saturation=config['saturation'])
            enhanced = self.enhance_sharpness(enhanced, strength=config['sharpness'])
            enhanced = self.reduce_noise(enhanced)
            return enhanced
            
        except Exception as e:
            print(f"Frame enhancement error: {e}")
            return frame

class VideoDecoder:
    def __init__(self):
        self.enhancer = VideoEnhancer()
    
    def find_ooo_files(self):
        src_dir = os.path.join(os.path.dirname(__file__), 'src')
        if not os.path.exists(src_dir):
            return []
        ooo_files = glob.glob(os.path.join(src_dir, "*.ooo"))
        return sorted(ooo_files)
    
    def validate_ooo_file(self, file_path):
        try:
            if not os.path.exists(file_path):
                return False, "File does not exist"
            if not file_path.lower().endswith('.ooo'):
                return False, "File must have .ooo extension"
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            if 'metadata' not in data or 'frames' not in data:
                return False, "Invalid .ooo file structure"
            return True, "Valid file"
        except json.JSONDecodeError:
            return False, "File is not valid JSON"
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def load_encoded_data(self, input_path):
        try:
            with open(input_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            if 'metadata' not in data or 'frames' not in data:
                raise ValueError("Invalid .ooo file structure")
            print(f"✅ .ooo file loaded successfully")
            return data
        except Exception as e:
            raise Exception(f"Error loading .ooo file: {e}")
    
    def get_video_name_from_ooo(self, ooo_path):
        filename = Path(ooo_path).stem
        return filename
    
    def get_output_filename(self, original_name, preset, output_format='mp4', output_dir=None):
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), 'src')
        os.makedirs(output_dir, exist_ok=True)
        
        if preset == 'original':
            base_name = os.path.join(output_dir, f'{original_name}_decoded')
        else:
            base_name = os.path.join(output_dir, f'{original_name}_{preset}')
        
        counter = 1
        output_file = f'{base_name}.{output_format}'
        
        while os.path.exists(output_file):
            output_file = f'{base_name}_{counter:02d}.{output_format}'
            counter += 1
        
        return output_file
    
    def decode_and_enhance(self, input_path, output_path, preset='original'):
        try:
            print("Loading encoded data...")
            encoded_data = self.load_encoded_data(input_path)
            frames_data = encoded_data['frames']
            total_frames = len(frames_data)
            metadata = encoded_data['metadata']
            
            original_fps = metadata.get('fps', 30)
            original_resolution = metadata.get('resolution', 'Unknown')
            
            print(f"Original video properties:")
            print(f"   - Frames: {total_frames}")
            print(f"   - FPS: {original_fps}")
            print(f"   - Resolution: {original_resolution}")
            
            if preset == 'original':
                print("Mode: ORIGINAL (no enhancements)")
            else:
                print(f"Applying enhancements with preset: {preset}")
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = None
            start_time = cv2.getTickCount()
            processed_frames = 0
            
            for i, frame_info in enumerate(frames_data):
                try:
                    frame_base64 = frame_info['data']
                    frame_data = base64.b64decode(frame_base64)
                    frame_array = np.frombuffer(frame_data, np.uint8)
                    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                    
                    if frame is None:
                        print(f"Skipping frame {i} due to decode error")
                        continue
                    
                    if preset == 'original':
                        enhanced_frame = frame
                    else:
                        enhanced_frame = self.enhancer.enhance_frame(frame, preset)
                    
                    if out is None:
                        height, width = enhanced_frame.shape[:2]
                        out = cv2.VideoWriter(output_path, fourcc, original_fps, (width, height))
                        print(f"Video configured: {width}x{height}, FPS: {original_fps}")
                    
                    out.write(enhanced_frame)
                    processed_frames += 1
                    
                    if (i + 1) % 30 == 0 or (i + 1) == total_frames:
                        elapsed_time = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
                        frames_per_second = (i + 1) / elapsed_time if elapsed_time > 0 else 0
                        progress_percent = ((i + 1) / total_frames) * 100
                        remaining_frames = total_frames - (i + 1)
                        eta_seconds = remaining_frames / frames_per_second if frames_per_second > 0 else 0
                        
                        print(f"Progress: {i + 1}/{total_frames} ({progress_percent:.1f}%) | "
                              f"Speed: {frames_per_second:.1f} FPS | "
                              f"ETA: {eta_seconds:.1f}s")
                        
                except Exception as e:
                    print(f"Error processing frame {i}: {e}")
                    continue
            
            if out:
                out.release()
            
            total_time = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
            
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024 * 1024)
                print(f"\n✅ Decoding completed!")
                print(f"Final statistics:")
                print(f"   - Total time: {total_time:.1f} seconds")
                print(f"   - Processed frames: {processed_frames}/{total_frames}")
                print(f"   - File size: {file_size:.2f} MB")
                print(f"   - Average speed: {total_frames/total_time:.1f} FPS")
                print(f"File saved to: {output_path}")
                return True
            else:
                print("Error: Output file was not created")
                return False
            
        except Exception as e:
            print(f"Decoding error: {e}")
            return False

def select_file_interactively():
    decoder = VideoDecoder()
    
    print("\nINPUT OPTIONS:")
    print("1. Auto-search in 'src' folder")
    print("2. Enter manual .ooo file path")
    print("3. Search in another folder")
    
    choice = input("\nSelect option (1-3, Enter for 1): ").strip()
    
    if choice == "2":
        print("\nEnter full path to .ooo file:")
        file_path = input().strip()
        file_path = os.path.expanduser(file_path)
        is_valid, message = decoder.validate_ooo_file(file_path)
        if is_valid:
            return file_path
        else:
            print(f"❌ {message}")
            return None
            
    elif choice == "3":
        print("\nEnter folder path to search:")
        folder_path = input().strip()
        folder_path = os.path.expanduser(folder_path)
        
        if not os.path.exists(folder_path):
            print("Folder does not exist")
            return None
        
        ooo_files = glob.glob(os.path.join(folder_path, "*.ooo"))
        if not ooo_files:
            print("No .ooo files found in specified folder")
            return None
        
        print("\nFound .ooo files:")
        for i, ooo_file in enumerate(ooo_files, 1):
            filename = Path(ooo_file).name
            file_size = os.path.getsize(ooo_file) / (1024 * 1024)
            print(f"   {i}. {filename} ({file_size:.1f} MB)")
        
        print(f"\nSelect file (1-{len(ooo_files)}):")
        try:
            file_choice = int(input().strip()) - 1
            if 0 <= file_choice < len(ooo_files):
                return ooo_files[file_choice]
            else:
                print("Invalid selection")
                return None
        except:
            print("Selection error")
            return None
    
    else:
        ooo_files = decoder.find_ooo_files()
        if not ooo_files:
            print("No .ooo files found in 'src' folder")
            return None
        
        print("\n.ooo files in 'src' folder:")
        for i, ooo_file in enumerate(ooo_files, 1):
            filename = Path(ooo_file).name
            file_size = os.path.getsize(ooo_file) / (1024 * 1024)
            print(f"   {i}. {filename} ({file_size:.1f} MB)")
        
        print(f"\nSelect file (1-{len(ooo_files)}, Enter for first):")
        try:
            choice_input = input().strip()
            if choice_input:
                choice = int(choice_input) - 1
                if 0 <= choice < len(ooo_files):
                    return ooo_files[choice]
                else:
                    return ooo_files[0]
            else:
                return ooo_files[0]
        except:
            return ooo_files[0]

def main():
    decoder = VideoDecoder()
    
    print("=== VIDEO DECODER ===")
    
    selected_file = select_file_interactively()
    
    if not selected_file:
        print("No valid file selected")
        return
    
    print(f"Selected file: {Path(selected_file).name}")
    
    presets = list(decoder.enhancer.enhancement_presets.keys())
    
    print("\nAvailable processing presets:")
    for i, preset in enumerate(presets, 1):
        config = decoder.enhancer.enhancement_presets[preset]
        if preset == 'original':
            print(f"   {i}. {preset.upper()} - No enhancements, original quality")
        else:
            print(f"   {i}. {preset.upper()} - Brightness: {config['brightness']}, "
                  f"Contrast: {config['contrast']:.1f}, "
                  f"Sharpness: {config['sharpness']:.1f}")
    
    print("\nSelect preset (number) or press Enter for 'original':")
    try:
        preset_choice = input().strip()
        if preset_choice:
            choice_idx = int(preset_choice) - 1
            selected_preset = presets[choice_idx] if 0 <= choice_idx < len(presets) else 'original'
        else:
            selected_preset = 'original'
    except:
        selected_preset = 'original'
        print("Using 'original' preset")
    
    print("\nWhere to save decoded video?")
    print("1. 'src' folder (default)")
    print("2. Other folder")
    
    output_choice = input("Select option (1-2, Enter for 1): ").strip()
    
    if output_choice == "2":
        print("Enter output folder path:")
        output_dir = input().strip()
        output_dir = os.path.expanduser(output_dir)
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = os.path.join(os.path.dirname(__file__), 'src')
    
    original_name = decoder.get_video_name_from_ooo(selected_file)
    output_file = decoder.get_output_filename(original_name, selected_preset, output_dir=output_dir)
    
    print(f"\nDecoding configuration:")
    print(f"   - File: {Path(selected_file).name}")
    print(f"   - Preset: {selected_preset.upper()}")
    print(f"   - Output: {output_file}")
    
    print("\nStart decoding? (y/n):")
    final_confirm = input().strip().lower()
    
    if final_confirm != 'y':
        print("Decoding cancelled")
        return
    
    print("\n" + "="*50)
    success = decoder.decode_and_enhance(selected_file, output_file, selected_preset)
    
    if success:
        print(f"\n✅ PROCESS COMPLETED SUCCESSFULLY!")
        print(f"Video saved to:")
        print(f"   {output_file}")
        
        print("\nOpen containing folder? (y/n):")
        open_folder = input().strip().lower()
        if open_folder == 'y':
            folder_path = os.path.dirname(output_file)
            try:
                os.startfile(folder_path)
            except:
                print("Could not open folder automatically")
    else:
        print("\n❌ Error in decoding process")

if __name__ == "__main__":
    main()