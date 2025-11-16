import os
import subprocess
import sys
from pathlib import Path
import re

def check_and_update_dependencies():
    """Verifica y actualiza las dependencias necesarias"""
    print("🔍 Verificando dependencias...")
    
    dependencies = ["spotdl"]
    
    for package in dependencies:
        try:
            # Intentar importar para verificar si está instalado
            if package == "spotdl":
                subprocess.run([sys.executable, "-m", "spotdl", "--version"], 
                             check=True, capture_output=True)
            print(f"✓ {package} está instalado")
            
            # Preguntar si quiere actualizar
            response = input(f"¿Actualizar {package}? (s/N): ").lower().strip()
            if response in ['s', 'si', 'y', 'yes']:
                print(f"🔄 Actualizando {package}...")
                subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", package], 
                             check=True, capture_output=True)
                print(f"✅ {package} actualizado correctamente")
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"📦 Instalando {package}...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", package], 
                             check=True, capture_output=True)
                print(f"✅ {package} instalado correctamente")
            except subprocess.CalledProcessError:
                print(f"❌ Error instalando {package}")
                return False
    return True

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
    """Get playlist URL, destination folder, and song range from user"""
    print("=" * 60)
    print("SPOTIFY PLAYLIST DOWNLOADER")
    print("=" * 60)
    
    # Get playlist URL
    playlist_url = input("Enter Spotify playlist URL: ").strip()
    
    # Basic URL validation
    if not playlist_url.startswith("https://open.spotify.com/playlist/"):
        print("✗ Invalid Spotify URL. Must be a playlist.")
        return None, None, None, None
    
    # Get destination folder
    default_folder = "C:\\Spotify"
    folder_input = input(f"Enter destination folder (Enter for '{default_folder}'): ").strip()
    
    if folder_input:
        download_folder = folder_input
    else:
        download_folder = default_folder
    
    # Get song range
    print("\n🎵 Rango de canciones a descargar:")
    print("   - Dejar ambos campos vacíos para descargar toda la playlist")
    print("   - Ingresa números específicos para descargar un rango")
    
    start_input = input("   Desde la canción número: ").strip()
    end_input = input("   Hasta la canción número: ").strip()
    
    start_track = int(start_input) if start_input.isdigit() else None
    end_track = int(end_input) if end_input.isdigit() else None
    
    # Validate range
    if start_track is not None and end_track is not None:
        if start_track > end_track:
            print("✗ Error: El número inicial no puede ser mayor que el final")
            return None, None, None, None
        print(f"✓ Rango seleccionado: canciones {start_track} a {end_track}")
    elif start_track is not None or end_track is not None:
        print("✗ Error: Debes especificar ambos límites del rango o ninguno")
        return None, None, None, None
    else:
        print("✓ Descargando toda la playlist")
    
    # Create folder if it doesn't exist
    try:
        os.makedirs(download_folder, exist_ok=True)
        print(f"✓ Download folder: {download_folder}")
    except Exception as e:
        print(f"✗ Error creating folder: {e}")
        return None, None, None, None
    
    return playlist_url, download_folder, start_track, end_track

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

def download_playlist(playlist_url, download_folder, existing_songs, start_track=None, end_track=None):
    """Download playlist with track range support and detailed progress"""
    print(f"\nStarting download to: {download_folder}")
    
    if start_track is not None and end_track is not None:
        print(f"Downloading tracks: {start_track} to {end_track}")
    
    # Configure output template WITHOUT extension in the template
    output_template = os.path.join(download_folder, "{artist} - {title}")
    
    try:
        # Build command
        command = [
            sys.executable, "-m", "spotdl",
            playlist_url,
            "--output", output_template,
            "--format", "mp3"
        ]
        
        print(f"\nCommand: {' '.join(command)}")
        print("Downloading... (this may take several minutes)")
        print("-" * 80)
        
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
        
        # Track counters and state
        current_track = 0
        downloaded_count = 0
        skipped_count = 0
        in_range = start_track is None  # If no range specified, we're always in range
        
        # Process output line by line with detailed tracking
        for line in process.stdout:
            line = line.strip()
            
            # Track progress indicators
            if "Downloading" in line and "playlist" not in line:
                current_track += 1
                
                # Check if we're in the specified range
                if start_track is not None:
                    in_range = start_track <= current_track <= end_track
                
                if in_range:
                    status = "⬇️ DESCARGANDO"
                    # Extract song name if possible
                    song_info = extract_song_info(line)
                    print(f"{current_track:3d}. {song_info} - {status}")
                else:
                    status = "⏭️  SALTEADA (fuera de rango)"
                    print(f"{current_track:3d}. {status}")
                    
            elif "Skipping" in line and current_track > 0:
                if in_range:
                    skipped_count += 1
                    print(f"{current_track:3d}. ❌ SKIPPEADA (ya existe)")
                    
            elif "Downloaded" in line and current_track > 0:
                if in_range:
                    downloaded_count += 1
                    print(f"{current_track:3d}. ✅ DESCARGADA")
                    
            elif "error" in line.lower() and current_track > 0:
                if in_range:
                    print(f"{current_track:3d}. ❌ ERROR en descarga")
                    
            # Print other relevant lines
            elif any(keyword in line for keyword in ["Fetching", "Found", "Processing"]):
                if not any(skip in line for skip in ["Downloading", "Skipping", "Downloaded"]):
                    print(f"   ℹ️  {line}")
        
        process.wait()
        
        if process.returncode == 0:
            print("-" * 80)
            print(f"\n✅ Download completed successfully!")
            print(f"📊 Resumen:")
            print(f"   • Canciones descargadas: {downloaded_count}")
            print(f"   • Canciones skipheadas: {skipped_count}")
            print(f"   • Total procesadas: {current_track}")
            
            # Clean any files with double extensions
            clean_double_extensions(download_folder)
            
            # Show summary of new songs
            new_songs = get_new_downloaded_songs(download_folder, existing_songs)
            if new_songs:
                print(f"\n🎵 Nuevas canciones descargadas: {len(new_songs)}")
                for song in list(new_songs)[:10]:  # Show first 10
                    print(f"   • {song}")
                if len(new_songs) > 10:
                    print(f"   ... y {len(new_songs) - 10} más")
            else:
                print("✓ Todas las canciones ya estaban descargadas")
                
        else:
            print(f"\n❌ Download error. Code: {process.returncode}")
            
    except Exception as e:
        print(f"❌ Error during download: {e}")

def extract_song_info(line):
    """Extract song information from spotDL output line"""
    # Try to extract artist and title from different line formats
    if "Downloading" in line:
        # Remove "Downloading" prefix
        clean_line = line.replace("Downloading", "").strip()
        # Remove progress indicators if present
        clean_line = re.sub(r'\[\d+/\d+\]', '', clean_line).strip()
        return clean_line
    return "Canción"

def clean_double_extensions(download_folder):
    """Clean files with double extensions like '.mp3.mp3'"""
    audio_extensions = ['.mp3', '.m4a', '.flac', '.wav', '.ogg']
    
    try:
        cleaned_count = 0
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
                            cleaned_count += 1
                        else:
                            # If correct file already exists, remove the duplicate
                            os.remove(file_path)
                            cleaned_count += 1
                        break
        
        if cleaned_count > 0:
            print(f"✓ Archivos con doble extensión corregidos: {cleaned_count}")
                        
    except Exception as e:
        print(f"Note: Could not clean file extensions: {e}")

def get_new_downloaded_songs(download_folder, existing_songs_before):
    """Get songs that were newly downloaded"""
    existing_songs_after = get_existing_songs(download_folder)
    return existing_songs_after - existing_songs_before

def main():
    """Main function"""
    try:
        # Check and update dependencies
        if not check_and_update_dependencies():
            print("❌ No se pudieron instalar las dependencias necesarias")
            return
        
        # Get user input
        playlist_url, download_folder, start_track, end_track = get_user_input()
        if not playlist_url:
            return
        
        print(f"\n📋 Resumen:")
        print(f"   Playlist: {playlist_url}")
        print(f"   Carpeta destino: {download_folder}")
        if start_track is not None and end_track is not None:
            print(f"   Rango: canciones {start_track} a {end_track}")
        else:
            print(f"   Rango: toda la playlist")
        
        # Check existing songs
        existing_songs = get_existing_songs(download_folder)
        
        # Confirm download
        confirm = input("\n¿Continuar con la descarga? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes', 's', 'si']:
            print("Descarga cancelada.")
            return
        
        # Start download
        download_playlist(playlist_url, download_folder, existing_songs, start_track, end_track)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Descarga interrumpida por el usuario.")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()