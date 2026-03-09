from init_data import db
from sqlalchemy import text
from functools import wraps
from models import Eateries

def transactional(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            db.session.execute(text("BEGIN;"))
            result = fn(*args, **kwargs)
            db.session.execute(text("COMMIT;"))
            return result
        except:
            db.session.execute(text("ROLLBACK;"))
            raise
    return wrapper


def get_eateries_columns():
    sql = text("""
      SELECT COLUMN_NAME
      FROM INFORMATION_SCHEMA.COLUMNS
      WHERE TABLE_SCHEMA = :schema
        AND TABLE_NAME   = :table
      ORDER BY ORDINAL_POSITION
    """)
    rows = db.session.execute(sql, {
      "schema": db.engine.url.database,  
      "table":  Eateries.__table__.name  
    }).fetchall()
    return [r[0] for r in rows]

#gives list of eateries that is filtered by user's choice
def find_eateries(postal_code: str, **filters):
    params = {
      "sector":            f"{postal_code[:2]}%",
      "outdoor_seating":   f"%{filters.get('outdoor_seating','')}%" if filters.get('outdoor_seating') else None,
      "family_friendly":   f"%{filters.get('family_friendly','')}%"  if filters.get('family_friendly') else None,
      "price_range":       f"%{filters.get('price_range','')}%"      if filters.get('price_range') else None,
      "hygiene_rating":    f"%{filters.get('hygiene_rating','')}%"   if filters.get('hygiene_rating') else None,
      "self_service":      f"%{filters.get('self_service','')}%"     if filters.get('self_service') else None,
      "category":          filters.get('category') 
    }

    sql = text("""
      SELECT 
        e.*,
        GROUP_CONCAT(c.name ORDER BY c.name SEPARATOR ', ') AS categories
      FROM eateries e
      LEFT JOIN eateries_category_map m 
        ON m.eatery_id = e.id
      LEFT JOIN categories c 
        ON c.id = m.category_id
      WHERE e.postal_code LIKE :sector
        AND (:outdoor_seating   IS NULL OR e.outdoor_seating   LIKE :outdoor_seating)
        AND (:family_friendly   IS NULL OR e.family_friendly   LIKE :family_friendly)
        AND (:price_range       IS NULL OR e.price_range       LIKE :price_range)
        AND (:hygiene_rating    IS NULL OR e.hygiene_rating    LIKE :hygiene_rating)
        AND (:self_service      IS NULL OR e.self_service      LIKE :self_service)
        AND (
          :category IS NULL
          OR EXISTS (
            SELECT 1
            FROM eateries_category_map m2
            JOIN categories c2 ON c2.id = m2.category_id
            WHERE m2.eatery_id = e.id
              AND c2.name = :category
          )
        )
      GROUP BY e.id
      ORDER BY e.name;
      """)

    return db.session.execute(sql, params).mappings().all()



def count_eateries(postal_code: str, **filters) -> int:
    params = {
      "sector":            f"{postal_code[:2]}%",
      "outdoor_seating":   f"%{filters.get('outdoor_seating','')}%" if filters.get('outdoor_seating') else None,
      "family_friendly":   f"%{filters.get('family_friendly','')}%"  if filters.get('family_friendly') else None,
      "price_range":       f"%{filters.get('price_range','')}%"      if filters.get('price_range') else None,
      "hygiene_rating":    f"%{filters.get('hygiene_rating','')}%"   if filters.get('hygiene_rating') else None,
      "self_service":      f"%{filters.get('self_service','')}%"     if filters.get('self_service') else None,
      "category":          filters.get('category') 
    }

    sql = text("""
      SELECT COUNT(DISTINCT e.id)
      FROM eateries e
      LEFT JOIN eateries_category_map m 
        ON m.eatery_id = e.id
      LEFT JOIN categories c 
        ON c.id = m.category_id
      WHERE e.postal_code LIKE :sector
        AND (:outdoor_seating   IS NULL OR e.outdoor_seating   LIKE :outdoor_seating)
        AND (:family_friendly   IS NULL OR e.family_friendly   LIKE :family_friendly)
        AND (:price_range       IS NULL OR e.price_range       LIKE :price_range)
        AND (:hygiene_rating    IS NULL OR e.hygiene_rating    LIKE :hygiene_rating)
        AND (:self_service      IS NULL OR e.self_service      LIKE :self_service)
        AND (
          :category IS NULL
          OR c.name = :category
        )
    """)
    return db.session.execute(sql, params).scalar()


#provides filtered list of selected hygiene rating near attraction
def hygiene_ratings(attraction_keyword, max_hygiene):
    query = text("""
        SELECT e.name AS eateries_name, e.hygiene_rating, a.name AS attraction_name
        FROM eateries e
        JOIN attractions a ON e.postal_code = a.postal_code
        WHERE e.hygiene_rating <= :max_hygiene
        AND a.name LIKE :attraction_keyword
        ORDER BY e.name;
    """)
    result = db.session.execute(query, {
        "attraction_keyword": f"%{attraction_keyword}%",
        "max_hygiene": max_hygiene
    })
    return result.fetchall()

# discover food places by selecting a region 
def region(region_name):
    query = text("""
      SELECT e.name, e.hygiene_rating, region.region_name AS region_name
      FROM eateries e
      JOIN postal_region_map prm ON LEFT(e.postal_code, 2) = prm.sector_prefix
      JOIN region ON prm.region_id = region.id
      WHERE region.region_name = :region_name
      ORDER BY e.name;
      """)
    return db.session.execute(query, {"region_name": region_name}).fetchall()



#using normalisation table to get count of eateries,attractions and hawker centre in each region
def get_count_sector():
    sql = text("""
        SELECT 
            r.region_name,
            l.entity_type,
            COUNT(*) AS count
        FROM located_in l
        JOIN region r ON l.region_id = r.id
        GROUP BY r.region_name, l.entity_type
        ORDER BY r.region_name, l.entity_type;
    """)
    result = db.session.execute(sql)
    return result.mappings().all()


# get the 8 nearest eateries to an attraction by calculating its great circle distance using the spherical law of cosines
# which makes use of an eateries's coordinates
def get_nearest_eateries(attraction_id: int, limit: int = 8):
    sql = text(f"""
      SELECT
        e.id AS eatery_id, e.name AS name, e.outdoor_seating, e.hygiene_rating, e.price_range,
        (6371 * ACOS(
          COS(RADIANS(a.latitude)) 
        * COS(RADIANS(e.Latitude)) 
        * COS(RADIANS(e.Longitude) - RADIANS(a.longitude))
        + SIN(RADIANS(a.latitude)) 
        * SIN(RADIANS(e.Latitude))
        ) ) AS distance_km
      FROM attractions a
      CROSS JOIN eateries e
      WHERE a.id = :attraction_id
      ORDER BY distance_km
      LIMIT {limit}
      """)
    result = db.session.execute(sql, {"attraction_id": attraction_id})
    return result.mappings().all()

# gives the top 3 eateries in terms of hygiene_rating
def get_top_rated_eateries_by_region(limit=3):
    sql = text("""
        SELECT region_name, eatery_id, eatery_name, hygiene_rating FROM (
            SELECT 
                e.id AS eatery_id,
                e.name AS eatery_name,
                e.hygiene_rating,
                r.region_name,
                ROW_NUMBER() OVER (PARTITION BY r.region_name ORDER BY e.name) AS rn
            FROM eateries e
            JOIN postal_region_map prm ON LEFT(e.postal_code, 2) = prm.sector_prefix
            JOIN region r ON prm.region_id = r.id
            WHERE e.hygiene_rating = 'A'
        ) AS ranked
        WHERE rn <= :limit
        ORDER BY region_name, rn;
    """)
    rows = db.session.execute(sql, {"limit": limit}).mappings().all()
    return rows


# trigger used for automatically checking if there is another attraction with same name when admin creates new attraction
@transactional
def name_uniqueness_trigger():
    db.session.execute(text("DROP TRIGGER IF EXISTS trg_before_insert_attraction_name_dup"))

    db.session.execute(text("""
    CREATE TRIGGER trg_before_insert_attraction_name_dup
    BEFORE INSERT ON attractions
    FOR EACH ROW
    BEGIN
      IF EXISTS (SELECT 1 FROM attractions WHERE name = NEW.name) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'An attraction with that name already exists.';
      END IF;
    END;
    """))
@transactional
def create_located_in_trigger():
    db.session.execute(text("DROP TRIGGER IF EXISTS trg_after_insert_attraction;"))

    db.session.execute(text("""
    CREATE TRIGGER trg_after_insert_attraction
    AFTER INSERT ON attractions
    FOR EACH ROW
    BEGIN
      INSERT INTO located_in (entity_id, entity_type, region_id)
      SELECT NEW.id, 'Attraction', prm.region_id
      FROM postal_region_map prm
      WHERE prm.sector_prefix = LEFT(NEW.postal_code, 2);
    END;
    """))


# left join, right join then union to emulate a full join 
# full join both eateries and hawkers and then group them by their region
# returning eateries and hawkers count in each region
def get_counts_by_region_fulljoin():
    sql = text("""
                  SELECT
            r.region_name AS region,
            SUM(COALESCE(e.eatery_count,0))  AS eatery_count,
            SUM(COALESCE(h.hawker_count,0))  AS hawker_count
          FROM region r
          JOIN postal_region_map prm  ON prm.region_id = r.id
          LEFT JOIN (
            SELECT LEFT(postal_code,2) AS sector_prefix, COUNT(*) AS eatery_count
            FROM eateries
            GROUP BY sector_prefix
          ) e ON e.sector_prefix = prm.sector_prefix
          LEFT JOIN (
            SELECT LEFT(postal_code,2) AS sector_prefix, COUNT(*) AS hawker_count
            FROM hawkers
            GROUP BY sector_prefix
          ) h ON h.sector_prefix = prm.sector_prefix
          GROUP BY r.region_name
          ORDER BY r.region_name;

    """)
    return db.session.execute(sql).mappings().all()
