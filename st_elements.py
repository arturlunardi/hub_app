import streamlit as st
import requests
import json
import re


def real_br_money_mask(my_value):
    a = '{:,.2f}'.format(float(my_value))
    b = a.replace(',','v')
    c = b.replace('.',',')
    return "R$ " + c.replace('v','.')


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
        answers_filter_dict["Quanto você pode/está disposto a investir?"] = real_br_money_mask(answers_filter_dict["Quanto você pode/está disposto a investir?"])
        
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
    pattern = "\(\d{2,}\) \d{4,}\-\d{4}"

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
            elif len(re.findall(pattern, client_exact_submit_dict["phone"])) < 1:
                st.error('Por favor, o formato do telefone do contato deve ser como em: (55) 99999-9999 ou (55) 3221-5469.')
                st.stop()
            st.spinner('Registrando o formulário...')
            try:
                create_exact_lead(client_dict=client_exact_submit_dict)  
                st.success("Formulário enviado com sucesso!")
            except:
                st.write("Houve um erro no envio do formulário. Por favor, tente novamente em alguns minutos. Caso o erro persista, entre em contato com o administrador.")
    return None


def get_form_cliente_atendido(indicadores, origens, finalidade, exact_filtro_1, exact_filtro_2):
    client_exact_submit_dict = {"cliente_atendido": "Sim"}
    client_exact_filter_submit_dict = {}
    pattern = "\(\d{2,}\) \d{4,}\-\d{4}"

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
                        if row['text'] == 'Quanto você pode/está disposto a investir?':
                            client_exact_filter_submit_dict[row['text']] = st.number_input(label=row['text'])
                        else:
                            client_exact_filter_submit_dict[row['text']] = st.text_input(label=row['text'])

            st.info("**Por favor, confira todos os valores antes de enviar o formulário.**")
            submitted = st.form_submit_button("Enviar")
            if submitted:
                required_fields_clients = ['name', 'source', 'phone', 'leadProduct', 'city', 'description']
                required_fields_filters = ['Que tipo de imóvel você prefere?', 'Tem preferência por algum bairro?', 'Qual o motivo da procura por imóvel?', 'Qual sua ocupação atual?', 'Quanto você pode/está disposto a investir?']
                if any([True for field in [client_exact_submit_dict.get(key) for key in required_fields_clients] if field == '' or field == []]) or any([True for field in [client_exact_filter_submit_dict.get(key) for key in required_fields_filters] if field == '' or field == []]):
                    st.error('Por favor, preencha todos os campos corretamente.')
                    st.stop()
                elif len(re.findall(pattern, client_exact_submit_dict["phone"])) < 1:
                    st.error('Por favor, o formato do telefone do contato deve ser como em: (55) 99999-9999 ou (55) 3221-5469.')
                    st.stop()
                st.spinner('Registrando o formulário...')
                try:
                    create_exact_lead(client_dict=client_exact_submit_dict, answers_filter_dict=client_exact_filter_submit_dict)
                    st.success("Formulário enviado com sucesso!")
                except:
                    st.write("Houve um erro no envio do formulário. Por favor, tente novamente em alguns minutos. Caso o erro persista, entre em contato com o administrador.")

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
                        if row['text'] == 'Quanto você pode/está disposto a investir?':
                            client_exact_filter_submit_dict[row['text']] = st.number_input(label=row['text'])
                        else:
                            client_exact_filter_submit_dict[row['text']] = st.text_input(label=row['text'])

            st.info("**Por favor, confira todos os valores antes de enviar o formulário.**")
            submitted = st.form_submit_button("Enviar")
            if submitted:
                required_fields_clients = ['name', 'source', 'phone', 'leadProduct', 'city', 'description']
                required_fields_filters = ['Que tipo de imóvel você prefere?', 'Tem preferência por algum bairro?', 'Qual o motivo da procura por imóvel?', 'Qual sua ocupação atual?', 'Quanto você pode/está disposto a investir?']
                if any([True for field in [client_exact_submit_dict.get(key) for key in required_fields_clients] if field == '' or field == []]) or any([True for field in [client_exact_filter_submit_dict.get(key) for key in required_fields_filters] if field == '' or field == []]):
                    st.error('Por favor, preencha todos os campos corretamente.')
                    st.stop()
                elif len(re.findall(pattern, client_exact_submit_dict["phone"])) < 1:
                    st.error('Por favor, o formato do telefone do contato deve ser como em: (55) 99999-9999 ou (55) 3221-5469.')
                    st.stop()
                st.spinner('Registrando o formulário...')
                try:
                    create_exact_lead(client_dict=client_exact_submit_dict, answers_filter_dict=client_exact_filter_submit_dict)
                    st.success("Formulário enviado com sucesso!")
                except:
                    st.write("Houve um erro no envio do formulário. Por favor, tente novamente em alguns minutos. Caso o erro persista, entre em contato com o administrador.")
               
    return None

# ---------------------------------------------------------------

def modify_exact_client(**kwargs):
    tentativas = 10

    exact_headers = {
        'Content-Type': 'application/json',
        'token_exact': st.secrets['token_exact_api']
    }

    client_dict = kwargs.get('client_dict')

    mensagem_cliente = f'Atenção Pré-Vendedor! Este cliente foi cadastrado por um corretor através de um formulário, não é necessário atendê-lo, a não ser que seja solicitado. \n\n A mensagem deixada pelo corretor foi: \n\n {client_dict["description"]} \n\n'
    phone_with_re = re.sub(r'\D', '', client_dict['phone'])

    # pegando o id do lead que já foi criado pelo vista
    # url = f"https://api.exactsales.com.br/v3/Leads?$filter=phone1 eq '{phone_with_re}' and lead eq '{client_dict['name']}'"
    # eu tirei pra verificar também o nome, pq pode acontecer de já existir o cliente e não conseguir identificar, só pelo telefone serve pra verificar
    url = f"https://api.exactsales.com.br/v3/Leads?$filter=phone1 eq '{phone_with_re}'"
    response = requests.get(url, headers=exact_headers)

    x = 0
    while json.loads(response.content)['value'] == []:
        if x >= tentativas:
            st.error(response.content)
            raise Exception("Erro ao **identificar** o cliente na Exact.")
        url = f"https://api.exactsales.com.br/v3/Leads?$filter=phone1 eq '{phone_with_re}'"
        response = requests.get(url, headers=exact_headers)
        x+=1
    lead_id = json.loads(response.content)["value"][0]["id"]
        
    # modificando o lead
    # V3
    values = {
        "duplicityValidation": "false",
        "lead": 
            {
                "name": client_dict["name"],
                "industry": client_dict["campanha"],
                "source": client_dict["source"],
                "sdrEmail" : "atendimento@orionsm.com.br",
                "phone": client_dict["phone"],
                "leadProduct": client_dict["leadProduct"],
                "city": client_dict["city"],
                # por enquanto to deixando padrão rs e brasil, depois dá pra buscar e mudar automaticamente por api
                "state": "Rio Grande do Sul",
                "country": "Brasil",
                "description": mensagem_cliente,
            }
    }

    response = requests.put(f'https://api.exactsales.com.br/v3/LeadsUpdate/{lead_id}', json=values, headers=exact_headers)

    i = 0
    while response.status_code != 201:
        if i >= tentativas:
            st.error(response.content)
            raise Exception("Erro ao **atualizar** o cliente na Exact.")
        response = requests.put(f'https://api.exactsales.com.br/v3/LeadsUpdate/{lead_id}', json=values, headers=exact_headers)
        i+=1

    # adicionando campos personalizados do lead
    values = {
      "leadId": lead_id,
      "customFields": [
        {
            # corretor responsável
            "id": 20222,
            "value": client_dict["indicator"],
            "options": []
        },
        {
            # atendimento já realizado
            "id": 26347,
            "value": "Sim",
            "options": []
        },
      ]
    }

    response = requests.post('https://api.exactsales.com.br/v3/leadsCustomFieldsAdd', json=values, headers=exact_headers)

    return None


def create_vista_lead(**kwargs):
    client_dict = kwargs.get('client_dict')
    indicadores = kwargs.get('indicadores')

    mensagem_cliente = f'A mensagem deixada pelo corretor foi: \n\n {client_dict["description"]} \n\n'

    headers = {
    'accept': 'application/json'
    }

    # aqui é pra criar o lead
    data= {
        "cadastro": {
            "lead":{
                "nome":client_dict["name"],
                "fone":client_dict["phone"],
                "email":client_dict["email"], 
                "mensagem": mensagem_cliente,
                "veiculo": client_dict["source"],
                "interesse": client_dict["leadProduct"],
                "corretor": indicadores.loc[indicadores["Nomecompleto"] == client_dict["indicator"]]["Codigo"].squeeze(),
            }
        }
    }
    url = f'http://brasaolt-rest.vistahost.com.br/lead?key={st.secrets["vista_api_key"]}'

    response = requests.post(url=url, headers=headers, json=data)

    if json.loads(response.content)["message"] == 'O cadastro foi encontrado.':
        # como o cliente já existe no vista, eu não vou modifica-lo na exact. Por isso, vou identificar o erro e parar a execução.
        # mesmo que o cliente já exista, o corretor foi atribuido a ele automaticamente, então ele poderá procurar o cliente.
        raise Exception("O cliente já foi cadastrado anteriormente, ele não será modificado na Exact. Por favor, entre em contato com o seu gerente para identificá-lo.")

    else:
        # aqui é pra modificar o lead
        client_code = json.loads(response.content)["Codigo"]

        data = {
            "cadastro": {
                "fields":{
                    "CidadeResidencial": client_dict["city"],  
                    "Observacoes": mensagem_cliente,
                }
            }
        }

        url = f'http://brasaolt-rest.vistahost.com.br/clientes/detalhes?key={st.secrets["vista_api_key"]}&cliente={client_code}'

        response = requests.put(url=url, headers=headers, json=data)

    return None


def get_form_client(indicadores, origens, empreendimentos):
    client_dict = {}
    phone_pattern = "\(\d{2,}\) \d{4,}\-\d{4}"

    with st.form('cliente_form'):
        col_1, col_2 = st.columns(2)
        with col_1:
            client_dict["name"] = st.text_input(label="Nome", help="Informe o nome completo do Cliente.")
            client_dict["phone"] = st.text_input(label="Telefone", help="Informe o telefone do Cliente.")
            client_dict["email"] = st.text_input(label="E-mail", help="Informe o email do Cliente.")
            client_dict["city"] = st.selectbox(label='Cidade de Busca', help='Informe em que cidade o Cliente busca imóveis.', options=['Santa Maria', 'Itaara'])
            
        with col_2:
            client_dict["leadProduct"] = st.selectbox(label="Interesse", help="Informe o que o cliente está buscando.", options=["Venda", "Locação"])
            client_dict["source"] = st.selectbox(options=origens, label="Origem do Contato", help="Informe o canal de onde o Cliente surgiu.")
            client_dict["indicator"] = st.selectbox(label="Responsável", options=indicadores['Nomecompleto'].tolist())
            client_dict["campanha"] = st.selectbox(label="Produto", help="O cliente veio de alguma campanha, empreendimento específico?", options=empreendimentos)

        client_dict["description"] = st.text_area(label="Descrição", help="Descreva detalhadamente o que foi conversado com o cliente.", height=232)

        st.info("**Por favor, confira todos os valores antes de enviar o formulário.**")
        submitted = st.form_submit_button("Enviar")
        if submitted:
            required_fields_clients = ['name', 'phone', 'city', 'leadProduct', 'source', 'indicator', 'description']
            if any([True for field in [client_dict.get(key) for key in required_fields_clients] if field == '' or field == []]):
                st.error('Por favor, preencha todos os campos corretamente.')
                st.stop()
            elif len(re.findall(phone_pattern, client_dict["phone"])) < 1:
                st.error('Por favor, o formato do telefone do contato deve ser como em: (55) 99999-9999 ou (55) 3221-5469.')
                st.stop()
            with st.spinner('Registrando o formulário...'):
                try:
                    create_vista_lead(client_dict=client_dict, indicadores=indicadores)
                    modify_exact_client(client_dict=client_dict)
                    st.write(client_dict)
                    st.success("Formulário enviado com sucesso!")
                except Exception as error:
                    st.error(f"Houve um erro no envio do formulário. {error}")


                    