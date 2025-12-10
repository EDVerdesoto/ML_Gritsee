from fastapi import FastAPI

app = FastAPI(title="API Control Calidad Pizzas", version="1.0.0")

@app.get("/")
def read_root():
    return {"mensaje": "Sistema de Inspección de Pizzas - ONLINE 🍕🚀"}

@app.get("/health")
def health_check():
    return {"status": "ok"}