from google.appengine.ext import db

class Show(db.Model):
    show_id = db.IntegerProperty()
    name = db.StringProperty()
    last_updated = db.DateTimeProperty()

class ShowEpisode(db.Model):
    show_id = db.IntegerProperty()
    episode_id = db.IntegerProperty()
    title = db.StringProperty()
    overview = db.TextProperty()
    air_date = db.DateProperty()
    season_number = db.IntegerProperty()
    episode_number = db.IntegerProperty()
    rating = db.FloatProperty()

class UserShow(db.Model):
    show_id = db.IntegerProperty()
    user = db.StringProperty()
    order = db.IntegerProperty()