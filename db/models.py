from sqlalchemy import Column, Integer, Float, String
from db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class RaportZintegrowany(Base):
    __tablename__ = "raporty_zintegrowane"
    id = Column(Integer, primary_key=True, index=True)
    rok = Column(Integer, index=True)
    gatunek = Column(String, index=True)
    liczba_ptakow_api = Column(Integer)
    parki = Column(Float)
    zielence = Column(Float)
    zielen_uliczna = Column(Float)
    zielen_osiedlowa = Column(Float)
    cmentarze = Column(Float)
    lasy = Column(Float)