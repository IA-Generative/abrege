import uuid

from src.schemas.entity import EntityTable
from src.schemas.result import EntityModel, RelationshipModel


def _task_id() -> str:
    return f"task-{uuid.uuid4()}"


def test_save_chunk_entities_persists_entities_and_resolves_relationship_indices():
    table = EntityTable()
    task_id = _task_id()

    table.save_chunk_entities(
        task_id=task_id,
        chunk_index=0,
        entities=[
            EntityModel(type="PERSON", text="Alice", contexts=["Alice travaille chez Acme"], pages=[1]),
            EntityModel(type="ORGANIZATION", text="Acme", contexts=["Alice travaille chez Acme"], pages=[1]),
        ],
        relationships=[RelationshipModel(source_index=0, target_index=1, relationship_type="WORKS_AT", description="Alice travaille chez Acme")],
    )

    entities = table.get_entities_by_task(task_id)
    relationships = table.get_relationships_by_task(task_id)

    assert len(entities) == 2
    assert len(relationships) == 1

    alice = next(e for e in entities if e.text == "Alice")
    acme = next(e for e in entities if e.text == "Acme")
    assert relationships[0].source_entity_id == alice.id
    assert relationships[0].target_entity_id == acme.id
    assert relationships[0].chunk_index == 0


def test_save_chunk_entities_ignores_out_of_range_relationship_indices():
    table = EntityTable()
    task_id = _task_id()

    table.save_chunk_entities(
        task_id=task_id,
        chunk_index=0,
        entities=[EntityModel(type="PERSON", text="Alice", contexts=[], pages=[1])],
        relationships=[RelationshipModel(source_index=0, target_index=5, relationship_type="WORKS_AT", description="invalid target")],
    )

    assert table.get_relationships_by_task(task_id) == []


def test_save_chunk_entities_is_idempotent_per_chunk_on_retry():
    table = EntityTable()
    task_id = _task_id()

    table.save_chunk_entities(
        task_id=task_id,
        chunk_index=0,
        entities=[EntityModel(type="PERSON", text="Alice", contexts=[], pages=[1])],
        relationships=[],
    )
    table.save_chunk_entities(
        task_id=task_id,
        chunk_index=0,
        entities=[EntityModel(type="PERSON", text="Bob", contexts=[], pages=[1])],
        relationships=[],
    )

    entities = table.get_entities_by_task(task_id)

    assert len(entities) == 1
    assert entities[0].text == "Bob"


def test_save_chunk_entities_keeps_other_chunks_untouched():
    table = EntityTable()
    task_id = _task_id()

    table.save_chunk_entities(task_id=task_id, chunk_index=0, entities=[EntityModel(type="PERSON", text="Alice", contexts=[], pages=[1])], relationships=[])
    table.save_chunk_entities(task_id=task_id, chunk_index=1, entities=[EntityModel(type="PERSON", text="Bob", contexts=[], pages=[2])], relationships=[])

    table.save_chunk_entities(task_id=task_id, chunk_index=0, entities=[], relationships=[])

    entities = table.get_entities_by_task(task_id)

    assert len(entities) == 1
    assert entities[0].text == "Bob"


def test_save_global_relationships_resolves_entity_ids_in_order():
    table = EntityTable()
    task_id = _task_id()

    table.save_chunk_entities(
        task_id=task_id,
        chunk_index=0,
        entities=[EntityModel(type="PERSON", text="Alice", contexts=[], pages=[1])],
        relationships=[],
    )
    table.save_chunk_entities(
        task_id=task_id,
        chunk_index=1,
        entities=[EntityModel(type="ORGANIZATION", text="Acme", contexts=[], pages=[5])],
        relationships=[],
    )

    entities = table.get_entities_by_task(task_id)
    entity_ids_in_order = [e.id for e in entities]

    table.save_global_relationships(
        task_id=task_id,
        entity_ids_in_order=entity_ids_in_order,
        relationships=[
            RelationshipModel(source_index=0, target_index=1, relationship_type="WORKS_AT", description="Cross-chunk link")
        ],
    )

    relationships = table.get_relationships_by_task(task_id)
    global_relationships = [r for r in relationships if r.chunk_index is None]

    assert len(global_relationships) == 1
    assert global_relationships[0].source_entity_id == entity_ids_in_order[0]
    assert global_relationships[0].target_entity_id == entity_ids_in_order[1]


def test_save_global_relationships_does_not_touch_local_chunk_relationships():
    table = EntityTable()
    task_id = _task_id()

    table.save_chunk_entities(
        task_id=task_id,
        chunk_index=0,
        entities=[
            EntityModel(type="PERSON", text="Alice", contexts=[], pages=[1]),
            EntityModel(type="ORGANIZATION", text="Acme", contexts=[], pages=[1]),
        ],
        relationships=[RelationshipModel(source_index=0, target_index=1, relationship_type="WORKS_AT", description="local")],
    )
    entities = table.get_entities_by_task(task_id)

    table.save_global_relationships(task_id=task_id, entity_ids_in_order=[e.id for e in entities], relationships=[])
    table.save_global_relationships(task_id=task_id, entity_ids_in_order=[e.id for e in entities], relationships=[])

    relationships = table.get_relationships_by_task(task_id)

    assert len(relationships) == 1
    assert relationships[0].chunk_index == 0


def test_get_entities_by_task_returns_empty_list_when_none():
    table = EntityTable()
    assert table.get_entities_by_task(_task_id()) == []
    assert table.get_relationships_by_task(_task_id()) == []
