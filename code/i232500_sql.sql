-- eeshaal adeel (23i-2500)
drop database if exists walmart_dw;
create database walmart_dw;
use walmart_dw;

drop table if exists fact_sales;
drop table if exists dim_product;
drop table if exists dim_customer;
drop table if exists dim_date;
drop table if exists dim_store;
drop table if exists dim_supplier;

create table dim_customer (
    customer_id int primary key,
    gender varchar(10),
    age varchar(10),
    occupation varchar(50),
    city_category char(1),
    stay_in_current_city_years varchar(5),
    marital_status boolean
);

create table dim_store (
    store_id int primary key,
    store_name varchar(100)
);

create table dim_supplier (
    supplier_id int primary key,
    supplier_name varchar(100)
);

create table dim_product (
    product_id varchar(20) primary key,
    product_category varchar(50),
    price decimal(10,2)
);

create table dim_date (
    date_id int primary key,
    full_date date,
    day int,
    month int,
    quarter int,
    year int,
    weekday varchar(10)
);

create table fact_sales (
    order_id int,  
    customer_id int,
    product_id varchar(20),
    date_id int,
    store_id int,
    supplier_id int,
    quantity int,
    revenue decimal(12,2),

    primary key (order_id, product_id), 
    foreign key (customer_id) references dim_customer(customer_id),
    foreign key (product_id) references dim_product(product_id),
    foreign key (date_id) references dim_date(date_id),
    foreign key (store_id) references dim_store(store_id),
    foreign key (supplier_id) references dim_supplier(supplier_id)
);

-- Queries
-- Q1: Top 5 Revenue-Generating Products on Weekdays/Weekends (Monthly)
-- (Assuming 'a specified year' is 2016)
WITH RankedRevenue AS (
    SELECT
        DD.year,
        DD.month,
        DP.product_id,
        CASE
            WHEN DD.weekday IN ('Saturday', 'Sunday') THEN 'Weekend'
            ELSE 'Weekday'
        END AS day_type,
        SUM(FS.revenue) AS total_revenue,
        RANK() OVER (
            PARTITION BY DD.year, DD.month, CASE WHEN DD.weekday IN ('Saturday', 'Sunday') THEN 'Weekend' ELSE 'Weekday' END
            ORDER BY SUM(FS.revenue) DESC
        ) AS revenue_rank
    FROM fact_sales FS
    JOIN dim_date DD ON FS.date_id = DD.date_id
    JOIN dim_product DP ON FS.product_id = DP.product_id
    WHERE DD.year = 2016 -- Assuming specified year
    GROUP BY DD.year, DD.month, DP.product_id, day_type
)
SELECT *
FROM RankedRevenue
WHERE revenue_rank <= 5
ORDER BY year, month, day_type, revenue_rank;


-- Q2: Customer Demographics by Purchase Amount with City Category Breakdown
SELECT
    DC.city_category,
    DC.gender,
    DC.age,
    SUM(FS.revenue) AS total_purchase_amount
FROM fact_sales FS
JOIN dim_customer DC ON FS.customer_id = DC.customer_id
GROUP BY DC.city_category, DC.gender, DC.age
ORDER BY DC.city_category, DC.gender, DC.age;


-- Q3: Product Category Sales by Occupation
SELECT
    DP.product_category,
    DC.occupation,
    SUM(FS.revenue) AS total_sales
FROM fact_sales FS
JOIN dim_product DP ON FS.product_id = DP.product_id
JOIN dim_customer DC ON FS.customer_id = DC.customer_id
GROUP BY DP.product_category, DC.occupation
ORDER BY DP.product_category, total_sales DESC;


-- Q4: Total Purchases by Gender and Age Group with Quarterly Trend
-- (Assuming 'current year' is 2015)
SELECT
    DD.year,
    DD.quarter,
    DC.gender,
    DC.age,
    SUM(FS.revenue) AS total_purchases
FROM fact_sales FS
JOIN dim_customer DC ON FS.customer_id = DC.customer_id
JOIN dim_date DD ON FS.date_id = DD.date_id
WHERE DD.year = 2015 -- Assuming current year
GROUP BY DD.year, DD.quarter, DC.gender, DC.age
ORDER BY DD.year, DD.quarter, DC.gender, DC.age;


-- Q5: Top 5 Occupations by Product Category Sales
WITH RankedOccupations AS (
    SELECT
        DP.product_category,
        DC.occupation,
        SUM(FS.revenue) AS total_sales,
        RANK() OVER (
            PARTITION BY DP.product_category
            ORDER BY SUM(FS.revenue) DESC
        ) AS sales_rank
    FROM fact_sales FS
    JOIN dim_product DP ON FS.product_id = DP.product_id
    JOIN dim_customer DC ON FS.customer_id = DC.customer_id
    GROUP BY DP.product_category, DC.occupation
)
SELECT *
FROM RankedOccupations
WHERE sales_rank <= 5
ORDER BY product_category, sales_rank;


-- Q6: City Category Performance by Marital Status with Monthly Breakdown (Past 6 Months)
SELECT
    DD.year,
    DD.month,
    DC.city_category,
    DC.marital_status,
    SUM(FS.revenue) AS total_purchase_amount
FROM fact_sales FS
JOIN dim_customer DC ON FS.customer_id = DC.customer_id
JOIN dim_date DD ON FS.date_id = DD.date_id
WHERE DD.full_date >= DATE_SUB('2016-4-12', INTERVAL 6 MONTH)
  AND DD.full_date <= '2016-4-12'
GROUP BY DD.year, DD.month, DC.city_category, DC.marital_status
ORDER BY DD.year, DD.month, DC.city_category;


-- Q7: Average Purchase Amount by Stay Duration and Gender
SELECT
    DC.stay_in_current_city_years,
    DC.gender,
    AVG(FS.revenue) AS average_purchase_amount
FROM fact_sales FS
JOIN dim_customer DC ON FS.customer_id = DC.customer_id
GROUP BY DC.stay_in_current_city_years, DC.gender
ORDER BY DC.stay_in_current_city_years, DC.gender;


-- Q8: Top 5 Revenue-Generating Cities by Product Category
WITH RankedCities AS (
    SELECT
        DP.product_category,
        DC.city_category,
        SUM(FS.revenue) AS total_revenue,
        RANK() OVER (
            PARTITION BY DP.product_category
            ORDER BY SUM(FS.revenue) DESC
        ) AS revenue_rank
    FROM fact_sales FS
    JOIN dim_customer DC ON FS.customer_id = DC.customer_id
    JOIN dim_product DP ON FS.product_id = DP.product_id
    GROUP BY DP.product_category, DC.city_category
)
SELECT *
FROM RankedCities
WHERE revenue_rank <= 5
ORDER BY product_category, revenue_rank;


-- Q9: Monthly Sales Growth by Product Category
-- (Assuming 'current year' is 2017)
WITH MonthlySales AS (
    SELECT
        DD.year,
        DD.month,
        DP.product_category,
        SUM(FS.revenue) AS total_sales
    FROM fact_sales FS
    JOIN dim_product DP ON FS.product_id = DP.product_id
    JOIN dim_date DD ON FS.date_id = DD.date_id
    WHERE DD.year = 2017 -- Assuming current year
    GROUP BY DD.year, DD.month, DP.product_category
),
LaggedSales AS (
    SELECT
        year,
        month,
        product_category,
        total_sales,
        LAG(total_sales, 1, 0) OVER (
            PARTITION BY product_category
            ORDER BY year, month
        ) AS previous_month_sales
    FROM MonthlySales
)
SELECT
    year,
    month,
    product_category,
    total_sales,
    previous_month_sales,
    CASE
        WHEN previous_month_sales = 0 THEN NULL -- Avoid division by zero
        ELSE (total_sales - previous_month_sales) / previous_month_sales * 100
    END AS sales_growth_percentage
FROM LaggedSales
ORDER BY product_category, year, month;


-- Q10: Weekend vs. Weekday Sales by Age Group
-- (Assuming 'current year' is 2020)
SELECT
    DC.age,
    CASE
        WHEN DD.weekday IN ('Saturday', 'Sunday') THEN 'Weekend'
        ELSE 'Weekday'
    END AS day_type,
    SUM(FS.revenue) AS total_sales
FROM fact_sales FS
JOIN dim_customer DC ON FS.customer_id = DC.customer_id
JOIN dim_date DD ON FS.date_id = DD.date_id
WHERE DD.year = 2020 
GROUP BY DC.age, day_type
ORDER BY DC.age, day_type;


-- Q11: Top Revenue-Generating Products on Weekdays and Weekends with Monthly Drill-Down
-- Find the top 5 products that generated the highest revenue, separated by weekday and weekend
-- sales, with results grouped by month for a specified year.
-- (Assuming 'a specified year' is 2016)
WITH TopProductsByMonth AS (
    SELECT
        DD.year,
        DD.month,
        DP.product_id,
        CASE
            WHEN DD.weekday IN ('Saturday', 'Sunday') THEN 'Weekend'
            ELSE 'Weekday'
        END AS day_type,
        SUM(FS.revenue) AS total_revenue,
        RANK() OVER (
            PARTITION BY DD.year, DD.month, CASE WHEN DD.weekday IN ('Saturday', 'Sunday') THEN 'Weekend' ELSE 'Weekday' END
            ORDER BY SUM(FS.revenue) DESC
        ) AS revenue_rank
    FROM fact_sales FS
    JOIN dim_date DD ON FS.date_id = DD.date_id
    JOIN dim_product DP ON FS.product_id = DP.product_id
    WHERE DD.year = 2016 -- Assuming specified year
    GROUP BY DD.year, DD.month, DP.product_id, day_type
)
SELECT *
FROM TopProductsByMonth
WHERE revenue_rank <= 5
ORDER BY year, month, day_type, revenue_rank;


-- Q12: Trend Analysis of Store Revenue Growth Rate Quarterly for 2017
WITH QuarterlySales AS (
    SELECT
        DS.store_name,
        DD.quarter,
        SUM(FS.revenue) AS total_sales
    FROM fact_sales FS
    JOIN dim_date DD ON FS.date_id = DD.date_id
    JOIN dim_store DS ON FS.store_id = DS.store_id
    WHERE DD.year = 2017
    GROUP BY DS.store_name, DD.quarter
),
LaggedQuarterlySales AS (
    SELECT
        store_name,
        quarter,
        total_sales,
        LAG(total_sales, 1, 0) OVER (
            PARTITION BY store_name
            ORDER BY quarter
        ) AS previous_quarter_sales
    FROM QuarterlySales
)
SELECT
    store_name,
    quarter,
    total_sales,
    previous_quarter_sales,
    CASE
        WHEN previous_quarter_sales = 0 THEN NULL
        ELSE (total_sales - previous_quarter_sales) / previous_quarter_sales * 100
    END AS growth_rate_percentage
FROM LaggedQuarterlySales
ORDER BY store_name, quarter;


-- Q13: Detailed Supplier Sales Contribution by Store and Product Name
-- (Using product_id as product_name is not in the schema)
SELECT
    DS.store_name,
    DSU.supplier_name,
    DP.product_id,
    SUM(FS.revenue) AS total_sales
FROM fact_sales FS
JOIN dim_product DP ON FS.product_id = DP.product_id
JOIN dim_store DS ON FS.store_id = DS.store_id
JOIN dim_supplier DSU ON FS.supplier_id = DSU.supplier_id
GROUP BY DS.store_name, DSU.supplier_name, DP.product_id
ORDER BY DS.store_name, DSU.supplier_name, total_sales DESC;


-- Q14: Seasonal Analysis of Product Sales Using Dynamic Drill-Down
SELECT
    DP.product_id,
    CASE
        WHEN DD.month IN (3, 4, 5) THEN 'Spring'
        WHEN DD.month IN (6, 7, 8) THEN 'Summer'
        WHEN DD.month IN (9, 10, 11) THEN 'Fall'
        WHEN DD.month IN (12, 1, 2) THEN 'Winter'
    END AS season,
    SUM(FS.revenue) AS total_sales
FROM fact_sales FS
JOIN dim_product DP ON FS.product_id = DP.product_id
JOIN dim_date DD ON FS.date_id = DD.date_id
GROUP BY DP.product_id, season
ORDER BY DP.product_id, total_sales DESC;


-- Q15: Store-Wise and Supplier-Wise Monthly Revenue Volatility
WITH MonthlySales AS (
    SELECT
        DS.store_name,
        DSU.supplier_name,
        DD.year,
        DD.month,
        SUM(FS.revenue) AS total_sales
    FROM fact_sales FS
    JOIN dim_date DD ON FS.date_id = DD.date_id
    JOIN dim_store DS ON FS.store_id = DS.store_id
    JOIN dim_supplier DSU ON FS.supplier_id = DSU.supplier_id
    GROUP BY DS.store_name, DSU.supplier_name, DD.year, DD.month
),
LaggedSales AS (
    SELECT
        store_name,
        supplier_name,
        year,
        month,
        total_sales,
        LAG(total_sales, 1, 0) OVER (
            PARTITION BY store_name, supplier_name
            ORDER BY year, month
        ) AS previous_month_sales
    FROM MonthlySales
)
SELECT
    store_name,
    supplier_name,
    year,
    month,
    total_sales,
    previous_month_sales,
    CASE
        WHEN previous_month_sales = 0 THEN NULL
        ELSE (total_sales - previous_month_sales) / previous_month_sales * 100
    END AS revenue_volatility_percentage
FROM LaggedSales
ORDER BY store_name, supplier_name, year, month;




-- Q16: Top 5 Products Purchased Together (Product Affinity Analysis)
-- Since every order_id is unique, we group by Customer + Date
-- to identify products bought in the "same basket/transaction".

with daily_baskets as (
    select
        fs1.product_id as product_a,
        fs2.product_id as product_b,
        fs1.customer_id
    from fact_sales fs1
    join fact_sales fs2
        on fs1.customer_id = fs2.customer_id
        and fs1.date_id = fs2.date_id   -- Must be bought on the same day
        and fs1.product_id < fs2.product_id -- Prevents duplicates (A-B vs B-A)
),
pair_counts as (
    select
        product_a,
        product_b,
        count(*) as together_count
    from daily_baskets
    group by product_a, product_b
)
select product_a, product_b, together_count
from pair_counts
order by together_count desc
limit 5;


-- Q17: Yearly Revenue Trends by Store, Supplier, and Product with ROLLUP
SELECT
    DD.year,
    DS.store_name,
    DSU.supplier_name,
    DP.product_id,
    SUM(FS.revenue) AS total_revenue
FROM fact_sales FS
JOIN dim_date DD ON FS.date_id = DD.date_id
JOIN dim_product DP ON FS.product_id = DP.product_id
JOIN dim_store DS ON FS.store_id = DS.store_id
JOIN dim_supplier DSU ON FS.supplier_id = DSU.supplier_id
GROUP BY DD.year, DS.store_name, DSU.supplier_name, DP.product_id WITH ROLLUP
ORDER BY DD.year, DS.store_name, DSU.supplier_name, DP.product_id;


-- Q18: Revenue and Volume-Based Sales Analysis for Each Product for H1 and H2
SELECT
    DP.product_id,
    DD.year,
    SUM(CASE WHEN DD.month <= 6 THEN FS.revenue ELSE 0 END) AS H1_Revenue,
    SUM(CASE WHEN DD.month > 6 THEN FS.revenue ELSE 0 END) AS H2_Revenue,
    SUM(FS.revenue) AS Yearly_Revenue,
    SUM(CASE WHEN DD.month <= 6 THEN FS.quantity ELSE 0 END) AS H1_Quantity,
    SUM(CASE WHEN DD.month > 6 THEN FS.quantity ELSE 0 END) AS H2_Quantity,
    SUM(FS.quantity) AS Yearly_Quantity
FROM fact_sales FS
JOIN dim_product DP ON FS.product_id = DP.product_id
JOIN dim_date DD ON FS.date_id = DD.date_id
GROUP BY DP.product_id, DD.year
ORDER BY DP.product_id, DD.year;


-- Q19: Identify High Revenue Spikes in Product Sales and Highlight Outliers
WITH DailySales AS (
    SELECT
        DP.product_id,
        DD.full_date,
        SUM(FS.revenue) AS daily_sales
    FROM fact_sales FS
    JOIN dim_product DP ON FS.product_id = DP.product_id
    JOIN dim_date DD ON FS.date_id = DD.date_id
    GROUP BY DP.product_id, DD.full_date
),
ProductAvgSales AS (
    SELECT
        product_id,
        AVG(daily_sales) AS avg_daily_sales,
        STDDEV_POP(daily_sales) AS std_daily_sales
    FROM DailySales
    GROUP BY product_id
)
SELECT
    DS.full_date,
    DS.product_id,
    DS.daily_sales,
    PAS.avg_daily_sales,
    CASE 
        WHEN PAS.avg_daily_sales > 0 THEN (DS.daily_sales / PAS.avg_daily_sales)
        ELSE NULL
    END AS spike_factor
FROM DailySales DS
JOIN ProductAvgSales PAS ON DS.product_id = PAS.product_id
WHERE DS.daily_sales > (PAS.avg_daily_sales + COALESCE(PAS.std_daily_sales, 0))
   OR DS.daily_sales > (1.5 * PAS.avg_daily_sales)
ORDER BY spike_factor DESC;


-- Q20: Create a View STORE_QUARTERLY_SALES
DROP VIEW IF EXISTS STORE_QUARTERLY_SALES;

CREATE VIEW STORE_QUARTERLY_SALES AS
SELECT
    DS.store_name,
    DD.year,
    DD.quarter,
    SUM(FS.revenue) AS total_quarterly_sales
FROM fact_sales FS
JOIN dim_date DD ON FS.date_id = DD.date_id
JOIN dim_store DS ON FS.store_id = DS.store_id
GROUP BY DS.store_name, DD.year, DD.quarter
ORDER BY DS.store_name, DD.year, DD.quarter;

SELECT * FROM STORE_QUARTERLY_SALES WHERE store_name = 'Game Zone';


SELECT 'dim_customer' AS table_name, COUNT(*) AS no_rows FROM dim_customer
UNION ALL
SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL
SELECT 'dim_store', COUNT(*) FROM dim_store
UNION ALL
SELECT 'dim_supplier', COUNT(*) FROM dim_supplier
UNION ALL
SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL
SELECT 'fact_sales', COUNT(*) FROM fact_sales;

