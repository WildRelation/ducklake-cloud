INSTALL ducklake;
INSTALL postgres;
LOAD ducklake;
LOAD postgres;

CREATE OR REPLACE SECRET (
    TYPE postgres,
    HOST '127.0.0.1',
    PORT 5432,
    DATABASE 'ducklake',
    USER 'duck',
    PASSWORD 'postgres'
);

CREATE OR REPLACE SECRET (
    TYPE s3,
    KEY_ID 'ducklake',
    SECRET 'minioadmin',
    REGION 'local',
    ENDPOINT '127.0.0.1:9000',
    URL_STYLE 'path',
    USE_SSL false
);

ATTACH 'ducklake:postgres:dbname=ducklake'
AS mitt_lake (DATA_PATH 's3://ducklake/');

USE mitt_lake;
