/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.7.2-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: KopiGo
-- ------------------------------------------------------
-- Server version	11.7.2-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `attractions`
--

DROP TABLE IF EXISTS `attractions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `attractions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `address` varchar(255) DEFAULT NULL,
  `latitude` float DEFAULT NULL,
  `longitude` float DEFAULT NULL,
  `overview` text DEFAULT NULL,
  `postal_code` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=513 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE INDEX idx_attractions_postal_code ON attractions(postal_code);
CREATE INDEX idx_attractions_name ON attractions(name);
CREATE INDEX idx_attractions_lat_lng ON attractions(latitude, longitude);

/*!40101 SET character_set_client = @saved_cs_client */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_uca1400_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_before_insert_attraction_name_dup
    BEFORE INSERT ON attractions
    FOR EACH ROW
    BEGIN
      IF EXISTS (SELECT 1 FROM attractions WHERE name = NEW.name ) 
        THEN
          SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'An attraction with that name already exists.';
      END IF;
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_uca1400_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_after_insert_attraction
    AFTER INSERT ON attractions
    FOR EACH ROW
    BEGIN
      DECLARE regionId INT;
      SET regionId = (
        SELECT region_id
        FROM postal_region_map
        WHERE sector_prefix = LEFT(NEW.postal_code, 2)
      );

      IF regionId IS NOT NULL THEN
        INSERT INTO located_in (entity_id, entity_type, region_id)
        VALUES (NEW.id, 'Attraction', regionId);
      END IF;
    END */;;
DELIMITER ;

/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `eateries`
--

DROP TABLE IF EXISTS `eateries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `eateries` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `address` varchar(255) DEFAULT NULL,
  `latitude` float DEFAULT NULL,
  `longitude` float DEFAULT NULL,
  `price_range` varchar(10) DEFAULT NULL,
  `postal_code` varchar(20) DEFAULT NULL,
  `hygiene_rating` varchar(5) DEFAULT NULL,
  `outdoor_seating` varchar(10) DEFAULT NULL,
  `family_friendly` varchar(10) DEFAULT NULL,
  `self_service` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9051 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE INDEX idx_eateries_postal_code ON eateries(postal_code);
CREATE INDEX idx_eateries_lat_lng ON eateries(latitude, longitude);
CREATE INDEX idx_eateries_price_range ON eateries(price_range);
CREATE INDEX idx_eateries_hygiene_rating ON eateries(hygiene_rating);
CREATE INDEX idx_eateries_outdoor_seating ON eateries(outdoor_seating);
CREATE INDEX idx_eateries_family_friendly ON eateries(family_friendly);
CREATE INDEX idx_eateries_self_service ON eateries(self_service);
CREATE INDEX idx_eateries_filter_combo 
    ON eateries(hygiene_rating, price_range, outdoor_seating, family_friendly, self_service);

/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `categories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=232 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `eateries_category_map`
--

DROP TABLE IF EXISTS `eateries_category_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `eateries_category_map` (
  `eatery_id` int(11) NOT NULL,
  `category_id` int(11) NOT NULL,
  PRIMARY KEY (`eatery_id`,`category_id`),
  KEY `category_id` (`category_id`),
  CONSTRAINT `eateries_category_map_ibfk_1` FOREIGN KEY (`eatery_id`) REFERENCES `eateries` (`id`) ON DELETE CASCADE,
  CONSTRAINT `eateries_category_map_ibfk_2` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `hawker_stall_type_map`
--

DROP TABLE IF EXISTS `hawker_stall_type_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `hawker_stall_type_map` (
  `hawker_id` int(11) NOT NULL,
  `stall_type_id` int(11) NOT NULL,
  `count` int(11) NOT NULL,
  PRIMARY KEY (`hawker_id`,`stall_type_id`),
  KEY `stall_type_id` (`stall_type_id`),
  CONSTRAINT `hawker_stall_type_map_ibfk_1` FOREIGN KEY (`hawker_id`) REFERENCES `hawkers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `hawker_stall_type_map_ibfk_2` FOREIGN KEY (`stall_type_id`) REFERENCES `stall_types` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `hawkers`
--

DROP TABLE IF EXISTS `hawkers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `hawkers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name_of_centre` varchar(255) NOT NULL,
  `location_of_centre` varchar(255) DEFAULT NULL,
  `type_of_centre` varchar(255) DEFAULT NULL,
  `owner` varchar(100) DEFAULT NULL,
  `postal_code` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=216 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE INDEX idx_hawkers_postal_code ON hawkers(postal_code);

/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `located_in`
--

DROP TABLE IF EXISTS `located_in`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `located_in` (
  `entity_id` int(11) NOT NULL,
  `entity_type` varchar(20) NOT NULL CHECK (`entity_type` in ('Attraction','Eatery','Hawker')),
  `region_id` int(11) NOT NULL,
  PRIMARY KEY (`entity_id`,`entity_type`),
  KEY `region_id` (`region_id`),
  CONSTRAINT `located_in_ibfk_1` FOREIGN KEY (`region_id`) REFERENCES `region` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE INDEX idx_located_in_region_id ON located_in(region_id);
CREATE INDEX idx_located_in_entity_type ON located_in(entity_type);

/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `postal_region_map`
--

DROP TABLE IF EXISTS `postal_region_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `postal_region_map` (
  `sector_prefix` varchar(2) NOT NULL,
  `region_id` int(11) NOT NULL,
  PRIMARY KEY (`sector_prefix`),
  KEY `region_id` (`region_id`),
  CONSTRAINT `postal_region_map_ibfk_1` FOREIGN KEY (`region_id`) REFERENCES `region` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE INDEX idx_prm_region_id ON postal_region_map(region_id);

/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `region`
--

DROP TABLE IF EXISTS `region`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `region` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `region_name` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `region_name` (`region_name`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `stall_types`
--

DROP TABLE IF EXISTS `stall_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `stall_types` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2025-06-28 12:57:10
/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.7.2-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: KopiGo
-- ------------------------------------------------------
-- Server version	11.7.2-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Dumping data for table `region`
--

LOCK TABLES `region` WRITE;
/*!40000 ALTER TABLE `region` DISABLE KEYS */;
INSERT INTO `region` VALUES
(4,'Central'),
(2,'East'),
(1,'North'),
(5,'North-East'),
(3,'West');
/*!40000 ALTER TABLE `region` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `postal_region_map`
--

LOCK TABLES `postal_region_map` WRITE;
/*!40000 ALTER TABLE `postal_region_map` DISABLE KEYS */;
INSERT INTO `postal_region_map` VALUES
('05',1),
('06',1),
('07',1),
('25',1),
('27',1),
('28',1),
('69',1),
('70',1),
('71',1),
('72',1),
('73',1),
('75',1),
('76',1),
('77',1),
('78',1),
('13',2),
('14',2),
('15',2),
('16',2),
('17',2),
('18',2),
('42',2),
('43',2),
('44',2),
('45',2),
('46',2),
('47',2),
('48',2),
('49',2),
('50',2),
('51',2),
('52',2),
('81',2),
('10',3),
('11',3),
('12',3),
('22',3),
('23',3),
('58',3),
('59',3),
('60',3),
('61',3),
('62',3),
('63',3),
('64',3),
('65',3),
('66',3),
('67',3),
('68',3),
('01',4),
('02',4),
('03',4),
('04',4),
('08',4),
('09',4),
('21',4),
('24',4),
('26',4),
('29',4),
('30',4),
('31',4),
('32',4),
('33',4),
('34',4),
('35',4),
('36',4),
('37',4),
('38',4),
('39',4),
('40',4),
('41',4),
('19',5),
('20',5),
('53',5),
('54',5),
('55',5),
('56',5),
('57',5),
('79',5),
('80',5),
('82',5);
/*!40000 ALTER TABLE `postal_region_map` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES
(1,'art_gallery'),
(2,'bakery'),
(3,'bar'),
(4,'beauty_salon'),
(5,'bicycle_store'),
(6,'book_store'),
(7,'bowling_alley'),
(8,'cafe'),
(9,'campground'),
(10,'car_wash'),
(11,'clothing_store'),
(12,'convenience_store'),
(13,'department_store'),
(14,'electronics_store'),
(15,'establishment'),
(16,'finance'),
(17,'florist'),
(18,'food'),
(19,'furniture_store'),
(20,'gas_station'),
(21,'grocery_or_supermarket'),
(22,'gym'),
(23,'hair_care'),
(24,'health'),
(25,'home_goods_store'),
(26,'laundry'),
(27,'library'),
(28,'liquor_store'),
(29,'lodging'),
(30,'meal_delivery'),
(31,'meal_takeaway'),
(32,'movie_theater'),
(33,'museum'),
(34,'night_club'),
(35,'park'),
(36,'pet_store'),
(37,'point_of_interest'),
(38,'real_estate_agency'),
(39,'restaurant'),
(40,'school'),
(41,'shopping_mall'),
(42,'spa'),
(43,'storage'),
(44,'store'),
(45,'supermarket'),
(46,'tourist_attraction');
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `stall_types`
--

LOCK TABLES `stall_types` WRITE;
/*!40000 ALTER TABLE `stall_types` DISABLE KEYS */;
INSERT INTO `stall_types` VALUES
(2,'Cooked Food Stalls'),
(3,'Market Produce Stalls'),
(1,'Total Stalls');
/*!40000 ALTER TABLE `stall_types` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2025-06-28 12:57:59
