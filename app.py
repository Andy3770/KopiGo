import random
from flask import Flask, render_template, request, jsonify,abort ,flash,get_flashed_messages
from flask import redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from init_data import db,load_initial_data
import pandas as pd
import numpy as np
import boto3
import uuid
from PIL import Image
import io
from pymongo import MongoClient
from services import find_eateries, create_located_in_trigger, get_counts_by_region_fulljoin, get_eateries_columns, get_top_rated_eateries_by_region, hygiene_ratings, region, name_uniqueness_trigger, count_eateries, get_nearest_eateries,get_count_sector
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from sqlalchemy.exc import DatabaseError
from bson import ObjectId
import math
from flask_sqlalchemy import SQLAlchemy
import os
import requests
import time

app = Flask(__name__)
bcrypt = Bcrypt(app)
password = os.environ.get('MYSQL_PASS')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{password}@localhost/KopiGo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key ='7b1cfea1e51f38f4fdbf490c3a2b3f3e77594d04d179e8c67187ecf6d79a9373'  # CHANGE TO LOAD FROM.ENV file

# AWS S3 Bucket
# Connect to S3 with harcoded credentials
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# MongoDB Atlas NoSQL Connection
client = MongoClient()
mongodb = client["KopiGo"]
mongo_reviews = mongodb["User_Reviews"]
mongo_users = mongodb["Users"]
mongo_tips = mongodb["CulturalTips"]
mongo_loginLogs = mongodb["LoginLogs"]
mongo_postalLogs = mongodb["PostalCodeSearchLogs"]

db.init_app(app)  # 🔴 REQUIRED — registers the app with the db
@app.route("/") # Home page 
def home():
    isAuth = False
    if session.get('users') != None:
        isAuth = True
        user = session.get('users')
        userid = session.get('user_id')
        usertype = session.get('user_type')
    session.clear()  # removes all session data
    if isAuth == True:
        session['users'] = user
        session['user_id'] = userid
        session['user_type'] = usertype
    
    top_rated_eateries = get_top_rated_eateries_by_region(limit=3)

    return render_template("index.html", top_rated_eateries=top_rated_eateries)

@app.route("/eateries/<int:attraction_id>")
def show_nearby(attraction_id):
    user = session.get('users')  # Check if user is logged in
    if not user:
        return redirect(url_for('login'))  # 🚫 Not logged in

    # Fetch attraction details
    sql_attr = text("SELECT * FROM attractions WHERE id = :id")
    row = db.session.execute(sql_attr, {"id": attraction_id}).mappings().fetchone()
    if not row:
        abort(404)
    attraction = dict(row)

    # Get filter selections from query params
    field_list = request.args.getlist('filter_field[]')
    value_list = request.args.getlist('filter_value[]')

    # Columns allowed for filtering
    all_cols = get_eateries_columns()
    filter_fields = [c for c in all_cols if c not in ("id", "address", "latitude", "longitude","postal_code")]
    filter_fields.append("category") 

    # Build filter dictionary
    filters = {}
    for f, v in zip(field_list, value_list):
        if f and v and f in filter_fields:
            filters[f] = v
            
    sort_by = request.args.get("sort_by", default=None)

    # Find matching eateries near the attraction
    eateries = find_eateries(attraction['postal_code'], **filters)
    total_eateries = count_eateries(attraction['postal_code'], **filters)
    
    eatery_ids = [e["id"] for e in eateries]

    # MongoDB: Group reviews by eatery_id and calculate stats
    pipeline = [
        { "$match": { "eatery_id": { "$in": eatery_ids } } },
        { "$group": {
            "_id": "$eatery_id",
            "avg_rating": { "$avg": "$rating" },
            "review_count": { "$sum": 1 }
        }}
    ]

    review_stats = list(mongo_reviews.aggregate(pipeline))

    # Create a lookup map: { eatery_id: { avg_rating, review_count } }
    rating_map = {
        str(item["_id"]): {
            "avg_rating": round(item.get("avg_rating", 0), 1),
            "review_count": item.get("review_count", 0)
        }
        for item in review_stats
    }

    # Convert to dict and assign avg_rating
    eateriesr = []
    for row in eateries:
        e = dict(row)
        r = rating_map.get(str(e["id"]), {"avg_rating": 0, "review_count": 0})
        e["avg_rating"] = r["avg_rating"]
        e["review_count"] = r["review_count"]
        eateriesr.append(e)
    
    # Sort by selected option
    if sort_by == "ratings":
        eateriesr.sort(key=lambda x: x["avg_rating"], reverse=True)
    elif sort_by == "most_reviewed":
        eateriesr.sort(key=lambda x: x["review_count"], reverse=True)
        
    # calculate how many pages needed for eateries
    page = request.args.get("page", 1, type=int)
    per_page = 10
    total        = len(eateriesr)
    total_pages  = math.ceil(total / per_page)
    start        = (page - 1) * per_page
    end          = start + per_page
    page_eats = eateriesr[start:end]

    return render_template(
        "eateries.html",
        eateriesr = page_eats,
        total_eateries=total_eateries,
        page=page,
        total_pages=total_pages,
        attraction=attraction,
        filter_fields=filter_fields,
        selected_fields=field_list,
        selected_values=value_list,
        zip=zip,
        sort_by=sort_by
    )

@app.route("/dashboard/<int:attraction_id>", methods=['POST'])
def add_itinerary(attraction_id):
    userid = session.get('user_id')
    
    if not userid:
        return redirect(url_for('login'))

    result = mongo_users.update_one(
        {"user_id": userid},
        {"$addToSet": {"itineraries": attraction_id}}  # prevents duplicates
    )

    if result.modified_count:
        flash("Added to your itinerary!", "success")
    else:
        flash("Already in your itinerary.","info")

    return redirect(request.referrer or url_for('dashboard'))


# Reviews
@app.route('/review/<int:attraction_id>/<int:eatery_id>')
def review_eaterie(attraction_id,eatery_id):
    user = session.get('users')  # check if user is logged in
    if not user:
        return redirect(url_for('login'))  # 🚫 not logged in
    user_id = session.get('user_id')
    sql = text("SELECT * FROM eateries WHERE id = :id")
    row = db.session.execute(sql, {"id": eatery_id}).mappings().fetchone()
    eatery = dict(row)

    reviews = list(mongo_reviews.find({"eatery_id": eatery_id}))
    pipeline = [
        { "$match": { "eatery_id": eatery_id } },
        {
            "$group": {
                "_id": "$eatery_id",
                "average_rating": { "$avg": "$rating" },
                "total_reviews": { "$sum": 1 }
            }
        }
    ]
    result = list(mongo_reviews.aggregate(pipeline))
    if result:
        avg_rating = round(result[0]['average_rating'], 2)
        review_count = result[0]['total_reviews']
    else:
        avg_rating = None
        review_count = 0

    for review in reviews:
        review['liked_by_user'] = user_id in review.get('likes', [])

    return render_template("review.html",attraction_id=attraction_id,eatery=eatery,reviews=reviews,avg_rating=avg_rating,review_count=review_count)
       
@app.route('/review/<int:attraction_id>/<int:eatery_id>', methods=['POST'])
def upload_image(attraction_id, eatery_id):
    rating = int(request.form['rating'])
    review = request.form['review']
    userid = session.get('user_id')
    name = session.get('users')
    
    image_file = request.files.get('image')
    
    if not image_file or image_file.filename == '':
        # Case: No image uploaded
        image_url = 'nil'
    else:
        # Case: Image is uploaded
        extension = image_file.filename.rsplit('.', 1)[-1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{extension}"

        # 🗜️ Compress/resize image
        img = Image.open(image_file)
        img.thumbnail((800, 800))
        buffer = io.BytesIO()
        img.save(buffer, format=img.format, optimize=True, quality=75)
        buffer.seek(0)

        # Upload to S3
        s3.upload_fileobj(
            buffer,
            S3_BUCKET,
            unique_filename,
            ExtraArgs={'ContentType': image_file.content_type}
        )

        image_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"

    # MongoDB document
    review_data = {
        "eatery_id": eatery_id,
        "user_id": userid,
        "rating": rating,
        "comment": review,
        "image_url": image_url,
        "user_name": name,
        "created_at": datetime.now()
    }

    mongo_reviews.insert_one(review_data)
    flash("✅ Review uploaded successfully! Thank you for your feedback!", "success")
    return redirect(url_for('review_eaterie', attraction_id=attraction_id, eatery_id=eatery_id))

# For testing purposes
@app.route('/upload', methods=['GET'])
def upload_form():
    return render_template('upload.html')
    
# Used once to load initial data
# @app.route('/import-tips')
# def import_tips():
#     df = pd.read_csv('dataset/cultural_tips.csv')  # or full path if needed
#     tips = df.to_dict(orient='records')
#     mongo_tips.insert_many(tips)
#     return f"✅ Inserted {len(tips)} cultural tips into MongoDB!"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = mongo_users.find_one({"email": email})
        
        if user and bcrypt.check_password_hash(user['password'], password):
            session['users'] = user['name']
            session['user_id'] = user['user_id']

            mongo_loginLogs.insert_one({
                "user_id": session['user_id'],
                "username": session['users'],
                "email": email,
                "status": "Success",
                "timestamp": datetime.utcnow()
            })

            if 'user_type' in user and user['user_type'] == 'admin':
                session['user_type'] = 'admin'
                return redirect(url_for('admin_dashboard'))
            else:
                session['user_type'] = 'user'
                return redirect(url_for('dashboard'))
        mongo_loginLogs.insert_one({
                "email": email,
                "status": "Failure",
                "timestamp": datetime.utcnow()
            })
        return render_template("login.html", error="Invalid Login credentials")

    postal_code = request.args.get('postalCode')
    if postal_code:
        mongo_postalLogs.insert_one({
                "user_id": session['user_id'],
                "postalCode": postal_code,
                "timestamp": datetime.utcnow()
            })
        session['postal'] = postal_code
    
    return render_template('login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    user_type = session.get('user_type')  # check if user is admin
    user = session.get('users')
    if user_type != 'admin':
        return redirect(url_for('login'))  # 🚫 not logged in
    sql = text("SELECT * FROM attractions ")
    rows = db.session.execute(sql).mappings().all()
    total_tourist_attraction = [dict(r) for r in rows]
    return render_template('admin_dashboard.html', user=user,attractions = total_tourist_attraction)

@app.route('/region_count')
def count_region():
    user_type = session.get('user_type')  # check if user is admin
    user = session.get('users')
    if user_type != 'admin':
        return redirect(url_for('login'))  # 🚫 not logged in
    summary = get_count_sector()
    print(summary)
    return render_template('count_region.html', user=user,summary = summary)

@app.route('/eateries_hawkers_count')
def count_eateries_hawkers():
    user_type = session.get('user_type')
    user = session.get('users')
    if user_type != 'admin':
        return redirect(url_for('login'))
    summary = get_counts_by_region_fulljoin()  # returns mappings of region, eatery_count, hawker_count :contentReference[oaicite:0]{index=0}
    return render_template(
        'count_eateries_hawkers.html',
        user=user,
        summary=summary
    )

@app.route('/create_attraction', methods=['GET', 'POST'])

@app.route('/create_attraction', methods=['GET', 'POST'])
def create_attraction():
    if session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        overview = request.form['overview']
        postal_code = request.form['postal_code']
        latitude = request.form['latitude']
        longitude = request.form['longitude']

        try:
            sql = text("""
                INSERT INTO attractions (name, address, overview, postal_code, latitude, longitude)
                VALUES (:name, :address, :overview, :postal_code, :latitude, :longitude)
            """)
            db.session.execute(sql, {
                "name": name, "address": address, "overview": overview,
                "postal_code": postal_code, "latitude": latitude,
                "longitude": longitude
            })
            db.session.commit()
            flash("Attraction created successfully!", "success")
            return redirect(url_for('admin_dashboard'))

        except SQLAlchemyError as e:
            db.session.rollback()

            # Optional: log full error string
            err_str = str(e.__cause__ or e)

            if "already exists" in err_str:
                flash("An attraction with that name already exists.", "danger")
            else:
                flash("An error occurred while creating the attraction.", "danger")

            return render_template('create_attraction.html')

    return render_template('create_attraction.html')

@app.route('/update_attraction/<int:attraction_id>', methods=['GET', 'POST'])
def update_attraction(attraction_id):
    if  session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        overview = request.form['overview']
        postal_code = request.form['postal_code']
        latitude = request.form['latitude']
        longitude = request.form['longitude']

        sql = text("""
            UPDATE attractions
            SET name = :name, address = :address, overview = :overview,
                postal_code = :postal_code, latitude = :latitude, longitude = :longitude
            WHERE id = :id
        """)
        db.session.execute(sql, {
            "name": name, "address": address, "overview": overview,
            "postal_code": postal_code, "latitude": latitude,
            "longitude": longitude, "id": attraction_id
        })
        db.session.commit()
        flash("Attraction updated successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    attraction = db.session.execute(
        text("SELECT * FROM attractions WHERE id = :id"), {"id": attraction_id}
    ).mappings().fetchone()
    return render_template("update_attraction.html", attraction=attraction)

@app.route('/delete_attraction/<int:attraction_id>')
def delete_attraction(attraction_id):

    db.session.execute(text("DELETE FROM attractions WHERE id = :id"), {"id": attraction_id})
    db.session.commit()
    flash("Attraction deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        #NoSQL Sign up
        user_id = str(uuid.uuid4())
        name = request.form['name']
        email = request.form['email']
        password = request.form['password'] #hash the password
        hashed_pwd = bcrypt.generate_password_hash(password)

        if mongo_users.find_one({"email": email}):
            return render_template("signup.html", error="User already exists")
        
        mongo_users.insert_one({"user_id": user_id,"email": email, "password": hashed_pwd, "name": name})
        return redirect(url_for('login'))
    
    return render_template("signup.html")

 
@app.route('/dashboard')
def dashboard():
    user = session.get('users')  # check if user is logged in
    postal = session.get('postal')

    if request.args.get('postalCode'):
        postal = request.args.get('postalCode')
        session['postal'] = postal

    if not user:
        return redirect(url_for('login'))  # 🚫 not logged in
    sector = postal[:2] if postal and len(postal) >= 2 else None
    nearby_tourist_attraction = []

    if sector:
        sql = text("SELECT * FROM attractions WHERE postal_code LIKE :sec")
        rows = db.session.execute(sql, {"sec": sector +"%"}).mappings().fetchall()
        nearby_tourist_attraction = [dict(r) for r in rows]
    if postal:
        mongo_postalLogs.insert_one({
                "user_id": session['user_id'],
                "postalCode": postal,
                "timestamp": datetime.utcnow()
            })
    
    total = mongo_tips.count_documents({})
                
    random_index = random.randint(0, total - 1)
    tip = mongo_tips.find().skip(random_index).limit(1)[0]

    cultural_tip  = {
        'tip': tip.get("tip"),
        'category': tip.get("category")
    }

    return render_template('dashboard.html', user=user, postal=postal,attractions = nearby_tourist_attraction, tip = cultural_tip)

@app.route('/logout')
def logout():
    session.clear()  # removes all session data
    print(str(session.get('users')))

    return redirect(url_for('home'))  # redirect to login page

# advanced filtering with SQL - link to service.py 
@app.route('/hygiene-near-attraction')
def clean_near_attraction():
    keyword = request.args.get('attraction')
    hygiene = request.args.get('hygiene')
    
    results = []
    if keyword and hygiene:
        results = hygiene_ratings(keyword, hygiene)

    return render_template('hygiene_near_attraction.html', results=results, keyword=keyword, hygiene=hygiene)

@app.route('/region-foods')
def food_by_region():
    region_name = request.args.get('region', 'Central')
    results = region(region_name)
    return render_template('food_by_region.html', results=results, region=region_name)

@app.route('/my-reviews')
def my_reviews():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    sort_option = request.args.get('sort', 'newest')  # default is newest now

    # Define sorting logic based on user selection
    if sort_option == 'newest':
        sort_query = [("created_at", -1)]  # Most recent first
    elif sort_option == 'oldest':
        sort_query = [("created_at", 1)]   # Earliest first
    elif sort_option == 'highest':
        sort_query = [("rating", -1)]      # 5 stars first
    elif sort_option == 'lowest':
        sort_query = [("rating", 1)]       # 1 star first
    else:
        sort_query = [("created_at", -1)]  # fallback to newest

    # Fetch reviews from MongoDB
    raw_reviews = list(mongo_reviews.find({"user_id": user_id}).sort(sort_query))

    # Add eatery name using SQL for each review
    enriched_reviews = []
    for review in raw_reviews:
        eatery_id = review.get("eatery_id")
        result = db.session.execute(
            text("SELECT name FROM eateries WHERE id = :id"),
            {"id": eatery_id}
        ).mappings().fetchone()

        review["eatery_name"] = result["name"] if result else "Unknown Eatery"
        enriched_reviews.append(review)

    return render_template('my_reviews.html', reviews=enriched_reviews, sort=sort_option)

# Delete review
@app.route('/delete_review/<review_id>', methods=['POST'])
def delete_review(review_id):
    mongo_reviews.delete_one({"_id": ObjectId(review_id)})

    flash("✅ Review has been deleted successfully", "success")
    return redirect(url_for('my_reviews'))

# Update Review
@app.route('/update_review/<review_id>', methods=['GET', 'POST'])
def update_review(review_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    review = mongo_reviews.find_one({"_id": ObjectId(review_id)})
    
    eatery_id = review.get("eatery_id")
    result = db.session.execute(
        text("SELECT name FROM eateries WHERE id = :id"),
        {"id": eatery_id}
    ).mappings().fetchone()

    eatery_name = result["name"] if result else "Unknown Eatery"
    print(eatery_name)

    if not review:
        flash("Review not found.", "danger")
        return redirect(url_for('my_reviews'))

    if request.method == 'POST':
        rating = int(request.form['rating'])
        comment = request.form['review']
        new_image = request.files.get('image')

        update_data = {
            'rating': rating,
            'comment': comment,
        }

        if new_image and new_image.filename != '':
            extension = new_image.filename.rsplit('.', 1)[-1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{extension}"

            img = Image.open(new_image)
            img.thumbnail((800, 800))
            buffer = io.BytesIO()
            img.save(buffer, format=img.format, optimize=True, quality=75)
            buffer.seek(0)

            s3.upload_fileobj(
                buffer,
                S3_BUCKET,
                unique_filename,
                ExtraArgs={'ContentType': new_image.content_type}
            )

            image_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"
            update_data['image_url'] = image_url

        mongo_reviews.update_many({"_id": ObjectId(review_id)}, {"$set": update_data})
        flash("✅ Review has been updated", "success")
        return redirect(url_for('my_reviews'))

    return render_template('update_reviews.html', review=review, eatery_name=eatery_name)

# Like Review
@app.route('/like_review/<review_id>', methods=['POST'])
def like_review(review_id):
    review = mongo_reviews.find_one({"_id": ObjectId(review_id)})
    user_id = session.get('user_id')


    if "likes_count" not in review:
        current_likes = len(review.get("likes", []))
        mongo_reviews.update_one(
            {"_id": ObjectId(review_id)},
            {"$set": {"likes_count": current_likes}}
        )
        review["likes_count"] = current_likes 

    if user_id in review.get("likes", []):
        # User already liked → unlike
        mongo_reviews.update_one(
            {"_id": ObjectId(review_id)},
            {
                "$pull": {"likes": user_id},
                "$inc": {"likes_count": -1}
            }
        )
    else:
        # User hasn't liked → like
        mongo_reviews.update_one(
            {"_id": ObjectId(review_id)},
            {
                "$addToSet": {"likes": user_id},
                "$inc": {"likes_count": 1}
            }
        )

    return redirect(request.referrer)

#gives users options they can filter by
@app.route("/api/filter-options/<filter_field>")
def filter_options(filter_field):
    allowed = {
        "category",
        "price_range",
        "postal_code",
        "hygiene_rating",
        "outdoor_seating",
        "family_friendly",
        "self_service",
    }

    if filter_field not in allowed:
        abort(400, "Invalid filter")
    
    if filter_field == "category":
        sql = text(
            "SELECT DISTINCT name "
            "FROM categories "
            "ORDER BY name"
        )
    else:
        # wrap the f-string in text()
        sql = text(
            f"SELECT DISTINCT {filter_field} "
            "FROM eateries "
            f"WHERE {filter_field} IS NOT NULL "
            f"ORDER BY {filter_field}"
        )
    
    result = db.session.execute(sql).fetchall()
    options = [row[0] for row in result]
    return jsonify(options)

@app.route('/api/nearest-eateries/<int:attraction_id>')
def nearest_eateries(attraction_id):
    limit = request.args.get('limit', default=8, type=int)
    rows  = get_nearest_eateries(attraction_id, limit)
    output = []
    for row in rows:
        data = dict(row)                      
        data['distance_km'] = float(data['distance_km'])
        eatery_reviews = list(mongo_reviews.find({"eatery_id": data['eatery_id']}))
        for review in eatery_reviews:
            review['_id'] = str(review['_id'])  

        data['reviews'] = eatery_reviews  
        output.append(data)

    return jsonify(output)


@app.route('/admin_analysis')
def admin_analysis():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    if session.get('user_type') != "admin":
        return redirect(url_for('login'))
    
    # rating chart pipeline
    rating_data_pipeline = [
        {"$group": {"_id": "$rating", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]

    rating_data = list(mongo_reviews.aggregate(rating_data_pipeline))  
    
     # Reviews over time chart
    reviews_overtime_pipeline = [
        {"$match": {"created_at": {"$gte": datetime.utcnow() - timedelta(days=30)}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    today = datetime.utcnow().date()
    date_labels = [(today - timedelta(days=i)).isoformat() for i in range(29, -1, -1)]

    raw_review_data = list(mongo_reviews.aggregate(reviews_overtime_pipeline)) 
    reviews_by_date = {}
    for record in raw_review_data:
        date = record["_id"]  
        count = record["count"]
        reviews_by_date[date] = count

    review_timeline_data = []
    for date in date_labels:
        review_timeline_data.append({
            "_id": date,
            "count": reviews_by_date.get(date, 0)
        })

    # Postal Code chart
    postal_data_pipeline = [
        {"$group": {"_id": "$postalCode", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    
    postal_code_data = list(mongo_postalLogs.aggregate(postal_data_pipeline))  
    print("postal_code_data" + str(postal_code_data))
    return render_template("admin_analysis.html",
        rating_data=rating_data or [],
        review_timeline_data=review_timeline_data or [],
        postal_code_data=postal_code_data
    )



def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def geocode_postal(postal):
    url = f"https://nominatim.openstreetmap.org/search?postalcode={postal}&country=Singapore&format=json"
    headers = {"User-Agent": "KopiGo/1.0"}
    res = requests.get(url, headers=headers)
    data = res.json()
    if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
    return None, None

@app.route("/itinerary")
def show_itinerary():
    user_id = session.get('user_id')
    if not user_id:
        flash("You must be logged in to view your itinerary.", "danger")
        return redirect(url_for('login'))

    user = mongo_users.find_one({"user_id": user_id})
    itinerary_ids = user.get("itineraries", [])
    if not itinerary_ids:
        return render_template("itinerary.html", itinerary_items=[])

    sql = text("SELECT * FROM attractions WHERE id IN :ids")
    rows = db.session.execute(sql, {"ids": tuple(itinerary_ids)}).mappings().all()
    itinerary_items = [dict(row) for row in rows]

    start = request.args.get("start", "")
    if start:
        lat1, lon1 = geocode_postal(start)
        if lat1:
            for item in itinerary_items:
                lat2, lon2 = item["latitude"], item["longitude"]
                item["distance"] = round(haversine(lat1, lon1, lat2, lon2), 2)
            # Sort by nearest
            itinerary_items.sort(key=lambda x: x.get("distance", float('inf')))

    return render_template("itinerary.html", itinerary_items=itinerary_items, start=start)

@app.route("/remove_itinerary/<int:attraction_id>")
def remove_itinerary(attraction_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("You must be logged in.", "danger")
        return redirect(url_for('login'))

    mongo_users.update_one(
        {"user_id": user_id},
        {"$pull": {"itineraries": attraction_id}}
    )

    start = request.args.get("start", "")
    return redirect(url_for("show_itinerary", start=start))

# ---------- Index Creation and Benchmarking ----------
def create_mongo_indexes():
    mongo_reviews.create_index([("eatery_id", 1)])
    mongo_reviews.create_index([("user_id", 1), ("created_at", -1)])
    mongo_reviews.create_index([("rating", 1)])

    mongo_users.create_index([("email", 1)], unique=True)
    mongo_users.create_index([("user_id", 1)], unique=True)

    # Automatically deletes logs after 7 days (604800 seconds)
    mongo_loginLogs.create_index([("timestamp", 1)], expireAfterSeconds=604800)
    mongo_postalLogs.create_index([("timestamp", 1)], expireAfterSeconds=604800)
    mongo_postalLogs.create_index([("postalCode", 1)])

    print("All MongoDB indexes created.")

def drop_mongo_indexes():
    mongo_reviews.drop_indexes()
    mongo_users.drop_indexes()
    mongo_loginLogs.drop_indexes()
    mongo_postalLogs.drop_indexes()
    print("All MongoDB indexes dropped.")

# --- Benchmark Function ---
def benchmark_mongo_query(label, fn):
    start = time.perf_counter()
    results = list(fn())
    end = time.perf_counter()
    duration = end - start
    print(f"MongoDB {label}: {duration:.5f}s, Records: {len(results)}")
    return duration, len(results)

def benchmark_mongo_indexes():
    print("\n=== MongoDB Benchmarking ===")
    results = {}

    drop_mongo_indexes()

    print("\nRunning MongoDB queries BEFORE indexing...\n")
    results["reviews_before"] = benchmark_mongo_query("FIND reviews (BEFORE INDEX)",
        lambda: mongo_reviews.find({"user_id": "17b24ce3-1b3f-4b4c-8899-7d0a77177240"}).sort("created_at", -1)
    )

    results["rating_before"] = benchmark_mongo_query("FIND rating (BEFORE INDEX)",
        lambda: mongo_reviews.find({"rating": 5})
    )

    results["postal_before"] = benchmark_mongo_query("FIND postalCode (BEFORE INDEX)",
        lambda: mongo_postalLogs.find({"postalCode": {"$regex": "172222"}})
    )

    create_mongo_indexes()

    print("\nRunning MongoDB queries AFTER indexing...\n")
    results["reviews_after"] = benchmark_mongo_query("FIND reviews (AFTER INDEX)",
        lambda: mongo_reviews.find({"user_name": "javier"}).sort("created_at", -1)
    )

    results["rating_after"] = benchmark_mongo_query("FIND rating (AFTER INDEX)",
        lambda: mongo_reviews.find({"rating": 5})
    )

    results["postal_after"] = benchmark_mongo_query("FIND postalCode (AFTER INDEX)",
        lambda: mongo_postalLogs.find({"postalCode": {"$regex": "172222"}})
    )
    print("\n=== MongoDB Benchmark Summary ===")
    for key in ["reviews", "rating", "postal"]:
        before = results[f"{key}_before"][0]
        after = results[f"{key}_after"][0]
        change = after - before
        verdict = "FASTER" if change < 0 else "SLOWER"
        print(f"{key.capitalize()}: {before:.5f}s → {after:.5f}s | Δ: {change:+.5f}s ({verdict})")



queries = [
    ("Read Attractions by Postal", "SELECT * FROM attractions WHERE postal_code LIKE '17%'"),
    ("Read All Tourist Attractions", "SELECT * FROM attractions"),
    ("Read Nearby Eateries by Postal", "SELECT * FROM eateries WHERE postal_code LIKE '17%'"),
    ("Read Eateries by Region", """
        SELECT e.* FROM eateries e
        JOIN postal_region_map prm ON LEFT(e.postal_code, 2) = prm.sector_prefix
        JOIN region r ON prm.region_id = r.id
        WHERE r.region_name = 'Central'
    """),
    ("Read Eateries Count by Region", """
        SELECT r.region_name, COUNT(*) AS count
        FROM region r
        JOIN postal_region_map prm ON prm.region_id = r.id
        JOIN eateries e ON LEFT(e.postal_code, 2) = prm.sector_prefix
        GROUP BY r.region_name
    """),
    ("Read Eateries by Filter", """
        SELECT * FROM eateries
        WHERE hygiene_rating = 'A' AND price_range = '1' AND outdoor_seating = 'Yes'
    """)
]

def drop_indexes():
    statements = [
        "DROP INDEX IF EXISTS idx_eateries_postal_code ON eateries",
        "DROP INDEX IF EXISTS idx_eateries_lat_lng ON eateries",
        "DROP INDEX IF EXISTS idx_eateries_price_range ON eateries",
        "DROP INDEX IF EXISTS idx_eateries_hygiene_rating ON eateries",
        "DROP INDEX IF EXISTS idx_eateries_outdoor_seating ON eateries",
        "DROP INDEX IF EXISTS idx_eateries_family_friendly ON eateries",
        "DROP INDEX IF EXISTS idx_eateries_self_service ON eateries",
        "DROP INDEX IF EXISTS idx_eateries_filter_combo ON eateries",
        "DROP INDEX IF EXISTS idx_attractions_postal_code ON attractions",
        "DROP INDEX IF EXISTS idx_attractions_name ON attractions",
        "DROP INDEX IF EXISTS idx_attractions_lat_lng ON attractions",
        "DROP INDEX IF EXISTS idx_hawkers_postal_code ON hawkers",
        "DROP INDEX IF EXISTS idx_located_in_region_id ON located_in",
        "DROP INDEX IF EXISTS idx_located_in_entity_type ON located_in",
        "DROP INDEX IF EXISTS idx_prm_region_id ON postal_region_map"
    ]
    for stmt in statements:
        db.session.execute(text(stmt))
    db.session.commit()
    print("All indexes dropped.")


def create_indexes():
    statements = [
        "CREATE INDEX idx_eateries_postal_code ON eateries(postal_code)",
        "CREATE INDEX idx_eateries_lat_lng ON eateries(latitude, longitude)",
        "CREATE INDEX idx_eateries_price_range ON eateries(price_range)",
        "CREATE INDEX idx_eateries_hygiene_rating ON eateries(hygiene_rating)",
        "CREATE INDEX idx_eateries_outdoor_seating ON eateries(outdoor_seating)",
        "CREATE INDEX idx_eateries_family_friendly ON eateries(family_friendly)",
        "CREATE INDEX idx_eateries_self_service ON eateries(self_service)",
        "CREATE INDEX idx_eateries_filter_combo ON eateries(hygiene_rating, price_range, outdoor_seating, family_friendly, self_service)",
        "CREATE INDEX idx_attractions_postal_code ON attractions(postal_code)",
        "CREATE INDEX idx_attractions_name ON attractions(name)",
        "CREATE INDEX idx_attractions_lat_lng ON attractions(latitude, longitude)",
        "CREATE INDEX idx_hawkers_postal_code ON hawkers(postal_code)",
        "CREATE INDEX idx_located_in_region_id ON located_in(region_id)",
        "CREATE INDEX idx_located_in_entity_type ON located_in(entity_type)",
        "CREATE INDEX idx_prm_region_id ON postal_region_map(region_id)"
    ]
    for stmt in statements:
        db.session.execute(text(stmt))
    db.session.commit()
    print("All indexes created.")

def benchmark_query(label, sql):
    start = time.perf_counter()
    result = db.session.execute(text(sql)).fetchall()
    end = time.perf_counter()
    print(f"[{label}] {end - start:.5f}s | Records: {len(result)}")
    return end - start

def run_mysql_benchmarks():
    print("\n=== MySQL Benchmarking ===")
    results = {}

    drop_indexes()
    print("\nRunning BEFORE index...\n")
    for label, sql in queries:
        results[label + "_before"] = benchmark_query(label + " (Before)", sql)

    create_indexes()
    print("\nRunning AFTER index...\n")
    for label, sql in queries:
        results[label + "_after"] = benchmark_query(label + " (After)", sql)

    print("\n=== Benchmark Summary ===")
    for label, _ in queries:
        before = results[label + "_before"]
        after = results[label + "_after"]
        delta = after - before
        verdict = "FASTER" if delta < 0 else "SLOWER"
        print(f"{label}: {before:.5f}s → {after:.5f}s | Δ: {delta:+.5f}s ({verdict})")


# ---------- Flask App Initialization ----------
if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        with app.app_context():
            app.jinja_env.globals['zip'] = zip
            db.create_all()  # Ensures table exists
            print("Connected to:", db.engine.url)
            load_initial_data()
            name_uniqueness_trigger()
            create_located_in_trigger()
            run_mysql_benchmarks()
            benchmark_mongo_indexes() 
            print("Starting Flask app...")
    app.run(debug=True)
