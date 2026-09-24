"""
Hook PostToolUse: controlla che l'output degli agenti non contenga
linguaggio da consulenza finanziaria vietato.
"""
import sys
import re

PATTERN_VIETATI = [
    r'\bti consiglio\b',
    r'\bdovresti\b',
    r'\bconviene fare\b',
    r'\bti conviene\b',
    r'\bla scelta migliore\b',
    r'\bscegli\b',
    r'\bpreferisci\b',
    r'\binvestire in\b',
]

def main():
    output = sys.stdin.read() if not sys.argv[1:] else ' '.join(sys.argv[1:])
    output_lower = output.lower()

    trovati = []
    for pattern in PATTERN_VIETATI:
        if re.search(pattern, output_lower):
            trovati.append(pattern)

    if trovati:
        print(f"[VALIDATE] ATTENZIONE: output contiene linguaggio da consulenza finanziaria: {trovati}", file=sys.stderr)
        print("[VALIDATE] Rimandare l'utente a un CAF o commercialista per consigli personalizzati.", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
