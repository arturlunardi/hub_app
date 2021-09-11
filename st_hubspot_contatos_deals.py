from hubspot import HubSpot
from hubspot.crm.deals import ApiException
import pandas as pd
import streamlit as st
import base64
from io import BytesIO


@st.cache(hash_funcs={"_thread.RLock": lambda _: None})
def get_df_deals():
    try:
        api_client = HubSpot(api_key=st.secrets["api_key"])
        api_response = api_client.crm.deals.get_all(archived=False, associations=['contact'], properties=['bairro', 'tipo_de_imovel', 'origem', 'rua', 'hubspot_owner_id', "amount", "closedate", "createdate", "dealname", "dealstage", "hs_lastmodifieddate",	"hs_object_id"])
        api_contacts = api_client.crm.contacts.get_all(archived=False, properties=['firstname', 'lastname', 'phone'])

        df_contacts = pd.DataFrame([i.to_dict().get('properties') for i in api_contacts])
        df_deals = pd.DataFrame([i.to_dict().get('properties') for i in api_response])
        df_associations = [i.to_dict().get("associations") for i in api_response]
        df_associations = pd.DataFrame([i.get('contacts').get('results')[0].get('id') if i is not None else '-' for i in df_associations ])
        df_deals['contact_id'] = df_associations.values

        df_deals.loc[df_deals['dealstage'] ==
                'appointmentscheduled', 'dealstage'] = 'Imóvel Captado'
        df_deals.loc[df_deals['dealstage'] == 'qualifiedtobuy',
                    'dealstage'] = 'Cliente Qualificado'
        df_deals.loc[df_deals['dealstage'] == '10692229',
                    'dealstage'] = 'Cliente Contatado - Aguardando Retorno'
        df_deals.loc[df_deals['dealstage'] == 'presentationscheduled',
                    'dealstage'] = 'Imóvel Disponível'
        df_deals.loc[df_deals['dealstage'] == 'decisionmakerboughtin',
                    'dealstage'] = 'Condições Negociadas'
        df_deals.loc[df_deals['dealstage'] ==
                    '7077163', 'dealstage'] = 'Fotos Realizadas'
        df_deals.loc[df_deals['dealstage'] == '7077164',
                    'dealstage'] = 'Cadastro Realizado'
        df_deals.loc[df_deals['dealstage'] ==
                    'closedwon', 'dealstage'] = 'Negócio Fechado'
        df_deals.loc[df_deals['dealstage'] ==
                    'closedlost', 'dealstage'] = 'Negócio Perdido'

        
        df_deals.loc[df_deals['hubspot_owner_id'] == '53280320',
                'hubspot_owner_id'] = 'Artur Lunardi Di Fante'
        df_deals.loc[df_deals['hubspot_owner_id'] == '53280868',
                    'hubspot_owner_id'] = 'Artur Lunardi Di Fante'
        df_deals.loc[df_deals['hubspot_owner_id'] == '58310573',
                    'hubspot_owner_id'] = 'Fernando Kerkhoff'
        df_deals.loc[df_deals['hubspot_owner_id'] == '58311273',
                    'hubspot_owner_id'] = 'Giselle Centenaro'
        df_deals.loc[df_deals['hubspot_owner_id'] == '102130963',
                    'hubspot_owner_id'] = 'Lucas Oliveira'

        df_deals.loc[df_deals['hubspot_owner_id'] == 'Fernando Kerkhoff',
                    'hubspot_owner_id'] = 'Luis Fernando Kerkhoff'


        df_contacts = df_contacts.drop(columns=['createdate', 'lastname', 'lastmodifieddate'])

        df_deals.columns=['valor_aluguel', 'bairro', 'data_fechamento', 'createdate', 'nome_negocio', 'dealstage', 'ultima_modificacao', 'deal_id', 'dono_negocio', 'origem', 'tipologia', 'finalidade', 'contact_id']
        df_deals = df_deals[['createdate', 'nome_negocio', 'bairro', 'tipologia', 'finalidade', 'valor_aluguel', 'dealstage', 'origem', 'dono_negocio', 'data_fechamento', 'ultima_modificacao', 'deal_id', 'contact_id']]
        df_deals = df_deals.loc[df_deals['dealstage'] == 'Cliente Qualificado']
        df_deals = df_deals.merge(df_contacts, left_on='contact_id', right_on='hs_object_id', how='left')
        # pprint(api_response)

    except ApiException as e:
        print("Exception when calling basic_api->get_page: %s\n" % e)
    
    return df_deals


@st.cache
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data


df_deals = get_df_deals()
df_excel = to_excel(df_deals)
password = st.text_input("Password:", value="", type="password")

if password == st.secrets['application_password']:
    st.download_button(
        label="Pressione para Download",
        data=df_excel,
        file_name='extract.xlsx',
    )
elif password == "":
    st.write('Digite a senha para acessar o App')
else:
    st.write('Password Incorreto')