import pygetwindow as gw

wins = gw.getAllWindows()

for i, w in enumerate(wins):
    title = (w.title or "").strip()
    if not title:
        continue
    print(f"[{i}] '{title}'  |  ({w.left},{w.top}) {w.width}x{w.height}")