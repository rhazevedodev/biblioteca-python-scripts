import time
import cv2
import numpy as np
import mss
import pygetwindow as gw
import pyautogui

TITLE_CONTAINS = "WLO"
ANCHOR_PATH = "anchors/inventario.png"

THRESHOLD = 0.80

# quantas tentativas de captura até desistir
MAX_TRIES = 30
SLEEP_BETWEEN_TRIES = 0.10

# filtro “frame branco”: se a média estiver muito alta, provavelmente é branco
WHITE_MEAN_THRESHOLD = 245  # 0..255

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

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

def grab_window_bgr(sct, target):
    region = {"left": target.left, "top": target.top, "width": target.width, "height": target.height}
    shot = sct.grab(region)
    return np.array(shot)[:, :, :3]  # BGR

def is_probably_white(img_bgr: np.ndarray) -> bool:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    return gray.mean() >= WHITE_MEAN_THRESHOLD

target = find_first_window()
if not target:
    print(f"FALHA: não achei janela contendo '{TITLE_CONTAINS}' (ou está minimizada).")
    raise SystemExit(1)

# Tenta trazer pra frente, mas não confia no primeiro frame depois disso
try:
    target.activate()
except Exception:
    pass

anchor = load_anchor(ANCHOR_PATH)
ah, aw = anchor.shape[:2]

with mss.mss() as sct:
    stable_img = None

    for i in range(MAX_TRIES):
        img_bgr = grab_window_bgr(sct, target)

        if is_probably_white(img_bgr):
            print(f"[{i+1}/{MAX_TRIES}] Frame branco/instável... aguardando")
            time.sleep(SLEEP_BETWEEN_TRIES)
            continue

        stable_img = img_bgr
        break

    if stable_img is None:
        print("FALHA: não consegui capturar um frame estável (sem branco).")
        raise SystemExit(0)

    img_gray = cv2.cvtColor(stable_img, cv2.COLOR_BGR2GRAY)

# Template matching no frame estável
result = cv2.matchTemplate(img_gray, anchor, cv2.TM_CCOEFF_NORMED)
_, max_val, _, max_loc = cv2.minMaxLoc(result)

if max_val < THRESHOLD:
    print(f"FALHA: âncora não encontrada. melhor_confianca={max_val:.3f} (threshold={THRESHOLD})")
    raise SystemExit(0)

x, y = max_loc
center_x_rel = x + aw // 2
center_y_rel = y + ah // 2

click_x = target.left + center_x_rel
click_y = target.top + center_y_rel

print(f"SUCESSO: confianca={max_val:.3f} | clique em ({click_x},{click_y})")

# ===== CONFIG DE CLIQUE =====
CLICK_MODE = "hold"     # "single", "double", "hold"
CLICK_INTERVAL = 0.30   # tempo entre cliques no double
HOLD_SECONDS = 0.12     # tempo segurando no modo hold

# Move primeiro (pra garantir foco e posição)
pyautogui.moveTo(click_x, click_y, duration=0.15)
time.sleep(0.10)

if CLICK_MODE == "single":
    pyautogui.click()  # já está no ponto
    print("Clique (single) executado.")

elif CLICK_MODE == "double":
    pyautogui.click()
    time.sleep(CLICK_INTERVAL)
    pyautogui.click()
    print("Clique (double) executado.")

elif CLICK_MODE == "hold":
    pyautogui.mouseDown()
    time.sleep(HOLD_SECONDS)
    pyautogui.mouseUp()
    print("Clique (hold) executado.")

else:
    print(f"CLICK_MODE inválido: {CLICK_MODE}")