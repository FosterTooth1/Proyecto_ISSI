import ctypes
from ctypes import c_int, c_double, c_char_p, POINTER, Structure
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# Para soportar imágenes JPG en Tkinter
try:
    from PIL import Image, ImageTk
except ImportError:
    messagebox.showerror("Error", "Se requiere instalar 'Pillow' para visualizar imágenes JPG.")
    sys.exit(1)

# =======================
# ESTRUCTURAS Y CLASES C
# =======================
class ResultadoGenetico(Structure):
    _fields_ = [
        ("recorrido", POINTER(c_int)),            # Puntero al arreglo de la mejor ruta
        ("fitness", c_double),                    # Fitness del mejor individuo
        ("tiempo_ejecucion", c_double),           # Tiempo de ejecución del algoritmo
        ("nombres_ciudades", POINTER(ctypes.c_char * 50 * 32)),  # Puntero a los nombres de las ciudades
        ("longitud_recorrido", c_int)             # Longitud de la ruta
    ]


class AlgoritmoGenetico:
    def __init__(self, ruta_biblioteca):
        # Cargamos la biblioteca compartida desde la ruta proporcionada
        self.biblioteca = ctypes.CDLL(ruta_biblioteca)
        
        # Configuramos el tipo de retorno de la función `ejecutar_algoritmo_genetico_ventanas_tiempo`
        self.biblioteca.ejecutar_algoritmo_genetico_ventanas_tiempo.restype = POINTER(ResultadoGenetico)
        
        # Especificamos los tipos de argumentos que espera `ejecutar_algoritmo_genetico_ventanas_tiempo`
        self.biblioteca.ejecutar_algoritmo_genetico_ventanas_tiempo.argtypes = [
            c_int,      # tamano_poblacion
            c_int,      # longitud_genotipo
            c_int,      # num_generaciones
            c_int,      # num_competidores
            c_int,      # m parametro de heurística
            c_double,   # probabilidad_mutacion
            c_double,   # probabilidad_cruce
            c_char_p,   # nombre_archivo (ruta al archivo con matriz de distancias)
            c_int       # km_hr
        ]
        
        # Configuramos la función para liberar resultados
        self.biblioteca.liberar_resultado.argtypes = [POINTER(ResultadoGenetico)]

    def ejecutar(self, tamano_poblacion, longitud_genotipo, num_generaciones,
                 num_competidores, m, probabilidad_mutacion,
                 probabilidad_cruce, nombre_archivo, km_hr):
        try:
            nombre_archivo_bytes = nombre_archivo.encode('utf-8')
            resultado = self.biblioteca.ejecutar_algoritmo_genetico_ventanas_tiempo(
                tamano_poblacion,
                longitud_genotipo,
                num_generaciones,
                num_competidores,
                m,
                probabilidad_mutacion,
                probabilidad_cruce,
                nombre_archivo_bytes,
                km_hr
            )
            
            if not resultado:
                raise RuntimeError("Error al ejecutar el algoritmo genético.")
            
            recorrido = [resultado.contents.recorrido[i]
                         for i in range(resultado.contents.longitud_recorrido)]
            
            nombres_ciudades = []
            for i in range(resultado.contents.longitud_recorrido):
                ciudad_c = bytes(resultado.contents.nombres_ciudades.contents[i]).decode('utf-8')
                # Quitar caracteres nulos
                ciudad_c = ciudad_c.split('\0')[0]
                nombres_ciudades.append(ciudad_c)
            
            salida = {
                'recorrido': recorrido,
                'nombres_ciudades': nombres_ciudades,
                'fitness': resultado.contents.fitness,
                'tiempo_ejecucion': resultado.contents.tiempo_ejecucion
            }
            
            self.biblioteca.liberar_resultado(resultado)
            
            return salida
            
        except Exception as e:
            raise RuntimeError(f"Error al ejecutar el algoritmo genético: {str(e)}")

# ==================================
# FUNCIÓN PRINCIPAL Y LÓGICA DE GUI
# ==================================
def crear_gui():
    ventana = tk.Tk()
    ventana.title("Algoritmo Bioinspirado con Interfaz")

    # ------------------------------------------------
    # Variables de control y lista de estados
    # ------------------------------------------------
    estados_mexico = [
        "Aguascalientes", "Baja California", "Baja California Sur",
        "Campeche", "Chiapas", "Chihuahua", "Coahuila", "Colima", "Durango",
        "Guanajuato", "Guerrero", "Hidalgo", "Jalisco", "Estado de Mexico",
        "Michoacan", "Morelos", "Nayarit", "Nuevo Leon", "Oaxaca", "Puebla",
        "Queretaro", "Quintana Roo", "San Luis Potosi", "Sinaloa", "Sonora",
        "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz", "Yucatan",
        "Zacatecas", "CDMX"
    ]

    ubicacion_concedida = tk.BooleanVar(value=False)  # Para saber si se concedió ubicación
    # Combobox que selecciona inicio (por defecto 0)
    ciudad_inicio = tk.StringVar(value=estados_mexico[0])
    # Combobox que selecciona destino (por defecto 1)
    ciudad_destino = tk.StringVar(value=estados_mexico[1])

    # ------------------------------------------------
    # Frame superior: Botones y Combobox
    # ------------------------------------------------
    marco_seleccion = ttk.Frame(ventana, padding="10")
    marco_seleccion.grid(row=0, column=0, sticky="W")

    # Botón para acceder a la ubicación
    def acceder_ubicacion():
        respuesta = messagebox.askyesno(
            "Permiso de Ubicación",
            "¿Permitir acceso a la ubicación? "
        )
        if respuesta:
            # Si el usuario dijo "Sí": poner Ciudad de México como default
            ciudad_inicio.set("CDMX")
            ubicacion_concedida.set(True)
        else:
            # Si dijo "No", se pregunta si desea ingresar manualmente la ciudad
            resp_manual = messagebox.askyesno(
                "Configurar manualmente",
                "¿Desea ingresar manualmente la ciudad de inicio?"
            )
            if resp_manual:
                # Usuario dice "Sí": entonces todo normal
                ubicacion_concedida.set(True)
            else:
                # Usuario dice "No": marcar error y cerrar
                messagebox.showerror(
                    "Error",
                    "No se concedió acceso a la ubicación y no se ingresará manualmente.\nCerrando aplicación..."
                )
                ventana.destroy()  # Cerrar la ventana principal
                sys.exit(0)        # Cerrar completamente la aplicación

    boton_ubicacion = ttk.Button(marco_seleccion, text="Acceder a la Ubicación", command=acceder_ubicacion)
    boton_ubicacion.grid(row=0, column=0, columnspan=2, pady=5)

    etiqueta_inicio = ttk.Label(marco_seleccion, text="Seleccione punto de inicio:")
    etiqueta_inicio.grid(row=1, column=0, padx=5, pady=5, sticky="W")

    combo_inicio = ttk.Combobox(marco_seleccion, values=estados_mexico, textvariable=ciudad_inicio, state="readonly")
    combo_inicio.grid(row=1, column=1, padx=5, pady=5)

    etiqueta_destino = ttk.Label(marco_seleccion, text="Seleccione destino:")
    etiqueta_destino.grid(row=2, column=0, padx=5, pady=5, sticky="W")

    combo_destino = ttk.Combobox(marco_seleccion, values=estados_mexico, textvariable=ciudad_destino, state="readonly")
    combo_destino.grid(row=2, column=1, padx=5, pady=5)

    # ------------------------------------------------
    # Frame para resultados (Text) y la imagen
    # ------------------------------------------------
    marco_resultados = ttk.Frame(ventana, padding="10")
    marco_resultados.grid(row=1, column=0, sticky="NSEW")

    texto_resultado = tk.Text(marco_resultados, width=50, height=20)
    texto_resultado.grid(row=0, column=0, sticky="NSEW")

    label_mapa = ttk.Label(marco_resultados)
    label_mapa.grid(row=0, column=1, padx=10, pady=10, sticky="NSEW")

    # ------------------------------------------------
    # FUNCIÓN PARA GENERAR Y MOSTRAR LA RUTA
    # ------------------------------------------------
    def ejecutar_y_mostrar_ruta():
        # Comprobamos si se concedió ubicación
        if not ubicacion_concedida.get():
            messagebox.showerror("Error", "No se ha concedido acceso a la ubicación.\nOperación cancelada.")
            return

        # Limpiamos el Text
        texto_resultado.delete("1.0", tk.END)

        inicio = ciudad_inicio.get()
        destino = ciudad_destino.get()

        # Mensaje decorativo (opcional)
        texto_resultado.insert(tk.END, f"Punto de Inicio: {inicio}\n")
        texto_resultado.insert(tk.END, f"Destino : {destino}\n\n")

        try:
            directorio_actual = os.path.dirname(os.path.abspath(__file__))
            nombre_biblioteca = "genetic_algo_vent.dll" if os.name == 'nt' else "libgenetic_algo_vent.so"
            ruta_biblioteca = os.path.join(directorio_actual, nombre_biblioteca)

            if not os.path.exists(ruta_biblioteca):
                raise RuntimeError(f"No se encuentra la biblioteca en {ruta_biblioteca}")

            ag = AlgoritmoGenetico(ruta_biblioteca)

            # Parámetros fijos
            tamano_poblacion = 1000
            longitud_genotipo = 32
            num_generaciones = 100
            num_competidores = 2
            m = 3
            probabilidad_mutacion = 0.3
            probabilidad_cruce = 0.9
            nombre_archivo = "Distancias_no_head.csv"
            km_hr = 80

            resultado = ag.ejecutar(
                tamano_poblacion=tamano_poblacion,
                longitud_genotipo=longitud_genotipo,
                num_generaciones=num_generaciones,
                num_competidores=num_competidores,
                m=m,
                probabilidad_mutacion=probabilidad_mutacion,
                probabilidad_cruce=probabilidad_cruce,
                nombre_archivo=nombre_archivo,
                km_hr=km_hr
            )

            # --------------------------------------------
            # OBTENIENDO LA SUB-RUTA DE INICIO A DESTINO
            # --------------------------------------------
            nombres = resultado['nombres_ciudades']

            try:
                start_index = nombres.index(inicio)
                end_index = nombres.index(destino)
            except ValueError:
                messagebox.showerror("Error", f"No se encontró '{inicio}' o '{destino}' en la ruta.")
                return

            # Si el índice de inicio es menor o igual que el de destino
            if start_index <= end_index:
                sub_ruta = nombres[start_index:end_index + 1]
            else:
                # Si la permutación "da la vuelta"
                sub_ruta = nombres[start_index:] + nombres[:end_index + 1]

            # --------------------------------------------
            # IMPRESIÓN DE LA INFORMACIÓN
            # --------------------------------------------
            texto_resultado.insert(tk.END, f"Ciudad de Inicio: {inicio}\n")
            texto_resultado.insert(tk.END, f"Ciudad de Destino: {destino}\n\n")
            texto_resultado.insert(tk.END, "Mejor ruta encontrada:\n\n")

            # Imprime la sub-ruta sin los índices de la permutación
            for i, ciudad in enumerate(sub_ruta, start=1):
                texto_resultado.insert(tk.END, f"{i}. {ciudad}\n")

            texto_resultado.insert(tk.END, f"\nFitness: {resultado['fitness']}\n")
            texto_resultado.insert(tk.END, f"Tiempo de ejecución: {resultado['tiempo_ejecucion']:.2f} segundos\n")

            # --------------------------------------------
            # MOSTRAR IMAGEN DEL MAPA
            # --------------------------------------------
            try:
                ruta_imagen = os.path.join(directorio_actual, "mexico.jpg")
                if not os.path.exists(ruta_imagen):
                    raise FileNotFoundError("No se encontró 'mexico.jpg' en el directorio actual.")

                # Cargar imagen con PIL
                imagen = Image.open(ruta_imagen)
                mapa_image = ImageTk.PhotoImage(imagen)
                label_mapa.configure(image=mapa_image)
                # Guardar referencia para evitar que el objeto sea recolectado
                label_mapa.image = mapa_image

            except Exception as e:
                texto_resultado.insert(tk.END, f"\n[Advertencia] No se pudo cargar la imagen: {e}\n")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # Botón para generar la ruta
    boton_ejecutar = ttk.Button(marco_seleccion, text="Generar Ruta", command=ejecutar_y_mostrar_ruta)
    boton_ejecutar.grid(row=3, column=0, columnspan=2, pady=10)

    ventana.mainloop()


if __name__ == "__main__":
    crear_gui()
