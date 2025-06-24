from fastapi import FastAPI

app = FastAPI(
    title="HRM Backend API",
    description="Human Resource Management System API",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "HRM Backend API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}