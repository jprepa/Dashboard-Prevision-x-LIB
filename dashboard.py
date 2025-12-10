import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO GLOBAL ---
st.set_page_config(page_title="Prevision X LIB", layout="wide")

# Estilo CSS
st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #262730;
    border: 1px solid #444;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
}
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES (BLINDAGEM DE DADOS) ---
def is_true(val):
    # Converte para string, tira espaços extras e joga para minúsculo
    texto = str(val).strip().lower()
    # Lista de valores aceitos como "Sim"
    aceitos = ['sim', 's', 'yes', 'y', 'verdadeiro', 'true', 'ativo', '1', '1.0']
    return texto in aceitos

def get_index(lista_colunas, nomes_buscados):
    """Procura se algum dos nomes_buscados existe na lista_colunas e retorna o índice."""
    if isinstance(nomes_buscados, str):
        nomes_buscados = [nomes_buscados]
    
    for nome in nomes_buscados:
        # Tenta achar exato
        if nome in lista_colunas:
            return lista_colunas.index(nome)
        # Tenta achar ignorando maiúsculas/minúsculas (fallback)
        for i, col_real in enumerate(lista_colunas):
            if str(col_real).strip().lower() == str(nome).strip().lower():
                return i
    return 0 

# --- BARRA LATERAL: SELEÇÃO DE MODO ---
st.sidebar.title("🎛️ Controle do Painel")
modo_visualizacao = st.sidebar.radio("Qual visão você deseja?", ["Análise Prevision", "Análise LIB"])

st.sidebar.markdown("---")
st.sidebar.header("1. Carregar Arquivo")
uploaded_file = st.sidebar.file_uploader("Suba o arquivo Excel", type=["xlsx", "xls"])

# ==============================================================================
# MODO 1: ANÁLISE PREVISION (INTERNA)
# ==============================================================================
if modo_visualizacao == "Análise Prevision":
    st.title("📊 Painel Estratégico Prevision")
    
    if uploaded_file is not None:
        try:
            excel_file = pd.ExcelFile(uploaded_file)
            
            abas = excel_file.sheet_names
            idx_aba = abas.index("Clientes") if "Clientes" in abas else 0
            
            selected_sheet = st.sidebar.selectbox("Escolha a aba:", abas, index=idx_aba, key="sheet_internal")
            
            df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            
            if df.empty:
                st.error("Aba vazia.")
            else:
                # --- MAPEAMENTO AUTOMÁTICO ---
                st.sidebar.markdown("---")
                st.sidebar.header("Mapear Colunas")
                cols = df.columns.tolist()
                
                idx_cli = get_index(cols, ["Cliente", "Nome Fantasia", "Empresa"])
                idx_prt = get_index(cols, ["Porte", "CNPJ", "Tamanho"])
                
                c_cliente = st.sidebar.selectbox("Nome do Cliente:", cols, index=idx_cli, key="cli_in")
                c_porte = st.sidebar.selectbox("Porte:", cols, index=idx_prt, key="porte_in")
                
                st.sidebar.markdown("---")
                st.sidebar.info("Colunas de Flags (Sim/Não)")
                
                cols_flags = ["(Não usar)"] + cols
                
                def get_flag_index(target_names):
                    # Procura o índice + 1 (pois temos o '(Não usar)' na frente)
                    idx_found = get_index(cols, target_names)
                    # Se achou a coluna 0 mas o nome não bate com a busca (é falso positivo), retorna 0
                    if idx_found == 0:
                        # Verifica se realmente a primeira coluna é uma das buscadas
                        first_col_name = cols[0]
                        if any(t.lower() == str(first_col_name).lower() for t in target_names):
                            return 1
                        return 0
                    return idx_found + 1

                # LISTAS DE SINÔNIMOS ATUALIZADAS
                idx_icp = get_flag_index(["ICP", "É ICP?", "Perfil Ideal"])
                idx_hot = get_flag_index(["Prospect Quente", "Quente", "Hot", "Prioridade"])
                idx_opp = get_flag_index(["Oportunidade", "Opp", "Negócio"])
                
                # AQUI ESTÁ A CORREÇÃO PRINCIPAL: Adicionei a variação exata com '?'
                idx_prev = get_flag_index(["É Cliente Prevision?", "É Cliente Prevision", "Cliente Prevision", "Já é Cliente?"])
                
                idx_ecos = get_flag_index(["É cliente Ecossistema", "Ecossistema", "Cliente Ecossistema", "Parceiro"])

                c_icp = st.sidebar.selectbox("Coluna Total ICPs:", cols_flags, index=idx_icp)
                c_icp_quente = st.sidebar.selectbox("Coluna ICP Quente (18):", cols_flags, index=idx_hot)
                c_oportunidade = st.sidebar.selectbox("Coluna Oportunidade (30):", cols_flags, index=idx_opp)
                
                # Verifica visualmente se ele selecionou certo
                c_prev = st.sidebar.selectbox("Coluna Cliente Prevision (6):", cols_flags, index=idx_prev)
                c_ecos = st.sidebar.selectbox("Coluna Cliente Ecossistema:", cols_flags, index=idx_ecos)
                
                # --- PROCESSAMENTO ---
                val_total = len(df)
                val_icp = len(df[df[c_icp].apply(is_true)]) if c_icp != "(Não usar)" else 0
                val_hot = len(df[df[c_icp_quente].apply(is_true)]) if c_icp_quente != "(Não usar)" else 0
                val_opp = len(df[df[c_oportunidade].apply(is_true)]) if c_oportunidade != "(Não usar)" else 0
                val_prev = len(df[df[c_prev].apply(is_true)]) if c_prev != "(Não usar)" else 0
                val_ecos_only = len(df[df[c_ecos].apply(is_true)]) if c_ecos != "(Não usar)" else 0
                
                val_ecos_merged = val_prev + val_ecos_only

                config_grupos = [
                    ("Total Mapeado", "ALL_ROWS"),
                    ("Total ICPs", c_icp),
                    ("Oportunidades Quentes", c_icp_quente),
                    ("ICP", c_oportunidade),
                    ("Clientes Prevision", c_prev),
                    ("Clientes Ecossistema", c_ecos)
                ]
                
                resumo_barras = {'Categoria': [], 'Quantidade': [], 'Lista_Clientes': []}
                lista_matriz = []
                
                for nome_grupo, col_excel in config_grupos:
                    if col_excel != "(Não usar)":
                        if col_excel == "ALL_ROWS":
                            filtro = df
                        else:
                            filtro = df[df[col_excel].apply(is_true)]
                        
                        resumo_barras['Categoria'].append(nome_grupo)
                        resumo_barras['Quantidade'].append(len(filtro))
                        resumo_barras['Lista_Clientes'].append(filtro[c_cliente].tolist())
                        
                        for _, row in filtro.iterrows():
                            lista_matriz.append({'Porte': row[c_porte], 'Status': nome_grupo, 'Cliente': row[c_cliente]})

                df_resumo = pd.DataFrame(resumo_barras)
                df_matriz_source = pd.DataFrame(lista_matriz)

                # --- VISUALIZAÇÃO ---
                st.divider()
                
                k1, k2, k3, k4, k5 = st.columns(5)
                k1.metric("Total Mapeado", val_total)
                k2.metric("Oportunidades (Geral)", val_icp)
                k3.metric("Oportunidades Quentes", val_hot)
                k4.metric("Clientes Prevision", val_prev)
                k5.metric("Clientes Ecossistema", val_ecos_merged, help="Clientes Prevision + Clientes Ecossistema")
                
                st.markdown("---")
                
                c_bar, c_pie = st.columns([1.5, 1])
                
                with c_bar:
                    st.subheader("Funil Geral")
                    fig_bar = px.bar(df_resumo, x='Quantidade', y='Categoria', orientation='h', text='Quantidade', color='Categoria')
                    fig_bar.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None)
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                with c_pie:
                    st.subheader("Distribuição ICPs")
                    # Evita erro na pizza se tudo for zero
                    dados_pizza = [
                        {"Label": "Oportunidades Quentes", "Valor": val_hot},
                        {"Label": "Oportunidades (Geral)", "Valor": val_opp},
                        {"Label": "Clientes Prevision", "Valor": val_prev}
                    ]
                    # Filtra valores zero para a pizza não ficar feia
                    dados_pizza = [d for d in dados_pizza if d['Valor'] > 0]
                    
                    if dados_pizza:
                        fig_pie = px.pie(pd.DataFrame(dados_pizza), names='Label', values='Valor', hole=0.5, 
                                         color_discrete_sequence=["#00CC96", "#AB63FA", "#FFA15A"])
                        fig_pie.update_traces(textposition='inside', textinfo='value+label')
                        fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
                        st.plotly_chart(fig_pie, use_container_width=True)
                    else:
                        st.info("Sem dados suficientes para gerar o gráfico de pizza.")
                
                st.markdown("---")
                c_matriz, c_lista = st.columns([1.5, 1])
                
                filtro_ativo = False
                df_filtrado_show = pd.DataFrame()
                msg_filtro = ""

                with c_matriz:
                    st.subheader("Matriz")
                    if not df_matriz_source.empty:
                        matriz_final = pd.crosstab(df_matriz_source['Porte'], df_matriz_source['Status'])
                        fig_heat = px.imshow(matriz_final, text_auto=True, aspect="auto", color_continuous_scale='Viridis')
                        selection = st.plotly_chart(fig_heat, use_container_width=True, on_select="rerun", selection_mode="points")
                    else:
                        selection = None

                with c_lista:
                    st.subheader("Detalhes")
                    if selection:
                        try:
                            pts = selection.get('selection', {}).get('points', [])
                            if not pts and 'points' in selection: pts = selection['points']
                            
                            if pts:
                                p = pts[0]
                                status_c = p['x']
                                porte_c = p['y']
                                msg_filtro = f"Filtro: {status_c} + {porte_c}"
                                clientes_alvo = df_matriz_source[(df_matriz_source['Status']==status_c) & (df_matriz_source['Porte']==porte_c)]['Cliente'].unique()
                                df_filtrado_show = df[df[c_cliente].isin(clientes_alvo)]
                                filtro_ativo = True
                        except: pass
                    
                    if not filtro_ativo:
                        grupo = st.selectbox("Selecione grupo:", df_resumo['Categoria'].unique(), key="sel_g_in")
                        if grupo:
                            row = df_resumo[df_resumo['Categoria']==grupo].iloc[0]
                            df_filtrado_show = df[df[c_cliente].isin(row['Lista_Clientes'])]
                    
                    if not df_filtrado_show.empty:
                        st.info(msg_filtro if filtro_ativo else "Listando Grupo Inteiro")
                        st.dataframe(df_filtrado_show[[c_cliente, c_porte]], hide_index=True, use_container_width=True, height=300)

        except Exception as e:
            st.error(f"Erro no Painel Prevision: {e}")

# ==============================================================================
# MODO 2: ANÁLISE LIB (PARCEIRO)
# ==============================================================================
elif modo_visualizacao == "Análise LIB":
    st.title("📊 Painel Estratégico LIB")
    
    if uploaded_file is not None:
        try:
            excel_file = pd.ExcelFile(uploaded_file)
            
            abas = excel_file.sheet_names
            idx_aba_p = abas.index("Planilha1") if "Planilha1" in abas else (1 if len(abas)>1 else 0)
            
            selected_sheet = st.sidebar.selectbox("Escolha a aba:", abas, index=idx_aba_p, key="sheet_partner")
            
            df_parceiro = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            
            if df_parceiro.empty:
                st.error("Aba vazia.")
            else:
                st.sidebar.markdown("---")
                st.sidebar.header("Configuração da Base LIB")
                cols_p = df_parceiro.columns.tolist()
                
                idx_cli_p = get_index(cols_p, "Cliente")
                idx_prt_p = get_index(cols_p, "Porte")
                
                c_cliente_p = st.sidebar.selectbox("Coluna Cliente:", cols_p, index=idx_cli_p, key="cli_p")
                c_porte_p = st.sidebar.selectbox("Coluna Porte (G1, G2...):", cols_p, index=idx_prt_p, key="porte_p")
                
                cols_mutuo_opts = ["(Não existe)"] + cols_p
                def get_mutuo_index():
                    target = ["Cliente LIB", "É Cliente Prevision", "Cliente Prevision", "É Cliente Prevision?"]
                    for t in target:
                        if t in cols_p:
                            return cols_p.index(t) + 1
                    return 0
                
                c_mutuo = st.sidebar.selectbox("Coluna 'É Cliente Prevision?':", cols_mutuo_opts, index=get_mutuo_index(), key="mutuo_p")
                
                st.sidebar.markdown("---")
                st.sidebar.subheader("Definição de 'Oportunidade Quente'")
                
                todos_portes = df_parceiro[c_porte_p].dropna().unique().tolist()
                sugestao_quentes = ['G1', 'G2', 'G3', 'M2', 'M3']
                padrao_selecionado = [p for p in sugestao_quentes if p in todos_portes]
                
                portes_quentes = st.sidebar.multiselect("Selecione quais Portes são 'Quentes':", options=todos_portes, default=padrao_selecionado)
                
                # --- CÁLCULOS ---
                total_base = len(df_parceiro)
                
                if c_mutuo != "(Não existe)":
                    mutual_clients = df_parceiro[df_parceiro[c_mutuo].apply(is_true)]
                    qtd_mutuos = len(mutual_clients)
                else:
                    qtd_mutuos = 0
                
                oportunidades_quentes = df_parceiro[df_parceiro[c_porte_p].isin(portes_quentes)]
                qtd_quentes = len(oportunidades_quentes)
                
                # --- VISUAL ---
                st.divider()
                
                kp1, kp2, kp3 = st.columns(3)
                kp1.metric("Total Mapeado", total_base)
                kp2.metric("Oportunidades Quentes", qtd_quentes, f"Portes: {', '.join(map(str, portes_quentes))}")
                kp3.metric("Clientes LIB", qtd_mutuos)
                
                st.markdown("---")
                c1, c2 = st.columns(2)
                
                with c1:
                    st.subheader("Potencial da Base")
                    dados_graf = pd.DataFrame({
                        "Categoria": ["Base Prevision", "Oportunidades Quentes", "Clientes Atuais"],
                        "Quantidade": [total_base, qtd_quentes, qtd_mutuos]
                    })
                    fig_p = px.bar(dados_graf, x="Categoria", y="Quantidade", color="Categoria", text="Quantidade",
                                   color_discrete_sequence=["#1f77b4", "#2ca02c", "#ff7f0e"])
                    st.plotly_chart(fig_p, use_container_width=True)
                    
                with c2:
                    st.subheader("Distribuição por Porte")
                    contagem_porte = df_parceiro[c_porte_p].value_counts().reset_index()
                    contagem_porte.columns = ['Porte', 'Qtd']
                    fig_pie_p = px.pie(contagem_porte, names='Porte', values='Qtd', hole=0.4)
                    st.plotly_chart(fig_pie_p, use_container_width=True)

                st.markdown("---")
                with st.expander("🔎 Ver Lista de Oportunidades Quentes"):
                    st.write(f"Listando empresas com porte: {', '.join(map(str, portes_quentes))}")
                    st.dataframe(oportunidades_quentes[[c_cliente_p, c_porte_p]], hide_index=True, use_container_width=True)

        except Exception as e:
            st.error(f"Erro no Painel LIB: {e}")

else:
    st.info("Selecione um arquivo.")

