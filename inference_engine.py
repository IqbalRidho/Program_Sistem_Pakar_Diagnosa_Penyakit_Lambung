import json
from typing import Dict, List

def load_knowledge_base(path: str = "knowledge_base.json") -> dict:
    """
    Memuat basis pengetahuan dari file JSON.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def combine_cf(cf1: float, cf2: float) -> float:
    """
    Menggabungkan dua nilai CF menggunakan rumus:
    CFcombine = CF1 + CF2 * (1 - CF1)
    """
    return cf1 + cf2 * (1 - cf1)

def forward_chaining_with_cf(answers: Dict[str, bool], kb: dict) -> List[dict]:
    """
    Mesin inferensi berbasis metode Certainty Factor dan Forward Chaining.

    Parameter:
    - answers: dict berisi jawaban user, contoh {"G01": True, "G02": False, ...}
    - kb: basis pengetahuan hasil load dari JSON

    Return:
    - List hasil diagnosis penyakit dengan nilai CF (urut dari tertinggi)
    """
    rules = kb["rules"]
    conditions = kb["conditions"]
    facts = kb.get("facts", {})
    penyakit = kb["penyakit"]

    cf_results: Dict[str, float] = {}
    known_facts = set([k for k, v in answers.items() if v])  # gejala yang dijawab "ya"
    new_fact_added = True

    # Proses forward chaining sampai tidak ada fakta baru
    while new_fact_added:
        new_fact_added = False

        for rule in rules:
            rule_if = rule["if"]
            rule_then = rule["then"]
            rule_cf = rule["cf"]

            # Cek apakah semua kondisi terpenuhi
            if all(cond in known_facts for cond in rule_if):
                # Hitung nilai CF dari aturan
                cf_values = [
                    conditions.get(cond, {"cf_yes": 1}).get("cf_yes", 1)
                    if cond in conditions else cf_results.get(cond, 1)
                    for cond in rule_if
                ]
                cf_rule = min(cf_values) * rule_cf

                # Jika hasil (then) sudah punya nilai CF, gabungkan
                if rule_then in cf_results:
                    cf_results[rule_then] = combine_cf(cf_results[rule_then], cf_rule)
                else:
                    cf_results[rule_then] = cf_rule

                # Jika hasil merupakan fakta baru, tambahkan
                if rule_then not in known_facts:
                    known_facts.add(rule_then)
                    new_fact_added = True

    # Ambil hasil akhir berupa penyakit
    final_diagnosis: List[dict] = [
        {
            "penyakit_id": pid,
            "penyakit": penyakit.get(pid, pid),
            "cf": round(cf_val, 4)
        }
        for pid, cf_val in cf_results.items()
        if pid in penyakit
    ]

    # Urutkan berdasarkan CF tertinggi
    final_diagnosis.sort(key=lambda x: x["cf"], reverse=True)
    return final_diagnosis
