import streamlit as st
from random import random
import pandas as pd
import os
import csv
from sklearn.metrics import pairwise_distances
from sklearn.neighbors import NearestNeighbors
import numpy as np

def get_similar_users(sim_df, user_id, k):
    knn = NearestNeighbors(metric='cosine')
    knn.fit(sim_df)
    distances, indices = knn.kneighbors(sim_df.loc[[user_id]], n_neighbors=k+1)
    similar_users = sim_df.index[indices.flatten()[1:]]
    return similar_users

def find_sim_users(target_user, sim_df, young_users, old_users, fam_users, fan_users):

  # Retrieve the target persona from the target user's index label
  target_persona = target_user.split('_')[0]
  sim_df = sim_df.copy()
  # Define the personas and their corresponding sets of users
  personas = {'young': young_users.index,
            'old': old_users.index,
            'family': fam_users.index,
            'fan': fan_users.index}

  # Retrieve the set of users from the target user's persona
  try:
    users_from_same_persona = personas[target_persona]
  except KeyError:
    raise ValueError(f"Invalid persona '{target_persona}' in target user '{target_user}'")


  # Set the similarity scores of users in the same persona as the target user to 0.0, to consider them as not similar
  sim_df.loc[target_user, sim_df.index.str.startswith(target_persona)] = 0.0

  # Sort the remaining values in the target user's row in descending order
  similar_users_indices = sim_df.loc[target_user, :].sort_values(ascending=False).index 

  # Exclude the target user's index label from the list of similar users indices
  similar_users_indices = similar_users_indices[similar_users_indices != target_user]

  K=3

  top_K_users = {}
  for user_idx in similar_users_indices:
      if len(top_K_users) == K:
            break
      if user_idx not in users_from_same_persona and user_idx not in top_K_users:
            top_K_users[user_idx] = sim_df.loc[target_user, user_idx]

  return top_K_users

def recommend_movies_user(target_user, similarity_df, user_item_df, young_users, old_users, fam_users, fan_users, n=3):
    # get the n nearest similar users for the input user
    nearest_users = find_sim_users(target_user, similarity_df, young_users, old_users, fam_users, fan_users)
    sim_users = list(nearest_users.keys())[:n]
    
    # create a list of sets of the movies watched by each similar user
    user_movies = [set(user_item_df.loc[(user, slice(None))].loc[user_item_df.loc[(user, slice(None))] == 1].index) for user in sim_users]

    # find the movies watched by any of the similar users
    sim_movies = set.union(*user_movies)
    
    # remove the movies already watched by the input user
    watched_movies = set(user_item_df.loc[target_user].loc[user_item_df.loc[target_user] == 1].index)
    sim_movies = sim_movies - watched_movies
    
    # sort the movies by the number of similar users who watched them and return the top 10
    sorted_sim_movies = sorted([(movie, sum([movie in user_movies[i] for i in range(len(user_movies))])) for movie in sim_movies], key=lambda x: x[1], reverse=True)
    recommended_movies = [movie[0] for movie in sorted_sim_movies[:10] if movie[0] not in watched_movies]

    return recommended_movies

def update_recommendations(show, user):
  # read users csv
  df_users = pd.read_csv(os.getcwd() + "/data/df_users.csv", index_col = 0)

  # put a 1 in the watched show that the user clicked in
  df_users.loc[user, show] = 1
  data = np.array(df_users)

  # recalculate similarities
  jaccard_sim = 1 - pairwise_distances(data, metric='jaccard')
  similarity_df = pd.DataFrame(jaccard_sim, index=df_users.index, columns=df_users.index)

  # here were duplicate rows and columns
  similarity_df = similarity_df.drop_duplicates()
  similarity_df = similarity_df.loc[:,~similarity_df.columns.duplicated()]
  df_users.drop_duplicates(inplace= True)

  # separate personsas dataframes
  young_users = similarity_df.loc[similarity_df.index.str.startswith('young_user')]
  old_users = similarity_df.loc[similarity_df.index.str.startswith('old_user')]
  fam_users = similarity_df.loc[similarity_df.index.str.startswith('family_user')]
  fan_users = similarity_df.loc[similarity_df.index.str.startswith('fan_user')]

  recommended_shows = recommend_movies_user(user, similarity_df, df_users, young_users, old_users, fam_users, fan_users, n=3)

  df_users.to_csv(os.getcwd() + '/data/df_users.csv', index=True)

  # save the recommendations
  with open(os.getcwd() + '/data/recommendations.csv', 'w', newline='') as myfile:
    writer = csv.writer(myfile)
    writer.writerow(['show'])
    for value in recommended_shows:
        writer.writerow([value])

def update_recommendations_most_watched(show, username):
  df_watched = pd.read_csv(os.getcwd() + "/data/df_watched.csv", index_col=0)
  df_watched.loc[username] = show
  df_watched.to_csv(os.getcwd() + "/data/df_watched.csv",index=True)
  top_10 = df_watched['show'].value_counts().head(10).reset_index().rename(columns={'index':'show', 'show':'count'})
  top_10.to_csv(os.getcwd() + '/data/recommendations-most-watched.csv', index=False)

# set episode session state
def select_book(show, username):
  st.session_state['show'] = show

  # create the new recommendations
  update_recommendations_most_watched(show, username)
  update_recommendations(show, username)

def tile_item(column, item, username):
  with column:
    st.button('🎥', key=random(), on_click=select_book, args=(item['show'], username))
    st.image(item['image'], use_column_width='always')
    st.caption(item['show'])

def recommendations_most_watched(df, username):

  # check the number of items
  nbr_items = df.shape[0]

  if nbr_items != 0:

    # create columns with the corresponding number of items
    columns = st.columns(nbr_items)

    # convert df rows to dict lists
    items = df.to_dict(orient='records')

    # apply tile_item to each column-item tuple (created with python 'zip')
    any(tile_item(x[0], x[1], username) for x in zip(columns, items))
  