"""
HTML CONTRACT TEST — Validación del orden de carga de scripts en archivos HTML.

Verifica que los archivos HTML del proyecto respeten el orden canónico de scripts
documentado en ARCHITECTURE.md. Esto previene errores de dependencia en runtime
como TypeError: window.SurveyDomHelpers is undefined.

Ejecutar en CI (tests.yml) o localmente con:
    python -m pytest zoho-survey/scripts/tests/test_html_contract.py -v
"""

import unittest
import re
from pathlib import Path


# Rutas base
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent  # survey-storytelling/
ZOHO_DIR = ROOT_DIR / "zoho-survey"

# Orden canónico del template (13 scripts: template/index.html → dashboards individuales)
TEMPLATE_SCRIPT_ORDER = [
    "config/constants.js",
    "utils/formatters.js",
    "utils/metrics.js",
    "utils/sanitizer.js",
    "utils/dom-helpers.js",
    "components/tooltip.js",
    "components/progress-bar.js",
    "components/custom-select.js",
    "components/multiselect.js",
    "components/filter-controller.js",
    "components/radar-chart.js",
    "components/sentiment-view.js",
    "dashboard.js",
]

# Orden canónico del portal v5.0 (14 scripts: index.html → portal multi-fase)
PORTAL_SCRIPT_ORDER = [
    "config/constants.js",
    "utils/sanitizer.js",
    "components/tooltip.js",
    "utils/dom-helpers.js",
    "utils/formatters.js",
    "components/sentiment-view.js",
    "components/custom-select.js",
    "components/multiselect.js",
    "portal/portal-data.js",
    "portal/portal-dashboard.js",
    "portal/portal-radar.js",
    "portal/portal-filters.js",
    "portal/portal-survey.js",
    "portal.js",
]


def _extract_scripts(html_path: Path) -> list:
    """Extrae la lista de rutas de scripts (relativas a shared/js/) desde un HTML."""
    content = html_path.read_text(encoding="utf-8")
    # Capturar src="...js" - captura todo lo que termina en .js (incluyendo subdirectorios)
    pattern = re.compile(r'<script[^>]+src="([^"]*\.js)(?:\?[^"]*)?"')
    scripts = []
    for match in pattern.finditer(content):
        full_src = match.group(1)
        # Normalizar: extraer la parte relativa a shared/js/
        # Ej: "shared/js/config/constants.js" → "config/constants.js"
        # Ej: "shared/js/portal/portal-data.js" → "portal/portal-data.js"
        parts = full_src.replace("\\", "/").split("shared/js/")
        if len(parts) > 1:
            scripts.append(parts[-1])
        else:
            # Si no tiene shared/js/, mantener el path completo sin query string
            scripts.append(full_src.split("?")[0])
    return scripts


def _check_order(actual: list, expected: list) -> list:
    """Verifica que los elementos de 'expected' aparezcan en 'actual' en el orden correcto.
    Retorna lista de mensajes de error (vacía si todo OK)."""
    errors = []
    # Mapear índice de cada script esperado en la lista real
    prev_idx = -1
    for expected_script in expected:
        found = False
        for i, actual_script in enumerate(actual):
            if actual_script.endswith(expected_script) or expected_script.endswith(actual_script):
                if i <= prev_idx and prev_idx != -1:
                    errors.append(
                        f"Orden incorrecto: '{expected_script}' (índice {i}) "
                        f"debe aparecer después del script anterior (índice {prev_idx})"
                    )
                prev_idx = i
                found = True
                break
        if not found:
            errors.append(f"Script no encontrado: '{expected_script}'")
    return errors


def _check_critical_order(actual: list, before: str, after: str) -> list:
    """Verifica que 'before' aparezca antes que 'after' en la lista."""
    errors = []
    idx_before = next((i for i, s in enumerate(actual) if before in s), -1)
    idx_after = next((i for i, s in enumerate(actual) if after in s), -1)
    
    if idx_before == -1:
        errors.append(f"Script requerido no encontrado: '{before}'")
    if idx_after == -1:
        errors.append(f"Script requerido no encontrado: '{after}'")
    if idx_before != -1 and idx_after != -1 and idx_before >= idx_after:
        errors.append(
            f"CRÍTICO: '{before}' (índice {idx_before}) debe cargarse antes que "
            f"'{after}' (índice {idx_after})"
        )
    return errors


class TestHTMLContracts(unittest.TestCase):
    """Validación de contratos HTML: orden de carga de scripts."""

    def test_template_script_order(self):
        """Verifica que template/index.html cargue los 13 scripts en el orden canónico."""
        template_path = ZOHO_DIR / "template" / "index.html"
        if not template_path.exists():
            self.skipTest(f"Template no encontrado: {template_path}")
        
        scripts = _extract_scripts(template_path)
        errors = _check_order(scripts, TEMPLATE_SCRIPT_ORDER)
        self.assertEqual(len(errors), 0, msg="\n" + "\n".join(errors))

    def test_portal_script_order(self):
        """Verifica que index.html (portal v5.0) cargue los 14 scripts en el orden canónico."""
        portal_path = ZOHO_DIR / "index.html"
        if not portal_path.exists():
            self.skipTest(f"Portal no encontrado: {portal_path}")
        
        scripts = _extract_scripts(portal_path)
        errors = _check_order(scripts, PORTAL_SCRIPT_ORDER)
        self.assertEqual(len(errors), 0, msg="\n" + "\n".join(errors))

    def test_dom_helpers_before_custom_select_in_portal(self):
        """Verifica que dom-helpers.js se cargue antes que custom-select.js en el portal."""
        portal_path = ZOHO_DIR / "index.html"
        if not portal_path.exists():
            self.skipTest(f"Portal no encontrado: {portal_path}")
        
        scripts = _extract_scripts(portal_path)
        errors = _check_critical_order(
            scripts,
            before="dom-helpers.js",
            after="custom-select.js"
        )
        self.assertEqual(len(errors), 0, msg="\n" + "\n".join(errors))

    def test_dom_helpers_before_custom_select_in_template(self):
        """Verifica que dom-helpers.js se cargue antes que custom-select.js en el template."""
        template_path = ZOHO_DIR / "template" / "index.html"
        if not template_path.exists():
            self.skipTest(f"Template no encontrado: {template_path}")
        
        scripts = _extract_scripts(template_path)
        errors = _check_critical_order(
            scripts,
            before="dom-helpers.js",
            after="custom-select.js"
        )
        self.assertEqual(len(errors), 0, msg="\n" + "\n".join(errors))

    def test_portal_critical_dependencies(self):
        """Verifica dependencias críticas de carga en el portal."""
        portal_path = ZOHO_DIR / "index.html"
        if not portal_path.exists():
            self.skipTest(f"Portal no encontrado: {portal_path}")
        
        scripts = _extract_scripts(portal_path)
        errors = []
        
        # portal-data.js debe cargar antes que módulos portal que lo consumen
        for dep in ["portal/portal-dashboard.js", "portal/portal-radar.js", 
                    "portal/portal-filters.js", "portal/portal-survey.js"]:
            errors.extend(_check_critical_order(scripts, "portal/portal-data.js", dep))
        
        # portal-filters.js antes que portal-survey.js (portal-survey usa SurveyPortalFilters)
        errors.extend(_check_critical_order(scripts, "portal/portal-filters.js", "portal/portal-survey.js"))
        
        # portal.js último (orquestador)
        for dep in ["config/constants.js", "utils/sanitizer.js", "components/tooltip.js",
                    "utils/dom-helpers.js", "utils/formatters.js", "components/sentiment-view.js",
                    "components/custom-select.js", "components/multiselect.js",
                    "portal/portal-data.js", "portal/portal-dashboard.js", "portal/portal-radar.js",
                    "portal/portal-filters.js", "portal/portal-survey.js"]:
            errors.extend(_check_critical_order(scripts, dep, "portal.js"))
        
        self.assertEqual(len(errors), 0, msg="\n" + "\n".join(errors))

    def test_period_html_script_order(self):
        """Verifica que todos los index.html de periodo sigan el orden canónico del template."""
        errors_all = []
        students_dir = ZOHO_DIR / "students"
        if not students_dir.exists():
            self.skipTest(f"Directorio students/ no encontrado: {students_dir}")
        
        for html_file in students_dir.rglob("index.html"):
            scripts = _extract_scripts(html_file)
            errs = _check_order(scripts, TEMPLATE_SCRIPT_ORDER)
            if errs:
                errors_all.append(f"{html_file.relative_to(ROOT_DIR)}:\n  " + "\n  ".join(errs))
        
        self.assertEqual(len(errors_all), 0, msg="\n" + "\n".join(errors_all))


if __name__ == '__main__':
    unittest.main()