-- Compare customer review volume and average rating by product.
-- Results describe reviews, not units sold or revenue.
SELECT
    parent_asin,
    COUNT(*) AS review_count,
    ROUND(AVG(rating), 2) AS average_rating,
    SUM(helpful_vote) AS helpful_votes
FROM read_json_auto('data/raw/All_Beauty.jsonl.gz')
GROUP BY parent_asin
HAVING COUNT(*) >= 20
ORDER BY average_rating DESC, review_count DESC
LIMIT 50;
