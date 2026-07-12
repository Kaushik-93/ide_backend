from typing import Generic, Type, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import Base

ModelT = TypeVar("ModelT", bound=Base)
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)


class CRUDBase(Generic[ModelT, CreateSchemaT, UpdateSchemaT]):
    """
    Generic create/read/update/delete for a single SQLAlchemy model.
    Every resource router builds one of these and reuses the same logic
    instead of hand-writing near-identical query code 14 times.
    """

    def __init__(self, model: Type[ModelT]):
        self.model = model

    def get(self, db: Session, id: UUID) -> ModelT | None:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> list[ModelT]:
        return db.query(self.model).order_by(self.model.id).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: CreateSchemaT) -> ModelT:
        data = obj_in.model_dump()
        # metadata is a reserved attribute name on declarative models;
        # DocumentNode/AuditLog/CreditTransaction map "metadata" (client-
        # facing) onto the "metadata_" python attribute internally.
        if "metadata" in data and hasattr(self.model, "metadata_"):
            data["metadata_"] = data.pop("metadata")
        db_obj = self.model(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: ModelT, obj_in: UpdateSchemaT) -> ModelT:
        data = obj_in.model_dump(exclude_unset=True)
        if "metadata" in data and hasattr(self.model, "metadata_"):
            data["metadata_"] = data.pop("metadata")
        for field, value in data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: ModelT) -> None:
        db.delete(db_obj)
        db.commit()
