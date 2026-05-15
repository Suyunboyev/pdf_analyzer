"""
app.py — PDF Contract Analyzer frontend
Shows extracted products, comparison table, and detailed web price sources.
"""

import streamlit as st
import requests
import pandas as pd

BACKEND_URL      = "http://localhost:8000"
ANALYZE_ENDPOINT = f"{BACKEND_URL}/analyze-pdf"

st.set_page_config(page_title="PDF Contract Analyzer", page_icon="📄", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}

.header{background:linear-gradient(135deg,#0f172a,#1e3a5f);padding:2rem 2.5rem;
  border-radius:12px;margin-bottom:2rem;border-left:5px solid #38bdf8;}
.header h1{color:#f0f9ff;font-size:1.9rem;font-weight:700;margin:0;}
.header p{color:#94a3b8;margin:.3rem 0 0;font-size:.9rem;}

.metric-card{background:#0f172a;border:1px solid #1e3a5f;border-radius:10px;
  padding:1.1rem 1.4rem;text-align:center;}
.mlabel{color:#64748b;font-size:.75rem;text-transform:uppercase;letter-spacing:1px;font-family:'IBM Plex Mono',monospace;}
.mvalue{font-size:1.9rem;font-weight:700;font-family:'IBM Plex Mono',monospace;margin-top:.15rem;}
.blue{color:#38bdf8;} .green{color:#4ade80;} .red{color:#f87171;} .yellow{color:#fbbf24;}

.sec{font-size:1.05rem;font-weight:600;color:#e2e8f0;border-bottom:2px solid #1e3a5f;
  padding-bottom:.4rem;margin:1.4rem 0 .9rem;}

/* web sources table */
.src-table{width:100%;border-collapse:collapse;font-family:'IBM Plex Mono',monospace;font-size:.8rem;}
.src-table th{background:#1e3a5f;color:#94a3b8;padding:.4rem .7rem;text-align:left;font-weight:600;}
.src-table td{padding:.4rem .7rem;border-bottom:1px solid #1e293b;color:#cbd5e1;}
.src-table tr:hover td{background:#1e293b;}
.avg-row td{background:#0f2744 !important;color:#38bdf8 !important;font-weight:700;}
.src-link{color:#38bdf8;text-decoration:none;}
.src-link:hover{text-decoration:underline;}

.web-card{background:#0c1a2e;border:1px solid #1e3a5f;border-left:4px solid #fbbf24;
  border-radius:10px;padding:1.1rem 1.4rem;margin-bottom:1rem;}
.web-card h4{color:#fbbf24;margin:0 0 .6rem;font-size:.95rem;}
.web-card p{color:#94a3b8;font-size:.82rem;margin:.3rem 0;}

.stButton>button{background:linear-gradient(135deg,#0369a1,#0284c7);color:#fff;
  border:none;border-radius:8px;padding:.55rem 1.8rem;font-weight:600;font-size:1rem;width:100%;}
.stButton>button:hover{background:linear-gradient(135deg,#0284c7,#0ea5e9);transform:translateY(-1px);}
[data-testid="stFileUploader"]{background:#0f172a;border:2px dashed #1e3a5f;border-radius:10px;padding:.8rem;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
  <h1>📄 PDF Contract Analyzer</h1>
  <p>Upload contract → AI extracts products → Compare vs DB or multi-source web prices → Show average</p>
</div>""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 2.2], gap="large")

with col_left:
    st.markdown('<div class="sec">📤 Upload Contract</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("PDF file", type=["pdf"], label_visibility="collapsed")
    if uploaded:
        st.success(f"✅ **{uploaded.name}**  \n`{uploaded.size/1024:.1f} KB`")
    btn = st.button("🔍 Analyze", disabled=not uploaded)

    # st.markdown("---")
    # st.markdown("""
    # <div style='color:#475569;font-size:.82rem;line-height:1.9;'>
    # <b style='color:#64748b;'>HOW IT WORKS</b><br>
    # 1. PDF text extracted<br>
    # 2. Gemini parses products<br>
    # 3. Fuzzy match vs local DB<br>
    # 4. Not in DB? → <span style='color:#fbbf24'>web search</span><br>
    # &nbsp;&nbsp;&nbsp;• Multiple sources found<br>
    # &nbsp;&nbsp;&nbsp;• Average price calculated<br>
    # 5. Diff & % shown per product
    # </div>""", unsafe_allow_html=True)

with col_right:
    if btn and uploaded:
        with st.spinner("🤖 Analyzing — web search may take a moment..."):
            try:
                resp = requests.post(
                    ANALYZE_ENDPOINT,
                    files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                    timeout=200,
                )
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.ConnectionError:
                st.error("❌ Backend not running on `localhost:8000`"); st.stop()
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out"); st.stop()
            except requests.exceptions.HTTPError as e:
                st.error(f"❌ {resp.json().get('detail', str(e))}"); st.stop()
            except Exception as e:
                st.error(f"❌ {e}"); st.stop()

        comparison = data.get("comparison", [])
        total      = data.get("total_products", 0)
        mismatches = data.get("mismatches", 0)
        ok_count   = sum(1 for c in comparison if c.get("status") in ("OK", "Approx. OK"))
        web_count  = sum(1 for c in comparison if c.get("price_source") == "web_search")

        # ── Metrics ───────────────────────────────────────────────────────
        st.markdown('<div class="sec">📊 Summary</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="metric-card"><div class="mlabel">Total</div><div class="mvalue blue">{total}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><div class="mlabel">Price OK</div><div class="mvalue green">{ok_count}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><div class="mlabel">Mismatch</div><div class="mvalue {"red" if mismatches else "green"}">{mismatches}</div></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="metric-card"><div class="mlabel">Web Search</div><div class="mvalue yellow">{web_count}</div></div>', unsafe_allow_html=True)

        # ── Extracted products ────────────────────────────────────────────
        st.markdown('<div class="sec">📦 Extracted Products</div>', unsafe_allow_html=True)
        prods = data.get("products", [])
        if prods:
            df = pd.DataFrame(prods)
            for col in ["price","total","vat_amount","total_with_tax"]:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: f"{int(x):,}".replace(",", " ") if x else "—")
            st.dataframe(df, use_container_width=True, hide_index=True)

        # ── Comparison table ──────────────────────────────────────────────
        st.markdown('<div class="sec">⚖️ Price Comparison</div>', unsafe_allow_html=True)

        def fmt(v): return f"{int(v):,}".replace(",", " ") if v is not None else "—"

        rows = []
        for item in comparison:
            src    = item.get("price_source","")
            pct    = item.get("percent")
            diff   = item.get("difference")
            status = item.get("status","—")
            src_lbl = "🗄️ DB" if src=="local_db" else "🌐 Web avg"

            rows.append({
                "Product":    item.get("name","—"),
                "Unit":       item.get("unit","—"),
                "Qty":        item.get("quantity","—"),
                "PDF Price":  fmt(item.get("pdf_price")),
                "Ref Price":  fmt(item.get("ref_price")),
                "Difference": f"{int(diff):+,}".replace(",", " ") if diff is not None else "—",
                "Δ %":        f"{pct:+.2f}%" if pct is not None else "—",
                "Source":     src_lbl,
                "Status":     status,
            })

        df_cmp = pd.DataFrame(rows)

        def st_status(v):
            if v == "OK":               return "background:#166534;color:#4ade80;font-weight:600"
            if v == "Mismatch":         return "background:#7f1d1d;color:#f87171;font-weight:600"
            if v == "Approx. OK":       return "background:#164e2e;color:#6ee7b7;font-weight:600"
            if v == "Approx. Mismatch": return "background:#431407;color:#fdba74;font-weight:600"
            return "background:#1c1917;color:#a8a29e"

        def st_diff(v):
            if v == "—": return ""
            try:
                n = float(v.replace(" ","").replace("+","").replace("%",""))
                return "color:#f87171" if n > 0 else "color:#4ade80" if n < 0 else ""
            except: return ""

        def st_src(v):
            return "color:#38bdf8" if "DB" in v else "color:#fbbf24"

        styled = (df_cmp.style
                  .applymap(st_status, subset=["Status"])
                  .applymap(st_diff,   subset=["Difference","Δ %"])
                  .applymap(st_src,    subset=["Source"]))
        st.dataframe(styled, use_container_width=True, hide_index=True)

        # ── Web price sources breakdown ───────────────────────────────────
        web_items = [c for c in comparison if c.get("price_source") == "web_search" and c.get("web_prices")]
        if web_items:
            st.markdown('<div class="sec">🌐 Web Price Sources (detail)</div>', unsafe_allow_html=True)

            for item in web_items:
                wp      = item["web_prices"]
                sources = wp.get("sources", [])
                avg     = wp.get("average")
                mtype   = wp.get("match_type","approximate")
                summary = wp.get("summary","")
                badge   = "🎯 exact" if mtype=="exact" else "〜 approximate"

                with st.expander(f"🌐 **{item['name']}** — avg: {fmt(avg)} UZS  ·  {badge}  ·  {len(sources)} sources", expanded=True):
                    if summary:
                        st.markdown(f"<p style='color:#94a3b8;font-size:.83rem;margin-bottom:.8rem;'>📝 {summary}</p>", unsafe_allow_html=True)

                    # Build HTML table of sources
                    rows_html = ""
                    for s in sources:
                        price_str = fmt(s.get("price"))
                        src_name  = s.get("source","—")
                        url       = s.get("url")
                        note      = s.get("note","")
                        src_cell  = src_name
                        rows_html += f"<tr><td>{src_cell}</td><td>{price_str} UZS</td><td>{note}</td></tr>"

                    # Average row
                    rows_html += f'<tr class="avg-row"><td>📊 <b>Average ({len(sources)} sources)</b></td><td>{fmt(avg)} UZS</td><td>Used for comparison</td></tr>'

                    st.markdown(f"""
                    <table class="src-table">
                      <thead><tr><th>Source</th><th>Price</th><th>Note</th></tr></thead>
                      <tbody>{rows_html}</tbody>
                    </table>""", unsafe_allow_html=True)

                    # Mini bar chart
                    prices_valid = [s["price"] for s in sources if s.get("price")]
                    if len(prices_valid) >= 2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        chart_data = pd.DataFrame({
                            "Source": [s.get("source","?")[:25] for s in sources if s.get("price")],
                            "Price (UZS)": prices_valid,
                        }).set_index("Source")
                        st.bar_chart(chart_data, height=200)

        # ── Alerts ───────────────────────────────────────────────────────
        mm = [r for r in rows if "Mismatch" in r["Status"]]
        if mm: st.error(f"⚠️ {len(mm)} mismatch(es) detected!")
        else:  st.success("✅ All prices within acceptable range.")
        if web_count:
            st.info(f"🌐 {web_count} product(s) priced via multi-source web search (average used).")

        with st.expander("🔍 Raw extracted text"):
            st.code(data.get("raw_text_preview",""), language=None)

    elif not uploaded:
        st.markdown("""
        <div style='background:#0f172a;border:1px dashed #1e3a5f;border-radius:12px;
                    padding:3rem 2rem;text-align:center;'>
          <div style='font-size:3rem;margin-bottom:.8rem;'>📋</div>
          <div style='font-size:1.05rem;color:#475569;font-weight:600;'>Upload a PDF to get started</div>
          <div style='font-size:.82rem;color:#334155;margin-top:.4rem;'>
            Multi-source web prices · Average calculation · Diff & %
          </div>
        </div>""", unsafe_allow_html=True)