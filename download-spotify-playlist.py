import os
import subprocess
import sys
from pathlib import Path
import re

def check_spotdl_installation():
    """Check if spotDL is installed, if not, install it"""
    try:
        subprocess.run([sys.executable, "-m", "spotdl", "--version"], 
                      check=True, capture_output=True)
        print("✓ spotDL is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing spotDL...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "spotdl"], 
                          check=True, capture_output=True)
            print("✓ spotDL installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Error installing spotDL")
            return False

def clean_filename(filename):
    """Clean filename by removing invalid characters and fixing double extensions"""
    # Remove invalid characters for Windows
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    
    # Fix double extensions (like .mp3.mp3)
    name, ext = os.path.splitext(filename)
    if ext in ['.mp3', '.m4a', '.flac', '.wav']:
        # If the name already ends with this extension, remove it
        if name.lower().endswith(ext.lower()):
            name = name[:-len(ext)]
    
    return f"{name}{ext}"

def get_user_input():
    """Get playlist URL and destination folder from user"""
    print("=" * 50)
    print("SPOTIFY PLAYLIST DOWNLOADER")
    print("=" * 50)
    
    # Get playlist URL
    playlist_url = input("Enter Spotify playlist URL: ").strip()
    
    # Basic URL validation
    if not playlist_url.startswith("https://open.spotify.com/playlist/"):
        print("✗ Invalid Spotify URL. Must be a playlist.")
        return None, None
    
    # Get destination folder
    default_folder = "C:\\Spotify"
    folder_input = input(f"Enter destination folder (Enter for '{default_folder}'): ").strip()
    
    if folder_input:
        download_folder = folder_input
    else:
        download_folder = default_folder
    
    # Create folder if it doesn't exist
    try:
        os.makedirs(download_folder, exist_ok=True)
        print(f"✓ Download folder: {download_folder}")
    except Exception as e:
        print(f"✗ Error creating folder: {e}")
        return None, None
    
    return playlist_url, download_folder

def get_existing_songs(download_folder):
    """Get list of already downloaded songs in the folder"""
    existing_songs = set()
    audio_extensions = {'.mp3', '.m4a', '.flac', '.wav', '.ogg'}
    
    try:
        for file in os.listdir(download_folder):
            file_lower = file.lower()
            if any(file_lower.endswith(ext) for ext in audio_extensions):
                # Remove extension and clean for comparison
                song_name = os.path.splitext(file)[0]
                # Remove possible double extensions
                song_name = clean_filename(song_name)
                existing_songs.add(song_name.lower())
        
        print(f"✓ Found {len(existing_songs)} existing songs in folder")
        return existing_songs
    except Exception as e:
        print(f"✗ Error reading folder: {e}")
        return set()

def download_playlist(playlist_url, download_folder, existing_songs):
    """Download playlist while checking for existing songs"""
    print(f"\nStarting download to: {download_folder}")
    print("Checking existing songs...")
    
    # Configure output template WITHOUT extension in the template
    # spotDL will add the extension automatically
    output_template = os.path.join(download_folder, "{artist} - {title}")
    
    try:
        # Execute spotDL with custom template
        command = [
            sys.executable, "-m", "spotdl",
            playlist_url,
            "--output", output_template,
            "--format", "mp3"
        ]
        
        print(f"\nCommand: {' '.join(command)}")
        print("Downloading... (this may take several minutes)")
        
        # Execute and capture output in real time
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace'
        )
        
        # Show progress
        for line in process.stdout:
            print(line.strip())
        
        process.wait()
        
        if process.returncode == 0:
            print("\n✓ Download completed successfully!")
            
            # Clean any files with double extensions
            clean_double_extensions(download_folder)
            
            # Show summary of new songs
            new_songs = get_new_downloaded_songs(download_folder, existing_songs)
            if new_songs:
                print(f"\nNew songs downloaded: {len(new_songs)}")
                for song in list(new_songs)[:10]:  # Show first 10
                    print(f"  • {song}")
                if len(new_songs) > 10:
                    print(f"  ... and {len(new_songs) - 10} more")
            else:
                print("✓ All songs were already downloaded")
                
        else:
            print(f"\n✗ Download error. Code: {process.returncode}")
            
    except Exception as e:
        print(f"✗ Error during download: {e}")

def clean_double_extensions(download_folder):
    """Clean files with double extensions like '.mp3.mp3'"""
    audio_extensions = ['.mp3', '.m4a', '.flac', '.wav', '.ogg']
    
    try:
        for file in os.listdir(download_folder):
            file_path = os.path.join(download_folder, file)
            
            if os.path.isfile(file_path):
                name, ext = os.path.splitext(file)
                
                # Check if the name ends with an audio extension
                for audio_ext in audio_extensions:
                    if name.lower().endswith(audio_ext.lower()):
                        # This file has double extension
                        correct_name = name  # Remove the duplicate extension
                        correct_path = os.path.join(download_folder, correct_name)
                        
                        # Rename file to remove double extension
                        if not os.path.exists(correct_path):
                            os.rename(file_path, correct_path)
                            print(f"✓ Fixed double extension: {file} -> {correct_name}")
                        else:
                            # If correct file already exists, remove the duplicate
                            os.remove(file_path)
                            print(f"✓ Removed duplicate: {file}")
                        break
                        
    except Exception as e:
        print(f"Note: Could not clean file extensions: {e}")

def get_new_downloaded_songs(download_folder, existing_songs_before):
    """Get songs that were newly downloaded"""
    existing_songs_after = get_existing_songs(download_folder)
    return existing_songs_after - existing_songs_before

def main():
    """Main function"""
    try:
        # Check installation
        if not check_spotdl_installation():
            return
        
        # Get user input
        playlist_url, download_folder = get_user_input()
        if not playlist_url:
            return
        
        print(f"\nPlaylist: {playlist_url}")
        print(f"Destination folder: {download_folder}")
        
        # Check existing songs
        existing_songs = get_existing_songs(download_folder)
        
        # Confirm download
        confirm = input("\nContinue with download? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes', 's', 'si']:
            print("Download cancelled.")
            return
        
        # Start download
        download_playlist(playlist_url, download_folder, existing_songs)
        
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user.")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")

if __name__ == "__main__":
    main()