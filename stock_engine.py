import requests
import pandas as pd


#data Cleaning --------------------------------

def clean_number(value):
    
    if value is None or value=="":
        return 0.0
    
    if isinstance(value, str):
        clean_value =  value.replace(",", "").replace("%", "")
        try:
            return float(clean_value)
        except ValueError:
            return 0.0
        
    return float(value)

# Data Fetch from API 1 

def parse_api_1_financials(data):

    extracted = {}

    target_keys = {
        "PER": "PE_Ratio",
        "ROE": "ROE",
        "Net Margin": "Net_Margin",
        "BVPS": "BVPS", 
        "EPS": "EPS",
        "DPS": "DPS",
        "Div Yield":"Div_Yield",
        "PER":"PER",
        "PBV":"PBV",
        "Price/Sales":"Price/Sales",
        "EV/Sales":"EV/Sales",
        "EV/EBITDA":"EV/EBITDA",
        "Gross Margin":"Gross_Margin",
        "EBITDA Margin":"EBITDA_Margin",
        "Operating Margin":"Operating_Margin",

    }

    for item in data:
        raw_label = item.get('label','')

        for key_word, clean_name in target_keys.items():
            if key_word in raw_label:

                for year_data in item.get('data',[]):
                    try:
                        year = year_data.get('year')
                        val = clean_number(year_data.get('value'))

                        col_name = f"{clean_name}_{year}"
                        extracted[col_name]=val

                    except:
                        pass
                
                try:
                    latest_val = clean_number(item['data'][-1]['value'])
                    extracted[clean_name] = latest_val
                except:
                    pass

    return extracted


def parse_api_2_market(data):

    extracted = {}

    #--------------------Trading Data--------------------------  
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

    #Circuit Breaker & Day Range 
    cb_data = data.get('circuit_breaker', {})
    extracted['Circuit Breaker']= f"{clean_number(cb_data.get('lower_lock'))}-{clean_number(cb_data.get('upper_lock'))}"


    dr_data = data.get('day_range', {})
    extracted['Day Range'] = f"{clean_number(dr_data.get('low'))}-{clean_number(dr_data.get('high'))}"

    
    #--------------------Returns and History-------------------------------
    extracted['52W_High'] = clean_number(data.get('fifty_two_week_high'))
    extracted['52W_Low'] = clean_number(data.get('fifty_two_week_low'))
    extracted['52W_Avg'] = clean_number(data.get('fifty_two_week_average'))

    #total Retun 1M,3M,6M, 1Y,3Y,5Y

    tr_data = data.get('total_return',{})
    extracted['1M Returns']=clean_number(tr_data.get('1M'))
    extracted['3M Returns']=clean_number(tr_data.get('3M'))
    extracted['6M Returns']=clean_number(tr_data.get('6M'))
    extracted['1Y Returns']=clean_number(tr_data.get('1Y'))
    extracted['3Y Returns']=clean_number(tr_data.get('3Y'))
    extracted['5Y Returns']=clean_number(tr_data.get('5Y'))

    # ---------------------- Valuation-------------------------- 
    extracted['PE_Live'] = clean_number(data.get('pe')) 
    extracted['Div Yield'] = clean_number(data.get('dividend_yield'))
    extracted['PBV_Live'] = clean_number(data.get('pbv'))
    extracted['Enterprise Value'] = clean_number(data.get('ev'))
    extracted['Total_Debt'] = clean_number(data.get('total_debt'))
    extracted['Cash'] = clean_number(data.get('cash'))
    extracted['Current_Price'] = clean_number(data.get('current'))

    #---------------------Equity Profile--------------------------
    extracted['Market_Cap'] = clean_number(data.get('market_cap'))
    extracted['Total_Shares'] = clean_number(data.get('shares'))
    extracted['Free Float Value'] = clean_number(data.get('free_float'))
    extracted['Free Float %'] = clean_number(data.get('free_float_percentage')) 
    extracted['Change'] = clean_number(data.get('change'))
    extracted['Change_%'] = clean_number(data.get('change_in_percentage'))

    # --- 5. Date (Text Format) ---
    
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
                try:
                    val = clean_number(graph['data'][-1]['value'])
                    extracted[label]=val
                except:
                    extracted[label]=0.0
    return extracted

#--------------Industry Averages ----------------------

def parse_api_4_industry(data):

    extracted = {}

    match_map = {
        "Div Yield": "Industry_Div_Yield",
        "PER": "Industry_PE_Ratio",
        "PBV": "Industry_PBV",
        "Price/Sales": "Industry_Price_Sales",
        "EV/Sales": "Industry_EV_Sales",
        "EV/EBITDA": "Industry_EV_EBITDA",
        "ROE": "Industry_ROE",
        "Gross Margin": "Industry_Gross_Margin",
        "EBITDA Margin": "Industry_EBITDA_Margin",
        "Operating Margin": "Industry_Operating_Margin",
        "Net Margin": "Industry_Net_Margin"
    }

    for item in data:
        label = item.get('label')

        if label in match_map:
            try:
                val = clean_number(item.get('value'))

                new_key = match_map[label]

                extracted[new_key]=val

            except:
                pass
    return extracted

#-----------------Stock Data-------------------------------

def parse_api_5_stock_price(data):

    extracted={}

    for category in data:
        metrics = category.get('data', [])
        
        for metric in metrics:
            metric_label = metric.get('label')
            year_data = metric.get('data', [])

            for entry in year_data:
                try:
                    year = entry.get('year')
                    val = clean_number(entry.get('value'))

                    col_name = f'{metric_label}_{year}'
                    extracted[col_name]=val

                except:
                    pass
    return extracted


#----------------Income Statement-----------------------------

def parse_api_6_income_statement(data):

    annual_extracted = {}
    quarter_extracted = {}

    annual_list = data.get('annual',[])
    for item in annual_list:
        label = item.get('label','').strip()
        for entry in item.get('data',[]):
            try:
                year = entry.get('year')
                val = clean_number(entry.get('value'))

                column_name = f'{label}_{year}'

                annual_extracted[column_name]=val
            except:
                pass
    
    quarter_list = data.get('quarter',[])
    for item in quarter_list:
        label = item.get('label','').strip()
        for entry in item.get('data',[]):
            try:
                year = entry.get('year')
                val = clean_number(entry.get('value'))
                column_name=f'{label}_{year}'
                quarter_extracted[column_name]=val
            except:
                pass
    return {
        'Annual':annual_extracted,
        'Quarter':quarter_extracted
    }


#-----------------Balance Sheet-----------------------------------

def parse_api_7_balance_sheet(data):
    extracted={}

    annual_data = data.get('annual',[])
    for category in annual_data:
        label_1 = category.get('label','').strip()

        category_data = category.get('data',[])
        for item in category_data:
            label_2 = item.get('label','').strip()

            year_data = item.get('data',[])
            for entry in year_data:
                try:
                    year = entry.get('year')
                    val = clean_number(entry.get('value'))
                    column_name = f"{label_1}_{label_2}_{year}"
                    extracted[column_name]=val
                except:
                    pass
    return extracted

#-----------------Calling Function -----------------------------

def get_stock_foundation(ticker):

    print(f"\n🏗️  Building Foundation for Stock ID: {ticker}...")

    url_1 = f"https://api.askanalyst.com.pk/api/companyfinancialnew/{ticker}?companyfinancial=true&&test=true"
    url_2 = f"https://api.askanalyst.com.pk/api/sharepricedatanew/{ticker}"
    url_3 = f"https://api.askanalyst.com.pk/api/financialchartnew/{ticker}?financialchartnew=true"
    url_4 = f"https://api.askanalyst.com.pk/api/industrynew/{ticker}"
    url_5 = f"https://api.askanalyst.com.pk/api/stockpricedatanew/{ticker}"
    url_6 = f"https://api.askanalyst.com.pk/api/is/{ticker}"
    url_7 = F"https://api.askanalyst.com.pk/api/bs/{ticker}"

    try:
        
        headers = {'User-Agent': 'Mozilla/5.0'} 
        
        resp1 = requests.get(url_1, headers=headers).json()
        resp2 = requests.get(url_2, headers=headers).json()
        resp3 = requests.get(url_3, headers=headers).json()
        resp4 = requests.get(url_4, headers=headers).json()
        resp5 = requests.get(url_5, headers=headers).json()
        resp6 = requests.get(url_6, headers=headers).json()
        resp7 = requests.get(url_7, headers=headers).json()
        
        financials = parse_api_1_financials(resp1) 
        market = parse_api_2_market(resp2)         
        growth = parse_api_3_growth(resp3)
        industry = parse_api_4_industry(resp4)         
        stock_data = parse_api_5_stock_price(resp5)
        income_statement = parse_api_6_income_statement(resp6)
        balance_sheet = parse_api_7_balance_sheet(resp7)
        
        # master_data = {**financials, **market, **growth}

        total_equity = financials.get('BVPS', 0) * market.get('Total_Shares', 0)
        
        
        if total_equity > 0:
            d_e_ratio = market['Total_Debt'] / total_equity
        else:
            d_e_ratio = 0.0

        market['Debt_to-Equity']= round(d_e_ratio,2)

        return {
            "Financials": financials,
            "Market": market,
            "Growth": growth,
            "Industry":industry,
            "Stock Data": stock_data,
            "Ann_IS":income_statement['Annual'],
            "Qtr_IS":income_statement['Quarter'],
            "Balance Sheet":balance_sheet
        }
    
    except Exception as e:
        print(f"Error: {e}")
        return None
    

if __name__ == "__main__":
    
    ticker_id = "359" 
    
    
    result = get_stock_foundation(ticker_id)
    
    if result:
        print("\n✅ Data is ready! (Final Data):")
        
        
        file_name = f"Stock_Data_{ticker_id}.xlsx"

        try:
            with pd.ExcelWriter(file_name, engine='openpyxl') as writer:

                pd.DataFrame([result['Market']]).to_excel(writer, sheet_name="Market Overview", index=False)
                
                pd.DataFrame([result['Financials']]).to_excel(writer, sheet_name="Financial History", index=False)
                
                pd.DataFrame([result['Growth']]).to_excel(writer, sheet_name="Growth Trends", index=False)
                
                pd.DataFrame([result['Industry']]).to_excel(writer, sheet_name="Industry Averages",index=False)

                pd.DataFrame([result['Stock Data']]).to_excel(writer, sheet_name="Stock_data",index=False)

                pd.DataFrame([result['Ann_IS']]).to_excel(writer, sheet_name="Annual_Income_statement",index=False)

                pd.DataFrame([result['Qtr_IS']]).to_excel(writer, sheet_name="Quarter_Income_statement",index=False)

                pd.DataFrame([result['Balance Sheet']]).to_excel(writer, sheet_name="Balance_sheet",index=False)

            print(f"\n📂  File saved: {file_name}")
            print("   Check Tabs: 'Market Overview', 'Financial History', 'Growth Trends'")
            
            # Terminal par sirf Market Data dikha dete hain quick view k liye
            print("-" * 40)
            print("Quick View (Market Data):")
            print(pd.DataFrame([result['Market']]).T)
            print("-" * 40)

        except Exception as e:
            print(f"\n⚠️  Excel Error: {e}")
            
    else:
        print("\n❌ No data found.")