from fastapi import FastAPI

app = FastAPI(
    title = "DataInsight Agent",
    description = "A LLM-powered data analysis agent.",
    version = "0.1.0",
)

@app.get("/")
def root():
    return {"message": "DataInsight Agent is running."}

@app.get("/health")
def health_check():
    return {"status": "ok"}