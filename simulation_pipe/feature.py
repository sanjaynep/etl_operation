from __future__ import annotations

import pickle
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path


MODEL_PATH = Path(__file__).with_name("anomalymodel.pkl")

FEATURE_COLUMNS = [
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "response_time_ms",
    "status_code",
    "log_level",
    "year",
    "month",
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
]

SERVICE_COLUMNS = [column for column in FEATURE_COLUMNS if column.startswith("service_")]

LOG_LEVEL_MAP = {
    "debug": 0,
    "info": 1,
    "warning": 2,
    "warn": 2,
    "error": 3,
    "critical": 4,
}


def _extract_timestamp(line: str) -> datetime | None:
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
    match = re.search(r"\b([1-5]\d{2})\b", line)
    if not match:
        return 0
    return int(match.group(1))


def _infer_service_features(line: str, source_path: str) -> list[int]:
    haystack = f"{line} {source_path}".lower()
    features = []
    for column in SERVICE_COLUMNS:
        service_name = column.replace("service_", "")
        features.append(1 if service_name in haystack else 0)
    return features


def build_feature_vector(line: str, source_path: str = "") -> list[float]:
    timestamp = _extract_timestamp(line)
    year = timestamp.year if timestamp else 0
    month = timestamp.month if timestamp else 0
    hour = timestamp.hour if timestamp else 0
    minute = timestamp.minute if timestamp else 0
    second = timestamp.second if timestamp else 0

    feature_vector = [
        _extract_numeric(r"cpu(?:_percent)?\s*[:=]\s*(\d+(?:\.\d+)?)", line),
        _extract_numeric(r"memory(?:_percent)?\s*[:=]\s*(\d+(?:\.\d+)?)", line),
        _extract_numeric(r"disk(?:_percent)?\s*[:=]\s*(\d+(?:\.\d+)?)", line),
        _extract_numeric(r"response[_\s-]?time(?:_ms)?\s*[:=]\s*(\d+(?:\.\d+)?)", line),
        float(_extract_status_code(line)),
        float(_extract_log_level(line)),
        float(year),
        float(month),
        float(hour),
        float(minute),
        float(second),
    ]
    feature_vector.extend(float(value) for value in _infer_service_features(line, source_path))
    return feature_vector


@lru_cache(maxsize=1)
def load_model():
    with open(MODEL_PATH, "rb") as model_file:
        return pickle.load(model_file)


def score_log_line(line: str, source_path: str = "", model=None) -> int:
    if model is None:
        model = load_model()
    feature_vector = build_feature_vector(line, source_path)
    prediction = model.predict([feature_vector])[0]
    return int(prediction)


def preprocess_log_lines(lines: list[str], filepath: str = "") -> list[int | None]:
    results: list[int | None] = []
    try:
        model = load_model()
    except Exception as exc:
        print(f"Error loading anomaly model from {MODEL_PATH}: {exc}")
        return []

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue

        try:
            anomaly = score_log_line(stripped_line, filepath, model=model)
            results.append(anomaly)
            print(f"{anomaly} | {stripped_line}")
        except Exception as exc:
            print(f"Error processing line in {filepath}: {exc}")
            results.append(None)
    return results


def preprocess_log(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as file_handle:
            lines = file_handle.readlines()
        return preprocess_log_lines(lines, filepath)
    except Exception as exc:
        print(f"Error processing {filepath}: {exc}")
        return []
