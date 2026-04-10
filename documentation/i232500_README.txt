================================================================================
WALMART DATA WAREHOUSE PROJECT
Near-Real-Time Data Warehouse Implementation using HYBRIDJOIN Algorithm
================================================================================

Student: Eeshaal Adeel
Student ID: 23i-2500

================================================================================
PROJECT STRUCTURE
================================================================================

The project contains the following files:

1. project.sql          - SQL script to create the data warehouse schema
2. hybrid.py            - Python implementation of HYBRIDJOIN ETL algorithm
3. queries.sql          - SQL script containing 20 OLAP analytical queries
4. customer_master_data.csv      - Customer dimension data
5. product_master_data.csv      - Product dimension data
6. transactional_data.csv         - Transactional fact data
7. Project-Report     - Project documentation and report
8. README.txt           - This file (setup and operation instructions)

================================================================================
PREREQUISITES
================================================================================

Before running the project, ensure you have the following installed:

1. Python 3.7 or higher
   - Download from: https://www.python.org/downloads/
   - Verify installation: python --version

2. MySQL Server 8.0 or higher
   - Download from: https://dev.mysql.com/downloads/mysql/
   - Verify installation: mysql --version

3. Required Python Packages:
   - pandas
   - mysql-connector-python
   
   Install packages using:
   pip install pandas mysql-connector-python

4. MySQL Workbench (optional, for running queries)
   - Download from: https://dev.mysql.com/downloads/workbench/

================================================================================
STEP 1: DATABASE SETUP
================================================================================

1.1 Start MySQL Server
   - On Windows: Start MySQL service from Services
   - On Linux/Mac: sudo systemctl start mysql (or mysql.server start)

1.2 Create Database User (if needed)
   - Open MySQL command line or MySQL Workbench
   - Login as root user
   - Create user (optional, you can use root):
     CREATE USER 'walmart_user'@'localhost' IDENTIFIED BY 'your_password';
     GRANT ALL PRIVILEGES ON *.* TO 'walmart_user'@'localhost';
     FLUSH PRIVILEGES;

1.3 Create the Data Warehouse Schema
   - Open MySQL Workbench or MySQL command line
   - Connect to your MySQL server
   - Open and execute the project.sql file:
     - In MySQL Workbench: File → Open SQL Script → Select project.sql → Execute
     - In command line: mysql -u root -p < project.sql
   
   This will:
   - Drop existing walmart_dw database if it exists
   - Create new walmart_dw database
   - Create all dimension tables (dim_customer, dim_product, dim_store, dim_supplier, dim_date)
   - Create fact table (fact_sales)
   - Set up all primary keys and foreign key constraints

1.4 Verify Schema Creation
   - Run the following query to verify tables were created:
     USE walmart_dw;
     SHOW TABLES;
   
   You should see 6 tables:
   - dim_customer
   - dim_date
   - dim_product
   - dim_store
   - dim_supplier
   - fact_sales

================================================================================
STEP 2: DATA LOADING USING HYBRIDJOIN
================================================================================

2.1 Prepare Data Files
   - Ensure all three CSV files are in the same directory as hybrid.py:
     - customer_master_data.csv
     - product_master_data.csv
     - transactional_data.csv

2.2 Run the HYBRIDJOIN ETL Process
   - Open terminal/command prompt
   - Navigate to the project directory:
     cd C:\Users\umar\Desktop\i232500\project
   
   - Run the Python script:
     python hybrid.py

2.3 Enter Database Credentials
   When prompted, enter your MySQL connection details:
   
   Host [localhost]: 
     - Press Enter for localhost (default)
     - Or enter your MySQL server hostname/IP
   
   User [root]:
     - Press Enter for root (default)
     - Or enter your MySQL username
   
   Password:
     - Enter your MySQL password (input will be hidden)
   
   Database [walmart_dw]:
     - Press Enter for walmart_dw (default)
     - Or enter your database name

2.4 Monitor ETL Process
   The script will display progress messages:
   
   [Loader] Loading dim_product + dim_store + dim_supplier...
   [Loader] Loading dim_customer...
   [Loader] Populating dim_date...
   [Stream] Starting producer reading transactional_data.csv
   [Hybrid] Consumer started. HS=10000 VP=500
   [Hybrid] Stream finished and processing complete.
   [Run] ETL finished in X.XX seconds.

2.5 Verify Data Loading
   After the ETL completes, verify data was loaded:
   
   - Open MySQL Workbench
   - Connect to your database
   - Run verification queries:
   
     USE walmart_dw;
     SELECT COUNT(*) FROM dim_customer;
     SELECT COUNT(*) FROM dim_product;
     SELECT COUNT(*) FROM dim_store;
     SELECT COUNT(*) FROM dim_supplier;
     SELECT COUNT(*) FROM dim_date;
     SELECT COUNT(*) FROM fact_sales;
   
   - Check a sample of fact data:
     SELECT * FROM fact_sales LIMIT 10;

================================================================================
STEP 3: RUNNING ANALYTICAL QUERIES
================================================================================

3.1 Open Queries File
   - Open MySQL Workbench
   - File → Open SQL Script → Select queries.sql

3.2 Execute Individual Queries
   - Each query is separated by comments (-- Q1, -- Q2, etc.)
   - To run a specific query:
     - Highlight the query block (from -- QX to the next -- QY)
     - Click Execute (or press Ctrl+Shift+Enter)
   
   - To run all queries:
     - Select all (Ctrl+A)
     - Execute (Ctrl+Shift+Enter)

3.3 Query Descriptions
   The queries.sql file contains 20 analytical queries:
   
   Q1:  Top 5 Revenue-Generating Products on Weekdays/Weekends (Monthly)
   Q2:  Customer Demographics by Purchase Amount with City Category
   Q3:  Product Category Sales by Occupation
   Q4:  Total Purchases by Gender and Age Group (Quarterly)
   Q5:  Top 5 Occupations by Product Category Sales
   Q6:  City Category Performance by Marital Status (Past 6 Months)
   Q7:  Average Purchase Amount by Stay Duration and Gender
   Q8:  Top 5 Revenue-Generating Cities by Product Category
   Q9:  Monthly Sales Growth by Product Category
   Q10: Weekend vs. Weekday Sales by Age Group
   Q11: Top 5 Revenue-Generating Products on Weekdays/Weekends (Monthly)
   Q12: Store Revenue Growth Rate Quarterly for 2017
   Q13: Supplier Sales Contribution by Store and Product
   Q14: Seasonal Analysis of Product Sales
   Q15: Store-Wise and Supplier-Wise Monthly Revenue Volatility
   Q16: Top 5 Products Purchased Together (Product Affinity)
   Q17: Yearly Revenue Trends by Store, Supplier, Product (with ROLLUP)
   Q18: Revenue and Volume Analysis for H1 and H2
   Q19: Identify High Revenue Spikes in Product Sales
   Q20: Create STORE_QUARTERLY_SALES View

3.4 Query Results
   - Results will be displayed in the Result Grid below the query editor
   - You can export results to CSV if needed
   - For Q20, the view is created and can be queried separately:
     SELECT * FROM STORE_QUARTERLY_SALES;

================================================================================
STEP 4: TROUBLESHOOTING
================================================================================

4.1 Connection Errors
   Problem: "Cannot connect to MySQL server"
   Solution:
   - Verify MySQL server is running
   - Check host, username, and password are correct
   - Ensure MySQL port (3306) is not blocked by firewall

4.2 Import Errors
   Problem: "No module named 'pandas'" or "No module named 'mysql'"
   Solution:
   - Install missing packages: pip install pandas mysql-connector-python
   - If using virtual environment, ensure it's activated

4.3 File Not Found Errors
   Problem: "CSV file not found"
   Solution:
   - Ensure all CSV files are in the same directory as hybrid.py
   - Check file names match exactly (case-sensitive on Linux/Mac)
   - Verify file paths are correct

4.4 Database Errors
   Problem: "Table doesn't exist" or "Foreign key constraint fails"
   Solution:
   - Re-run project.sql to recreate the schema
   - Ensure all tables were created successfully
   - Check that dimension tables are loaded before fact table

4.5 Query Errors
   Problem: "Unknown column" or syntax errors in queries
   Solution:
   - Verify schema matches the queries (run project.sql again)
   - Check that data was loaded successfully
   - Ensure you're using the correct database (USE walmart_dw;)

4.6 Performance Issues
   Problem: Queries run very slowly
   Solution:
   - Ensure indexes are created (primary keys create indexes automatically)
   - Check that sufficient data was loaded
   - Consider adding additional indexes on frequently queried columns

================================================================================
STEP 5: RE-RUNNING THE ETL PROCESS
================================================================================

If you need to reload data:

5.1 Drop Existing Data (Optional)
   - In MySQL Workbench, run:
     USE walmart_dw;
     TRUNCATE TABLE fact_sales;
     TRUNCATE TABLE dim_customer;
     TRUNCATE TABLE dim_product;
     TRUNCATE TABLE dim_store;
     TRUNCATE TABLE dim_supplier;
     TRUNCATE TABLE dim_date;

5.2 Re-run project.sql (if schema changes needed)
   - Execute project.sql to recreate tables

5.3 Re-run hybrid.py
   - Follow Step 2 instructions again

================================================================================
CONFIGURATION PARAMETERS
================================================================================

The hybrid.py file contains configurable parameters (lines 26-33):

HASH_TABLE_SLOTS = 10000    # Number of hash table slots (hS)
DISK_BUFFER_SIZE = 500      # Partition size (vP)
BATCH_INSERT_SIZE = 500     # Batch size for database inserts
STREAM_BUFFER_MAX = 20000   # Maximum stream buffer size
STREAM_CHUNK_SIZE = 200     # CSV reading chunk size

You can modify these values if needed, but default values work well for most cases.

================================================================================
PROJECT DELIVERABLES SUMMARY
================================================================================

1. Create-DW (project.sql)
   - SQL script to create star schema
   - Drops existing schema before creating new one
   - Creates all dimension and fact tables with constraints

2. Hybrid-Join (hybrid.py)
   - Python implementation of HYBRIDJOIN algorithm
   - Implements complete ETL pipeline
   - Prompts for database credentials at runtime

3. Queries-DW (queries.sql)
   - Contains all 20 OLAP queries
   - Includes slicing, dicing, drill-down, and rollup operations
   - Creates materialized view (Q20)

4. Project-Report (Project-Report.md)
   - Project overview
   - DW schema explanation
   - HYBRIDJOIN algorithm explanation
   - Three shortcomings of HYBRIDJOIN
   - Lessons learned

5. Read-Me (README.txt)
   - This file with step-by-step instructions

