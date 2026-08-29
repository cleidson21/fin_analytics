import os
import sys

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.integrations.myprofit.parser import MyProfitParser, parse_pt_br_amount

def test_parse_amount():
    cases = [
        ("R$ 1.033,31", 1033.31),
        ("R$ 5,3096", 5.3096),
        ("51,43 %", 51.43),
        ("0,24", 0.24),
        ("-R$ 18,63", -18.63),
        ("-3,47 %", -3.47),
        ("R$ 468.146,30", 468146.30),
        ("100.00 %", 100.00), # In case of US format mix
        ("-", None),
        ("", None),
    ]
    for val, expected in cases:
        res = parse_pt_br_amount(val)
        assert res == expected, f"Failed for {val}: got {res}, expected {expected}"
    print("parse_pt_br_amount tests passed!")

def test_csv_reading():
    files = [
        "Exemplo_Ativos_Myprofit.csv",
        "Exemplo_Evolucao_carteira_Myprofit.csv",
        "Exemplo_Proventos_Myprofit.csv",
    ]
    for f in files:
        if not os.path.exists(f):
            print(f"Skipping {f} (not found)")
            continue
            
        with open(f, 'rb') as file:
            content = file.read()
            
        parser = MyProfitParser(content)
        rows = parser.parse()
        print(f"\n{f}: {len(rows)} rows parsed.")
        if rows:
            print(f"Columns: {list(rows[0].keys())}")
            print(f"Sample row 1: {rows[0]}")

if __name__ == "__main__":
    test_parse_amount()
    test_csv_reading()
