from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import Float, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint, create_engine, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class AccountState(Base):
    __tablename__ = "account_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    server: Mapped[str] = mapped_column(String(16), default="NA")
    data_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    builds_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    achievements_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    stickerbook_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    ww_builds_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    data_mtime: Mapped[float | None] = mapped_column(Float, nullable=True)
    ww_mtime: Mapped[float | None] = mapped_column(Float, nullable=True)
    item_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    character_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parse_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_last_update: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    ww_source_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_iasync_lua: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    raw_ww_lua: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    last_ingested_at: Mapped[float] = mapped_column(Float, default=lambda: time.time())
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    primary_sessions: Mapped[list["WorkspaceSession"]] = relationship(
        foreign_keys="WorkspaceSession.primary_account_id",
        overlaps="primary_account",
    )
    shadow_sessions: Mapped[list["WorkspaceSession"]] = relationship(
        foreign_keys="WorkspaceSession.shadow_account_id",
        overlaps="shadow_account",
    )
    share_codes: Mapped[list["AccountShareCode"]] = relationship(back_populates="account")


class WorkspaceSession(Base):
    __tablename__ = "workspace_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    primary_account_id: Mapped[int | None] = mapped_column(ForeignKey("account_states.id"), nullable=True, index=True)
    shadow_account_id: Mapped[int | None] = mapped_column(ForeignKey("account_states.id"), nullable=True, index=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("account_states.id"), nullable=True, index=True)
    active_slot: Mapped[str] = mapped_column(String(16), default="primary")
    last_active: Mapped[float] = mapped_column(Float, default=lambda: time.time(), index=True)
    encrypted_api_key: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    primary_account: Mapped[AccountState | None] = relationship(
        foreign_keys=[primary_account_id],
        overlaps="primary_sessions",
    )
    shadow_account: Mapped[AccountState | None] = relationship(
        foreign_keys=[shadow_account_id],
        overlaps="shadow_sessions",
    )


class AccountShareCode(Base):
    __tablename__ = "account_share_codes"

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account_states.id"), index=True)
    created_at: Mapped[float] = mapped_column(Float, default=lambda: time.time())
    updated_at: Mapped[float] = mapped_column(Float, default=lambda: time.time())

    account: Mapped[AccountState] = relationship(back_populates="share_codes")


class BuildExport(Base):
    __tablename__ = "build_exports"

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    account_name: Mapped[str] = mapped_column(String(255), index=True)
    character_id: Mapped[str] = mapped_column(String(255), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[float] = mapped_column(Float, default=lambda: time.time())
    updated_at: Mapped[float] = mapped_column(Float, default=lambda: time.time())


class ImportedBuild(Base):
    __tablename__ = "imported_builds"
    __table_args__ = (
        UniqueConstraint("workspace_session_id", "account_name", "character_id", name="ux_imported_build_slot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_session_id: Mapped[str] = mapped_column(String(64), index=True)
    account_name: Mapped[str] = mapped_column(String(255), index=True)
    character_id: Mapped[str] = mapped_column(String(255), index=True)
    build_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    exported_from_account: Mapped[str | None] = mapped_column(String(255), nullable=True)
    exported_from_character_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[float] = mapped_column(Float, default=lambda: time.time())
    updated_at: Mapped[float] = mapped_column(Float, default=lambda: time.time())


@dataclass
class AccountPayload:
    account_name: str
    server: str
    data_bytes: bytes | None = None
    builds_bytes: bytes | None = None
    achievements_bytes: bytes | None = None
    stickerbook_bytes: bytes | None = None
    ww_builds_bytes: bytes | None = None
    data_mtime: float | None = None
    ww_mtime: float | None = None
    item_count: int | None = None
    character_count: int | None = None
    parse_ms: int | None = None
    source_last_update: int | None = None
    source_path: str | None = None
    ww_source_path: str | None = None
    raw_iasync_lua: bytes | None = None
    raw_ww_lua: bytes | None = None
    last_error: str | None = None


_ENGINE = None
_SESSION_MAKER: sessionmaker | None = None
SlotName = Literal["primary", "shadow"]


def init_db(database_url: str) -> None:
    global _ENGINE, _SESSION_MAKER
    if _ENGINE is not None:
        return
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite:") else {}
    _ENGINE = create_engine(database_url, future=True, connect_args=connect_args)
    _SESSION_MAKER = sessionmaker(_ENGINE, expire_on_commit=False, future=True)
    Base.metadata.create_all(_ENGINE)
    _ensure_schema_columns(_ENGINE)


def _ensure_schema_columns(engine) -> None:
    cols = {col["name"] for col in inspect(engine).get_columns("account_states")}
    ddl = []
    if "raw_iasync_lua" not in cols:
        ddl.append("ALTER TABLE account_states ADD COLUMN raw_iasync_lua BLOB")
    if "raw_ww_lua" not in cols:
        ddl.append("ALTER TABLE account_states ADD COLUMN raw_ww_lua BLOB")
    sess_cols = {col["name"] for col in inspect(engine).get_columns("workspace_sessions")}
    if "primary_account_id" not in sess_cols:
        ddl.append("ALTER TABLE workspace_sessions ADD COLUMN primary_account_id INTEGER")
    if "shadow_account_id" not in sess_cols:
        ddl.append("ALTER TABLE workspace_sessions ADD COLUMN shadow_account_id INTEGER")
    if "active_slot" not in sess_cols:
        ddl.append("ALTER TABLE workspace_sessions ADD COLUMN active_slot TEXT DEFAULT 'primary'")
    if "encrypted_api_key" not in sess_cols:
        ddl.append("ALTER TABLE workspace_sessions ADD COLUMN encrypted_api_key BLOB")
    if not ddl and "account_id" not in sess_cols:
        return
    with engine.begin() as conn:
        for stmt in ddl:
            conn.execute(text(stmt))
        if "account_id" in sess_cols:
            conn.execute(text("""
                UPDATE workspace_sessions
                SET primary_account_id = COALESCE(primary_account_id, account_id),
                    active_slot = COALESCE(active_slot, 'primary')
                WHERE account_id IS NOT NULL
            """))


@contextmanager
def session_scope():
    if _SESSION_MAKER is None:
        raise RuntimeError("database not initialized")
    db: Session = _SESSION_MAKER()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_account_state(account_name: str) -> AccountState | None:
    with session_scope() as db:
        return db.scalar(select(AccountState).where(AccountState.account_name == account_name))


def _normalize_slot(slot: str | None) -> SlotName:
    return "shadow" if slot == "shadow" else "primary"


def _slot_account(row: WorkspaceSession, slot: SlotName) -> AccountState | None:
    return row.shadow_account if slot == "shadow" else row.primary_account


def get_workspace_binding(session_id: str) -> dict:
    with session_scope() as db:
        session_row = db.get(WorkspaceSession, session_id)
        if not session_row:
            return {"primary_account": None, "shadow_account": None, "active_slot": "primary"}
        session_row.last_active = time.time()
        active_slot = _normalize_slot(session_row.active_slot)
        return {
            "primary_account": session_row.primary_account.account_name if session_row.primary_account else None,
            "shadow_account": session_row.shadow_account.account_name if session_row.shadow_account else None,
            "active_slot": active_slot,
        }


def get_account_state_for_session(session_id: str, slot: str | None = None) -> AccountState | None:
    with session_scope() as db:
        session_row = db.get(WorkspaceSession, session_id)
        if not session_row:
            return None
        session_row.last_active = time.time()
        target_slot = _normalize_slot(slot or session_row.active_slot)
        account = _slot_account(session_row, target_slot)
        if account is not None:
            return account
        if target_slot == "shadow" and session_row.primary_account is not None:
            return session_row.primary_account
        return session_row.primary_account


def bind_session(session_id: str, account_name: str | None, slot: str = "primary", *, make_active: bool = True) -> None:
    with session_scope() as db:
        row = db.get(WorkspaceSession, session_id)
        if row is None:
            row = WorkspaceSession(session_id=session_id)
            db.add(row)
        row.last_active = time.time()
        target_slot = _normalize_slot(slot)
        if account_name is None:
            if target_slot == "shadow":
                row.shadow_account = None
            else:
                row.primary_account = None
        else:
            account = db.scalar(select(AccountState).where(AccountState.account_name == account_name))
            if account is None:
                account = AccountState(account_name=account_name)
                db.add(account)
                db.flush()
            if target_slot == "shadow":
                row.shadow_account = account
            else:
                row.primary_account = account
        if make_active:
            row.active_slot = target_slot
        if row.active_slot == "shadow" and row.shadow_account is None:
            row.active_slot = "primary"


def set_active_slot(session_id: str, slot: str) -> bool:
    with session_scope() as db:
        row = db.get(WorkspaceSession, session_id)
        if row is None:
            return False
        row.last_active = time.time()
        target_slot = _normalize_slot(slot)
        account = _slot_account(row, target_slot)
        if account is None:
            return False
        row.active_slot = target_slot
        return True


def touch_session(session_id: str) -> None:
    with session_scope() as db:
        row = db.get(WorkspaceSession, session_id)
        if row is None:
            row = WorkspaceSession(session_id=session_id, last_active=time.time())
            db.add(row)
        else:
            row.last_active = time.time()


def session_slot_for_account(session_id: str, account_name: str) -> SlotName | None:
    with session_scope() as db:
        row = db.get(WorkspaceSession, session_id)
        if row is None:
            return None
        row.last_active = time.time()
        if row.primary_account and row.primary_account.account_name == account_name:
            return "primary"
        if row.shadow_account and row.shadow_account.account_name == account_name:
            return "shadow"
        return None


def delete_shadow_slot(session_id: str) -> tuple[str | None, bool]:
    with session_scope() as db:
        row = db.get(WorkspaceSession, session_id)
        if row is None or row.shadow_account is None:
            return None, False
        account = row.shadow_account
        account_name = account.account_name
        row.shadow_account = None
        row.last_active = time.time()
        if _normalize_slot(row.active_slot) == "shadow":
            row.active_slot = "primary"

        still_referenced = db.scalar(select(WorkspaceSession).where(
            (WorkspaceSession.primary_account_id == account.id) | (WorkspaceSession.shadow_account_id == account.id)
        )) is not None
        has_share = db.scalar(select(AccountShareCode).where(AccountShareCode.account_id == account.id)) is not None
        if still_referenced or has_share:
            return account_name, False
        db.delete(account)
        return account_name, True


def find_session_for_account(account_name: str) -> str | None:
    with session_scope() as db:
        account = db.scalar(select(AccountState).where(AccountState.account_name == account_name))
        if account is None:
            return None
        row = db.scalar(select(WorkspaceSession).where(
            (WorkspaceSession.primary_account_id == account.id) | (WorkspaceSession.shadow_account_id == account.id)
        ))
        return row.session_id if row else None


def upsert_account_payload(payload: AccountPayload) -> None:
    with session_scope() as db:
        row = db.scalar(select(AccountState).where(AccountState.account_name == payload.account_name))
        if row is None:
            row = AccountState(account_name=payload.account_name)
            db.add(row)
        row.server = payload.server
        if payload.data_bytes is not None:
            row.data_bytes = payload.data_bytes
        if payload.builds_bytes is not None:
            row.builds_bytes = payload.builds_bytes
        if payload.achievements_bytes is not None:
            row.achievements_bytes = payload.achievements_bytes
        if payload.stickerbook_bytes is not None:
            row.stickerbook_bytes = payload.stickerbook_bytes
        if payload.ww_builds_bytes is not None:
            row.ww_builds_bytes = payload.ww_builds_bytes
        if payload.data_mtime is not None:
            row.data_mtime = payload.data_mtime
        if payload.ww_mtime is not None:
            row.ww_mtime = payload.ww_mtime
        if payload.item_count is not None:
            row.item_count = payload.item_count
        if payload.character_count is not None:
            row.character_count = payload.character_count
        if payload.parse_ms is not None:
            row.parse_ms = payload.parse_ms
        if payload.source_last_update is not None:
            row.source_last_update = payload.source_last_update
        if payload.source_path is not None:
            row.source_path = payload.source_path
        if payload.ww_source_path is not None:
            row.ww_source_path = payload.ww_source_path
        if payload.raw_iasync_lua is not None:
            row.raw_iasync_lua = payload.raw_iasync_lua
        if payload.raw_ww_lua is not None:
            row.raw_ww_lua = payload.raw_ww_lua
        row.last_error = payload.last_error
        row.last_ingested_at = time.time()


def update_account_blobs(account_name: str, *, achievements_bytes: bytes | None = None, stickerbook_bytes: bytes | None = None) -> None:
    with session_scope() as db:
        row = db.scalar(select(AccountState).where(AccountState.account_name == account_name))
        if row is None:
            raise KeyError(account_name)
        if achievements_bytes is not None:
            row.achievements_bytes = achievements_bytes
        if stickerbook_bytes is not None:
            row.stickerbook_bytes = stickerbook_bytes
        row.last_ingested_at = time.time()


def get_or_create_share_code(code: str, account_name: str) -> None:
    with session_scope() as db:
        account = db.scalar(select(AccountState).where(AccountState.account_name == account_name))
        if account is None:
            raise KeyError(account_name)
        row = db.get(AccountShareCode, code)
        if row is None:
            db.add(AccountShareCode(code=code, account=account))
            return
        row.account = account
        row.updated_at = time.time()


def find_share_code_for_account(account_name: str) -> str | None:
    with session_scope() as db:
        account = db.scalar(select(AccountState).where(AccountState.account_name == account_name))
        if account is None:
            return None
        row = db.scalar(select(AccountShareCode).where(AccountShareCode.account_id == account.id))
        return row.code if row else None


def resolve_account_for_share_code(code: str) -> str | None:
    with session_scope() as db:
        row = db.get(AccountShareCode, code)
        if row is None or row.account is None:
            return None
        row.updated_at = time.time()
        return row.account.account_name


def upsert_build_export(code: str, account_name: str, character_id: str, payload_json: str) -> None:
    with session_scope() as db:
        row = db.get(BuildExport, code)
        if row is None:
            db.add(BuildExport(
                code=code,
                account_name=account_name,
                character_id=character_id,
                payload_json=payload_json,
            ))
            return
        row.account_name = account_name
        row.character_id = character_id
        row.payload_json = payload_json
        row.updated_at = time.time()


def upsert_build_export_for_character(
    code: str,
    account_name: str,
    character_id: str,
    payload_json: str,
) -> str:
    """Ensure a single export row per account+character and return its code."""
    with session_scope() as db:
        rows = db.scalars(select(BuildExport).where(
            BuildExport.account_name == account_name,
            BuildExport.character_id == character_id,
        ).order_by(BuildExport.created_at.asc())).all()
        if not rows:
            db.add(BuildExport(
                code=code,
                account_name=account_name,
                character_id=character_id,
                payload_json=payload_json,
            ))
            return code

        keep = rows[0]
        keep.payload_json = payload_json
        keep.updated_at = time.time()
        for extra in rows[1:]:
            db.delete(extra)
        return keep.code


def resolve_build_export(code: str) -> dict | None:
    with session_scope() as db:
        row = db.get(BuildExport, code)
        if row is None:
            return None
        row.updated_at = time.time()
        return {
            "code": row.code,
            "account_name": row.account_name,
            "character_id": row.character_id,
            "payload_json": row.payload_json,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }


def upsert_imported_build(
    *,
    workspace_session_id: str,
    account_name: str,
    character_id: str,
    build_name: str | None,
    source_code: str | None,
    exported_from_account: str | None,
    exported_from_character_id: str | None,
    payload_json: str,
) -> None:
    with session_scope() as db:
        row = db.scalar(select(ImportedBuild).where(
            ImportedBuild.workspace_session_id == workspace_session_id,
            ImportedBuild.account_name == account_name,
            ImportedBuild.character_id == character_id,
        ))
        if row is None:
            db.add(ImportedBuild(
                workspace_session_id=workspace_session_id,
                account_name=account_name,
                character_id=character_id,
                build_name=build_name,
                source_code=source_code,
                exported_from_account=exported_from_account,
                exported_from_character_id=exported_from_character_id,
                payload_json=payload_json,
            ))
            return
        row.build_name = build_name
        row.source_code = source_code
        row.exported_from_account = exported_from_account
        row.exported_from_character_id = exported_from_character_id
        row.payload_json = payload_json
        row.updated_at = time.time()


def list_imported_builds(workspace_session_id: str, account_name: str) -> list[dict]:
    with session_scope() as db:
        rows = db.scalars(select(ImportedBuild).where(
            ImportedBuild.workspace_session_id == workspace_session_id,
            ImportedBuild.account_name == account_name,
        )).all()
        return [{
            "character_id": row.character_id,
            "build_name": row.build_name,
            "source_code": row.source_code,
            "exported_from_account": row.exported_from_account,
            "exported_from_character_id": row.exported_from_character_id,
            "payload_json": row.payload_json,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        } for row in rows]


def delete_imported_build(workspace_session_id: str, account_name: str, character_id: str) -> bool:
    with session_scope() as db:
        row = db.scalar(select(ImportedBuild).where(
            ImportedBuild.workspace_session_id == workspace_session_id,
            ImportedBuild.account_name == account_name,
            ImportedBuild.character_id == character_id,
        ))
        if row is None:
            return False
        db.delete(row)
        return True


def save_session_api_key(session_id: str, encrypted: bytes) -> None:
    with session_scope() as db:
        row = db.get(WorkspaceSession, session_id)
        if row is None:
            row = WorkspaceSession(session_id=session_id)
            db.add(row)
        row.encrypted_api_key = encrypted
        row.last_active = time.time()


def get_session_api_key(session_id: str) -> bytes | None:
    with session_scope() as db:
        row = db.get(WorkspaceSession, session_id)
        return row.encrypted_api_key if row else None


def delete_session_api_key(session_id: str) -> None:
    with session_scope() as db:
        row = db.get(WorkspaceSession, session_id)
        if row is not None:
            row.encrypted_api_key = None
            row.last_active = time.time()
