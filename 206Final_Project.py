import os
import aiml
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

kernel = aiml.Kernel()
for directory in os.listdir('aiml_data'):
	kernel.learn('aiml_data/'+ directory)

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
		print('pulling Facebook data from cache...')
		return CACHE_DICTION['fb_likes']
	else:
		print('fetching Facebook data...')
		fb_likes = graph.get_all_connections(id = user, connection_name = 'likes')
		CACHE_DICTION['fb_likes'] = [data for data in fb_likes] # must use iteration to receive data from generator objects
		CACHE_DICTION['fb_likes'] = CACHE_DICTION['fb_likes'][:100] # ensured that exactly 100 objects were being retreived
		fb_posts = graph.get_all_connections(id = user, connection_name = 'posts')
		CACHE_DICTION['fb_posts'] = [data for data in fb_posts]
		CACHE_DICTION['fb_posts'] = CACHE_DICTION['fb_posts'][:100]
		fb_user_info = graph.get_connections(id = user, connection_name = 'friends')
		CACHE_DICTION['fb_user_info'] = fb_user_info
		cache_file = open(CACHE_FNAME, 'w')
		cache_file.write(json.dumps(CACHE_DICTION))
		cache_file.close()
		return CACHE_DICTION['fb_likes']
get_facebook_data('me') # calling function in order to get my likes into cache
############################################################################################################################### Creating cache function to get my instagram posts and likes
def get_insta_data(user):
	if 'insta_posts' in CACHE_DICTION:
		print('pulling Instagram data from cache...')
		return CACHE_DICTION['insta_posts']
	else:
		print('fetching Instagram data...')
		insta_posts = requests.get('https://api.instagram.com/v1/users/{}/media/recent?access_token={}'.format(user, final_project_info.insta_access_token))
		CACHE_DICTION['insta_posts'] = json.loads(insta_posts.text)
		insta_likes = requests.get('https://api.instagram.com/v1/users/{}/media/liked?access_token={}'.format(user, final_project_info.insta_access_token))
		CACHE_DICTION['insta_likes'] = json.loads(insta_likes.text)
		insta_user_info = requests.get('https://api.instagram.com/v1/users/{}/?access_token={}'.format(user, final_project_info.insta_access_token))
		CACHE_DICTION['insta_user_info'] = json.loads(insta_user_info.text)
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
	weekday_dict = {'Monday': 0, 'Tuesday': 0, 'Wednesday': 0, 'Thursday': 0, 'Friday': 0, 'Saturday': 0, 'Sunday': 0} # ensure there will be no error if no posts/likes that day
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
def make_graph(graph_type, platform1, datatype1, platform2='', datatype2=''):
	fb_colors = ['rgba(52,102,150,1)','rgba(52,102,150,1)','rgba(52,102,150,1)','rgba(52,102,150,1)','rgba(52,102,150,1)','rgba(52,102,150,1)','rgba(52,102,150,1)'] # colors for any facebook data in plotly
	insta_colors = ['rgba(180,67,71,1)','rgba(180,67,71,1)','rgba(180,67,71,1)','rgba(180,67,71,1)','rgba(180,67,71,1)','rgba(180,67,71,1)','rgba(180,67,71,1)'] # colors for any instagram data in plotly
	weekday_colors = ['#a63030', '#30a4a6', '#a66b30', '#3e30a6', '#3ea630','#3090a6', '#d6cf00' ]
	try: 
		if platform1 == 'Facebook' or platform1 == 'facebook' or platform1 == 'fb': # taking user input and turning it into dictionary keys
			if datatype1 == 'likes':
				data1 = 'fb_likes'
			if datatype1 == 'posts':
				data1 = 'fb_posts'
		if platform1 == 'Instagram' or platform1 == 'instagram' or platform1 == 'insta':
			if datatype1 == 'likes':
				data1 = 'insta_likes'
			if datatype1 == 'posts':
				data1 = 'insta_posts'
		if platform2 == 'Facebook' or platform2 == 'facebook' or platform2 == 'fb':
			if datatype2 == 'likes':
				data2 = 'fb_likes'
			if datatype2 == 'posts':
				data2 = 'fb_posts'
		if platform2 == 'Instagram' or platform2 == 'instagram' or platform2 == 'insta':
			if datatype2 == 'likes':
				data2 = 'insta_likes'
			if datatype2 == 'posts':
				data2 = 'insta_posts'
		data1_info = get_weekday_dict(data1)
		if datatype2 != '':
			data2_info = get_weekday_dict(data2)

		if graph_type == 'bar chart' or graph_type == 'bar graph': # making a bar graph out of data 
			if 'fb' in data1:
				trace1 = go.Bar(x = weekdays_list, y = [data1_info[day] for day in weekdays_list], name = data1, marker=dict(color=fb_colors))
			else:
				trace1 = go.Bar(x = weekdays_list, y = [data1_info[day] for day in weekdays_list], name = data1, marker=dict(color=insta_colors))
			if 'fb' in data2:
				trace2 = go.Bar(x = weekdays_list, y = [data2_info[day] for day in weekdays_list], name = data2, marker=dict(color=fb_colors))
			else:
				trace2 = go.Bar(x = weekdays_list, y = [data2_info[day] for day in weekdays_list], name = data2, marker=dict(color=insta_colors))
			data = [trace1, trace2]
			layout = go.Layout(barmode = 'group')
			fig = go.Figure(data=data, layout=layout)
			py.iplot(fig, filename=data1+' graphed against '+data2)
			return 'All done! Check plotly for your graph'

		if graph_type == 'pie chart'or graph_type == 'pie graph': # making a pie chart out of data
			labels = weekdays_list
			values = [data1_info[day] for day in weekdays_list]
			colors = weekday_colors
			trace = go.Pie(labels=labels, values=values, hoverinfo='label+percent', textinfo='value', textfont=dict(size=20),marker=dict(colors=colors, line=dict(color='#000000', width=2)))
			py.iplot([trace], filename=data1+'pie chart')
			return 'All done! Check plotly for your graph'

		if graph_type == 'line plot' or graph_type == 'scatter plot':
			if 'fb' in data1:
				trace1 = go.Scatter(x = weekdays_list, y=[data1_info[day] for day in weekdays_list], name=data1, line=dict(color=('rgba(52,102,150,1)'),width=4))
			else:
				trace1 = go.Scatter(x = weekdays_list, y=[data1_info[day] for day in weekdays_list], name=data1, line=dict(color=('rgba(180,67,71,1)'),width=4))
			if 'fb' in data2:
				trace2 = go.Scatter(x = weekdays_list, y=[data2_info[day] for day in weekdays_list], name=data2, line=dict(color=('rgba(52,102,150,1)'),width=4))
			else:
				trace2 = go.Scatter(x = weekdays_list, y=[data2_info[day] for day in weekdays_list], name=data2, line=dict(color=('rgba(180,67,71,1)'),width=4))
			data = [trace1,trace2]
			layout = dict(title = data1+' and '+data2+' line plot', xaxis = dict(title='Day of the week'), yaxis = dict(title='Frequency of usage'))
			fig = dict(data=data, layout=layout)
			py.iplot(fig, filename=data1+' and '+data2+' line plot')
			return 'All done! Check plotly for your graph'
	except:
		return 'Please make sure you are using the correct syntax and then try again'
kernel.addPattern('Make a {graph_type} of my {platform1} {datatype1} and my {platform2} {datatype2}', make_graph)
kernel.addPattern('Make a {graph_type} of my {platform1} {datatype1}', make_graph)
############################################################################################################################### Function to receive basic social media info
def get_basic_info(data, platform):
	try:
		if data == 'friends' and platform == 'facebook' or platform == 'Facebook' or platform == 'fb':
			return 'You have {} friends on Facebook'.format(str(CACHE_DICTION['fb_user_info']['summary']['total_count']))

		if platform == 'instagram' or platform == 'Instagram' or platform == 'insta':
			if data == 'followers':
				return 'You have {} followers on Instagram'.format(str(CACHE_DICTION['insta_user_info']['data']['counts']['followed_by']))
			if data == 'posts':
				return 'You have {} posts on Instagram'.format(str(CACHE_DICTION['insta_user_info']['data']['counts']['media']))
			if data == 'follows':
				return 'You follow {} people on Instagram'.format(str(CACHE_DICTION['insta_user_info']['data']['counts']['follows']))
	except:
		return 'Im sorry, I do not have access to that information or there is a typo'

kernel.addPattern('How many {data} do I have on {platform}', get_basic_info)
############################################################################################################################### While loop to run chatbot
print('Hello and welcome to the SI206 social media chatbot! Ask me questions about your accounts, tell me to make you graphs, or just chat! Type exit to leave and see report if you have any questions.')
user_query = ''
while user_query != 'exit':
	user_query = input('> ')
	print(kernel.respond(user_query))




