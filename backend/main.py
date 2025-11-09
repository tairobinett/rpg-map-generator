from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow your React app to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000/"],  # React default port
    allow_credentials=True,
    allow_methods=[""],
    allow_headers=[""],
)

@app.get("/hello")
def hello_world():
    return {"message": "Hello World!"}