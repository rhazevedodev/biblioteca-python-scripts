import mss
import mss.tools

with mss.mss() as sct:
    monitor = sct.monitors[1]  # 1 = monitor principal
    img = sct.grab(monitor)

    mss.tools.to_png(img.rgb, img.size, output="captura.png")
    print("Salvou: captura.png")