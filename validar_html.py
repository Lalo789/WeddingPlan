"Script para generar HTML renderizado de todas las páginas para validación W3C"

from app import app
import os

PAGINAS = [
    ('/', 'index.html'),
    ('/servicios', 'servicios.html'),
    ('/login', 'login.html'),
    ('/registro', 'registro.html'),
]

def generar_html_estatico():
    "Genera archivos HTML estáticos para validación"
    
    output_dir = 'html_validacion'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with app.test_client() as client:
        for ruta, nombre_archivo in PAGINAS:
            print(f'Generando {nombre_archivo}...')
            
            response = client.get(ruta)
            
            if response.status_code == 200:
                filepath = os.path.join(output_dir, nombre_archivo)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(response.data.decode('utf-8'))
                print(f'✓ {nombre_archivo} guardado')
            else:
                print(f'✗ Error en {ruta}: {response.status_code}')
    
    print(f'\nArchivos guardados en carpeta: {output_dir}/')
    print('Sube estos archivos a https://validator.w3.org/ para validar')

if __name__ == '__main__':
    generar_html_estatico()