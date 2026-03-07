from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from pathlib import Path

import requests
import json
import pandas as pd
import re
import argparse

import requests
from bs4 import BeautifulSoup


    
features = []

# id:
# link:
# Name: 

# profile_image: is there PROFILE image or not? 0/1
# background_exist: is there BACKGROUND image or not? 0/1


# friend_count: number of friends

# ********POSTS
# Intro 
# Image
# Friend_count
# Check 10 random friend if they have mutual friend or not...  (intersection)


# ********INTRODUCTION

# Workplace: 
# Studied_at: 0/1
# Live_at: 0/1
# Home_town:
# Relationship:
# Phone: 

# Job:
# Edu_uni:
# Edu_highschool:

# Email:
# Other_social_media_link: LINK
# Basic_info: 
# Gender:
# Title:
# DoB:

# Family_member:

# Introduce:
# How_to_read_name:
# Other_nickname:
# Favorite_quote:

# Life_event:
# Join_FB: DATE

# ********FRIEND
# Friend count
# Check 10 random friend if they have mutual friend or not...  (intersection)

# ********PICTURE
# Picture_count
# Album

# ********MUSIC
# Music_count
# Artist

# ********BOOK
# Book_count

# ********MOVIE
# Movie_count

# ********TV SHOWs
# TVshow_count

# ********Events
# Events_count

# ********Applications and Games
# Game_count

# ********Reels
# Reel_count
# Count_each_Reel 

# ********Check IN
# Check_in_Place_count


# ********Sports
# Sport_count

# ********Written Comments (Bài đánh giá đã viết)
# Comments_count

# ********POSTS********POSTS********POSTS********POSTS********POSTS********POSTS
# Post_type repost/self-post
# Posts_count
# Post_date 
# Post_react 
# React_count_each_post 
# Comments_count_each_post
# Title_each_post
# See if FRIENDS react that post or who else









