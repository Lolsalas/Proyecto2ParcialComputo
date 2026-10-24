import uuid
import json
import socket
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--nodo_destino", required=True, help="El ID del nodo destino (ej. nodo_1)")
parser.add_argument("--config", default="config_nodo.json", help="Ruta al archivo JSON")
args = parser.parse_args()

with open(args.config, 'r') as archivo:
    configuracion = json.load(archivo)

datos_nodo = configuracion["nodos"][args.nodo_destino]
IP = datos_nodo["ip"]
PORT = datos_nodo["puerto"]   

def operacion(decoded_data):

    operandos=decoded_data['operandos']
    if operandos[1]==0:
        print('division entre cero')
        resultado = 'N/A'
        return resultado
    
    resultado=operandos[0]/operandos[1]
    return resultado

server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
try:
    
    server.connect((IP,PORT))
except ConnectionRefusedError:
    exit()

buffer = ""

while True:
    data=server.recv(1024)
    if not data:
        break

    buffer += data.decode('utf-8')

    while '\n' in buffer:
        linea, buffer = buffer.split('\n', 1)
        linea = linea.strip()
        
        if not linea:
            continue

        decoded_data = json.loads(linea)
        print(decoded_data)

        if decoded_data['codigo_contenido'] == 'DIV_REQ':
            resultado = operacion(decoded_data)

            respuesta = {
                'id_mensaje': str(uuid.uuid4()),
                'id_solicitud_original': decoded_data['id_mensaje'],
                'codigo_contenido': 'DIV_RES',
                'resultado': resultado
            }

            respuesta_str = json.dumps(respuesta) + '\n'
            server.send(respuesta_str.encode('utf-8'))

