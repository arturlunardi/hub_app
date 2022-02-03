import streamlit as st
import requests
import json


def create_exact_lead(**kwargs):
    exact_headers = {
        'Content-Type': 'application/json',
        'token_exact': st.secrets['token_exact_api']
    }

    client_dict = kwargs.get('client_dict')
    mensagem_cliente = f'A mensagem deixada pelo corretor foi: \n\n {client_dict["description"]} \n\n'

    # pegando os dados do filter dict
    if client_dict["cliente_atendido"] == "Sim":
        answers_filter_dict = kwargs.get('answers_filter_dict')
        # aqui to só colocando a list em string pra ficar visualmente mais bonito pra atendente.
        for key, value in answers_filter_dict.items():
            if type(value) == list:
                answers_filter_dict[key] = ", ".join(value)
        
    # criando o lead
    values = {
        "duplicityValidation": "true",
        "lead": 
            {
                "name": client_dict["name"],
                "industry": "Pessoa Física - Vendas",
                "source": client_dict["source"],
                "sdrEmail" : "atendimento@orionsm.com.br",
                "phone": client_dict["phone"],
                "leadProduct": client_dict["leadProduct"],
                "city": client_dict["city"],
                # por enquanto to deixando padrão rs e brasil, depois dá pra buscar e mudar automaticamente por api
                "state": "Rio Grande do Sul",
                "country": "Brasil",
                "description": mensagem_cliente if client_dict["cliente_atendido"] == "Não" else mensagem_cliente + "As Informações coletadas foram: \n" + json.dumps(answers_filter_dict, indent=4, ensure_ascii=False).replace("{", "").replace("}", "").replace('"', ""),
            }
    }

    response = requests.post('https://api.exactsales.com.br/v3/leadsAdd', json=values, headers=exact_headers)

    lead_id = json.loads(response.content)['value']

    # criando o contato do lead
    values = {
    "leadId": lead_id,
    "name": client_dict["name"],
    "email": client_dict["email"],
    "phone1": client_dict["phone"],
    "mainContact": True
    }

    response = requests.post('https://api.exactsales.com.br/v3/personsAdd', json=values, headers=exact_headers)

    # adicionando campos personalizados do lead
    values = {
      "leadId": lead_id,
      "customFields": [
        {
            # corretor responsável
            "id": 20222,
            "value": client_dict["nome_do_indicador"],
            "options": []
        },
        {
            # atendimento já realizado
            "id": 26347,
            "value": client_dict["cliente_atendido"],
            "options": []
        },
      ]
    }

    response = requests.post('https://api.exactsales.com.br/v3/leadsCustomFieldsAdd', json=values, headers=exact_headers)

    return None


def get_form_cliente_nao_atendido(indicadores, origens):
    client_exact_submit_dict = {"cliente_atendido": "Não"}
    with st.form("cadastro_cliente_nao_realizado"):
        col_1, col_2 = st.columns(2)
        with col_1:
            client_exact_submit_dict["name"] = st.text_input(label='Nome do Cliente', help='Informe o nome completo do Cliente.')
            client_exact_submit_dict["source"] = st.selectbox(options=origens, label='Origem do Contato', help='Informe o canal de onde o Cliente surgiu.')
            client_exact_submit_dict["phone"] = st.text_input(label='Telefone do Cliente', help='Informe o telefone do Cliente.')
            client_exact_submit_dict["email"] = st.text_input(label='Email do Cliente', help='Informe o email do Cliente.')
            client_exact_submit_dict["nome_do_indicador"] = st.selectbox(options=indicadores['Nomecompleto'].tolist(), label='Indicador')
        with col_2:
            client_exact_submit_dict["leadProduct"] = st.selectbox(label='Interesse', help='Informe o que o cliente está buscando.', options=['Venda', 'Locação'])
            client_exact_submit_dict["city"] = st.selectbox(label='Cidade de Busca', help='Informe em que cidade o Cliente busca imóveis.', options=['Santa Maria', 'Itaara'])
            client_exact_submit_dict["description"] = st.text_area(label='Descrição', help='Descreva detalhadamente o que foi conversado com o cliente.', height=240)

        st.info("**Por favor, confira todos os valores antes de enviar o formulário.**")
        submitted = st.form_submit_button("Enviar")
        if submitted:
            required_fields_clients = ['name', 'source', 'phone', 'leadProduct', 'city', 'description']
            if any([True for field in [client_exact_submit_dict.get(key) for key in required_fields_clients] if field == '' or field == []]):
                st.error('Por favor, preencha todos os campos corretamente.')
                st.stop()
            try:
                create_exact_lead(client_dict=client_exact_submit_dict)  
                st.success("Formulário enviado com sucesso!")
            except:
                st.write("Houve um erro no envio do formulário. Por favor, tente novamente. Caso o erro persista, entre em contato com o administrador.")
    return None


def get_form_cliente_atendido(indicadores, origens, finalidade, exact_filtro_1, exact_filtro_2):
    client_exact_submit_dict = {"cliente_atendido": "Sim"}
    client_exact_filter_submit_dict = {}

    filter_dict = {
                'locacao': {
                    'first_filter': {
                        'residencial_id': 943412, 
                        'comercial_id': 943413
                    },
                    'second_filter': 943518
                },
                'vendas': {
                    'first_filter': {
                        'residencial_id': 952305,
                        'comercial_id': 952306
                    },
                    'second_filter': 943519
                }
            }
    
    if finalidade == 'Residencial':
        client_exact_filter_submit_dict['finalidade'] = 'Residencial'
        with st.form('exact_residencial_form'):
            col_1, col_2 = st.columns(2)
            with col_1:
                client_exact_submit_dict["name"] = st.text_input(label='Nome do Cliente', help='Informe o nome completo do Cliente.')
                client_exact_submit_dict["source"] = st.selectbox(options=origens, label='Origem do Contato', help='Informe o canal de onde o Cliente surgiu.')
                client_exact_submit_dict["phone"] = st.text_input(label='Telefone do Cliente', help='Informe o telefone do Cliente.')
                client_exact_submit_dict["email"] = st.text_input(label='Email do Cliente', help='Informe o email do Cliente.')
                client_exact_submit_dict["leadProduct"] = st.selectbox(label='Interesse', help='Informe o que o cliente está buscando.', options=['Venda', 'Locação'])
                client_exact_submit_dict["city"] = st.selectbox(label='Cidade de Busca', help='Informe em que cidade o Cliente busca imóveis.', options=['Santa Maria', 'Itaara'])
                client_exact_submit_dict["nome_do_indicador"] = st.selectbox(options=indicadores['Nomecompleto'].tolist(), label='Indicador')
                client_exact_submit_dict["description"] = st.text_area(label='Descrição', help='Descreva detalhadamente o que foi conversado com o cliente.', height=330)
            with col_2:
                questions = exact_filtro_1.loc[exact_filtro_1['parentAnswerId'] == filter_dict.get('vendas').get('first_filter').get('residencial_id')].append(exact_filtro_2.loc[exact_filtro_2['parentAnswerId'] == filter_dict.get('vendas').get('second_filter')])
                for index, row in questions.iterrows():
                    if row['text'] == 'Em que cidade você está buscando imóveis?':
                        continue
                    elif row.get('type') == 'Multiple':
                        client_exact_filter_submit_dict[row['text']] = st.multiselect(label=row['text'], options=[i.get('text') for i in row['answers']])
                    elif row.get('type') == 'Unique':
                        client_exact_filter_submit_dict[row['text']] = st.selectbox(label=row['text'], options=[i.get('text') for i in row['answers']])
                        # if row['text'] == 'Já escolheu algum imóvel específico?' and client_exact_filter_submit_dict[row['text']] == 'Sim':
                        if row['text'] == 'Já escolheu algum imóvel específico?':
                            client_exact_filter_submit_dict['Código do Imóvel'] = st.text_input('Digite aqui o código do imóvel se ele existir.')
                    elif row.get('type') == 'Open':
                        client_exact_filter_submit_dict[row['text']] = st.text_input(label=row['text'])

            st.info("**Por favor, confira todos os valores antes de enviar o formulário.**")
            submitted = st.form_submit_button("Enviar")
            if submitted:
                required_fields_clients = ['name', 'source', 'phone', 'leadProduct', 'city', 'description']
                required_fields_filters = ['Que tipo de imóvel você prefere?', 'Tem preferência por algum bairro?', 'Qual o motivo da procura por imóvel?', 'Qual sua ocupação atual?', 'Quanto você pode/está disposto a investir?']
                if any([True for field in [client_exact_submit_dict.get(key) for key in required_fields_clients] if field == '' or field == []]) or any([True for field in [client_exact_filter_submit_dict.get(key) for key in required_fields_filters] if field == '' or field == []]):
                    st.error('Por favor, preencha todos os campos corretamente.')
                    st.stop()
                try:
                    create_exact_lead(client_dict=client_exact_submit_dict, answers_filter_dict=client_exact_filter_submit_dict)
                    st.success("Formulário enviado com sucesso!")
                except:
                    st.write("Houve um erro no envio do formulário. Por favor, tente novamente. Caso o erro persista, entre em contato com o administrador.")

    elif finalidade == 'Comercial':
        client_exact_filter_submit_dict['finalidade'] = 'Comercial'
        with st.form('exact_comercial_form'):
            col_1, col_2 = st.columns(2)
            with col_1:
                client_exact_submit_dict["name"] = st.text_input(label='Nome do Cliente', help='Informe o nome completo do Cliente.')
                client_exact_submit_dict["source"] = st.selectbox(options=origens, label='Origem do Contato', help='Informe o canal de onde o Cliente surgiu.')
                client_exact_submit_dict["phone"] = st.text_input(label='Telefone do Cliente', help='Informe o telefone do Cliente.')
                client_exact_submit_dict["email"] = st.text_input(label='Email do Cliente', help='Informe o email do Cliente.')
                client_exact_submit_dict["leadProduct"] = st.selectbox(label='Interesse', help='Informe o que o cliente está buscando.', options=['Venda', 'Locação'])
                client_exact_submit_dict["city"] = st.selectbox(label='Cidade de Busca', help='Informe em que cidade o Cliente busca imóveis.', options=['Santa Maria', 'Itaara'])
                client_exact_submit_dict["nome_do_indicador"] = st.selectbox(options=indicadores['Nomecompleto'].tolist(), label='Indicador')
                client_exact_submit_dict["description"] = st.text_area(label='Descrição', help='Descreva detalhadamente o que foi conversado com o cliente.', height=232)
            with col_2:
                questions = exact_filtro_1.loc[exact_filtro_1['parentAnswerId'] == filter_dict.get('vendas').get('first_filter').get('comercial_id')].append(exact_filtro_2.loc[exact_filtro_2['parentAnswerId'] == filter_dict.get('vendas').get('second_filter')])
                for index, row in questions.iterrows():
                    if row['text'] == 'Em que cidade você está buscando imóveis?':
                        continue
                    elif row.get('type') == 'Multiple':
                        client_exact_filter_submit_dict[row['text']] = st.multiselect(label=row['text'], options=[i.get('text') for i in row['answers']])
                    elif row.get('type') == 'Unique':
                        client_exact_filter_submit_dict[row['text']] = st.selectbox(label=row['text'], options=[i.get('text') for i in row['answers']])
                        # if row['text'] == 'Já escolheu algum imóvel específico?' and client_exact_filter_submit_dict[row['text']] == 'Sim':
                        if row['text'] == 'Já escolheu algum imóvel específico?':
                            client_exact_filter_submit_dict['Código do Imóvel'] = st.text_input('Digite aqui o código do imóvel se ele existir.')
                    elif row.get('type') == 'Open':
                        client_exact_filter_submit_dict[row['text']] = st.text_input(label=row['text'])

            st.info("**Por favor, confira todos os valores antes de enviar o formulário.**")
            submitted = st.form_submit_button("Enviar")
            if submitted:
                required_fields_clients = ['name', 'source', 'phone', 'leadProduct', 'city', 'description']
                required_fields_filters = ['Que tipo de imóvel você prefere?', 'Tem preferência por algum bairro?', 'Qual o motivo da procura por imóvel?', 'Qual sua ocupação atual?', 'Quanto você pode/está disposto a investir?']
                if any([True for field in [client_exact_submit_dict.get(key) for key in required_fields_clients] if field == '' or field == []]) or any([True for field in [client_exact_filter_submit_dict.get(key) for key in required_fields_filters] if field == '' or field == []]):
                    st.error('Por favor, preencha todos os campos corretamente.')
                    st.stop()
                try:
                    create_exact_lead(client_dict=client_exact_submit_dict, answers_filter_dict=client_exact_filter_submit_dict)
                    st.success("Formulário enviado com sucesso!")
                except:
                    st.write("Houve um erro no envio do formulário. Por favor, tente novamente. Caso o erro persista, entre em contato com o administrador.")
               
    return None

