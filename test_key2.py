from utils.diff import _key, _normalize_id, _normalize_syscode

# Two QM002-QM01 rows from the drawing
r1 = {"component_id": "QM002-QM01", "system_code": "Z02RAE30", "x": 4152, "y": 1707}
r2 = {"component_id": "QM002-QM01", "system_code": "Z02NHC10", "x": 3528, "y": 4400}

# Same QM002-QM01 in new version
r1_new = {"component_id": "QM002-QM01", "system_code": "Z02NHC20", "x": 4152, "y": 1649}
r2_new = {"component_id": "QM002-QM01", "system_code": "Z02NHC10", "x": 3528, "y": 4400}

print("r1 key:      ", _key(r1))
print("r2 key:      ", _key(r2))
print("r1_new key:  ", _key(r1_new))
print("r2_new key:  ", _key(r2_new))
print()
print("r1 == r2:    ", _key(r1) == _key(r2), "(should be False — different system codes)")
print("r1 == r1_new:", _key(r1) == _key(r1_new), "(should be False — sys changed RAE30→NHC20)")
print("r2 == r2_new:", _key(r2) == _key(r2_new), "(should be True  — identical)")