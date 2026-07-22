from __future__ import annotations

import json
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path
import random
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


MODEL_PATH = Path("/home/sanjay/etl_pipeline/simulation_pipe/anomalymodel.joblib")

DEFAULT_FEATURE_COLUMNS = [
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "response_time_ms",
    "status_code",
    "log_level",
    "year",
    "month",
    "day",
    "hour",
    "minute",
    "second",
    "service_api-gateway",
    "service_auth-service",
    "service_mysql-db",
    "service_nginx-gateway",
    "service_notification-service",
    "service_order-service",
    "service_payment-service",
    "service_redis-cache",
    "service_search-service",
    "service_user-service",
    "acquired",
    "after",
    "again",
    "applied",
    "attempted",
    "auth",
    "authenticated",
    "authorized",
    "backing",
    "backup",
    "breaker",
    "cache",
    "check",
    "checks",
    "circuit",
    "closed",
    "cluster",
    "completed",
    "config",
    "configuration",
    "connection",
    "contention",
    "corruption",
    "database",
    "degraded",
    "detected",
    "disk",
    "error",
    "eviction",
    "executed",
    "exhausted",
    "failed",
    "failure",
    "flush",
    "from",
    "gateway",
    "half",
    "health",
    "high",
    "hit",
    "in",
    "inbound",
    "increasing",
    "index",
    "lagging",
    "latency",
    "length",
    "limit",
    "limiting",
    "lock",
    "login",
    "lookup",
    "lost",
    "maintenance",
    "memory",
    "miss",
    "near",
    "node",
    "observed",
    "of",
    "ok",
    "open",
    "out",
    "passed",
    "passing",
    "payment",
    "pool",
    "processing",
    "progress",
    "provider",
    "query",
    "queue",
    "rate",
    "read",
    "rebuild",
    "recovered",
    "redis",
    "refreshed",
    "refused",
    "rejoined",
    "reload",
    "replacement",
    "replica",
    "request",
    "respond",
    "responded",
    "response",
    "restart",
    "restarted",
    "restored",
    "results",
    "resynced",
    "retries",
    "retry",
    "returned",
    "rising",
    "risk",
    "rolling",
    "routed",
    "running",
    "scheduled",
    "search",
    "service",
    "slow",
    "started",
    "store",
    "storm",
    "successfully",
    "thread",
    "timeout",
    "to",
    "token",
    "traffic",
    "transaction",
    "unavailable",
    "unreachable",
    "unresponsive",
    "up",
    "upstream",
    "user",
    "validation",
    "volume",
    "warmed",
    "write",
]

SERVICE_COLUMNS = [column for column in DEFAULT_FEATURE_COLUMNS if column.startswith("service_")]
NUMERIC_COLUMNS = [
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "response_time_ms",
    "status_code",
    "log_level",
    "year",
    "month",
    "day",
    "hour",
    "minute",
    "second",
]
TEXT_COLUMNS = [
    column
    for column in DEFAULT_FEATURE_COLUMNS
    if column not in NUMERIC_COLUMNS and column not in SERVICE_COLUMNS
]

LOG_LEVEL_MAP = {
    "info": 0,
    "warning": 1,
    "warn": 1,
    "error": 2,
    "critical": 2,
}


def _parse_json_line(line: str) -> dict:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return {}

    if isinstance(payload, dict):
        return payload
    return {}


def _extract_timestamp(line: str) -> datetime | None:
    payload = _parse_json_line(line)
    if payload:
        timestamp_text = payload.get("timestamp") or payload.get("time") or payload.get("datetime")
        if isinstance(timestamp_text, str):
            for format_string in (
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
            ):
                try:
                    return datetime.strptime(timestamp_text, format_string)
                except ValueError:
                    continue

    match = re.search(r"\[(?P<timestamp>[^\]]+)\]", line)
    if not match:
        return None

    timestamp_text = match.group("timestamp")
    for format_string in (
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S,%f",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(timestamp_text, format_string)
        except ValueError:
            continue
    return None


def _extract_log_level(line: str) -> int:
    payload = _parse_json_line(line)
    if payload:
        level_text = str(payload.get("log_level") or payload.get("level") or "").lower()
        if level_text in LOG_LEVEL_MAP:
            return LOG_LEVEL_MAP[level_text]

    upper_line = line.upper()
    for level_name, encoded_value in LOG_LEVEL_MAP.items():
        if level_name.upper() in upper_line:
            return encoded_value
    return LOG_LEVEL_MAP["info"]


def _extract_numeric(pattern: str, text: str, default: float = 0.0) -> float:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return default
    try:
        return float(match.group(1))
    except (TypeError, ValueError):
        return default


def _extract_status_code(line: str) -> int:
    payload = _parse_json_line(line)
    if payload:
        for key in ("status_code", "status", "http_status"):
            value = payload.get(key)
            if value is not None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    continue

    match = re.search(r"\b([1-5]\d{2})\b", line)
    if not match:
        return 0
    return int(match.group(1))


def _extract_service_name(line: str, source_path: str) -> str:
    payload = _parse_json_line(line)
    if payload:
        for key in ("service", "service_name"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value.lower()

    haystack = f"{line} {source_path}".lower()
    for column in SERVICE_COLUMNS:
        service_name = column.replace("service_", "")
        if service_name in haystack:
            return service_name
    return ""


def _extract_message(line: str) -> str:
    payload = _parse_json_line(line)
    if payload:
        for key in ("last_message", "message", "msg", "log_message"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        return line

    parts = line.split(" - ", 1)
    if len(parts) == 2:
        return parts[1].strip()
    return line.strip()


def _infer_service_features(line: str, source_path: str) -> list[int]:
    service_name = _extract_service_name(line, source_path)
    return [1 if service_name == column.replace("service_", "") else 0 for column in SERVICE_COLUMNS]


def _build_base_features(line: str, source_path: str = "") -> dict[str, float | int | str]:
    timestamp = _extract_timestamp(line)
    year = timestamp.year if timestamp else 0
    month = timestamp.month if timestamp else 0
    day = timestamp.day if timestamp else 0
    hour = timestamp.hour if timestamp else 0
    minute = timestamp.minute if timestamp else 0
    second = timestamp.second if timestamp else 0

    payload = _parse_json_line(line)
    return {
        "cpu_percent": float(payload.get("cpu_percent", _extract_numeric(r"cpu(?:_percent)?\s*[:=]\s*(\d+(?:\.\d+)?)", line))),
        "memory_percent": float(payload.get("memory_percent", _extract_numeric(r"memory(?:_percent)?\s*[:=]\s*(\d+(?:\.\d+)?)", line))),
        "disk_percent": float(payload.get("disk_percent", _extract_numeric(r"disk(?:_percent)?\s*[:=]\s*(\d+(?:\.\d+)?)", line))),
        "response_time_ms": float(payload.get("response_time_ms", _extract_numeric(r"response[_\s-]?time(?:_ms)?\s*[:=]\s*(\d+(?:\.\d+)?)", line))),
        "status_code": float(_extract_status_code(line)),
        "log_level": float(_extract_log_level(line)),
        "year": float(year),
        "month": float(month),
        "day": float(day),
        "hour": float(hour),
        "minute": float(minute),
        "second": float(second),
        "service": _extract_service_name(line, source_path),
        "message": _extract_message(line),
    }


def _get_expected_columns(model) -> list[str]:
    feature_names = getattr(model, "feature_names_in_", None)
    if feature_names is not None:
        return [str(name) for name in feature_names]
    return DEFAULT_FEATURE_COLUMNS


def _build_feature_frame(lines: list[str], filepath: str, model) -> pd.DataFrame:
    expected_columns = _get_expected_columns(model)
    records = [_build_base_features(line, filepath) for line in lines]
    frame = pd.DataFrame.from_records(records)

    if frame.empty:
        return pd.DataFrame(columns=expected_columns)

    service_frame = pd.get_dummies(frame["service"], prefix="service")
    service_frame = service_frame.reindex(columns=SERVICE_COLUMNS, fill_value=0)

    vectorizer = TfidfVectorizer(
        vocabulary=TEXT_COLUMNS,
        token_pattern=r"(?u)\b\w+\b",
        lowercase=True,
    )
    message_matrix = vectorizer.fit_transform(frame["message"].fillna("") )
    message_frame = pd.DataFrame(
        message_matrix.toarray(),
        columns=vectorizer.get_feature_names_out(),
        index=frame.index,
    )

    numeric_frame = frame[NUMERIC_COLUMNS].fillna(0).astype(float)
    feature_frame = pd.concat([numeric_frame, service_frame.astype(float), message_frame.astype(float)], axis=1)
    feature_frame = feature_frame.reindex(columns=expected_columns, fill_value=0.0)
    return feature_frame


@lru_cache(maxsize=1)
def load_model():
    from joblib import load
    return load(MODEL_PATH)


def score_log_line(line: str, source_path: str = "", model=None) -> int:
    if model is None:
        model = load_model()

    feature_frame = _build_feature_frame([line], source_path, model)
    prediction = model.predict(feature_frame)[0]
    return int(prediction)

def preprocess_log_lines(lines: list[str], filepath: str = "") -> tuple[list[tuple[int, str]], str]:
    results: list[tuple[int, str]] = []
    anomaly_lines: list[str] = []

    try:
        model = load_model()
    except Exception as exc:
        print(f"Error loading anomaly model from {MODEL_PATH}: {exc}")
        return [], ""

    for line in lines:
        stripped_line = line.strip()

        if not stripped_line:
            continue

        try:
            feature_frame = _build_feature_frame([stripped_line], filepath, model)
            anomaly = int(model.predict(feature_frame)[0])

            results.append((anomaly, stripped_line))

            if anomaly == 1:
                anomaly_lines.append(stripped_line)

            print(f"Anomaly={anomaly} | {stripped_line}")

        except Exception as exc:
            print(f"Error processing line in {filepath}: {exc}")

    aggregated_anomalies = "\n".join(anomaly_lines)

    return results, aggregated_anomalies


# for testing
# def preprocess_log_lines(lines: list[str], filepath: str = "") -> tuple[list[tuple[int, str]], str]:
#     results: list[tuple[int, str]] = []
#     anomaly_lines: list[str] = []

#     try:
#         model = load_model()
#     except Exception as exc:
#         print(f"Error loading anomaly model from {MODEL_PATH}: {exc}")
#         return [], ""

#     # Remove empty lines first
#     valid_lines = [line.strip() for line in lines if line.strip()]

#     # Pick one random line index for testing
#     random_index = random.randint(0, len(valid_lines) - 1) if valid_lines else -1

#     for idx, stripped_line in enumerate(valid_lines):
#         try:
#             feature_frame = _build_feature_frame([stripped_line], filepath, model)
#             anomaly = int(model.predict(feature_frame)[0])

#             # Force one random line to be anomaly for testing
#             if idx == random_index:
#                 anomaly = 1

#             results.append((anomaly, stripped_line))

#             if anomaly == 1:
#                 anomaly_lines.append(stripped_line)

#             print(f"Anomaly={anomaly} | {stripped_line}")

#         except Exception as exc:
#             print(f"Error processing line in {filepath}: {exc}")

#     aggregated_anomalies = "\n".join(anomaly_lines)
#     return results, aggregated_anomalies

def preprocess_log(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as file_handle:
            lines = file_handle.readlines()
        return preprocess_log_lines(lines, filepath)
    except Exception as exc:
        print(f"Error processing {filepath}: {exc}")
        return []
