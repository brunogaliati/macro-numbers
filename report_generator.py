import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, Flowable, Frame, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
import os

# Carregar dados das moedas e commodities globalmente
currencies = pd.read_csv('currencies_info.csv').set_index('Unnamed: 0').to_dict('index')
commodities = pd.read_csv('commodities_info.csv').set_index('Unnamed: 0').to_dict('index')

def create_enhanced_chart():
    # Carregar os dados
    df = pd.read_csv('currency_data.csv')
    
    # Ordenar por performance semanal para o segundo gráfico
    df_weekly = df.copy()
    df_weekly = df_weekly.sort_values(by='Performance Semanal (%)', ascending=True)
    df = df.sort_values(by='Performance YTD (%)', ascending=True)

    # Criar um dicionário reverso para mapear tickers para nomes
    ticker_to_name = {}
    for currency, info in currencies.items():
        ticker_to_name[info['ticker']] = info['name']
        if currency == 'DXY':
            ticker_to_name['DXY'] = 'Índice do Dólar (DXY)'
    
    # Debug pra ver que porra tá vindo
    print("Moedas no DataFrame:", df['Moeda'].tolist())
    print("\nTicker to name dict:", ticker_to_name)

    # Configurações do gráfico
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['font.size'] = 11
    plt.rcParams['font.family'] = 'Arial'

    # Criar dois subplots empilhados com tamanho menor
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 10))

    # Configurar ambos os gráficos
    for ax in [ax1, ax2]:
        ax.spines['top'].set_visible(True)
        ax.spines['right'].set_visible(True)
        ax.spines['bottom'].set_visible(True)
        ax.spines['left'].set_visible(True)
        for spine in ax.spines.values():
            spine.set_linewidth(1.5)

    # Gráfico YTD (mantém a ordem YTD)
    moedas_ytd = []
    for moeda in df['Moeda']:
        try:
            if moeda == 'DX-Y.NYB' or moeda == 'DXY':
                moedas_ytd.append('Índice do Dólar (DXY)')
            else:
                moedas_ytd.append(ticker_to_name[moeda])
        except KeyError as e:
            print(f"Erro na moeda: {moeda}")
            print(f"Dicionário disponível: {ticker_to_name}")
            raise e

    performance_ytd = df['Performance YTD (%)'].values
    bars1 = ax1.barh(moedas_ytd, performance_ytd, 
                     color=['#2E7D32' if x > 0 else '#F44336' for x in performance_ytd])
    ax1.set_title('Performance YTD', fontsize=14, fontweight='bold')
    
    # Gráfico Semanal (usa a ordem semanal)
    moedas_weekly = []
    for moeda in df_weekly['Moeda']:
        try:
            if moeda == 'DX-Y.NYB' or moeda == 'DXY':
                moedas_weekly.append('Índice do Dólar (DXY)')
            else:
                moedas_weekly.append(ticker_to_name[moeda])
        except KeyError as e:
            print(f"Erro na moeda: {moeda}")
            print(f"Dicionário disponível: {ticker_to_name}")
            raise e

    performance_week = df_weekly['Performance Semanal (%)'].values
    bars2 = ax2.barh(moedas_weekly, performance_week,
                     color=['#2E7D32' if x > 0 else '#F44336' for x in performance_week])
    ax2.set_title('Performance Semanal', fontsize=14, fontweight='bold')

    # Adicionar valores nas barras para ambos os gráficos
    for ax, bars, performance in [(ax1, bars1, performance_ytd), (ax2, bars2, performance_week)]:
        max_value = max(abs(performance.min()), abs(performance.max()))
        ax.set_xlim(-(max_value + 0.5), max_value + 0.5)
        
        for bar in bars:
            width = bar.get_width()
            offset = 0.05 * max_value
            ax.text(width + (offset if width > 0 else -offset), 
                    bar.get_y() + bar.get_height()/2,
                    f"{width:+.2f}%", 
                    va='center', 
                    ha='left' if width > 0 else 'right',
                    fontsize=10)
        
        ax.grid(axis='x', linestyle='--', alpha=0.5)
        ax.set_xlabel('Performance (%)', fontsize=12)

    plt.tight_layout()
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    plt.close()
    buffer.seek(0)
    return buffer

def create_enhanced_pdf(chart_image):
    # Proporção de slide (16:9)
    slide_width = 16 * inch
    slide_height = 9 * inch

    doc = SimpleDocTemplate("enhanced_currency_report.pdf",
                          pagesize=(slide_width, slide_height),
                          rightMargin=30,
                          leftMargin=30,
                          topMargin=30,
                          bottomMargin=30)

    story = []
    elements = []
    
    img = Image(chart_image, width=6 * inch, height=7 * inch)
    
    df = pd.read_csv('currency_data.csv')
    df = df.rename(columns={
        'Performance YTD (%)': 'YTD',
        'Performance Semanal (%)': 'Δ Semana'
    })

    # Criar um dicionário reverso para mapear tickers para nomes
    ticker_to_name = {}
    for currency, info in currencies.items():
        ticker_to_name[info['ticker']] = info['name']
        # Adiciona o DXY especificamente
        if currency == 'DXY':
            ticker_to_name['DXY'] = 'Índice do Dólar (DXY)'
    
    # Debug pra ver que porra tá vindo
    print("\nMoedas na tabela:", df['Moeda'].tolist())
    print("Dicionário disponível:", ticker_to_name)
    
    table_data = [['Moeda', 'YTD', 'Δ Semana']]
    for i, row in df.iterrows():
        try:
            if row['Moeda'] == 'DX-Y.NYB' or row['Moeda'] == 'DXY':
                name = 'Índice do Dólar (DXY)'
            else:
                name = ticker_to_name[row['Moeda']]
            
            table_data.append([
                name,
                f"{row['YTD']:+.2f}%",
                f"{row['Δ Semana']:+.2f}%"
            ])
        except KeyError as e:
            print(f"Erro na moeda: {row['Moeda']}")
            print(f"Dicionário disponível: {ticker_to_name}")
            raise e

    # Tabela com larguras menores
    table = Table(table_data, colWidths=[160, 80, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
    ]))

    # Layout table com larguras menores
    layout_table = Table([[img, table]], colWidths=[7.5*inch, 6*inch])
    layout_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(layout_table)
    doc.build(story)

def create_enhanced_commodities_chart():
    # Carregar os dados
    df = pd.read_csv('commodity_data.csv')
    
    # Ordenar por performance semanal para o segundo gráfico
    df_weekly = df.copy()
    df_weekly = df_weekly.sort_values(by='Performance Semanal (%)', ascending=True)
    df = df.sort_values(by='Performance YTD (%)', ascending=True)

    # Criar um dicionário reverso para mapear tickers para nomes
    ticker_to_name = {}
    for commodity, info in commodities.items():
        ticker_to_name[info['ticker']] = info['name']

    # Configurações do gráfico
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['font.size'] = 11
    plt.rcParams['font.family'] = 'Arial'

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 10))

    for ax in [ax1, ax2]:
        ax.spines['top'].set_visible(True)
        ax.spines['right'].set_visible(True)
        ax.spines['bottom'].set_visible(True)
        ax.spines['left'].set_visible(True)
        for spine in ax.spines.values():
            spine.set_linewidth(1.5)

    commodity_names = [ticker_to_name[comm] for comm in df['Moeda']]

    # Gráfico YTD
    performance_ytd = df['Performance YTD (%)'].values
    bars1 = ax1.barh(commodity_names, performance_ytd,
                     color=['#2E7D32' if x > 0 else '#F44336' for x in performance_ytd])
    ax1.set_title('Performance YTD', fontsize=14, fontweight='bold')
    
    # Gráfico Semanal
    performance_week = df_weekly['Performance Semanal (%)'].values
    bars2 = ax2.barh(commodity_names, performance_week,
                     color=['#2E7D32' if x > 0 else '#F44336' for x in performance_week])
    ax2.set_title('Performance Semanal', fontsize=14, fontweight='bold')

    # Adicionar valores nas barras para ambos os gráficos
    for ax, bars, performance in [(ax1, bars1, performance_ytd), (ax2, bars2, performance_week)]:
        max_value = max(abs(performance.min()), abs(performance.max()))
        ax.set_xlim(-(max_value + 0.5), max_value + 0.5)
        
        for bar in bars:
            width = bar.get_width()
            offset = 0.05 * max_value
            ax.text(width + (offset if width > 0 else -offset), 
                    bar.get_y() + bar.get_height()/2,
                    f"{width:+.2f}%", 
                    va='center', 
                    ha='left' if width > 0 else 'right',
                    fontsize=10)
        
        ax.grid(axis='x', linestyle='--', alpha=0.5)
        ax.set_xlabel('Performance (%)', fontsize=12)

    plt.tight_layout()
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    plt.close()
    buffer.seek(0)
    return buffer

def create_enhanced_commodities_pdf(chart_image):
    # Usar a mesma lógica do create_enhanced_pdf(), mas para commodities
    slide_width = 16 * inch
    slide_height = 9 * inch

    doc = SimpleDocTemplate("enhanced_commodities_report.pdf",
                          pagesize=(slide_width, slide_height),
                          rightMargin=30,
                          leftMargin=30,
                          topMargin=30,
                          bottomMargin=30)

    story = []
    elements = []
    
    img = Image(chart_image, width=6 * inch, height=7 * inch)
    
    df = pd.read_csv('commodity_data.csv')
    df = df.rename(columns={
        'Performance YTD (%)': 'YTD',
        'Performance Semanal (%)': 'Δ Semana'
    })
    
    # Criar um dicionário reverso para mapear tickers para nomes
    ticker_to_name = {}
    for commodity, info in commodities.items():
        ticker_to_name[info['ticker']] = info['name']
    
    table_data = [['Commodity', 'YTD', 'Δ Semana']]
    for i, row in df.iterrows():
        table_data.append([
            ticker_to_name[row['Moeda']],
            f"{row['YTD']:+.2f}%",
            f"{row['Δ Semana']:+.2f}%"
        ])

    table = Table(table_data, colWidths=[160, 80, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
    ]))

    layout_table = Table([[img, table]], colWidths=[7.5*inch, 6*inch])
    layout_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(layout_table)
    doc.build(story)

def create_combined_pdf(currency_chart, commodity_chart):
    # Proporção de slide (16:9)
    slide_width = 16 * inch
    slide_height = 9 * inch

    doc = SimpleDocTemplate("combined_market_report.pdf",
                          pagesize=(slide_width, slide_height),
                          rightMargin=30,
                          leftMargin=30,
                          topMargin=30,
                          bottomMargin=30)

    story = []
    
    # Página 1 - Moedas
    currency_img = Image(currency_chart, width=6 * inch, height=7 * inch)
    df_currencies = pd.read_csv('currency_data.csv')
    df_currencies = df_currencies.rename(columns={
        'Performance YTD (%)': 'YTD',
        'Performance Semanal (%)': 'Δ Semana'
    })

    # Criar dicionário para moedas
    currency_to_name = {}
    for currency, info in currencies.items():
        currency_to_name[info['ticker']] = info['name']
        if currency == 'DXY':
            currency_to_name['DXY'] = 'Índice do Dólar (DXY)'
    
    # Tabela de moedas
    currency_table_data = [['Moeda', 'YTD', 'Δ Semana']]
    for i, row in df_currencies.iterrows():
        try:
            if row['Moeda'] == 'DX-Y.NYB' or row['Moeda'] == 'DXY':
                name = 'Índice do Dólar (DXY)'
            else:
                name = currency_to_name[row['Moeda']]
            
            currency_table_data.append([
                name,
                f"{row['YTD']:+.2f}%",
                f"{row['Δ Semana']:+.2f}%"
            ])
        except KeyError as e:
            print(f"Erro na moeda: {row['Moeda']}")
            print(f"Dicionário disponível: {currency_to_name}")
            raise e

    currency_table = Table(currency_table_data, colWidths=[160, 80, 80])
    currency_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
    ]))

    currency_layout = Table([[currency_img, currency_table]], colWidths=[7.5*inch, 6*inch])
    currency_layout.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(currency_layout)
    story.append(PageBreak())  # Adiciona quebra de página

    # Página 2 - Commodities
    commodity_img = Image(commodity_chart, width=6 * inch, height=7 * inch)
    df_commodities = pd.read_csv('commodity_data.csv')
    df_commodities = df_commodities.rename(columns={
        'Performance YTD (%)': 'YTD',
        'Performance Semanal (%)': 'Δ Semana'
    })

    # Criar dicionário para commodities
    commodity_to_name = {}
    for commodity, info in commodities.items():
        commodity_to_name[info['ticker']] = info['name']
    
    # Tabela de commodities
    commodity_table_data = [['Commodity', 'YTD', 'Δ Semana']]
    for i, row in df_commodities.iterrows():
        try:
            name = commodity_to_name[row['Moeda']]
            commodity_table_data.append([
                name,
                f"{row['YTD']:+.2f}%",
                f"{row['Δ Semana']:+.2f}%"
            ])
        except KeyError as e:
            print(f"Erro na commodity: {row['Moeda']}")
            print(f"Dicionário disponível: {commodity_to_name}")
            raise e

    commodity_table = Table(commodity_table_data, colWidths=[160, 80, 80])
    commodity_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
    ]))

    commodity_layout = Table([[commodity_img, commodity_table]], colWidths=[7.5*inch, 6*inch])
    commodity_layout.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(commodity_layout)
    doc.build(story)

# Gerar ambos os relatórios
if __name__ == "__main__":
    # Gerar gráficos
    enhanced_chart = create_enhanced_chart()
    chart_path = "enhanced_chart.png"
    with open(chart_path, "wb") as f:
        f.write(enhanced_chart.getbuffer())

    enhanced_commodities_chart = create_enhanced_commodities_chart()
    commodities_chart_path = "enhanced_commodities_chart.png"
    with open(commodities_chart_path, "wb") as f:
        f.write(enhanced_commodities_chart.getbuffer())

    # Criar PDF combinado
    create_combined_pdf(chart_path, commodities_chart_path)

    # Limpar arquivos temporários
    os.remove(chart_path)
    os.remove(commodities_chart_path)
