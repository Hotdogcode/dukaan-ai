# DukaanAI — Application Lifecycle & Request Processing

## 1. Application Startup Sequence

```mermaid
sequenceDiagram
    autonumber
    participant Boot as Uvicorn Worker
    participant Conf as Pydantic Settings
    participant Log as Structured Logging
    participant DB as SQLAlchemy Engine
    participant App as FastAPI App

    Boot->>Conf: Load .env & System Environment
    Conf->>Conf: Execute model_validator (block insecure production secrets)
    Boot->>Log: setup_logging() (Initialize JSON / Text formatters)
    Boot->>DB: create_engine() with connection pool & pre-ping
    Boot->>App: Mount Middlewares & Include Master Routers (/api/v1)
    App->>App: Lifespan startup event executes
    App-->>Boot: Application Ready to accept HTTP traffic
```

### Startup Safety Validations:
- In `production`, `Settings.validate_production_settings()` strictly enforces that `JWT_SECRET_KEY` is not default and $\ge 32$ chars, `OTP_PROVIDER != 'dev'`, and `DEBUG == False`. Any violation aborts startup immediately with a clear error before binding network ports.

---

## 2. Request-Response Lifecycle

Every HTTP request traverses a standardized lifecycle pipeline:

```mermaid
flowchart TD
    Req[Incoming HTTP Request] --> M1[RequestCorrelationMiddleware<br/>Extract or generate X-Request-ID<br/>Set ContextVars & Start Timer]
    M1 --> M2[CORSMiddleware<br/>Validate Origin & Headers]
    M2 --> Router[FastAPI Master Router]
    
    Router --> Dep1[get_current_user<br/>Decode JWT & Verify RefreshSession liveness]
    Dep1 --> Dep2[get_tenant_membership<br/>Verify User is active in business_id<br/>Execute SET LOCAL app.current_tenant_id]
    Dep2 --> Dep3[require_permission<br/>Assert Role has required permission]
    
    Dep3 --> Handler[Route Endpoint / Application Service]
    Handler --> DB[(PostgreSQL with RLS)]
    
    Handler --> Resp[Generate Response / DTO]
    Resp --> M1Resp[Append X-Request-ID Header<br/>Log Structured JSON Record]
    M1Resp --> Out[HTTP Response]
    
    Handler -.->|Exception Raised| ErrH[Global Exception Handler<br/>Format Standard Error Envelope<br/>Scrub Stack Traces in Production]
    ErrH --> M1Resp
```

---

## 3. Shutdown Sequence

When receiving `SIGTERM` or `SIGINT` (e.g. during rolling Kubernetes deployment):
1. **Liveness/Readiness Signals**: Stop accepting new traffic on `/ready`.
2. **Grace Period**: Drain inflight HTTP transactions within standard 30-second window.
3. **Connection Pool Disposal**: SQLAlchemy `engine.dispose()` closes all idle and active PostgreSQL pool connections.
4. **Log Flush**: Emits structured `"Shutting down DukaanAI Backend"` log record.
