# File: nurolab/tests/test_websocket.py
#
# Automated test for the NuroLab live data WebSocket stream (/ws/live).
# Run with:  python nurolab/tests/test_websocket.py   (backend must already be running)
#
# What this checks:
#   1. The connection actually succeeds.
#   2. We receive N payloads (default 5) without errors or timeouts.
#   3. Every payload is valid JSON and contains all the expected fields.
#   4. The connection closes cleanly afterwards.
#
# NOTE: this assumes the server.py wiring fix has been applied (delta_de,
# gamma_de, alpha_beta_ratio, engagement_index, relaxation_index,
# cognitive_load, signal_quality all added to the live payload). If that fix
# hasn't landed yet, this test will correctly FAIL on the missing-fields
# check -- that's expected, not a bug in this test.
#
# Uses the `websockets` library (pip install websockets) for the connection.

import asyncio
import json
import sys

import websockets

WS_URL = "ws://127.0.0.1:8000/ws/live?user_id=test-user-001"
N_PAYLOADS = 5
TIMEOUT_SEC = 15  # live payloads arrive every ~2s, so 5 payloads needs ~10s minimum

REQUIRED_FIELDS = [
    "timestamp",
    "alpha_de",
    "beta_de",
    "theta_de",
    "delta_de",
    "gamma_de",
    "alpha_beta_ratio",
    "engagement_index",
    "relaxation_index",
    "cognitive_load",
    "signal_quality",
    "deviation_score",
    "risk_tier",
    # predict_all() spreads these three directly into the payload --
    # there is no single "predictions" field.
    "stress_prediction",
    "attention_prediction",
    "fatigue_prediction",
]


async def run():
    n_pass = 0
    n_fail = 0

    def report(ok, message):
        nonlocal n_pass, n_fail
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {message}")
        if ok:
            n_pass += 1
        else:
            n_fail += 1

    print(f"Connecting to {WS_URL} ...")
    try:
        websocket = await asyncio.wait_for(websockets.connect(WS_URL), timeout=TIMEOUT_SEC)
    except Exception as e:
        report(False, f"connection failed: {e}")
        print("\n0 passed, 1 failed, 1 total")
        sys.exit(1)

    report(True, "connection established")

    received = 0
    try:
        async with asyncio.timeout(TIMEOUT_SEC):
            while received < N_PAYLOADS:
                raw_message = await websocket.recv()
                received += 1

                try:
                    payload = json.loads(raw_message)
                except json.JSONDecodeError as e:
                    report(False, f"payload #{received}: not valid JSON ({e})")
                    print(f"  raw: {raw_message!r}")
                    continue

                print(f"  payload #{received}: {payload}")

                if "error" in payload:
                    report(False, f"payload #{received}: server sent an error frame: {payload['error']}")
                    continue

                missing = [f for f in REQUIRED_FIELDS if f not in payload]
                report(
                    len(missing) == 0,
                    f"payload #{received}: all required fields present"
                    if not missing
                    else f"payload #{received}: missing fields {missing}",
                )

                if "risk_tier" in payload:
                    report(
                        payload["risk_tier"] in ("low", "moderate", "high"),
                        f"payload #{received}: risk_tier is a valid value ({payload.get('risk_tier')!r})",
                    )
    except (TimeoutError, asyncio.TimeoutError):
        report(False, f"only received {received}/{N_PAYLOADS} payloads within {TIMEOUT_SEC}s")
    except websockets.exceptions.ConnectionClosed as e:
        report(False, f"connection closed unexpectedly after {received} payloads: {e}")
    finally:
        try:
            await websocket.close()
            report(True, "disconnected cleanly")
        except Exception as e:
            report(False, f"error while closing connection: {e}")

    print("=" * 60)
    print(f"{n_pass} passed, {n_fail} failed, {n_pass + n_fail} total")
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == "__main__":
    asyncio.run(run())
