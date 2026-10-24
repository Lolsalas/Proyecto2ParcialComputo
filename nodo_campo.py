import socket
import threading
import json
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--id", required=True, help="El ID de este nodo (ej. nodo_1)")
parser.add_argument("--config", default="config_nodo.json", help="Ruta al archivo JSON")
args = parser.parse_args()

with open(args.config, 'r') as archivo:
    configuracion = json.load(archivo)

mis_datos = configuracion["nodos"][args.id]
IP_NODO = mis_datos["ip"]
PUERTO_NODO = mis_datos["puerto"]

lista_vecinos = []
for nombre_nodo, datos in configuracion["nodos"].items():
    if nombre_nodo != args.id: 
        lista_vecinos.append(datos)


conexiones_activas = []
mensajes_procesados = set()

def manejar_conexion(conexion, direccion):
    print(f"Nueva conexión establecida desde {direccion}")
    
    buffer = ""
    
    while True:
        try:
            data = conexion.recv(2048)
            if not data:
                break 
            
            buffer += data.decode('utf-8')
            
            while '\n' in buffer:
                linea, buffer = buffer.split('\n', 1)
                linea = linea.strip()
                
                if not linea:
                    continue
                
                mensaje_json = json.loads(linea)
                id_msg = mensaje_json.get("id_mensaje")
                
                if id_msg in mensajes_procesados:
                    continue 
            
                mensajes_procesados.add(id_msg)
                print(f"Propagando mensaje: {id_msg} | Operación: {mensaje_json.get('codigo_contenido')}")
                
                mensaje_a_enviar = linea + '\n'
                hacer_broadcast(mensaje_a_enviar.encode('utf-8'), remitente_socket=conexion)
            
        except ConnectionResetError:
            break
            
    print(f"Conexión cerrada con {direccion}")
    if conexion in conexiones_activas:
        conexiones_activas.remove(conexion)
    conexion.close()

def hacer_broadcast(datos_en_bytes, remitente_socket):

    for conn in conexiones_activas:
        if conn != remitente_socket:
            try:
                conn.send(datos_en_bytes)
            except Exception as e:

                pass


servidor_nodo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor_nodo.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

def conectar_con_vecino(ip_vecino, puerto_vecino):
    while True:
        try:
            socket_vecino = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_vecino.connect((ip_vecino, puerto_vecino))
            
            print(f"Enlace de malla establecido hacia el nodo en {ip_vecino}:{puerto_vecino}")
            
            conexiones_activas.append(socket_vecino)
            
            hilo = threading.Thread(target=manejar_conexion, args=(socket_vecino, (ip_vecino, puerto_vecino)))
            hilo.start()
            
            break 
            
        except ConnectionRefusedError:
            time.sleep(2)


for vecino in lista_vecinos:
    hilo_vecino = threading.Thread(target=conectar_con_vecino, args=(vecino["ip"], vecino["puerto"]))
    hilo_vecino.start()

servidor_nodo.bind((IP_NODO, PUERTO_NODO))
servidor_nodo.listen()

print(f"Nodo operando en {IP_NODO}:{PUERTO_NODO} y esperando conexiones...")

while True:
    conexion_entrante, direccion = servidor_nodo.accept()
    conexiones_activas.append(conexion_entrante) 
    
    hilo = threading.Thread(target=manejar_conexion, args=(conexion_entrante, direccion))
    hilo.start()