"""Build Part B: market-basket recommender UI as a single self-contained HTML page.

Rubric rules implemented exactly:
  - Apriori with min support = 2 baskets, min confidence = 0.10, lift > 1.0.
  - Recommendations come from the WHOLE cart only: a rule fires only when
    its antecedent equals the exact cart combination. No partial-basket
    fallback: if nothing covers the exact combination, the panel blanks out,
    even if an earlier (smaller) cart had recommendations.
  - Full product list stays visible and unfiltered.

Run: venv/bin/python src/build_market_basket.py  -> partb/market_basket.html
"""
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from recommender import load_transactions, frequent_itemsets, association_rules

ROOT = Path(__file__).resolve().parent.parent
MIN_SUPPORT = 2 / 1000
MIN_CONFIDENCE = 0.10

DEMO_GOOD = [
    "Hikvision DS-2CD2385FWD-I IP Camera (SKU: DS-2CD2385FWD-I)",
    "Pelco IMP1110-1ES IP Camera (SKU: IMP1110-1ES)",
]
DEMO_BLANK = [
    "Bosch D7050 Detector (SKU: D7050)",
    "DSC PG9914 Motion Detector (SKU: PG9914)",
]


def category_of(name):
    lname = name.lower()
    if "camera" in lname:
        return "IP / network cameras"
    if "nvr" in lname:
        return "Network video recorders"
    if "detector" in lname or "keypad" in lname or "wireless key" in lname:
        return "Detectors & keypads"
    if "panel" in lname or "receiver" in lname:
        return "Panels & receivers"
    return "Other components"


def main():
    txns = load_transactions()
    freq = frequent_itemsets(txns, min_support=MIN_SUPPORT, max_len=4)
    rules = [r for r in association_rules(freq)
             if r["confidence"] >= MIN_CONFIDENCE and r["lift"] > 1.0]

    products = sorted({i for t in txns for i in t})
    cats = {}
    for p in products:
        cats.setdefault(category_of(p), []).append(p)

    # explode rules to one row per consequent item; key = exact antecedent
    rows = []
    for r in rules:
        key = "\u0001".join(sorted(r["antecedent"]))
        for c in r["consequent"]:
            rows.append({"key": key,
                         "item": c,
                         "support": r["support"],
                         "confidence": r["confidence"],
                         "lift": r["lift"],
                         "antecedent": sorted(r["antecedent"])})
    # keep best row per (key, item)
    best = {}
    for row in rows:
        k = (row["key"], row["item"])
        if k not in best or row["confidence"] * row["lift"] > \
                best[k]["confidence"] * best[k]["lift"]:
            best[k] = row
    rows = sorted(best.values(),
                  key=lambda r: (-r["confidence"] * r["lift"], r["item"]))

    # sanity: demo carts behave as the rubric requires
    def fires(cart):
        key = "\u0001".join(sorted(cart))
        return [r for r in rows if r["key"] == key]

    good_hits = fires(DEMO_GOOD)
    blank_hits = fires(DEMO_BLANK)
    assert good_hits, "demo-good cart should fire at least one rule"
    assert not blank_hits, "demo-blank cart must fire no rules"
    print(f"rules embedded: {len(rows)} | demo-good fires: {len(good_hits)} | "
          f"demo-blank fires: {len(blank_hits)}")

    html = build_html(products, cats, rows)
    outdir = ROOT / "partb"
    outdir.mkdir(exist_ok=True)
    (outdir / "market_basket.html").write_text(html, encoding="utf-8")
    print("wrote", outdir / "market_basket.html")


def build_html(products, cats, rows):
    data = json.dumps({"rules": rows, "demoGood": DEMO_GOOD,
                       "demoBlank": DEMO_BLANK})
    cat_blocks = []
    for cat in sorted(cats):
        items = "\n".join(
            f'<div class="prod"><span>{p}</span>'
            f'<button onclick="addToCart({json.dumps(p)})">Add</button></div>'
            for p in cats[cat])
        cat_blocks.append(f"<h3>{cat}</h3>\n{items}")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Market Basket Recommender \u2014 CMPE 256 Hackathon</title>
<style>
body {{ font-family: Calibri, Arial, sans-serif; margin: 0; color: #000; }}
.wrap {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
h1 {{ font-size: 28px; margin-bottom: 4px; }}
.sub {{ color: #000; font-size: 14px; margin-bottom: 20px; }}
.cols {{ display: flex; gap: 24px; }}
.panel {{ flex: 1; border: 1px solid #000; border-radius: 8px; padding: 16px; }}
.panel h2 {{ font-size: 18px; margin-top: 0; }}
.panel h3 {{ font-size: 14px; margin: 14px 0 6px; border-bottom: 1px solid #ccc; padding-bottom: 4px; }}
.prod {{ display: flex; justify-content: space-between; align-items: center;
        padding: 5px 0; border-bottom: 1px dotted #ddd; font-size: 13px; }}
button {{ background: #000; color: #fff; border: none; border-radius: 4px;
         padding: 5px 12px; cursor: pointer; font-size: 13px; }}
button.ghost {{ background: #fff; color: #000; border: 1px solid #000; }}
button:disabled {{ opacity: .35; cursor: default; }}
#cartItems {{ min-height: 40px; }}
.cartrow {{ display: flex; justify-content: space-between; padding: 5px 0;
           border-bottom: 1px dotted #ddd; font-size: 14px; }}
.rec {{ border: 1px solid #000; border-radius: 6px; padding: 10px 12px;
       margin: 8px 0; font-size: 14px; }}
.rec .m {{ font-size: 12px; }}
.blank {{ border: 1px dashed #000; border-radius: 6px; padding: 14px;
         font-size: 14px; margin: 8px 0; }}
.demo {{ margin: 12px 0; display: flex; gap: 8px; flex-wrap: wrap; }}
.note {{ font-size: 13px; margin-top: 16px; }}
code {{ font-size: 13px; }}
</style></head><body><div class="wrap">
<h1>Market Basket Recommender</h1>
<div class="sub">CMPE 256 Hackathon \u2014 Part B. Apriori on 1,000 procurement
transactions and 40 SKUs. Thresholds: min support 2 baskets, min confidence
0.10, lift &gt; 1. Recommendations use the <b>whole cart only</b>: a rule fires
only when its antecedent equals your exact cart combination. Otherwise this
panel stays blank \u2014 even if a smaller cart had recommendations.</div>
<div class="demo">
<button class="ghost" onclick="loadDemo('good')">Demo: cart with recommendations</button>
<button class="ghost" onclick="loadDemo('blank')">Demo: cart that blanks out</button>
<button class="ghost" onclick="clearCart()">Clear cart</button>
</div>
<div class="cols">
<div class="panel"><h2>Products (full list)</h2>
{"".join(cat_blocks)}
</div>
<div class="panel"><h2>Cart</h2><div id="cartItems"></div>
<h2 style="margin-top:20px">Recommendations</h2><div id="recs"></div>
<div class="note">How it works: <code>src/recommender.py</code> mines
association rules; this page matches them against your exact cart. Add items
with the Add buttons; remove them from the cart to see recommendations
change \u2014 or vanish when no rule covers the combination.</div>
</div></div></div>
<script>
const DATA = {data};
let cart = [];
function keyOf(items) {{ return items.slice().sort().join("\\u0001"); }}
function render() {{
  const ci = document.getElementById("cartItems");
  ci.innerHTML = cart.length ? "" : "<i>Cart is empty \u2014 add products from the list.</i>";
  cart.forEach((p, i) => {{
    const d = document.createElement("div"); d.className = "cartrow";
    d.innerHTML = "<span></span>";
    d.firstChild.textContent = p;
    const b = document.createElement("button"); b.textContent = "Remove";
    b.onclick = () => {{ cart.splice(i, 1); render(); }};
    d.appendChild(b); ci.appendChild(d);
  }});
  document.querySelectorAll(".prod button").forEach(b => {{}});
  refreshButtons();
  const rc = document.getElementById("recs");
  rc.innerHTML = "";
  if (!cart.length) return;
  const k = keyOf(cart);
  const hits = DATA.rules.filter(r => r.key === k)
    .sort((a, b) => (b.confidence * b.lift) - (a.confidence * a.lift))
    .slice(0, 8);
  if (!hits.length) {{
    rc.innerHTML = '<div class="blank"><b>No recommendations.</b> No frequent '
      + 'pattern covers this exact combination at the current thresholds '
      + '(min support 2 baskets, min confidence 0.10, lift &gt; 1).</div>';
    return;
  }}
  hits.forEach(r => {{
    const d = document.createElement("div"); d.className = "rec";
    const t = document.createElement("div"); t.innerHTML = "<b></b>";
    t.firstChild.textContent = r.item; d.appendChild(t);
    const m = document.createElement("div"); m.className = "m";
    m.textContent = "support " + r.support + " \u00b7 confidence " + r.confidence
      + " \u00b7 lift " + r.lift + " \u00b7 because cart = " + r.antecedent.join(" + ");
    d.appendChild(m); rc.appendChild(d);
  }});
}}
function refreshButtons() {{
  document.querySelectorAll(".prod").forEach(d => {{
    const name = d.firstChild.textContent;
    const b = d.querySelector("button");
    b.disabled = cart.includes(name);
    b.textContent = cart.includes(name) ? "In cart" : "Add";
  }});
}}
function addToCart(p) {{ if (!cart.includes(p)) {{ cart.push(p); render(); }} }}
function clearCart() {{ cart = []; render(); }}
function loadDemo(which) {{
  cart = (which === "good" ? DATA.demoGood : DATA.demoBlank).slice();
  render();
}}
render();
</script></body></html>"""

if __name__ == "__main__":
    main()
