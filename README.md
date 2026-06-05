# Dream Team Automation

Playwright + pytest automation framework using the **Page Object Model (POM)** for [Addo Dream Team](https://team.addo.ai/).

## Project structure

```
DreamTeam Automation/
├── config/
│   └── settings.py          # Environment and runtime settings
├── auth/                    # Saved session (gitignored); see scripts below
├── pages/
│   ├── base_page.py         # Shared page behavior
│   ├── login_page.py        # Login page object
│   ├── dashboard_page.py    # Dashboard page object
│   └── ...
├── tests/
│   ├── conftest.py            # Registers Allure plugin only
│   ├── test_login_page.py
│   ├── test_forgot_password_page.py
│   ├── test_profile_page.py
│   ├── test_dashboard_page.py
│   └── test_logout_page.py
├── utils/
│   ├── auth_helper.py         # SSO login and storage_state helpers
│   ├── allure_reporting.py    # Standalone Allure helpers
│   └── allure_plugin.py       # Pytest plugin (registered in pytest.ini)
├── scripts/
│   └── save_auth_and_explore_dashboard.py
├── conftest.py              # Pytest fixtures
├── pytest.ini
├── requirements.txt
└── .env.example
```

## Prerequisites

- Python 3.10+
- Windows / macOS / Linux

## Setup

```powershell
cd "d:\DreamTeam Automation"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
copy .env.example .env
```

Edit `.env` and optionally set credentials for authenticated tests:

```env
TEST_USER_EMAIL=your@email.com
TEST_USER_PASSWORD=your-password
```

## Running tests

```powershell
# All tests (headed by default; HTML report at reports/report.html)
pytest

# Smoke tests only
pytest -m smoke

# Dashboard tests (requires auth/storage_state.json)
pytest -m dashboard

# Run headless (override default)
$env:HEADLESS="true"; pytest

# Custom HTML report path
pytest --html=reports/custom-report.html --self-contained-html

# Specific file
pytest tests/test_login_page.py -v
```

Open `reports/report.html` in a browser after each run to view pass/fail details.

A visual **test dashboard** with a pass/fail pie chart is generated automatically at `reports/dashboard.html` (raw data in `reports/results.json`).

```powershell
start reports/dashboard.html
```

On failure, a full-page screenshot is saved under `screenshots/` and embedded in the HTML report.

### Allure report

Each `pytest` run writes raw results to `allure-results/` and **automatically generates** `allure-report/index.html` when the Allure CLI is available (PATH, or `node_modules/.bin/allure` after `npm install --save-dev allure-commandline`).

```powershell
pytest
start allure-report/index.html
```

Manual regenerate or serve only:

```powershell
.\scripts\allure_report.ps1
.\scripts\allure_report.ps1 -ServeOnly
```

## Playwright codegen (pytest)

Record browser actions and generate **pytest** test code with the Playwright Inspector:

```powershell
# Login page (default)
.\scripts\codegen.ps1

# Dashboard (loads auth/storage_state.json if it exists)
.\scripts\codegen.ps1 -Dashboard

# Save generated script to a file
.\scripts\codegen.ps1 -Dashboard -Output tests\generated\recorded_test.py
```

Manual command (same as the script):

```powershell
playwright codegen --target=python-pytest https://team.addo.ai/login
playwright codegen --target=python-pytest --load-storage=auth/storage_state.json https://team.addo.ai/dashboard
```

Copy useful locators from the inspector into `pages/` page objects, then add proper tests under `tests/`.

## Page Object Model

Each page class extends `BasePage` and encapsulates:

- Locators (selectors)
- User actions (`login`, `click_forgot_password`, etc.)
- Assertions (`assert_on_login_page`, `assert_login_form_visible`)

Example:

```python
from pages.login_page import LoginPage

def test_example(page):
    login = LoginPage(page)
    login.navigate()
    login.fill_email("user@example.com")
    login.fill_password("secret")
    login.click_login()
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `https://team.addo.ai` | Application base URL |
| `BROWSER` | `chromium` | Browser engine |
| `HEADLESS` | `false` | Headless mode (set `true` to run without UI) |
| `DEFAULT_TIMEOUT` | `30000` | Playwright timeout (ms) |
| `TEST_USER_EMAIL` | — | Optional login email |
| `TEST_USER_PASSWORD` | — | Optional login password |

## Authenticated / dashboard tests

Dashboard and profile tests reuse a saved Playwright session (`auth/storage_state.json`) so MFA is not required on every run.

**Full suite (recommended):** When `TEST_USER_EMAIL` and `TEST_USER_PASSWORD` are set in `.env`, the Microsoft SSO login test runs last in the login module and **automatically saves** a fresh `auth/storage_state.json` before profile and dashboard tests run.

```powershell
pytest -v
```

**One-time setup (headed — complete MFA in the browser):** Use this when running only dashboard/profile tests without the login module, or when credentials are not in `.env`:

```powershell
$env:HEADLESS="false"
python scripts/save_auth_and_explore_dashboard.py
```

Then run authenticated tests:

```powershell
pytest tests/test_dashboard_page.py -m dashboard -v
```

If tokens expire mid-run, `conftest.py` will attempt to re-authenticate via Microsoft SSO when credentials are available.

## Adding new pages

1. Create `pages/your_page.py` extending `BasePage`.
2. Set `path` and define locators in `__init__`.
3. Add action and assertion methods.
4. Export from `pages/__init__.py`.
5. Add a fixture in `conftest.py` if needed.
6. Write tests under `tests/`.

## CI

GitHub Actions workflow [`.github/workflows/tests.yml`](.github/workflows/tests.yml) runs two jobs:

| Job | Scope | Secrets |
|-----|-------|---------|
| **smoke** | Login + forgot password UI tests | None |
| **authenticated** | Microsoft SSO login, profile, dashboard, logout | `TEST_USER_EMAIL`, `TEST_USER_PASSWORD`; optional `AUTH_STORAGE_STATE` (base64-encoded `auth/storage_state.json` to skip MFA in CI) |

To generate `AUTH_STORAGE_STATE` locally:

```powershell
python scripts/save_auth_and_explore_dashboard.py
[Convert]::ToBase64String([IO.File]::ReadAllBytes("auth/storage_state.json"))
```

Add the output as a repository secret in GitHub.
