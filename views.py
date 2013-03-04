import os
import datetime
import urllib2
import zipfile
import json
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.api import users
from StringIO import StringIO
from xml.dom.minidom import parseString
from models import *

class Index(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        user = users.get_current_user()
        data = { 'user': user }
        if user:
            user_shows = UserShow.gql('WHERE user = :1 ORDER BY order', str(user))
            shows = []
            for user_show in user_shows:
                shows.append({ 'id': user_show.show_id, 'order': user_show.order })
            data['shows'] = shows
        self.response.out.write(template.render(path, data))

class Login(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.redirect('/')
        else:
            self.redirect(users.create_login_url(self.request.uri))

class Logout(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.redirect(users.create_logout_url(self.request.uri))
        else:
            self.redirect('/')

class ShowData(webapp.RequestHandler):
    def get(self, id, name):
        id = int(id)
        name = urllib2.unquote(name.encode('ascii')).decode('utf-8')
        show = Show.gql('WHERE show_id = :1', id).get()
        
        populate_episodes = False
        
        # create the show and populate episodes if it doesn't exist
        if show == None:
            show = Show()
            show.show_id = id
            show.name = name
            show.last_updated = datetime.datetime.now()
            show.put()
            
            populate_episodes = True
        else:
            # if last update date is older than 3 days, update it
            if show.last_updated < datetime.datetime.now() - datetime.timedelta(days = 3):
                populate_episodes = True
                show.last_updated = datetime.datetime.now()
                show.put()
            pass
        
        if populate_episodes:
            xml = get_show_episodes(show.show_id)
            dom = parseString(xml)
            episodes = dom.getElementsByTagName('Episode')
            
            for episode_node in episodes:
                # if the episode exists, update it, otherwise, create it
                episode_id = int(self.read_dom_node_element_text(episode_node, 'id'))
                
                episode = ShowEpisode.gql('WHERE episode_id = :1', episode_id).get()
                
                if episode == None:
                    episode = ShowEpisode()
                    episode.episode_id = episode_id
                
                episode.show_id = show.show_id
                episode.title = self.read_dom_node_element_text(episode_node, 'EpisodeName')
                episode.overview = self.read_dom_node_element_text(episode_node, 'Overview')
                air_date = self.read_dom_node_element_text(episode_node, 'FirstAired')
                if air_date:
                    year, month, day = air_date.split('-')
                    episode.air_date = datetime.date(int(year), int(month), int(day))
                episode.season_number = int(self.read_dom_node_element_text(episode_node, 'SeasonNumber'))
                episode.episode_number = int(self.read_dom_node_element_text(episode_node, 'EpisodeNumber'))
                rating = self.read_dom_node_element_text(episode_node, 'Rating')
                if rating:
                    episode.rating = float(rating)
                
                episode.put()
        
        episodes = ShowEpisode.gql('WHERE show_id = :1 ORDER BY season_number DESC, episode_number DESC', show.show_id)
        
        episodes_for_response = []
        
        today_episode_added = False
        for episode in episodes:
            if episode.season_number > 0:
                if not episode.air_date is None and episode.air_date < datetime.date.today() and not today_episode_added:
                    episodes_for_response.append({
                            'episode_id': -1,
                            'title': 'TODAY',
                            'overview': '',
                            'air_date': '',
                            'season_number': 0,
                            'episode_number': 0,
                            'rating': 0,
                        })
                    today_episode_added = True
                episodes_for_response.append({
                        'episode_id': episode.episode_id,
                        'title': episode.title,
                        'overview': episode.overview,
                        'air_date': str(episode.air_date),
                        'season_number': episode.season_number,
                        'episode_number': episode.episode_number,
                        'rating': episode.rating,
                    })
        
        # add show to the current user if it doesn't exist
        user = users.get_current_user()
        if user:
            user_show = UserShow.gql('WHERE show_id = :1 AND user = :2', id, str(user)).get()
            if user_show == None:
                user_show = UserShow()
                user_show.show_id = id
                user_show.user = str(user)
                user_show.order = UserShow.gql('WHERE user = :1', str(user)).count() + 1
                user_show.put()
        
        self.response.out.write(json.dumps({ 'show_name': show.name, 'episodes': episodes_for_response }))
    
    def read_dom_node_element_text(self, node, element):
        elements = node.getElementsByTagName(element)
        if len(elements) and len(elements[0].childNodes):
            return elements[0].childNodes[0].data
        return None

class RemoveShow(webapp.RequestHandler):
    def get(self, id):
        user = users.get_current_user()
        if user:
            user_show = UserShow.gql('WHERE show_id = :1 AND user = :2', int(id), str(user)).get()
            if user_show:
                user_show.delete()

def get_show_episodes(show_id):
    # download zip file contents
    zip_file_handler = urllib2.urlopen('http://www.thetvdb.com/api/E11BD0139D0A90AE/series/%d/all/en.zip' % (show_id))
    zip_file_contents = zip_file_handler.read()

    # read zip in memory
    zip_data = StringIO()
    zip_data.write(zip_file_contents)
    zip_file = zipfile.ZipFile(zip_data)
    
    # return contents of the en.xml file
    show_data_file = zip_file.open('en.xml')
    return show_data_file.read()


class SaveShowsOrder(webapp.RequestHandler):
    def get(self, shows_and_orders):
        user = users.get_current_user()
        if user:
            shows, orders = shows_and_orders.split('|')
            shows = shows.split(',')
            orders = orders.split(',')
            i = 0
            for show in shows:
                user_show = UserShow.gql('WHERE show_id = :1 AND user = :2', int(show), str(user)).get()
                if user_show:
                    user_show.order = int(orders[i])
                    user_show.put()
                i += 1
