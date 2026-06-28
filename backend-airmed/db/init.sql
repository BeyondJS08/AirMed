-- Create test database alongside the main 'airmed' database
SELECT 'CREATE DATABASE airmed_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airmed_test')\gexec
