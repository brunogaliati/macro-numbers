import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Define as moedas e seus tickers no Yahoo Finance com nomes completos
currencies = {
    'TRY/USD': {'ticker': 'USDTRY=X', 'name': 'Lira Turca', 'invert': False, 'country_code': 'TR'},
    'BRL/USD': {'ticker': 'USDBRL=X', 'name': 'Real', 'invert': False, 'country_code': 'BR'},
    'ARS/USD': {'ticker': 'USDARS=X', 'name': 'Peso Argentino', 'invert': False, 'country_code': 'AR'},
    'MXN/USD': {'ticker': 'USDMXN=X', 'name': 'Peso Mexicano', 'invert': False, 'country_code': 'MX'},
    'CAD/USD': {'ticker': 'USDCAD=X', 'name': 'Dólar Canadense', 'invert': False, 'country_code': 'CA'},
    'EUR/USD': {'ticker': 'EURUSD=X', 'name': 'Euro', 'invert': True, 'country_code': 'EU'},
    #'ZAR/USD': {'ticker': 'USDZAR=X', 'name': 'Rand Sul-Africano', 'invert': False, 'country_code': 'ZA'},
    'JPY/USD': {'ticker': 'JPY=X', 'name': 'Iene Japonês', 'invert': False, 'country_code': 'JP'},
    'CNY/USD': {'ticker': 'USDCNY=X', 'name': 'Yuan Chinês', 'invert': False, 'country_code': 'CN'},
    'KRW/USD': {'ticker': 'USDKRW=X', 'name': 'Won Sul-Coreano', 'invert': False, 'country_code': 'KR'},
    'INR/USD': {'ticker': 'USDINR=X', 'name': 'Rúpia Indiana', 'invert': False, 'country_code': 'IN'},
    'SGD/USD': {'ticker': 'USDSGD=X', 'name': 'Dólar de Singapura', 'invert': False, 'country_code': 'SG'},
    'NZD/USD': {'ticker': 'NZDUSD=X', 'name': 'Dólar Neozelandês', 'invert': True, 'country_code': 'NZ'},
    'AUD/USD': {'ticker': 'AUDUSD=X', 'name': 'Dólar Australiano', 'invert': True, 'country_code': 'AU'},
    'RUB/USD': {'ticker': 'USDRUB=X', 'name': 'Rublo Russo', 'invert': False, 'country_code': 'RU'},
    'GBP/USD': {'ticker': 'GBPUSD=X', 'name': 'Libra Esterlina', 'invert': True, 'country_code': 'GB'},
    'HUF/USD': {'ticker': 'USDHUF=X', 'name': 'Florim Húngaro', 'invert': False, 'country_code': 'HU'},
}

# Adiciona o DXY (Índice do Dólar)
currencies['DXY'] = {'ticker': 'DX-Y.NYB', 'name': 'DXY', 'invert': False}

# Define as commodities e seus tickers
commodities = {
    'CL': {'ticker': 'CL=F', 'name': 'Petróleo WTI', 'invert': False},
    'BZ': {'ticker': 'BZ=F', 'name': 'Petróleo Brent', 'invert': False},
    'GC': {'ticker': 'GC=F', 'name': 'Ouro', 'invert': False},
    'SI': {'ticker': 'SI=F', 'name': 'Prata', 'invert': False},
    'HG': {'ticker': 'HG=F', 'name': 'Cobre', 'invert': False},
    'PL': {'ticker': 'PL=F', 'name': 'Platina', 'invert': False},
    'PA': {'ticker': 'PA=F', 'name': 'Paládio', 'invert': False},
    'NG': {'ticker': 'NG=F', 'name': 'Gás Natural', 'invert': False},
    'ZC': {'ticker': 'ZC=F', 'name': 'Milho', 'invert': False},
    'ZS': {'ticker': 'ZS=F', 'name': 'Soja', 'invert': False},
    'ZW': {'ticker': 'ZW=F', 'name': 'Trigo', 'invert': False},
}

if __name__ == "__main__":
    current_date = datetime.now()
    current_year = current_date.year
    performance_data = []
    commodities_performance = []

    # Função auxiliar para calcular performance
    def calculate_performance(ticker_info, asset_type='currency'):
        # Busca dados do ano anterior e atual
        prior_year_end = datetime(current_year - 1, 12, 31)
        prior_year_data = yf.download(ticker_info['ticker'], 
                                    start=prior_year_end - timedelta(days=7), 
                                    end=prior_year_end)
        
        if prior_year_data.empty:
            return None
            
        current_data = yf.download(ticker_info['ticker'], 
                                 start=f'{current_year}-01-01', 
                                 end=current_date.strftime('%Y-%m-%d'))
        
        if current_data.empty:
            return None

        # Busca dados da última semana com margem extra para garantir dados
        week_data = yf.download(ticker_info['ticker'],
                              start=current_date - timedelta(days=10),  # Aumenta janela para 10 dias
                              end=current_date)
        
        # Calcula performance YTD
        start_price = prior_year_data['Close'].iloc[-1]
        end_price = current_data['Close'].iloc[-1]
        
        # Aplica inversão apenas para moedas (não para commodities)
        if asset_type == 'currency':
            if ticker_info['invert']:
                # Para moedas que já estão na forma correta (EUR/USD, GBP/USD, etc)
                ytd_performance = (end_price - start_price) / start_price * 100
            else:
                # Para moedas que precisam ser invertidas (USD/BRL, USD/JPY, etc)
                ytd_performance = -(end_price - start_price) / start_price * 100
        else:
            # Para commodities, mantém o cálculo normal
            ytd_performance = (end_price - start_price) / start_price * 100

        # Calcula performance semanal com tratamento para dados faltantes
        if not week_data.empty and len(week_data) > 1:
            week_end_price = week_data['Close'].iloc[-1]
            
            # Pega o preço mais próximo de 7 dias atrás
            week_start_index = week_data.index[-1] - timedelta(days=7)
            closest_date = min(week_data.index, key=lambda x: abs(x - week_start_index))
            week_start_price = week_data.loc[closest_date, 'Close']
            
            # Aplica inversão apenas para moedas (não para commodities)
            if asset_type == 'currency':
                if ticker_info['invert']:
                    # Para moedas que já estão na forma correta
                    weekly_performance = (week_end_price - week_start_price) / week_start_price * 100
                else:
                    # Para moedas que precisam ser invertidas
                    weekly_performance = -(week_end_price - week_start_price) / week_start_price * 100
            else:
                # Para commodities, mantém o cálculo normal
                weekly_performance = (week_end_price - week_start_price) / week_start_price * 100
        else:
            weekly_performance = 0
            print(f"Aviso: Sem dados semanais para {ticker_info['ticker']}")
        
        return {
            'Moeda': ticker_info['ticker'],
            'Base Date': prior_year_data.index[-1].strftime('%Y-%m-%d'),
            'Current Date': current_data.index[-1].strftime('%Y-%m-%d'),
            'Preço Base (XXX/USD)': start_price,
            'Preço Atual (XXX/USD)': end_price,
            'Performance YTD (%)': ytd_performance,
            'Performance Semanal (%)': weekly_performance
        }

    # Calcula performance para cada moeda
    for currency, info in currencies.items():
        if currency == 'DXY':
            continue
        perf = calculate_performance(info, 'currency')
        if perf:
            performance_data.append(perf)

    # Adiciona DXY
    dxy_data = yf.download('DX-Y.NYB', start=f'{current_year}-01-01', end=current_date.strftime('%Y-%m-%d'))
    dxy_week_data = yf.download('DX-Y.NYB', start=current_date - timedelta(days=7), end=current_date)
    
    if not dxy_data.empty:
        ytd_perf = (dxy_data['Close'].iloc[-1] - dxy_data['Close'].iloc[0]) / dxy_data['Close'].iloc[0] * 100
        weekly_perf = (dxy_week_data['Close'].iloc[-1] - dxy_week_data['Close'].iloc[0]) / dxy_week_data['Close'].iloc[0] * 100 if not dxy_week_data.empty else 0
        
        performance_data.append({
            'Moeda': 'DXY',
            'Base Date': dxy_data.index[0].strftime('%Y-%m-%d'),
            'Current Date': dxy_data.index[-1].strftime('%Y-%m-%d'),
            'Preço Base (XXX/USD)': dxy_data['Close'].iloc[0],
            'Preço Atual (XXX/USD)': dxy_data['Close'].iloc[-1],
            'Performance YTD (%)': ytd_perf,
            'Performance Semanal (%)': weekly_perf
        })

    # Calcula performance para cada commodity
    for commodity, info in commodities.items():
        perf = calculate_performance(info, 'commodity')
        if perf:
            commodities_performance.append(perf)

    # Criar DataFrames e salvar
    df_currencies = pd.DataFrame(performance_data)
    df_currencies = df_currencies.sort_values(by='Performance YTD (%)', ascending=False)
    
    df_commodities = pd.DataFrame(commodities_performance)
    df_commodities = df_commodities.sort_values(by='Performance YTD (%)', ascending=False)
    
    # Salvar dados em CSV
    df_currencies.to_csv('currency_data.csv', index=False)
    df_commodities.to_csv('commodity_data.csv', index=False)
    
    # Salvar dicionários em CSV
    currencies_df = pd.DataFrame.from_dict(currencies, orient='index')
    currencies_df.to_csv('currencies_info.csv')
    
    commodities_df = pd.DataFrame.from_dict(commodities, orient='index')
    commodities_df.to_csv('commodities_info.csv')
    
    print("✅ Dados salvos com sucesso!") 