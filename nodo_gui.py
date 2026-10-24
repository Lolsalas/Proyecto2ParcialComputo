import socket
import json
import tkinter as tk
import threading
import sqlite3 
import uuid
import argparse
from tkinter import messagebox


parser = argparse.ArgumentParser()
parser.add_argument("--nodo_destino", required=True, help="ID del nodo al que se conectará (ej. nodo_1)")
parser.add_argument("--config", default="config_nodo.json", help="Ruta al archivo JSON")
args = parser.parse_args()

with open(args.config, 'r') as archivo:
    configuracion = json.load(archivo)

datos_nodo = configuracion["nodos"][args.nodo_destino]
IP_NODO = datos_nodo["ip"]
PUERTO_NODO = datos_nodo["puerto"]


operacion = ""
id_esperado = None


cliente_gui = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    cliente_gui.connect((IP_NODO, PUERTO_NODO))
    print(f"GUI conectada exitosamente al {args.nodo_destino} en {IP_NODO}:{PUERTO_NODO}")
except ConnectionRefusedError:
    print(f"Error: No se pudo conectar al nodo {args.nodo_destino}. Asegúrate de iniciarlo primero.")
    exit()


def escuchar_nodo():
    global id_esperado, operacion
    

    while True:
        try:
            data = cliente_gui.recv(2048)
            if not data:
                print("El nodo cerró la conexión.")
                break
                
            mensaje = json.loads(data.decode('utf-8'))
            
            # Filtro vital: ¿Es una respuesta a la petición que YO hice?
            if mensaje.get("id_solicitud_original") == id_esperado and id_esperado is not None:
                resultado = str(mensaje.get("resultado"))
                

                
                # Actualizar la interfaz gráfica
                box.delete('1.0', tk.END)
                box.insert(tk.END, resultado)
                
                # Reiniciar estado para la siguiente operación
                operacion = resultado
                id_esperado = None


                
        except json.JSONDecodeError:
            pass # Ignorar mensajes mal formados
        except Exception as e:
            print(f"Error en el hilo receptor: {e}")
            break

# Iniciar el hilo en segundo plano
hilo_escucha = threading.Thread(target=escuchar_nodo, daemon=True)
hilo_escucha.start()

# ====================================================================
# 5. LÓGICA DE LA INTERFAZ
# ====================================================================
def ejemplo(char):
    global operacion
    operacion = operacion + char
    box.insert(tk.END, char)

def delete():
    global operacion
    operacion = ''
    box.delete('1.0', tk.END)

def send():
    global operacion, id_esperado
    
    if not operacion:
        return

    codigo = ""
    operador = ""
    
    # 1. Identificar el operador (priorizando de abajo hacia arriba en operaciones básicas)
    if '+' in operacion:
        codigo = "SUM_REQ"
        operador = '+'
    elif '*' in operacion:
        codigo = "MUL_REQ"
        operador = '*'
    elif '/' in operacion:
        codigo = "DIV_REQ"
        operador = '/'
    elif '-' in operacion:
        codigo = "SUB_REQ"
        operador = '-'
    else:
        print("Operación incompleta")
        return

    # 2. Parsear operandos (rsplit protege el caso donde el primer número es negativo)
    partes = operacion.rsplit(operador, 1)
    
    try:
        operandos = [float(partes[0]), float(partes[1])]
    except ValueError:
        print("Error al leer los números.")
        return

    # 3. Generar ID y armar el mensaje
    id_esperado = str(uuid.uuid4())
    
    mensaje = {
        'id_mensaje': id_esperado,
        'codigo_contenido': codigo,
        'operandos': operandos
    }

    # 4. Enviar al nodo
    try:

        mensaje_enviar=json.dumps(mensaje) + '\n'
        cliente_gui.send(mensaje_enviar.encode('utf-8'))
    except Exception as e:
        print(f"Error al enviar: {e}")


# ====================================================================
# 6. DISEÑO DE TKINTER
# ====================================================================
ventana = tk.Tk()
ventana.title('Mi calculadora ADS')
ventana.geometry('1320x700')

estilo_texto = {"bg": "#f1f2f6", "fg": "#2f3542", "font": ("Arial", 22, "bold"), "bd": 0, "padx": 10, "pady": 10}
estilo_num = {"bg": "#57606f", "fg": "#ffffff", "font": ("Arial", 16, "bold"), "bd": 0, "cursor": "hand2", "activebackground": "#747d8c", "activeforeground": "white"}
estilo_op = {"bg": "#1e90ff", "fg": "#ffffff", "font": ("Arial", 16, "bold"), "bd": 0, "cursor": "hand2", "activebackground": "#70a1ff", "activeforeground": "white"}
estilo_ac = {"bg": "#ff4757", "fg": "#ffffff", "font": ("Arial", 14, "bold"), "bd": 0, "cursor": "hand2", "activebackground": "#ff6b81", "activeforeground": "white"}
estilo_hist = {"bg": "#ffa502", "fg": "#ffffff", "font": ("Arial", 14, "bold"), "bd": 0, "cursor": "hand2", "activebackground": "#ff7f50", "activeforeground": "white"}

box = tk.Text(ventana, height=2, **estilo_texto)
box.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky='we')

tk.Button(ventana, text='AC', height=2, **estilo_ac, command=delete).grid(row=1, column=0, padx=10, pady=10, sticky='we', columnspan=2)
tk.Button(ventana, text='HISTORIAL', height=2, **estilo_hist, command='').grid(row=1, column=2, padx=10, pady=10, sticky='we', columnspan=2)

tk.Button(ventana, text='7', height=2, **estilo_num, command=lambda: ejemplo('7')).grid(row=2, column=0, padx=10, pady=10, sticky='we')
tk.Button(ventana, text='8', height=2, **estilo_num, command=lambda: ejemplo('8')).grid(row=2, column=1, padx=10, pady=10, sticky='we')
tk.Button(ventana, text='9', height=2, **estilo_num, command=lambda: ejemplo('9')).grid(row=2, column=2, padx=10, pady=10, sticky='we')

tk.Button(ventana, text='4', height=2, **estilo_num, command=lambda: ejemplo('4')).grid(row=3, column=0, padx=10, pady=10, sticky='we')
tk.Button(ventana, text='5', height=2, **estilo_num, command=lambda: ejemplo('5')).grid(row=3, column=1, padx=10, pady=10, sticky='we')
tk.Button(ventana, text='6', height=2, **estilo_num, command=lambda: ejemplo('6')).grid(row=3, column=2, padx=10, pady=10, sticky='we')

tk.Button(ventana, text='1', height=2, **estilo_num, command=lambda: ejemplo('1')).grid(row=4, column=0, padx=10, pady=10, sticky='we')
tk.Button(ventana, text='2', height=2, **estilo_num, command=lambda: ejemplo('2')).grid(row=4, column=1, padx=10, pady=10, sticky='we')
tk.Button(ventana, text='3', height=2, **estilo_num, command=lambda: ejemplo('3')).grid(row=4, column=2, padx=10, pady=10, sticky='we')

tk.Button(ventana, text='+', height=2, **estilo_op, command=lambda: ejemplo('+')).grid(row=2, column=3, padx=10, pady=10, sticky='we')
tk.Button(ventana, text='-', height=2, **estilo_op, command=lambda: ejemplo('-')).grid(row=3, column=3, padx=10, pady=10, sticky='we')
tk.Button(ventana, text='*', height=2, **estilo_op, command=lambda: ejemplo('*')).grid(row=4, column=3, padx=10, pady=10, sticky='we')
tk.Button(ventana, text='/', height=2, **estilo_op, command=lambda: ejemplo('/')).grid(row=5, column=3, padx=10, pady=10, sticky='we')

tk.Button(ventana, text='0', height=2, **estilo_num, command=lambda: ejemplo('0')).grid(row=5, column=0, padx=10, pady=10, sticky='we')
tk.Button(ventana, text='.', height=2, **estilo_num, command=lambda: ejemplo('.')).grid(row=5, column=1, padx=10, pady=10, sticky='we')
tk.Button(ventana, text='=', height=2, **estilo_op, command=send).grid(row=5, column=2, padx=10, pady=10, sticky='we')

ventana.mainloop()