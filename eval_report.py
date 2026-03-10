import django, os, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jorise.settings')
django.setup()

from training.models import TrainingJob

jobs = [
    'Friday-PortScan-CSV', 'Friday-DDos-CSV', 'Friday-Morning-CSV',
    'Thursday-Afternoon-CSV', 'Thursday-Morning-CSV', 'Wednesday-CSV',
    'Tuesday-CSV', 'Monday-CSV',
]

print("=" * 70)
print(f"{'MODEL':<30} {'ACC':>8} {'F1':>8} {'PREC':>8} {'REC':>8}")
print("=" * 70)

for name in jobs:
    j = TrainingJob.objects.filter(model_name=name, algorithm='random_forest').first()
    if not j:
        continue
    acc  = f"{j.accuracy*100:.3f}%" if j.accuracy  is not None else "N/A"
    f1   = f"{j.f1_score*100:.3f}%" if j.f1_score  is not None else "N/A"
    prec = f"{j.precision*100:.3f}%" if j.precision is not None else "N/A"
    rec  = f"{j.recall*100:.3f}%"    if j.recall   is not None else "N/A"
    print(f"{name:<30} {acc:>9} {f1:>9} {prec:>9} {rec:>9}")

print()
print("=" * 70)
print("PER-CLASS BREAKDOWN")
print("=" * 70)

for name in jobs:
    j = TrainingJob.objects.filter(model_name=name, algorithm='random_forest').first()
    if not j or not j.report_json:
        continue
    r = j.report_json if isinstance(j.report_json, dict) else json.loads(j.report_json)
    print(f"\n--- {name} ---")
    for cls, vals in r.items():
        if isinstance(vals, dict) and 'f1-score' in vals:
            p  = vals['precision']
            rc = vals['recall']
            f  = vals['f1-score']
            s  = int(vals['support'])
            flag = " <<<" if f < 0.5 and s > 0 else ""
            print(f"  {str(cls):<35} P={p:.3f}  R={rc:.3f}  F1={f:.3f}  n={s:>7}{flag}")
