"""Standalone Allure reporting utilities (independent of pytest-html and dashboard hooks)."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import allure
import pytest
from playwright.sync_api import Page

from config.settings import settings
from utils.report_dashboard import DEFAULT_JSON, TestResult, summarize

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ALLURE_RESULTS_DIR = PROJECT_ROOT / "allure-results"
ALLURE_REPORT_DIR = PROJECT_ROOT / "allure-report"

_collected_results: list[TestResult] = []


def get_collected_results() -> list[TestResult]:
    return list(_collected_results)


def clear_collected_results() -> None:
    _collected_results.clear()


def record_test_result(result: TestResult) -> None:
    _collected_results.append(result)


def resolve_playwright_page(item: pytest.Item) -> Page | None:
    """Find the Playwright page from test fixtures or page objects."""
    for name in ("page", "authenticated_page"):
        if name in item.funcargs:
            return item.funcargs[name]
    for value in item.funcargs.values():
        page = getattr(value, "page", None)
        if page is not None:
            return page
    return None


def _safe_screenshot_name(nodeid: str) -> str:
    return re.sub(r"[^\w.-]+", "_", nodeid)


def save_failure_screenshot(page: Page, nodeid: str) -> Path:
    settings.screenshot_dir.mkdir(parents=True, exist_ok=True)
    path = settings.screenshot_dir / f"{_safe_screenshot_name(nodeid)}.png"
    page.screenshot(path=str(path), full_page=True)
    return path


def attach_failure_screenshot_to_allure(page: Page, nodeid: str) -> Path | None:
    try:
        screenshot_path = save_failure_screenshot(page, nodeid)
        allure.attach.file(
            str(screenshot_path),
            name="Failure screenshot",
            attachment_type=allure.attachment_type.PNG,
        )
        return screenshot_path
    except Exception as exc:
        allure.attach(
            str(exc),
            name="Screenshot error",
            attachment_type=allure.attachment_type.TEXT,
        )
        return None


def apply_test_labels(item: pytest.Item) -> None:
    module_name = Path(item.fspath).stem
    allure.dynamic.feature(module_name)
    allure.dynamic.story(item.name)


def _write_properties_file(path: Path, properties: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}={value}" for key, value in properties.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_environment_properties(
    *,
    started_at: datetime | None = None,
    duration_seconds: float = 0.0,
    exit_status: int = 0,
    results_summary: dict[str, Any] | None = None,
) -> Path:
    """Write Allure environment.properties for the current run."""
    started = started_at or datetime.now(timezone.utc)
    properties: dict[str, str] = {
        "Project": "Dream Team Automation",
        "Base.URL": settings.base_url,
        "Browser": settings.browser,
        "Headless": str(settings.headless),
        "Started.At": started.isoformat(),
        "Duration.Seconds": f"{duration_seconds:.2f}",
        "Exit.Status": str(exit_status),
        "Pytest.HTML.Report": "reports/report.html",
        "Dashboard.Report": "reports/dashboard.html",
        "Results.JSON": "reports/results.json",
    }

    if results_summary:
        counts = results_summary.get("counts", {})
        properties["Tests.Total"] = str(results_summary.get("total", 0))
        properties["Tests.Passed"] = str(counts.get("passed", 0))
        properties["Tests.Failed"] = str(counts.get("failed", 0))
        properties["Tests.Skipped"] = str(counts.get("skipped", 0))
        properties["Tests.Pass.Rate"] = f"{results_summary.get('pass_rate', 0)}%"

    target = ALLURE_RESULTS_DIR / "environment.properties"
    _write_properties_file(target, properties)
    return target


def _load_results_json(json_path: Path) -> dict[str, Any] | None:
    if not json_path.is_file():
        return None
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def sync_pytest_results_json(
    json_path: Path = DEFAULT_JSON,
    *,
    results_dir: Path = ALLURE_RESULTS_DIR,
) -> Path | None:
    """
    Copy reports/results.json into allure-results and align environment metadata
    with the dashboard pytest outcome summary.
    """
    if not json_path.is_file():
        return None

    results_dir.mkdir(parents=True, exist_ok=True)
    target = results_dir / "pytest-results.json"
    shutil.copy2(json_path, target)
    return target


def attach_results_summary_to_allure(
    results: list[TestResult],
    *,
    results_dir: Path = ALLURE_RESULTS_DIR,
) -> Path | None:
    """Write a compact JSON summary derived from collected pytest TestResult rows."""
    if not results:
        return None

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summarize(results),
        "tests": [
            {
                "nodeid": item.nodeid,
                "outcome": item.outcome,
                "duration": item.duration,
                "module": item.module,
            }
            for item in results
        ],
    }
    results_dir.mkdir(parents=True, exist_ok=True)
    target = results_dir / "pytest-results-summary.json"
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target


def finalize_allure_session(
    results: list[TestResult],
    *,
    started_at: datetime | None = None,
    duration_seconds: float = 0.0,
    exit_status: int = 0,
    results_json_path: Path = DEFAULT_JSON,
    results_dir: Path = ALLURE_RESULTS_DIR,
) -> None:
    """
    Post-run Allure enrichment: environment, pytest results.json sync, and summary file.
    Intended to run after the dashboard hook writes reports/results.json.
    """
    results_dir.mkdir(parents=True, exist_ok=True)

    dashboard_payload = _load_results_json(results_json_path)
    results_summary = dashboard_payload.get("summary") if dashboard_payload else summarize(results)

    write_environment_properties(
        started_at=started_at,
        duration_seconds=duration_seconds,
        exit_status=exit_status,
        results_summary=results_summary,
    )
    sync_pytest_results_json(results_json_path, results_dir=results_dir)
    attach_results_summary_to_allure(results, results_dir=results_dir)
