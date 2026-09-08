import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, ForeignKey, Integer, JSON, String, Text

from src.internal.db import Base, get_db
from src.schemas.result import EntityModel, RelationshipModel


class EntityRow(Base):
    __tablename__ = "entities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False, index=True)
    type = Column(String, nullable=False)
    text = Column(String, nullable=False)
    contexts = Column(JSON, nullable=True)
    pages = Column(JSON, nullable=True)
    created_at = Column(BigInteger, default=lambda: int(datetime.now().timestamp()))


class RelationshipRow(Base):
    __tablename__ = "relationships"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=True, index=True)  # None = relation globale (cross-chunk)
    source_entity_id = Column(String, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    target_entity_id = Column(String, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(BigInteger, default=lambda: int(datetime.now().timestamp()))


class EntityRowModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str
    chunk_index: int
    type: str
    text: str
    contexts: Optional[List[str]] = None
    pages: Optional[List[int]] = None
    created_at: int


class RelationshipRowModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str
    chunk_index: Optional[int] = None
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    description: Optional[str] = None
    created_at: int


class EntityTable:
    def save_chunk_entities(
        self,
        task_id: str,
        chunk_index: int,
        entities: List[EntityModel],
        relationships: List[RelationshipModel],
    ) -> None:
        with get_db() as db:
            db.query(RelationshipRow).filter(
                RelationshipRow.task_id == task_id,
                RelationshipRow.chunk_index == chunk_index,
            ).delete()
            db.query(EntityRow).filter(
                EntityRow.task_id == task_id,
                EntityRow.chunk_index == chunk_index,
            ).delete()

            entity_rows: List[EntityRow] = []
            for entity in entities or []:
                row = EntityRow(
                    task_id=task_id,
                    chunk_index=chunk_index,
                    type=entity.type,
                    text=entity.text,
                    contexts=entity.contexts,
                    pages=entity.pages,
                )
                db.add(row)
                entity_rows.append(row)
            db.flush()

            for relationship in relationships or []:
                if 0 <= relationship.source_index < len(entity_rows) and 0 <= relationship.target_index < len(entity_rows):
                    db.add(
                        RelationshipRow(
                            task_id=task_id,
                            chunk_index=chunk_index,
                            source_entity_id=entity_rows[relationship.source_index].id,
                            target_entity_id=entity_rows[relationship.target_index].id,
                            relationship_type=relationship.relationship_type,
                            description=relationship.description,
                        )
                    )

            db.commit()

    def get_entities_by_task(self, task_id: str) -> List[EntityRow]:
        with get_db() as db:
            rows = db.query(EntityRow).filter(EntityRow.task_id == task_id).order_by(EntityRow.created_at).all()
            db.expunge_all()
            return rows

    def get_relationships_by_task(self, task_id: str) -> List[RelationshipRow]:
        with get_db() as db:
            rows = db.query(RelationshipRow).filter(RelationshipRow.task_id == task_id).order_by(RelationshipRow.created_at).all()
            db.expunge_all()
            return rows

    def get_entity_by_id(self, task_id: str, entity_id: str) -> Optional[EntityRow]:
        with get_db() as db:
            row = db.query(EntityRow).filter(EntityRow.task_id == task_id, EntityRow.id == entity_id).first()
            if row is not None:
                db.expunge(row)
            return row

    def delete_entity_by_id(self, task_id: str, entity_id: str) -> bool:
        with get_db() as db:
            # Relationships pointing to this entity are removed too (FK ondelete=CASCADE at the DB level
            # for engines that enforce it; deleted explicitly here so it also holds on sqlite in tests).
            db.query(RelationshipRow).filter(
                RelationshipRow.task_id == task_id,
                (RelationshipRow.source_entity_id == entity_id) | (RelationshipRow.target_entity_id == entity_id),
            ).delete()
            deleted = db.query(EntityRow).filter(EntityRow.task_id == task_id, EntityRow.id == entity_id).delete()
            db.commit()
            return deleted > 0

    def get_relationship_by_id(self, task_id: str, relationship_id: str) -> Optional[RelationshipRow]:
        with get_db() as db:
            row = db.query(RelationshipRow).filter(RelationshipRow.task_id == task_id, RelationshipRow.id == relationship_id).first()
            if row is not None:
                db.expunge(row)
            return row

    def delete_relationship_by_id(self, task_id: str, relationship_id: str) -> bool:
        with get_db() as db:
            deleted = db.query(RelationshipRow).filter(
                RelationshipRow.task_id == task_id, RelationshipRow.id == relationship_id
            ).delete()
            db.commit()
            return deleted > 0

    def save_global_relationships(
        self,
        task_id: str,
        entity_ids_in_order: List[str],
        relationships: List[RelationshipModel],
    ) -> None:
        with get_db() as db:
            db.query(RelationshipRow).filter(
                RelationshipRow.task_id == task_id,
                RelationshipRow.chunk_index.is_(None),
            ).delete()

            for relationship in relationships or []:
                if 0 <= relationship.source_index < len(entity_ids_in_order) and 0 <= relationship.target_index < len(entity_ids_in_order):
                    db.add(
                        RelationshipRow(
                            task_id=task_id,
                            chunk_index=None,
                            source_entity_id=entity_ids_in_order[relationship.source_index],
                            target_entity_id=entity_ids_in_order[relationship.target_index],
                            relationship_type=relationship.relationship_type,
                            description=relationship.description,
                        )
                    )

            db.commit()


entity_table = EntityTable()
