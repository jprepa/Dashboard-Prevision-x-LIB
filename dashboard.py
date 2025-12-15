import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from urllib.request import urlopen

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
iframe { border: none !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---

@st.cache_data
def carregar_mapa_brasil():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    with urlopen(url) as response:
        brazil_states = json.load(response)
    return brazil_states

def is_true(val):
    texto = str(val).strip().lower()
    aceitos = ['sim', 's', 'yes', 'y', 'verdadeiro', 'true', 'ativo', '1', '1.0']
    return texto in aceitos

# --- NAVEGAÇÃO E UPLOAD ---
st.sidebar.title("🎛️ Navegação")
modo_visualizacao = st.sidebar.radio("Selecione a Visão:", ["Análise LIB", "Análise Prevision"])
st.sidebar.markdown("---")

# --- ALTERAÇÃO DE SEGURANÇA ---
# Removida a verificação automática de arquivo local (os.path.exists).
# Agora o upload é obrigatório para visualizar qualquer dado.
st.sidebar.warning("🔒 Acesso Restrito")
st.sidebar.info("Por motivos de segurança, é necessário realizar o upload da planilha para visualizar os dados.")
arquivo_carregado = st.sidebar.file_uploader("Faça upload da planilha:", type=["xlsx", "xls"])

# ==============================================================================
# MODO 1: ANÁLISE PREVISION (DADOS INTERNOS - ABA CLIENTES)
# ==============================================================================
if modo_visualizacao == "Análise LIB":
    st.title("📊 Análise Base Clientes LIB")
    
    if arquivo_carregado:
        try:
            df = pd.read_excel(arquivo_carregado, sheet_name="Clientes")
            
            # --- NOMES DAS COLUNAS (Ajustados conforme solicitado) ---
            c_cliente = "Cliente"
            c_porte = "Porte"
            c_cidade = "Cidade"
            c_mercado = "Mercado de atuação"
            c_obras = "Obras Contratadas"
            
            # Colunas Novas (Imagem Esquerda)
            c_plano = "Plano"
            c_erp = "ERP"
            c_upsell = "Último Upsell" 
            c_data_ganho = "Data de Ganho"
            
            # Flags
            c_icp = "ICP"
            c_fora_icp = "Fora ICP"
            c_icp_quente = "Prospect Quente"
            c_oportunidade = "Oportunidade"
            c_prev = "É Cliente Prevision?" 
            c_ecos = "É cliente Ecossistema"

            # --- PROCESSAMENTO ---
            val_total = len(df)
            val_icp = len(df[df[c_icp].apply(is_true)]) if c_icp in df.columns else 0
            val_hot = len(df[df[c_icp_quente].apply(is_true)]) if c_icp_quente in df.columns else 0
            val_opp = len(df[df[c_oportunidade].apply(is_true)]) if c_oportunidade in df.columns else 0
            val_prev = len(df[df[c_prev].apply(is_true)]) if c_prev in df.columns else 0
            val_ecos_only = len(df[df[c_ecos].apply(is_true)]) if c_ecos in df.columns else 0
            val_ecos_merged = val_prev + val_ecos_only

            # Preparação Gráficos
            config_grupos = [
                ("Total Mapeado", "ALL_ROWS"),
                ("Total ICPs", c_icp),
                ("Fora ICP", c_fora_icp),
                ("Oportunidades Quentes", c_icp_quente),
                ("Oportunidades (Geral)", c_oportunidade),
                ("Clientes Ecossistema Starian", c_ecos),
                ("Clientes Prevision", c_prev)
            ]
            
            resumo_barras = {'Categoria': [], 'Quantidade': [], 'Lista_Clientes': []}
            lista_matriz = []
            
            for nome_grupo, col_excel in config_grupos:
                if col_excel == "ALL_ROWS":
                    filtro = df
                elif col_excel in df.columns:
                    filtro = df[df[col_excel].apply(is_true)]
                else:
                    filtro = pd.DataFrame()
                
                if not filtro.empty:
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
            k2.metric("ICPs", val_icp)
            k3.metric("Oportunidades Quentes", val_hot, help="Critérios: ICP, Porte Médio+, Último contato com LIB em 24/25 e não é Cliente Prevision")
            k4.metric("Clientes Prevision", val_prev)
            k5.metric("Clientes Ecossistema", val_ecos_merged, help="Clientes Prevision + Ecossistema Starian")
            
            st.markdown("---")
            c_bar, c_pie = st.columns([1.5, 1])
            with c_bar:
                st.subheader("Visão Geral Base")
                if not df_resumo.empty:
                    fig_bar = px.bar(df_resumo, x='Quantidade', y='Categoria', orientation='h', text='Quantidade', color='Categoria')
                    fig_bar.update_layout(showlegend=False)
                    st.plotly_chart(fig_bar, use_container_width=True)
            with c_pie:
                st.subheader("Distribuição ICPs")
                dados_pizza = [
                    {"Label": "Oportunidades Quentes", "Valor": val_hot},
                    {"Label": "Oportunidades (Geral)", "Valor": val_opp},
                    {"Label": "Clientes Prevision", "Valor": val_prev}
                ]
                dados_pizza = [d for d in dados_pizza if d['Valor'] > 0]
                if dados_pizza:
                    fig_pie = px.pie(pd.DataFrame(dados_pizza), names='Label', values='Valor', hole=0.5,
                                     color_discrete_sequence=["#00CC96", "#AB63FA", "#FFA15A"])
                    st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("---")
            c_matriz, c_lista = st.columns([1.5, 1])
            filtro_ativo = False
            df_filtrado_show = pd.DataFrame()
            msg_filtro = ""

            with c_matriz:
                st.subheader("Matriz Porte x Status")
                selection = None
                if not df_matriz_source.empty:
                    matriz_final = pd.crosstab(df_matriz_source['Porte'], df_matriz_source['Status'])
                    fig_heat = px.imshow(matriz_final, text_auto=True, aspect="auto", color_continuous_scale='Viridis')
                    selection = st.plotly_chart(fig_heat, use_container_width=True, on_select="rerun", selection_mode="points")

            with c_lista:
                st.subheader("Detalhes")
                # Filtros
                if selection and "selection" in selection and selection["selection"]["points"]:
                    pts = selection["selection"]["points"][0]
                    status_c = pts['x']
                    porte_c = pts['y']
                    msg_filtro = f"Filtro: {status_c} + {porte_c}"
                    clientes_alvo = df_matriz_source[(df_matriz_source['Status']==status_c) & (df_matriz_source['Porte']==porte_c)]['Cliente'].unique()
                    df_filtrado_show = df[df[c_cliente].isin(clientes_alvo)]
                    filtro_ativo = True
                elif not filtro_ativo and not df_resumo.empty:
                    grupo = st.selectbox("Selecione grupo:", df_resumo['Categoria'].unique(), key="sel_g_in")
                    if grupo:
                        row = df_resumo[df_resumo['Categoria']==grupo].iloc[0]
                        df_filtrado_show = df[df[c_cliente].isin(row['Lista_Clientes'])]
                
                if not df_filtrado_show.empty:
                    st.info(msg_filtro if filtro_ativo else "Listando Grupo Selecionado")
                    
                    # --- DEFINIÇÃO DAS COLUNAS A EXIBIR ---
                    cols_preferenciais = [
                        c_cliente, c_porte, c_cidade, c_mercado, 
                        c_plano, c_erp, c_upsell, c_data_ganho, # Colunas ajustadas
                        c_obras
                    ]
                    # Filtra apenas as que existem no Excel para não dar erro
                    cols_finais = [c for c in cols_preferenciais if c in df.columns]
                    
                    st.dataframe(df_filtrado_show[cols_finais], hide_index=True, use_container_width=True, height=400)

        except Exception as e:
            st.error(f"Erro ao ler aba 'Clientes'. Detalhe: {e}")
    else:
         st.warning("⚠️ Aguardando upload da planilha para exibir Análise LIB.")

# ==============================================================================
# MODO 2: ANÁLISE PREVISION (DADOS PARCEIRO - ABA PLANILHA1)
# ==============================================================================
elif modo_visualizacao == "Análise Prevision":
    st.title("📊 Análise Base Clientes Prevision")
    
    if arquivo_carregado:
        try:
            df_parceiro = pd.read_excel(arquivo_carregado, sheet_name="Planilha1")
            
            # --- NOMES DAS COLUNAS (Ajustados conforme solicitado) ---
            c_cliente_p = "Cliente"
            c_porte_p = "Porte"
            c_uf_p = "Estado"
            c_cidade_p = "Cidade"
            c_tipologia_p = "Tipologia"
            c_obras_p = "Obras Contratadas"
            c_mutuo = "Cliente LIB"
            
            # Colunas Novas (Imagem Direita)
            c_servico = "Serviço vendido"
            c_ano_proj = "Ano do último projeto"
            c_contato = "Atual Contato"
            c_solucoes = "Solucoes Starian"

            # Parâmetros
            st.sidebar.header("Parâmetros de Análise")
            todos_portes = df_parceiro[c_porte_p].dropna().unique().tolist()
            padrao_quentes = ['G1', 'G2', 'G3', 'M2', 'M3']
            padrao_selecionado = [p for p in padrao_quentes if p in todos_portes]
            portes_quentes = st.sidebar.multiselect("Definir Portes Ideais:", options=todos_portes, default=padrao_selecionado)
            
            # Cálculos
            total_base = len(df_parceiro)
            if c_mutuo in df_parceiro.columns:
                df_parceiro['Is_Cliente'] = df_parceiro[c_mutuo].apply(is_true)
                mutual_clients = df_parceiro[df_parceiro['Is_Cliente']]
                qtd_mutuos = len(mutual_clients)
            else:
                df_parceiro['Is_Cliente'] = False
                qtd_mutuos = 0
            
            df_parceiro['Is_Quente'] = df_parceiro[c_porte_p].isin(portes_quentes)
            oportunidades_quentes = df_parceiro[df_parceiro['Is_Quente']]
            qtd_quentes = len(oportunidades_quentes)
            
            # Visual
            st.divider()
            kp1, kp2, kp3 = st.columns(3)
            kp1.metric("Total Mapeado", total_base)
            kp2.metric("ICPs", qtd_quentes)
            kp3.metric("Clientes LIB", qtd_mutuos, help="Apenas os Clientes Lib na base Prevision")
            
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Potencial da Base")
                dados_graf = pd.DataFrame({
                    "Categoria": ["Clientes Prevision", "Leads Ideais LIB", "Clientes Atuais"],
                    "Quantidade": [total_base, qtd_quentes, qtd_mutuos]
                })
                fig_p = px.bar(dados_graf, x="Categoria", y="Quantidade", color="Categoria", text="Quantidade", color_discrete_sequence=["#1f77b4", "#2ca02c", "#ff7f0e"])
                st.plotly_chart(fig_p, use_container_width=True)
            with c2:
                st.subheader("Distribuição por Porte")
                contagem_porte = df_parceiro[c_porte_p].value_counts().reset_index()
                contagem_porte.columns = ['Porte', 'Qtd']
                fig_pie_p = px.pie(contagem_porte, names='Porte', values='Qtd', hole=0.4)
                st.plotly_chart(fig_pie_p, use_container_width=True)

            # Matriz
            st.markdown("---")
            st.subheader("Matriz Porte x Status")
            grupos_lib = [
                ("Total Mapeado", df_parceiro), 
                ("Clientes LIB", mutual_clients),
                ("ICP", oportunidades_quentes) 
            ]
            lista_matriz_lib = []
            for nome, dff in grupos_lib:
                for _, row in dff.iterrows():
                        lista_matriz_lib.append({'Porte': row[c_porte_p], 'Status': nome, 'Cliente': row[c_cliente_p]})
            
            df_matriz_source_lib = pd.DataFrame(lista_matriz_lib)
            selection_matriz = None
            if not df_matriz_source_lib.empty:
                matriz_final_lib = pd.crosstab(df_matriz_source_lib['Porte'], df_matriz_source_lib['Status'])
                cols = sorted(matriz_final_lib.columns.tolist())
                if "Total Mapeado" in cols:
                    cols.remove("Total Mapeado")
                    cols.insert(0, "Total Mapeado")
                matriz_final_lib = matriz_final_lib[cols]
                fig_heat_lib = px.imshow(matriz_final_lib, text_auto=True, aspect="auto", color_continuous_scale='Viridis')
                selection_matriz = st.plotly_chart(fig_heat_lib, use_container_width=True, on_select="rerun", selection_mode="points")

            # Mapa
            st.markdown("---")
            st.subheader("📍 Visão por Estado")
            selection_mapa = None
            if c_uf_p in df_parceiro.columns:
                df_mapa = df_parceiro.groupby(c_uf_p).apply(lambda x: pd.Series({'Total_Linhas': len(x), 'Qtd_Clientes': x['Is_Cliente'].sum(), 'Qtd_Quentes': x['Is_Quente'].sum()})).reset_index()
                df_mapa.rename(columns={c_uf_p: 'UF'}, inplace=True)
                df_mapa['Oportunidades Geral'] = df_mapa['Total_Linhas'] - df_mapa['Qtd_Quentes']
                with st.spinner("Carregando mapa..."):
                    brazil_states = carregar_mapa_brasil()
                fig_map = px.choropleth(df_mapa, geojson=brazil_states, locations='UF', featureidkey='properties.sigla', color='Qtd_Quentes', color_continuous_scale="Reds", title="Calor por Oportunidades")
                fig_map.update_geos(fitbounds="locations", visible=False)
                fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', geo=dict(bgcolor='rgba(0,0,0,0)'), clickmode='event+select')
                selection_mapa = st.plotly_chart(fig_map, use_container_width=True, on_select="rerun", selection_mode="points")
            
            # Tabela Detalhes
            df_filtrado_final = df_parceiro.copy()
            msg_filtro = "Mostrando base completa"

            if selection_matriz and "selection" in selection_matriz and selection_matriz["selection"]["points"]:
                pts = selection_matriz["selection"]["points"][0]
                status_c = pts['x']
                porte_c = pts['y']
                clientes_alvo = df_matriz_source_lib[(df_matriz_source_lib['Status']==status_c) & (df_matriz_source_lib['Porte']==porte_c)]['Cliente'].unique()
                df_filtrado_final = df_filtrado_final[df_filtrado_final[c_cliente_p].isin(clientes_alvo)]
                msg_filtro = f"Matriz: {status_c} + {porte_c}"
            elif selection_mapa and "selection" in selection_mapa and selection_mapa["selection"]["points"]:
                pts = selection_mapa["selection"]["points"][0]
                uf_clicada = pts.get('location', pts.get('x'))
                if uf_clicada:
                    df_filtrado_final = df_filtrado_final[df_filtrado_final[c_uf_p] == uf_clicada]
                    msg_filtro = f"Mapa: Estado {uf_clicada}"

            with st.expander(f"🔎 Detalhes da Base ({msg_filtro})", expanded=True):
                # --- DEFINIÇÃO DAS COLUNAS A EXIBIR (PARCEIRO) ---
                cols_preferenciais_p = [
                    c_cliente_p, c_porte_p, c_uf_p, c_cidade_p, c_tipologia_p, 
                    c_servico, c_ano_proj, c_contato, c_solucoes, # Colunas ajustadas
                    c_obras_p
                ]
                # Filtra apenas as que existem no Excel
                cols_finais_p = [c for c in cols_preferenciais_p if c in df_filtrado_final.columns]
                
                st.dataframe(df_filtrado_final[cols_finais_p], hide_index=True, use_container_width=True)

        except Exception as e:
            st.error(f"Erro ao ler aba 'Planilha1'. Detalhe: {e}")
    else:
        st.warning("⚠️ Aguardando upload da planilha para exibir Análise Prevision.")
