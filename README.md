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
│   ├── test_login_page.py
│   ├── test_forgot_password_page.py
│   └── test_dashboard_page.py
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
# All tests (headless by default; HTML report at reports/report.html)
pytest

# Smoke tests only
pytest -m smoke

# Dashboard tests (requires auth/storage_state.json)
pytest -m dashboard

# With browser visible
$env:HEADLESS="false"; pytest

# Custom HTML report path
pytest --html=reports/custom-report.html --self-contained-html

# Specific file
pytest tests/test_login_page.py -v
```

Open `reports/report.html` in a browser after each run to view pass/fail details.

On failure, a full-page screenshot is saved under `screenshots/` and embedded in the HTML report.

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
| `HEADLESS` | `true` | Headless mode |
| `DEFAULT_TIMEOUT` | `30000` | Playwright timeout (ms) |
| `TEST_USER_EMAIL` | — | Optional login email |
| `TEST_USER_PASSWORD` | — | Optional login password |

## Authenticated / dashboard tests

Dashboard tests reuse a saved Playwright session so MFA is not required on every run.

**One-time setup (headed — complete MFA in the browser):**

```powershell
$env:HEADLESS="false"
python scripts/save_auth_and_explore_dashboard.py
```

This creates `auth/storage_state.json`. Then run:

```powershell
pytest tests/test_dashboard_page.py -m dashboard -v
```

## Adding new pages

1. Create `pages/your_page.py` extending `BasePage`.
2. Set `path` and define locators in `__init__`.
3. Add action and assertion methods.
4. Export from `pages/__init__.py`.
5. Add a fixture in `conftest.py` if needed.
6. Write tests under `tests/`.

## CI example

```yaml
- run: pip install -r requirements.txt && playwright install --with-deps chromium
- run: pytest -m smoke --html=report.html
```
