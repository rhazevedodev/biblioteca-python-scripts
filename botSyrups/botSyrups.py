import time
import cv2
import numpy as np
import mss
import pygetwindow as gw
import pyautogui

TITLE_CONTAINS = "WLO"
ANCHOR_BLENDER = "anchors/blender.png"
ANCHOR_BLENDER_ABERTO = "anchors/blender_aberto.png"

THRESHOLD = 0.80

# quantas tentativas de captura até desistir (frame estável)
MAX_TRIES = 30
SLEEP_BETWEEN_TRIES = 0.10

# filtro “frame branco”: se a média estiver muito alta, provavelmente é branco
WHITE_MEAN_THRESHOLD = 245  # 0..255

# ===== CONFIG DE CLIQUE =====
CLICK_MODE = "hold"     # "single", "double", "hold"
CLICK_INTERVAL = 0.30   # tempo entre cliques no double
HOLD_SECONDS = 0.12     # tempo segurando no modo hold

# ===== CONFIG DE MOVIMENTO DO MOUSE =====
MOUSE_MOVE_DURATION = 0.20   # tempo para mover até o alvo
MOUSE_PRE_CLICK_DELAY = 0.25  # tempo parado APÓS chegar no alvo (antes de clicar)

# ===== CONFIG DE TEMPO =====
POST_CLICK_SLEEP = 1.0  # espera base após clicar (antes de começar a confirmar)

# ✅ MINI WAIT INCREMENTAL (para confirmar "blender aberto")
CONFIRM_TRIES = 4       # quantas checagens de confirmação por tentativa
CONFIRM_SLEEP = 0.25    # tempo entre checagens (segundos)

# ===== PONTO NEUTRO (RESET DE FOCO) =====
NEUTRAL_OFFSET_X = 60
NEUTRAL_OFFSET_Y = 60
NEUTRAL_SLEEP = 0.20

# ===== RETRY =====
RETRY_COUNT = 3  # quantas tentativas totais de clique + confirmação

# ===== ÂNCORA 2 (SETA) =====
ANCHOR_ARROW = "anchors/seta.png"
ARROW_THRESHOLD = 0.80

# Quantos cliques dar na seta (definido por você)
ARROW_CLICKS = 8
ARROW_CLICK_SLEEP = 0.15  # pausa entre cliques (segundos)

# ===== ÂNCORA 3 (VERIFICAÇÃO FINAL APÓS CLICAR NA SETA) =====
ANCHOR_AFTER_ARROW = "anchors/achou_grape_syrup.png"
AFTER_THRESHOLD = 0.80

AFTER_CONFIRM_TRIES = 4
AFTER_CONFIRM_SLEEP = 0.25
AFTER_POST_SLEEP = 0.20  # pequena pausa após terminar os cliques (opcional)

# ===== ÂNCORA 4 (CONFIRMAÇÃO PÓS-CLIQUE FINAL) =====
ANCHOR_POST_FINAL = "anchors/abriu_grape_syrup.png"
POST_FINAL_THRESHOLD = 0.80

POST_FINAL_TRIES = 6
POST_FINAL_SLEEP = 0.25
POST_FINAL_POST_CLICK_SLEEP = 0.40  # espera após o clique final antes de começar a confirmar

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


def grab_window_bgr(sct, target_window):
    region = {
        "left": target_window.left,
        "top": target_window.top,
        "width": target_window.width,
        "height": target_window.height
    }
    shot = sct.grab(region)
    return np.array(shot)[:, :, :3]  # BGR


def is_probably_white(img_bgr: np.ndarray) -> bool:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    return gray.mean() >= WHITE_MEAN_THRESHOLD


def check_anchor_once(anchor_path, threshold=THRESHOLD):
    """
    Checa uma âncora UMA VEZ dentro da janela target.
    Retorna (found: bool, confidence: float)
    """
    anchor = cv2.imread(anchor_path, cv2.IMREAD_GRAYSCALE)
    if anchor is None:
        raise FileNotFoundError(anchor_path)

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


def confirm_with_mini_wait(anchor_path):
    """
    Confirma blender aberto usando múltiplas checagens curtas (mini wait incremental).
    Retorna (confirmed: bool, best_confidence: float)
    """
    if POST_CLICK_SLEEP > 0:
        print(f"Aguardando {POST_CLICK_SLEEP:.2f}s antes de iniciar confirmação...")
        time.sleep(POST_CLICK_SLEEP)

    best_conf = 0.0

    for i in range(1, CONFIRM_TRIES + 1):
        confirmed, conf = check_anchor_once(anchor_path, threshold=THRESHOLD)
        best_conf = max(best_conf, conf)

        if confirmed:
            print(f"✅ Confirmação OK na checagem {i}/{CONFIRM_TRIES} (confiança={conf:.3f})")
            return True, conf

        if i < CONFIRM_TRIES:
            print(
                f"⏳ Ainda não... checagem {i}/{CONFIRM_TRIES} (confiança={conf:.3f}). "
                f"Esperando {CONFIRM_SLEEP:.2f}s"
            )
            time.sleep(CONFIRM_SLEEP)

    print(f"❌ Não confirmou após {CONFIRM_TRIES} checagens. melhor_confiança={best_conf:.3f}")
    return False, best_conf


def confirm_with_mini_wait_custom(anchor_path: str, threshold: float, tries: int, sleep_s: float):
    """
    Confirma uma âncora com N checagens e intervalo custom.
    Retorna (confirmed: bool, best_confidence: float)
    """
    best_conf = 0.0

    for i in range(1, tries + 1):
        confirmed, conf = check_anchor_once(anchor_path, threshold=threshold)
        best_conf = max(best_conf, conf)

        if confirmed:
            print(f"✅ Confirmação OK na checagem {i}/{tries} (confiança={conf:.3f})")
            return True, conf

        if i < tries:
            print(f"⏳ Ainda não... checagem {i}/{tries} (confiança={conf:.3f}). Esperando {sleep_s:.2f}s")
            time.sleep(sleep_s)

    print(f"❌ Não confirmou após {tries} checagens. melhor_confiança={best_conf:.3f}")
    return False, best_conf


def move_to_neutral_point():
    nx = target.left + NEUTRAL_OFFSET_X
    ny = target.top + NEUTRAL_OFFSET_Y
    print(f"↪ Movendo mouse para ponto neutro ({nx},{ny})")
    pyautogui.moveTo(nx, ny, duration=0.12)
    time.sleep(NEUTRAL_SLEEP)


def click_at(x: int, y: int) -> bool:
    """
    Move para (x,y), espera estabilizar e clica conforme CLICK_MODE.
    """
    pyautogui.moveTo(x, y, duration=MOUSE_MOVE_DURATION)

    # ⏸️ tempo hábil para o cursor estabilizar no alvo
    if MOUSE_PRE_CLICK_DELAY > 0:
        time.sleep(MOUSE_PRE_CLICK_DELAY)

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


def click_n_times_at(x: int, y: int, n: int, sleep_between: float) -> None:
    """Clica N vezes em (x,y) usando click_at (respeita CLICK_MODE)."""
    if n <= 0:
        print("ℹ️ ARROW_CLICKS <= 0, pulando cliques.")
        return

    print(f"🖱️ Executando {n} cliques em ({x},{y}) (intervalo={sleep_between:.2f}s)")
    for i in range(1, n + 1):
        ok = click_at(x, y)
        if not ok:
            print("⚠️ Falha no modo de clique, abortando sequência.")
            return

        if i < n and sleep_between > 0:
            time.sleep(sleep_between)


def find_anchor_center_abs(anchor_path: str, threshold: float):
    """
    Procura uma âncora no frame estável da janela target.
    Retorna (found, confidence, abs_x, abs_y)
    """
    anchor = load_anchor(anchor_path)
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
            return False, 0.0, None, None

    img_gray = cv2.cvtColor(stable_img, cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(img_gray, anchor, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val < threshold:
        return False, max_val, None, None

    x, y = max_loc
    center_x_rel = x + aw // 2
    center_y_rel = y + ah // 2

    abs_x = target.left + center_x_rel
    abs_y = target.top + center_y_rel

    return True, max_val, abs_x, abs_y


# ===== MAIN =====

target = find_first_window()
if not target:
    print(f"FALHA: não achei janela contendo '{TITLE_CONTAINS}' (ou está minimizada).")
    raise SystemExit(1)

# Tenta trazer pra frente, mas não confia no primeiro frame depois disso
try:
    target.activate()
except Exception:
    pass

# 1) Achar âncora 1 (blender fechado) e calcular ponto de clique
found1, conf1, click_x, click_y = find_anchor_center_abs(ANCHOR_BLENDER, THRESHOLD)
if not found1:
    print(f"FALHA: âncora 1 não encontrada. melhor_confianca={conf1:.3f} (threshold={THRESHOLD})")
    raise SystemExit(0)

print(f"SUCESSO: âncora 1 encontrada (confiança={conf1:.3f}) | clique em ({click_x},{click_y})")

# 2) Retry: clicar e confirmar blender aberto
opened = False

for attempt in range(1, RETRY_COUNT + 1):
    print(f"▶ Tentativa {attempt}/{RETRY_COUNT} de abrir blender")

    # Entre tentativas, reseta foco
    if attempt > 1:
        print("↪ Resetando foco antes da próxima tentativa...")
        move_to_neutral_point()

    if not click_at(click_x, click_y):
        break

    confirmed_open, best_open_conf = confirm_with_mini_wait(ANCHOR_BLENDER_ABERTO)
    if confirmed_open:
        print(f"✅ Blender ABERTO confirmado (confiança={best_open_conf:.3f})")
        opened = True
        break

    print(f"⚠️ Tentativa {attempt} falhou (melhor_confiança={best_open_conf:.3f})")

if not opened:
    print("❌ Falha: blender não abriu após todas as tentativas.")
    raise SystemExit(0)

# 3) Blender aberto: encontrar âncora 2 (seta)
print("🔎 Procurando âncora 2 (seta)...")
found2, conf2, arrow_x, arrow_y = find_anchor_center_abs(ANCHOR_ARROW, ARROW_THRESHOLD)

if not found2:
    print(f"❌ Âncora 2 (seta) NÃO encontrada. melhor_confianca={conf2:.3f} (threshold={ARROW_THRESHOLD})")
    raise SystemExit(0)

print(f"✅ Âncora 2 (seta) encontrada! confiança={conf2:.3f} | ponto=({arrow_x},{arrow_y})")

# 4) Clicar N vezes na seta
click_n_times_at(arrow_x, arrow_y, ARROW_CLICKS, ARROW_CLICK_SLEEP)

if AFTER_POST_SLEEP > 0:
    time.sleep(AFTER_POST_SLEEP)

# 5) Depois dos cliques, verificar âncora 3 (estado final)
print("🔎 Verificando âncora 3 (estado final) após cliques na seta...")
confirmed3, best3 = confirm_with_mini_wait_custom(
    ANCHOR_AFTER_ARROW,
    threshold=AFTER_THRESHOLD,
    tries=AFTER_CONFIRM_TRIES,
    sleep_s=AFTER_CONFIRM_SLEEP
)

if not confirmed3:
    print(f"❌ Estado final NÃO confirmado (âncora 3). melhor_confiança={best3:.3f}")
    raise SystemExit(0)

print(f"✅ Estado final confirmado (âncora 3) (confiança={best3:.3f})")

# 👉 AGORA: localizar novamente a âncora final para clicar nela
print("🖱️ Localizando âncora final para clique...")
found_final, conf_final, final_x, final_y = find_anchor_center_abs(
    ANCHOR_AFTER_ARROW,
    AFTER_THRESHOLD
)

if not found_final:
    print(
        f"❌ Não consegui mapear a âncora final para clique. "
        f"melhor_confianca={conf_final:.3f}"
    )
    raise SystemExit(0)

print(
    f"🎯 Âncora final mapeada para clique "
    f"(confiança={conf_final:.3f}) em ({final_x},{final_y})"
)

# ✅ Clique final (respeita delay humano e modo de clique)
click_at(final_x, final_y)

print(f"⏳ Aguardando {POST_FINAL_POST_CLICK_SLEEP:.2f}s após clique final...")
time.sleep(POST_FINAL_POST_CLICK_SLEEP)

print("🔎 Confirmando âncora 4 (pós-clique final)...")
confirmed4, best4 = confirm_with_mini_wait_custom(
    ANCHOR_POST_FINAL,
    threshold=POST_FINAL_THRESHOLD,
    tries=POST_FINAL_TRIES,
    sleep_s=POST_FINAL_SLEEP
)

if confirmed4:
    print(f"✅ Pós-clique confirmado (âncora 4) (confiança={best4:.3f})")
else:
    print(f"❌ Pós-clique NÃO confirmado (âncora 4). melhor_confiança={best4:.3f}")
    raise SystemExit(0)

print("🏁 Fluxo concluído com sucesso.")