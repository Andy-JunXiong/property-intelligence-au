import json
from pathlib import Path
from typing import Dict, Any, List


OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

ABS_DATAFLOWS_PATH = OUTPUT_DIR / "abs_dataflows.json"


KEYWORDS = [
    "income",
    "rent",
    "housing",
    "dwelling",
    "population",
    "migration",
    "family",
    "household",
    "property",
    "region",
    "suburb",
    "sa2",
    "lga",
    "census",
]


def load_abs_dataflows() -> Dict[str, Any]:
    with open(ABS_DATAFLOWS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_references(data: Dict[str, Any]) -> Dict[str, Any]:
    return data.get("references", {})


def find_candidate_dataflows(references: Dict[str, Any], keywords: List[str]) -> List[Dict[str, str]]:
    candidates = []

    for _, item in references.items():
        item_id = str(item.get("id", ""))
        name = str(item.get("name", ""))
        description = str(item.get("description", ""))

        searchable_text = f"{item_id} {name} {description}".lower()

        matched_keywords = [kw for kw in keywords if kw.lower() in searchable_text]

        if matched_keywords:
            candidates.append(
                {
                    "id": item_id,
                    "name": name,
                    "description": description,
                    "matched_keywords": ", ".join(matched_keywords),
                }
            )

    return candidates


def save_json(data: Any, filename: str) -> None:
    output_path = OUTPUT_DIR / filename
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    abs_data = load_abs_dataflows()
    references = extract_references(abs_data)
    candidates = find_candidate_dataflows(references, KEYWORDS)

    save_json(candidates, "abs_candidate_dataflows.json")

    print(f"Total references: {len(references)}")
    print(f"Candidate datasets found: {len(candidates)}")
    print("Saved candidates to data/abs_candidate_dataflows.json")

    print("\nTop 20 candidates:")
    for item in candidates[:20]:
        print("-" * 80)
        print("ID:", item["id"])
        print("Name:", item["name"])
        print("Matched:", item["matched_keywords"])