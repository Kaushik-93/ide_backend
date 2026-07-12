from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# pool_pre_ping avoids using a dead connection after e.g. Postgres restarts
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a DB session and always closes it,
    even if the request raises.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------
# NOTE on Row-Level Security (see schema.sql section 13/15):
# Most tables have RLS policies keyed off two session variables:
#   app.current_user_id, app.current_org_ids
# The connection you configure in DATABASE_URL right now is almost
# certainly your own Postgres superuser/table-owner account, which
# BYPASSES RLS entirely — that's why plain CRUD works with zero setup.
#
# Once you add real authentication, switch the app's DB role to a
# restricted, non-superuser `app_user` role and set these per-request
# inside a transaction, e.g. as a dependency that runs before each
# request handler:
#
#   def get_db_with_context(user_id: str, org_ids: list[str]):
#       db = SessionLocal()
#       try:
#           db.execute(text("SET LOCAL app.current_user_id = :uid"), {"uid": user_id})
#           db.execute(text("SET LOCAL app.current_org_ids = :oids"), {"oids": ",".join(org_ids)})
#           yield db
#       finally:
#           db.close()
#
# Until auth exists, this file intentionally keeps things simple.
