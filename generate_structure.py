import os
import argparse
from pathlib import Path

def generate_folder_structure(root_path, output_file="Structure.md", ignore_dirs=None, ignore_files=None):
    """
    Genera la estructura de carpetas en formato markdown
    
    Args:
        root_path (str): Ruta de la carpeta raíz
        output_file (str): Nombre del archivo de salida
        ignore_dirs (list): Lista de carpetas a ignorar
        ignore_files (list): Lista de archivos a ignorar
    """
    
    if ignore_dirs is None:
        ignore_dirs = ['.git', '__pycache__', '.vscode', '.idea', 'node_modules', 'venv']
    
    if ignore_files is None:
        ignore_files = ['.DS_Store', 'Thumbs.db']
    
    root_path = Path(root_path)
    
    if not root_path.exists():
        print(f"❌ Error: La ruta '{root_path}' no existe.")
        return
    
    if not root_path.is_dir():
        print(f"❌ Error: '{root_path}' no es una carpeta.")
        return
    
    structure_lines = ["### Project Structure\n", "```"]
    
    def build_tree(directory, prefix="", is_last=True):
        """Función recursiva para construir el árbol de directorios"""
        
        # Obtener todos los elementos del directorio
        try:
            items = sorted([item for item in directory.iterdir()])
        except PermissionError:
            return
        
        # Filtrar elementos a ignorar
        items = [item for item in items 
                if (item.is_dir() and item.name not in ignore_dirs) or 
                   (item.is_file() and item.name not in ignore_files)]
        
        # Determinar el prefijo para los elementos
        connector = "└── " if is_last else "├── "
        
        # Procesar cada elemento
        for index, item in enumerate(items):
            is_last_item = index == len(items) - 1
            new_prefix = prefix + ("    " if is_last else "│   ")
            
            if item.is_dir():
                # Es una carpeta
                structure_lines.append(f"{prefix}{connector}{item.name}/")
                build_tree(item, new_prefix, is_last_item)
            else:
                # Es un archivo
                structure_lines.append(f"{prefix}{connector}{item.name}")
    
    # Obtener el nombre de la carpeta raíz
    folder_name = root_path.name if root_path.name else root_path.parent.name
    structure_lines[1] += f"\n{folder_name}/"
    
    # Construir el árbol
    build_tree(root_path, "", True)
    
    structure_lines.append("```")
    
    # Escribir al archivo
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(structure_lines))
        print(f"✅ Archivo '{output_file}' generado exitosamente!")
        print(f"📁 Ruta del archivo: {Path(output_file).absolute()}")
    except Exception as e:
        print(f"❌ Error al escribir el archivo: {e}")

def main():
    """Función principal que solicita la ruta al usuario"""
    
    print("=" * 50)
    print("    GENERADOR DE ESTRUCTURA DE CARPETAS")
    print("=" * 50)
    print()
    
    while True:
        folder_path = input("📁 Ingresa la ruta de la carpeta local: ").strip()
        
        # Si la ruta está vacía, usar el directorio actual
        if not folder_path:
            folder_path = "."
        
        # Expandir ~ y variables de entorno
        folder_path = os.path.expanduser(folder_path)
        folder_path = os.path.expandvars(folder_path)
        
        if os.path.exists(folder_path):
            break
        else:
            print("❌ La ruta ingresada no existe. Intenta nuevamente.\n")
    
    # Preguntar por el nombre del archivo de salida
    output_name = input("📄 Nombre del archivo de salida [Structure.md]: ").strip()
    if not output_name:
        output_name = "Structure.md"
    elif not output_name.endswith('.md'):
        output_name += '.md'
    
    # Preguntar si quiere personalizar carpetas/archivos a ignorar
    print("\n¿Deseas personalizar las carpetas y archivos a ignorar?")
    print("(Enter para usar valores por defecto: .git, __pycache__, node_modules, etc.)")
    custom_ignore = input("Personalizar? (s/N): ").strip().lower()
    
    ignore_dirs = None
    ignore_files = None
    
    if custom_ignore == 's':
        print("\nIngresa las carpetas a ignorar (separadas por coma):")
        dirs_input = input("Carpetas: ").strip()
        if dirs_input:
            ignore_dirs = [d.strip() for d in dirs_input.split(',')]
        
        print("\nIngresa los archivos a ignorar (separados por coma):")
        files_input = input("Archivos: ").strip()
        if files_input:
            ignore_files = [f.strip() for f in files_input.split(',')]
    
    # Generar la estructura
    print(f"\n🔄 Generando estructura para: {folder_path}")
    generate_folder_structure(folder_path, output_name, ignore_dirs, ignore_files)

if __name__ == "__main__":
    main()