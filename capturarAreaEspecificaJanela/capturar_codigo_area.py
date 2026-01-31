import time
import mss
import mss.tools
import pygetwindow as gw

TITLE_CONTAINS = "WLO"

# ====== RECORTE DENTRO DA JANELA (RELATIVO) ======
# Ajuste depois que você testar (é a “caixinha” onde fica o código)
# x/y = posição dentro da janela
# w/h = tamanho do recorte
CROP_X = 0
CROP_Y = 25
CROP_W = 200
CROP_H = 150

def find_first_window():
    for w in gw.getAllWindows():
        title = (w.title or "").strip()
        if title and TITLE_CONTAINS.lower() in title.lower():
            if w.width > 0 and w.height > 0 and not w.isMinimized:
                return w
    return None

target = find_first_window()
if not target:
    print(f"Nenhuma janela encontrada contendo '{TITLE_CONTAINS}' (ou está minimizada).")
    exit(1)

# Pequena pausa só pra garantir coordenadas estáveis
time.sleep(0.1)

# Região da tela = janela inteira
window_region = {
    "left": target.left,
    "top": target.top,
    "width": target.width,
    "height": target.height
}

# Região do código = janela + deslocamento interno
code_region = {
    "left": target.left + CROP_X,
    "top": target.top + CROP_Y,
    "width": CROP_W,
    "height": CROP_H
}

with mss.mss() as sct:
    img_window = sct.grab(window_region)
    mss.tools.to_png(img_window.rgb, img_window.size, output="janela_jogo.png")

    img_code = sct.grab(code_region)
    mss.tools.to_png(img_code.rgb, img_code.size, output="codigo_area.png")

print("Salvou: janela_jogo.png e codigo_area.png")
print(f"Janela: ({target.left},{target.top}) {target.width}x{target.height}")
print(f"Recorte: X={CROP_X}, Y={CROP_Y}, W={CROP_W}, H={CROP_H}")