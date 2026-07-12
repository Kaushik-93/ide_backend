from typing import Type
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.crud import CRUDBase
from app.database import get_db


def build_crud_router(
    *,
    model,
    create_schema: Type[BaseModel],
    update_schema: Type[BaseModel],
    read_schema: Type[BaseModel],
    prefix: str,
    tags: list[str],
    allow_create: bool = True,
    allow_update: bool = True,
    allow_delete: bool = True,
) -> APIRouter:
    """
    Returns an APIRouter with standard REST endpoints:
      POST   /{prefix}/          create
      GET    /{prefix}/          list (paginated)
      GET    /{prefix}/{id}      get one
      PATCH  /{prefix}/{id}      update   (optional, allow_update)
      DELETE /{prefix}/{id}      delete   (optional, allow_delete)

    Used for every resource that maps 1:1 onto CRUD. Resources with
    special mutation rules (wallets, credit ledger) opt out of
    update/delete here and get dedicated endpoints instead — see
    app/routers/credits.py.
    """
    router = APIRouter(prefix=prefix, tags=tags)
    crud = CRUDBase(model)

    if allow_create:
        @router.post("/", response_model=read_schema, status_code=201)
        def create(obj_in: create_schema, db: Session = Depends(get_db)):
            return crud.create(db, obj_in)

    @router.get("/", response_model=list[read_schema])
    def list_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
        return crud.get_multi(db, skip=skip, limit=limit)

    @router.get("/{id}", response_model=read_schema)
    def get_one(id: UUID, db: Session = Depends(get_db)):
        obj = crud.get(db, id)
        if obj is None:
            raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
        return obj

    if allow_update:
        @router.patch("/{id}", response_model=read_schema)
        def update(id: UUID, obj_in: update_schema, db: Session = Depends(get_db)):
            db_obj = crud.get(db, id)
            if db_obj is None:
                raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
            return crud.update(db, db_obj, obj_in)

    if allow_delete:
        @router.delete("/{id}", status_code=204)
        def delete(id: UUID, db: Session = Depends(get_db)):
            db_obj = crud.get(db, id)
            if db_obj is None:
                raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
            crud.delete(db, db_obj)
            return None

    return router
