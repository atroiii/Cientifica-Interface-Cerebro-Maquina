import inspect
import os
import queue
import threading
import time

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from src.models.eeg_buffer import EEGBuffer, HISTORY
from src.utils.hardware_helpers import listar_portas


# ── Temas ─────────────────────────────────────────────────────────────────
PALETTES = {
    "light": {
        "bg":          "#F4F6FB",
        "panel":       "#FFFFFF",
        "card":        "#EEF1F8",
        "border":      "#D6DCEA",
        "grid":        "#E3E8F2",
        "text":        "#1E2A45",
        "dim":         "#6B7A9E",
        "accent":      "#0D9488",
        "accent_hov":  "#0F766E",
        "accent_txt":  "#FFFFFF",
        "value":       "#D97706",
        "danger":      "#DC2626",
        "violet":      "#7C3AED",
    },
    "dark": {
        "bg":          "#0B0F17",
        "panel":       "#121826",
        "card":        "#1A2133",
        "border":      "#252E43",
        "grid":        "#1C2436",
        "text":        "#E6EAF2",
        "dim":         "#7C879E",
        "accent":      "#2DD4BF",
        "accent_hov":  "#22B8A5",
        "accent_txt":  "#062821",
        "value":       "#F5B83D",
        "danger":      "#F87171",
        "violet":      "#A78BFA",
    },
}

STATE_COLORS = {
    "A": ("#EF4444", "Distração"),
    "B": ("#8A94A8", "Neutro"),
    "C": ("#14B8A6", "Foco leve"),
    "D": ("#3B82F6", "Foco alto"),
    "E": ("#8B5CF6", "Foco máximo"),
}

FONT = "Segoe UI"
THEME_FILE = os.path.join(os.path.expanduser("~"), ".icm_tema")


def C(key):
    """Cor (claro, escuro) para widgets do CustomTkinter — trocam sozinhos com o tema."""
    return PALETTES["light"][key], PALETTES["dark"][key]


def cur(key):
    """Cor do tema ativo (para matplotlib e Canvas do tk, que não trocam sozinhos)."""
    return PALETTES[_mode()][key]


def _mode():
    return "dark" if ctk.get_appearance_mode().lower() == "dark" else "light"


def F(size, weight="normal"):
    return ctk.CTkFont(family=FONT, size=size, weight=weight)


def _load_theme():
    try:
        with open(THEME_FILE, encoding="utf-8") as f:
            mode = f.read().strip()
        return mode if mode in PALETTES else "dark"
    except OSError:
        return "dark"


def _save_theme(mode):
    try:
        with open(THEME_FILE, "w", encoding="utf-8") as f:
            f.write(mode)
    except OSError:
        pass


def _smooth(y, factor=8, sigma=1.0):
    """Curva suave (sem scipy): filtro gaussiano leve nas amostras + spline Catmull-Rom,
    que passa pelos pontos sem formar quinas. Retorna (x, y) com x em índices de amostra."""
    y = np.asarray(y, dtype=float)
    n = len(y)
    if sigma > 0:
        r = int(3 * sigma) + 1
        k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
        y = np.convolve(np.pad(y, r, mode="edge"), k / k.sum(), mode="valid")

    p = np.pad(y, 1, mode="edge")
    p0, p1, p2, p3 = p[:-3], p[1:-2], p[2:-1], p[3:]
    t = np.linspace(0, 1, factor, endpoint=False)[:, None]
    seg = 0.5 * (2 * p1 + (p2 - p0) * t
                 + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                 + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3)
    xs = (np.arange(n - 1)[:, None] + t.T).ravel()
    return np.append(xs, n - 1), np.append(seg.T.ravel(), y[-1])


def _ease(p):
    """Suaviza o início e o fim do deslizamento (smoothstep)."""
    p = min(max(p, 0.0), 1.0)
    return p * p * (3 - 2 * p)


def _windows_timer_1ms():
    """No Windows o timer padrão tem resolução de ~15,6 ms, o que faz o after() do tk
    atrasar e a animação oscilar. timeBeginPeriod(1) baixa para 1 ms enquanto o app roda."""
    if os.name != "nt":
        return
    try:
        import ctypes
        import atexit
        winmm = ctypes.WinDLL("winmm")
        if winmm.timeBeginPeriod(1) == 0:
            atexit.register(winmm.timeEndPeriod, 1)
    except (OSError, AttributeError):
        pass


_windows_timer_1ms()
ctk.set_appearance_mode(_load_theme())
ctk.set_default_color_theme("blue")


class EEGApp(ctk.CTk):

    SEM_PORTA = "(nenhuma porta)"
    MIN_LOADING_S = 1.0   # tempo mínimo da tela de carregamento (evita "piscar")

    def __init__(self, on_start_callback=None):
        super().__init__()
        self.on_start_callback = on_start_callback
        self.buffer = EEGBuffer()

        self.title("ICM · Monitor de Atenção")
        self.geometry("560x720")
        self.minsize(480, 640)
        self.configure(fg_color=C("bg"))

        self._current_frame = None
        self._theme_btn = None
        self._chart = None
        self._last_sel = (None, None)
        self._show_port_selector()

    # ── Infra: troca de telas e tema ──────────────────────────────────────
    def _swap_frame(self, frame):
        old, self._current_frame = self._current_frame, frame
        if old is not None:
            old.destroy()
        frame.pack(fill="both", expand=True)

    @staticmethod
    def _theme_text():
        return "☀  Claro" if _mode() == "dark" else "☾  Escuro"

    def _make_theme_button(self, parent):
        self._theme_btn = ctk.CTkButton(
            parent, text=self._theme_text(), command=self._toggle_theme,
            width=96, height=30, corner_radius=8, font=F(12),
            fg_color="transparent", hover_color=C("card"),
            border_width=1, border_color=C("border"), text_color=C("dim"),
        )
        return self._theme_btn

    def _toggle_theme(self):
        mode = "light" if _mode() == "dark" else "dark"
        ctk.set_appearance_mode(mode)
        _save_theme(mode)
        if self._theme_btn is not None:
            self._theme_btn.configure(text=self._theme_text())
        if self._chart is not None:
            self._style_chart()

    # ── Tela 1: seleção de portas ─────────────────────────────────────────
    def _show_port_selector(self, error=""):
        self._chart = None
        frame = ctk.CTkFrame(self, fg_color=C("bg"), corner_radius=0)

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 0))
        self._make_theme_button(top).pack(side="right")

        col = ctk.CTkFrame(frame, fg_color="transparent", width=380)
        col.pack(expand=True, pady=(0, 24))

        ctk.CTkLabel(col, text="ICM · Sessão", font=F(12, "bold"),
                     text_color=C("accent")).pack()
        ctk.CTkLabel(col, text="Conectar dispositivos", font=F(26, "bold"),
                     text_color=C("text")).pack(pady=(2, 4))
        ctk.CTkLabel(col, text="Selecione a porta do Arduino e o dispositivo "
                               "BrainLink antes de iniciar a sessão.",
                     font=F(12), text_color=C("dim"), wraplength=330,
                     justify="center").pack(pady=(0, 22))

        ports = self._get_ports()
        arduino_padrao, brainlink_padrao = self._portas_padrao(ports)
        last_a, last_b = self._last_sel
        if last_a in ports:
            arduino_padrao = last_a
        if last_b in ports:
            brainlink_padrao = last_b

        self._arduino_var = ctk.StringVar(value=arduino_padrao)
        self._brainlink_var = ctk.StringVar(value=brainlink_padrao)

        self._arduino_combo = self._device_card(
            col, "◈", C("violet"), "Arduino",
            "Comunicação serial · atuação dos servos", ports, self._arduino_var)
        self._brainlink_combo = self._device_card(
            col, "◉", C("accent"), "BrainLink",
            "Headset EEG · leitura de atenção", ports, self._brainlink_var)

        ctk.CTkButton(
            col, text="Atualizar portas", command=self._refresh_ports,
            height=36, corner_radius=10, font=F(12),
            fg_color="transparent", hover_color=C("card"),
            border_width=1, border_color=C("border"), text_color=C("dim"),
        ).pack(fill="x", pady=(4, 12))

        ctk.CTkButton(
            col, text="Iniciar sessão", command=self._confirm_ports,
            height=46, corner_radius=10, font=F(15, "bold"),
            fg_color=C("accent"), hover_color=C("accent_hov"),
            text_color=C("accent_txt"),
        ).pack(fill="x")

        self._error_label = ctk.CTkLabel(col, text="", font=F(12),
                                         wraplength=300, justify="center")
        self._error_label.pack(pady=(12, 0))
        self._set_hint(error, is_error=bool(error))
        frame.set_error = lambda msg: self._set_hint(msg, is_error=True)

        self._swap_frame(frame)

    def _device_card(self, parent, icon, icon_color, title, desc, ports, var):
        card = ctk.CTkFrame(parent, fg_color=C("panel"), corner_radius=14,
                            border_width=1, border_color=C("border"))
        card.pack(fill="x", pady=(0, 12))
        card.columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text=icon, width=38, height=38, corner_radius=10,
                     fg_color=C("card"), text_color=icon_color,
                     font=F(16, "bold")).grid(row=0, column=0, rowspan=2,
                                              padx=(18, 12), pady=(18, 0), sticky="n")
        ctk.CTkLabel(card, text=title, font=F(14, "bold"), text_color=C("text"),
                     anchor="w").grid(row=0, column=1, sticky="w", pady=(16, 0), padx=(0, 18))
        ctk.CTkLabel(card, text=desc, font=F(11), text_color=C("dim"),
                     anchor="w").grid(row=1, column=1, sticky="w", padx=(0, 18))

        combo = ctk.CTkOptionMenu(
            card, values=ports, variable=var, dynamic_resizing=False,
            height=34, corner_radius=8, font=F(12), dropdown_font=F(12),
            fg_color=C("card"), button_color=C("card"),
            button_hover_color=C("border"), text_color=C("text"),
            dropdown_fg_color=C("panel"), dropdown_hover_color=C("card"),
            dropdown_text_color=C("text"),
        )
        combo.grid(row=2, column=0, columnspan=2, sticky="ew", padx=18, pady=(14, 18))
        return combo

    def _set_hint(self, msg, is_error=False):
        if not msg:
            msg, is_error = "Selecione as portas para continuar", False
        self._error_label.configure(text=msg,
                                    text_color=C("danger") if is_error else C("dim"))

    def _get_ports(self):
        """Textos do menu ("COM5 - HC-05"). Guarda em self._port_map o texto -> porta ("COM5")."""
        self._port_map = {f"{porta} - {nome}": porta for porta, nome in listar_portas()}
        return list(self._port_map) or [self.SEM_PORTA]

    @staticmethod
    def _portas_padrao(ports):
        """Pré-seleciona o HC-05 para o Arduino e o BrainLink para o BrainLink, se existirem."""
        def achar(trecho, padrao):
            return next((p for p in ports if trecho.lower() in p.lower()), padrao)
        arduino   = achar("HC-05", ports[0])
        brainlink = achar("BrainLink", ports[-1] if len(ports) > 1 else ports[0])
        return arduino, brainlink

    def _refresh_ports(self):
        ports = self._get_ports()
        self._arduino_combo.configure(values=ports)
        self._brainlink_combo.configure(values=ports)
        arduino_padrao, brainlink_padrao = self._portas_padrao(ports)
        self._arduino_var.set(arduino_padrao)
        self._brainlink_var.set(brainlink_padrao)
        self._set_hint("Portas atualizadas")

    def _confirm_ports(self):
        # "COM5 - HC-05" -> "COM5": o callback recebe só a porta
        a = self._port_map.get(self._arduino_var.get())
        b = self._port_map.get(self._brainlink_var.get())
        if a is None or b is None:
            self._set_hint("Nenhuma porta serial detectada.", is_error=True)
            return
        if a == b:
            self._set_hint("Arduino e BrainLink não podem usar a mesma porta.", is_error=True)
            return

        self._last_sel = (self._arduino_var.get(), self._brainlink_var.get())
        self.arduino_port   = a
        self.brainlink_port = b
        self._show_loading(a, b)

    # ── Tela 2: carregamento (conexão roda em thread, UI não trava) ──────
    LOADING_STEPS = [
        ("brainlink", "Conectando ao BrainLink"),
        ("arduino",   "Conectando ao Arduino"),
        ("painel",    "Preparando painel"),
    ]

    def _show_loading(self, arduino_port, brainlink_port):
        frame = ctk.CTkFrame(self, fg_color=C("bg"), corner_radius=0)

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 0))
        self._make_theme_button(top).pack(side="right")

        col = ctk.CTkFrame(frame, fg_color="transparent")
        col.pack(expand=True, pady=(0, 40))

        self._spinner = ctk.CTkCanvas(col, width=72, height=72,
                                      highlightthickness=0, bd=0)
        self._spinner.pack(pady=(0, 20))
        self._spin_angle = 0

        ctk.CTkLabel(col, text="Iniciando sessão", font=F(22, "bold"),
                     text_color=C("text")).pack()
        self._loading_status = ctk.CTkLabel(col, text="Aguarde um instante…",
                                            font=F(12), text_color=C("dim"))
        self._loading_status.pack(pady=(4, 22))

        steps_card = ctk.CTkFrame(col, fg_color=C("panel"), corner_radius=14,
                                  border_width=1, border_color=C("border"))
        steps_card.pack(fill="x", ipadx=8)
        self._step_rows = {}
        for i, (key, text) in enumerate(self.LOADING_STEPS):
            row = ctk.CTkFrame(steps_card, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=(14 if i == 0 else 4, 14 if i == 2 else 4))
            icon = ctk.CTkLabel(row, text="○", width=20, font=F(13, "bold"),
                                text_color=C("dim"))
            icon.pack(side="left")
            lbl = ctk.CTkLabel(row, text=text, font=F(13), text_color=C("dim"),
                               anchor="w", width=240)
            lbl.pack(side="left", padx=(8, 0))
            self._step_rows[key] = (icon, lbl)

        self._swap_frame(frame)

        self._loading_alive = True
        self._loading_t0 = time.monotonic()
        self._conn_queue = queue.Queue()
        self._set_step("brainlink", "active")
        threading.Thread(target=self._connect_worker,
                         args=(arduino_port, brainlink_port), daemon=True).start()
        self._poll_loading()

    def _connect_worker(self, arduino_port, brainlink_port):
        q = self._conn_queue
        try:
            cb = self.on_start_callback
            if cb is None:
                res = (True, "")
            elif len(inspect.signature(cb).parameters) >= 3:
                res = cb(arduino_port, brainlink_port, lambda step: q.put(("step", step)))
            else:
                res = cb(arduino_port, brainlink_port)
        except Exception as e:  # noqa: BLE001 — qualquer falha volta para a tela de portas
            res = (False, f"Erro ao conectar: {e}")
        if isinstance(res, bool):
            res = (res, "" if res else "Falha ao conectar. Verifique as portas.")
        q.put(("done", res))

    def _set_step(self, key, status):
        icon, lbl = self._step_rows[key]
        if status == "active":
            icon.configure(text="●", text_color=C("accent"))
            lbl.configure(text_color=C("text"))
            self._loading_status.configure(
                text=dict(self.LOADING_STEPS)[key] + "…", text_color=C("dim"))
        elif status == "done":
            icon.configure(text="✓", text_color=C("accent"))
            lbl.configure(text_color=C("dim"))
        elif status == "error":
            icon.configure(text="✕", text_color=C("danger"))
            lbl.configure(text_color=C("danger"))

    def _advance_to(self, key):
        keys = [k for k, _ in self.LOADING_STEPS]
        for k in keys[:keys.index(key)]:
            self._set_step(k, "done")
        self._set_step(key, "active")
        self._active_step = key

    def _draw_spinner(self):
        c = self._spinner
        c.configure(bg=cur("bg"))
        c.delete("all")
        c.create_oval(6, 6, 66, 66, outline=cur("border"), width=5)
        c.create_arc(6, 6, 66, 66, start=self._spin_angle, extent=100,
                     style="arc", outline=cur("accent"), width=5)
        self._spin_angle = (self._spin_angle - 10) % 360

    def _poll_loading(self):
        if not self._loading_alive:
            return
        self._draw_spinner()
        self._active_step = getattr(self, "_active_step", "brainlink")
        try:
            while True:
                kind, payload = self._conn_queue.get_nowait()
                if kind == "step":
                    self._advance_to(payload)
                elif kind == "done":
                    self._on_connect_done(*payload)
                    return
        except queue.Empty:
            pass
        self.after(30, self._poll_loading)

    def _on_connect_done(self, ok, msg):
        if not ok:
            self._loading_alive = False
            self._set_step(self._active_step, "error")
            self._loading_status.configure(text=msg or "Falha ao conectar.",
                                           text_color=C("danger"))
            self.after(1600, lambda: self._show_port_selector(error=msg))
            return

        self._advance_to("painel")
        # mantém a animação até o tempo mínimo e então monta o painel
        wait_ms = max(0, int((self.MIN_LOADING_S - (time.monotonic() - self._loading_t0)) * 1000))

        def keep_spinning():
            if self._loading_alive:
                self._draw_spinner()
                self.after(30, keep_spinning)
        keep_spinning()

        def go():
            self._set_step("painel", "done")
            self.update_idletasks()
            self._show_dashboard()
        self.after(wait_ms + 120, go)

    # ── Tela 3: dashboard ─────────────────────────────────────────────────
    def _show_dashboard(self):
        frame = ctk.CTkFrame(self, fg_color=C("bg"), corner_radius=0)

        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(18, 12))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text="Monitor de Atenção", font=F(15, "bold"),
                     text_color=C("text"), anchor="w").pack(anchor="w")
        self._value_label = ctk.CTkLabel(left, text="0 / 100", font=F(30, "bold"),
                                         text_color=C("value"), anchor="w")
        self._value_label.pack(anchor="w")

        ctk.CTkButton(
            header, text="Encerrar", command=self._encerrar,
            width=96, height=32, corner_radius=8, font=F(12),
            fg_color="transparent", hover_color=C("card"),
            border_width=1, border_color=C("border"), text_color=C("dim"),
        ).pack(side="right")

        self._paused = False
        self._toggle_btn = ctk.CTkButton(
            header, text="Pausar", command=self._toggle_pause,
            width=96, height=32, corner_radius=8, font=F(12, "bold"),
            fg_color=C("card"), hover_color=C("border"), text_color=C("text"),
        )
        self._toggle_btn.pack(side="right", padx=(0, 8))

        self._make_theme_button(header).pack(side="right", padx=(0, 8))

        self._connected = True
        self._conn_label = ctk.CTkLabel(header, text="", font=F(12),
                                        text_color=C("accent"))
        self._conn_label.pack(side="right", padx=(0, 16))

        # Card do gráfico
        card = ctk.CTkFrame(frame, fg_color=C("panel"), corner_radius=16,
                            border_width=1, border_color=C("border"))
        card.pack(fill="both", expand=True, padx=28, pady=(0, 24))

        stats = ctk.CTkFrame(card, fg_color="transparent")
        stats.pack(side="bottom", fill="x", padx=24, pady=(4, 18))
        stats.columnconfigure((0, 1), weight=1, uniform="s")
        self._stats = {}
        for i, (key, name) in enumerate([("now", "Nível atual"), ("peak", "Pico"),
                                         ("avg", "Média (janela)"), ("state", "Estado")]):
            r, c = divmod(i, 2)
            cell = ctk.CTkFrame(stats, fg_color="transparent")
            cell.grid(row=r, column=c, sticky="ew",
                      padx=(0, 24) if c == 0 else (24, 0), pady=4)
            ctk.CTkLabel(cell, text=name, font=F(12), text_color=C("dim")).pack(side="left")
            val = ctk.CTkLabel(cell, text="–", font=F(12, "bold"), text_color=C("text"))
            val.pack(side="right")
            self._stats[key] = val

        self._build_chart(card)   # depois das estatísticas: o gráfico ocupa o espaço restante

        self._swap_frame(frame)
        self._loading_alive = False

        try:
            self.state("zoomed")
        except Exception:
            try:
                self.attributes("-zoomed", True)
            except Exception:
                pass
        self.minsize(760, 520)

        self._session_t0 = time.monotonic()
        self.set_connected(True)
        self._refresh()

    FRAME_S = 1 / 60   # 60 fps

    def _build_chart(self, parent):
        fig, ax = plt.subplots(figsize=(9, 4.5), dpi=100)
        fig.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0.03)
        ax.set_xlim(0, HISTORY - 1)
        ax.set_ylim(0, 105)
        ax.set_xticks(np.linspace(0, HISTORY - 1, 8)[1:-1])
        ax.set_yticks([])
        ax.tick_params(length=0, labelbottom=False)
        for spine in ax.spines.values():
            spine.set_visible(False)

        zeros = [0.0] * HISTORY
        self._chart = {
            "fig": fig, "ax": ax,
            "hist": zeros,                 # último histórico lido do buffer
            "series": [0.0] + zeros,       # histórico + 1 ponto à esquerda (sai da tela)
            "count": None,                 # contador de amostras do buffer
            "t_new": 0.0,                  # quando chegou a última amostra
            "interval": 1.0,               # intervalo médio entre amostras (s)
            "bg": None,                    # fundo em cache para o blitting
        }
        # animated=True: linha e área ficam fora do desenho completo e são
        # redesenhadas sozinhas sobre o fundo em cache (blitting) a cada quadro.
        self._chart["line"], = ax.plot([], [], linewidth=2.4, solid_capstyle="round",
                                       solid_joinstyle="round", animated=True, zorder=3)
        self._chart["fill"], = ax.fill([0, 1], [0, 0], linewidth=0, animated=True, zorder=2)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        widget = canvas.get_tk_widget()
        widget.configure(highlightthickness=0, bd=0)
        widget.pack(fill="both", expand=True, padx=16, pady=(16, 8))
        self._chart["canvas"] = canvas
        # todo desenho completo (início, redimensionar, trocar tema) recaptura o fundo
        canvas.mpl_connect("draw_event", self._on_chart_full_draw)
        self._style_chart()

    def _on_chart_full_draw(self, _event):
        ch = self._chart
        ch["bg"] = ch["canvas"].copy_from_bbox(ch["fig"].bbox)
        self._blit_chart()

    def _style_chart(self):
        ch = self._chart
        fig, ax = ch["fig"], ch["ax"]
        fig.patch.set_facecolor(cur("panel"))
        ax.set_facecolor(cur("panel"))
        ax.grid(axis="x", color=cur("grid"), linewidth=1)
        ax.grid(axis="y", visible=False)
        ch["line"].set_color(cur("accent"))
        ch["fill"].set_facecolor(cur("accent"))
        ch["fill"].set_alpha(0.22)
        ch["canvas"].get_tk_widget().configure(bg=cur("panel"))
        self._update_chart_data(force=True)
        ch["canvas"].draw()   # desenho completo -> draw_event recaptura o fundo

    def _feed_chart(self, hist, count):
        """Registra uma nova leitura do buffer. Quando chega amostra nova, começa a
        deslizar a curva um passo para a esquerda em vez de pular de uma vez."""
        ch = self._chart
        now = time.perf_counter()
        if count == ch["count"]:
            return
        if ch["count"] is not None and count == ch["count"] + 1:
            dt = now - ch["t_new"]
            ch["interval"] = 0.7 * ch["interval"] + 0.3 * min(max(dt, 0.1), 2.5)
            ch["series"] = [ch["hist"][0]] + list(hist)
            ch["t_new"] = now
        else:
            # primeira leitura ou várias amostras de uma vez: sem animação
            ch["series"] = [hist[0]] + list(hist)
            ch["t_new"] = now - 10.0
        ch["hist"] = list(hist)
        ch["count"] = count
        ch["curve"] = _smooth(ch["series"])   # a curva só muda com amostra nova

    def _update_chart_data(self, force=False):
        """Posiciona a curva no instante atual. Retorna False se nada mudou."""
        ch = self._chart
        p = _ease((time.perf_counter() - ch["t_new"]) / ch["interval"])
        if p == ch.get("drawn_p") and not force:
            return False
        ch["drawn_p"] = p

        xs, ys = ch.get("curve") or _smooth(ch["series"])
        xs = xs - p                     # desliza: em p=1 a amostra nova chega à borda direita
        ys = np.clip(ys, 0, 100)
        ch["line"].set_data(xs, ys)
        ch["fill"].set_xy(np.column_stack((
            np.concatenate(([xs[0]], xs, [xs[-1]])),
            np.concatenate(([0.0], ys, [0.0])),
        )))
        return True

    def _blit_chart(self):
        ch = self._chart
        if ch["bg"] is None:
            return
        canvas, ax = ch["canvas"], ch["ax"]
        canvas.restore_region(ch["bg"])
        ax.draw_artist(ch["fill"])
        ax.draw_artist(ch["line"])
        canvas.blit(ax.bbox)

    # ── Loop de refresh — lê APENAS do buffer (mesmos dados do console) ──
    def _refresh(self):
        t0 = time.perf_counter()
        self._update_live_label()
        if not self._paused:
            snap = self.buffer.snapshot()
            hist = snap["att_hist"]
            count = snap["count"]
            new_sample = count != self._chart["count"]
            self._feed_chart(hist, count)
            if self._update_chart_data():
                self._blit_chart()

            if new_sample:
                att = snap["attention"]   # = Att Filtrada do console
                self._value_label.configure(text=f"{round(att):d} / 100")
                window = [v for v in hist if v > 0] or [0.0]
                self._stats["now"].configure(text=f"{round(att):d}")
                self._stats["avg"].configure(text=f"{round(sum(window) / len(window)):d}")
                self._stats["peak"].configure(text=f"{round(max(window)):d}")
                self.update_state(snap["state"], snap["blocked"])

        # agenda o próximo quadro descontando o tempo gasto neste (ritmo estável)
        self._next_frame = getattr(self, "_next_frame", t0) + self.FRAME_S
        if self._next_frame < t0:          # atrasou: não tenta "recuperar" quadros
            self._next_frame = t0 + self.FRAME_S
        delay = max(1, int((self._next_frame - time.perf_counter()) * 1000))
        self.after(delay, self._refresh)

    def _update_live_label(self):
        secs = int(time.monotonic() - self._session_t0)
        clock = f"{secs // 60:02d}:{secs % 60:02d}"
        if not self._connected:
            text, color = f"● desconectado · {clock}", "danger"
        elif self._paused:
            text, color = f"● pausado · {clock}", "dim"
        else:
            text, color = f"● ao vivo · {clock}", "accent"
        if (text, color) != getattr(self, "_live_cache", None):
            self._live_cache = (text, color)
            self._conn_label.configure(text=text, text_color=C(color))

    def _toggle_pause(self):
        self._paused = not self._paused
        self._toggle_btn.configure(text="Retomar" if self._paused else "Pausar")
        self._update_live_label()

    def _encerrar(self):
        self.destroy()
        os.kill(os.getpid(), 9)

    # ── API pública ───────────────────────────────────────────────────────
    def update_state(self, state_key: str, blocked: bool):
        color, label = STATE_COLORS.get(state_key, ("#8A94A8", "?"))
        suffix = " · bloqueado" if blocked else ""
        self._stats["state"].configure(text=f"{state_key} · {label}{suffix}",
                                       text_color=color)

    def set_connected(self, ok: bool):
        self._connected = ok
        if hasattr(self, "_session_t0"):
            self._update_live_label()
