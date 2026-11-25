import tkinter as tk
from tkinter import ttk


class CompiladorGUI:

    def __init__(self, root, callback_analizar=None, callback_triplos=None):
        self.root = root
        self.callback_analizar = callback_analizar
        self.callback_triplos = callback_triplos

        self.root.title("Compilador - Analizador Semántico")
        self.root.geometry("1100x650")
        self.root.configure(bg="#1e1e2e")

        # ==================================================
        # ESTILOS
        # ==================================================

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TFrame",
            background="#1e1e2e"
        )

        style.configure(
            "TLabel",
            background="#1e1e2e",
            foreground="#cdd6f4",
            font=("Consolas", 11, "bold")
        )

        style.configure(
            "TButton",
            font=("Consolas", 10, "bold"),
            padding=6
        )

        style.configure(
            "Treeview",
            background="#313244",
            foreground="#cdd6f4",
            fieldbackground="#313244",
            font=("Consolas", 10),
            rowheight=24
        )

        style.configure(
            "Treeview.Heading",
            background="#45475a",
            foreground="#f5e0dc",
            font=("Consolas", 10, "bold")
        )

        style.map(
            "Treeview",
            background=[("selected", "#89b4fa")]
        )

        # ==================================================
        # CONTENEDOR PRINCIPAL
        # ==================================================

        contenedor = ttk.Frame(
            self.root,
            padding=10
        )

        contenedor.pack(
            fill="both",
            expand=True
        )

        # ==================================================
        # PANEL IZQUIERDO
        # ==================================================

        panel_izq = ttk.Frame(contenedor)

        panel_izq.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 10)
        )

        ttk.Label(
            panel_izq,
            text="Código fuente:"
        ).pack(anchor="w")

        # --------------------------------------------------
        # EDITOR
        # --------------------------------------------------

        # Contenedor interno solamente para el editor
        # y los números de línea.
        frame_editor = ttk.Frame(panel_izq)

        frame_editor.pack(
            fill="both",
            expand=True,
            pady=(5, 10)
        )

        # --------------------------------------------------
        # NÚMEROS DE LÍNEA
        # --------------------------------------------------

        self.txt_lineas = tk.Text(
            frame_editor,
            width=4,
            padx=5,
            pady=5,
            bg="#181825",
            fg="#6c7086",
            font=("Consolas", 12),
            wrap="none",
            state="disabled",
            bd=0,
            highlightthickness=0
        )

        self.txt_lineas.pack(
            side="left",
            fill="y"
        )

        # --------------------------------------------------
        # EDITOR DE CÓDIGO
        # --------------------------------------------------

        self.txt_codigo = tk.Text(
            frame_editor,
            bg="#181825",
            fg="#cdd6f4",
            insertbackground="#f5e0dc",
            font=("Consolas", 12),
            wrap="none",
            undo=True
        )

        self.txt_codigo.pack(
            side="left",
            fill="both",
            expand=True
        )

        # Actualizar números de línea al escribir
        self.txt_codigo.bind(
            "<KeyRelease>",
            self.actualizar_lineas
        )

        # Actualizar números de línea
        self.actualizar_lineas()

        # ==================================================
        # BOTONES
        # ==================================================

        frame_botones = ttk.Frame(panel_izq)

        frame_botones.pack(
            fill="x"
        )

        ttk.Button(
            frame_botones,
            text="▶ Analizar",
            command=self.analizar
        ).pack(
            side="left",
            padx=2
        )

        ttk.Button(
            frame_botones,
            text="🧹 Limpiar",
            command=self.limpiar_todo
        ).pack(
            side="left",
            padx=2
        )

        ttk.Button(
            frame_botones,
            text="📋 Copiar código",
            command=self.copiar_codigo
        ).pack(
            side="left",
            padx=2
        )

        ttk.Button(
            frame_botones,
            text="Generar triplos",
            command=self.generar_triplos
        ).pack(
            side="left",
            padx=2
        )

        # ==================================================
        # PANEL DERECHO
        # ==================================================

        panel_der = ttk.Frame(contenedor)

        panel_der.pack(
            side="right",
            fill="both",
            expand=True
        )

        # ==================================================
        # NOTEBOOK
        # ==================================================

        self.notebook = ttk.Notebook(panel_der)

        self.notebook.pack(
            fill="both",
            expand=True
        )

        # ==================================================
        # PESTAÑA TABLA DE TIPOS
        # ==================================================

        frame_tipos = ttk.Frame(
            self.notebook
        )

        self.notebook.add(
            frame_tipos,
            text="  Tabla de Simbolos  "
        )

        self.tabla_tipos = ttk.Treeview(
            frame_tipos,
            columns=(
                "lexema",
                "tipo"
            ),
            show="headings"
        )

        self.tabla_tipos.heading(
            "lexema",
            text="Lexema"
        )

        self.tabla_tipos.heading(
            "tipo",
            text="Tipo de dato"
        )

        self.tabla_tipos.column(
            "lexema",
            width=180,
            anchor="center"
        )

        self.tabla_tipos.column(
            "tipo",
            width=200,
            anchor="center"
        )

        # Scrollbar
        scroll_tipos = ttk.Scrollbar(
            frame_tipos,
            orient="vertical",
            command=self.tabla_tipos.yview
        )

        self.tabla_tipos.configure(
            yscrollcommand=scroll_tipos.set
        )

        scroll_tipos.pack(
            side="right",
            fill="y",
            pady=5,
            padx=(0, 5)
        )

        self.tabla_tipos.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(5, 0),
            pady=5
        )

        # ==================================================
        # PESTAÑA TABLA DE ERRORES
        # ==================================================

        frame_errores = ttk.Frame(
            self.notebook
        )

        self.notebook.add(
            frame_errores,
            text="  Tabla de Errores  "
        )

        self.tabla_errores = ttk.Treeview(
            frame_errores,
            columns=(
                "token",
                "lexema",
                "linea",
                "descripcion"
            ),
            show="headings"
        )

        self.tabla_errores.heading(
            "token",
            text="Token"
        )

        self.tabla_errores.heading(
            "lexema",
            text="Lexema"
        )

        self.tabla_errores.heading(
            "linea",
            text="Línea"
        )

        self.tabla_errores.heading(
            "descripcion",
            text="Descripción"
        )

        self.tabla_errores.column(
            "token",
            width=90,
            anchor="center"
        )

        self.tabla_errores.column(
            "lexema",
            width=120,
            anchor="center"
        )

        self.tabla_errores.column(
            "linea",
            width=60,
            anchor="center"
        )

        self.tabla_errores.column(
            "descripcion",
            width=340,
            anchor="w"
        )

        # Scrollbar
        scroll_errores = ttk.Scrollbar(
            frame_errores,
            orient="vertical",
            command=self.tabla_errores.yview
        )

        self.tabla_errores.configure(
            yscrollcommand=scroll_errores.set
        )

        scroll_errores.pack(
            side="right",
            fill="y",
            pady=5,
            padx=(0, 5)
        )

        self.tabla_errores.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(5, 0),
            pady=5
        )

        # ==================================================
        # BARRA DE ESTADO
        # ==================================================

        self.estado = tk.StringVar(
            value="Listo."
        )

        tk.Label(
            self.root,
            textvariable=self.estado,
            bg="#313244",
            fg="#a6e3a1",
            font=("Consolas", 10),
            anchor="w"
        ).pack(
            fill="x",
            side="bottom"
        )

    # ======================================================
    # ACTUALIZAR NÚMEROS DE LÍNEA
    # ======================================================

    def actualizar_lineas(self, event=None):

        cantidad_lineas = int(
            self.txt_codigo.index("end-1c").split(".")[0]
        )

        numeros = "\n".join(
            str(i) for i in range(1, cantidad_lineas + 1)
        )

        self.txt_lineas.config(
            state="normal"
        )

        self.txt_lineas.delete(
            "1.0",
            "end"
        )

        self.txt_lineas.insert(
            "1.0",
            numeros
        )

        self.txt_lineas.config(
            state="disabled"
        )

    # ======================================================
    # OBTENER CÓDIGO
    # ======================================================

    def obtener_codigo(self):

        return self.txt_codigo.get(
            "1.0",
            "end-1c"
        )

    # ======================================================
    # ANALIZAR
    # ======================================================

    def analizar(self):

        codigo = self.obtener_codigo()

        if not codigo.strip():

            self.estado.set(
                "No hay código para analizar."
            )

            return

        # La interfaz NO hace el análisis.
        # Se lo manda a main.py.

        if self.callback_analizar:

            self.callback_analizar(codigo)

    # ======================================================
    # LIMPIAR TABLAS
    # ======================================================

    def limpiar_tablas(self):

        for fila in self.tabla_tipos.get_children():

            self.tabla_tipos.delete(fila)

        for fila in self.tabla_errores.get_children():

            self.tabla_errores.delete(fila)

    # ======================================================
    # LIMPIAR TODO
    # ======================================================

    def limpiar_todo(self):

        self.txt_codigo.delete(
            "1.0",
            "end"
        )

        self.actualizar_lineas()

        self.limpiar_tablas()

        self.estado.set(
            "Todo limpio."
        )

    # ======================================================
    # COPIAR CÓDIGO
    # ======================================================

    def copiar_codigo(self):

        codigo = self.obtener_codigo()

        self.root.clipboard_clear()

        self.root.clipboard_append(
            codigo
        )

        self.estado.set(
            "Código copiado al portapapeles."
        )

    # ======================================================
    # MOSTRAR RESULTADOS
    # ======================================================

    def mostrar_resultados(
        self,
        tabla,
        errores
    ):

        # --------------------------------------------------
        # Limpiar resultados anteriores
        # --------------------------------------------------

        self.limpiar_tablas()

        # --------------------------------------------------
        # TABLA DE TIPOS
        # --------------------------------------------------

        for lexema, tipo in tabla.items():

            # Los símbolos sin tipo (operadores, ";",
            # variables no definidas) se muestran con "-"
            # en lugar de dejar la celda como "None".
            tipo_mostrado = tipo if tipo is not None else "-"

            self.tabla_tipos.insert(
                "",
                "end",
                values=(
                    lexema,
                    tipo_mostrado
                )
            )

        # --------------------------------------------------
        # TABLA DE ERRORES
        # --------------------------------------------------

        for error in errores:

            token = error[0]
            lexema = error[1]
            linea = error[2]
            descripcion = error[3]

            self.tabla_errores.insert(
                "",
                "end",
                values=(
                    token,
                    lexema,
                    linea,
                    descripcion
                )
            )

        # --------------------------------------------------
        # ESTADO
        # --------------------------------------------------

        if errores:

            self.estado.set(
                f"⚠ Análisis completado — "
                f"{len(errores)} error(es)."
            )

            # Mostrar errores automáticamente
            self.notebook.select(1)

        else:

            # La tabla incluye operadores, números, etc.; aquí solo se
            # cuentan las variables que sí tienen tipo.
            variables = sum(
                1 for lexema, tipo in tabla.items()
                if lexema.startswith("*") and tipo is not None
            )

            self.estado.set(
                f"✔ Análisis completado — "
                f"{variables} variable(s), "
                f"0 errores."
            )

            self.notebook.select(0)

    def generar_triplos(self):
        codigo = self.obtener_codigo()

        if not codigo.strip():
            self.estado.set("No hay código para generar triplos.")
            return

        if self.callback_triplos:
            self.callback_triplos(codigo)