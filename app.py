from datetime import date, datetime, timedelta
from wordcloud import WordCloud, STOPWORDS
from collections import Counter
import plotly.express as px
import streamlit as st
import pandas as pd
import emoji
import regex
import re

st.set_page_config(layout="wide") 

st.markdown("<h1 style='text-align: center;'>ANALYSE YOUR WHATSAPP CHAT</h1>", unsafe_allow_html=True)
st.subheader("In this web application you can import your Whatsapp chat and analyse all the data it contains filtering by the dates you want to analyse.")
st.write("")
video = 'https://www.youtube.com/watch?v=TL9fq-EYlKg'
st.subheader("In order to analyze your WhatsApp chat, you must import the entire conversation in .txt format. You can see how to export your conversation in the following [video]({}).".format(video))
st.write("No chat data is sent to a server! All codes are executed locally in your browser.")

uploaded_file = st.file_uploader(label='Iporta el archivo .txt', type=["txt"])

def get_df(file):
    pattern = re.compile(r'\[(\d+/\d+/\d+, \d+:\d+:\d+)\] (.+?): (.+)')

    data = []
    content = uploaded_file.read().decode('utf-8').splitlines()

    for line in content:
        match = pattern.match(line)
        if match:
            timestamp = match.group(1)
            username = match.group(2)
            message = match.group(3)

            date, time = timestamp.split(', ')
            
            data.append([date, time, username, message])

    df = pd.DataFrame(data, columns=['Date', 'Time', 'Username', 'Message'])
    
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y')
    df['Date'] = df['Date'].dt.date
    
    return df

if uploaded_file is not None:
    # Leer el contenido del archivo
    total_df = get_df(uploaded_file)
    max_index = len(total_df) - 1
    min_date = total_df['Date'][0]
    max_date = total_df['Date'].iloc[-1]
    col1, col2, col3, col4 = st.columns([0.5,0.5,1,1.5])
    
    with col1:
        start_date = st.date_input(label="Select a start date", value=min_date, min_value=min_date, format="DD/MM/YYYY")
    with col2:
        end_date = st.date_input(label="Select an end date", value=max_date, max_value=max_date, format="DD/MM/YYYY")
        end_date = end_date + timedelta(days=1)
    with col3:
        st.title("")
        action = st.button(label='View Results')
        
        
    def get_filtered_df(df, start, end):
        df_filtrado = df.loc[(df['Date'] >= start) & (df['Date'] <= end)]
        return df_filtrado

    def get_emogis(df):
        def ObtenerEmojis(Mensaje):
            emoji_lista = []
            data = regex.findall(r'\X', Mensaje) # Obtener lista de caracteres de cada mensaje
            for caracter in data:
                if caracter in emoji.EMOJI_DATA: # Obtener emojis en idioma español
                    emoji_lista.append(caracter)
            return emoji_lista
        
        df['Emojis'] = df["Message"].apply(ObtenerEmojis) # Se agrega columna 'Emojis'
        
        emojis_lista = list([a for b in df['Emojis'] for a in b])
        emoji_diccionario = dict(Counter(emojis_lista))
        emoji_diccionario = sorted(emoji_diccionario.items(), key=lambda x: x[1], reverse=True)

        # Convertir el diccionario a dataframe
        emoji_df = pd.DataFrame(emoji_diccionario, columns=['Emoji', 'Cantidad'])

        # Establecer la columna Emoji como índice
        emoji_df = emoji_df.set_index('Emoji')
        return emoji_df
    
    def get_messages(df):
        df_persona = df.groupby('Username').count().reset_index()

        return df_persona

    def get_daily_mess(df):
        df['# Mensajes por día'] = 1
        date_df = df.groupby('Date').sum().reset_index()
        return date_df

    def get_weekly_mes(df):
        dia = []
        días = {0: 'Dilluns', 1: 'Dimarts', 2: 'Dimecres', 3: 'Dijous', 4: 'Divendres', 5: 'Dissabte', 6: 'Diumenge'}

        for i, row in df.iterrows():
            fecha_obj = datetime.strptime(str(row['Date']), '%Y-%m-%d')
            dia_semana = fecha_obj.weekday()
            dia_semana_f = días[dia_semana]
            dia.append(dia_semana_f)
            
        df['day_of_the_week'] = dia
        
        numeric_columns = df.select_dtypes(include='number').columns
        week_df = df.groupby('day_of_the_week')[numeric_columns].sum().reset_index()
        return week_df

    if action:
        df = get_filtered_df(total_df, start_date, end_date)
        c1, c2 = st.columns(2)
        
        with c1:
            e_df = get_emogis(df)
            fig = px.pie(e_df, values='Cantidad', names=e_df.index, title='Use of emojis')
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, theme='streamlit', use_container_width=True)
        
        with c2:
            mes_df = get_messages(df)
            fig = px.bar(mes_df, x='Message', y='Username', title='Number of message per user', orientation='h')

            fig.update_xaxes(title_text='# Mensajes', tickangle=45, nticks=35)
            fig.update_yaxes(title_text='Username')
            st.plotly_chart(fig, theme='streamlit', use_container_width=True)    
        
        def get_perc_mess(df):
            if len(df) > 7:
                half = (len(df) + 1) // 2
                cols = st.columns(half)
                total = df['Message'].sum()

                for i, col in enumerate(cols):
                    if i < len(df):
                        user = df['Username'][i]
                        perc = "{:.2%}".format(df['Message'][i] / total)
                        col.metric(label=f'Messages of {user}:', value=perc)

                for i, col in enumerate(cols, start=half):
                    if i <= len(df):
                        user = df['Username'][i]
                        perc = "{:.2%}".format(df['Message'][i] / total)
                        col.metric(label=f'Messages of {user}:', value=perc)
            
            else:
                cols = st.columns(len(df))
                total = df['Message'].sum()

                for i, col in enumerate(cols):
                    if i < len(df):
                        user = df['Username'][i]
                        perc = "{:.2%}".format(df['Message'][i] / total)
                        col.metric(label=f'Messages of {user}:', value=perc)
        
        try:
            st.markdown("**Percentage of messages by user**", unsafe_allow_html=True)
            get_perc_mess(mes_df)
        except KeyError:
            pass
        
        date_df = get_daily_mess(df)
        fig = px.line(date_df, x='Date', y='# Mensajes por día', title='Progression of number of message by time')
        fig.update_xaxes(title_text='Date', tickangle=45, nticks=35)
        fig.update_yaxes(title_text='# Mensajes')
        st.plotly_chart(fig, theme='streamlit', use_container_width=True)

        week_df = get_weekly_mes(df)
        fig = px.bar(week_df, x='day_of_the_week', y='# Mensajes por día', title='Number of messages by weekday')
        fig.update_xaxes(title_text='Week Day', tickangle=45, nticks=35)
        fig.update_yaxes(title_text='# Mensajes')
        st.plotly_chart(fig, theme='streamlit', use_container_width=True)

        try:
            total_palabras = ' '
            stopwords = set(STOPWORDS)
            stopwords.update(['que', 'qué', 'con', 'de', 'te', 'en', 'la', 'lo', 'le', 'el', 'las', 'los', 'les', 'por', 'es',
                              'son', 'se', 'para', 'un', 'una', 'chicos', 'su', 'si', 'chic','nos', 'ya', 'hay', 'esta',
                              'pero', 'del', 'mas', 'más', 'eso', 'este', 'como', 'así', 'todo', 'https','Media','omitted',
                              'y', 'mi', 'o', 'q', 'yo', 'al', 'per', 'https:', 'que', 'en', 'https', 'utm_medium'])

            for mensaje in df['Message'].values:
                palabras = str(mensaje).lower().split()
                for palabra in palabras:
                    total_palabras = total_palabras + palabra + ' '

            wordcloud = WordCloud(width=1000, height=700, background_color='black', stopwords=stopwords, min_font_size=10).generate(total_palabras)
            st.markdown("**Word map of the most used words**", unsafe_allow_html=True)
            st.image(wordcloud.to_image(), use_column_width=True)

        
        except ValueError:
            st.markdown("<h1 style='text-align: center;'>No hay datos que analizar</h1>", unsafe_allow_html=True)