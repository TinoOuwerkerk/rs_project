import streamlit as st
import pandas as pd
import template as t
import random
import csv
import os 

# load the dataset with the shows
df_shows = pd.read_csv('data/df_shows.csv', encoding='latin-1')
df_users = pd.read_csv('data/df_users.csv', encoding='latin-1', index_col=0)
cos_sim_data = pd.read_csv('data/cos_sim_data.csv', encoding='latin-1', index_col=0)
all_users = df_users.index.values
df_watched = pd.read_csv('data/df_watched.csv', encoding='latin-1', index_col=0)
df_recom_content = pd.read_csv('data/content_based_recom.csv', encoding='latin-1', index_col=0)
similarity_df = pd.read_csv('data/similarity_df.csv', index_col=0)

young_users=pd.read_csv('data/young_users.csv', index_col=0)
old_users=pd.read_csv('data/old_users.csv', index_col=0)
fam_users=pd.read_csv('data/fam_users.csv', index_col=0)
fan_users=pd.read_csv('data/fan_users.csv', index_col=0)

# keep most recent episode to recommend
df_shows = df_shows.sort_values(['show', 'aired'], ascending=False).drop_duplicates(['show'])

# if the user is not logged in, show the login form
if 'loggedin' not in st.session_state:
    # create a title    for the login form
    st.title("Login")

    # create input fields for username and password
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    # create a button to submit the login credentials
    if st.button("Login"):
        # check if the username and password are valid
        if username in all_users and password == "mypassword":
            st.session_state['loggedin'] = True
            st.success("Login successful!")
            st.session_state['username'] = username
            st.experimental_rerun()
        else:
            st.error("Invalid username or password.")
else:
    # show the main interface if the user is logged in
    st.set_page_config(layout="wide")
    st.write(f"Welcome, {st.session_state.username}!")

    # select a show to kickstart the interface
    if 'show' not in st.session_state:
      st.session_state['show'] = 'Yes to Running: Bill Harley Live'

    df_show = df_shows[df_shows['show'] == st.session_state['show']]
    # create a cover and info column to display the selected show
    cover, info = st.columns([2, 3])

    with cover:
      # display the image
      st.image(df_show['image'].iloc[0])

    with info:
      # display the show information
      st.title(df_show['title'].iloc[0])
      st.markdown(df_show['description'].iloc[0])
      st.caption(str(df_show['aired'].iloc[0]) + ' | ' + df_show['duration'].iloc[0])

    st.subheader('Recommendations based most watched')
    df = pd.read_csv('data/recommendations-most-watched.csv',sep=',', encoding='latin-1', dtype=object)
    df = df.merge(df_shows, on='show')
    t.recommendations_most_watched(df, st.session_state['username'])

    # Based on watched movies
    data=pd.read_csv('data/content_based.csv', index_col=0)
    # check what shows the user watched
    watched_shows = df_watched.loc[df_watched.user==st.session_state['username']].show.values
    movie_ids = df_shows.loc[df_shows['show'].isin(watched_shows)].index

    # give recommendations based on watched shows
    df_recom_content['show'] = data['show']
    recom_movie = df_recom_content.loc[df_recom_content.index.isin(movie_ids)]
    random_num = random.choice(recom_movie.index)
    recommendations = recom_movie.loc[random_num]
    movie = recom_movie.loc[random_num]['show']
    recommendations = df_shows.loc[df_shows.show.isin(recommendations).values]
    st.subheader('Recommendations because you watched ' + movie)

    
    t.recommendations_most_watched(recommendations, st.session_state['username'])


    st.subheader('Recommendations collaborative filtering user based')
    user = st.session_state['username']
    recommendations = t.recommend_movies_user(user, similarity_df,df_users,young_users,old_users,fam_users, fan_users,n=3)

    # save the recommendations
    with open(os.getcwd() + '/data/recommendations.csv', 'w', newline='') as myfile:
        writer = csv.writer(myfile)
        writer.writerow(['show'])
        for value in recommendations:
            writer.writerow([value])
    
    df = pd.read_csv('data/recommendations.csv', index_col=0)
    df = df.merge(df_shows, on='show')
    t.recommendations_most_watched(df, st.session_state['username'])
    
    # df = pd.read_csv('recommendations/r ecommendations-ratings-weight.csv', sep=',', encoding='latin-1', dtype=object)
    # df = df.merge(df_books, on='ISBN')
    # t.recommendations(df)

    # st.subheader('Recommendations based on Frequently Reviewed Together (frequency)')
    # df = pd.read_csv('recommendations/recommendations-seeded-freq.csv', sep=',', encoding='latin-1', dtype=object)
    # isbn = st.session_state['ISBN']
    # df_recommendations = df[df['book_a'] == isbn].sort_values(by='count', ascending=False)
    # df_recommendations = df_recommendations.rename(columns={"book_b": "ISBN"})
    # df_recommendations = df_recommendations.merge(df_books, on='ISBN')
    # df = df.merge(df_books, on='ISBN')
    # t.recommendations(df)

    # st.subheader('Recommendations based on Frequently Reviewed Together (associations)')
    # df = pd.read_csv('recommendations/recommendations-seeded-associations.csv', sep=',', encoding='latin-1', dtype=object)
    # isbn = st.session_state['ISBN']
    # df_recommendations = df[df['source'] == isbn].sort_values(by='confidence', ascending=False).head(10)
    # df_recommendations = df_recommendations.rename(columns={"target": "ISBN"})
    # df_recommendations = df_recommendations.merge(df_books, on='ISBN')
    # t.recommendations(df_recommendations)