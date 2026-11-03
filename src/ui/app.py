import os
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from src.models.eeg_buffer import EEGBuffer, HISTORY
from src.utils.hardware_helpers import listar_portas

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

BG_LIGHT   = "#F4F6FB"
BG_PANEL   = "#FFFFFF"
BG_CARD    = "#EEF1F8"
ACCENT_1   = "#2563EB"
ACCENT_2   = "#7C3AED"
GRID_COLOR = "#D1D9EE"
TEXT_MAIN  = "#1E2A45"
TEXT_DIM   = "#6B7A9E"
BORDER_CLR = "#C8D0E5"

STATE_COLORS = {
    "A": ("#EF4444", "DISTRACAO"),
    "B": ("#6B7A9E", "NEUTRO"),
    "C": ("#0D9488", "FOCO LEVE"),
    "D": ("#2563EB", "FOCO ALTO"),
    "E": ("#7C3AED", "FOCO MAXIMO"),
}


def _apply_light_style(ax, ylabel=""):
    ax.set_facecolor(BG_PANEL)
    ax.tick_params(colors=TEXT_DIM, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(BORDER_CLR)
    ax.grid(color=GRID_COLOR, linewidth=0.5, alpha=0.8, linestyle="--")
    if ylabel:
        ax.set_ylabel(ylabel, color=TEXT_DIM, fontsize=8, fontfamily="monospace")


class EEGApp(ctk.CTk):

    def __init__(self, on_start_callback=None):
        super().__init__()
        self.on_start_callback = on_start_callback
        self.buffer = EEGBuffer()

        self.title("EEG Neural Monitor")
        self.geometry("440x420")
        self.configure(fg_color=BG_LIGHT)
        self.resizable(False, False)

        self._current_frame = None
        self._show_port_selector()

    # ── Tela de seleção de porta ──────────────────────────────────────────
    def _show_port_selector(self):
        if self._current_frame:
            self._current_frame.destroy()

        frame = ctk.CTkFrame(self, fg_color=BG_LIGHT)
        frame.pack(fill="both", expand=True)
        self._current_frame = frame

        ctk.CTkLabel(frame, text="EEG NEURAL",
            font=ctk.CTkFont(family="Courier New", size=22, weight="bold"),
            text_color=ACCENT_1,
        ).pack(pady=(32, 2))

        ctk.CTkLabel(frame, text="configuracao de portas seriais",
            font=ctk.CTkFont(family="Courier New", size=10),
            text_color=TEXT_DIM,
        ).pack(pady=(0, 28))

        card = ctk.CTkFrame(frame, fg_color=BG_PANEL, corner_radius=14,
                            border_width=1, border_color=BORDER_CLR)
        card.pack(padx=32, fill="x")

        ports = self._get_ports()

        ctk.CTkLabel(card, text="ARDUINO",
            font=ctk.CTkFont(family="Courier New", size=10, weight="bold"),
            text_color=ACCENT_1,
        ).pack(anchor="w", padx=22, pady=(20, 4))

        arduino_padrao, brainlink_padrao = self._portas_padrao(ports)

        self._arduino_var = ctk.StringVar(value=arduino_padrao)
        self._arduino_combo = ctk.CTkOptionMenu(
            card, values=ports, variable=self._arduino_var,
            fg_color=BG_CARD, button_color=ACCENT_1, button_hover_color="#1D4ED8",
            dropdown_fg_color=BG_PANEL, text_color=TEXT_MAIN,
            font=ctk.CTkFont(family="Courier New", size=12), width=360,
        )
        self._arduino_combo.pack(padx=22, pady=(0, 16))

        ctk.CTkFrame(card, fg_color=BORDER_CLR, height=1).pack(fill="x", padx=22)

        ctk.CTkLabel(card, text="BRAINLINK",
            font=ctk.CTkFont(family="Courier New", size=10, weight="bold"),
            text_color=ACCENT_2,
        ).pack(anchor="w", padx=22, pady=(16, 4))

        self._brainlink_var = ctk.StringVar(value=brainlink_padrao)
        self._brainlink_combo = ctk.CTkOptionMenu(
            card, values=ports, variable=self._brainlink_var,
            fg_color=BG_CARD, button_color=ACCENT_2, button_hover_color="#6D28D9",
            dropdown_fg_color=BG_PANEL, text_color=TEXT_MAIN,
            font=ctk.CTkFont(family="Courier New", size=12), width=360,
        )
        self._brainlink_combo.pack(padx=22, pady=(0, 20))

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(pady=24, fill="x", padx=32)

        ctk.CTkButton(btn_row, text="ATUALIZAR",
            fg_color=BG_CARD, hover_color=GRID_COLOR, text_color=TEXT_DIM,
            font=ctk.CTkFont(family="Courier New", size=11),
            width=120, corner_radius=8, command=self._refresh_ports,
        ).pack(side="left")

        ctk.CTkButton(btn_row, text="INICIAR",
            fg_color=ACCENT_1, hover_color="#1D4ED8", text_color="#FFFFFF",
            font=ctk.CTkFont(family="Courier New", size=13, weight="bold"),
            width=180, corner_radius=8, command=self._confirm_ports,
        ).pack(side="right")

        self._error_label = ctk.CTkLabel(frame, text="",
            font=ctk.CTkFont(family="Courier New", size=10),
            text_color="#EF4444",
        )
        self._error_label.pack()
        frame.set_error = lambda msg: self._error_label.configure(text=msg)

    SEM_PORTA = "(nenhuma porta)"

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
        self._error_label.configure(text="portas atualizadas")

    def _confirm_ports(self):
        # "COM5 - HC-05" -> "COM5": o callback recebe só a porta
        a = self._port_map.get(self._arduino_var.get())
        b = self._port_map.get(self._brainlink_var.get())
        if a is None or b is None:
            self._error_label.configure(text="Nenhuma porta serial detectada.")
            return
        if a == b:
            self._error_label.configure(
                text="Arduino e BrainLink nao podem usar a mesma porta.")
            return

        self.arduino_port   = a
        self.brainlink_port = b

        if self.on_start_callback:
            ok = self.on_start_callback(a, b)
            if not ok:
                self._error_label.configure(
                    text="Falha ao conectar. Verifique as portas.")
                return

        self._show_dashboard()

    # ── Dashboard ─────────────────────────────────────────────────────────
    def _show_dashboard(self):
        if self._current_frame:
            self._current_frame.destroy()

        try:
            self.state('zoomed')
        except Exception:
            self.attributes('-zoomed', True)
        self.resizable(True, True)
        self.minsize(760, 520)

        frame = ctk.CTkFrame(self, fg_color=BG_LIGHT)
        frame.pack(fill="both", expand=True)
        self._current_frame = frame

        # Header
        header = ctk.CTkFrame(frame, fg_color=BG_PANEL, corner_radius=0,
                               height=56, border_width=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="NEURAL EEG MONITOR",
            font=ctk.CTkFont(family="Courier New", size=16, weight="bold"),
            text_color=ACCENT_1,
        ).pack(side="left", padx=24, pady=16)

        self._state_label = ctk.CTkLabel(header,
            text="ESTADO  B  -  NEUTRO",
            font=ctk.CTkFont(family="Courier New", size=11),
            text_color=TEXT_DIM,
        )
        self._state_label.pack(side="right", padx=24)

        self._conn_label = ctk.CTkLabel(header, text="● CONECTADO",
            font=ctk.CTkFont(family="Courier New", size=10),
            text_color="#0D9488",
        )
        self._conn_label.pack(side="right", padx=12)

        ctk.CTkButton(header, text="ENCERRAR",
            fg_color=BG_CARD, hover_color=GRID_COLOR, text_color=TEXT_DIM,
            font=ctk.CTkFont(family="Courier New", size=11),
            width=120, corner_radius=8, command=self._encerrar,
        ).pack(side="right", padx=(0, 12), pady=12)

        self._paused = False
        self._toggle_btn = ctk.CTkButton(header, text="PAUSAR",
            fg_color=ACCENT_1, hover_color="#1D4ED8", text_color="#FFFFFF",
            font=ctk.CTkFont(family="Courier New", size=13, weight="bold"),
            width=140, corner_radius=8, command=self._toggle_pause,
        )
        self._toggle_btn.pack(side="right", padx=(0, 6), pady=12)

        ctk.CTkFrame(frame, fg_color=BORDER_CLR, height=1).pack(fill="x")

        # Body
        body = ctk.CTkFrame(frame, fg_color=BG_LIGHT)
        body.pack(fill="both", expand=True, padx=16, pady=14)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # Coluna esquerda
        left = ctk.CTkFrame(body, fg_color=BG_PANEL, corner_radius=14,
                            border_width=1, border_color=BORDER_CLR)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(left, text="VALORES ATUAIS",
            font=ctk.CTkFont(family="Courier New", size=10, weight="bold"),
            text_color=TEXT_DIM,
        ).pack(pady=(18, 12), padx=20, anchor="w")

        cards_row = ctk.CTkFrame(left, fg_color="transparent")
        cards_row.pack(fill="x", padx=16)
        self._att_label = self._metric_card(cards_row, "ATT FILTRADA", ACCENT_1, "#EFF6FF")
        self._med_label = self._metric_card(cards_row, "MEDITACAO",    ACCENT_2, "#F5F3FF")

        ctk.CTkFrame(left, fg_color=BORDER_CLR, height=1).pack(fill="x", padx=16, pady=16)

        ctk.CTkLabel(left, text="COMPARATIVO",
            font=ctk.CTkFont(family="Courier New", size=10, weight="bold"),
            text_color=TEXT_DIM,
        ).pack(pady=(0, 8), padx=20, anchor="w")

        self._build_bar_panel(left)

        # Coluna direita
        right = ctk.CTkFrame(body, fg_color=BG_PANEL, corner_radius=14,
                              border_width=1, border_color=BORDER_CLR)
        right.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(right, text="HISTORICO (tempo real)",
            font=ctk.CTkFont(family="Courier New", size=10, weight="bold"),
            text_color=TEXT_DIM,
        ).pack(pady=(18, 0), padx=20, anchor="w")

        legend = ctk.CTkFrame(right, fg_color="transparent")
        legend.pack(anchor="w", padx=20, pady=(4, 0))
        for label, color in [("  ● Att Filtrada", ACCENT_1),
                              ("  ● Meditacao",   ACCENT_2)]:
            ctk.CTkLabel(legend, text=label,
                font=ctk.CTkFont(family="Courier New", size=9),
                text_color=color,
            ).pack(side="left")

        self._build_history_panel(right)

        self._refresh()

    def _metric_card(self, parent, label, color, bg):
        card = ctk.CTkFrame(parent, fg_color=bg, corner_radius=10)
        card.pack(side="left", expand=True, fill="both", padx=4, pady=4)
        ctk.CTkLabel(card, text=label,
            font=ctk.CTkFont(family="Courier New", size=8, weight="bold"),
            text_color=color,
        ).pack(pady=(12, 0))
        val = ctk.CTkLabel(card, text="0.0",
            font=ctk.CTkFont(family="Courier New", size=30, weight="bold"),
            text_color=color,
        )
        val.pack(pady=(0, 12))
        return val

    def _build_bar_panel(self, parent):
        fig, ax = plt.subplots(figsize=(3.8, 2.6), dpi=100)
        fig.patch.set_facecolor(BG_PANEL)
        fig.subplots_adjust(left=0.14, right=0.96, top=0.88, bottom=0.12)
        _apply_light_style(ax)

        self._bars = ax.bar(
            ["ATT FILT.", "MEDIT."], [0, 0],
            color=[ACCENT_1, ACCENT_2], width=0.5, edgecolor="none", zorder=3,
        )
        ax.set_ylim(0, 100)
        ax.set_xlim(-0.6, 1.6)
        ax.tick_params(colors=TEXT_DIM, labelsize=8)

        self._bar_texts = [
            ax.text(0, 2, "0.0", ha="center", va="bottom",
                    color=ACCENT_1, fontsize=13, fontweight="bold",
                    fontfamily="monospace"),
            ax.text(1, 2, "0.0", ha="center", va="bottom",
                    color=ACCENT_2, fontsize=13, fontweight="bold",
                    fontfamily="monospace"),
        ]

        self._bar_canvas = FigureCanvasTkAgg(fig, master=parent)
        self._bar_canvas.get_tk_widget().pack(
            fill="both", expand=True, padx=8, pady=(0, 12))

    def _build_history_panel(self, parent):
        fig, axes = plt.subplots(2, 1, figsize=(7, 4.8), dpi=100, sharex=True)
        fig.patch.set_facecolor(BG_PANEL)
        fig.subplots_adjust(
            left=0.09, right=0.97, top=0.94, bottom=0.08, hspace=0.12)

        x = np.arange(HISTORY)
        self._hist_lines = {}
        self._hist_fills = {}
        self._hist_axes  = axes

        configs = [
            ("attention",  "ATT FILTRADA", ACCENT_1),
            ("meditation", "MEDITACAO",    ACCENT_2),
        ]

        for ax, (key, label, color) in zip(axes, configs):
            _apply_light_style(ax, ylabel=label)
            line, = ax.plot(x, [0] * HISTORY, color=color,
                            linewidth=1.6, alpha=0.9, zorder=3)
            fill  = ax.fill_between(x, [0] * HISTORY, color=color, alpha=0.10)
            ax.set_xlim(0, HISTORY - 1)
            ax.set_ylim(0, 105)
            self._hist_lines[key] = line
            self._hist_fills[key] = fill

        self._hist_x = x
        self._hist_canvas = FigureCanvasTkAgg(fig, master=parent)
        self._hist_canvas.get_tk_widget().pack(
            fill="both", expand=True, padx=8, pady=(4, 12))

    # ── Loop de refresh — lê APENAS do buffer (mesmos dados do console) ──
    def _refresh(self):
        if not self._paused:
            snap = self.buffer.snapshot()
            att  = snap["attention"]   # = Att Filtrada do console
            med  = snap["meditation"]
            state   = snap["state"]
            blocked = snap["blocked"]

            # Barras
            for bar, val in zip(self._bars, [att, med]):
                bar.set_height(min(val, 100))
            for txt, val in zip(self._bar_texts, [att, med]):
                txt.set_text(f"{val:.1f}")
                txt.set_y(min(val, 100) + 2)
            self._bar_canvas.draw_idle()

            # Histórico
            for key, ax in zip(["attention", "meditation"], self._hist_axes):
                y = snap["att_hist"] if key == "attention" else snap["med_hist"]
                self._hist_lines[key].set_ydata(y)
                self._hist_fills[key].remove()
                color = ACCENT_1 if key == "attention" else ACCENT_2
                self._hist_fills[key] = ax.fill_between(
                    self._hist_x, y, color=color, alpha=0.10)
            self._hist_canvas.draw_idle()

            # Labels numéricos
            self._att_label.configure(text=f"{att:.1f}")
            self._med_label.configure(text=f"{med:.1f}")

            # Estado no header — espelha exatamente o console
            self.update_state(state, blocked)

        self.after(100, self._refresh)

    def _toggle_pause(self):
        self._paused = not self._paused
        label = "RETOMAR" if self._paused else "PAUSAR"
        self._toggle_btn.configure(text=label)

    def _encerrar(self):
        self.destroy()
        os.kill(os.getpid(), 9)

    # ── API pública ───────────────────────────────────────────────────────
    def update_state(self, state_key: str, blocked: bool):
        color, label = STATE_COLORS.get(state_key, ("#6B7A9E", "?"))
        suffix = "  BLOQUEADO" if blocked else ""
        self._state_label.configure(
            text=f"ESTADO  {state_key}  -  {label}{suffix}",
            text_color=color,
        )

    def set_connected(self, ok: bool):
        if ok:
            self._conn_label.configure(text="● CONECTADO",    text_color="#0D9488")
        else:
            self._conn_label.configure(text="● DESCONECTADO", text_color="#EF4444")

