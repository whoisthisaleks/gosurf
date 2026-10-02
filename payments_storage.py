"""Small JSON storage for pending USDT payments and consumed transactions."""

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone


if os.path.exists("/data"):
    FILE_PATH = "/data/payments.json"
else:
    FILE_PATH = "payments.json"


def _load():
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            raise ValueError("Invalid payments storage format")
        data.setdefault("payments", {})
        data.setdefault("processed_tx_ids", [])
        return data
    except FileNotFoundError:
        return {"payments": {}, "processed_tx_ids": []}
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"PAYMENTS STORAGE ERROR: {exc}")
        return {"payments": {}, "processed_tx_ids": []}


def _save(data):
    directory = os.path.dirname(FILE_PATH) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix="payments-", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, FILE_PATH)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def create_payment(user_id):
    """Create/reuse one payment request. Only one request may be awaiting payment."""
    data = _load()
    now = datetime.now(timezone.utc)
    for payment in data["payments"].values():
        if payment.get("status") in ("pending", "checking"):
            try:
                created_at = datetime.fromisoformat(payment["created_at"])
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                if now - created_at > timedelta(hours=24):
                    payment["status"] = "expired"
                    continue
            except (KeyError, TypeError, ValueError):
                payment["status"] = "expired"
                continue
            if int(payment.get("user_id", 0)) == int(user_id):
                return payment
            return None

    payment = {
        "user_id": int(user_id),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
    }
    data["payments"][str(user_id)] = payment
    _save(data)
    return payment


def mark_payment_checking(user_id):
    data = _load()
    payment = data["payments"].get(str(user_id))
    if not payment or payment.get("status") != "pending":
        return False
    payment["status"] = "checking"
    payment["checking_since"] = datetime.now(timezone.utc).isoformat()
    _save(data)
    return True


def get_checking_payments():
    data = _load()
    return [dict(p) for p in data["payments"].values() if p.get("status") == "checking"]


def is_transaction_processed(tx_id):
    return tx_id in _load()["processed_tx_ids"]


def complete_payment(user_id, tx_id):
    """Atomically persist transaction consumption and payment completion."""
    data = _load()
    if tx_id in data["processed_tx_ids"]:
        return False
    payment = data["payments"].get(str(user_id))
    if not payment or payment.get("status") != "checking":
        return False
    data["processed_tx_ids"].append(tx_id)
    payment["status"] = "paid"
    payment["transaction_id"] = tx_id
    payment["completed_at"] = datetime.now(timezone.utc).isoformat()
    _save(data)
    return True
