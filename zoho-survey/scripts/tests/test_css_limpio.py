"""Prueba guardian del CSS: sin codigo muerto y sin reglas repetidas iguales.

Forma parte de la limpieza de hojas de estilo (ver .hermes/plans y ARCHITECTURE.md):
una regla que necesiten el portal y las fichas por periodo se escribe una sola vez, en
shared/css/common.css. Esta prueba es la que evita que la limpieza se deshaga sola.

Se ejecuta con el resto de la suite en GitHub Actions:
    cd zoho-survey/scripts && python -m unittest discover tests/ -v
"""
import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]                      # zoho-survey/
HOJAS = sorted((RAIZ / 'shared' / 'css').glob('**/*.css'))
FUENTES = sorted(RAIZ.glob('**/*.html')) + sorted(RAIZ.glob('shared/js/**/*.js'))

# Clases que a proposito todavia no se usan (agregar aqui con el motivo)
PERMITIDAS = set()
# Tokens que a proposito se conservan sin uso (agregar aqui con el motivo)
PERMITIDOS_TOKENS = set()
HOJA_TOKENS = 'tokens.css'


def _reglas(texto):
    """Reglas del CSS con su selector (incluido el @media que las envuelve)."""
    texto = re.sub(r'/\*.*?\*/', '', texto, flags=re.S)
    reglas, pila, buf, i = [], [], '', 0
    while i < len(texto):
        ch = texto[i]
        if ch == '{':
            sel = re.sub(r'\s+', ' ', buf.strip())
            if sel.startswith('@'):
                pila.append(sel)
            else:
                j = texto.find('}', i)
                cuerpo = re.sub(r'\s+', ' ', texto[i + 1:j]).strip()
                reglas.append((' '.join(pila + [sel]), cuerpo))
                i = j
            buf = ''
        elif ch == '}':
            if pila:
                pila.pop()
            buf = ''
        else:
            buf += ch
        i += 1
    return reglas


class TestCssLimpio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fuentes = '\n'.join(p.read_text(encoding='utf-8', errors='ignore') for p in FUENTES)
        cls.hojas = {str(p.relative_to(RAIZ)): _reglas(p.read_text(encoding='utf-8')) for p in HOJAS}

    def _en_uso(self, nombre):
        """La clase aparece en alguna pagina o modulo; tambien si el programa la arma por trozos."""
        if nombre in self.fuentes:
            return True
        partes = nombre.split('-')
        return any('-'.join(partes[:c]) + '-' in self.fuentes
                   for c in range(len(partes) - 1, 0, -1))

    def test_sin_clases_muertas(self):
        muertas = {}
        for hoja, reglas in self.hojas.items():
            for sel, _ in reglas:
                for nombre in re.findall(r'\.([A-Za-z][\w-]*)', sel):
                    if nombre in PERMITIDAS or self._en_uso(nombre):
                        continue
                    muertas.setdefault(nombre, set()).add(hoja)
        self.assertEqual({}, {c: sorted(h) for c, h in muertas.items()},
                         'clases definidas y nunca usadas: borrarlas o agregarlas a PERMITIDAS')

    def test_sin_reglas_repetidas_iguales(self):
        vistas, repetidas = {}, {}
        for hoja, reglas in self.hojas.items():
            if hoja == HOJA_TOKENS:
                continue
            for sel, cuerpo in reglas:
                if not cuerpo or not sel.strip():
                    continue
                previas = vistas.setdefault(sel, [])
                if any(h != hoja and c == cuerpo for h, c in previas):
                    repetidas[sel] = sorted({h for h, c in previas if c == cuerpo} | {hoja})
                previas.append((hoja, cuerpo))
        self.assertEqual({}, repetidas,
                         'el mismo estilo esta escrito en dos hojas: moverlo a shared/css/common.css')

    def test_sin_tokens_muertos(self):
        hoja = (RAIZ / 'shared' / 'css' / 'tokens.css').read_text(encoding='utf-8')
        definidos = re.findall(r'(--[a-z][\w-]*)\s*:', hoja)
        # tambien cuenta como uso que otro token lo referencie: --x: rgba(var(--y), .15)
        referidos = set(re.findall(r'var\((--[a-z][\w-]*)\)', hoja))
        texto = self.fuentes + '\n'.join(p.read_text(encoding='utf-8')
                                         for p in HOJAS if p.name != HOJA_TOKENS)
        libres = [d for d in definidos if d not in texto and d not in referidos
                  and d not in PERMITIDOS_TOKENS]
        self.assertEqual([], libres, 'tokens definidos y nunca usados')
