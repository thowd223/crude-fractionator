# Generates example_units.json: 15 ILLUSTRATIVE units (not plant data). Run: python3 make_example_data.py
import json
import os
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"example_units.json")
comps=[("H2","Hydrogen",2.016,285.83,1,"h2"),("CH4","Methane",16.043,890.56,2,"c1"),
 ("C2H4","Ethylene",28.054,1411.18,2,"c2"),("C2H6","Ethane",30.070,1560.69,3,"c2"),
 ("C3H6","Propylene",42.081,2058.02,3,"c3"),("C3H8","Propane",44.097,2219.17,4,"c3"),
 ("C4","Butanes (as n-butane)",58.123,2877.40,5,"c4"),("C5+","Pentanes+ (as n-pentane)",72.150,3535.77,6,"c5"),
 ("N2","Nitrogen",28.013,0,0,"inert"),("CO2","Carbon dioxide",44.010,0,0,"inert"),("H2S","Hydrogen sulphide",34.081,562.01,1,"h2s")]
ids=[c[0] for c in comps]
G_RICH={"H2":-4,"C3H8":2,"C4":2}; G_LEAN={"H2":4,"C3H8":-2,"C4":-2}
U=[
("cdu","Crude unit overhead off-gas",120,80,150,900,[2,25,0,20,0,28,15,6,2,1.99,0.01],{"C3H8":5,"C4":3,"CH4":-5,"C2H6":-3},{"C3H8":-5,"C4":-3,"CH4":5,"C2H6":3}),
("vdu","Vacuum unit ejector off-gas",40,20,55,350,[3,40,0,15,0,12,8,10,8,3.95,0.05],{"H2S":0.10,"C5+":4,"CH4":-4.1},{"H2S":-0.03,"C5+":-4,"CH4":4.03}),
("fcc","FCC gas plant dry gas",900,700,1000,150,[18,38,15,16,3,2,1,0.3,5,1.69,0.01],{"C2H4":3,"C3H6":2,"H2":-5},{"H2":5,"C2H4":-3,"C3H6":-2}),
("dcu","Delayed coker off-gas",500,380,560,400,[12,50,3,18,3,7,3,1,1,1.98,0.02],{"C3H8":2,"C4":1.5,"H2":-3.51,"H2S":0.01},{"H2":3,"C3H8":-2,"C4":-1}),
("ccr","Reformer net gas spill",300,150,400,600,[82,8,0,5,0,3,1.5,0.5,0,0,0],{"H2":-8,"CH4":4,"C2H6":2,"C3H8":2},{"H2":4,"CH4":-2,"C2H6":-1,"C3H8":-1}),
("nht","Naphtha hydrotreater off-gas",90,60,110,120,[55,20,0,10,0,8,4,1,1,0.99,0.01],G_RICH,G_LEAN),
("kht","Kerosene hydrotreater off-gas",60,40,75,80,[58,18,0,10,0,7,4,1,1.995,0,0.005],G_RICH,G_LEAN),
("dht","Diesel hydrotreater off-gas",200,150,240,150,[60,20,0,10,0,6,2,0,1.995,0,0.005],G_RICH,G_LEAN),
("hcu","Hydrocracker LP flash gas",250,180,300,350,[45,25,0,12,0,10,5,1.5,1,0.49,0.01],G_RICH,G_LEAN),
("gho","Gas oil hydrotreater off-gas",120,80,150,150,[50,24,0,12,0,8,3,1,1.99,0,0.01],G_RICH,G_LEAN),
("isom","Isomerization stabilizer off-gas",50,30,60,40,[40,10,0,10,0,25,13,2,0,0,0],G_RICH,G_LEAN),
("sgp","Saturated gas plant off-gas",150,100,180,60,[5,55,0,25,0,8,2,0.5,3,1.48,0.02],{"C2H6":3,"C3H8":2,"CH4":-5},{"C2H6":-3,"C3H8":-2,"CH4":5}),
("vbu","Visbreaker off-gas",80,50,100,120,[8,45,4,18,3,9,5,2,2,3.97,0.03],{"C3H8":2,"C4":2,"H2":-4,"H2S":0.02},{"H2":3,"C3H8":-2,"C4":-1}),
("alky","Alkylation depropanizer off-gas",30,15,40,70,[0,5,0,15,0,70,8,0,2,0,0],{"C3H8":5,"C2H6":-5},{"C3H8":-5,"C2H6":5}),
("bsu","Benzene saturation off-gas",30,20,40,30,[65,15,0,8,0,6,3,1,2,0,0],G_RICH,G_LEAN),
]
SHORT=dict(cdu="Crude unit",vdu="Vacuum unit",fcc="FCC",dcu="Delayed coker",ccr="Reformer",nht="Naphtha HT",kht="Kerosene HT",dht="Diesel HT",hcu="Hydrocracker",gho="Gas oil HT",isom="Isomerization",sgp="Sat gas plant",vbu="Visbreaker",alky="Alkylation",bsu="Benzene saturation")
def shift(y,d):
    z=[max(0.0,v+d.get(k,0)) for k,v in zip(ids,y)]; t=sum(z); return [round(v*100/t,4) for v in z]
def norm(y): t=sum(y); return [round(v*100/t,4) for v in y]
qnet={c[0]:c[3]-c[4]*44.01 for c in comps}
def heat(F,y): t=sum(y); return F*22.414*sum(v/t*qnet[k]/22.414 for k,v in zip(ids,y))/1000
units=[]; sup=0; cons=0
for (i,n,F,lo,hi,cn,y,r,l) in U:
    units.append(dict(id=i,name=n,short=SHORT[i],flow_kmol_h=dict(min=lo,normal=F,max=hi),fuel_use_gj_h=round(cn*0.6),
        analysis_mol_pct=dict(lean=shift(y,l),normal=norm(y),rich=shift(y,r))))
    sup+=heat(F,y); cons+=round(cn*0.6)
ng=[0,92,0,4,0,1,0,0,2,1,0]
# set external demand so NG make-up supplies ~10% of header heat at normal operation
ext=round((sup/0.9-cons)/10)*10
print("supply",round(sup),"unit use",cons,"external",ext)
data=dict(
 _note="ILLUSTRATIVE EXAMPLE DATA ONLY. Not plant data. Replace with client historian data.",
 basis=dict(normal_conditions="0 C, 101.325 kPa",molar_volume_nm3_kmol=22.414,air_mw=28.964,
   latent_heat_water_kj_mol=44.01,heats_of_combustion="gross, kJ/mol at 25 C; net = gross - n_H2O x 44.01"),
 components=[dict(id=c[0],name=c[1],mw=c[2],q_gross_kj_mol=c[3],n_h2o=c[4],group=c[5]) for c in comps],
 units=units,
 other_consumers=dict(name="Utility boilers and offsites",fuel_use_gj_h=ext),
 makeup=dict(id="ng",name="Natural gas import",max_kmol_h=2500,analysis_mol_pct=norm(ng)),
 limits=dict(wobbe_band_pct=5,wobbe_reference_mj_nm3=None,h2s_ppmv_max=160),
 scenarios=[dict(id="normal",name="Normal operation",down=[])]+
   [dict(id="down-"+u[0],name=SHORT[u[0]]+" down",down=[u[0]]) for u in U]+
   [dict(id="ta-crude",name="Crude turnaround (crude + vacuum)",down=["cdu","vdu"]),
    dict(id="ta-fcc",name="FCC turnaround (FCC + alky)",down=["fcc","alky"]),
    dict(id="ta-ccr",name="Reformer turnaround (CCR + NHT + BSU)",down=["ccr","nht","bsu"])])
json.dump(data,open(OUT,"w"),indent=1)
for s in data["scenarios"]: print(s["name"])
