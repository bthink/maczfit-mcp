import os
import re
import requests
from pathlib import Path
from dotenv import load_dotenv
from html_parser import (
    parse_all_transactions,
    parse_delivery_dates,
    parse_delivery_hours,
    parse_user_id,
    parse_transaction_ids,
    extract_packages,
)

load_dotenv(Path(__file__).parent / ".env")

APP_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJBcGlVc2VyIjoiV1dXIiwia"
    "HR0cDovL3NjaGVtYXMueG1sc29hcC5vcmcvd3MvMjAwNS8wNS9pZGVudGl0eS9j"
    "bGFpbXMvZW1haWxhZGRyZXNzIjoiZG9fbm90X3JlbW92ZUBwcm9leGUucGwiLCJ"
    "odHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2"
    "NsYWltcy9uYW1lIjoiMzIiLCJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93c"
    "y8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9zeXN0ZW0iOiJXV1ciLCJDYW5FZGl0"
    "U2NoZWR1bGVzIjoiRmFsc2UiLCJBY2NvdW50VHlwZSI6IjAiLCJBY2NvdW50VHlw"
    "ZUF1dGhvcml6ZVJlcXVpcmVkIjoiRmFsc2UiLCJleHAiOjE3NzgxMDE5NzgsImlz"
    "cyI6Im1hY3pmaXQucGwiLCJhdWQiOiJtYWN6Zml0LnBsIn0.XsOOXSyIi3819S4r"
    "jM1ufATWSSO2OfdhtDfnJYcggKg"
)

BASE_URL = "https://www.maczfit.pl"


class MaczfitClient:
    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "Mozilla/5.0"})
        self._authenticated = False
        self._csrf: str = ""
        self._client_id: int = 0
        self._transaction_ids: list[int] = []

    def _csrf_token(self) -> str:
        return self._csrf

    def _is_redirected_to_login(self, response: requests.Response) -> bool:
        return response.url.rstrip("/") in (
            f"{BASE_URL}/login",
            f"{BASE_URL}/logowanie",
        ) or response.status_code in (401, 302, 500)

    def _meta_csrf_token(self, html: str) -> str:
        match = re.search(
            r'<meta[^>]+name=["\']csrf-token["\'][^>]+content=["\']([^"\']+)["\']',
            html,
        )
        if not match:
            raise RuntimeError("csrf-token meta tag not found in page")
        return match.group(1)

    def login(self) -> None:
        email = os.environ["MACZFIT_EMAIL"]
        password = os.environ["MACZFIT_PASSWORD"]

        # GET homepage to establish session and get CSRF token from meta tag
        init = self._session.get(f"{BASE_URL}/")
        init.raise_for_status()
        csrf = self._meta_csrf_token(init.text)

        resp = self._session.post(
            f"{BASE_URL}/login-endpoint",
            json={"email": email, "password": password, "remember_me": False},
            headers={
                "Authorization": f"Bearer {APP_TOKEN}",
                "X-CSRF-TOKEN": csrf,
                "x-requested-with": "XMLHttpRequest",
            },
            allow_redirects=True,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Login failed: HTTP {resp.status_code}")
        if not self._session.cookies.get("maczfit_session"):
            raise RuntimeError("Login failed: no session cookie")
        # After login, fetch account page to get CSRF token + auto-discover client/transaction IDs
        account = self._session.get(f"{BASE_URL}/moje-konto")
        self._csrf = self._meta_csrf_token(account.text)
        self._client_id = parse_user_id(account.text)
        self._transaction_ids = parse_transaction_ids(account.text)
        self._authenticated = True

    def _get(self, url: str) -> requests.Response:
        resp = self._session.get(url)
        if self._is_redirected_to_login(resp):
            self.login()
            resp = self._session.get(url)
        return resp

    def _refresh_csrf(self) -> None:
        """Fetch a fresh CSRF token from the account page."""
        r = self._session.get(f"{BASE_URL}/moje-konto")
        self._csrf = self._meta_csrf_token(r.text)

    def _post_form(self, url: str, data: dict) -> requests.Response:
        if not self._authenticated:
            self.login()
        # Always refresh CSRF before write - tokens are single-use in Laravel
        self._refresh_csrf()
        resp = self._session.post(
            url,
            data=data,
            headers={
                "x-csrf-token": self._csrf_token(),
                "x-requested-with": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        if resp.status_code == 419:
            # Token still stale - full re-login and retry
            self.login()
            resp = self._session.post(
                url,
                data=data,
                headers={
                    "x-csrf-token": self._csrf_token(),
                    "x-requested-with": "XMLHttpRequest",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
        return resp

    def get_order_page(self, transaction_id: int) -> str:
        resp = self._get(f"{BASE_URL}/moje-konto/zamowienia/{transaction_id}")
        resp.raise_for_status()
        return resp.text

    def get_schedule(self, transaction_id: int) -> dict:
        html = self.get_order_page(transaction_id)
        transactions = parse_all_transactions(html)
        delivery_dates = parse_delivery_dates(html)
        delivery_hours = parse_delivery_hours(html)
        packages = extract_packages(transactions)
        return {
            "packages": packages,
            "delivery_dates": delivery_dates,
            "available_days": [d["Day"] for d in delivery_hours],
        }

    def move_day(self, transaction_id: int, package_id: int, new_date: str) -> dict:
        data = {
            f"DeliveryDates[{package_id}]": new_date,
            "TransactionId": str(transaction_id),
            "ClientId": str(self._client_id),
        }
        resp = self._post_form(f"{BASE_URL}/my-account/change-delivery-date", data)
        if resp.status_code == 200:
            return {"success": True, "package_id": package_id, "new_date": new_date}
        return {
            "success": False,
            "package_id": package_id,
            "status_code": resp.status_code,
            "response": resp.text[:500],
        }

    def move_day_by_date(
        self,
        from_date: str,
        to_date: str,
        transaction_ids: list[int] | None = None,
    ) -> list[dict]:
        tx_ids = transaction_ids or self._transaction_ids
        results = []
        for tx_id in tx_ids:
            schedule = self.get_schedule(tx_id)
            for pkg in schedule["packages"]:
                if pkg["date"] == from_date:
                    if not pkg["is_editable"]:
                        results.append({
                            "success": False,
                            "package_id": pkg["package_id"],
                            "diet_name": pkg["diet_name"],
                            "reason": "not_editable",
                        })
                        continue
                    if to_date not in schedule["available_days"]:
                        results.append({
                            "success": False,
                            "package_id": pkg["package_id"],
                            "diet_name": pkg["diet_name"],
                            "reason": f"target date {to_date} not available",
                        })
                        continue
                    result = self.move_day(tx_id, pkg["package_id"], to_date)
                    result["diet_name"] = pkg["diet_name"]
                    results.append(result)
        return results

    def list_diets(self) -> list[dict]:
        if not self._authenticated:
            self.login()
        # allTransactions on any order page contains all active diets - one request suffices
        schedule = self.get_schedule(self._transaction_ids[0])
        by_tx: dict[int, dict] = {}
        for pkg in schedule["packages"]:
            tx_id = pkg["transaction_id"]
            if tx_id not in by_tx:
                by_tx[tx_id] = {
                    "transaction_id": tx_id,
                    "diet_name": pkg["diet_name"],
                    "kcal": pkg["kcal"],
                    "package_count": 0,
                }
            by_tx[tx_id]["package_count"] += 1
        return list(by_tx.values())
