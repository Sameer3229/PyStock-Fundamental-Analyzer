import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import io
from datetime import datetime
from pdf_generator import create_pdf

# 1. BACKEND ENGINE 
#==============================================================================================

def clean_number(value):
    if value is None or value=="": return 0.0
    if isinstance(value, str):
        clean_value =  value.replace(",", "").replace("%", "")
        try: return float(clean_value)
        except ValueError: return 0.0
    return float(value)

# API 1 =======================================================================================

def parse_api_1_financials(data):
    extracted = {}
    target_keys = {
        "PER": "PE_Ratio", "ROE": "ROE", "Net Margin": "Net_Margin",
        "BVPS": "BVPS", "EPS": "EPS", "DPS": "DPS", "Div Yield":"Div_Yield",
        "PBV":"PBV", "Price/Sales":"Price/Sales", "EV/Sales":"EV/Sales",
        "EV/EBITDA":"EV/EBITDA", "Gross Margin":"Gross_Margin",
        "EBITDA Margin":"EBITDA_Margin", "Operating Margin":"Operating_Margin",
    }
    if not data: return extracted
    for item in data:
        raw_label = item.get('label','')
        for key_word, clean_name in target_keys.items():
            if key_word in raw_label:
                for year_data in item.get('data',[]):
                    try:
                        extracted[f"{clean_name}_{year_data.get('year')}"] = clean_number(year_data.get('value'))
                    except: pass
                try: extracted[clean_name] = clean_number(item['data'][-1]['value'])
                except: pass
    return extracted

# API 2 =======================================================================================

def parse_api_2_market(data):
    extracted = {}
    if not data: return extracted
    extracted['Open'] = clean_number(data.get('open'))
    extracted['High'] = clean_number(data.get('high'))
    extracted['Low'] = clean_number(data.get('low'))
    extracted['LDCP'] = clean_number(data.get('ldcp'))
    extracted['Volume'] = clean_number(data.get('volume'))
    extracted['Value'] = clean_number(data.get('value'))
    extracted['Close'] = clean_number(data.get('close'))
    cb_data = data.get('circuit_breaker', {})
    extracted['Circuit Breaker']= f"{clean_number(cb_data.get('lower_lock'))}-{clean_number(cb_data.get('upper_lock'))}"
    dr_data = data.get('day_range', {})
    extracted['Day Range'] = f"{clean_number(dr_data.get('low'))}-{clean_number(dr_data.get('high'))}"
    extracted['52W_High'] = clean_number(data.get('fifty_two_week_high'))
    extracted['52W_Low'] = clean_number(data.get('fifty_two_week_low'))
    extracted['52W_Avg'] = clean_number(data.get('fifty_two_week_average'))
    tr_data = data.get('total_return',{})
    extracted['1M Returns']=clean_number(tr_data.get('1M'))
    extracted['3M Returns']=clean_number(tr_data.get('3M'))
    extracted['6M Returns']=clean_number(tr_data.get('6M'))
    extracted['1Y Returns']=clean_number(tr_data.get('1Y'))
    extracted['3Y Returns']=clean_number(tr_data.get('3Y'))
    extracted['5Y Returns']=clean_number(tr_data.get('5Y'))
    extracted['PE_Live'] = clean_number(data.get('pe')) 
    extracted['Div Yield'] = clean_number(data.get('dividend_yield'))
    extracted['PBV_Live'] = clean_number(data.get('pbv'))
    extracted['Enterprise Value'] = clean_number(data.get('ev'))
    extracted['Total_Debt'] = clean_number(data.get('total_debt'))
    extracted['Cash'] = clean_number(data.get('cash'))
    extracted['Current_Price'] = clean_number(data.get('current'))
    extracted['Market_Cap'] = clean_number(data.get('market_cap'))
    extracted['Total_Shares'] = clean_number(data.get('shares'))
    extracted['Free Float Value'] = clean_number(data.get('free_float'))
    extracted['Free Float %'] = clean_number(data.get('free_float_percentage')) 
    extracted['Change'] = clean_number(data.get('change'))
    extracted['Change_%'] = clean_number(data.get('change_in_percentage'))
    extracted['Last_Updated'] = data.get('date', '')
    extracted['Net_Debt'] = extracted['Total_Debt'] - extracted['Cash']
    return extracted

# API 3 =======================================================================================

def parse_api_3_growth(data):
    extracted = {}
    if not data: return extracted
    targets = ["Revenue Growth", "Net Profit Growth"]
    for section in data:
        graphs = section.get('graphs',[])
        for graph in graphs:
            label = graph.get('label')
            if label in targets:
                try: extracted[label]=clean_number(graph['data'][-1]['value'])
                except: extracted[label]=0.0
    return extracted

def parse_api_4_industry(data):
    extracted = {}
    if not data: return extracted
    match_map = {
        "Div Yield": "Ind_Div_Yield", "PER": "Ind_PE", "PBV": "Ind_PBV", 
        "ROE": "Ind_ROE", "Net Margin": "Ind_Net_Margin",
        "Price/Sales": "Ind_Price_Sales", "EV/Sales": "Ind_EV_Sales",
        "EV/EBITDA": "Ind_EV_EBITDA", "Gross Margin": "Ind_Gross_Margin",
        "EBITDA Margin": "Ind_EBITDA_Margin", "Operating Margin": "Ind_Op_Margin"
    }
    for item in data:
        label = item.get('label')
        if label in match_map:
            try:
                val = clean_number(item.get('value'))
                new_key = match_map[label]
                extracted[new_key]=val
            except: pass
    return extracted

# API 5 =======================================================================================

def parse_api_5_stock_price(data):
    extracted={}
    if not data: return extracted
    for category in data:
        metrics = category.get('data', [])
        for metric in metrics:
            metric_label = metric.get('label')
            year_data = metric.get('data', [])
            for entry in year_data:
                try: extracted[f'{metric_label}_{entry.get("year")}']=clean_number(entry.get('value'))
                except: pass
    return extracted

# API 6 =======================================================================================

def parse_api_6_income_statement(data):
    annual_extracted = {}
    quarter_extracted = {}
    if not data: return {'Annual':annual_extracted, 'Quarter':quarter_extracted}
    for item in data.get('annual',[]):
        label = item.get('label','').strip()
        for entry in item.get('data',[]):
            try: annual_extracted[f'{label}_{entry.get("year")}']=clean_number(entry.get('value'))
            except: pass
    for item in data.get('quarter',[]):
        label = item.get('label','').strip()
        for entry in item.get('data',[]):
            try: quarter_extracted[f'{label}_{entry.get("year")}']=clean_number(entry.get('value'))
            except: pass
    return {'Annual':annual_extracted, 'Quarter':quarter_extracted}

# API 7 =======================================================================================

def parse_api_7_balance_sheet(data):
    extracted={}
    quarter_extracted={}
    if not data: return {'Annual': extracted, 'Quarter': quarter_extracted}
    annual_data = data.get('annual',[])
    for category in annual_data:
        label_1 = category.get('label','').strip()
        category_data = category.get('data',[])
        for item in category_data:
            label_2 = item.get('label','').strip()
            year_data = item.get('data',[])
            for entry in year_data:
                try: extracted[f"{label_1}_{label_2}_{entry.get('year')}"]=clean_number(entry.get('value'))
                except: pass
    q_data = data.get('quarter', [])
    for category in q_data:
        label_1 = category.get('label','').strip()
        category_data = category.get('data',[])
        for item in category_data:
            label_2 = item.get('label','').strip()
            year_data = item.get('data',[])
            for entry in year_data:
                try: quarter_extracted[f"{label_1}_{label_2}_{entry.get('year')}"]=clean_number(entry.get('value'))
                except: pass
    return {'Annual': extracted, 'Quarter': quarter_extracted}

# API 8 =======================================================================================

def parse_api_8_valuation(data):
    cleaned_data = {}
    if not data: return cleaned_data
    for metric_name, timeframes in data.items():
        if isinstance(timeframes, dict):
            cleaned_data[metric_name] = {}
            for period, points in timeframes.items():
                try:
                    df = pd.DataFrame(points)
                    if not df.empty and 'x' in df.columns and 'y' in df.columns:
                        df['Date'] = pd.to_datetime(df['x'])
                        df['Value'] = pd.to_numeric(df['y'])
                        df = df.set_index('Date')
                        cleaned_data[metric_name][period] = df[['Value']]
                except Exception as e:
                    pass
    return cleaned_data

# Helper Functions ==================================================================================

def safe_fetch(url, default_type="dict"):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return [] if default_type == "list" else {}

@st.cache_data
def get_all_companies():
    url = "https://api.askanalyst.com.pk/api/companylistwithids"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching company list: {e}")
        return []

def get_stock_foundation(ticker):
    base = "https://api.askanalyst.com.pk/api"
    r1 = safe_fetch(f"{base}/companyfinancialnew/{ticker}?companyfinancial=true&&test=true", "list")
    r2 = safe_fetch(f"{base}/sharepricedatanew/{ticker}", "dict")
    r3 = safe_fetch(f"{base}/financialchartnew/{ticker}?financialchartnew=true", "list")
    r4 = safe_fetch(f"{base}/industrynew/{ticker}", "list")
    r5 = safe_fetch(f"{base}/stockpricedatanew/{ticker}", "list")
    r6 = safe_fetch(f"{base}/is/{ticker}", "dict")
    r7 = safe_fetch(f"{base}/bs/{ticker}", "dict")
    r8 = safe_fetch(f"{base}/generatevaluation/{ticker}", "dict")
    
    try:
        financials = parse_api_1_financials(r1) 
        market = parse_api_2_market(r2)         
        growth = parse_api_3_growth(r3)
        industry = parse_api_4_industry(r4)         
        stock_data = parse_api_5_stock_price(r5)
        income_statement = parse_api_6_income_statement(r6)
        balance_sheet = parse_api_7_balance_sheet(r7)
        valuation_data = parse_api_8_valuation(r8) 
        
        total_shares = market.get('Total_Shares', 0) or 0
        bvps = financials.get('BVPS', 0) or 0
        total_debt = market.get('Total_Debt', 0) or 0
        total_equity = bvps * total_shares
        
        debt_to_equity = 0.0
        if total_equity > 0:
            debt_to_equity = round(total_debt / total_equity, 2)
        market['Debt_to-Equity'] = debt_to_equity

        return {
            "Financials": financials, "Market": market, "Growth": growth, "Industry":industry,
            "Stock Data": stock_data, "Ann_IS":income_statement['Annual'], "Qtr_IS":income_statement['Quarter'],
            "BS_Ann":balance_sheet['Annual'], "BS_Qtr":balance_sheet['Quarter'],
            "Valuation": valuation_data
        }
    except Exception as e:
        st.error(f"Data Processing Error: {e}")
        return None


# 2. UI TRANSFORMATION LOGIC ====================================================================


def transform_to_grid(flat_data):
    if not flat_data: return pd.DataFrame()
    data_map = {}
    years = set()
    for key, value in flat_data.items():
        if "_" in key and key.rsplit('_', 1)[-1].isdigit(): 
            parts = key.rsplit('_', 1)
            metric, year = parts[0], parts[1]
            if metric not in data_map: data_map[metric] = {}
            data_map[metric][year] = value
            years.add(year)
    if not data_map: return pd.DataFrame(list(flat_data.items()), columns=["Metric", "Value"]).astype(str)
    df = pd.DataFrame.from_dict(data_map, orient='index')
    df = df.sort_index(axis=1, ascending=False)
    df = df.iloc[:, :5]
    df = df.sort_index(axis=0) 
    return df.astype(str)

def make_hierarchical_grid(flat_data):
    if not flat_data: return pd.DataFrame()
    tree = {}
    all_years = set()
    for key, value in flat_data.items():
        parts = key.split('_')
        if len(parts) >= 3:
            year = parts[-1]
            all_years.add(year)
            if len(parts) == 2:
                cat = "Items"
                item = parts[0]
            else:
                cat = parts[0]
                item = "_".join(parts[1:-1])
            if cat not in tree: tree[cat] = {}
            if item not in tree[cat]: tree[cat][item] = {}
            tree[cat][item][year] = value
    sorted_years = sorted(list(all_years), reverse=True)[:5]
    rows = []
    for category, items in tree.items():
        if category != "Items": 
            head_row = {"Metric": f"{category.upper()}"}
            for y in sorted_years: head_row[y] = "" 
            rows.append(head_row)
        for item_name, year_vals in items.items():
            display_name = f"      {item_name}" if category != "Items" else item_name
            row = {"Metric": display_name}
            for y in sorted_years:
                row[y] = str(year_vals.get(y, "0"))
            rows.append(row)
    return pd.DataFrame(rows).astype(str)

def show_kv_table(data_dict, title):
    if not data_dict: return
    df = pd.DataFrame(list(data_dict.items()), columns=['Metric', 'Value'])
    if title: st.caption(title)
    st.dataframe(df.astype(str), width=500, hide_index=True)

def dict_to_df(d):
    return pd.DataFrame(list(d.items()), columns=['Metric', 'Value']).astype(str)

# --- CHART GENERATION HELPER ---
def generate_chart_image(df, title, color_hex):
    """Generates a Matplotlib chart and returns a BytesIO object."""
    plt.switch_backend('Agg') 
    fig, ax = plt.subplots(figsize=(7, 3))
    
    x = df.index
    y = df.iloc[:, 0]
    
    ax.fill_between(x, y, color=color_hex, alpha=0.3)
    ax.plot(x, y, color=color_hex, linewidth=1.5)
    
    ax.set_title(title, fontsize=10, fontweight='bold', pad=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.tick_params(axis='both', which='major', labelsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    fig.autofmt_xdate()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf


# 3. STREAMLIT APP DISPLAY ==========================================


st.set_page_config(page_title="Stock Analyzer", layout="wide", page_icon="📈")

all_companies = get_all_companies()
company_map = {f"{item['symbol']} | {item['name']}": item for item in all_companies}
options = list(company_map.keys())

col_logo_app, col_search, col_btn = st.columns([1, 4, 1])
with col_logo_app:
    st.markdown("### 📈 **Search**")

with col_search:
    default_idx = 0
    if "AIRLINK | Air Link Communication Limited" in options:
        default_idx = options.index("AIRLINK | Air Link Communication Limited")
        
    selected_option = st.selectbox("Select Company:", options, index=default_idx, label_visibility="collapsed", placeholder="Search for a company...")

with col_btn:
    if st.button("Fetch Report", type="primary", use_container_width=True):
        meta = company_map[selected_option]
        t_id = meta['value']
        with st.spinner(f"Fetching Data for {meta['symbol']}..."):
            fetched_data = get_stock_foundation(t_id)
            st.session_state['data'] = fetched_data
            st.session_state['current_meta'] = meta 
            st.session_state['data_loaded'] = True 

if st.session_state.get('data_loaded') and st.session_state.get('data'):
    data = st.session_state['data']
    meta = st.session_state['current_meta']
    mkt = data['Market']
    val_charts = data.get('Valuation', {})
    
    with st.container():
        h1, h2, h3 = st.columns([1, 3, 2])
        with h1:
            if meta.get('image'): st.image(meta['image'], width=80)
            else: st.write("🏦")
        with h2:
            st.subheader(f"{meta['name']}")
            st.caption(f"**Sector:** {meta.get('sector', 'N/A')} | **Symbol:** {meta.get('symbol', 'N/A')}")
        with h3:
            curr_p = mkt.get('Current_Price', 0)
            chg = mkt.get('Change', 0)
            chg_pct = mkt.get('Change_%', 0)
            st.metric("Current Price (PKR)", f"{curr_p:,.2f}", f"{chg} ({chg_pct}%)")

    st.divider()
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Market Cap", f"{mkt.get('Market_Cap', 0):,.0f} M")
    k2.metric("P/E Ratio", mkt.get('PE_Live', '-'))
    k3.metric("Debt-to-Equity", mkt.get('Debt_to-Equity', '-'))
    k4.metric("Div Yield", f"{mkt.get('Div Yield', 0)}%")
    k5.metric("Volume", f"{mkt.get('Volume', 0):,}")
    st.divider()

    t1, t2, t3, t4, t5, t6, t7, t8 = st.tabs([
        "Financial History", "Market Overview", "Growth Trends", "Industry Averages",
        "Stock Data", "Annual IS", "Balance Sheet", "Valuation Charts"
    ])

    with t1:
        st.subheader("Financial History (5 Years)")
        st.dataframe(transform_to_grid(data['Financials']), use_container_width=True)
    with t2:
        st.subheader("Market Snapshot")
        col1, col2 = st.columns(2)
        session = {k: mkt[k] for k in ["Open", "High", "Low", "Close", "Volume", "LDCP"] if k in mkt}
        ranges = {k: mkt[k] for k in ["Day Range", "52W_High", "52W_Low", "Circuit Breaker"] if k in mkt}
        valuations = {k: mkt[k] for k in ["PE_Live", "PBV_Live", "Div Yield", "Enterprise Value"] if k in mkt}
        debt = {k: mkt[k] for k in ["Total_Debt", "Cash", "Net_Debt", "Debt_to-Equity"] if k in mkt}
        returns = {k: mkt[k] for k in mkt if "Return" in k}
        with col1:
            show_kv_table(session, "⚡ Live Session")
            show_kv_table(valuations, "💰 Valuation & Ratios")
        with col2:
            show_kv_table(ranges, "📏 Ranges & Limits")
            show_kv_table(debt, "🏦 Capital Structure")
        st.caption("🚀 Returns Profile")
        st.dataframe(pd.DataFrame([returns]), use_container_width=True, hide_index=True)
    with t3:
        st.subheader("Growth Metrics")
        show_kv_table(data['Growth'], "")
    with t4:
        st.subheader("Industry Benchmarks")
        show_kv_table(data['Industry'], "")
    with t5:
        st.subheader("Stock Price History")
        st.dataframe(transform_to_grid(data['Stock Data']), use_container_width=True)
    with t6:
        st.subheader("Annual Income Statement")
        st.dataframe(transform_to_grid(data['Ann_IS']), use_container_width=True)
    with t7:
        st.subheader("Balance Sheet Position")
        with st.expander("🏛️ Annual Balance Sheet", expanded=True):
            df_bs_ann = make_hierarchical_grid(data['BS_Ann'])
            st.dataframe(df_bs_ann, use_container_width=True, height=600, hide_index=True)
        with st.expander("🏛️ Quarterly Balance Sheet"):
            df_bs_qtr = make_hierarchical_grid(data['BS_Qtr'])
            st.dataframe(df_bs_qtr, use_container_width=True, hide_index=True)
            
    with t8:
        st.subheader("Valuation Multiples")
        periods = ["1M", "3M", "6M", "1Y", "3Y", "5Y"]
        selected_period = st.select_slider("Select Time Period:", options=periods, value="1Y")
        metrics = list(val_charts.keys())
        if metrics:
            cols = st.columns(2)
            colors = ["#3060b2", "#6aa84f", "#8e7cc3", "#e69138"]
            for i, metric in enumerate(metrics):
                col_idx = i % 2
                with cols[col_idx]:
                    st.markdown(f"##### {metric} Multiple")
                    if selected_period in val_charts[metric]:
                        df_chart = val_charts[metric][selected_period]
                        chart_color = colors[i % len(colors)]
                        st.area_chart(df_chart, color=chart_color, use_container_width=True)
                    else:
                        st.info(f"No data available for {metric} ({selected_period})")
        else:
            st.warning("No Valuation Data returned from API.")


    # PDF DOWNLOAD =========================================================================
    
    with st.sidebar:
        st.divider()
        st.header("📄 Report")
        
        if st.button("Generate PDF Report"):
            with st.spinner("Generating Complete Report..."):
                
                # --- PREPARE DATA ---
                session_data = {k: mkt[k] for k in ["Open", "High", "Low", "Close", "Volume", "LDCP"] if k in mkt}
                ranges_data = {k: mkt[k] for k in ["Day Range", "52W_High", "52W_Low", "Circuit Breaker"] if k in mkt}
                val_data = {k: mkt[k] for k in ["PE_Live", "PBV_Live", "Div Yield", "Enterprise Value"] if k in mkt}
                debt_data = {k: mkt[k] for k in ["Total_Debt", "Cash", "Net_Debt", "Debt_to-Equity"] if k in mkt}
                
                # Generate Valuation Charts
                val_charts_section = {}
                if 'Valuation' in data:
                    colors = ["#3060b2", "#6aa84f", "#8e7cc3", "#e69138"]
                    i = 0
                    for metric, periods in data['Valuation'].items():
                        target = '1Y' if '1Y' in periods else (list(periods.keys())[0] if periods else None)
                        if target:
                            df_clean = periods[target].copy()
                            chart_color = colors[i % len(colors)]
                            img_buf = generate_chart_image(df_clean, f"{metric} History ({target})", chart_color)
                            val_charts_section[f"{metric} Chart"] = img_buf
                            i += 1

                # --- COMPILE PDF DATA
                pdf_data = {
                    "Financial History (5 Years)": transform_to_grid(data['Financials']),
                    "Market Overview": {
                        "Live Session": dict_to_df(session_data),
                        "Ranges & Limits": dict_to_df(ranges_data),
                        "Valuation & Ratios": dict_to_df(val_data),
                        "Capital Structure": dict_to_df(debt_data)
                    },
                    "Growth Trends": dict_to_df(data['Growth']),
                    "Industry Averages": dict_to_df(data['Industry']),
                    "Stock Price History": transform_to_grid(data['Stock Data']),
                    "Annual Income Statement": transform_to_grid(data['Ann_IS']),
                    "Annual Balance Sheet": make_hierarchical_grid(data['BS_Ann']),
                    "Valuation Analysis": val_charts_section  
                }

                # --- GENERATE PDF ---
                pdf_bytes = create_pdf(meta['name'], pdf_data)
                
                file_name = f"{meta['symbol']}_Full_Report_{datetime.now().strftime('%Y-%m-%d')}.pdf"
                
                st.success("Report Generated!")
                st.download_button(
                    label="⬇️ Download PDF Now",
                    data=pdf_bytes,
                    file_name=file_name,
                    mime="application/pdf",
                    type="primary"
                )

else:
    st.info("👈 Please select a company and click 'Fetch Report' to see the analysis.")