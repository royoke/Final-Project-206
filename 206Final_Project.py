import requests
import json
import sqlite3
import facebook
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import final_project_info
from datetime import datetime
import calendar
import re

plotly.tools.set_credentials_file(username = 'Teddy_Okerstrom', api_key = final_project_info.plotly_api_key)
graph = facebook.GraphAPI(access_token = final_project_info.fb_access_key) # creating connection with facebook Graph API
############################################################################################################################### Setting up cache
CACHE_FNAME = '206_final_project_cache.json'

try:
	cache_file = open(CACHE_FNAME, 'r')
	contents = cache_file.read()
	CACHE_DICTION = json.loads(contents)
	cache_file.close()
except:
	CACHE_DICTION = {}
############################################################################################################################### Creating cache function to get fb posts and likes
def get_facebook_data(user):
	if 'fb_likes' in CACHE_DICTION:
		return CACHE_DICTION['fb_likes']
	else:
		fb_likes = graph.get_all_connections(id = user, connection_name = 'likes')
		CACHE_DICTION['fb_likes'] = [data for data in fb_likes] # must use iteration to receive data from generator objects
		CACHE_DICTION['fb_likes'] = CACHE_DICTION['fb_likes'][:100] # ensured that exactly 100 objects were being retreived
		fb_posts = graph.get_all_connections(id = user, connection_name = 'posts')
		CACHE_DICTION['fb_posts'] = [data for data in fb_posts]
		CACHE_DICTION['fb_posts'] = CACHE_DICTION['fb_posts'][:100]
		cache_file = open(CACHE_FNAME, 'w')
		cache_file.write(json.dumps(CACHE_DICTION))
		cache_file.close()
		return CACHE_DICTION['fb_likes']
get_facebook_data('me') # calling function in order to get my likes into cache
############################################################################################################################### Creating cache function to get my instagram posts and likes
def get_insta_data(user):
	if 'insta_posts' in CACHE_DICTION:
		return CACHE_DICTION['insta_posts']
	else:
		insta_posts = requests.get('https://api.instagram.com/v1/users/{}/media/recent?access_token={}'.format(user, final_project_info.insta_access_token))
		CACHE_DICTION['insta_posts'] = json.loads(insta_posts.text)
		insta_likes = requests.get('https://api.instagram.com/v1/users/{}/media/liked?access_token={}'.format(user, final_project_info.insta_access_token))
		CACHE_DICTION['insta_likes'] = json.loads(insta_likes.text)
		cache_file = open(CACHE_FNAME, 'w')
		cache_file.write(json.dumps(CACHE_DICTION))
		cache_file.close()
		return CACHE_DICTION['insta_posts']
get_insta_data('self')
############################################################################################################################### Getting the dates of my data
def get_day_of_week(timestamp):
	if '-' not in timestamp:
		timestamp = datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d')
		timestamp = datetime.strptime(timestamp, '%Y-%m-%d')
		return calendar.day_name[timestamp.weekday()]
	else:
		num_date = re.findall('[0-9]{4}-[0-9]{2}-[0-9]{2}', timestamp) # takes only the date from the full timestamp
		date_obj = datetime.strptime(num_date[0], '%Y-%m-%d') # converts the string into the actual datetime object
		return calendar.day_name[date_obj.weekday()] # uses calender to return what day of the week that date occured on
############################################################################################################################### Writting data into DB
conn = sqlite3.connect('206Final_ProjectDBs.sqlite')
cur = conn.cursor()

cur.execute('DROP TABLE IF EXISTS FB_Likes')
cur.execute('CREATE TABLE FB_Likes (page_name TEXT, id TEXT, time_liked DATETIME, weekday TEXT)')

for data in CACHE_DICTION['fb_likes']:
	cur.execute('INSERT INTO FB_Likes (page_name, id, time_liked, weekday) VALUES (?,?,?,?)', (data['name'], data['id'], data['created_time'], get_day_of_week(data['created_time'])))

cur.execute('DROP TABLE IF EXISTS FB_Posts')
cur.execute('CREATE TABLE FB_Posts (message_or_story TEXT, id TEXT, time_posted DATETIME, weekday TEXT)')

for data in CACHE_DICTION['fb_posts']:
	if 'message' in data: # must specify whether 'message' or 'story' (your post v sharing someone elses)
		cur.execute('INSERT INTO FB_Posts (message_or_story, id, time_posted, weekday) VALUES (?,?,?,?)', (data['message'], data['id'], data['created_time'], get_day_of_week(data['created_time'])))
	else:
		cur.execute('INSERT INTO FB_Posts (message_or_story, id, time_posted, weekday) VALUES (?,?,?,?)', (data['story'], data['id'], data['created_time'], get_day_of_week(data['created_time'])))

cur.execute('DROP TABLE IF EXISTS Insta_Posts')
cur.execute('CREATE TABLE Insta_Posts (caption_text TEXT, id TEXT, created_time DATETIME, weekday TEXT)')

for data in CACHE_DICTION['insta_posts']['data']:
	cur.execute('INSERT INTO Insta_Posts (caption_text, id, created_time, weekday) VALUES (?,?,?,?)', (data['caption']['text'], data['id'], data['created_time'], get_day_of_week(data['created_time'])))

cur.execute('DROP TABLE IF EXISTS Insta_Likes')
cur.execute('CREATE TABLE Insta_Likes (caption_text TEXT, id TEXT, created_time DATETIME, weekday TEXT)')

for data in CACHE_DICTION['insta_likes']['data']:
	cur.execute('INSERT INTO Insta_Likes (caption_text, id, created_time, weekday) VALUES (?,?,?,?)', (data['caption']['text'], data['id'], data['created_time'], get_day_of_week(data['created_time'])))


conn.commit()
conn.close()
############################################################################################################################### Function to get day of the week for a user
weekdays_list = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

def get_weekday_dict(data):
	weekday_dict = {'Monday': 0, 'Tuesday': 0, 'Wednesday': 0, 'Thursday': 0, 'Friday': 0, 'Saturday': 0, 'Sunday': 0}
	if 'fb' in data:
		for objects in CACHE_DICTION[data]:
			weekday_dict[get_day_of_week(objects['created_time'])] = weekday_dict.get(get_day_of_week(objects['created_time']), 0) + 1
		return weekday_dict
	else:
		for objects in CACHE_DICTION[data]['data']:
			weekday_dict[get_day_of_week(objects['created_time'])] = weekday_dict.get(get_day_of_week(objects['created_time']), 0) + 1
		for key in weekday_dict:
			weekday_dict[key] = weekday_dict[key]*5
		return weekday_dict
############################################################################################################################### Function to make graph using plot.ly
def make_graph(data1, data2):
	data1_info = get_weekday_dict(data1)
	data2_info = get_weekday_dict(data2)
	trace1 = go.Bar(x = weekdays_list, y = [data1_info[day] for day in weekdays_list], name = data1)
	trace2 = go.Bar(x = weekdays_list, y = [data2_info[day] for day in weekdays_list], name = data2)
	data = [trace1, trace2]
	layout = go.Layout(barmode = 'group')
	fig = go.Figure(data=data, layout=layout)
	py.iplot(fig, filename=data1+' graphed against '+data2)
############################################################################################################################### While loop running users through graphing their data
yes_responses = ['yes', 'Yes', 'YES', 'ye', 'y', 'Y']
no_responses = ['no', 'No', 'NO', 'n', 'N']
user_input = input('Hello, would you like to graph your data using plotly today? Please enter yes or no: ')
if user_input in no_responses:
	print('Ok! Have a nice day :)')
if user_input not in yes_responses and user_input not in no_responses:
	print('I will take that as a no...')
if user_input in yes_responses:
	while True:
		input1 = input('Please enter your first piece of data you would like graphed. Options are fb_likes, fb_posts, insta_likes, and insta_posts: ')
		if input1 not in CACHE_DICTION.keys():
			print('that is not a valid piece of data! Please try again')
			continue
		input2 = input('Please enter your second piece of data you would like graphed. Options are fb_likes, fb_posts, insta_likes, and insta_posts: ')
		if input2 not in CACHE_DICTION.keys():
			print('that is not a valid piece of data! Please try again')
			continue
		print('Graphing your data. Check plotly for the graph!')
		make_graph(input1, input2)
		continue_using = input('Would you like to make another graph? Please enter yes or no: ')
		if continue_using in no_responses:
			print('Ok! Have a nice day :)')
			break
		if continue_using not in yes_responses and continue_using not in no_responses:
			print('I will take that as a no...')
			break




