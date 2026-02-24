from app.database import SessionLocal
from app.models import Class, ClassLineage

CLASSES = {
    0: "TransKnight",
    1: "Foema",
    2: "BeastMaster",
    3: "Huntress",
}

LINEAGES = {
    0: {
        1: "Confiança",
        2: "Trans",
        3: "Espada Mágica",
    },
    1: {
        1: "Magia Branca",
        2: "Magia Negra",
        3: "Magia Especial",
    },
    2: {
        1: "Elemental",
        2: "Evocação",
        3: "Natureza",
    },
    3: {
        1: "Sobrevivência",
        2: "Troca",
        3: "Captura",
    },
}


def seed_classes_and_lineages():
    session = SessionLocal()
    try:
        # insert classes if missing
        for cid, name in CLASSES.items():
            existing = session.query(Class).filter(Class.id == cid).first()
            if not existing:
                session.add(Class(id=cid, name=name))

        session.flush()

        # insert lineages
        for class_id, lineages in LINEAGES.items():
            for idx, lname in lineages.items():
                exists = (
                    session.query(ClassLineage)
                    .filter(ClassLineage.class_id == class_id, ClassLineage.lineage_index == idx)
                    .first()
                )
                if not exists:
                    session.add(ClassLineage(class_id=class_id, lineage_index=idx, name=lname))

        session.commit()

    finally:
        session.close()
