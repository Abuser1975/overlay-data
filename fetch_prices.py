import re, csv, json
from datetime import datetime, timezone
from urllib.request import Request, urlopen

TANGO_URL = "https://www.tango.nl/stations/tango-den-bosch-maaspoort"
METEO_URL = "https://api.open-meteo.com/v1/forecast?latitude=51.6978&longitude=5.3037&current=temperature_2m&timezone=Europe%2FAmsterdam"
BTC_URL   = "https://api.coinbase.com/v2/prices/BTC-EUR/spot"

def get(url):
    req = Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")

def parse_tango(html):
    # Zoek Euro95 pompprijs en Diesel pompprijs + update tijd (op de pagina aanwezig) [2](https://geacloud.sharepoint.com/sites/Connect-legal/SitePages/GEA-Whistleblower-System.aspx?web=1)
    euro = re.search(r"Euro\s*95.*?Pompprijs:\s*([0-9]+[.,][0-9]+)\s*EUR/L", html, re.I|re.S)
    diesel = re.search(r"Diesel.*?Pompprijs:\s*([0-9]+[.,][0-9]+)\s*EUR/L", html, re.I|re.S)
    upd = re.search(r"Laatste\s*prijs\s*update:\s*([0-9:]+\s*uur,\s*[0-9-]+)", html, re.I)
    if not euro or not diesel:
        return None
    euro_v = euro.group(1).replace(".", ",")
    diesel_v = diesel.group(1).replace(".", ",")
    upd_v = upd.group(1) if upd else ""
    return euro_v, diesel_v, upd_v

def parse_meteo(js):
    data = json.loads(js)
    t = data.get("current", {}).get("temperature_2m", None)
    return t

def parse_btc(js):
    data = json.loads(js)
    amt = data.get("data", {}).get("amount", None)
    return amt

def main():
    now = datetime.now(timezone.utc).astimezone().strftime("%d-%m-%Y %H:%M")
    out = []

    tango_html = get(TANGO_URL)
    t = parse_tango(tango_html)
    if t:
        euro95, diesel, upd = t
        out.append(("Tango_Euro95", euro95, upd or now))
        out.append(("Tango_Diesel", diesel, upd or now))
    else:
        out.append(("Tango_Euro95", "", ""))
        out.append(("Tango_Diesel", "", ""))

    meteo_js = get(METEO_URL)
    temp = parse_meteo(meteo_js)
    out.append(("OutsideTemp", (str(temp).replace(".", ",") if temp is not None else ""), now))

    btc_js = get(BTC_URL)
    btc = parse_btc(btc_js)
    out.append(("BTC_EUR", (str(btc).replace(".", ",") if btc is not None else ""), now))

    with open("Overlay_Input.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Key","Value","Updated"])
        w.writerows(out)

if __name__ == "__main__":
    main()
