WITH sales AS (
    SELECT
        date,
        store_id,
        item_id,
        department_id,
        category_id,
        SUM(sales) AS total_sales,
        AVG(sell_price) AS avg_price
    FROM {{ source('raw', 'sales') }}
    GROUP BY 1, 2, 3, 4, 5
)

SELECT *
FROM sales
