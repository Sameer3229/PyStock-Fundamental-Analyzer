import streamlit as st
import pandas as pd
import requests

# ==========================================
# 1. BACKEND ENGINE 
# ==========================================

def clean_number(value):
    if value is None or value=="": return 0.0
    if isinstance(value, str):
        clean_value =  value.replace(",", "").replace("%", "")
        try: return float(clean_value)
        except ValueError: return 0.0
    return float(value)

def parse_api_1_financials(data):
    extracted = {}
    target_keys = {
        "PER": "PE_Ratio", "ROE": "ROE", "Net Margin": "Net_Margin",
        "BVPS": "BVPS", "EPS": "EPS", "DPS": "DPS", "Div Yield":"Div_Yield",
        "PBV":"PBV", "Price/Sales":"Price/Sales", "EV/Sales":"EV/Sales",
        "EV/EBITDA":"EV/EBITDA", "Gross Margin":"Gross_Margin",
        "EBITDA Margin":"EBITDA_Margin", "Operating Margin":"Operating_Margin",
    }
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

def parse_api_2_market(data):
    extracted = {}
    extracted['Open'] = clean_number(data.get('open'))
    extracted['High'] = clean_number(data.get('high'))
    extracted['Low'] = clean_number(data.get('low'))
    extracted['LDCP'] = clean_number(data.get('ldcp'))
    extracted['Bid Price'] = clean_number(data.get('bid_price'))
    extracted['Bid Volume'] = clean_number(data.get('bid_volume'))
    extracted['Ask Price'] = clean_number(data.get('ask_price'))
    extracted['Ask Volume'] = clean_number(data.get('ask_volume'))
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

def parse_api_3_growth(data):
    extracted = {}
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

def parse_api_5_stock_price(data):
    extracted={}
    for category in data:
        metrics = category.get('data', [])
        for metric in metrics:
            metric_label = metric.get('label')
            year_data = metric.get('data', [])
            for entry in year_data:
                try: extracted[f'{metric_label}_{entry.get("year")}']=clean_number(entry.get('value'))
                except: pass
    return extracted

def parse_api_6_income_statement(data):
    annual_extracted = {}
    quarter_extracted = {}
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

def parse_api_7_balance_sheet(data):
    extracted={}
    # Annual Logic
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
    
    # Quarterly Logic (Backend mein rakh rahay hain, display mein hide karenge)
    quarter_extracted={}
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

def get_stock_foundation(ticker):
    base = "https://api.askanalyst.com.pk/api"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'} 
        r1 = requests.get(f"{base}/companyfinancialnew/{ticker}?companyfinancial=true&&test=true", headers=headers).json()
        r2 = requests.get(f"{base}/sharepricedatanew/{ticker}", headers=headers).json()
        r3 = requests.get(f"{base}/financialchartnew/{ticker}?financialchartnew=true", headers=headers).json()
        r4 = requests.get(f"{base}/industrynew/{ticker}", headers=headers).json()
        r5 = requests.get(f"{base}/stockpricedatanew/{ticker}", headers=headers).json()
        r6 = requests.get(f"{base}/is/{ticker}", headers=headers).json()
        r7 = requests.get(f"{base}/bs/{ticker}", headers=headers).json()
        
        financials = parse_api_1_financials(r1) 
        market = parse_api_2_market(r2)         
        growth = parse_api_3_growth(r3)
        industry = parse_api_4_industry(r4)         
        stock_data = parse_api_5_stock_price(r5)
        income_statement = parse_api_6_income_statement(r6)
        balance_sheet = parse_api_7_balance_sheet(r7)
        
        total_equity = financials.get('BVPS', 0) * market.get('Total_Shares', 0)
        market['Debt_to-Equity']= round(market['Total_Debt'] / total_equity,2) if total_equity > 0 else 0.0

        return {
            "Financials": financials, "Market": market, "Growth": growth, "Industry":industry,
            "Stock Data": stock_data, "Ann_IS":income_statement['Annual'], "Qtr_IS":income_statement['Quarter'],
            "BS_Ann":balance_sheet['Annual'], "BS_Qtr":balance_sheet['Quarter']
        }
    except Exception as e: return None

# ==========================================
# 2. UI TRANSFORMATION LOGIC 
# ==========================================

import pandas as pd
import streamlit as st

def transform_to_grid(flat_data):
    """ Simple Grid for Financials & Stock Data """
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
    if not data_map: return pd.DataFrame(list(flat_data.items()), columns=["Metric", "Value"]).astype(str) # FIX 1
    
    df = pd.DataFrame.from_dict(data_map, orient='index')
    
    # --- Sort DESCENDING ---
    df = df.sort_index(axis=1, ascending=False) 
    df = df.sort_index(axis=0) 
    
    return df.astype(str) # FIX 2: Sab kuch string bana diya taake crash na ho

def make_hierarchical_grid(flat_data):
    """ Hierarchy for Balance Sheet """
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

    sorted_years = sorted(list(all_years), reverse=True)
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
                # FIX 3: Value ko pehle hi string bana diya
                row[y] = str(year_vals.get(y, "0"))
            rows.append(row)
            
    # FIX 4: Final DataFrame ko bhi string ensure kar diya
    return pd.DataFrame(rows).astype(str)

def show_kv_table(data_dict, title):
    if not data_dict: return
    df = pd.DataFrame(list(data_dict.items()), columns=['Metric', 'Value'])
    st.caption(title)
    # FIX 5: width=True ghalat syntax hai naye version mein, aur .astype(str) zaroori hai
    st.dataframe(df.astype(str), width="stretch", hide_index=True)

# ==========================================
# 3. STREAMLIT APP DISPLAY 🖥️
# ==========================================

st.set_page_config(page_title="Stock Analyzer", layout="wide")
st.title("📊 Financial Analysis Dashboard")

# --- Input ---
c1, c2 = st.columns([1, 5])
with c1: ticker = st.text_input("Stock ID", value="359")
with c2: 
    if st.button("Fetch Report", type="primary"):
        with st.spinner("Fetching Data..."):
            st.session_state['data'] = get_stock_foundation(ticker)

# --- Main Logic ---
if 'data' in st.session_state and st.session_state['data']:
    data = st.session_state['data']
    mkt = data['Market']
    
    # Hero Section
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Price", f"PKR {mkt.get('Current_Price')}", mkt.get('Change'))
    h2.metric("Market Cap", f"{mkt.get('Market_Cap'):,.0f} M")
    h3.metric("P/E Ratio", mkt.get('PE_Live'))
    h4.metric("Debt-to-Equity", mkt.get('Debt_to-Equity'))
    st.divider()

    # Tabs (Reduced Count: Removed Quarterly IS)
    t1, t2, t3, t4, t5, t6, t7 = st.tabs([
        "Financial History", "Market Overview", "Growth Trends", "Industry Averages",
        "Stock Data", "Annual IS", "Balance Sheet"
    ])

    # 1. Financial History
    with t1:
        st.subheader("Financial History (5 Years)")
        st.dataframe(transform_to_grid(data['Financials']), width="stretch")

    # 2. Market Overview
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
        st.dataframe(pd.DataFrame([returns]), width="stretch", hide_index=True)

    # 3. Growth
    with t3:
        st.subheader("Growth Metrics")
        show_kv_table(data['Growth'], "")

    # 4. Industry
    with t4:
        st.subheader("Industry Benchmarks")
        show_kv_table(data['Industry'], "")

    # 5. Stock Data
    with t5:
        st.subheader("Stock Price History")
        st.dataframe(transform_to_grid(data['Stock Data']), width="stretch")

    # 6. Annual IS (Quarterly Removed)
    with t6:
        st.subheader("Annual Income Statement")
        st.dataframe(transform_to_grid(data['Ann_IS']), width="stretch")
        
        # --- HIDDEN QUARTERLY SECTION (As requested) ---
        # st.subheader("Quarterly Income Statement")
        # st.dataframe(transform_to_grid(data['Qtr_IS']), width="stretch")

    # 7. Balance Sheet (With Hierarchy)
    with t7:
        st.subheader("Balance Sheet Position")
        with st.expander("🏛️ Annual Balance Sheet", expanded=True):
            df_bs_ann = make_hierarchical_grid(data['BS_Ann'])
            st.dataframe(df_bs_ann, width="stretch", height=600, hide_index=True)
        
        # Quarterly BS ko bhi option mein rakha hai (Expandable), 
        # agar ye bhi chupana hai to bata dena.
        with st.expander("🏛️ Quarterly Balance Sheet"):
            df_bs_qtr = make_hierarchical_grid(data['BS_Qtr'])
            st.dataframe(df_bs_qtr, width="stretch", hide_index=True)

else:
    st.info("Enter Stock ID to analyze.")