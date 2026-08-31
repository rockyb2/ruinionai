from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.meetings import router as meetings_router
from database import Base , engine

Base.metadata.create_all(bind=engine)


app = FastAPI(title="RuinionAI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(meetings_router)