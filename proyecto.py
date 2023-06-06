import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import pandas as pd
import re
import spacy
import matplotlib.pyplot as plt
from collections import Counter
from wordcloud import WordCloud

BASIC_MODEL = 'es_core_news_sm'
ADVANCED_MODEL = 'es_dep_news_trf'

# Función para leer el archivo CSV y procesar los datos
def procesar_csv():
    # Seleccionar el archivo CSV
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    
    if file_path:
        # Leer el archivo CSV
        data = pd.read_csv(file_path, header=None).drop_duplicates()
        comentarios = data[0].tolist()
        
        # Ejecutar el procesamiento en un hilo separado
        threading.Thread(target=procesar_comentarios, args=(comentarios,)).start()
        mostrar_indicador_carga()

# Procesar los comentarios y generar gráficas
def procesar_comentarios(comentarios):
    def quitarEmojis(string):
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticonos
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002500-\U00002BEF"  # Chinese char
            u"\U00002702-\U000027B0"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            u"\U0001f926-\U0001f937"
            u"\U00010000-\U0010ffff"
            u"\u2640-\u2642" 
            u"\u2600-\u2B55"
            u"\u200d"
            u"\u23cf"
            u"\u23e9"
            u"\u231a"
            u"\ufe0f"  # dingbats
            u"\u3030"
        "]+", re.UNICODE)
        return emoji_pattern.sub(r'', string)

    def entidadNotificador(string):
        string = string.replace('FES Acatlán', 'FES')
        string = string.replace('Transporte + Recorridos', 'transporte')
        return string

    def eliminarCaracteresEspecificos(string:str):
        caracteres_especiales = ['*','+','•']
        for caracter in caracteres_especiales:
            string = string.replace(caracter,'')
        return string

    # Cargar el modelo de Spacy
    nlp = spacy.load(ADVANCED_MODEL)

    # Remover los emojis y procesar los comentarios con Spacy
    docs = [nlp(eliminarCaracteresEspecificos(entidadNotificador(quitarEmojis(comentario)))) for comentario in comentarios]

    # Quitar las stopwords y lematizar
    docs = [" ".join([token.lemma_ for token in doc if not token.is_stop and len(token)>2]) for doc in docs]

    # Encuentra los sustantivos más comunes
    sustantivos_comunes = Counter([token.text for doc in docs for token in nlp(doc) if token.pos_ == 'NOUN'])

    # Encuentra los verbos más comunes
    verbos_comunes = Counter([token.text for doc in docs for token in nlp(doc) if token.pos_ == 'VERB'])

    # Encuentra los adjetivos más comunes
    adjetivos_comunes = Counter([token.text for doc in docs for token in nlp(doc) if token.pos_ == 'ADJ'])

    # Encuentra los pronombres propios más comunes
    nombres_propios_comunes = Counter([token.text for doc in docs for token in nlp(doc) if token.pos_ == 'PROPN'])

    # Cargar el modelo básico de Spacy
    nlp = spacy.load(BASIC_MODEL)

    # Encuentra las entidades nombradas más comunes
    entidades_comunes = Counter([ent.text for doc in docs for ent in nlp(doc).ents])

    # Mostrar las gráficas en la ventana principal
    ventana_principal.after(0, lambda: mostrar_graficas(sustantivos_comunes, verbos_comunes, adjetivos_comunes, nombres_propios_comunes, entidades_comunes))

# Mostrar el indicador de carga
def mostrar_indicador_carga():
    label_carga.config(text="Procesando comentarios...")
    label_carga.pack(pady=10)

# Ocultar el indicador de carga
def ocultar_indicador_carga():
    label_carga.pack_forget()

# Mostrar las gráficas en la ventana principal
def mostrar_graficas(sustantivos_comunes, verbos_comunes, adjetivos_comunes, nombres_propios_comunes, entidades_comunes):
    # Crear el marco de desplazamiento
    scroll_frame = tk.Frame(frame_canvas)

    # Crear el lienzo con desplazamiento
    canvas = tk.Canvas(scroll_frame, width=800, height=400)
    scrollbar = tk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Gráficas de sustantivos más comunes
    plt.subplot(2, 2, 1)
    graficarPalabras(sustantivos_comunes, "Sustantivos más comunes")

    # Gráficas de verbos más comunes
    plt.subplot(2, 2, 2)
    graficarPalabras(verbos_comunes, "Verbos más comunes")

    # Gráficas de adjetivos más comunes
    plt.subplot(2, 2, 3)
    graficarPalabras(adjetivos_comunes, "Adjetivos más comunes")

    # Gráficas de nombres propios más comunes
    plt.subplot(2, 2, 4)
    graficarPalabras(nombres_propios_comunes, "Nombres propios más comunes")

    # Ajustar el tamaño del lienzo al contenido
    canvas.configure(scrollregion=canvas.bbox("all"))

    # Mostrar las gráficas en la ventana
    plt.tight_layout()
    plt.show()

    # Ocultar el indicador de carga
    ocultar_indicador_carga()

# Función para graficar las palabras más comunes
def graficarPalabras(counter, title):
    wordcloud = WordCloud(width=800, height=800, background_color='white').generate_from_frequencies(counter)

    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.title(title)

# Crear la ventana principal
ventana_principal = tk.Tk()
ventana_principal.title("Análisis de comentarios")
ventana_principal.geometry("400x200")
ventana_principal.resizable = (False, False)

# Crear el marco de desplazamiento
frame_canvas = tk.Frame(ventana_principal)
frame_canvas.pack(fill="both", expand=False)

# Etiqueta de carga
label_carga = tk.Label(ventana_principal, text="Procesando comentarios...")

# Botón para seleccionar el archivo CSV
button = tk.Button(ventana_principal, text="Seleccionar archivo CSV", command=procesar_csv)
button.pack(side= tk.TOP)

# Ejecutar la ventana principal
ventana_principal.mainloop()
 