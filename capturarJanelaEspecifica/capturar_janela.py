import time
import mss
import mss.tools
import pygetwindow as gw

# Coloque aqui um pedaço do título da janela do jogo:
TITLE_CONTAINS = "WLO Rhodes Island"   # exemplo: "WLO" ou "Wonderland" ou o nome exato

def find_windows():
    result = []
    for w in gw.getAllWindows():
        title = (w.title or "").strip()
        if title and TITLE_CONTAINS.lower() in title.lower():
            if w.width > 0 and w.height > 0:
                result.append(w)
    return result

wins = find_windows()

if not wins:
    print(f"Nenhuma janela encontrada contendo: '{TITLE_CONTAINS}'")
    exit(1)

print("Janelas encontradas:")
for i, w in enumerate(wins):
    print(f"[{i}] '{w.title}' | ({w.left},{w.top}) {w.width}x{w.height}")

# Se tiver mais de uma, por enquanto vamos pegar a primeira
target = wins[0]

# garante que não está minimizada
if target.isMinimized:
    print("A janela está minimizada. Restaure ela e rode de novo.")
    exit(1)

# dá uma pausa só pra garantir que coordenadas estão OK
time.sleep(0.2)

region = {
    "left": target.left,
    "top": target.top,
    "width": target.width,
    "height": target.height
}

with mss.mss() as sct:
    img = sct.grab(region)
    mss.tools.to_png(img.rgb, img.size, output="janela_jogo.png")

print("Salvou: janela_jogo.png")