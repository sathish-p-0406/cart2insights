# Every query uses the same filter: real sales only, selected states, selected months.
FILTER = """o.order_status NOT IN ('canceled', 'unavailable')
            AND o.order_value IS NOT NULL
            AND o.customer_state IN :states
            AND o.purchase_month BETWEEN :start AND :end"""

KPI = f"""
SELECT ROUND(SUM(o.order_value), 2)           AS revenue,
       COUNT(*)                               AS orders,
       COUNT(DISTINCT o.customer_unique_id)   AS customers,
       ROUND(AVG(o.order_value), 2)           AS avg_order_value,
       ROUND(AVG(o.review_score), 2)          AS avg_review
FROM order_features o
WHERE {FILTER}
"""

SELLER_COUNT = f"""
SELECT COUNT(DISTINCT i.seller_id) AS sellers
FROM item_features i
JOIN order_features o ON i.order_id = o.order_id
WHERE {FILTER}
"""

MONTHLY_REVENUE = f"""
SELECT o.purchase_month AS month,
       ROUND(SUM(o.order_value), 2) AS revenue,
       COUNT(*) AS orders
FROM order_features o
WHERE {FILTER}
GROUP BY o.purchase_month
ORDER BY o.purchase_month
"""

REVENUE_BY_CATEGORY = f"""
SELECT i.category,
       COUNT(*) AS items_sold,
       ROUND(SUM(i.price), 2) AS revenue
FROM item_features i
JOIN order_features o ON i.order_id = o.order_id
WHERE {FILTER}
GROUP BY i.category
HAVING COUNT(*) >= 50
ORDER BY revenue DESC
LIMIT 15
"""

TOP_PRODUCTS = f"""
SELECT i.product_id, i.category,
       COUNT(*) AS units_sold,
       ROUND(SUM(i.price), 2) AS revenue
FROM item_features i
JOIN order_features o ON i.order_id = o.order_id
WHERE {FILTER}
GROUP BY i.product_id, i.category
ORDER BY units_sold DESC
LIMIT 10
"""

SALES_BY_STATE = f"""
SELECT o.customer_state AS state,
       ROUND(SUM(o.order_value), 2) AS revenue,
       COUNT(*) AS orders
FROM order_features o
WHERE {FILTER}
GROUP BY o.customer_state
ORDER BY revenue DESC
"""

CUSTOMER_TOTALS = f"""
SELECT o.customer_unique_id,
       COUNT(*) AS orders,
       ROUND(SUM(o.order_value), 2) AS total_spent
FROM order_features o
WHERE {FILTER}
GROUP BY o.customer_unique_id
"""

CUSTOMERS_BY_STATE = f"""
SELECT o.customer_state AS state,
       COUNT(DISTINCT o.customer_unique_id) AS customers
FROM order_features o
WHERE {FILTER}
GROUP BY o.customer_state
ORDER BY customers DESC
"""

SELLER_PERFORMANCE = f"""
SELECT i.seller_id,
       ROUND(SUM(i.price), 2) AS revenue,
       COUNT(DISTINCT i.order_id) AS orders,
       ROUND(AVG(o.review_score), 2) AS avg_review
FROM item_features i
JOIN order_features o ON i.order_id = o.order_id
WHERE {FILTER}
GROUP BY i.seller_id
ORDER BY revenue DESC
LIMIT 10
"""

DELIVERY_STATUS = f"""
SELECT o.delivery_status AS status,
       COUNT(*) AS orders,
       ROUND(AVG(o.review_score), 2) AS avg_review
FROM order_features o
WHERE {FILTER}
GROUP BY o.delivery_status
"""

DELIVERY_BY_STATE = f"""
SELECT o.customer_state AS state,
       ROUND(AVG(o.delivery_days), 1) AS avg_delivery_days,
       ROUND(AVG(o.is_delayed) * 100, 1) AS delayed_pct,
       COUNT(*) AS orders
FROM order_features o
WHERE {FILTER} AND o.delivery_days IS NOT NULL
GROUP BY o.customer_state
ORDER BY avg_delivery_days DESC
"""

AVG_DELIVERY = f"""
SELECT ROUND(AVG(o.delivery_days), 1) AS avg_delivery_days
FROM order_features o
WHERE {FILTER} AND o.delivery_days IS NOT NULL
"""

REVIEW_DISTRIBUTION = f"""
SELECT o.review_score, COUNT(*) AS reviews
FROM order_features o
WHERE {FILTER} AND o.review_score IS NOT NULL
GROUP BY o.review_score
ORDER BY o.review_score
"""

REVIEWS_BY_CATEGORY = f"""
SELECT i.category,
       COUNT(*) AS items,
       ROUND(AVG(o.review_score), 2) AS avg_review
FROM item_features i
JOIN order_features o ON i.order_id = o.order_id
WHERE {FILTER} AND o.review_score IS NOT NULL
GROUP BY i.category
HAVING COUNT(*) >= 100
ORDER BY avg_review
LIMIT 15
"""

REVIEW_BY_DELIVERY_TIME = f"""
SELECT CASE WHEN o.delivery_days <= 7  THEN '1. up to 7 days'
            WHEN o.delivery_days <= 14 THEN '2. 8-14 days'
            WHEN o.delivery_days <= 21 THEN '3. 15-21 days'
            ELSE '4. over 21 days' END AS delivery_time,
       COUNT(*) AS orders,
       ROUND(AVG(o.review_score), 2) AS avg_review
FROM order_features o
WHERE {FILTER} AND o.delivery_days IS NOT NULL AND o.review_score IS NOT NULL
GROUP BY delivery_time
ORDER BY delivery_time
"""
