"""TronScan polling for confirmed USDT TRC20 transfers."""

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import requests

from payments_storage import (
    complete_payment,
    get_checking_payments,
    is_transaction_processed,
)
from pro import add_pro_user


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
TRONSCAN_URL = "https://apilist.tronscanapi.com/api/token_trc20/transfers"
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
PAYMENT_AMOUNT = Decimal("2.99")
USDT_DECIMALS = 6
POLL_SECONDS = 120
# Enable only in a local .env: PAYMENTS_TEST_MODE=true. Defaults safe for production.
TEST_MODE = os.getenv("PAYMENTS_TEST_MODE", "false").strip().lower() == "true"


def _timestamp_ms(value):
    return int(datetime.fromisoformat(value).timestamp() * 1000)


def _fetch_transfers(start_timestamp):
    wallet = os.getenv("USDT_TRC20_WALLET", "").strip()
    if TEST_MODE:
        logger.info("TEST_MODE enabled: returning a fake confirmed USDT transfer")
        return [{
            "transaction_id": f"TEST_TX_{uuid.uuid4().hex}",
            "contract_address": USDT_CONTRACT,
            "to_address": wallet,
            "quant": str(int(PAYMENT_AMOUNT * (10 ** USDT_DECIMALS))),
            "confirmed": True,
            "finalResult": "SUCCESS",
            "event_type": "Transfer",
            "block_ts": max(start_timestamp, int(datetime.now().timestamp() * 1000)),
        }]

    params = {
        "contract_address": USDT_CONTRACT,
        "toAddress": wallet,
        "start_timestamp": start_timestamp,
        "start": 0,
        "limit": 50,
        "confirm": 0,
    }
    headers = {}
    api_key = os.getenv("TRONSCAN_API_KEY", "").strip()
    if api_key:
        headers["TRON-PRO-API-KEY"] = api_key
    try:
        logger.info("Fetching USDT TRC20 transfers from TronScan")
        response = requests.get(TRONSCAN_URL, params=params, headers=headers, timeout=20)
        if response.status_code != 200:
            logger.warning("TronScan API error: %s", response.status_code)
            return []
        payload = response.json()
        transfers = payload.get("token_transfers", []) if isinstance(payload, dict) else []
        if not isinstance(transfers, list):
            logger.warning("Unexpected TronScan response format")
            return []
        logger.info("Fetched %s transfers", len(transfers))
        return transfers
    except requests.RequestException:
        logger.exception("TronScan request failed; returning no transfers")
        return []
    except (ValueError, TypeError):
        logger.exception("Could not parse TronScan response; returning no transfers")
        return []


def _matching_transfer(payment, transfers, wallet):
    created_ms = _timestamp_ms(payment["created_at"])
    expected_raw = int(PAYMENT_AMOUNT * (10 ** USDT_DECIMALS))
    for transfer in transfers:
        tx_id = transfer.get("transaction_id")
        try:
            amount = int(transfer.get("quant", "0"))
        except (TypeError, ValueError):
            continue
        if not tx_id or is_transaction_processed(tx_id):
            continue
        if transfer.get("contract_address", "").lower() != USDT_CONTRACT.lower():
            continue
        if transfer.get("to_address", "").lower() != wallet.lower():
            continue
        if transfer.get("confirmed") is not True or transfer.get("finalResult") != "SUCCESS":
            continue
        if transfer.get("event_type") != "Transfer":
            continue
        if abs(amount - expected_raw) > int(0.2 * 10**USDT_DECIMALS):
            continue
        try:
            if int(transfer.get("block_ts", 0)) < created_ms:
                continue
        except (TypeError, ValueError):
            continue
        return tx_id
    return None


async def payment_watcher(bot):
    """Check submitted payment claims every two minutes; transient API errors retry."""
    wallet = os.getenv("USDT_TRC20_WALLET", "").strip()
    if not wallet:
        logger.error("USDT_TRC20_WALLET is not configured; payment watcher is disabled")
        return

    logger.info("Payment watcher started; polling every %s seconds (TEST_MODE=%s)", POLL_SECONDS, TEST_MODE)
    while True:
        try:
            payments = get_checking_payments()
            logger.info("Payment watcher found %s payment(s) in checking state", len(payments))
            if payments:
                oldest = min(_timestamp_ms(p["created_at"]) for p in payments)
                transfers = await asyncio.to_thread(_fetch_transfers, oldest)
                logger.info("Payment watcher fetched %s transfer(s)", len(transfers))
                for payment in payments:
                    tx_id = _matching_transfer(payment, transfers, wallet)
                    if tx_id:
                        logger.info("TX matched for user %s: %s", payment["user_id"], tx_id)
                    else:
                        logger.info("No matching tx found for user %s", payment["user_id"])
                    if tx_id and complete_payment(payment["user_id"], tx_id):
                        try:
                            add_pro_user(int(payment["user_id"]), days=30)
                            logger.info("Payment completed for user %s (tx=%s)", payment["user_id"], tx_id)
                            await bot.send_message(
                                int(payment["user_id"]),
                                "✅ Payment confirmed! PRO is active for 30 days. Enjoy 🤙",
                            )
                        except Exception:
                            logger.exception(
                                "Could not activate or notify paid user %s",
                                payment["user_id"],
                            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Payment watcher failed; will retry")
        await asyncio.sleep(POLL_SECONDS)
