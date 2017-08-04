import httplib2
import os
import webapp2
from apiclient.discovery import build
from google.appengine.ext import webapp
from oauth2client.contrib.appengine import OAuth2DecoratorFromClientSecrets
import json
import logging
import time
from datetime import datetime
from dateutil.parser import parse 
from lib import feedparser
import pprint
from operator import itemgetter
import jinja2
from google.appengine.api import users
import create_feed
from utilities import users_utils
import ast


from utilities import add_channel

decorator = OAuth2DecoratorFromClientSecrets(os.path.join(os.path.dirname(__file__), 'tuberc.json'),  'https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/plus.login')
service = build('youtube', 'v3')

# Set jinja Environment
template_env= jinja2.Environment(loader=jinja2.FileSystemLoader(os.getcwd()))


def get_user_info():
    
    request = service.channels().list(mine=True, part='snippet').execute(decorator.http())
    
    items = request.get('items')
    uid = items[0].get('id')

    snippet = items[0].get('snippet')
    title = snippet.get('title')
    description = snippet.get('description')

    thumbnails = snippet.get('thumbnails')
    high = thumbnails.get('high')
    url = high.get('url')

    self.response.write(uid + '<br>')
    self.response.write(str(title) + '<br>')
    self.response.write(str(description) + '<br>')
    self.response.write('<img src="'+ str(url) + '">')    

def get_sub_list():
    
    more = True
    nextPageToken = False    
    
    subs_channel_id = []
    
    while more: 
                
        if nextPageToken:
            subs = service.subscriptions().list(pageToken = nextPageToken, maxResults=50, part='snippet', mine=True).execute(decorator.http())
        else:
            subs = service.subscriptions().list(maxResults=50, part='snippet', mine=True).execute(decorator.http())
        
        items = subs.get('items')

        for item in items:
            snippet = item.get('snippet')        
            resourceId = snippet.get('resourceId')
            channelId = resourceId.get('channelId') 
            logging.info('channelId - {}'.format(channelId)) 
            subs_channel_id.append(channelId)

        nextPageToken = subs.get('nextPageToken')
    
        if nextPageToken:
            logging.info('Recieved nextPageToken...')
            more = True
        else:
            more = False  
    
    return subs_channel_id

def get_feed(channel_id):
       
    feedurl = 'https://www.youtube.com/feeds/videos.xml?channel_id=' + str(channel_id)
    try:
        d = feedparser.parse(feedurl)
    except Exception as e:
        logging.info('exception caught {}'.format(e))
    

class MainPage(webapp2.RequestHandler):

    @decorator.oauth_aware
    def get(self):

        if decorator.has_credentials():
            
            page = self.request.get('page')
            
            show_back = False
            back_page = None 
            
            if page == '':
                page = 1
            else:
                page = int(page)
                
            start = time.time()

            user = users.get_current_user()
            users_utils.add(user)
            
            tuberuser = users_utils.get_user(user.user_id())
            tuberuser_email = tuberuser.user_email
            tuberuser_sub_channels = tuberuser.sub_channels
            
            if len(tuberuser_sub_channels) > 2:
            
                tuberuser_sub_channels = ast.literal_eval(tuberuser_sub_channels)
            
                feed, number_of_vids = create_feed.post(tuberuser_sub_channels, page)
            
                dump = feed
                
                max_page = page * 20
                
                if max_page <= number_of_vids:
                    show_next = True
                    next_page = str(page + 1)
                else:
                    show_next = False
                    next_page = None
                    
                if page > 1 :
                    show_back = True
                    back_page = str(page - 1)                    
                    
                
            
                template = template_env.get_template('/www/main.html')

                content = {
                    'dump' : dump,
                    'number_of_vids' : number_of_vids, 
                    'tuberuser_email' : tuberuser_email,
                    'show_next' : show_next,
                    'show_back' : show_back,
                    'next_page' : next_page,
                    'back_page' : back_page
                }
            
                self.response.out.write(template.render(content)) 
                
            else:
                
                template = template_env.get_template('/www/no_subs.html')
                self.response.out.write(template.render())
            
            elapsed_time = (time.time() - start)
            logging.info('Elapsed Time - {}'.format(elapsed_time))

        else:
            
            # Get URL
            url = decorator.authorize_url()
            
            # Set the template
            template = template_env.get_template('/www/login.html')
            
            # Setup Content
            content = {
                'url':url
                }
            
            # Render
            self.response.out.write(template.render(content)) 

routes = [('/main', MainPage),  (decorator.callback_path, decorator.callback_handler())]

app = webapp2.WSGIApplication(routes, debug=True)
