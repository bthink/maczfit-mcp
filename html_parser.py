import re
import json
from typing import Any


def parse_user_id(html: str) -> int:
    match = re.search(r'(?:var|let|const)\s+userId\s*=\s*(\d+)', html)
    if not match:
        raise ValueError("JS variable 'userId' not found in HTML")
    return int(match.group(1))


def parse_transaction_ids(html: str) -> list[int]:
    txs = _extract_js_var(html, "allTransactions")
    return list({tx["Id"] for tx in txs if "Id" in tx})


def _extract_js_var(html: str, var_name: str) -> Any:
    pattern = rf'(?:var|let|const)\s+{re.escape(var_name)}\s*=\s*(\[.*?\]|\{{.*?\}})\s*;'
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        raise ValueError(f"JS variable '{var_name}' not found in HTML")
    return json.loads(match.group(1))


def parse_all_transactions(html: str) -> list[dict]:
    return _extract_js_var(html, "allTransactions")


def parse_delivery_dates(html: str) -> dict:
    return _extract_js_var(html, "deliveryDates")


def parse_delivery_hours(html: str) -> list[dict]:
    return _extract_js_var(html, "deliveryHours")


def extract_packages(transactions: list[dict]) -> list[dict]:
    packages = []
    for tx in transactions:
        for pkg in tx.get("Packages", []):
            packages.append({
                "package_id": pkg["Id"],
                "transaction_id": pkg["TransactionId"],
                "date": pkg["ValidDisplayDeliveryDate"],
                "status": pkg["Status"],
                "is_editable": pkg["IsChangeDeliveryEditable"],
                "diet_name": tx["Product"]["Name"],
                "kcal": tx["Product"]["Kcal"],
            })
    return packages
