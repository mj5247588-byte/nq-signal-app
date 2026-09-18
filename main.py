from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
import urllib.request
import json
import threading

def fetch_data():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/NQ=F?interval=15m&range=5d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    q = data["chart"]["result"][0]["indicators"]["quote"][0]
    clean = []
    for i in range(len(q["close"])):
        if q["close"][i] is not None and q["high"][i] is not None and q["low"][i] is not None:
            clean.append((q["close"][i], q["high"][i], q["low"][i]))
    return clean

def ema(vals, p):
    k = 2.0 / (p + 1)
    e = vals[0]
    out = [e]
    for v in vals[1:]:
        e = v * k + e * (1 - k)
        out.append(e)
    return out

def rsi_fn(closes, p=14):
    if len(closes) < p + 1:
        return [50.0] * len(closes)
    g = [0.0]; l = [0.0]
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        g.append(max(d, 0)); l.append(max(-d, 0))
    out = [50.0] * len(closes)
    ag = sum(g[1:p+1]) / p; al = sum(l[1:p+1]) / p
    out[p] = 100.0 if al == 0 else 100 - (100 / (1 + ag/al))
    for i in range(p+1, len(closes)):
        ag = (ag * (p - 1) + g[i]) / p
        al = (al * (p - 1) + l[i]) / p
        out[i] = 100.0 if al == 0 else 100 - (100 / (1 + ag/al))
    return out

def atr_fn(highs, lows, closes, p=3):
    trs = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        trs.append(tr)
    out = [trs[0]]
    for i in range(1, len(trs)):
        if i < p:
            out.append(sum(trs[:i+1]) / (i+1))
        else:
            out.append(sum(trs[i-p+1:i+1]) / p)
    return out

class NQApp(App):
    def build(self):
        box = BoxLayout(orientation="vertical", padding=20)
        self.lbl = Label(text="Loading NQ...", size_hint_y=None, height=500,
                         text_size=(350, None), halign="left", valign="top", font_size="18sp")
        sc = ScrollView()
        sc.add_widget(self.lbl)
        box.add_widget(sc)
        Clock.schedule_once(self.run, 0.5)
        return box

    def run(self, dt):
        def t():
            try:
                d = fetch_data()
                closes = [x[0] for x in d]
                highs = [x[1] for x in d]
                lows = [x[2] for x in d]
                e5 = ema(closes, 5); e13 = ema(closes, 13)
                r14 = rsi_fn(closes, 14); a3 = atr_fn(highs, lows, closes, 3)
                i = len(closes) - 1
                sig = 0
                if e5[i] > e13[i] and e5[i-1] <= e13[i-1] and r14[i] >= 50: sig = 1
                elif e5[i] < e13[i] and e5[i-1] >= e13[i-1] and r14[i] < 50: sig = -1
                txt = "NQ (15-min) Signal\n--------------------\n"
                txt += "Price: $" + str(round(closes[-1], 2)) + "\n"
                txt += "EMA5: $" + str(round(e5[-1], 2)) + "\n"
                txt += "EMA13: $" + str(round(e13[-1], 2)) + "\n"
                txt += "RSI: " + str(round(r14[-1], 2)) + "\n"
                txt += "ATR: " + str(round(a3[-1], 2)) + "\n--------------------\n\n"
                if sig == 1: txt += "ACTION: BUY"
                elif sig == -1: txt += "ACTION: SELL"
                else: txt += "ACTION: HOLD"
                self.lbl.text = txt
            except Exception as e:
                self.lbl.text = "Error: " + str(e)
        threading.Thread(target=t).start()

if __name__ == "__main__":
    NQApp().run()
