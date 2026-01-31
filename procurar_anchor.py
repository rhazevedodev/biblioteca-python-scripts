import time
import cv2
import numpy as np
import mss
import pygetwindow as gw
import pyautogui

TITLE_CONTAINS = "WLO"
ANCHOR_INVENTARIO = "anchors/inventario.png"
ANCHOR_INVENTARIO_ABERTO = "anchors/inventario_aberto.png"

THRESHOLD = 0.80

# quantas tentativas de captura até desistir
MAX_TRIES = 30
SLEEP_BETWEEN_TRIES = 0.10

# filtro “frame branco”: se a média estiver muito alta, provavelmente é branco
WHITE_MEAN_THRESHOLD = 245  # 0..255

# ===== CONFIG DE CLIQUE =====
CLICK_MODE = "hold"     # "single", "double", "hold"
CLICK_INTERVAL = 0.30   # tempo entre cliques no double
HOLD_SECONDS = 0.12     # tempo segurando no modo hold

# ===== CONFIG DE TEMPO =====
POST_CLICK_SLEEP = 1  # tempo de espera antes da próxima ação

# ===== PONTO NEUTRO (RESET DE FOCO) =====
NEUTRAL_OFFSET_X = 60
NEUTRAL_OFFSET_Y = 60
NEUTRAL_SLEEP = 0.20

# ===== RETRY =====
RETRY_COUNT = 3  # quantas tentativas totais de clique + confirmação

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

def check_anchor_once(anchor_inventario, threshold=THRESHOLD):
    anchor = cv2.imread(anchor_inventario, cv2.IMREAD_GRAYSCALE)
    if anchor is None:
        raise FileNotFoundError(anchor_inventario)

    with mss.mss() as sct:
        region = {
            "left": target.left,
            "top": target.top,
            "width": target.width,
            "height": target.height
        }
        shot = sct.grab(region)
        img = np.array(shot)[:, :, :3]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(gray, anchor, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)

    return max_val >= threshold, max_val

def move_to_neutral_point():
    nx = target.left + NEUTRAL_OFFSET_X
    ny = target.top + NEUTRAL_OFFSET_Y
    print(f"↪ Movendo mouse para ponto neutro ({nx},{ny})")
    pyautogui.moveTo(nx, ny, duration=0.12)
    time.sleep(NEUTRAL_SLEEP)

def click_at(x: int, y: int) -> bool:
    """Move para (x,y) e clica conforme CLICK_MODE. Retorna False se modo inválido."""
    pyautogui.moveTo(x, y, duration=0.15)
    time.sleep(0.10)

    if CLICK_MODE == "single":
        pyautogui.click()
        print("Clique (single) executado.")
        return True

    if CLICK_MODE == "double":
        pyautogui.click()
        time.sleep(CLICK_INTERVAL)
        pyautogui.click()
        print("Clique (double) executado.")
        return True

    if CLICK_MODE == "hold":
        pyautogui.mouseDown()
        time.sleep(HOLD_SECONDS)
        pyautogui.mouseUp()
        print("Clique (hold) executado.")
        return True

    print(f"CLICK_MODE inválido: {CLICK_MODE}")
    return False

target = find_first_window()
if not target:
    print(f"FALHA: não achei janela contendo '{TITLE_CONTAINS}' (ou está minimizada).")
    raise SystemExit(1)

# Tenta trazer pra frente, mas não confia no primeiro frame depois disso
try:
    target.activate()
except Exception:
    pass

anchor = load_anchor(ANCHOR_INVENTARIO)
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

# Move primeiro (garante foco e posição)
pyautogui.moveTo(click_x, click_y, duration=0.15)
time.sleep(0.10)

if CLICK_MODE == "single":
    pyautogui.click()
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

# ⬇️ ESPERA PARAMETRIZADA
print(f"Aguardando {POST_CLICK_SLEEP:.2f}s antes da próxima ação...")
time.sleep(POST_CLICK_SLEEP)

confirmed, confidence = check_anchor_once(ANCHOR_INVENTARIO_ABERTO)

if confirmed:
    print(f"✅ Inventário ABERTO confirmado (confiança={confidence:.3f})")
else:
    print(f"❌ Inventário NÃO confirmado (confiança={confidence:.3f})")

    print("↻ Retry: resetando foco e tentando o clique novamente...")

    # 1) move para ponto neutro
    move_to_neutral_point()

    # 2) volta pro ponto do clique (já calculado antes)
    pyautogui.moveTo(click_x, click_y, duration=0.15)
    time.sleep(0.10)

    # 3) repete o clique no mesmo modo configurado
    if CLICK_MODE == "single":
        pyautogui.click()
        print("Retry: clique (single) executado.")

    elif CLICK_MODE == "double":
        pyautogui.click()
        time.sleep(CLICK_INTERVAL)
        pyautogui.click()
        print("Retry: clique (double) executado.")

    elif CLICK_MODE == "hold":
        pyautogui.mouseDown()
        time.sleep(HOLD_SECONDS)
        pyautogui.mouseUp()
        print("Retry: clique (hold) executado.")

    else:
        print(f"CLICK_MODE inválido: {CLICK_MODE}")

    # 4) espera e confirma de novo
    print(f"Aguardando {POST_CLICK_SLEEP:.2f}s antes da confirmação (retry)...")
    time.sleep(POST_CLICK_SLEEP)

    confirmed2, confidence2 = check_anchor_once(ANCHOR_INVENTARIO_ABERTO)

    if confirmed2:
        print(f"✅ Inventário ABERTO confirmado no retry (confiança={confidence2:.3f})")
    else:
        # ===== TENTAR ABRIR INVENTÁRIO COM RETRY =====
        for attempt in range(1, RETRY_COUNT + 1):
            print(f"▶ Tentativa {attempt}/{RETRY_COUNT} de abrir inventário")

            # Entre tentativas, reseta foco (na primeira tentativa não precisa)
            if attempt > 1:
                print("↪ Resetando foco antes da próxima tentativa...")
                move_to_neutral_point()

            # 1) clique no ponto calculado
            if not click_at(click_x, click_y):
                break

            # 2) espera e confirma
            print(f"Aguardando {POST_CLICK_SLEEP:.2f}s antes da confirmação...")
            time.sleep(POST_CLICK_SLEEP)

            confirmed, confidence = check_anchor_once(ANCHOR_INVENTARIO_ABERTO)

            if confirmed:
                print(f"✅ Inventário ABERTO confirmado (confiança={confidence:.3f})")
                break

            print(f"⚠️ Tentativa {attempt} falhou (confiança={confidence:.3f})")

        else:
            print("❌ Falha: inventário não abriu após todas as tentativas.")