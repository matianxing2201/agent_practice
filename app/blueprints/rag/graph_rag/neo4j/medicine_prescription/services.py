"""
领域模型:
    ChineseMedicine(中药)   name / chapter / section / nature_flavor / meridian
                            / application / dosage / caution
    MedicineCategory(分类)  chapter / section
    ChineseMedicine -[:BELONGS_TO_CATEGORY]-> MedicineCategory  中药属于分类

    Prescription(方剂)      name / unit / subunit / function / indication
                            / compatibility_meaning / compatibility_feature / usage / other
    PrescriptionCategory(类型)  unit / subunit
    Prescription -[:BELONGS_TO_CATEGORY]-> PrescriptionCategory  方剂属于类型
    Prescription -[:CONTAINS]-> ChineseMedicine                   方剂包含中药


"""

import json
import os
from typing import Any

from ..neo4j_store import Neo4jStore

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
MEDICINE_JSON = os.path.join(_DATA_DIR, "medicine.json")
PRESCRIPTION_JSON = os.path.join(_DATA_DIR, "prescription.json")


def _store() -> Neo4jStore:
    return Neo4jStore()


def _load_json(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- 单点操作


def create_medicine(medicine: dict) -> None:
    """创建 / 合并单个中药节点,并关联它到中药分类。

    MERGE + SET 幂等:中药按 name 作为键,重复执行不产生重复节点,
    只把属性更新到最新。随后按 chapter / section 关联 MedicineCategory。
    """
    store = _store()
    try:
        store.run_cypher(
            """
            MERGE (m: ChineseMedicine {name: $name})
            SET
                m.chapter = $chapter,
                m.section = $section,
                m.nature_flavor = $nature_flavor,
                m.meridian = $meridian,
                m.application = $application,
                m.dosage = $dosage,
                m.caution = $caution
            """,
            params=medicine,
        )
        store.run_cypher(
            """
            MERGE (mcat: MedicineCategory {chapter: $chapter, section: $section})
            WITH mcat
            MATCH (m: ChineseMedicine {name: $name})
            MERGE (m)-[:BELONGS_TO_CATEGORY]->(mcat)
            """,
            params={
                "chapter": medicine["chapter"],
                "section": medicine["section"],
                "name": medicine["name"],
            },
        )
    finally:
        store.close()


def create_prescription(prescription: dict) -> None:
    """创建 / 合并单个方剂节点,并关联类型与组成。

    方剂按 name 作为 MERGE 键。composition 是方剂的内嵌组成列表,
    每一项 {drug: 中药名},通过 CONTAINS 关系连到 (已存在的) 中药节点。
    """
    store = _store()
    try:
        store.run_cypher(
            """
            MERGE (p: Prescription {name: $name})
            SET
                p.unit = $unit,
                p.subunit = $subunit,
                p.function = $function,
                p.indication = $indication,
                p.compatibility_meaning = $compatibility_meaning,
                p.compatibility_feature = $compatibility_feature,
                p.usage = $usage,
                p.other = $other
            """,
            params=prescription,
        )
        # 关联方剂类型
        store.run_cypher(
            """
            MERGE (pcat: PrescriptionCategory {unit: $unit, subunit: $subunit})
            WITH pcat
            MATCH (p: Prescription {name: $name})
            MERGE (p)-[:BELONGS_TO_CATEGORY]->(pcat)
            """,
            params={
                "unit": prescription["unit"],
                "subunit": prescription["subunit"],
                "name": prescription["name"],
            },
        )
        # 关联组成中药
        for composition in prescription.get("composition", []):
            drug = composition["drug"]
            store.run_cypher(
                """
                MATCH (p: Prescription {name: $prescription_name})
                MERGE (m: ChineseMedicine {name: $medicine_name})
                MERGE (p)-[:CONTAINS]->(m)
                """,
                params={
                    "prescription_name": prescription["name"],
                    "medicine_name": drug,
                },
            )
    finally:
        store.close()


# ---------------------------------------------------------------- 查询


def search_prescription(prescription_name: str) -> list[dict]:
    """按方剂名查询:方剂信息 + 它的组成中药列表。

    OPTIONAL MATCH 保证即使某些组成中药未建节点,方剂本身也能返回;
    collect 把多条组成中药聚合成一个列表。
    """
    store = _store()
    try:
        rows = store.run_cypher(
            """
            MATCH (p: Prescription {name: $prescription_name})
            OPTIONAL MATCH (p)-[:CONTAINS]->(m: ChineseMedicine)
            RETURN
                p{.*} AS prescription_info,
                collect(m{.*}) AS medicine_list
            """,
            params={"prescription_name": prescription_name},
        )
        return [dict(rec) for rec in rows]
    finally:
        store.close()


# ---------------------------------------------------------------- 全量建图


def seed_graph() -> dict[str, Any]:
    """读 data/ 下两份 JSON,全量构造医学图谱(幂等)。

    顺序:先建全部中药 + 分类,再建全部方剂 + 类型 + 组成。
    MERGE 保证重复调用不会产生重复节点 / 关系。
    """
    medicines = _load_json(MEDICINE_JSON)
    prescriptions = _load_json(PRESCRIPTION_JSON)

    for medicine in medicines:
        create_medicine(medicine)
    for prescription in prescriptions:
        create_prescription(prescription)

    return {
        "medicines": len(medicines),
        "prescriptions": len(prescriptions),
    }