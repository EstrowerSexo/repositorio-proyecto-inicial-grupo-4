import os

# Archivos a "desinfectar"
files_to_clean = [
    os.path.join('myapp', 'urls.py'),
    os.path.join('myapp', 'views.py')
]

# El carácter "basura" invisible (espacio de no ruptura)
BAD_CHAR = '\u00A0'
# El espacio normal
GOOD_CHAR = ' '

print("--- Iniciando script de limpieza de archivos ---")
found_problems = False

for file_path in files_to_clean:
    if not os.path.exists(file_path):
        print(f"ADVERTENCIA: No se encontró el archivo {file_path}. Saltando...")
        continue

    print(f"Analizando {file_path}...")
    
    try:
        # Leer el contenido del archivo
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Comprobar si el archivo está "contaminado"
        if BAD_CHAR in content:
            found_problems = True
            print(f"  ¡PROBLEMA ENCONTRADO! El archivo '{file_path}' está contaminado.")
            
            # Reemplazar la "basura" por espacios normales
            clean_content = content.replace(BAD_CHAR, GOOD_CHAR)
            
            # Sobrescribir el archivo con el contenido limpio
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(clean_content)
            
            print(f"  --- ¡Archivo '{file_path}' desinfectado con éxito! ---")
        else:
            print(f"  '{file_path}' ya estaba limpio. No se hicieron cambios.")

    except Exception as e:
        print(f"  ERROR: No se pudo leer o escribir en {file_path}. Detalle: {e}")

print("--- Limpieza completada ---")
if not found_problems:
    print("Todo parece estar limpio. Si el 404 persiste, el problema es otro.")