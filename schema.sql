
-- Author: Matt Cutshall
-- ------------------ CREATE SCHEMA-------------------------

DROP SCHEMA IF EXISTS nfl_combine;
CREATE SCHEMA nfl_combine;
USE nfl_combine;

-- Lookup Table: to find long description of position
CREATE TABLE position 
 (position_abr VARCHAR(5) NOT NULL,
  position_desc  VARCHAR(45) NOT NULL,
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  PRIMARY KEY  (position_abr)) ;


-- Lookup Table: to find conference that maps to school
CREATE TABLE conference 
 (school VARCHAR(45) NOT NULL,
 school_power VARCHAR(45) NOT NULL,
  conference VARCHAR(45) NOT NULL ,
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY  (school)) ;

-- Lookup Table: to find coeffiencts of attributes
CREATE TABLE attribute_coefficients
 (	Position VARCHAR(10) NOT NULL,
	Intercept FLOAT(10) NOT NULL,
	Weight_40yd_Dash  FLOAT(10) NOT NULL,
	Weight_Vertical_Jump  FLOAT(10) NOT NULL,
	Weight_Bench_Press  FLOAT(10) NOT NULL,
	Weight_Broad_Jump  FLOAT(10) NOT NULL,
	Weight_3Cone_Drill  FLOAT(10) NOT NULL,
	Weight_20yd_Shuttle  FLOAT(10) NOT NULL,
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY  (Position)) ;
  
-- Table structure for table `player`

CREATE TABLE player 
  (player_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  first_name  VARCHAr(45) NOT NULL,
  last_name VARCHAR(45) NOT NULL,
  drafted VARCHAR(1) NOT NULL,
  position_abr VARCHAR(5) NOT NULL,
  school VARCHAR(45) NOT NULL,
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY  (player_id),
  KEY idx_player_last_name (last_name),
  CONSTRAINT fk_player_position FOREIGN KEY (position_abr) REFERENCES position (position_abr),
  CONSTRAINT fk_player_school FOREIGN KEY (school) REFERENCES conference (school)) ;

CREATE TABLE draft_result 
  (draft_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  player_id INT UNSIGNED NOT NULL,  
  draft_year YEAR NOT NULL,
  draft_round INT(5) UNSIGNED NOT NULL ,
  draft_pick INT(5) NOT NULL,
  drafting_team VARCHAR(45) NOT NULL,
  last_update  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (draft_id),
  CONSTRAINT fk_draft_player FOREIGN KEY (player_id) REFERENCES player (player_id)) ;

CREATE TABLE combine_result 
  (combine_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  player_id INT UNSIGNED NOT NULL,  
  forty_yd_dash FLOAT(5),  
  vert_jump FLOAT(5),
  bench_press FLOAT(5),
  broad_jump FLOAT(5),
  cone_drill FLOAT(5),
  twenty_yd_dash FLOAT(5),
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (combine_id),
  CONSTRAINT fk_combine_player FOREIGN KEY (player_id)  REFERENCES player (player_id)) ;

-- Author: Matt Cutshall
-- ------------------ LOAD LOOKUP TABLES -------------------------

-- Load lookup_position.csv
-- I received help from AI to larn the INFILE statement to load from CSV. 

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/lookup_position.csv'
INTO TABLE position
FIELDS TERMINATED BY ',' 
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(position_abr, position_desc);

-- Load lookup_schools.csv (Maps School, Conference, Power to school, conference, school_power)
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/lookup_schools.csv'
INTO TABLE conference
FIELDS TERMINATED BY ',' 
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(school, conference, school_power);

-- Load lookup_weights.csv
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/lookup_weights.csv'
INTO TABLE attribute_coefficients
FIELDS TERMINATED BY ',' 
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(Position, Intercept, Weight_40yd_Dash, Weight_Vertical_Jump, Weight_Bench_Press, Weight_Broad_Jump, Weight_3Cone_Drill, Weight_20yd_Shuttle);



-- Author: Matt Cutshall
-- ------------------ LOAD PRIMARY TABLES-------------------------
-- create landing temp table for my data
CREATE TEMPORARY TABLE temp_combine (
  first_name  VARCHAR(45),
  last_name VARCHAR(45) ,
  position_abr VARCHAR(10),
  school VARCHAR(50),
  height VARCHAR(10) ,
  weight VARCHAR(10),
  forty_yd VARCHAR(10),
  vert VARCHAR(10) ,
  bench VARCHAR(10),
  broad VARCHAR(10),
  cone VARCHAR(10),
  shuttle VARCHAR(10),
  drafted VARCHAR(5),
  team VARCHAR(45),
  round VARCHAR(10) ,
  pick VARCHAR(10),
  year INT) ;

-- Load data to temp table
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/Combine.csv'
INTO TABLE temp_combine
FIELDS TERMINATED BY ',' 
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

-- insert data into table `player`
INSERT INTO player (first_name, last_name, drafted, position_abr, school)
SELECT 
  first_name, 
  last_name, 
  drafted , 
  position_abr, 
  school
FROM temp_combine ;

-- insert data into table `draft_result`
INSERT INTO draft_result (player_id, draft_year, draft_round, draft_pick, drafting_team)
SELECT 
  p.player_id,
  r.year,
  CAST(r.round AS UNSIGNED) ,
  CAST(r.pick AS UNSIGNED),
  r.team
FROM temp_combine r
JOIN player p ON p.first_name = r.first_name 
	AND p.last_name = r.last_name 
    AND p.school = r.school
WHERE r.drafted = 'Y' AND r.team IS NOT NULL;



-- insert data to  `combine_result` converts 'DNP' or blank strings to null
-- I was recieving error when running queries with DNP and reference AI for solution --
INSERT INTO combine_result (player_id, forty_yd_dash, vert_jump, bench_press, broad_jump, cone_drill, twenty_yd_dash)
SELECT 
  p.player_id,
  NULLIF(NULLIF(r.forty_yd, 'DNP'), ''),
  NULLIF(NULLIF(r.vert, 'DNP'), ''),
  NULLIF(NULLIF(r.bench, 'DNP'), ''),
  NULLIF(NULLIF(r.broad, 'DNP'), ''),
  NULLIF(NULLIF(r.cone, 'DNP'), ''),
  NULLIF(NULLIF(r.shuttle, 'DNP'), '')
FROM temp_combine r
JOIN player p ON p.first_name = r.first_name 
             AND p.last_name = r.last_name 
             AND p.school = r.school;


DROP TEMPORARY TABLE temp_combine ;



