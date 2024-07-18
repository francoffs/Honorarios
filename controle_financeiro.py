import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import locale
import os
import sys
from fpdf import FPDF
import time

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Função para obter o caminho relativo ao executável
def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Função para criar ou atualizar a tabela no banco de dados
def create_or_update_table():
    conn = sqlite3.connect(resource_path('clientes.db'))
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes
                 (codigo TEXT PRIMARY KEY, nome TEXT, contato TEXT, cpf TEXT, senha_egov TEXT, tipo_acao TEXT,
                  valor_honorarios REAL, resumo_caso TEXT, data_cadastro TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS parcelas
                 (codigo_cliente TEXT, numero_parcela INTEGER, valor_parcela REAL, data_pagamento TEXT, tipo_pagamento TEXT, conta_deposito TEXT, pago BOOLEAN, PRIMARY KEY (codigo_cliente, numero_parcela))''')
    conn.commit()
    conn.close()

# Função para adicionar cliente no banco de dados
def add_cliente(codigo, nome, contato, cpf, senha_egov, tipo_acao, valor_honorarios, resumo_caso, data_cadastro):
    try:
        conn = sqlite3.connect(resource_path('clientes.db'), timeout=10)
        c = conn.cursor()
        data_cadastro = data_cadastro.strftime('%d/%m/%Y')  # Convertendo datetime.date para string
        c.execute('INSERT INTO clientes (codigo, nome, contato, cpf, senha_egov, tipo_acao, valor_honorarios, resumo_caso, data_cadastro) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  (codigo, nome, contato, cpf, senha_egov, tipo_acao, valor_honorarios, resumo_caso, data_cadastro))
        conn.commit()
        conn.close()
        save_to_excel()
    except sqlite3.OperationalError:
        time.sleep(1)
        add_cliente(codigo, nome, contato, cpf, senha_egov, tipo_acao, valor_honorarios, resumo_caso, data_cadastro)

# Função para carregar dados do banco de dados
def load_data():
    conn = sqlite3.connect(resource_path('clientes.db'))
    df = pd.read_sql_query('SELECT * FROM clientes', conn)
    conn.close()
    return df

# Função para carregar parcelas do banco de dados
def load_parcelas(codigo_cliente):
    conn = sqlite3.connect(resource_path('clientes.db'))
    df = pd.read_sql_query('SELECT * FROM parcelas WHERE codigo_cliente = ?', conn, params=(codigo_cliente,))
    conn.close()
    return df

# Função para carregar todas as parcelas do banco de dados
def load_all_parcelas():
    conn = sqlite3.connect(resource_path('clientes.db'))
    df = pd.read_sql_query('SELECT * FROM parcelas', conn)
    conn.close()
    return df

# Função para carregar todas as parcelas com detalhes dos clientes
def load_all_parcelas_with_client_details():
    conn = sqlite3.connect(resource_path('clientes.db'))
    query = '''
    SELECT p.codigo_cliente, p.numero_parcela, p.valor_parcela, p.data_pagamento, p.conta_deposito, p.pago, c.nome
    FROM parcelas p
    JOIN clientes c ON p.codigo_cliente = c.codigo
    '''
    df = pd.read_sql_query(query, conn)
    df['data_pagamento'] = pd.to_datetime(df['data_pagamento'], format='%d/%m/%Y')
    conn.close()
    return df

# Função para gerar código único
def generate_code(df):
    if df.empty:
        return '0001'
    else:
        last_code = df['codigo'].iloc[-1]
        new_code = int(last_code) + 1
        return f'{new_code:04d}'

# Função para formatar o telefone
def formatar_telefone(telefone):
    telefone = ''.join(filter(str.isdigit, telefone))
    if len(telefone) == 11:
        return f'({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}'
    else:
        return telefone

# Função para formatar o CPF
def formatar_cpf(cpf):
    cpf = ''.join(filter(str.isdigit, cpf))
    if len(cpf) == 11:
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
    else:
        return cpf

# Função para formatar valores monetários
def formatar_valor(valor):
    return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

# Função para atualizar cliente no banco de dados
def update_cliente(codigo, nome, contato, cpf, senha_egov, tipo_acao, valor_honorarios, resumo_caso, data_cadastro):
    try:
        conn = sqlite3.connect(resource_path('clientes.db'), timeout=10)
        c = conn.cursor()
        data_cadastro = data_cadastro.strftime('%d/%m/%Y')  # Convertendo datetime.date para string
        c.execute('UPDATE clientes SET nome=?, contato=?, cpf=?, senha_egov=?, tipo_acao=?, valor_honorarios=?, resumo_caso=?, data_cadastro=? WHERE codigo=?',
                  (nome, contato, cpf, senha_egov, tipo_acao, valor_honorarios, resumo_caso, data_cadastro, codigo))
        conn.commit()
        conn.close()
        save_to_excel()
    except sqlite3.OperationalError:
        time.sleep(1)
        update_cliente(codigo, nome, contato, cpf, senha_egov, tipo_acao, valor_honorarios, resumo_caso, data_cadastro)

# Função para excluir cliente do banco de dados
def delete_cliente(codigo):
    try:
        conn = sqlite3.connect(resource_path('clientes.db'), timeout=10)
        c = conn.cursor()
        c.execute('DELETE FROM clientes WHERE codigo=?', (codigo,))
        conn.commit()
        conn.close()
        save_to_excel()
    except sqlite3.OperationalError:
        time.sleep(1)
        delete_cliente(codigo)

# Função para adicionar parcelas no banco de dados
def add_parcelas(codigo_cliente, numero_parcelas, valor_parcela):
    try:
        conn = sqlite3.connect(resource_path('clientes.db'), timeout=10)
        c = conn.cursor()
        for i in range(1, numero_parcelas + 1):
            data_pagamento = (datetime.today() + timedelta(days=(i-1) * 30)).strftime('%d/%m/%Y')
            c.execute('INSERT INTO parcelas (codigo_cliente, numero_parcela, valor_parcela, data_pagamento, pago) VALUES (?, ?, ?, ?, ?)',
                      (codigo_cliente, i, valor_parcela, data_pagamento, False))
        conn.commit()
        conn.close()
        save_to_excel()
    except sqlite3.OperationalError:
        time.sleep(1)
        add_parcelas(codigo_cliente, numero_parcelas, valor_parcela)

# Função para adicionar uma única parcela no banco de dados
def add_single_parcela(codigo_cliente, valor_parcela, data_pagamento, conta_deposito):
    try:
        conn = sqlite3.connect(resource_path('clientes.db'), timeout=10)
        c = conn.cursor()
        c.execute('SELECT MAX(numero_parcela) FROM parcelas WHERE codigo_cliente = ?', (codigo_cliente,))
        max_parcela = c.fetchone()[0]
        if max_parcela is None:
            max_parcela = 0
        numero_parcela = max_parcela + 1
        data_pagamento = data_pagamento.strftime('%d/%m/%Y')
        c.execute('INSERT INTO parcelas (codigo_cliente, numero_parcela, valor_parcela, data_pagamento, conta_deposito, pago) VALUES (?, ?, ?, ?, ?, ?)',
                  (codigo_cliente, numero_parcela, valor_parcela, data_pagamento, conta_deposito, False))
        conn.commit()
        conn.close()
        save_to_excel()
    except sqlite3.OperationalError:
        time.sleep(1)
        add_single_parcela(codigo_cliente, valor_parcela, data_pagamento, conta_deposito)

# Função para atualizar parcela no banco de dados
def update_parcela(codigo_cliente, numero_parcela, valor_parcela, data_pagamento, tipo_pagamento, conta_deposito, pago):
    try:
        conn = sqlite3.connect(resource_path('clientes.db'), timeout=10)
        c = conn.cursor()
        data_pagamento = datetime.strptime(data_pagamento, '%d/%m/%Y').strftime('%d/%m/%Y')  # Convertendo string para o formato correto
        c.execute('UPDATE parcelas SET valor_parcela=?, data_pagamento=?, tipo_pagamento=?, conta_deposito=?, pago=? WHERE codigo_cliente=? AND numero_parcela=?',
                  (valor_parcela, data_pagamento, tipo_pagamento, conta_deposito, pago, codigo_cliente, numero_parcela))
        conn.commit()
        conn.close()
        save_to_excel()
    except sqlite3.OperationalError:
        time.sleep(1)
        update_parcela(codigo_cliente, numero_parcela, valor_parcela, data_pagamento, tipo_pagamento, conta_deposito, pago)

# Função para carregar parcelas pagas agrupadas por mês e ano da planilha Excel
def load_parcelas_pagas_agrupadas_from_excel():
    for _ in range(5):  # Tenta 5 vezes
        try:
            df_parcelas = pd.read_excel('backup_clientes.xlsx', sheet_name='Parcelas')
            df_parcelas_pagas = df_parcelas[df_parcelas['pago'] == True]
            df_parcelas_pagas['data_pagamento'] = pd.to_datetime(df_parcelas_pagas['data_pagamento'], format='%d/%m/%Y')
            df_parcelas_pagas['mes'] = df_parcelas_pagas['data_pagamento'].dt.month
            df_parcelas_pagas['ano'] = df_parcelas_pagas['data_pagamento'].dt.year
            df_agrupado = df_parcelas_pagas.groupby(['mes', 'ano']).agg({'valor_parcela': 'sum'}).reset_index()
            df_agrupado['mes'] = df_agrupado['mes'].apply(lambda x: datetime.strptime(str(x), '%m').strftime('%B'))
            return df_agrupado
        except PermissionError:
            time.sleep(1)  # Espera 1 segundo antes de tentar novamente

# Função para carregar todas as parcelas não pagas da planilha Excel
def load_parcelas_nao_pagas_from_excel():
    for _ in range(5):  # Tenta 5 vezes
        try:
            df_parcelas = pd.read_excel('backup_clientes.xlsx', sheet_name='Parcelas')
            df_parcelas_nao_pagas = df_parcelas[df_parcelas['pago'] == False]
            df_parcelas_nao_pagas['data_pagamento'] = pd.to_datetime(df_parcelas_nao_pagas['data_pagamento'], format='%d/%m/%Y')
            df_parcelas_nao_pagas['mes'] = df_parcelas_nao_pagas['data_pagamento'].dt.month
            df_parcelas_nao_pagas['ano'] = df_parcelas_nao_pagas['data_pagamento'].dt.year
            df_agrupado = df_parcelas_nao_pagas.groupby(['mes', 'ano']).agg({'valor_parcela': 'sum'}).reset_index()
            df_agrupado['mes'] = df_agrupado['mes'].apply(lambda x: datetime.strptime(str(x), '%m').strftime('%B'))
            return df_agrupado, df_parcelas_nao_pagas
        except PermissionError:
            time.sleep(1)  # Espera 1 segundo antes de tentar novamente

# Função para formatar data para exibição
def formatar_data(data):
    if pd.isnull(data):
        return ''
    else:
        return datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')

# Função para salvar os dados em um arquivo Excel
def save_to_excel():
    for _ in range(5):  # Tenta 5 vezes
        try:
            conn = sqlite3.connect(resource_path('clientes.db'))
            df_clientes = pd.read_sql_query('SELECT * FROM clientes', conn)
            df_parcelas = pd.read_sql_query('SELECT * FROM parcelas', conn)
            conn.close()

            with pd.ExcelWriter('backup_clientes.xlsx') as writer:
                df_clientes.to_excel(writer, sheet_name='Clientes', index=False)
                df_parcelas.to_excel(writer, sheet_name='Parcelas', index=False)
            break  # Sai do loop se a operação for bem-sucedida
        except PermissionError:
            time.sleep(1)  # Espera 1 segundo antes de tentar novamente

# Classe para criar PDF
class PDF(FPDF):
    def header(self):
        self.image(resource_path('LOGO.png'), 10, 8, 33)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório de Parcelas', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Página %s de %s' % (self.page_no(), '{nb}'), 0, 0, 'C')
        self.line(10, self.get_y() - 5, 200, self.get_y() - 5)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

def generate_pdf(cliente_info, parcelas):
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Nome do cliente
    pdf.chapter_title(f"Nome do Cliente: {cliente_info['nome']}")

    # Tipo de Ação
    pdf.chapter_title(f"Tipo de Ação: {cliente_info['tipo_acao']}")

    # Valor dos Honorários
    pdf.chapter_title(f"Valor Total dos Honorários: {formatar_valor(cliente_info['valor_honorarios'])}")

    # Detalhamento das Parcelas
    pdf.chapter_title("Detalhamento das Parcelas:")
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(30, 10, 'Nº da Parcela', 1)
    pdf.cell(30, 10, 'Valor', 1)
    pdf.cell(50, 10, 'Data de Vencimento', 1)
    pdf.cell(30, 10, 'Pagamento', 1)
    pdf.cell(50, 10, 'Data do Pagamento', 1)
    pdf.ln()

    pdf.set_font('Arial', '', 12)
    total_a_pagar = 0
    for i in range(len(parcelas)):
        numero_parcela = str(i + 1)
        valor_parcela = formatar_valor(parcelas.iloc[i]['valor_parcela'])
        data_vencimento = datetime.strptime(parcelas.iloc[i]['data_pagamento'], '%d/%m/%Y').strftime('%d/%m/%Y')
        pagamento = 'Sim' if parcelas.iloc[i]['pago'] else 'Não'
        data_pagamento = datetime.strptime(parcelas.iloc[i]['data_pagamento'], '%d/%m/%Y').strftime('%d/%m/%Y') if parcelas.iloc[i]['pago'] else ''
        total_a_pagar += parcelas.iloc[i]['valor_parcela'] if not parcelas.iloc[i]['pago'] else 0

        pdf.cell(30, 10, numero_parcela, 1)
        pdf.cell(30, 10, valor_parcela, 1)
        pdf.cell(50, 10, data_vencimento, 1)
        pdf.cell(30, 10, pagamento, 1)
        pdf.cell(50, 10, data_pagamento, 1)
        pdf.ln()

    # Total a pagar
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Total a Pagar: {formatar_valor(total_a_pagar)}", 0, 1, 'L')

    # Salvar PDF
    pdf_file = 'relatorio_parcelas.pdf'
    pdf.output(pdf_file)

    return pdf_file

# Criar ou atualizar a tabela
create_or_update_table()

# Carregar dados existentes
df_clients = load_data()

# Configuração da página principal
logo_path = resource_path('LOGO.png')
st.image(logo_path, width=150)
st.title('SISTEMA DE CONTROLE DE HONORÁRIOS ADVOCATÍCIOS')

# Variável para armazenar a página atual
if 'page' not in st.session_state:
    st.session_state.page = 'CADASTRO DE CLIENTE'

# Variável para armazenar o cliente selecionado
if 'cliente_selecionado' not in st.session_state:
    st.session_state.cliente_selecionado = None

# Variável para armazenar o número de parcelas e o valor das parcelas
if 'numero_parcelas' not in st.session_state:
    st.session_state.numero_parcelas = 0

if 'valor_parcela' not in st.session_state:
    st.session_state.valor_parcela = 0

# Variável para armazenar a adição de novas parcelas
if 'adicionando_parcela' not in st.session_state:
    st.session_state.adicionando_parcela = False

# Barra lateral para seleção de página
with st.sidebar:
    if st.button('CADASTRO DE CLIENTE'):
        st.session_state.page = 'CADASTRO DE CLIENTE'
        st.session_state.cliente_selecionado = None
    if st.button('CONSULTA DE CLIENTES'):
        st.session_state.page = 'CONSULTA DE CLIENTES'
        st.session_state.cliente_selecionado = None
    if st.button('PARCELAS VENCIDAS'):
        st.session_state.page = 'PARCELAS VENCIDAS'
    if st.button('PARCELAS PAGAS'):
        st.session_state.page = 'PARCELAS PAGAS'
    if st.button('VALORES A RECEBER'):
        st.session_state.page = 'VALORES A RECEBER'
    if st.session_state.page == 'CONTROLE FINANCEIRO' or st.session_state.page == 'DETALHE FINANCEIRO':
        if st.button('VOLTAR'):
            st.session_state.page = 'CONSULTA DE CLIENTES'
            st.session_state.cliente_selecionado = None

page = st.session_state.page

if page == 'CADASTRO DE CLIENTE':
    st.header('CADASTRO DE CLIENTES')

    # Gerar código do cliente
    codigo = generate_code(df_clients)

    # Campos de entrada
    nome = st.text_input('NOME').upper()
    telefone_raw = st.text_input('CONTATO (APENAS NÚMEROS)')
    telefone = formatar_telefone(telefone_raw)
    cpf_raw = st.text_input('CPF (APENAS NÚMEROS)')
    cpf = formatar_cpf(cpf_raw)
    senha_egov = st.text_input('SENHA E-GOV', type='password').upper()
    tipo_acao = st.text_input('TIPO DE AÇÃO').upper()
    valor_honorarios_contratados = st.number_input('VALOR DOS HONORÁRIOS CONTRATADOS (R$)', min_value=0.0, format='%.2f')
    resumo_caso = st.text_area('RESUMO DO CASO').upper()
    data_cadastro = st.date_input('DATA', datetime.today())  # Retorna um objeto datetime.date

    # Exibir telefone e CPF formatados
    st.write(f'TELEFONE FORMATADO: {telefone}')
    st.write(f'CPF FORMATADO: {cpf}')
    st.write(f'VALOR DOS HONORÁRIOS: {formatar_valor(valor_honorarios_contratados)}')

    # Botão de submissão
    if st.button('CADASTRAR CLIENTE'):
        if len(telefone) != 15:
            st.error('FORMATO DE TELEFONE INVÁLIDO. CERTIFIQUE-SE DE INSERIR 11 DÍGITOS NUMÉRICOS.')
        elif len(cpf) != 14:
            st.error('FORMATO DE CPF INVÁLIDO. CERTIFIQUE-SE DE INSERIR 11 DÍGITOS NUMÉRICOS.')
        else:
            add_cliente(codigo, nome, telefone, cpf, senha_egov, tipo_acao, valor_honorarios_contratados, resumo_caso, data_cadastro)
            st.success(f'CLIENTE {nome} CADASTRADO COM SUCESSO!')
            df_clients = load_data()

elif page == 'CONSULTA DE CLIENTES':
    st.header('CLIENTES CADASTRADOS')
    search_term = st.text_input('PESQUISAR POR NOME', on_change=lambda: st.session_state.update(cliente_selecionado=None))
    
    if search_term:
        filtered_df = df_clients[df_clients['nome'].str.contains(search_term.upper(), case=False, na=False)]
    else:
        filtered_df = df_clients

    st.dataframe(filtered_df[['codigo', 'nome', 'tipo_acao']].reset_index(drop=True))

    cliente_selecionado = st.selectbox('SELECIONE UM CLIENTE PARA EDITAR OU EXCLUIR', [''] + list(filtered_df['codigo'].values))

    if cliente_selecionado:
        st.session_state.cliente_selecionado = cliente_selecionado

    if st.session_state.cliente_selecionado:
        cliente_info = filtered_df[filtered_df['codigo'] == st.session_state.cliente_selecionado].iloc[0]

        if st.button('EXCLUIR CLIENTE'):
            delete_cliente(st.session_state.cliente_selecionado)
            st.success(f'CLIENTE {cliente_info["nome"]} EXCLUÍDO COM SUCESSO!')
            st.session_state.cliente_selecionado = None
            df_clients = load_data()
            st.experimental_rerun()
        
        with st.form(key='edit_form'):
            st.write('---')
            st.write('**EDITAR CLIENTE**')
            nome_edit = st.text_input('NOME', cliente_info['nome'], key='nome_edit').upper()
            telefone_raw_edit = st.text_input('CONTATO (APENAS NÚMEROS)', cliente_info['contato'], key='telefone_edit')
            telefone_edit = formatar_telefone(telefone_raw_edit)
            cpf_raw_edit = st.text_input('CPF (APENAS NÚMEROS)', cliente_info['cpf'], key='cpf_edit')
            cpf_edit = formatar_cpf(cpf_raw_edit)
            senha_egov_edit = st.text_input('SENHA E-GOV', cliente_info['senha_egov'], type='password', key='senha_egov_edit').upper()
            tipo_acao_edit = st.text_input('TIPO DE AÇÃO', cliente_info['tipo_acao'], key='tipo_acao_edit').upper()
            valor_honorarios_contratados_edit = st.number_input('VALOR DOS HONORÁRIOS CONTRATADOS (R$)', min_value=0.0, format='%.2f', value=cliente_info['valor_honorarios'], key='valor_honorarios_edit')
            resumo_caso_edit = st.text_area('RESUMO DO CASO', cliente_info['resumo_caso'], key='resumo_caso_edit').upper()
            data_cadastro_edit = st.date_input('DATA', datetime.strptime(cliente_info['data_cadastro'], '%d/%m/%Y'), key='data_cadastro_edit')

            st.write(f'VALOR DOS HONORÁRIOS: {formatar_valor(valor_honorarios_contratados_edit)}')

            submit_button = st.form_submit_button(label='SALVAR ALTERAÇÕES')
            controle_button = st.form_submit_button(label='CONTROLE FINANCEIRO')

            if submit_button:
                update_cliente(st.session_state.cliente_selecionado, nome_edit, telefone_edit, cpf_edit, senha_egov_edit, tipo_acao_edit, valor_honorarios_contratados_edit, resumo_caso_edit, data_cadastro_edit)
                st.success(f'CLIENTE {nome_edit} ATUALIZADO COM SUCESSO!')
                st.session_state.cliente_selecionado = None
                df_clients = load_data()
                st.experimental_rerun()

            if controle_button:
                st.session_state.page = 'CONTROLE FINANCEIRO'
                st.experimental_rerun()

elif page == 'CONTROLE FINANCEIRO':
    if st.session_state.cliente_selecionado:
        cliente_info = df_clients[df_clients['codigo'] == st.session_state.cliente_selecionado].iloc[0]
        st.header('CONTROLE FINANCEIRO')
        st.write(f"**NOME:** {cliente_info['nome']}")
        st.write(f"**TIPO DE AÇÃO:** {cliente_info['tipo_acao']}")
        st.write(f"**VALOR DOS HONORÁRIOS CONTRATADOS:** {formatar_valor(cliente_info['valor_honorarios'])}")

        parcelas = load_parcelas(cliente_info['codigo'])

        if parcelas.empty:
            numero_parcelas = st.number_input('NÚMERO DE PARCELAS', min_value=1, format='%d')
            calcular_button = st.button('CALCULAR PARCELAS')

            if calcular_button:
                valor_parcela = cliente_info['valor_honorarios'] / numero_parcelas
                add_parcelas(cliente_info['codigo'], numero_parcelas, valor_parcela)
                st.session_state.numero_parcelas = numero_parcelas
                st.session_state.valor_parcela = valor_parcela
                st.experimental_rerun()
        else:
            st.session_state.page = 'DETALHE FINANCEIRO'
            st.experimental_rerun()

elif page == 'DETALHE FINANCEIRO':
    if st.session_state.cliente_selecionado:
        cliente_info = df_clients[df_clients['codigo'] == st.session_state.cliente_selecionado].iloc[0]
        st.header('DETALHAMENTO DAS PARCELAS')
        st.write(f"**NOME:** {cliente_info['nome']}")
        st.write(f"**TIPO DE AÇÃO:** {cliente_info['tipo_acao']}")
        st.write(f"**VALOR DOS HONORÁRIOS CONTRATADOS:** {formatar_valor(cliente_info['valor_honorarios'])}")

        parcelas = load_parcelas(cliente_info['codigo'])
        total_parcelas = 0
        saldo_a_pagar = 0

        for i in range(len(parcelas)):
            with st.form(key=f'parcela_form_{i+1}'):
                st.write(f"**PARCELA {i+1}**")
                valor_parcela = st.number_input('VALOR DA PARCELA', min_value=0.0, format='%.2f', value=parcelas.iloc[i]['valor_parcela'], key=f'valor_parcela_{i+1}')
                total_parcelas += valor_parcela
                pago = st.checkbox('PAGO', value=parcelas.iloc[i]['pago'], key=f'pago_{i+1}')
                if not pago:
                    saldo_a_pagar += valor_parcela
                data_pagamento = st.date_input('DATA DO PAGAMENTO', value=datetime.strptime(parcelas.iloc[i]['data_pagamento'], '%d/%m/%Y') if parcelas.iloc[i]['data_pagamento'] else datetime.today() + timedelta(days=30*i), key=f'data_pagamento_{i+1}')
                conta_deposito = st.text_input('CONTA DE DEPÓSITO', value=parcelas.iloc[i]['conta_deposito'] if parcelas.iloc[i]['conta_deposito'] else '', key=f'conta_deposito_{i+1}')
                salvar_button = st.form_submit_button(label='SALVAR')

                st.write(f'VALOR DA PARCELA: {formatar_valor(valor_parcela)}')

                if salvar_button:
                    update_parcela(cliente_info['codigo'], i+1, valor_parcela, data_pagamento.strftime('%d/%m/%Y'), None, conta_deposito, pago)
                    st.success(f'PARCELA {i+1} ATUALIZADA COM SUCESSO!')

        st.write(f"**SALDO A PAGAR:** {formatar_valor(saldo_a_pagar)}")

        if total_parcelas != cliente_info['valor_honorarios']:
            st.error(f"A SOMA DAS PARCELAS ({formatar_valor(total_parcelas)}) NÃO CORRESPONDE AO VALOR TOTAL DOS HONORÁRIOS CONTRATADOS ({formatar_valor(cliente_info['valor_honorarios'])}). POR FAVOR, AJUSTE OS VALORES DAS PARCELAS.")

        st.write('---')
        if st.button('ADICIONAR PARCELA'):
            st.session_state.adicionando_parcela = True

        if st.session_state.adicionando_parcela:
            with st.form(key='nova_parcela_form'):
                st.write('**NOVA PARCELA**')
                novo_valor_parcela = st.number_input('VALOR DA NOVA PARCELA', min_value=0.0, format='%.2f')
                nova_data_pagamento = st.date_input('DATA DO PAGAMENTO', value=datetime.today())
                nova_conta_deposito = st.text_input('CONTA DE DEPÓSITO')
                salvar_nova_parcela_button = st.form_submit_button(label='SALVAR NOVA PARCELA')

                if salvar_nova_parcela_button:
                    novo_total_parcelas = total_parcelas + novo_valor_parcela
                    if novo_total_parcelas > cliente_info['valor_honorarios']:
                        st.error(f"O valor total das parcelas ({formatar_valor(novo_total_parcelas)}) não pode exceder o valor total dos honorários contratados ({formatar_valor(cliente_info['valor_honorarios'])}).")
                    else:
                        add_single_parcela(cliente_info['codigo'], novo_valor_parcela, nova_data_pagamento, nova_conta_deposito)
                        st.success('Nova parcela adicionada com sucesso!')
                        st.session_state.adicionando_parcela = False
                        st.experimental_rerun()

        # Adicionar o botão de impressão
        if st.button('IMPRIMIR'):
            pdf_file = generate_pdf(cliente_info, parcelas)
            with open(pdf_file, 'rb') as f:
                st.download_button('Baixar PDF', f, file_name=pdf_file)

elif page == 'PARCELAS VENCIDAS':
    st.header('PARCELAS VENCIDAS NÃO PAGAS')

    todas_parcelas = load_all_parcelas_with_client_details()
    hoje = datetime.today()

    # Filtro de parcelas vencidas e não pagas
    todas_parcelas['data_pagamento'] = pd.to_datetime(todas_parcelas['data_pagamento'], format='%d/%m/%Y')
    parcelas_vencidas = todas_parcelas[(todas_parcelas['data_pagamento'] < hoje) & (todas_parcelas['pago'] == False)]

    # Selecionar as colunas desejadas
    parcelas_vencidas = parcelas_vencidas[['nome', 'numero_parcela', 'valor_parcela', 'data_pagamento', 'conta_deposito']]

    # Formatar os valores das parcelas
    parcelas_vencidas['valor_parcela'] = parcelas_vencidas['valor_parcela'].apply(lambda x: formatar_valor(x))

    # Calcular o total das parcelas vencidas e não pagas
    total_vencido = parcelas_vencidas['valor_parcela'].apply(lambda x: float(x.replace('R$', '').replace('.', '').replace(',', '.'))).sum()

    st.dataframe(parcelas_vencidas.reset_index(drop=True))
    st.write(f"**TOTAL VENCIDO:** {formatar_valor(total_vencido)}")

elif page == 'PARCELAS PAGAS':
    st.header('PARCELAS PAGAS AGRUPADAS POR MÊS E ANO')

    # Carregar parcelas pagas agrupadas
    df_parcelas_pagas = load_parcelas_pagas_agrupadas_from_excel()

    # Formatar os valores recebidos
    df_parcelas_pagas['valor_parcela'] = df_parcelas_pagas['valor_parcela'].apply(lambda x: formatar_valor(x))

    # Opções de filtragem
    meses = df_parcelas_pagas['mes'].unique().tolist()
    anos = df_parcelas_pagas['ano'].unique().tolist()

    filtro_mes = st.selectbox('FILTRAR POR MÊS', ['TODOS'] + meses)
    filtro_ano = st.selectbox('FILTRAR POR ANO', ['TODOS'] + anos)

    # Aplicar filtro
    if filtro_mes != 'TODOS':
        df_parcelas_pagas = df_parcelas_pagas[df_parcelas_pagas['mes'] == filtro_mes]
    if filtro_ano != 'TODOS':
        df_parcelas_pagas = df_parcelas_pagas[df_parcelas_pagas['ano'] == filtro_ano]

    # Exibir tabela
    st.dataframe(df_parcelas_pagas[['mes', 'ano', 'valor_parcela']].reset_index(drop=True))

elif page == 'VALORES A RECEBER':
    st.header('VALORES A RECEBER')

    # Carregar parcelas não pagas
    df_agrupado, df_parcelas_nao_pagas = load_parcelas_nao_pagas_from_excel()

    # Formatar os valores das parcelas
    df_agrupado['valor_parcela'] = df_agrupado['valor_parcela'].apply(lambda x: formatar_valor(x))

    # Selecionar as colunas desejadas
    df_agrupado = df_agrupado[['mes', 'ano', 'valor_parcela']]

    # Calcular o total dos valores a receber
    total_a_receber = df_agrupado['valor_parcela'].apply(lambda x: float(x.replace('R$', '').replace('.', '').replace(',', '.'))).sum()

    st.dataframe(df_agrupado.reset_index(drop=True))
    st.write(f"**TOTAL A RECEBER:** {formatar_valor(total_a_receber)}")

    # Filtros para detalhamento
    filtro_mes = st.selectbox('FILTRAR POR MÊS', ['TODOS'] + df_agrupado['mes'].unique().tolist())
    filtro_ano = st.selectbox('FILTRAR POR ANO', ['TODOS'] + df_agrupado['ano'].unique().tolist())

    df_detalhado = df_parcelas_nao_pagas.copy()

    if filtro_mes != 'TODOS':
        df_detalhado = df_detalhado[df_detalhado['mes'] == datetime.strptime(filtro_mes, '%B').month]
    if filtro_ano != 'TODOS':
        df_detalhado = df_detalhado[df_detalhado['ano'] == int(filtro_ano)]

    # Convertendo 'codigo_cliente' e 'codigo' para string
    df_detalhado['codigo_cliente'] = df_detalhado['codigo_cliente'].astype(str)
    df_clients['codigo'] = df_clients['codigo'].astype(str)

    # Merge com os dados dos clientes para obter o nome
    df_detalhado = df_detalhado.merge(df_clients[['codigo', 'nome']], left_on='codigo_cliente', right_on='codigo')

    # Selecionar colunas desejadas
    df_detalhado = df_detalhado[['nome', 'valor_parcela', 'data_pagamento']]
    
    # Formatar os valores das parcelas e as datas
    df_detalhado['valor_parcela'] = df_detalhado['valor_parcela'].apply(lambda x: formatar_valor(x))
    df_detalhado['data_pagamento'] = df_detalhado['data_pagamento'].apply(lambda x: x.strftime('%d/%m/%Y'))
    
    st.write('**DETALHAMENTO DOS VALORES A RECEBER**')
    st.dataframe(df_detalhado.reset_index(drop=True))
