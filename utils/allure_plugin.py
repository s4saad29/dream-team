"""
Pytest plugin for Allure reporting.

Loaded via pytest.ini (plugins = utils.allure_plugin). Does not modify conftest.py,
pytest-html, or dashboard collection behavior.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from utils.allure_reporting import (
    apply_test_labels,
    attach_failure_screenshot_to_allure,
    clear_collected_results,
    finalize_allure_session,
    generate_allure_html_report,
    get_collected_results,
    record_test_result,
    resolve_playwright_page,
)
from utils.report_dashboard import DEFAULT_JSON, TestResult

_session_started_at: datetime | None = None


def pytest_sessionstart(session: pytest.Session) -> None:
    global _session_started_at
    clear_collected_results()
    _session_started_at = datetime.now(timezone.utc)


def pytest_runtest_setup(item: pytest.Item) -> None:
    apply_test_labels(item)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        record_test_result(
            TestResult(
                nodeid=item.nodeid,
                outcome=report.outcome,
                duration=report.duration,
                module=Path(item.fspath).name,
            )
        )

    if report.when != "call" or not report.failed:
        return

    page = resolve_playwright_page(item)
    if page is None:
        return

    attach_failure_screenshot_to_allure(page, item.nodeid)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    started = _session_started_at or datetime.now(timezone.utc)
    duration = (datetime.now(timezone.utc) - started).total_seconds()
    finalize_allure_session(
        get_collected_results(),
        started_at=started,
        duration_seconds=duration,
        exit_status=exitstatus,
        results_json_path=DEFAULT_JSON,
    )

    try:
        report_index = generate_allure_html_report()
    except RuntimeError as exc:
        print(f"\nAllure report generation failed: {exc}")
        print("Raw results saved in allure-results/")
        print("Retry manually: .\\scripts\\allure_report.ps1")
    else:
        if report_index:
            print(f"\nAllure report: {report_index}")
        else:
            print("\nAllure results: allure-results/")
            print(
                "Install Allure CLI (scoop/choco) or run "
                "`npm install --save-dev allure-commandline`, then re-run pytest."
            )
