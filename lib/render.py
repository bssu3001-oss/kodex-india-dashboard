import json
import os

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "templates", "dashboard.html")
PLACEHOLDER = "__DASHBOARD_DATA__"


def render_dashboard(data, output_path):
    """
    Load the HTML template, inject data JSON, write output file.
    Replaces __DASHBOARD_DATA__ in the template script tag with JSON.
    """
    template_path = os.path.normpath(TEMPLATE_PATH)
    with open(template_path, encoding="utf-8") as f:
        html = f.read()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html = html.replace(PLACEHOLDER, payload, 1)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
