# Microsoft Fabric — Data Engineering Pipelines

## One-line summary
Two data engineering pipelines built on Microsoft Fabric using the Bronze-Silver-Gold Medallion architecture — one processing HR analytics data at Hosho Digital, one independently analyzing 7.7 million rows of real US traffic accident data (2016-2023) — both feeding star-schema Power BI dashboards.

## Project Ranking
Rated 7.5/10 by Anas. Strong real-world data engineering work — two independent Medallion-architecture pipelines, one on a genuine 7.7M-row dataset with a full star-schema Power BI dashboard. Best example of his data engineering skill specifically, distinct from his AI/agentic project work.

## Problem / context
Raw operational data (HR records, traffic incident logs) isn't directly usable for analytics — it needs staged cleansing, transformation, and modeling before it can support reliable dashboards and decision-making. The Medallion architecture solves this by separating raw ingestion, cleansing, and business-ready modeling into distinct layers rather than doing it all in one messy transformation step.

## Architecture
**Bronze layer** — raw data ingested as-is, zero transformations, saved as a Delta table in a Fabric Lakehouse, preserving an untouched copy for auditability/reprocessing.
**Silver layer** — cleansing and feature engineering: dropping unreliable columns, imputing missing values, deriving new features from raw fields, running explicit data-quality validation before promotion to Gold.
**Gold layer** — star-schema modeling (one fact table + multiple dimension tables linked via surrogate keys) optimized for query performance, feeding Power BI directly.
**Power BI** — interactive multi-page dashboards on top of the Gold layer, with custom DAX measures.

## Tech stack
Microsoft Fabric, PySpark, Delta Lake, Dataflow Gen2, Power Query, Lakehouse, Power BI, DAX, star-schema data modeling.

## Key decisions & why
- **Medallion architecture (Bronze-Silver-Gold) over a single-stage ETL** — separating raw/cleansed/modeled layers means a mistake in transformation logic doesn't corrupt the source data, and each layer can be reprocessed independently without re-ingesting from scratch.
- **Star schema in the Gold layer with surrogate keys** — fact table stores only foreign keys pointing to dimension tables instead of repeating text values millions of times across rows, which keeps the model efficient and DAX queries fast even at 7.7M-row scale.
- **Explicit data-quality gate before Gold promotion** — rather than assuming Silver-layer cleaning worked, ran dedicated validation checks (duplicates, nulls, invalid values, bad coordinates) across all 7.7M rows before allowing data into the Gold layer — a real production-style quality gate, not just "clean and hope."
- **Applying the same pattern to a second, independent, much larger dataset** — deliberately done to prove the Bronze-Silver-Gold pattern wasn't a one-off learned for a single internship task, but a data engineering approach applied by choice on a real, large, messy public dataset.

## Two implementations of this pattern

### 1. HR Analytics Pipeline (Hosho Digital internship)
Built as part of the Hosho Digital internship. Ingested HR data via Dataflow Gen2, cleansed through Power Query, modeled into a Gold-layer star schema, and surfaced via interactive Power BI dashboards for HR-related business metrics.

### 2. US Traffic Accidents Pipeline (independent project)
Built independently, applying the identical Medallion pattern via PySpark notebooks to a real-world dataset of **7.7 million rows and 46 columns**, covering US traffic accidents from **2016 to 2023**.

**Bronze:** Raw CSV ingested directly into a Fabric Lakehouse via PySpark with zero transformations, saved as a Delta table.

**Silver:** Dropped columns with heavy nulls (e.g. Wind Chill, Precipitation), imputed missing numeric values using the median, and engineered new features from raw timestamps — Year, Month, Hour, Weekday, Season — plus converted numeric severity scores into readable labels (Low/Medium/High/Critical) and calculated accident duration in minutes. Ran **8 explicit data-quality checks** (duplicates, nulls, invalid values, bad coordinates) — all passed cleanly across the full 7.7M rows before Gold promotion.

**Gold:** One fact table (`fact_accidents`) holding core measurements, linked via surrogate keys to **five dimension tables**: Date, Location, Weather Condition, Road Feature, and Severity — a proper star schema, visualized and connected via one-to-many relationships in the Power BI model view.

**Dashboard:** Six-page Power BI report — Executive Summary, Time Analysis, Location Analysis, Weather Analysis, Road Feature Analysis, and Severity Analysis — powered by DAX measures including Total Accidents, Average Severity, and Average Distance.

## Real findings from the dashboard (usable in conversation, not just architecture talk)
- 7.7 million total accidents across 49 states and roughly 14,000 cities; average severity 2.21.
- Accident volume grew steadily from 2016 to 2022, with clear rush-hour peaks around 7-9 AM and 3-6 PM.
- California, Florida, and Texas lead in raw accident counts — consistent with population and traffic volume rather than an anomaly.
- Most accidents occur in fair or cloudy weather, simply because those conditions are most common, not because they're riskier.
- Most accidents occur where road features like signals or junctions are *absent*, suggesting open-road incidents dominate over intersection-related ones.
- Nearly 80% of accidents fall in the "Medium" severity band, broken down further by state, weather, and time of day.

## Challenges & fixes
- **Heavy-null columns skewing the dataset** — columns like Wind Chill and Precipitation had enough missing data to be unreliable; rather than trying to impute them, they were dropped outright, while other numeric fields were imputed with the median instead of a more naive fill.
- **Validating quality at scale before Gold promotion** — with 7.7M rows, quality issues (bad coordinates, duplicates, invalid values) can't be manually spot-checked; built explicit automated checks covering all 8 categories across the full dataset before allowing promotion to the Gold layer.
- **Keeping the Gold layer performant at scale** — solved primarily through proper star-schema design (surrogate keys, fact/dimension separation) rather than a flat denormalized table, which is what keeps DAX measures fast over millions of rows.

## Results / metrics
7.7 million rows, 46 source columns, spanning 2016-2023. 8/8 data quality checks passed across the full dataset. 5-dimension star schema in Gold. 6-page Power BI dashboard with multiple DAX measures. Findings cover 49 states and ~14,000 cities.

## Presentation note
Recorded a ~6 minute walkthrough video covering the full pipeline (Bronze → Silver → Gold → Power BI model → dashboard tour) for the Hosho internship submission — good source material if you want to reuse framing/pacing for interview talking points or a future AskAnas answer script.
