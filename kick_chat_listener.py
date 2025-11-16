from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re

class KickChatSelenium:
    def __init__(self, channel_name):
        self.channel_name = channel_name.lower()
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Configura Chrome con opciones para evitar detección"""
        chrome_options = Options()
        
        # Opciones para evitar detección
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # User-Agent real
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def extract_chat_messages(self):
        """Extrae mensajes del chat del DOM"""
        try:
            # Buscar elementos del chat
            chat_selectors = [
                "[data-chat-message]",
                ".chat-message",
                ".message",
                "[class*='message']",
                "[class*='chat']"
            ]
            
            for selector in chat_selectors:
                messages = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if messages:
                    for message in messages[-5:]:  # Últimos 5 mensajes
                        try:
                            text = message.text.strip()
                            if text and len(text) > 0:
                                print(f"💬 {text}")
                        except:
                            pass
                    break
                    
        except Exception as e:
            print(f"Error extrayendo mensajes: {e}")
    
    def start(self):
        """Inicia el listener del chat"""
        print(f"🎯 Abriendo canal: {self.channel_name}")
        
        try:
            # Navegar al canal
            url = f"https://kick.com/{self.channel_name}"
            self.driver.get(url)
            
            print("⏳ Esperando a que cargue la página...")
            time.sleep(10)
            
            # Aceptar cookies si es necesario
            try:
                cookie_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Aceptar')]")
                for button in cookie_buttons:
                    try:
                        button.click()
                        print("✅ Cookies aceptadas")
                        time.sleep(2)
                        break
                    except:
                        pass
            except:
                pass
            
            print("🔍 Buscando chat...")
            
            # Monitorizar el chat continuamente
            while True:
                self.extract_chat_messages()
                time.sleep(2)  # Revisar cada 2 segundos
                
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo...")
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    print("🎥 Kick Chat Listener - Selenium")
    print("=" * 50)
    
    channel = input("Ingresa el nombre del canal: ").strip()
    
    if not channel:
        print("❌ Debes ingresar un nombre de canal")
        exit(1)
    
    listener = KickChatSelenium(channel)
    listener.start()