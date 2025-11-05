from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.responses import JSONResponse

# Routers
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.crm import router as crm_router


from fastapi.responses import JSONResponse

# --------------------------------------------------
# FASTAPI APP CONFIG
# --------------------------------------------------
app = FastAPI(
    title="Venu CIMS Table-Based Auth API",
    version="1.0.0",
    description="Table-based SQLAlchemy bilan Auth Sistema",
)



# --------------------------------------------------
# ROUTERS
# --------------------------------------------------
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(crm_router)




@app.get("/")
async def root():
    return {
        "message": "🚀VENU CIMS Table-Based Auth API",
        "approach": "Table-based SQLAlchemy",
        "docs": "/docs",
    }


# --------------------------------------------------
# ENTRYPOINT
# --------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("run:app", host="0.0.0.0", port=8000, reload=True)
