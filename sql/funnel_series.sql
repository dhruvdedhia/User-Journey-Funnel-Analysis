SELECT
    event,
    COUNT(DISTINCT user_id) AS users
FROM events
GROUP BY events
GROUP BY users DESC;

-- 2. Drop-off between stages
SELECT
    event,
    COUNT(DISTINCT user_id) AS users,
    ROUND(
        100.0 * COUNT(DISTINCT user_id) /
        MAX(COUNT(DISTINCT user_id)) OVER (), 1
    ) AS pct_of_total
FROM events
GROUP BY event
ORDER BY users DESC;

-- 3. Funnel segmented by device
SELECT
    device,
    event,
    COUNT(DISTINCT user_id) AS users
FROM events
GROUP BY device, event
ORDER BY device, users DESC;

-- 4. Funnel segmented by traffic source
SELECT
    traffic_source,
    event,
    COUNT(DISTINCT user_id) AS users
FROM events
GROUP BY traffic_source, event
ORDER BY traffic_source, users DESC;

-- 5. Funnel segmented by location
SELECT
    location,
    event,
    COUNT(DISTINCT user_id) AS users
FROM events
GROUP BY location, event
ORDER BY location, users DESC;

-- 6. Daily funnel trend
SELECT
    date,
    event,
    COUNT(DISTINCT user_id) AS users
FROM events
GROUP BY date, event
ORDER BY date, event;

-- 8. Conversion by hour of day
SELECT
    hour,
    event,
    COUNT(DISTINCT user_id) AS users
FROM events
GROUP BY hour, event
ORDER BY hour, event;

