import csv
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

def get_region_id_from_postal(postal_code):
    if not postal_code or len(postal_code) < 2:
        return None
    sector_prefix = postal_code.strip()[:2]
    sql = text("""
        SELECT region_id
        FROM postal_region_map
        WHERE sector_prefix = :prefix
    """)
    result = db.session.execute(sql, {'prefix': sector_prefix}).first()
    return result[0] if result else None

def insert_located_in(entity_type, entity_id, region_id):
    if region_id:
        sql = text("""
            INSERT INTO located_in (entity_type, entity_id, region_id)
            VALUES (:entity_type, :entity_id, :region_id)
        """)
        db.session.execute(sql, {
            'entity_type': entity_type,
            'entity_id': entity_id,
            'region_id': region_id
        })

def load_eatery_dataset():
    exists = db.session.execute(text("SELECT 1 FROM eateries LIMIT 1")).first()
    if exists:
        return

    category_map = {}

    with open('dataset/singapore_places_eatery_ids.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            postal_code = row.get('Postal Code', '').strip()
            if not postal_code:
                continue

            # Insert eatery
            insert_sql = text("""
                INSERT INTO eateries (id, name, address, latitude, longitude,
                price_range, postal_code, hygiene_rating, outdoor_seating,
                family_friendly, self_service)
                VALUES (:id, :name, :address, :latitude, :longitude, :price_range,
                :postal_code, :hygiene_rating, :outdoor_seating,
                :family_friendly, :self_service)
            """)
            params = {
                "id": row['Eatery ID'],
                "name": row['Name'],
                "address": row.get('Address'),
                "latitude": float(row['Latitude']) if row['Latitude'] else None,
                "longitude": float(row['Longitude']) if row['Longitude'] else None,
                "price_range": row.get('Price Range'),
                "postal_code": postal_code,
                "hygiene_rating": row.get('Hygiene Rating'),
                "outdoor_seating": row.get('Outdoor Seating'),
                "family_friendly": row.get('Family Friendly'),
                "self_service": row.get('Self Service')
            }
            db.session.execute(insert_sql, params)

            # Normalize category
            eatery_id = row['Eatery ID']
            raw_categories = str(row.get('Category', '')).split(',')
            for cat in raw_categories:
                cat = cat.strip()
                if not cat:
                    continue
                if cat not in category_map:
                    result = db.session.execute(
                        text("INSERT INTO categories (name) VALUES (:name) ON DUPLICATE KEY UPDATE name = name"),
                        {'name': cat}
                    )
                    cat_id = db.session.execute(
                        text("SELECT id FROM categories WHERE name = :name"), {'name': cat}
                    ).scalar()
                    category_map[cat] = cat_id
                db.session.execute(
                    text("INSERT IGNORE INTO eateries_category_map (eatery_id, category_id) VALUES (:eid, :cid)"),
                    {'eid': eatery_id, 'cid': category_map[cat]}
                )

            # Link to region
            region_id = get_region_id_from_postal(postal_code)
            insert_located_in('Eatery', eatery_id, region_id)

    db.session.commit()

def load_attractions_dataset():
    exists = db.session.execute(text("SELECT 1 FROM attractions LIMIT 1")).first()
    if exists:
        return

    with open('dataset/TouristAttractions_WithPostal.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            postal_code = row['Postal Code'].strip()
            if not postal_code:
                continue

            insert_sql = text("""
                INSERT INTO attractions (name, address, latitude, longitude, overview, postal_code)
                VALUES (:name, :address, :latitude, :longitude, :overview, :postal_code)
            """)
            db.session.execute(insert_sql, {
                "name": row['Name'],
                "address": row['Address'],
                "latitude": float(row['Latitude']),
                "longitude": float(row['Longitude']),
                "overview": row['Overview'],
                "postal_code": postal_code
            })

    db.session.commit()

def load_hawker_centre_dataset():
    exists = db.session.execute(text("SELECT 1 FROM hawkers LIMIT 1")).first()
    if exists:
        return

    with open('dataset/Hawker_Centre_Data.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            postal_code = row['postal_code'].strip()
            if not postal_code:
                continue

            insert_sql = text("""
                INSERT INTO hawkers
                (name_of_centre, location_of_centre, type_of_centre,
                 owner, postal_code)
                VALUES
                (:name_of_centre, :location_of_centre, :type_of_centre,
                 :owner, :postal_code)
            """)
            db.session.execute(insert_sql, {
                "name_of_centre": row['name_of_centre'],
                "location_of_centre": row['location_of_centre'],
                "type_of_centre": row['type_of_centre'],
                "owner": row['owner'],
                "postal_code": postal_code
            })

            hawker_id = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            region_id = get_region_id_from_postal(postal_code)
            insert_located_in('Hawker', hawker_id, region_id)

            # Stall breakdown (assumes stall_types exist)
            stall_map = {
                'Total Stalls': row.get('no_of_stalls'),
                'Cooked Food Stalls': row.get('no_of_cooked_food_stalls'),
                'Market Produce Stalls': row.get('no_of_mkt_produce_stalls'),
            }
            for type_name, count in stall_map.items():
                if count and count.isdigit():
                    type_id = db.session.execute(text("SELECT id FROM stall_types WHERE name = :name"), {'name': type_name}).scalar()
                    db.session.execute(
                        text("INSERT INTO hawker_stall_type_map (hawker_id, stall_type_id, count) VALUES (:hid, :tid, :cnt)"),
                        {'hid': hawker_id, 'tid': type_id, 'cnt': int(count)}
                    )

    db.session.commit()



def load_initial_data():
    load_eatery_dataset()
    load_attractions_dataset()
    load_hawker_centre_dataset()