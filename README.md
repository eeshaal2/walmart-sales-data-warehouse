## Walmart Sales Analytics – Data Warehouse Project

This project demonstrates the design and implementation of a near real-time data warehouse for retail analytics using SQL, Python, and dimensional modeling.

It simulates how companies like Walmart process high-volume transactional data to generate actionable business insights.

---

## Key Highlights
Designed a Star Schema data warehouse in MySQL
Built a custom ETL pipeline using Python
Implemented HYBRIDJOIN algorithm for stream processing
Performed OLAP analysis (slice, dice, drill-down)
Generated insights on sales, customers, and product performance

---

## Problem Statement

Retail businesses generate massive transactional data daily.
To make fast business decisions, they need:

Clean and structured data
Near real-time processing
Efficient analytical queries

This project solves that by building a scalable data warehousing pipeline.

---

## System Architecture
Data Sources: CSV files (customers, products, transactions)
ETL Layer: Python (HYBRIDJOIN + transformations)
Data Warehouse: MySQL (Star Schema)
Analytics Layer: SQL (OLAP queries)

---

## Data Warehouse Design
# Star Schema
Fact Table:
fact_sales → stores transactions (quantity, revenue)
Dimension Tables:
dim_customer → demographics (age, gender, city, etc.)
dim_product → product details
dim_store → store info
dim_supplier → supplier data
dim_date → time-based analysis

 Optimized for fast analytical queries
 Supports business intelligence use cases

---

## ETL Pipeline

The ETL pipeline:

Extracts data from CSV files
Transforms and enriches data
Loads into MySQL data warehouse
Key Features:
Batch processing for efficiency
In-memory caching
Data cleaning and transformation
Revenue calculation (price × quantity)
 
 ---
 
 ## HYBRIDJOIN Algorithm

A custom stream-based join algorithm designed for near real-time data processing.

What it does:
Joins fast-arriving transaction streams with master data
Uses:
Hash Table
Queue (FIFO)
Stream Buffer
Supports high-throughput data ingestion
Why it matters:

Traditional joins are slow for streaming data — this improves performance significantly.

---

## OLAP Analysis

Performed multiple analytical queries including:

Revenue trends over time
Customer segmentation
Product performance analysis
Store-level comparisons
Seasonal and time-based insights

---

## Sample Use Cases
Identify top-selling products
Analyze customer buying behavior
Track revenue trends by time and location
Optimize inventory decisions

---

## Tech Stack
Python (ETL + Algorithm)
MySQL (Data Warehouse)
SQL (Analytics Queries)
Pandas (Data Processing)

---

## Limitations
Fixed memory size in HYBRIDJOIN
Sequential partition processing
Limited handling of late-arriving data

---

## What I Learned
Data warehousing & dimensional modeling
Building ETL pipelines
Query optimization
Handling large-scale data processing
Real-world analytics workflows

---

## Author

Eeshaal Adeel
Data Analyst | SQL | Python | Tableau
