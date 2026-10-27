import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import test_firestore, auth, servers, iot, workloads, ai, alerts, reports

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background task
    sync_task = asyncio.create_task(periodic_sync())
    yield
    # Stop background task
    sync_task.cancel()
    try:
        await sync_task
    except asyncio.CancelledError:
        pass

async def periodic_sync():
    while True:
        try:
            await iot.sync_all_thingspeak_devices()
        except Exception as e:
            print(f"Error in periodic_sync: {e}")
        await asyncio.sleep(60)

app = FastAPI(title="IntelliDC API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(test_firestore.router)
app.include_router(auth.router)
app.include_router(servers.router)
app.include_router(iot.router)
app.include_router(workloads.router)
app.include_router(ai.router)
app.include_router(alerts.router)
app.include_router(reports.router)

@app.get("/")
@app.get("/api")
def root():
    return {
        "status": "online",
        "service": "IntelliDC API",
        "documentation": "/docs",
        "health": "/api/health"
    }

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "IntelliDC API"}

