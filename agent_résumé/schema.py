from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Utilisateur(BaseModel):
    nom: str
    prenom: str
    email: str
    mdp : str
    

class Meeting(BaseModel):
    meeting_id: int
    title: str
    transcription: str
    summary: Optional[str] = None
    date_created: str
    
class MeetingCreate(BaseModel):
    title: str
    participants: Optional[List[str]] = None
    
    
class MeetingRead(BaseModel):
    id: int
    title: str
    transcription: Optional[str] = None
    summary: Optional[str] = None
    participants: Optional[str] = None
    date: datetime

    class Config:
        from_attributes = True