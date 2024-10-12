import subprocess

# Ruta de la imagen en Windows
image_path = r'C:\Users\Artur\Desktop\COMPILADORES ll\proyecto v2.0\syntax_tree.png'

# Abrir la imagen con la aplicación predeterminada en Windows
subprocess.run(['cmd', '/c', 'start', '', image_path], shell=True)
