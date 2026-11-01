import ctypes
import json
import os
import sys
import time
import tkinter as tk
from collections import deque

# Faz as coordenadas baterem com os pixels reais (resolve escala 125%/150% do Windows)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

import keyboard
import mss
import numpy as np
import pyautogui

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

BASE = (
    os.path.dirname(sys.executable)
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)
CONFIG = os.path.join(BASE, "config.json")

DEFAULTS = {
    "x": 0,
    "y": 0,
    "largura": 70,
    "espessura": 3,
    "sens_pct": 15,
    "limite_branco": 190,
    "intervalo": 1.0,
    "botao": "right",
    "desligar_apos_clique": True,
    "mostrar_linha": True,
    "sempre_no_topo": True,
}

# ------------------------------------------------------------------ cores
BG = "#0e1014"
CARD = "#161920"
LINE = "#252a36"
TXT = "#e8eaf0"
MUTED = "#8a92a6"
ACC = "#4f8cff"
OK = "#22c55e"
BAD = "#ef4444"
WARN = "#f59e0b"
OFF = "#2a2f3c"
FONT = ("Segoe UI", 10)
FONT_S = ("Segoe UI", 9)
FONT_B = ("Segoe UI", 10, "bold")

CELULAS = 48          # quadradinhos da "visão da linha"
LARG_VISAO = 288


def analisar(img_bgr, limite_branco):
    """Classifica cada pixel da linha.

    - preto/escuro (divisórias e contorno da barra): ignorado
    - branco (inclui o cinza claro das marquinhas): barra ainda "vazia"
    - qualquer outra coisa: COR (a barra passou por ali)

    Retorna (pixels_coloridos, pixels_brancos, total).
    """
    img = img_bgr[..., :3]
    maximo = img.max(axis=2)
    minimo = img.min(axis=2)
    escuro = maximo < 70
    branco = (minimo >= limite_branco) & ~escuro
    colorido = ~(escuro | branco)
    return int(colorido.sum()), int(branco.sum()), int(maximo.size)


class App:
    def __init__(self):
        self.cfg = DEFAULTS.copy()
        try:
            with open(CONFIG, "r", encoding="utf-8") as f:
                self.cfg.update(json.load(f))
        except Exception:
            pass

        self.root = tk.Tk()
        self.root.title("Auto Clicker de Barra")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.ligado = False
        self.pronto = False        # linha ficou branca por tempo suficiente -> pode disparar
        self.t_branco = None       # desde quando a linha está branca
        self.ultimo_clique = 0.0
        self.cliques = 0
        self.posicionada = self.cfg["x"] != 0 or self.cfg["y"] != 0
        self.contando = False
        self.acoes = deque()
        self.ultimo_ui = 0.0
        self.ov_estado = None
        self.ov_visivel = False
        self.sct = mss.mss()

        # variáveis da interface
        self.v_x = tk.IntVar(value=self.cfg["x"])
        self.v_y = tk.IntVar(value=self.cfg["y"])
        self.v_w = tk.IntVar(value=self.cfg["largura"])
        self.v_h = tk.IntVar(value=self.cfg["espessura"])
        self.v_sens = tk.IntVar(value=self.cfg["sens_pct"])
        self.v_branco = tk.IntVar(value=self.cfg["limite_branco"])
        self.v_int = tk.DoubleVar(value=self.cfg["intervalo"])
        self.v_btn = tk.StringVar(value=self.cfg["botao"])
        self.v_auto = tk.BooleanVar(value=self.cfg["desligar_apos_clique"])
        self.v_show = tk.BooleanVar(value=self.cfg["mostrar_linha"])
        self.v_top = tk.BooleanVar(value=self.cfg["sempre_no_topo"])

        self.montar_ui()
        self.criar_overlay()
        self.registrar_atalhos()

        self.root.attributes("-topmost", self.v_top.get())
        self.escurecer_barra_titulo()
        self.root.protocol("WM_DELETE_WINDOW", self.fechar)
        self.tick()

    # ------------------------------------------------------- helpers de UI
    def botao(self, parent, texto, cmd, cor=LINE, fg=TXT):
        return tk.Button(
            parent, text=texto, command=cmd, bg=cor, fg=fg,
            activebackground=ACC, activeforeground="white",
            relief="flat", bd=0, padx=10, pady=7, font=FONT, cursor="hand2",
        )

    def card(self, parent, titulo):
        borda = tk.Frame(parent, bg=LINE)
        borda.pack(fill="x", padx=14, pady=(0, 10))
        dentro = tk.Frame(borda, bg=CARD)
        dentro.pack(fill="both", expand=True, padx=1, pady=1)
        tk.Label(
            dentro, text=titulo.upper(), bg=CARD, fg=MUTED, font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", padx=12, pady=(10, 4))
        corpo = tk.Frame(dentro, bg=CARD)
        corpo.pack(fill="x", padx=12, pady=(0, 12))
        return corpo

    def campo(self, parent, row, col, rotulo, var, de, ate, passo=1, padx=(0, 0)):
        tk.Label(parent, text=rotulo, bg=CARD, fg=MUTED, font=FONT_S).grid(
            row=row, column=col, sticky="w", pady=3, padx=padx
        )
        tk.Spinbox(
            parent, from_=de, to=ate, increment=passo, textvariable=var, width=6,
            bg=BG, fg=TXT, insertbackground=TXT, buttonbackground=LINE,
            relief="flat", highlightthickness=1, highlightbackground=LINE,
            highlightcolor=ACC, font=FONT,
        ).grid(row=row, column=col + 1, sticky="e", padx=(8, 0), pady=3)

    def check(self, parent, texto, var, cmd=None):
        return tk.Checkbutton(
            parent, text=texto, variable=var, command=cmd, bg=CARD, fg=TXT,
            selectcolor=BG, activebackground=CARD, activeforeground=TXT,
            bd=0, highlightthickness=0, font=FONT_S, anchor="w",
        )

    def escurecer_barra_titulo(self):
        try:
            self.root.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            v = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(v), 4)
        except Exception:
            pass

    # ------------------------------------------------------------------ UI
    def montar_ui(self):
        r = self.root

        # cabeçalho
        cab = tk.Frame(r, bg=BG)
        cab.pack(fill="x", padx=14, pady=(14, 10))
        tk.Label(cab, text="Auto Clicker", bg=BG, fg=TXT, font=("Segoe UI", 15, "bold")).pack(side="left")
        self.pill = tk.Label(
            cab, text="●  DESLIGADO", bg=OFF, fg=MUTED, font=("Segoe UI", 9, "bold"), padx=10, pady=3
        )
        self.pill.pack(side="right")

        self.btn_toggle = self.botao(r, "Ligar  (F6)", self.alternar, cor=ACC, fg="white")
        self.btn_toggle.config(font=FONT_B, pady=9)
        self.btn_toggle.pack(fill="x", padx=14, pady=(0, 8))

        self.lbl_estado = tk.Label(
            r, text="Posicione a linha na barra (F7)", bg=BG, fg=MUTED,
            font=FONT_S, wraplength=290, justify="left",
        )
        self.lbl_estado.pack(anchor="w", padx=14, pady=(0, 12))

        # linha
        c1 = self.card(r, "Linha de detecção")
        c1.grid_columnconfigure(1, weight=1)
        c1.grid_columnconfigure(3, weight=1)
        self.btn_pos = self.botao(c1, "Capturar posição do mouse  (F7)", self.iniciar_contagem)
        self.btn_pos.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 8))
        self.campo(c1, 1, 0, "X", self.v_x, 0, 10000)
        self.campo(c1, 1, 2, "Y", self.v_y, 0, 10000, padx=(16, 0))
        self.campo(c1, 2, 0, "Largura", self.v_w, 5, 1000)
        self.campo(c1, 2, 2, "Espessura", self.v_h, 1, 50, padx=(16, 0))
        aj = tk.Frame(c1, bg=CARD)
        aj.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        aj.grid_columnconfigure(0, weight=1)
        aj.grid_columnconfigure(1, weight=1)
        self.botao(aj, "▲  Subir  (F8)", lambda: self.mover(-2)).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.botao(aj, "▼  Descer  (F9)", lambda: self.mover(2)).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # visão da linha
        c2 = self.card(r, "O que a linha está vendo")
        self.cv = tk.Canvas(
            c2, width=LARG_VISAO, height=26, bg=BG, highlightthickness=1, highlightbackground=LINE
        )
        self.cv.pack(anchor="w")
        larg_cel = LARG_VISAO / CELULAS
        self.celulas = [
            self.cv.create_rectangle(i * larg_cel, 0, (i + 1) * larg_cel, 26, fill=BG, width=0)
            for i in range(CELULAS)
        ]
        self.lbl_live = tk.Label(c2, text="—", bg=CARD, fg=MUTED, font=FONT_S)
        self.lbl_live.pack(anchor="w", pady=(6, 0))

        # disparo
        c3 = self.card(r, "Disparo")
        c3.grid_columnconfigure(1, weight=1)
        self.campo(c3, 0, 0, "Sensibilidade (% da linha)", self.v_sens, 1, 100)
        self.campo(c3, 1, 0, "Limite do branco (0-255)", self.v_branco, 50, 255)
        self.campo(c3, 2, 0, "Intervalo entre cliques (s)", self.v_int, 0.1, 10, passo=0.1)

        tk.Label(c3, text="Botão do mouse", bg=CARD, fg=MUTED, font=FONT_S).grid(
            row=3, column=0, sticky="w", pady=(6, 0)
        )
        bt = tk.Frame(c3, bg=CARD)
        bt.grid(row=3, column=1, sticky="e", pady=(6, 0))
        for txt, val in (("Direito", "right"), ("Esquerdo", "left")):
            tk.Radiobutton(
                bt, text=txt, value=val, variable=self.v_btn, bg=CARD, fg=TXT,
                selectcolor=BG, activebackground=CARD, activeforeground=TXT,
                bd=0, highlightthickness=0, font=FONT_S,
            ).pack(side="left", padx=(8, 0))

        opc = tk.Frame(c3, bg=CARD)
        opc.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.check(opc, "Desligar sozinho depois do primeiro clique", self.v_auto).pack(anchor="w")
        self.check(opc, "Mostrar linha na tela", self.v_show).pack(anchor="w")
        self.check(
            opc, "Manter esta janela sempre no topo", self.v_top,
            cmd=lambda: self.root.attributes("-topmost", self.v_top.get()),
        ).pack(anchor="w")

        tk.Label(
            r, text="F6 liga/desliga  •  F7 captura  •  F8/F9 ajusta a linha",
            bg=BG, fg=MUTED, font=("Segoe UI", 8),
        ).pack(pady=(0, 12))

    def visual_ligado(self):
        if self.ligado:
            self.pill.config(text="●  LIGADO", bg=OK, fg="white")
            self.btn_toggle.config(text="Desligar  (F6)", bg=BAD, activebackground=BAD)
        else:
            self.pill.config(text="●  DESLIGADO", bg=OFF, fg=MUTED)
            self.btn_toggle.config(text="Ligar  (F6)", bg=ACC, activebackground=ACC)

    # ------------------------------------------------------------- overlay
    def criar_overlay(self):
        self.ov = tk.Toplevel(self.root)
        self.ov.overrideredirect(True)
        self.ov.attributes("-topmost", True)
        self.ov.configure(bg="red")
        self.ov.geometry("1x1+0+0")
        self.ov.update_idletasks()
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetParent(self.ov.winfo_id()) or self.ov.winfo_id()
            estilo = user32.GetWindowLongW(hwnd, -20)
            # layered + transparent (click-through) + toolwindow + NOACTIVATE (nunca rouba o foco do jogo)
            user32.SetWindowLongW(hwnd, -20, estilo | 0x80000 | 0x20 | 0x80 | 0x08000000)
        except Exception:
            pass
        self.ov.withdraw()

    # ------------------------------------------------------------- atalhos
    def registrar_atalhos(self):
        # os atalhos rodam em outra thread, então só enfileiramos a ação
        keyboard.add_hotkey("F6", lambda: self.acoes.append("toggle"))
        keyboard.add_hotkey("F7", lambda: self.acoes.append("pos"))
        keyboard.add_hotkey("F8", lambda: self.acoes.append("up"))
        keyboard.add_hotkey("F9", lambda: self.acoes.append("down"))

    def processar_acoes(self):
        while self.acoes:
            a = self.acoes.popleft()
            if a == "toggle":
                self.alternar()
            elif a == "pos":
                self.capturar()
            elif a == "up":
                self.mover(-2)
            elif a == "down":
                self.mover(2)

    # ------------------------------------------------------------- helpers
    @staticmethod
    def ler(var, padrao):
        try:
            return var.get()
        except Exception:
            return padrao

    def mover(self, dy):
        self.v_y.set(max(0, self.ler(self.v_y, 0) + dy))

    def capturar(self):
        p = pyautogui.position()
        self.v_x.set(p.x)
        self.v_y.set(p.y)
        self.posicionada = True

    def iniciar_contagem(self):
        if self.contando:
            return
        self.contando = True
        self.contagem(3)

    def contagem(self, n):
        if n > 0:
            self.btn_pos.config(text=f"Leve o mouse até a barra...  {n}")
            self.root.after(1000, lambda: self.contagem(n - 1))
        else:
            self.capturar()
            self.btn_pos.config(text="Capturar posição do mouse  (F7)")
            self.contando = False

    def alternar(self):
        if not self.posicionada:
            self.lbl_estado.config(text="Posicione a linha primeiro (F7)!", fg=WARN)
            return
        self.ligado = not self.ligado
        self.visual_ligado()

    def clicar(self):
        btn = self.v_btn.get()
        pyautogui.mouseDown(button=btn)
        time.sleep(0.03)
        pyautogui.mouseUp(button=btn)

    def desenhar_visao(self, img):
        w = img.shape[1]
        bordas = np.linspace(0, w, CELULAS + 1).astype(int)
        for i, item in enumerate(self.celulas):
            a = bordas[i]
            b = max(bordas[i + 1], a + 1)
            m = img[:, a:b, :3].reshape(-1, 3).mean(axis=0)  # BGR
            self.cv.itemconfig(item, fill="#%02x%02x%02x" % (int(m[2]), int(m[1]), int(m[0])))

    # --------------------------------------------------------------- laço
    def tick(self):
        # qualquer erro num ciclo NÃO pode matar o laço
        try:
            self._passo()
        except Exception as e:
            print("Erro no ciclo:", repr(e))
            try:
                self.lbl_estado.config(text=f"Erro: {e}", fg=BAD)
            except Exception:
                pass
        finally:
            self.root.after(5, self.tick)

    def _passo(self):
        self.processar_acoes()
        if not self.posicionada:
            return

        x = self.ler(self.v_x, 0)
        y = self.ler(self.v_y, 0)
        w = max(5, self.ler(self.v_w, 70))
        h = max(1, self.ler(self.v_h, 3))
        sens = min(100, max(1, self.ler(self.v_sens, 15)))
        limite = min(255, max(0, self.ler(self.v_branco, 190)))
        intervalo = max(0.1, self.ler(self.v_int, 1.0))
        left = x - w // 2

        # desenha a linha logo ACIMA da área detectada (só mexe na janela quando algo muda)
        if self.v_show.get():
            est = (w, h, left, max(0, y - h - 1), self.ligado)
            if est != self.ov_estado:
                self.ov.geometry(f"{w}x{h}+{left}+{max(0, y - h - 1)}")
                self.ov.configure(bg="lime" if self.ligado else "red")
                if not self.ov_visivel:
                    self.ov.deiconify()
                    self.ov_visivel = True
                self.ov_estado = est
        elif self.ov_visivel:
            self.ov.withdraw()
            self.ov_visivel = False
            self.ov_estado = None

        # lê a linha
        try:
            img = np.array(self.sct.grab({"left": left, "top": y, "width": w, "height": h}))
        except Exception:
            # captura falhou: recria o capturador e tenta de novo no próximo ciclo
            try:
                self.sct = mss.mss()
            except Exception:
                pass
            return

        coloridos, brancos, total = analisar(img, limite)
        mudou = coloridos * 100 >= sens * total     # a linha mostra COR (qualquer uma)
        agora = time.time()

        if mudou:
            # passou de branco para cor -> dispara (só se estava branca e estável antes)
            if self.ligado and self.pronto and agora - self.ultimo_clique > intervalo:
                self.clicar()
                self.cliques += 1
                self.ultimo_clique = agora
                if self.v_auto.get():
                    self.ligado = False
                    self.visual_ligado()
            self.pronto = False
            self.t_branco = None
        else:
            # linha branca: depois de um instante estável, fica pronta para disparar
            if self.t_branco is None:
                self.t_branco = agora
            if agora - self.t_branco >= 0.15:
                self.pronto = True

        # atualiza o painel ~10x por segundo
        if agora - self.ultimo_ui > 0.1:
            self.ultimo_ui = agora
            self.desenhar_visao(img)
            pct_cor = coloridos * 100 // total
            pct_branco = brancos * 100 // total
            self.lbl_live.config(text=f"Cor: {pct_cor}% da linha   •   Branco: {pct_branco}%")

            if not self.ligado:
                txt, cor = f"Desligado  •  cliques: {self.cliques}", MUTED
            elif self.pronto:
                txt, cor = f"Pronto: clica quando a linha mudar de cor  •  cliques: {self.cliques}", OK
            elif mudou:
                txt, cor = f"Esperando a linha voltar a ficar branca  •  cliques: {self.cliques}", WARN
            else:
                txt, cor = f"Confirmando que a linha está branca…  •  cliques: {self.cliques}", WARN
            self.lbl_estado.config(text=txt, fg=cor)

    # --------------------------------------------------------------- saída
    def fechar(self):
        try:
            self.cfg.update({
                "x": self.ler(self.v_x, 0),
                "y": self.ler(self.v_y, 0),
                "largura": self.ler(self.v_w, 70),
                "espessura": self.ler(self.v_h, 3),
                "sens_pct": self.ler(self.v_sens, 15),
                "limite_branco": self.ler(self.v_branco, 190),
                "intervalo": self.ler(self.v_int, 1.0),
                "botao": self.v_btn.get(),
                "desligar_apos_clique": self.v_auto.get(),
                "mostrar_linha": self.v_show.get(),
                "sempre_no_topo": self.v_top.get(),
            })
            with open(CONFIG, "w", encoding="utf-8") as f:
                json.dump(self.cfg, f, indent=2)
        except Exception:
            pass
        keyboard.unhook_all()
        self.root.destroy()

    def rodar(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().rodar()
