# pgbouncer Integration Guide — AEM-EVOLVE™ v1.5

**Scope:** Connecting `AsyncPostgresAdapter` (asyncpg) through pgbouncer for production workloads.

---

## Why pgbouncer

`AsyncPostgresAdapter` uses `asyncpg.create_pool` with a configurable `min_size` / `max_size`. Under high concurrency, direct PostgreSQL connections are expensive. pgbouncer sits in front of PostgreSQL and multiplexes many application connections onto a small number of server connections.

---

## Recommended mode: transaction pooling

asyncpg works with pgbouncer in **transaction pooling** mode. Statement pooling is not compatible with prepared statements.

```ini
# /etc/pgbouncer/pgbouncer.ini
[databases]
aem_evolve = host=localhost port=5432 dbname=aem_evolve

[pgbouncer]
listen_port  = 6432
listen_addr  = 127.0.0.1
auth_type    = scram-sha-256
auth_file    = /etc/pgbouncer/userlist.txt
pool_mode    = transaction
max_client_conn = 1000
default_pool_size = 20
server_idle_timeout = 600
log_connections = 1
log_disconnections = 1
```

---

## AsyncPostgresAdapter connection string

Point `AsyncPostgresAdapter.create()` at the pgbouncer port:

```python
adapter = await AsyncPostgresAdapter.create(
    dsn="postgresql://aem_user:password@127.0.0.1:6432/aem_evolve",
    min_size=2,
    max_size=10,   # connections to pgbouncer, not directly to PostgreSQL
)
```

---

## asyncpg + pgbouncer: prepared statement caveat

asyncpg uses prepared statements by default. In transaction pooling mode, prepared statements must be disabled:

```python
import asyncpg

async def create_pool_no_ps(dsn: str) -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=dsn,
        statement_cache_size=0,   # disable prepared statement caching
        max_cached_statement_lifetime=0,
    )
```

Or use `AsyncPostgresAdapter.create()` and override pool kwargs:

```python
# Extend AsyncPostgresAdapter for pgbouncer transaction pooling
pool = await asyncpg.create_pool(
    dsn=pgbouncer_dsn,
    min_size=2,
    max_size=10,
    statement_cache_size=0,
)
adapter = AsyncPostgresAdapter(pool)
```

---

## Health check

pgbouncer exposes an admin console on a separate port:

```bash
psql -h 127.0.0.1 -p 6433 -U pgbouncer pgbouncer -c "SHOW POOLS;"
```

`AsyncPostgresAdapter.ping()` (`SELECT 1`) works through pgbouncer in all pool modes.

---

## Non-claims

```
This guide is documentation only — not a production-tested configuration.
pgbouncer version compatibility must be verified for your deployment.
TLS configuration (sslmode, server_tls_*) is not covered here.
```
