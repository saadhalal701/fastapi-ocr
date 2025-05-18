import csv
import io
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, field_validator
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration de la Base de Données MySQL ---
DB_USERNAME = "pfe"
DB_PASSWORD = ""  # Remplacez par le mot de passe MySQL
DB_HOST = "localhost"
DB_PORT = 3307
DB_NAME = "marouni"

DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=1800
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Modèle SQLAlchemy pour les Enregistrements de Péage ---
class EnregistrementPeage(Base):
    __tablename__ = "enregistrements_peage"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plaque_immatriculation = Column(String(50), index=True, nullable=False)
    date_heure_passage = Column(DateTime, index=True, nullable=False)
    id_station_peage = Column(String(100), nullable=False)
    reference_photo = Column(String(255), nullable=True)
    date_enregistrement_db = Column(DateTime, default=datetime.utcnow)

# --- Modèle Pydantic pour création ---
class EnregistrementPeageCreate(BaseModel):
    plaque_immatriculation: str = Field(..., alias="Numéro de plaque")
    date_heure_passage: datetime = Field(..., alias="Heure et date")
    id_station_peage: str = Field(..., alias="ID de la station de péage")
    reference_photo: Optional[str] = Field(None, alias="Photo du véhicule ou de la plaque")

    model_config = {
        "populate_by_name": True,
        "populate_by_alias": True
    }

    @field_validator("date_heure_passage", mode="before")
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            formats = [
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y %H:%M",
                "%d/%m/%Y %H:%M:%S"
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Format de date/heure non supporté: '{v}'")
        return v

# --- Modèle Pydantic pour réponse ---
class EnregistrementPeageResponse(BaseModel):
    id: int
    plaque_immatriculation: str
    date_heure_passage: datetime
    id_station_peage: str
    reference_photo: Optional[str]
    date_enregistrement_db: datetime

    model_config = {"from_attributes": True}

# --- Lifecycle FastAPI ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Création des tables si besoin...")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Arrêt de l'application...")

# --- Application FastAPI ---
app = FastAPI(
    title="API Ingestion Péage CSV",
    version="1.0.0",
    lifespan=lifespan
)

# --- Dépendance DB ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Root endpoint ---
@app.get("/", tags=["Root"] )
async def read_root():
    return {"message": "Bienvenue à l'API d'Ingestion de Péage CSV. Utilisez /upload-csv/ pour poster et /enregistrements/ pour consulter."}

# --- Endpoints ---
@app.post("/upload-csv/", status_code=status.HTTP_201_CREATED, tags=["Ingestion CSV"])
async def upload_csv(
    file: UploadFile = File(..., description="Fichier CSV"),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format CSV.")

    raw = await file.read()
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        text = raw.decode('latin-1', errors='ignore')

    reader = csv.DictReader(io.StringIO(text))
    to_add, errors = [], []
    for idx, row in enumerate(reader, start=2):
        try:
            rec = EnregistrementPeageCreate.parse_obj(row)
            to_add.append(
                EnregistrementPeage(
                    plaque_immatriculation=rec.plaque_immatriculation,
                    date_heure_passage=rec.date_heure_passage,
                    id_station_peage=rec.id_station_peage,
                    reference_photo=rec.reference_photo
                )
            )
        except Exception as e:
            errors.append({"ligne": idx, "erreur": str(e)})

    if to_add:
        try:
            db.add_all(to_add)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Erreur DB: {e}")

    response = {"ajoutés": len(to_add)}
    if errors:
        response["erreurs"] = errors
    return response

@app.get("/enregistrements/", response_model=List[EnregistrementPeageResponse], tags=["Consultation"])
async def get_enregistrements(
    skip: int = 0,
    limit: int = 100,
    plaque: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(EnregistrementPeage)
    if plaque:
        q = q.filter(EnregistrementPeage.plaque_immatriculation.ilike(f"%{plaque}%"))
    return q.order_by(EnregistrementPeage.date_heure_passage.desc()).offset(skip).limit(limit).all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
