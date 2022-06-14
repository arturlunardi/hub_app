import pandas as pd
import streamlit as st
import json
import requests
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInput
from hubspot.crm.deals import ApiException as DealException
from hubspot.crm.contacts import ApiException as ContactException
from hubspot.crm.properties import ApiException as PropertyException
import datetime
import st_elements
import re


st.set_page_config(
    page_title="Plataforma de Cadastros da Órion",
    page_icon="https://i.ibb.co/m6kBTBT/INS2020-07-AVATAR-1024.jpg",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache(hash_funcs={"_thread.RLock": lambda _: None, 'builtins.weakref': lambda _: None}, show_spinner=False)
def get_exact_origens():
    exact_headers = {
        'Content-Type': 'application/json',
        'token_exact': st.secrets['token_exact_api']
    }

    response = requests.get('https://api.exactsales.com.br/v2/origens', headers=exact_headers)

    return [i["value"] for i in json.loads(response.content)]


@st.cache(hash_funcs={"_thread.RLock": lambda _: None, 'builtins.weakref': lambda _: None}, show_spinner=False)
def get_all_empreendimentos_vista():
    headers = {
    'accept': 'application/json'
    }
    b = []

    for i in range(1, 99999):
        url = f'http://brasaolt-rest.vistahost.com.br/imoveis/listar?key={st.secrets["vista_api_key"]}&showtotal=0&showInternal=1&showSuspended=1&pesquisa={{"fields":["Status", "Codigo", "Categoria", "Empreendimento"], "order": {{"Codigo": "asc"}}, "filter": {{"Categoria": ["Empreendimento"]}}, "paginacao":{{"pagina":{i},"quantidade":50}}}}'
        response = requests.get(url, headers = headers)
        if response.status_code == 500:
            break
        b.append(json.loads(response.content))
    a = []
    for item in b:
        df = pd.DataFrame(item).T
        a.append(df)
    return pd.concat(item for item in a)


def create_hubspot_file(filename, file_content):
    post_url = f'https://api.hubapi.com/filemanager/api/v3/files/upload?hapikey={st.secrets["api_key"]}'

    file_options = {
        'access': 'PRIVATE',
        'ttl': 'P12M',
        "overwrite": False,
        'duplicateValidationStrategy': 'NONE',
        'duplicateValidationScope': 'EXACT_FOLDER'
    }

    files_data = {
        'file': (filename, file_content, 'application/octet-stream'),
        'options': (None, json.dumps(file_options), 'text/strings'),
        'folderPath': (None, st.secrets['folder_agenciamentos_nome'], 'text/strings')
    }

    response = requests.post(post_url, files = files_data)

    return response


def associate_file_to_deal(deal_id, id_do_arquivo):
    url = "https://api.hubapi.com/engagements/v1/engagements"

    querystring = {"hapikey": st.secrets['api_key']}

    payload = json.dumps({
        "engagement": {
            "active": 'true',
            "type": "NOTE",
        },
        "associations": {
            "contactIds": [],
            "companyIds": [],
            "dealIds": [deal_id],
            "ownerIds": []
        },
        "attachments": [
            {
                "id": id_do_arquivo
            }
        ],
        "metadata": {
            "body": "nota"
        }
    })

    headers = {
        'Content-Type': "application/json",
    }

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

    return response


@st.cache(hash_funcs={"_thread.RLock": lambda _: None, 'builtins.weakref': lambda _: None}, show_spinner=False)
def get_exact_filtros():
    exact_headers = {
            'Content-Type': 'application/json',
            'token_exact': st.secrets['token_exact_api']
        }
    response = requests.get('https://api.exactsales.com.br/v3/Answers', headers=exact_headers)
    exact_filtro_1 = pd.DataFrame(json.loads(response.content)['value'][0]['questions'])
    exact_filtro_2 = pd.DataFrame(json.loads(response.content)['value'][1]['questions'])

    return exact_filtro_1, exact_filtro_2


def check_password(secrets_key):
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state[secrets_key] == st.secrets[secrets_key]:
            st.session_state[f"password_correct_{secrets_key}"] = True
            del st.session_state[secrets_key]  # don't store password
        else:
            st.session_state[f"password_correct_{secrets_key}"] = False

    if f"password_correct_{secrets_key}" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key=secrets_key
        )
        return False
    elif not st.session_state[f"password_correct_{secrets_key}"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key=secrets_key
        )
        st.error("Password incorreto 😕")
        return False
    else:
        # Password correct.
        return True

 
@st.cache(hash_funcs={"_thread.RLock": lambda _: None, 'builtins.weakref': lambda _: None}, show_spinner=False)
def get_df_usuarios(only_vendas):
    """
    Retorna df do vista com todos os usuários de locação.
    """
    headers = {
    'accept': 'application/json'
    }
    for page in range(1, 100):
        if only_vendas:
            url = f'http://brasaolt-rest.vistahost.com.br/usuarios/listar?key={st.secrets["vista_api_key"]}&pesquisa={{"fields":["Codigo", "Nomecompleto", "Nome", "E-mail", "Atua\\u00e7\\u00e3oemloca\\u00e7\\u00e3o", "Atua\\u00e7\\u00e3oemvenda",  "Corretor", "Gerente", "Agenciador", "Administrativo", "Observacoes", {{"Equipe": ["Nome"]}}], "filter": {{"Exibirnosite": ["Sim"], "Atua\\u00e7\\u00e3oemvenda": ["Sim"], "Corretor": ["Sim"], "Gerente": ["Nao"]}}, "paginacao":{{"pagina":{page}, "quantidade":50}}}}&Equipe={{"fields:["Nome"]}}'
        else:
            url = f'http://brasaolt-rest.vistahost.com.br/usuarios/listar?key={st.secrets["vista_api_key"]}&pesquisa={{"fields":["Codigo", "Nomecompleto", "Nome", "E-mail", "Atua\\u00e7\\u00e3oemloca\\u00e7\\u00e3o", "Atua\\u00e7\\u00e3oemvenda",  "Corretor", "Gerente", "Agenciador", "Administrativo", "Observacoes", {{"Equipe": ["Nome"]}}], "filter": {{"Exibirnosite": ["Sim"], "Corretor": ["Sim"], "Gerente": ["Nao"]}}, "paginacao":{{"pagina":{page}, "quantidade":50}}}}&Equipe={{"fields:["Nome"]}}'
        response = requests.get(url, headers=headers)
        if response.content == b'[]':
            break
        df_usuarios = pd.DataFrame(json.loads(response.content))[1:].T
    df_usuarios['Equipe'] = df_usuarios['Equipe'].apply(lambda x: [x[key] for key in x][0]['Nome'] if type(x) == dict else x)
    df_usuarios.reset_index(inplace=True, drop=True)

    return df_usuarios.sort_values(by="Nomecompleto")


# @st.cache
def return_labels_hubspot_property(object_type, property_name):
    try:
        # para consultar as properties
        api_response = api_client.crm.properties.core_api.get_by_name(object_type=object_type, property_name=property_name, archived=False)
        api_response_dict = api_response.to_dict()
        return {"options": [option.get('label') for option in api_response_dict['options']], "label": api_response_dict['label']}
    except PropertyException as e:
        print("Exception when calling core_api->get_by_name: %s\n" % e)


def create_hubspot_note(message):
    url = "https://api.hubapi.com/crm/v3/objects/notes"

    querystring = {"hapikey":f"{st.secrets['api_key']}"}

    payload = {"properties":{"hs_timestamp": f"{datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}", "hs_note_body": message}}

    headers = {
        'accept': "application/json",
        'content-type': "application/json"
        }

    response = requests.request("POST", url, data=json.dumps(payload), headers=headers, params=querystring)

    note_id = json.loads(response.content)['id']

    return note_id


def create_hubspot_deal(contact_dict, deal_dict, note_dict, files=None):
    try:
        # criando o contato no hubspot
        simple_public_object_input = SimplePublicObjectInput(
            properties=contact_dict
        )
        create_client_response = api_client.crm.contacts.basic_api.create(
            simple_public_object_input=simple_public_object_input
        )

        client_id = create_client_response.to_dict()['id']

        # criando o deal no hubspot
        # aqui estou definindo dentro da função pra mandar o deal pra essa parte da pipeline
        deal_dict["dealstage"] = "qualifiedtobuy" # Imóvel Captado
        simple_public_object_input = SimplePublicObjectInput(
            properties=deal_dict
        )
        create_deal_response = api_client.crm.deals.basic_api.create(
            simple_public_object_input=simple_public_object_input
        )

        deal_id = create_deal_response.to_dict()["id"]

        # associando os files ao deal, se existirem
        if files:
            for file in files:
                file_string = file.read()
                r = create_hubspot_file(filename=file.name, file_content=file_string)
                id_do_arquivo = json.loads(r.content)['objects'][0]['id']
                associate_file_to_deal(deal_id=deal_id, id_do_arquivo=id_do_arquivo)

        # associar o deal ao id do contato
        associate_contact_deal_response = api_client.crm.deals.associations_api.create(deal_id=deal_id, to_object_type="Contacts", to_object_id=client_id, association_type="deal_to_contact")

        # criando a note no hubspot
        note_id = create_hubspot_note(message=note_dict["note"])

        # associando a note ao deal
        associationType = "214"
        url = f"https://api.hubapi.com/crm/v3/objects/notes/{note_id}/associations/Deals/{deal_id}/{associationType}"
        querystring = {"hapikey":f"{st.secrets['api_key']}"}
        headers = {'accept': 'application/json'}

        response = requests.request("PUT", url, headers=headers, params=querystring)

    except ContactException as e:
        print("Exception when creating contact: %s\n" % e)
    except DealException as e:
        print("Exception when creating deal: %s\n" % e)

    return None   


if check_password("application_password"):

    # ----------- Global Sidebar ---------------

    condition = st.sidebar.selectbox(
        "Selecione a Aba",
        ("Cadastro de Agenciamentos", "Cadastro de Clientes")
    )

    # ------------- Agenciamentos ------------------------

    if condition == 'Cadastro de Agenciamentos':
        st.subheader("Formulário de Indicação de Agenciamentos")
        df_usuarios_ativos_vista_vendas = get_df_usuarios(only_vendas=False)
        api_client = HubSpot(api_key=st.secrets["api_key"])
        deal_submit_dict = {}
        contact_submit_dict = {}
        note_submit_dict = {}
        pattern = "\(\d{2,}\) \d{4,}\-\d{4}"

        # esse dict são as propriedades que serão consultadas
        hubspot_properties = [
            {'property_name': 'rua', 'object_type': 'Deals'},
            {'property_name': 'bairro', 'object_type': 'Deals'},
            {'property_name': 'cidade', 'object_type': 'Deals'},
            {'property_name': 'tipo_de_imovel', 'object_type': 'Deals'},
            {'property_name': 'origem', 'object_type': 'Deals'},
            {'property_name': 'status', 'object_type': 'Deals'},
            {'property_name': 'data_de_contato_para_confirmacao_de_informacoes', 'object_type': 'Deals'},
        ]

        type_of_view = st.radio("Selecione o tipo de visualização", ("Cadastrar um Agenciamento", "Verificar Status dos meus Agenciamentos"))    

        if type_of_view == "Cadastrar um Agenciamento":
            with st.form("cadastro_agenciamentos"):
                deal_submit_dict["dealname"] = st.text_input(label='Endereço do Imóvel', help='Informe apenas a Rua, o nº do imóvel e se existir, o complemento.')
                col_1, col_2 = st.columns(2)
                with col_1:
                    contact_submit_dict["firstname"] = st.text_input(label='Nome do Proprietário', help='Informe o nome completo do proprietário do imóvel.')
                    contact_submit_dict["lastname"] = st.text_input(label='Sobrenome do Proprietário', help='Informe o sobrenome do proprietário do imóvel.')
                    contact_submit_dict["email"] = st.text_input(label='E-mail do Proprietário', help='Informe o e-mail do proprietário do imóvel.')
                    contact_submit_dict["phone"] = st.text_input(label='Telefone do Proprietário', help='Informe o telefone do proprietário do imóvel.')
                    data_de_conversa = st.date_input(label='Data de Conversa com o Proprietário', help='Informe a data da conversa com o propriétario.')
                    mensagem = st.text_area(label='Mensagem', help='Descreva brevemente o que foi conversado com o proprietário.', height=238)

                with col_2:
                    for property in hubspot_properties:
                        property_characteristics = return_labels_hubspot_property(property['object_type'], property['property_name'])
                        # aqui eu ainda não defini o nome da variável pra adicionar no hub, mas tem que definir
                        deal_submit_dict[property.get('property_name')] = st.selectbox(options=property_characteristics.get("options"), label=property_characteristics.get("label"))
                    deal_submit_dict["nome_do_indicador"] = st.selectbox(options=df_usuarios_ativos_vista_vendas['Nomecompleto'].tolist(), label='Indicador')
                
                files = st.file_uploader(label='Caso existam documentos, anexe-os aqui.', accept_multiple_files=True)
                
                # Every form must have a submit button.
                st.info("**Por favor, confira todos os valores antes de enviar o formulário.**")
                submitted = st.form_submit_button("Enviar")
                if submitted:
                    # checando se existe algum campo requirido em campo.
                    required_fields = [deal_submit_dict["dealname"], contact_submit_dict["firstname"], contact_submit_dict["lastname"], contact_submit_dict["phone"], mensagem]
                    if any([True for field in required_fields if field == '' or field == []]):
                        st.error('Por favor, preencha todos os campos corretamente.')
                        st.stop()
                    elif len(re.findall(pattern, contact_submit_dict["phone"])) < 1:
                        st.error('Por favor, o formato do telefone do contato deve ser como em: (55) 99999-9999 ou (55) 3221-5469.')
                        st.stop()
                    # criando a mensagem para ser enviada no deal do hubspot
                    note_submit_dict["note"] = f'Imóvel indicado pelo corretor {deal_submit_dict["nome_do_indicador"]}. O corretor indicou que o conversou com o proprietário do imóvel no dia {data_de_conversa}. O imóvel está identificado como {deal_submit_dict["rua"]}, {deal_submit_dict["dealname"]} no bairro {deal_submit_dict["bairro"]} e estaria disponível para {deal_submit_dict["status"]}. O proprietário do imóvel é {contact_submit_dict["firstname"]} {contact_submit_dict["lastname"]} e o e-mail dele é {contact_submit_dict["email"] if contact_submit_dict["email"] != "" else "inexistente"}. O imóvel foi captado através de {deal_submit_dict["origem"]}, o contato do proprietário foi obtido através de {deal_submit_dict["data_de_contato_para_confirmacao_de_informacoes"]}. O telefone dele é {contact_submit_dict["phone"] if contact_submit_dict["phone"] != "" else "inexistente"}. O que ficou conversado entre o corretor e o proprietário foi: {mensagem}.'

                    dict_to_show_after_success = {
                        "Nome do proprietário": contact_submit_dict["firstname"],
                        "Sobrenome do proprietário": contact_submit_dict["lastname"],
                        "Email do proprietário": contact_submit_dict["email"],
                        "Telefone do proprietário": contact_submit_dict["phone"],
                        "Origem do Contato do Proprietário": deal_submit_dict["data_de_contato_para_confirmacao_de_informacoes"],
                        "Data de conversa com o proprietário": data_de_conversa.strftime('%d/%m/%Y'),
                        "Endereço do imóvel": deal_submit_dict["dealname"],
                        "Tipologia": deal_submit_dict["rua"],
                        "Bairro": deal_submit_dict["bairro"],
                        "Cidade": deal_submit_dict["cidade"],
                        "Finalidade": deal_submit_dict["tipo_de_imovel"],
                        "Origem do Imóvel": deal_submit_dict["origem"],
                        "Status": deal_submit_dict["status"],
                        "Nome do Indicador": deal_submit_dict["nome_do_indicador"],
                        "Mensagem": mensagem,
                    }
                    
                    try:
                        # colocar um spinner aqui checando se foi tudo bonitinho pro hubspot, se foi, exibe a mensagem, se não, pede pra cadastrar de novo
                        with st.spinner('Registrando o formulário...'):
                            create_hubspot_deal(contact_dict=contact_submit_dict, deal_dict=deal_submit_dict, note_dict=note_submit_dict, files=files)
                        st.success("Formulário enviado com sucesso!")
                        st.write(f"Os dados enviados foram: ")
                        st.write(dict_to_show_after_success)
                        st.warning("Por favor, confirme o envio dos dados. Caso haja alguma alteração, entrar em contato diretamente com o setor responsável.")
                    except:
                        st.write("Houve um erro no envio do formulário. Por favor, tente novamente em alguns minutos. Caso o erro persista, entre em contato com o administrador.")

        elif type_of_view == "Verificar Status dos meus Agenciamentos":
            pipeline_name = 'Captação de Imóveis'

            nome_do_corretor = st.selectbox(options=df_usuarios_ativos_vista_vendas['Nomecompleto'].tolist(), label='Indicador')
            button_filter_df = st.button('Filtrar')

            if button_filter_df:
                with st.spinner('Carregando os dados...'):
                    api_response = api_client.crm.deals.get_all(archived=False, properties=['amount', 'dealname', 'dealstage', 'status', 'bairro', 'valor_venda',
                                                                'data_de_contato_para_confirmacao_de_informacoes', 'data_das_fotos', 'nome_do_indicador', 'tipo_de_imovel', 'origem', 'rua', 'hubspot_owner_id', 'closed_lost_reason', 'closedate'])                                                                    
                    df_hubspot_deals = pd.DataFrame([i.to_dict().get('properties') for i in api_response])
                    df_hubspot_deals = df_hubspot_deals.drop_duplicates(subset='hs_object_id')
                    df_hubspot_deals.columns = ['valor_aluguel', 'bairro', 'motivo_perda', 'data_fechamento', 'data_indicacao', 'data_fotos_imovel', 'origem_contato_proprietario' , 'endereco', 'estagio_indicacao', 'ultima_atualizacao', 'deal_id', 'agenciador_responsavel', 'nome_do_indicador', 'origem_imovel', 'tipologia', 'status', 'finalidade', 'valor_venda']

                    df_hubspot_deals = df_hubspot_deals[['endereco', 'estagio_indicacao', 'data_indicacao', 'data_fotos_imovel', 'agenciador_responsavel', 'ultima_atualizacao', 'tipologia', 'bairro', 'finalidade', 'status', 'valor_aluguel', 'valor_venda', 'origem_imovel', 'origem_contato_proprietario', 'motivo_perda', 'nome_do_indicador']]

                    all_pipelines = api_client.crm.pipelines.pipelines_api.get_all(object_type="Deals")
                    my_pipeline_id = [i.get('id') for i in all_pipelines.to_dict()['results'] if i.get('label') == pipeline_name][0]
                    my_pipeline_stages = api_client.crm.pipelines.pipeline_stages_api.get_all(object_type="Deals", pipeline_id=my_pipeline_id)
                    my_pipeline_stages = pd.DataFrame(my_pipeline_stages.to_dict()['results'])

                    all_users = api_client.crm.owners.get_all()
                    all_users = pd.DataFrame([i.to_dict() for i in all_users])
                    all_users['agenciador_responsavel'] = all_users['first_name'] + ' ' + all_users['last_name']

                    df_hubspot_deals['estagio_indicacao'] = df_hubspot_deals['estagio_indicacao'].map(my_pipeline_stages.set_index('id')['label'])
                    df_hubspot_deals['agenciador_responsavel'] = df_hubspot_deals['agenciador_responsavel'].map(all_users.set_index('id')['agenciador_responsavel'])
                    df_to_show = df_hubspot_deals.loc[df_hubspot_deals['nome_do_indicador'] == nome_do_corretor]
                    if df_to_show.shape[0] > 0:
                        st.write(df_to_show)
                    else:
                        st.info("Nenhum agenciamento encontrado para o corretor selecionado.")




    # ------------- Clientes ------------------------

    # if condition == 'Cadastro de Clientes':
    #     st.subheader("Formulário de Cadastro de Clientes")
    #     # isso aqui eu coloco no custom field de corretor responsável
    #     df_usuarios_ativos_vista_all = get_df_usuarios(only_vendas=False)
    #     origens = ['Anúncio jornal', 'Inbound Marketing', 'Indicacao', 'Portais', 'Prospecção Ativa', 'Redes Sociais', 'Sede', 'Site', 'website_formulario_agendar_visita', 'website_formulario_anuncio', 'website_formulario_contato', 'website_formulario_indicacao', 'WhatsApp']
    #     atendimento_realizado = st.checkbox(label='Atendimento Já Realizado', help='Marque se você já realizou o atendimento e coletou todas as informações do cliente.')
        
    #     if atendimento_realizado:
    #         exact_filtro_1, exact_filtro_2 = get_exact_filtros()

    #         finalidade = st.selectbox(label='Finalidade', options=['Residencial', 'Comercial'])

    #         st_elements.get_form_cliente_atendido(indicadores=df_usuarios_ativos_vista_all, origens=origens, finalidade=finalidade, exact_filtro_1=exact_filtro_1, exact_filtro_2=exact_filtro_2)

    #     else:
    #         st_elements.get_form_cliente_nao_atendido(indicadores=df_usuarios_ativos_vista_all, origens=origens)

    if condition == 'Cadastro de Clientes':
        st.subheader("Formulário de Cadastro de Clientes")
        # isso aqui eu coloco no custom field de corretor responsável
        df_usuarios_ativos_vista_all = get_df_usuarios(only_vendas=False)
        # origens = ['Anúncio jornal', 'Inbound Marketing', 'Indicacao', 'Portais', 'Prospecção Ativa', 'Redes Sociais', 'Sede', 'Site', 'website_formulario_agendar_visita', 'website_formulario_anuncio', 'website_formulario_contato', 'website_formulario_indicacao', 'WhatsApp']
        origens = get_exact_origens()
        empreendimentos = get_all_empreendimentos_vista()

        st_elements.get_form_client(indicadores=df_usuarios_ativos_vista_all, origens=origens, empreendimentos=sorted(empreendimentos["Empreendimento"].unique()))




            
