-- Open your data/retailsense-user-<id>.sqlite3 with a SQLite client after loading data.
-- Gross purchases only; excluded rows and cancellations are not in this table.
SELECT ROUND(SUM(Revenue),2) AS gross_revenue,
       COUNT(DISTINCT InvoiceNo) AS orders,
       COUNT(DISTINCT CustomerID) AS customers,
       ROUND(SUM(Revenue)/COUNT(DISTINCT InvoiceNo),2) AS average_order
FROM transactions;

SELECT strftime('%Y-%m',InvoiceDate) AS month,
       ROUND(SUM(Revenue),2) AS revenue
FROM transactions GROUP BY month ORDER BY month;

SELECT Description, ROUND(SUM(Revenue),2) AS revenue
FROM transactions GROUP BY Description ORDER BY revenue DESC LIMIT 10;

SELECT Country, COUNT(DISTINCT InvoiceNo) AS orders,
       ROUND(SUM(Revenue),2) AS revenue
FROM transactions GROUP BY Country ORDER BY revenue DESC;

WITH customer_orders AS (
 SELECT CustomerID,COUNT(DISTINCT InvoiceNo) AS orders
 FROM transactions GROUP BY CustomerID
)
SELECT ROUND(100.0*SUM(CASE WHEN orders>1 THEN 1 ELSE 0 END)/COUNT(*),2)
 AS repeat_customer_percent FROM customer_orders;

SELECT CustomerID, probability FROM predictions ORDER BY probability DESC LIMIT 25;
