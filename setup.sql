--jinja
-- =============================================================================
-- Setup Role and Database
-- =============================================================================

CREATE ROLE IF NOT EXISTS <%sa_role%>;

SET current_user = (SELECT CURRENT_USER());
GRANT ROLE <%sa_role%> TO USER IDENTIFIER($current_user);

CREATE DATABASE IF NOT EXISTS <%db_name%>;
GRANT OWNERSHIP ON DATABASE <%db_name%> TO ROLE <%sa_role%>;
GRANT OWNERSHIP ON ALL SCHEMAS IN DATABASE <%db_name%> TO ROLE <%sa_role%>;

-- =============================================================================
-- Switch Context
-- =============================================================================

USE ROLE <%sa_role%>;
USE DATABASE <%db_name%>;
USE SCHEMA PUBLIC;

-- =============================================================================
-- Create Stage and Load Data
-- =============================================================================

CREATE STAGE IF NOT EXISTS <%db_name%>.PUBLIC.DATA;

PUT file://data/penguins.csv @<%db_name%>.PUBLIC.DATA AUTO_COMPRESS = FALSE;

-- =============================================================================
-- Create Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS <%db_name%>.PUBLIC.PENGUINS (
    species           VARCHAR,
    island            VARCHAR,
    bill_length_mm    FLOAT,
    bill_depth_mm     FLOAT,
    flipper_length_mm INTEGER,
    body_mass_g       INTEGER,
    sex               VARCHAR
);

-- =============================================================================
-- Load CSV Data
-- =============================================================================

CREATE FILE FORMAT IF NOT EXISTS <%db_name%>.PUBLIC.csv_format
    TYPE            = 'CSV'
    FIELD_DELIMITER = ','
    SKIP_HEADER     = 1;

COPY INTO <%db_name%>.PUBLIC.PENGUINS
    FROM @<%db_name%>.PUBLIC.DATA/penguins.csv
    FILE_FORMAT = <%db_name%>.PUBLIC.csv_format;

-- =============================================================================
-- Verify
-- =============================================================================

SELECT * FROM <%db_name%>.PUBLIC.PENGUINS LIMIT 10;
