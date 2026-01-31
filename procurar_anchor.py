import time
import cv2
import numpy as np
import mss
import pygetwindow as gw

TITLE_CONTAINS = "WLO"
ANCHOR_PATH = "anchors/anchor.png"

# Quanto maior, mais “certeza” (0.75 a 0.90 costuma ser bom)
THRESHOLD = 0.80

# Salvar imagem de debug com retângulo quando encontrar
SAVE_DEBUG_IMAGE = True
DEBUG_OUTPUT = "debug_match.png"

def find_first_window():
    for w in gw.getAllWindows():
        title = (w.title or "").strip()
        if title and TITLE_CONTAINS.lower() in title.lower():
            if w.width > 0 and w.height > 0 and not w.isMinimized:
                return w
    return None

def load_anchor(path: str):
    anchor = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if anchor is None:
        raise FileNotFoundError(f"Não achei a imagem em: {path}")
    return anchor

target = find_first_window()
if not target:
    print(f"FALHA: não achei janela contendo '{TITLE_CONTAINS}' (ou está minimizada).")
    raise SystemExit(1)

anchor = load_anchor(ANCHOR_PATH)
ah, aw = anchor.shape[:2]

# Região da janela
time.sleep(0.1)
region = {
    "left": target.left,
    "top": target.top,
    "width": target.width,
    "height": target.height
}

with mss.mss() as sct:
    shot = sct.grab(region)
    img_bgr = np.array(shot)[:, :, :3]  # BGR
    img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

# Template matching
result = cv2.matchTemplate(img_gray, anchor, cv2.TM_CCOEFF_NORMED)
_, max_val, _, max_loc = cv2.minMaxLoc(result)

if max_val >= THRESHOLD:
    x, y = max_loc
    print(f"SUCESSO: âncora encontrada! confianca={max_val:.3f} em (x={x}, y={y}) dentro da janela.")

    if SAVE_DEBUG_IMAGE:
        # Desenha um retângulo em cima do match
        debug = img_bgr.copy()
        cv2.rectangle(debug, (x, y), (x + aw, y + ah), (0, 255, 0), 2)
        cv2.imwrite(DEBUG_OUTPUT, debug)
        print(f"Salvei debug: {DEBUG_OUTPUT}")
else:
    print(f"FALHA: âncora NÃO encontrada. melhor_confianca={max_val:.3f} (threshold={THRESHOLD})")