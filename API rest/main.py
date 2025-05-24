import csv
import io
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
import logging
import os
import uvicorn

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Database Config ---
DB_USERNAME = "root"
DB_PASSWORD = ""
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "projet"

DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=1800
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELS ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100))
    matricule = Column(String(50), unique=True, index=True)

   # ocr_results = relationship("ResultatOCR", back_populates="user")

class EnregistrementPeage(Base):
    __tablename__ = "enregistrements_peage"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plaque_immatriculation = Column(String(50), index=True, nullable=False)
    date_heure_passage = Column(DateTime, index=True, nullable=False)
    id_station_peage = Column(String(100), nullable=False)
    reference_photo = Column(String(255), nullable=True)
    date_enregistrement_db = Column(DateTime, default=datetime.utcnow)

class ResultatOCR(Base):
    __tablename__ = "resultats_ocr"

    id = Column(Integer, primary_key=True, index=True)
    matricule = Column(String(50), index=True, nullable=False)
    date_detection = Column(DateTime, nullable=False)
    nom_station = Column(String(100), nullable=False)
    montant = Column(Integer, nullable=True)
    chemin_photo = Column(String(255), nullable=True)
    chemin_image_ocr = Column(String(255), nullable=True)
    date_insertion = Column(DateTime, default=datetime.utcnow)


# --- SCHEMAS ---

class EnregistrementPeageCreate(BaseModel):
    plaque_immatriculation: str
    date_heure_passage: datetime
    id_station_peage: str
    reference_photo: Optional[str] = None

class EnregistrementPeageResponse(BaseModel):
    id: int
    plaque_immatriculation: str
    date_heure_passage: datetime
    id_station_peage: str
    reference_photo: Optional[str] = None
    date_enregistrement_db: datetime

class ResultatOCRCreate(BaseModel):
    matricule: str
    date_detection: datetime
    nom_station: str
    montant: Optional[int] = None 
    chemin_photo: Optional[str] = None
    chemin_image_ocr: Optional[str] = None

class ResultatOCRResponse(BaseModel):
    id: int
    matricule: str
    date_detection: datetime
    nom_station: str
    montant: Optional[int] = None 
    chemin_photo: Optional[str] = None
    chemin_image_ocr: Optional[str] = None
    date_insertion: datetime
   # user_id: Optional[int] = None

# --- Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating tables...")
    Base.metadata.create_all(bind=engine)

    # Initial OCR CSV import
    try:
        db = SessionLocal()
        chemin_csv = r"C:\Users\dell\OneDrive\Bureau\plates - Copie\ocr_results.csv"
        importer_csv_ocr_initial(chemin_csv, db)
    except Exception as e:
        logger.error(f"Initial OCR CSV import error: {e}")
    finally:
        db.close()

    yield
    logger.info("Shutting down...")

# --- FastAPI App ---
app = FastAPI(
    title="API Ingestion Péage & OCR",
    version="1.1.0",
    lifespan=lifespan
)

# --- Dependencies ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Routes ---

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bienvenue à l'API d'Ingestion (péage & OCR)."}

@app.post("/upload-csv/", status_code=status.HTTP_201_CREATED, tags=["Péage"])
async def upload_csv(
    file: UploadFile = File(..., description="Fichier CSV pour les péages"),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format CSV.")

    try:
        contents = await file.read()
        text = contents.decode('utf-8')
    except UnicodeDecodeError:
        text = contents.decode('latin-1', errors='ignore')

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

    return {"ajoutés": len(to_add), "erreurs": errors if errors else None}

@app.get("/enregistrements/", response_model=List[EnregistrementPeageResponse], tags=["Péage"])
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

@app.post("/import-ocr-csv/", status_code=status.HTTP_201_CREATED, tags=["OCR"])
async def import_ocr_csv(
    file: UploadFile = File(..., description="Fichier CSV OCR"),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un CSV.")

    try:
        contents = await file.read()
        text = contents.decode("utf-8")
    except UnicodeDecodeError:
        text = contents.decode("latin-1", errors="ignore")

    reader = csv.DictReader(io.StringIO(text))
    to_add, errors = [], []

    for idx, row in enumerate(reader, start=2):
        try:
            mapped_row = {
            "matricule": row["PlateNumber"],
            "date_detection": row["Date"],
            "nom_station": row["Station"],
            "chemin_photo": row["Image"],
            "chemin_image_ocr": row["PlateImage"]
        }
            rec = ResultatOCRCreate.parse_obj(mapped_row)
            montant = 23 if rec.nom_station.lower() == "station paris" else 30 if rec.nom_station.lower() == "station marseille" else None

            to_add.append(
                ResultatOCR(
                    matricule=rec.matricule,
                    date_detection=rec.date_detection,
                    nom_station=rec.nom_station,
                    montant=montant,
                    chemin_photo=rec.chemin_photo,
                    chemin_image_ocr=rec.chemin_image_ocr
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

    return {"ajoutés": len(to_add), "erreurs": errors if errors else None}

@app.get("/resultats-ocr/", response_model=List[ResultatOCRResponse], tags=["OCR"])
async def get_resultats_ocr(
    skip: int = 0,
    limit: int = 100,
    matricule: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(ResultatOCR)
    if matricule:
        q = q.filter(ResultatOCR.matricule.ilike(f"%{matricule}%"))
    return q.order_by(ResultatOCR.date_detection.desc()).offset(skip).limit(limit).all()

# --- Helper Functions ---

def importer_csv_ocr_initial(path: str, db: Session):
    if not os.path.exists(path):
        logger.warning(f"Fichier OCR introuvable : {path}")
        return

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        to_add = []
        for idx, row in enumerate(reader, start=2):
            try:
                mapped_row = {
                    "matricule": row["PlateNumber"],
                    "date_detection": row["Date"],
                    "nom_station": row["Station"],
                    "montant":row["Montant"],
                    "chemin_photo": row["Image"],
                    "chemin_image_ocr": row["PlateImage"]
                }
                rec = ResultatOCRCreate.parse_obj(mapped_row)
                existe = db.query(ResultatOCR).filter_by(
                    matricule=rec.matricule,
                    date_detection=rec.date_detection
                ).first()
                montant = 23 if rec.nom_station.lower() == "station paris" else 30 if rec.nom_station.lower() == "station marseille" else None

                if not existe:

                    to_add.append(ResultatOCR(
                        matricule=rec.matricule,
                        date_detection=rec.date_detection,
                        nom_station=rec.nom_station,
                        montant=montant,
                        chemin_photo=rec.chemin_photo,
                        chemin_image_ocr=rec.chemin_image_ocr
                    ))
                else:
                    existe.nom_station = rec.nom_station
                    existe.chemin_photo = rec.chemin_photo
                    existe.chemin_image_ocr = rec.chemin_image_ocr
                    existe.montant = montant
                    db.add(existe)
            except Exception as e:
                logger.warning(f"Ligne {idx} ignorée : {e}")
        if to_add:
            db.add_all(to_add)
            db.commit()
            logger.info(f"{len(to_add)} lignes OCR ajoutées depuis le CSV initial.")
        else:
            logger.info("Aucune nouvelle donnée OCR à ajouter.")
            
@app.post("/ajouter-ocr", response_model=ResultatOCRResponse, tags=["OCR"])
async def ajouter_resultat_ocr(
    data: ResultatOCRCreate,
    db: Session = Depends(get_db)
):
    try:
        montant = 23 if data.nom_station.lower() == "station paris" else 30 if data.nom_station.lower() == "station marseille" else None

        nouveau_resultat = ResultatOCR(
            matricule=data.matricule,
            date_detection=data.date_detection,
            nom_station=data.nom_station,
            montant=montant,
            chemin_photo=data.chemin_photo,
            chemin_image_ocr=data.chemin_image_ocr
        )

        db.add(nouveau_resultat)
        db.commit()
        db.refresh(nouveau_resultat)

        return nouveau_resultat

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement OCR: {e}")


# --- Main ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)