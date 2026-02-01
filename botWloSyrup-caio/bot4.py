import cv2
import numpy as np
import pyautogui
import mss
import time
import sys
import pygetwindow as gw
import random

# --- CONFIGURAÇÕES GERAIS ---
NOME_JANELA = "WLO" 

CONFIANCA_CENARIO = 0.60 
CONFIANCA_TEXTO = 0.85 

IMAGENS_DE_PE = ['de_pe_1.png', 'de_pe_2.png']

# Tempo normal de descanso após terminar um craft (para sentar)
TEMPO_COOLDOWN_INICIAL = 10 

# --- NOVA CONFIGURAÇÃO ---
# Se acabar o material (semente/muck), por quanto tempo essa janela fica "paralisada"?
# Coloquei 120 segundos (2 minutos). É o tempo para você abastecer.
TEMPO_PAUSA_SEM_MATERIAL = 120 

# Tempo de troca entre janelas
TEMPO_ENTRE_JANELAS = 4 

# --- MAPA DE ERROS ---
MAPA_DE_ERROS = {
    'erro_uva.png':             'fazer_uva',     
    'erro_abacaxi.png':         'fazer_abacaxi', 
    'erro_semente_uva.png':     'erro_fatal',    # Acabou semente -> Fatal
    'erro_semente_abacaxi.png': 'erro_fatal',
    'erro_muck.png':            'erro_fatal'     # Acabou adubo -> Fatal
}

# --- RECEITAS ---
RECEITAS = {
    'grape_syrup': {
        'estacao': 'blender.png',       
        'item_menu': 'syrup.png',
        'rolar_lista': 7,
        'cliques_mais': 1
    },
    'fazer_uva': {
        'estacao': 'turf.png',
        'item_menu': 'menu_grape.png',
        'rolar_lista': 0,
        'cliques_mais': 5
    },
    'fazer_abacaxi': {
        'estacao': 'turf.png',
        'item_menu': 'menu_pineapple.png',
        'rolar_lista': 0,
        'cliques_mais': 5
    }
}

def capturar_tela():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        return np.array(sct_img)

def focar_janela(janela):
    try:
        if janela.isMinimized: janela.restore()
        janela.activate()
        time.sleep(1.0) 
        return True
    except:
        try:
            janela.minimize()
            time.sleep(0.2)
            janela.restore()
            time.sleep(0.5)
            janela.activate()
            return True
        except:
            return False

def localizar_centro_com_debug(imagem_referencia, tela, nome_imagem, confianca_usada=CONFIANCA_CENARIO):
    try:
        if imagem_referencia is None: return None
        imagem_cinza = cv2.cvtColor(imagem_referencia, cv2.COLOR_BGR2GRAY)
        tela_cinza = cv2.cvtColor(tela, cv2.COLOR_BGRA2GRAY)
    except: return None

    res = cv2.matchTemplate(tela_cinza, imagem_cinza, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    if "erro" in nome_imagem or "stamp" in nome_imagem:
        sys.stdout.write(f"\r   > Check Erro ({nome_imagem}): {max_val:.2f}   ")
        sys.stdout.flush()

    if max_val >= confianca_usada:
        h, w = imagem_cinza.shape
        return max_loc[0] + w // 2, max_loc[1] + h // 2
    return None

def esperar_e_clicar(nome_arquivo, tentativas=5, timeout=1):
    print(f"   -> Procurando: {nome_arquivo}...")
    img_ref = cv2.imread(nome_arquivo)
    if img_ref is None: return False

    for _ in range(tentativas):
        tela = capturar_tela()
        ponto = localizar_centro_com_debug(img_ref, tela, nome_arquivo, CONFIANCA_CENARIO)
        if ponto:
            pyautogui.moveTo(ponto[0], ponto[1], duration=0.2)
            pyautogui.click()
            return True
        time.sleep(timeout)
    return False

def clicar_repetidamente_na_seta(nome_arquivo_seta, quantidade):
    if quantidade == 0: return True 
    img_ref = cv2.imread(nome_arquivo_seta)
    if img_ref is None: return False

    tela = capturar_tela()
    ponto = localizar_centro_com_debug(img_ref, tela, "seta", CONFIANCA_CENARIO)

    if ponto:
        pyautogui.moveTo(ponto[0], ponto[1], duration=0.2)
        for i in range(quantidade):
            pyautogui.click()
            time.sleep(0.3)
        return True
    return False

def verificar_se_esta_de_pe():
    tela = capturar_tela()
    for nome_img in IMAGENS_DE_PE:
        img = cv2.imread(nome_img)
        if img is None: continue
        if localizar_centro_com_debug(img, tela, "de_pe", CONFIANCA_CENARIO):
            return True
    return False

def analisar_ingredientes_faltantes():
    print("\n   [?] Conferindo erros visuais específicos...")
    tela = capturar_tela()
    tela_gray = cv2.cvtColor(tela, cv2.COLOR_BGRA2GRAY)
    
    for imagem_erro, acao_solucao in MAPA_DE_ERROS.items():
        img_ref = cv2.imread(imagem_erro)
        if img_ref is None: continue 
            
        img_gray = cv2.cvtColor(img_ref, cv2.COLOR_BGR2GRAY)
        res = cv2.matchTemplate(tela_gray, img_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        if max_val >= CONFIANCA_TEXTO:
            print(f"\n   [DETECTADO] Encontrei '{imagem_erro}' (Conf: {max_val:.2f})")
            print(f"   -> Solução definida: {acao_solucao.upper()}")
            return acao_solucao

    print("\n   [OK] Nenhum erro conhecido encontrado.")
    return 'ok'

def tentar_executar_receita(nome_receita):
    dados = RECEITAS[nome_receita]
    print(f"\n>>> ABRINDO ESTAÇÃO PARA: {nome_receita.upper()} <<<")
    
    if not esperar_e_clicar(dados['estacao'], tentativas=3): return 'falha'
    time.sleep(1.5) 

    if dados['rolar_lista'] > 0:
        clicar_repetidamente_na_seta('seta.png', dados['rolar_lista'])
            
    if not esperar_e_clicar(dados['item_menu'], tentativas=3): return 'falha'
    time.sleep(0.8) 
    
    qtd = dados['cliques_mais']
    if qtd > 0:
        print(f"   -> Ajustando quantidade ({qtd} clicks)...")
        img_mais = cv2.imread('mais.png')
        if img_mais is not None:
             tela = capturar_tela()
             ponto_mais = localizar_centro_com_debug(img_mais, tela, 'mais', CONFIANCA_CENARIO)
             if ponto_mais:
                 pyautogui.moveTo(ponto_mais[0], ponto_mais[1], duration=0.2)
                 for _ in range(qtd):
                     pyautogui.click()
                     time.sleep(0.25)
                 time.sleep(0.5) 

    # Verifica erros
    proximo_passo = analisar_ingredientes_faltantes()
    
    # --- MUDANÇA: Retorna 'erro_fatal' especificamente ---
    if proximo_passo == 'erro_fatal':
        print("   [ALERTA] SEMENTE/MUCK ACABOU! Abortando esta janela.")
        pyautogui.press('esc')
        time.sleep(0.2)
        pyautogui.press('esc')
        return 'erro_fatal' 
        
    if proximo_passo != 'ok':
        print(f"   [!] Ingrediente craftável em falta! Mudando para: {proximo_passo}")
        pyautogui.press('esc') 
        time.sleep(1.0) 
        pyautogui.press('esc') 
        time.sleep(1.5) 
        return tentar_executar_receita(proximo_passo)

    if esperar_e_clicar('confirmar.png', tentativas=3):
        print("   >>> CRAFT INICIADO! <<<")
        return 'sucesso'
    else:
        print("ERRO: Botão confirmar não apareceu.")
        return 'falha'

def main():
    print("=== BOT MULTI-CLIENTE (AUTO-PAUSA NO ABASTECIMENTO) ===")
    print(f"Janelas Alvo: '{NOME_JANELA}'")
    print(f"Tempo de pausa se faltar semente: {TEMPO_PAUSA_SEM_MATERIAL} segundos")
    time.sleep(3)
    cooldowns_janelas = {}

    while True:
        try: todas_janelas = gw.getWindowsWithTitle(NOME_JANELA)
        except: todas_janelas = []

        if not todas_janelas:
            print(f"Aguardando janelas '{NOME_JANELA}'...")
            time.sleep(5)
            continue

        nenhuma_acao_realizada = True

        for i, janela in enumerate(todas_janelas):
            try: id_janela = str(janela._hWnd) 
            except: id_janela = f"{janela.title}_{i}"
            agora = time.time()

            # --- VERIFICAÇÃO DE COOLDOWN/PAUSA ---
            if id_janela in cooldowns_janelas:
                tempo_liberacao = cooldowns_janelas[id_janela]
                if agora < tempo_liberacao:
                    # Se estiver bloqueada, o bot nem imprime nada pra não sujar o log
                    # e corre pra próxima janela
                    continue

            print(f"\n--- Verificando: {janela.title} (ID: {id_janela}) ---")
            if not focar_janela(janela): continue

            if verificar_se_esta_de_pe():
                print("   >>> Personagem LIVRE. Iniciando lógica do Syrup...")
                
                resultado = tentar_executar_receita('grape_syrup')
                
                if resultado == 'sucesso':
                    # Deu bom, pausa curta só pra sentar
                    cooldowns_janelas[id_janela] = time.time() + TEMPO_COOLDOWN_INICIAL
                    nenhuma_acao_realizada = False
                    
                elif resultado == 'erro_fatal':
                    # ACABOU MATERIAL! Pausa longa pra você abastecer
                    print(f"   [PAUSA] Janela pausada por {TEMPO_PAUSA_SEM_MATERIAL}s aguardando abastecimento...")
                    cooldowns_janelas[id_janela] = time.time() + TEMPO_PAUSA_SEM_MATERIAL
                    nenhuma_acao_realizada = False
                    
            else:
                sys.stdout.write("   >>> Ocupado (Trabalhando).\n")
            
            print(f"   [Pausa] Aguardando {TEMPO_ENTRE_JANELAS}s...")
            time.sleep(TEMPO_ENTRE_JANELAS)
        
        if nenhuma_acao_realizada:
            # Se todas as janelas estiverem ocupadas OU pausadas sem material
            sys.stdout.write("\r[Standby] Todas as janelas ocupadas ou aguardando...   ")
            sys.stdout.flush()
            time.sleep(2)

if __name__ == "__main__":
    pyautogui.FAILSAFE = True
    main()
