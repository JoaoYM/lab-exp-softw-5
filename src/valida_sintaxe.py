#!/usr/bin/env python3
"""Valida a sintaxe dos scripts Python do projeto."""
import sys
import ast

scripts = ["mineracao.py", "analise.py"]
tudo_ok = True

for script in scripts:
    try:
        with open(script, encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
        print(f"✅ {script}: sintaxe OK")
    except SyntaxError as e:
        print(f"❌ {script}: erro de sintaxe - {e}")
        tudo_ok = False

sys.exit(0 if tudo_ok else 1)