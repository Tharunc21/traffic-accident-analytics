
-- 1. Overall collision severity
SELECT
    collision_severity,
    CASE collision_severity
        WHEN 1 THEN 'Fatal'
        WHEN 2 THEN 'Serious'
        WHEN 3 THEN 'Slight'
        ELSE 'Unknown'
    END AS severity_label,
    COUNT(*) AS total_collisions,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    ) AS percentage
FROM cleaned.collisions
GROUP BY collision_severity
ORDER BY collision_severity;

-- 2. Collision severity by year
SELECT
    collision_year,
    collision_severity,
    COUNT(*) AS total_collisions
FROM cleaned.collisions
GROUP BY collision_year, collision_severity
ORDER BY collision_year, collision_severity;

-- 3. Fatal collisions by year
SELECT
    collision_year,
    COUNT(*) AS fatal_collisions
FROM cleaned.collisions
WHERE collision_severity = 1
GROUP BY collision_year
ORDER BY collision_year;


-- 4. Monthly collision trends
SELECT
    EXTRACT(YEAR FROM date)::INTEGER AS year,
    EXTRACT(MONTH FROM date)::INTEGER AS month,
    COUNT(*) AS total_collisions
FROM cleaned.collisions
WHERE date IS NOT NULL
GROUP BY
    EXTRACT(YEAR FROM date),
    EXTRACT(MONTH FROM date)
ORDER BY year, month;
