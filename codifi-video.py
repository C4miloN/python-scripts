import cv2
import base64
import requests
import os
from pathlib import Path
import numpy as np
import re
import subprocess
import json
from urllib.parse import urlparse
import time

class VideoEncoder:
    def __init__(self):
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    
    def clean_filename(self, filename):
        cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
        return cleaned[:100]
    
    def get_video_name(self, video_source):
        if video_source.startswith(('http://', 'https://')):
            if 'x.com' in video_source or 'twitter.com' in video_source:
                tweet_id = self.extract_tweet_id(video_source)
                return f"twitter_video_{tweet_id}"
            else:
                parsed_url = urlparse(video_source)
                filename = Path(parsed_url.path).stem
                return filename if filename else "downloaded_video"
        else:
            return Path(video_source).stem
    
    def extract_tweet_id(self, url):
        patterns = [
            r'status/(\d+)',
            r'twitter\.com/\w+/status/(\d+)',
            r'x\.com/\w+/status/(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return url.split('/')[-1].split('?')[0]
    
    def download_twitter_video_ydl(self, tweet_url, output_path):
        methods = [
            ['yt-dlp', '-f', 'best', '-o', output_path, tweet_url],
            ['yt-dlp', '-f', 'mp4', '-o', output_path, tweet_url],
            ['yt-dlp', '-f', 'bestvideo', '-o', output_path, tweet_url],
            ['yt-dlp', '-o', output_path, tweet_url],
        ]
        
        for i, cmd in enumerate(methods):
            try:
                print(f"Trying method {i+1}...")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    if os.path.exists(output_path):
                        return output_path
                    possible_files = [f for f in os.listdir('.') 
                                    if f.startswith('twitter_video') or 'twitter' in f.lower()]
                    if possible_files:
                        return possible_files[0]
                
                print(f"Method {i+1} failed: {result.stderr[:100]}...")
                
            except subprocess.TimeoutExpired:
                print(f"Method {i+1} timeout")
            except Exception as e:
                print(f"Method {i+1} error: {e}")
        
        raise Exception("All yt-dlp methods failed")
    
    def download_twitter_video_alternative(self, tweet_url, output_path):
        try:
            print("Trying alternative method...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            session = requests.Session()
            session.headers.update(headers)
            
            response = session.get(tweet_url, timeout=10)
            response.raise_for_status()
            
            content = response.text
            video_patterns = [
                r'https://[^"\']*\.mp4[^"\']*',
                r'video_url[^=]*=[^"\'"]*["\']([^"\']+)["\']',
            ]
            
            video_urls = []
            for pattern in video_patterns:
                matches = re.findall(pattern, content)
                video_urls.extend(matches)
            
            if not video_urls:
                json_pattern = r'{"url":"([^"]*\.mp4[^"]*)"}'
                json_matches = re.findall(json_pattern, content)
                video_urls.extend(json_matches)
            
            for video_url in video_urls[:3]:
                try:
                    print(f"Testing URL: {video_url[:80]}...")
                    video_response = session.get(video_url, stream=True, timeout=15)
                    
                    if video_response.status_code == 200:
                        with open(output_path, 'wb') as f:
                            for chunk in video_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        if os.path.getsize(output_path) > 1000:
                            print("Video downloaded with alternative method")
                            return output_path
                        else:
                            os.remove(output_path)
                            
                except Exception as e:
                    print(f"Error with alternative URL: {e}")
                    continue
            
            raise Exception("No videos found with alternative method")
            
        except Exception as e:
            raise Exception(f"Alternative method failed: {e}")
    
    def download_twitter_video(self, tweet_url, output_path):
        print("Twitter/X link detected...")
        
        strategies = [
            self.download_twitter_video_ydl,
            self.download_twitter_video_alternative
        ]
        
        for i, strategy in enumerate(strategies):
            try:
                print(f"Trying strategy {i+1}...")
                result = strategy(tweet_url, output_path)
                if result:
                    return result
            except Exception as e:
                print(f"Strategy {i+1} failed: {e}")
                continue
        
        raise Exception("All download strategies failed")
    
    def download_regular_video(self, url, output_path):
        print(f"Downloading video from: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, stream=True, timeout=30, headers=headers)
        response.raise_for_status()
        
        with open(output_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print("Download completed")
        return output_path
    
    def download_video(self, url, local_path):
        if url.startswith(('http://', 'https://')):
            if 'x.com' in url or 'twitter.com' in url:
                return self.download_twitter_video(url, local_path)
            else:
                return self.download_regular_video(url, local_path)
        else:
            if not os.path.exists(url):
                raise FileNotFoundError(f"Video not found: {url}")
            return url

    def extract_frames(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frames_data = []
        frame_count = 0
        
        print(f"Video properties: {total_frames} frames, {fps:.2f} FPS")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            frames_data.append({
                'frame_number': frame_count,
                'data': frame_base64,
                'resolution': f"{frame.shape[1]}x{frame.shape[0]}"
            })
            
            frame_count += 1
            if frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"Processing: {frame_count}/{total_frames} frames ({progress:.1f}%)")
        
        cap.release()
        print(f"Frames extracted: {frame_count}")
        return frames_data, frame_count, fps

    def save_encoded_data(self, frames_data, output_path, original_fps):
        video_data = {
            'metadata': {
                'total_frames': len(frames_data),
                'resolution': frames_data[0]['resolution'] if frames_data else '0x0',
                'fps': original_fps,
                'format': 'ooo_encoded_v1.0'
            },
            'frames': frames_data
        }
        
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(video_data, file, indent=2)
        
        print(f"Encoded data saved to: {output_path}")

    def encode_video(self, video_source):
        try:
            original_name = self.get_video_name(video_source)
            print(f"Processing: {original_name}")
            
            src_dir = os.path.join(os.path.dirname(__file__), 'src')
            os.makedirs(src_dir, exist_ok=True)
            
            temp_video_path = os.path.join(src_dir, 'temp_video.mp4')
            video_path = self.download_video(video_source, temp_video_path)
            
            print("Extracting frames...")
            frames_data, total_frames, fps = self.extract_frames(video_path)
            
            if total_frames == 0:
                raise ValueError("No frames could be extracted")
            
            output_file = os.path.join(src_dir, f'{original_name}.ooo')
            self.save_encoded_data(frames_data, output_file, fps)
            
            if video_source.startswith(('http://', 'https://')) and os.path.exists(temp_video_path):
                os.remove(temp_video_path)
                print("Temporary file cleaned")
            
            file_size = os.path.getsize(output_file) / (1024 * 1024)
            print(f"Encoding completed!")
            print(f"Statistics:")
            print(f"   - File: {original_name}.ooo")
            print(f"   - Size: {file_size:.2f} MB")
            print(f"   - Frames: {total_frames}")
            print(f"   - Original FPS: {fps:.2f}")
            
            return output_file
            
        except Exception as e:
            print(f"Encoding error: {e}")
            temp_path = os.path.join(os.path.dirname(__file__), 'src', 'temp_video.mp4')
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return None

def select_video_source():
    print("\nINPUT OPTIONS:")
    print("1. Enter URL (Twitter/X or regular)")
    print("2. Enter local file path")
    
    choice = input("\nSelect option (1-2, Enter for 1): ").strip()
    
    if choice == "2":
        print("\nEnter local file path:")
        file_path = input().strip()
        file_path = os.path.expanduser(file_path)
        
        if not os.path.exists(file_path):
            print("File does not exist")
            return None
        
        supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in supported_formats:
            print(f"Unsupported format: {file_ext}")
            print(f"Supported formats: {', '.join(supported_formats)}")
            return None
        
        return file_path
    else:
        print("\nEnter video URL (Twitter/X or direct link):")
        url = input().strip()
        
        if not url.startswith(('http://', 'https://')):
            print("Invalid URL format")
            return None
        
        return url

def main():
    encoder = VideoEncoder()
    
    print("=== VIDEO ENCODER ===")
    
    video_source = select_video_source()
    
    if not video_source:
        print("No valid input provided")
        return
    
    if not video_source.startswith(('http://', 'https://')) and not os.path.exists(video_source):
        print(f"File does not exist: {video_source}")
        return
    
    encoder.encode_video(video_source)

if __name__ == "__main__":
    main()