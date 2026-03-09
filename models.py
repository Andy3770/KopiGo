from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# Cafes, food outlets, and businesses
class Eateries(db.Model):
    __tablename__ = 'eateries'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    category = db.Column(db.Text)
    price_range = db.Column(db.String(10))
    postal_code = db.Column(db.String(20))
    hygiene_rating = db.Column(db.String(5))
    outdoor_seating = db.Column(db.String(10))
    family_friendly = db.Column(db.String(10))
    self_service = db.Column(db.String(10))

# Tourist attractions
class Attraction(db.Model):
    __tablename__ = 'attractions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    overview = db.Column(db.Text)
    postal_code = db.Column(db.String(20))

# Hawker Centres

class HawkerCentres(db.Model):
    __tablename__ = 'hawkers'
    id = db.Column(db.Integer, primary_key=True)
    name_of_centre = db.Column(db.String(255), nullable=False)
    location_of_centre = db.Column(db.String(255))
    type_of_centre = db.Column(db.String(255))
    owner = db.Column(db.String(20))
    no_of_stalls = db.Column(db.Integer)
    no_of_cooked_food_stalls = db.Column(db.Integer)
    no_of_mkt_produce_stalls = db.Column(db.Integer)
    postal_code = db.Column(db.String(20), nullable=False)