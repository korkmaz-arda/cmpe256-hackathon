# CMPE 256 Hackathon: Agentic AI Management Consulting Platform

A Management Consulting **Manager Agent** that routes customer questions to four grounded specialist agents
(Technology, Clinical, SEC, Corporate Responsibility), plus an optional Market Basket checkout recommender.

See [RUBRIC.md](RUBRIC.md) for the requirements confirmed with the professor.

## Data setup

The course data isn't committed (this repo is public). Unzip the Canvas zips into `data/`:

```
data/Clinical/        <- Clinical.zip
data/SEC/             <- UnitedStatesSecuritiesandExchangeCommission(SEC).zip (rename the folder to SEC)
data/FoodSecurity/    <- FoodSecurity.zip
data/Retail/          <- Retail.zip
```

The web sources (Cisco datasheets, Agilent pages, GCP pages) are listed in `sources/*.txt`.
