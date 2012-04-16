from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from views import *

application = webapp.WSGIApplication([
        (r'^/$', Index),
        (r'^/login$', Login),
        (r'^/logout$', Logout),
        (r'^/show_data/(\d+)/(.*)', ShowData),
        (r'^/remove_show/(\d+)', RemoveShow),
        (r'^/save_shows_orders/(.*)', SaveShowsOrder),
    ])

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
