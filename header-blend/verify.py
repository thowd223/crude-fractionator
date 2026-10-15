"""Independent check of the header blending math in index.html.

Re-implements the mixing in plain Python (not translated from the JS) and
prints a hand-checkable worked case plus balance checks. Run: python3 verify.py
"""
MW  = {"H2":2.016,"CH4":16.043,"C2H4":28.054,"C2H6":30.070,"C3H6":42.081,"C3H8":44.097,
       "C4":58.123,"C5+":72.15,"N2":28.013,"CO2":44.010,"H2S":34.081}
LHV = {"H2":10.79,"CH4":35.81,"C2H4":59.03,"C2H6":63.74,"C3H6":86.00,"C3H8":91.25,
       "C4":118.4,"C5+":146.0,"N2":0,"CO2":0,"H2S":23.38}   # MJ/Nm3, 0 C / 1 atm, ideal gas
C = list(MW)
S = {  # kmol/h, mol% in order of C
 "FCC":(900,[18,38,15,16,3,2,1,0.3,5,1.69,0.010]),
 "DHT":(300,[60,20,0,10,0,6,2,0,1.995,0,0.005]),
 "CDU":(150,[2,25,0,20,0,28,15,6,2,1.99,0.010]),
 "CCR":(400,[82,8,0,5,0,3,1.5,0.5,0,0,0]),
 "DCU":(500,[12,50,3,18,3,7,3,1,1,1.98,0.020]),
 "NG" :(250,[0,92,0,4,0,1,0,0,2,1,0]),
}
def blend(flows):
    comp_kmol = {c:0.0 for c in C}
    for name,F in flows.items():
        y = S[name][1]; t = sum(y)
        for c,v in zip(C,y): comp_kmol[c] += F*v/t
    Ftot = sum(flows.values())
    x = {c:comp_kmol[c]/Ftot for c in C}
    mw = sum(x[c]*MW[c] for c in C); lhv = sum(x[c]*LHV[c] for c in C)
    sg = mw/28.964
    return dict(F=Ftot, x=x, kmol=comp_kmol, mw=mw, lhv=lhv, wobbe=lhv/sg**0.5,
                duty_GJh=Ftot*22.414*lhv/1000, h2s_ppm=x["H2S"]*1e6)

base = {k:v[0] for k,v in S.items()}
coker_off = dict(base, DCU=0)
for label, case in [("Base, all units on", base), ("Coker shut down", coker_off)]:
    r = blend(case)
    print(f"\n{label}\n  flow {r['F']:.0f} kmol/h  MW {r['mw']:.2f}  LHV {r['lhv']:.1f} MJ/Nm3  "
          f"Wobbe {r['wobbe']:.1f}  H2S {r['h2s_ppm']:.0f} ppmv  duty {r['duty_GJh']:.0f} GJ/h")
    # balance checks
    assert abs(sum(r['x'].values())-1) < 1e-12, "mol fractions must sum to 1"
    assert abs(sum(r['kmol'].values())-r['F']) < 1e-9, "component kmol must sum to total"
    print("  checks: sum(x)=1 OK, component balance OK")

# NG make-up that restores base heat duty when the coker is off
b = blend(base); off = blend(dict(coker_off, NG=0))
ng_lhv = blend({"NG":1})["lhv"]
ng = (b["duty_GJh"]-off["duty_GJh"])*1000/22.414/ng_lhv
held = blend(dict(coker_off, NG=ng))
print(f"\nCoker off, NG make-up held: NG {ng:.0f} kmol/h, duty {held['duty_GJh']:.0f} vs base {b['duty_GJh']:.0f} GJ/h")
assert abs(held["duty_GJh"]-b["duty_GJh"]) < 1e-6

# Hand-checkable case: equal kmol of pure H2 and pure CH4 -> 50/50 mix
mw = 0.5*2.016+0.5*16.043; lhv = 0.5*10.79+0.5*35.81
print(f"\nHand check, 50/50 H2/CH4: MW {mw:.3f} (=(2.016+16.043)/2), LHV {lhv:.2f} (=(10.79+35.81)/2)")
