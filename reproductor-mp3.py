import os
import sys
import warnings
import pygame
import time
import glob
import random
import threading
import msvcrt  # Para Windows

# Suprimir advertencias de pygame y pkg_resources
warnings.filterwarnings("ignore", category=UserWarning, module="pkgdata")
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

class ReproductorMP3:
    def __init__(self, carpeta):
        self.carpeta = carpeta
        self.archivos_mp3 = []
        self.indice_actual = 0
        self.reproduciendo = False
        self.pausado = False
        self.volumen = 0.5  # Volumen inicial 50%
        self.modo_aleatorio = True  # Modo aleatorio por defecto
        self.canciones_reproducidas = []
        
        # Inicializar pygame sin mensajes
        pygame.mixer.init()
        pygame.mixer.music.set_volume(self.volumen)
        self.cargar_archivos()
        
        # Seleccionar canción aleatoria al iniciar
        if self.archivos_mp3:
            self.cancion_aleatoria()
    
    def cargar_archivos(self):
        """Carga todos los archivos MP3 de la carpeta"""
        patron = os.path.join(self.carpeta, "*.mp3")
        self.archivos_mp3 = glob.glob(patron)
        
        if not self.archivos_mp3:
            print("No se encontraron archivos MP3 en la carpeta.")
            return False
        
        print(f"Se cargaron {len(self.archivos_mp3)} canciones")
        return True
    
    def mostrar_cancion_actual(self):
        """Muestra solo la canción actual en reproducción"""
        if self.archivos_mp3:
            cancion_actual = os.path.basename(self.archivos_mp3[self.indice_actual])
            estado = "▶ Reproduciendo" if self.reproduciendo and not self.pausado else "⏸ Pausada"
            print(f"\n{'='*50}")
            print(f"{estado}: {cancion_actual}")
            print(f"Volumen: {int(self.volumen * 100)}% | Modo: {'Aleatorio' if self.modo_aleatorio else 'Normal'}")
            print(f"{'='*50}")
    
    def reproducir_actual(self):
        """Reproduce el archivo actual"""
        if not self.archivos_mp3:
            return False
        
        archivo = self.archivos_mp3[self.indice_actual]
        
        try:
            pygame.mixer.music.load(archivo)
            pygame.mixer.music.play()
            self.reproduciendo = True
            self.pausado = False
            
            # Agregar a canciones reproducidas si estamos en modo aleatorio
            if self.modo_aleatorio and self.indice_actual not in self.canciones_reproducidas:
                self.canciones_reproducidas.append(self.indice_actual)
            
            self.mostrar_cancion_actual()
            return True
            
        except pygame.error as e:
            print(f"Error al reproducir el archivo: {e}")
            return False
    
    def siguiente_cancion(self):
        """Pasa a la siguiente canción según el modo"""
        if not self.archivos_mp3:
            return
        
        if self.modo_aleatorio:
            self.cancion_aleatoria()
        else:
            self.indice_actual = (self.indice_actual + 1) % len(self.archivos_mp3)
        
        self.reproducir_actual()
    
    def cancion_anterior(self):
        """Regresa a la canción anterior"""
        if not self.archivos_mp3:
            return
        
        if self.modo_aleatorio:
            # En modo aleatorio, vamos a la canción anterior reproducida
            if len(self.canciones_reproducidas) > 1:
                self.canciones_reproducidas.pop()  # Remover la actual
                self.indice_actual = self.canciones_reproducidas[-1] if self.canciones_reproducidas else 0
        else:
            self.indice_actual = (self.indice_actual - 1) % len(self.archivos_mp3)
        
        self.reproducir_actual()
    
    def cancion_aleatoria(self):
        """Selecciona una canción aleatoria no reproducida"""
        if not self.archivos_mp3:
            return
        
        # Si ya se reprodujeron todas, reiniciar la lista
        if len(self.canciones_reproducidas) >= len(self.archivos_mp3):
            print("\n🔄 Todas las canciones reproducidas, reiniciando lista...")
            self.canciones_reproducidas = []
        
        # Buscar canciones no reproducidas
        canciones_no_reproducidas = [i for i in range(len(self.archivos_mp3)) 
                                   if i not in self.canciones_reproducidas]
        
        if canciones_no_reproducidas:
            self.indice_actual = random.choice(canciones_no_reproducidas)
        else:
            # Fallback: cualquier canción aleatoria
            self.indice_actual = random.randint(0, len(self.archivos_mp3) - 1)
    
    def toggle_pausa(self):
        """Pausa o reanuda la reproducción"""
        if not self.reproduciendo:
            return
        
        if self.pausado:
            pygame.mixer.music.unpause()
            self.pausado = False
            print("▶ Reproducción reanudada")
            self.mostrar_cancion_actual()
        else:
            pygame.mixer.music.pause()
            self.pausado = True
            print("⏸ Reproducción pausada")
    
    def subir_volumen(self):
        """Sube el volumen en 10%"""
        self.volumen = min(1.0, self.volumen + 0.1)
        pygame.mixer.music.set_volume(self.volumen)
        print(f"🔊 Volumen: {int(self.volumen * 100)}%")
    
    def bajar_volumen(self):
        """Baja el volumen en 10%"""
        self.volumen = max(0.0, self.volumen - 0.1)
        pygame.mixer.music.set_volume(self.volumen)
        print(f"🔈 Volumen: {int(self.volumen * 100)}%")
    
    def toggle_modo_aleatorio(self):
        """Cambia entre modo normal y aleatorio"""
        self.modo_aleatorio = not self.modo_aleatorio
        if self.modo_aleatorio:
            print("🔀 Modo aleatorio activado")
        else:
            print("➡️ Modo normal activado")
    
    def detener(self):
        """Detiene la reproducción"""
        pygame.mixer.music.stop()
        self.reproduciendo = False
        self.pausado = False
        print("⏹ Reproducción detenida")

def monitorear_reproduccion(reproductor):
    """Hilo para monitorear cuando termina una canción"""
    while True:
        if (reproductor.reproduciendo and 
            not pygame.mixer.music.get_busy() and 
            not reproductor.pausado):
            # La canción terminó, pasar automáticamente a la siguiente
            print("\n🔄 Canción terminada, pasando a la siguiente...")
            reproductor.siguiente_cancion()
        time.sleep(0.5)

def mostrar_banner():
    """Muestra el banner personalizado"""
    print("\n" + "="*60)
    print(" "*20 + "🎵 ECLIPSE 🎵")
    print(" "*15 + "Reproductor de Música MP3")
    print("="*60)

def mostrar_controles():
    """Muestra los controles disponibles"""
    print("\n🎵 CONTROLES:")
    print("[P] Play/Reproducir")
    print("[Space] Pausar/Reanudar")
    print("[N] Siguiente canción")
    print("[B] Canción anterior") 
    print("[+] Subir volumen")
    print("[-] Bajar volumen")
    print("[R] Modo aleatorio/Normal")
    print("[S] Detener")
    print("[Q] Salir")
    print("-" * 30)

def main():
    """Función principal"""
    # Limpiar pantalla
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Mostrar banner personalizado
    mostrar_banner()
    
    carpeta = "C:/Users/nunci/Music/Urbano"  # Cambia esta ruta si es necesario
    
    if not os.path.exists(carpeta):
        print(f"\nError: La carpeta '{carpeta}' no existe.")
        print("Por favor, crea una carpeta 'musica' con archivos MP3.")
        input("Presiona Enter para salir...")
        return
    
    reproductor = ReproductorMP3(carpeta)
    
    if not reproductor.archivos_mp3:
        input("Presiona Enter para salir...")
        return
    
    # Iniciar hilo para monitorear la reproducción
    hilo_monitor = threading.Thread(target=monitorear_reproduccion, args=(reproductor,), daemon=True)
    hilo_monitor.start()
    
    mostrar_controles()
    
    # Reproducir automáticamente al iniciar
    print("\n🎶 Iniciando reproducción automática...")
    reproductor.reproducir_actual()
    
    try:
        while True:
            if msvcrt.kbhit():  # Verifica si se presionó una tecla
                key = msvcrt.getch().decode('utf-8').lower()
                
                if key == 'q':
                    print("\n👋 Saliendo del reproductor ECLIPSE...")
                    reproductor.detener()
                    break
                    
                elif key == 'p':
                    if not reproductor.reproduciendo:
                        reproductor.reproducir_actual()
                    else:
                        print("Ya se está reproduciendo música")
                        
                elif key == ' ':
                    reproductor.toggle_pausa()
                    
                elif key == 'n':  # Siguiente canción
                    reproductor.siguiente_cancion()
                    
                elif key == 'b':  # Canción anterior
                    reproductor.cancion_anterior()
                    
                elif key == '+':  # Subir volumen
                    reproductor.subir_volumen()
                    
                elif key == '-':  # Bajar volumen
                    reproductor.bajar_volumen()
                    
                elif key == 'r':  # Modo aleatorio
                    reproductor.toggle_modo_aleatorio()
                    
                elif key == 's':  # Detener
                    reproductor.detener()
                
            time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\n\n👋 Saliendo del reproductor ECLIPSE...")
        reproductor.detener()
    except Exception as e:
        print(f"Error: {e}")
        reproductor.detener()
    finally:
        input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()