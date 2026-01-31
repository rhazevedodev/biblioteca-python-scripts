# 📌 Automação por Âncora de Imagem — `procurar_anchor.py`

Este script automatiza interações no jogo **WLO** usando **reconhecimento de imagem** e **controle de mouse**.

Ele foi projetado para funcionar de forma **robusta mesmo com lag**, atrasos de servidor e pequenas instabilidades visuais do jogo.

---

## 🎯 Objetivo do Script

O fluxo principal é:

1. Encontrar a janela do jogo (WLO)
2. Capturar a imagem da janela de forma estável (evitando “tela branca”)
3. Procurar uma **âncora visual** (imagem de referência)
4. Clicar **no centro da âncora**
5. Confirmar se o inventário abriu (segunda âncora)
6. Caso falhe:
   - resetar o foco do mouse
   - tentar novamente (retry configurável)

---

## 🧩 Tecnologias Utilizadas

- **OpenCV** — reconhecimento de imagem (`matchTemplate`)
- **mss** — captura de tela rápida
- **pygetwindow** — localizar janela do jogo
- **pyautogui** — mover mouse e clicar
- **numpy** — manipulação de imagem

---

## 📁 Estrutura Esperada

anchors/
├─ inventario.png
└─ inventario_aberto.png


- `inventario.png`  
  → imagem de um elemento clicável para abrir o inventário

- `inventario_aberto.png`  
  → imagem que **só aparece quando o inventário está aberto**

---

## ⚙️ Variáveis de Configuração (Topo do Código)

### 🔹 Identificação da Janela

```python
TITLE_CONTAINS = "WLO"

Parte do título da janela do jogo.
O script escolhe a primeira janela aberta que contenha esse texto.
```

🔹 Âncoras de Imagem
```
ANCHOR_INVENTARIO = "anchors/inventario.png"
ANCHOR_INVENTARIO_ABERTO = "anchors/inventario_aberto.png"
```

```
ANCHOR_INVENTARIO
Âncora usada para definir o ponto de clique

ANCHOR_INVENTARIO_ABERTO
Âncora usada para confirmar sucesso da ação

```

🔹 Threshold de Reconhecimento
```
THRESHOLD = 0.80
```
```
Confiança mínima para considerar que uma âncora foi encontrada.

Diminua se estiver falhando em achar (0.75)

Aumente se tiver falso positivo (0.85+)
```

🔹 Proteção contra “Tela Branca”

```
MAX_TRIES = 30
SLEEP_BETWEEN_TRIES = 0.10
WHITE_MEAN_THRESHOLD = 245
```

```
Evita capturas inválidas quando o jogo está atualizando a tela.

O script rejeita frames muito claros (quase brancos)

Repete a captura até obter imagem estável
```

🔹 Configuração de Clique

```
CLICK_MODE = "hold"   # single | double | hold
CLICK_INTERVAL = 0.30
HOLD_SECONDS = 0.12
```
```
single → clique simples

double → dois cliques

hold → segura o mouse (mais confiável com lag)
```

🔹 Espera Após Clique
```
POST_CLICK_SLEEP = 1.0
```
Tempo inicial de espera antes de começar a confirmar se o inventário abriu.

🔹 Mini Wait Incremental (Confirmação)
```
CONFIRM_TRIES = 4
CONFIRM_SLEEP = 0.25
```
```
Em vez de checar só uma vez, o script:

verifica várias vezes

com pequenas pausas

reduz falha por atraso do servidor

⏱ Tempo total aproximado:
```
```
POST_CLICK_SLEEP + (CONFIRM_TRIES - 1) * CONFIRM_SLEEP
```
🔹 Retry
```
RETRY_COUNT = 3
```
```
Quantidade máxima de tentativas completas:

clicar

esperar

confirmar

resetar foco

tentar novamente
```
🔹 Ponto Neutro (Reset de Foco)
```
NEUTRAL_OFFSET_X = 60
NEUTRAL_OFFSET_Y = 60
NEUTRAL_SLEEP = 0.20
```
```
Antes de um retry, o mouse é movido para um ponto neutro da janela:

limpa hover

evita foco preso

melhora consistência do próximo clique
```
🔹 Configurações do PyAutoGUI
```
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05
```
```
FAILSAFE: mover o mouse para o canto superior esquerdo cancela o script

PAUSE: pequena pausa entre comandos (mais estabilidade)
```
🔄 Fluxo Completo do Script

1. Localiza a janela do jogo

2. Garante foco

3. Captura imagem estável da janela

4. Procura a âncora do inventário

5. Calcula o centro do match

6. Entra no loop de tentativas:

7. clica no ponto

8. espera

9. confirma abertura

10. se falhar, move para ponto neutro e tenta de novo

11. Finaliza com sucesso ou erro após todas as tentativas

🧠 Por que esse script é robusto?

✔ Não depende de coordenadas fixas </br>
✔ Funciona mesmo com lag alto</br>
✔ Evita falso negativo por delay</br>
✔ Evita erro por tela branca</br>
✔ Retry inteligente com reset de foco</br>

▶️ Execução

Com o jogo aberto:

```
python procurar_anchor.py
```

🚧 Possíveis Evoluções

- Suporte a múltiplas instâncias do jogo

- Logs em arquivo

- Debug visual automático

- Ações encadeadas por estado

- Timeout dinâmico por latência

✅ Status

✔ Testado</br>
✔ Estável</br>
✔ Pronto para automação real</br>