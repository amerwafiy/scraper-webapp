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
def clean_tweet(tweet):
    tweet = repr(tweet)
    tweet = tweet.replace("\\n" , " ")
    tweet = tweet.replace("  " , " ")
    tweet = tweet.replace("amp;" , " ")
    mention = re.compile(r'@([a-zA-Z0-9_]+)').findall(tweet)
    link  = re.compile(r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})').findall(tweet)
    return tweet, mention, link

@st.cache
def convert_df(df):
    return df.to_csv().encode('utf-8')

@st.cache(show_spinner = False)
def scrape_tweets(search_term, max_tweets):
    user_tweets = []
    for i,data in enumerate(sntwitter.TwitterSearchScraper(search_term).get_items()):
        if i == int(max_tweets):
            break
        date = pd.to_datetime(str(data.date)[:19]) + timedelta(hours=8)
        time = str(date)[11:]
        username = '@' + data.username
        tweet, mention, link = clean_tweet(data.content)
        if len(mention) > 0:
            mention = ['@' + x for x in mention]
        url = data.url
        user_tweets.append([date, time , username, tweet, mention, link, url])
    return user_tweets


image = Image.open('invoke_logo.jpg')

st.sidebar.title('Social Media Scraper')
st.sidebar.image(image)
option1 = st.sidebar.selectbox('Select a platform', ('Twitter 🐦', 'Facebook 📘', 'Instagram 📸'))

if option1 == 'Twitter 🐦':
    twitter = Image.open('twitter-logo.png')
    st.image(twitter)
    option = st.sidebar.selectbox('Choose a scraping option',
        ('Scrape on user 👨‍👩‍👧‍👦', 'Scrape on keyword/hashtag 💬'))

    if option == 'Scrape on user 👨‍👩‍👧‍👦':
        users= st.text_input('Enter username(Separate multiple users by "," e.g. rafiziramli,najibrazak)', '')
        from_date = st.date_input("From", value = dt.date.today() - dt.timedelta(days=1), max_value = dt.date.today() - dt.timedelta(days=1))
        end_date = str(st.date_input("Until", max_value = dt.date.today(), min_value = from_date + dt.timedelta(days=1)))
        max_results = st.text_input('Set maximum number of tweets to scrape per profile', '')
        if st.button('Scrape Tweet!'):
            try:
                max_results = int(max_results)
                tweets_list = []
                users = users.split(',')

                # Using TwitterSearchScraper to scrape data and append tweets to list
                with st.spinner('Scraping tweets...'):
                    for user in users:
                        user = user.strip()
                        search_term = 'from:' + user + ' since:' + str(from_date) + ' until:' + str(end_date)
                        user_tweets = scrape_tweets(search_term, max_results)
                        if len(user_tweets) > 0:
                            if len(user_tweets) < int(max_results):
                                st.write('WARNING: @' + user + ' only made ' + str(len(user_tweets)) + ' tweet(s) during the specified date')
                            user_tweets = pd.DataFrame(user_tweets, columns=['Date', 'Time', 'Username', 'Tweet', 'Mention', 'Link', 'Tweet URL'])
                            user_tweets['Date'] = user_tweets["Date"].dt.strftime("%d/%m/%Y")
                            tweets_list.append(user_tweets)
                        else:
                            st.write('WARNING: No tweet found by @' + user + ' during the specified date')
                
                if len(tweets_list) == 0:
                    pass
                else:
                    show_tweets = []
                    if len(tweets_list) == 1:
                        tweets_df = tweets_list[0]
                        tweets_df.index += 1
                        show_tweets = tweets_df
                        st.subheader('Sample Data')
                        st.table(show_tweets[['Date', 'Username', 'Tweet']].head())
                    else:
                        tweets_df = pd.concat(tweets_list).reset_index(drop = True)
                        tweets_df.index += 1
                        for i in range(len(tweets_list)):
                            curr_df = tweets_list[i]
                            show_tweets.append(curr_df[['Date', 'Username', 'Tweet']].head(3))
                        show_tweets = pd.concat(show_tweets).reset_index(drop = True)
                        show_tweets.index += 1
                        st.table(show_tweets)
                    csv = convert_df(tweets_df)
                    st.download_button(label="📥 Download data as CSV", data=csv,file_name='tweets_df.csv', mime='text/csv')
            
            except ValueError:
                st.write('Please input an integer value for maximum number of tweets to scrape!')


    elif option == 'Scrape on keyword/hashtag 💬':
        search= st.text_input('Enter keyword/hashtag (Please separate multiple keywords/hashtags by "," e.g. Bitcoin,#Ethereum)', '')
        from_date = st.date_input("From", value = dt.date.today() - dt.timedelta(days=1), max_value = dt.date.today() - dt.timedelta(days=1))
        end_date = str(st.date_input("Until", max_value = dt.date.today(), min_value = from_date + dt.timedelta(days=1)))
        max_results = st.text_input('Set maximum number of tweets to scrape per keyword/hashtag', '')
        if st.button('Scrape Tweet!'):
            try:
                max_results = int(max_results)
                tweets_list = []
                search = search.split(',')

                with st.spinner('Scraping tweets...'):
                    for s in search:
                        s = s.strip()
                        search_term = s + ' since:' + str(from_date) + ' until:' + str(end_date)
                        search_tweets = scrape_tweets(search_term, max_results)
                        if len(search_tweets) > 0:
                            if len(search_tweets) < int(max_results):
                                st.write('WARNING: Only ' + str(len(search_tweets)) + ' tweet(s) were made on "' + str(s) + '" during the specified date')
                            search_tweets = pd.DataFrame(search_tweets, columns=['Date', 'Time', 'Username', 'Tweet', 'Mention', 'Link', 'Tweet URL'])
                            search_tweets['Date'] = search_tweets["Date"].dt.strftime("%d/%m/%Y")
                            search_tweets['Keyword'] = s
                            tweets_list.append(search_tweets)
                        else:
                            st.write('WARNING: No tweet found by on "' + str(s) + '" during the specified date')


                if len(tweets_list) == 0:
                    pass
                else:
                    show_tweets = []
                    if len(tweets_list) == 1:
                        tweets_df = tweets_list[0]
                        tweets_df.index += 1
                        show_tweets = tweets_df
                        st.subheader('Sample Data')
                        st.table(show_tweets[['Date', 'Username', 'Tweet','Keyword']].head())
                    else:
                        tweets_df = pd.concat(tweets_list).reset_index(drop = True)
                        tweets_df.index += 1
                        for i in range(len(tweets_list)):
                            curr_df = tweets_list[i]
                            show_tweets.append(curr_df[['Date', 'Username', 'Tweet','Keyword']].head(3))
                        show_tweets = pd.concat(show_tweets).reset_index(drop = True)
                        show_tweets.index += 1
                        st.table(show_tweets)
                    csv = convert_df(tweets_df)
                    st.download_button(label="📥 Download data as CSV", data=csv,file_name='tweets_df.csv', mime='text/csv')
        
            except ValueError:
                st.write('Please input an integer value for maximum number of tweets to scrape!')


elif option1 == 'Facebook 📘':
    st.subheader('Facebook scraper coming soon! Stay tuned!! 🤗')

elif option1 == 'Instagram 📸':
    st.subheader('Instagram scraper coming soon! Stay tuned!! 🤗')
