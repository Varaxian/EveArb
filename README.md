<<<<<<< HEAD
# EVE Arb v2.08

This build keeps the working v2.07 base and adds the v2.08 hardening layer:
- CSV export
- scheduler endpoints and optional background scheduler
- route-aware logistics using ESI route jumps
- minimal browser dashboard
=======
# EveArb (EVE Online Market Arbitrage Tool)

## Current Version: v2.08
>>>>>>> dda9f0c17d76fe9c7059302955a72bcaf037cf33

### Overview

EveArb is a market arbitrage scanner for EVE Online using ESI data.
It identifies profitable trade routes between regions while factoring in logistics constraints and route security.

---

## Core Features

### Market Arbitrage Engine

* Identifies buy/sell spreads across regions
* Calculates:

  * Net profit (ISK)
  * Profit per m3
  * ISK per jump

---

### Route Intelligence (v2.07+)

* Route calculation between systems
* Security classification:

  * Highsec only
  * High/Low mix
  * Avoid nullsec
  * Includes nullsec
* Outputs:

  * route_security_profile
  * min_security_on_path
  * max_security_on_path
  * jump count

---

### Filtering (v2.08)

* Route security filtering:

  * `route_security_mode`
* Minimum system security:

  * `min_system_security`
* Logistics constraints:

  * `max_jumps`
  * `max_total_m3`

---

## API Endpoints

### Opportunities

```
/market/opportunities
```

Supports:

* route_security_mode
* min_system_security
* max_jumps
* max_total_m3

---

### Route Calculation

```
/logistics/route
```

---

### Health

```
/health
```

---

## Tech Stack

* FastAPI
* SQLite (dev) / Postgres (prod)
* Redis (planned caching layer)
* Railway (hosting)

---

## Roadmap

### v2.09 (Next)

* Cargo realism:

  * total_m3_available (user setting)
  * total_m3_necessary (per opportunity)
  * fits_cargo
* Profit realism:

  * Broker fees
  * Sales tax
  * Hauling assumptions

### v3

* Multi-user support
* Persistent user settings
* Authentication + SSO
* SaaS-ready architecture

---

## Notes

* This project is actively under development
* Versioning follows semantic-ish increments:

  * Major: v2 → v3
  * Minor: v2.07 → v2.08 → v2.09

---

## Repo

https://github.com/Varaxian/EveArb
