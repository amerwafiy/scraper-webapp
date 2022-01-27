import streamlit as st
import pandas as pd
import datetime as dt
from datetime import timedelta
import re
from datetime import date
import snscrape.modules.twitter as sntwitter
import os
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb
from PIL import Image
import matplotlib.pyplot as plt
from colour import Color
#from st_aggrid import AgGrid
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('max_colwidth', None)

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Data')
    workbook = writer.book
    worksheet = writer.sheets['Data']
    format1 = workbook.add_format({'num_format': '0.00'})
    worksheet.set_column('A:A', None, format1)
    writer.save()
    processed_data = output.getvalue()
    return processed_data

@st.cache
def convert_df(df):
    return df.to_csv().encode('utf-8')

image = Image.open('invoke_logo.jpg')
st.image(image)
st.title('Social Media Scraper')

option1 = st.selectbox('Select a platform', ('Twitter 🐦', 'Facebook 📘', 'Instagram 📸'))

if option1 == 'Twitter 🐦':
    option = st.selectbox('Choose a scraping option',
        ('', 'Scrape on user 👨‍👩‍👧‍👦', 'Scrape on keyword/hashtag 💬'))

    if option == 'Scrape on user 👨‍👩‍👧‍👦':
        users= st.text_input('Enter username(e.g. @rafiziramli @najibrazak)', '')
        from_date = st.date_input("From", value = dt.date.today() - dt.timedelta(days=1), max_value = dt.date.today() - dt.timedelta(days=1))
        end_date = str(st.date_input("Until", max_value = dt.date.today(), min_value = from_date + dt.timedelta(days=1)))
        max_results = (st.text_input('Set maximum number of tweets to scrape per profile', ''))
        if st.button('Scrape Tweet!'):
            tweets_list = []
            users = users.split(' ')
            users = [x[1:] for x in users]

            # Using TwitterSearchScraper to scrape data and append tweets to list
            for user in users:
                search_term = user + ' since:' + str(from_date) + ' until:' + str(end_date)
                for i,data in enumerate(sntwitter.TwitterUserScraper(search_term).get_items()):
                    if i == int(max_results):
                        break
                    date = pd.to_datetime(str(data.date)[:19]) + timedelta(hours=8)
                    time = str(date)[11:]
                    username = data.username
                    tweet = data.content
                    tweet = repr(tweet)
                    tweet = tweet.replace("\\n" , " ")
                    tweet = tweet.replace("  " , " ")
                    mention = re.compile(r'@([a-zA-Z0-9_]+)').findall(tweet)
                    link = ink = re.compile(r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})').findall(tweet)
                    if len(mention) > 0:
                        mention = ['@' + x for x in mention]
                    url = data.url
                    tweets_list.append([date, time , username, tweet, mention, link, url])

            if len(tweets_list) == 0:
                st.write('No tweets found! Please make sure you entered the correct profile name')
            else:
                tweets_df = pd.DataFrame(tweets_list, columns=['Date', 'Time', 'Username', 'Tweet', 'Mention', 'Link', 'Tweet URL'])
                tweets_df['Date'] = tweets_df["Date"].dt.strftime("%d/%m/%Y")
                tweets_df.index += 1
                st.subheader('Sample Data')
                if int(max_results) > 5:
                    st.table(tweets_df[['Date', 'Tweet']][:5])
                else:
                    st.table(tweets_df[['Date', 'Tweet']])
                csv = convert_df(tweets_df)
                st.download_button(label="📥 Download data as CSV", data=csv,file_name='tweets_df.csv', mime='text/csv')
#                 df_xlsx = to_excel(tweets_df)
#                 st.download_button(label='📥 Download Full Data', data=df_xlsx, file_name='tweets_'+ str(max_results)+ '.xlsx')

    elif option == 'Scrape on keyword/hashtag 💬':
        search= st.text_input('Enter keyword/hashtag (Please separate multiple keywords/hashtags by "," e.g. Bitcoin,#Ethereum)', '')
        from_date = st.date_input("From", value = dt.date.today() - dt.timedelta(days=1), max_value = dt.date.today() - dt.timedelta(days=1))
        end_date = str(st.date_input("Until", max_value = dt.date.today(), min_value = from_date + dt.timedelta(days=1)))
        max_results = (st.text_input('Set maximum number of tweets to scrape', ''))
        if st.button('Scrape Tweet!'):
            tweets_list = []
            search = search.split(',')
            for s in search:
                search_term = s + ' since:' + str(from_date) + ' until:' + str(end_date)
                for i,data in enumerate(sntwitter.TwitterSearchScraper(search_term).get_items()):
                    if i == int(max_results):
                        break
                    date = pd.to_datetime(str(data.date)[:19]) + timedelta(hours=8)
                    time = str(date)[11:]
                    keyword = s
                    tweet = data.content
                    tweet = repr(tweet)
                    tweet = tweet.replace("\\n" , " ")
                    tweet = tweet.replace("  " , " ")
                    mention = re.compile(r'@([a-zA-Z0-9_]+)').findall(tweet)
                    link = ink = re.compile(r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})').findall(tweet)
                    if len(mention) > 0:
                        mention = ['@' + x for x in mention]
                    url = data.url
                    tweets_list.append([date, time , tweet, keyword, mention, link, url])

            if len(tweets_list) == 0:
                st.write('No tweets found!')
            else:
                tweets_df = pd.DataFrame(tweets_list, columns=['Date', 'Time', 'Tweet', 'Keyword', 'Mention', 'Link', 'Tweet URL'])
                tweets_df['Date'] = tweets_df["Date"].dt.strftime("%d/%m/%Y")
                tweets_df.index += 1
                st.subheader('Sample Data')
                if int(max_results) > 5:
                    st.table(tweets_df[['Date', 'Tweet', 'Mention', 'Keyword']][:5])
                else:
                    st.table(tweets_df[['Date', 'Tweet', 'Mention', 'Keyword']])
                csv = convert_df(tweets_df)
                st.download_button(label="📥 Download data as CSV", data=csv,file_name='tweets_df.csv', mime='text/csv')
#                 df_xlsx = to_excel(tweets_df)
#                 st.download_button(label='📥 Download Full Data', data=df_xlsx, file_name='tweets_'+ str(max_results)+ '.xlsx')

elif option1 == 'Facebook 📘':
    st.subheader('Facebook scraper coming soon! Stay tuned!! 🤗')

elif option1 == 'Instagram 📸':
    st.subheader('Instagram scraper coming soon! Stay tuned!! 🤗')
