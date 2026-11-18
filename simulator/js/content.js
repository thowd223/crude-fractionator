/* CDU LIVE - teaching content: equipment explainers, concept cards, guided tour, missions. */
(function () {
  "use strict";
  const f0 = (x) => (isFinite(x) ? Math.round(x).toLocaleString("en-US") : "–");
  const f1 = (x) => (isFinite(x) ? x.toFixed(1) : "–");

  // ---- equipment explainers (keys are mimic ids; tags are the project's equipment numbers)
  const EQUIP = {
    tanks: { tag: "TK (OSBL)", name: "Crude tankage", groups: ["crude"],
      what: "Crude arrives from storage. Refiners blend crudes to buy cheaper barrels, but every crude boils differently, so every switch moves the whole unit.",
      watch: "API gravity, sulfur, salt and metals of the blend. A heavy crude means less distillate, more residue and more work for the vacuum unit." },
    preheat: { tag: "E-101…E-111", name: "Preheat trains", groups: ["pa"],
      what: "Eleven exchangers heat the cold crude with hot products and pumparounds before it reaches the furnace. This heat integration recovers around 90 MW that would otherwise be thrown away in air coolers.",
      watch: "CIT (crude inlet temperature to the heater). Every 1 °C of CIT saves about 0.5 MW of fired duty. Fouling slowly steals it." },
    desalter: { tag: "D-101A/B", name: "Two-stage electrostatic desalter", groups: ["desalt"],
      what: "Crude carries brine. Wash water is mixed in through a mix valve, then a 20 kV field coalesces the droplets and the water settles out, taking the salt with it.",
      watch: "Outlet salt (target ≤ 1–2 PTB) and water carry-over (BS&W). Chloride salts that get through hydrolyse to HCl in the heater and attack the column overhead." },
    h101: { tag: "H-101", name: "Atmospheric charge heater", groups: ["heater"],
      what: "A two-cell cabin heater, 16 burners, 8 passes of 9Cr tubes. It lifts the crude from about 274 °C to 366 °C and vaporises roughly half of it. It is the single biggest energy consumer on the unit.",
      watch: "COT drives how much crude vaporises. Tube metal temperature (TMT) limits run length: coke builds up inside the tubes and insulates them. Excess O₂ trades efficiency against unburnt CO." },
    c101: { tag: "C-101", name: "Atmospheric fractionator", groups: ["column", "pa"],
      what: "41 valve trays, 6.9 m diameter. Vapour rises from the flash zone and is condensed by colder liquid coming down. Each tray is a small equilibrium stage, so the column settles into a temperature gradient from about 349 °C at the bottom to 134 °C at the top.",
      watch: "Draw rates set the cut points. Internal reflux sets how cleanly neighbouring products separate. Flooding (too much vapour or liquid) destroys separation." },
    strippers: { tag: "C-102/103/104", name: "Side strippers", groups: ["strip"],
      what: "Each side draw still carries some lighter material. Steam injected at the bottom of a small 6-tray stripper drives those light ends back to the main column.",
      watch: "Flash point of kerosene and diesel. Too little steam and the product fails flash point; too much wastes steam and loads the overhead." },
    overhead: { tag: "A-101 / D-102", name: "Overhead system", groups: ["column", "desalt"],
      what: "Naphtha and steam leave the top, condense in the air coolers and separate in a three-phase drum: off-gas, naphtha (part is pumped back as reflux) and sour water.",
      watch: "Top temperature must stay well above the water dew point, otherwise liquid water forms inside the column with HCl in it. Neutraliser keeps the sour-water pH at 5.5–6.5." },
    lightends: { tag: "C-105 / C-106", name: "Stabiliser and naphtha splitter", groups: [],
      what: "The stabiliser strips LPG out of the naphtha; the splitter separates light naphtha (to isomerisation) from heavy naphtha (to the reformer).",
      watch: "Heavy naphtha end point feeds the reformer specification." },
    h201: { tag: "H-201", name: "Vacuum heater", groups: ["vac"],
      what: "Atmospheric residue is reheated to about 398 °C. Hotter than this and the oil starts to crack into gas and coke.",
      watch: "Cracked gas overloads the ejectors and destroys the vacuum it depends on. That feedback loop is why VDU heater outlet temperatures are capped." },
    c201: { tag: "C-201", name: "Vacuum column", groups: ["vac"],
      what: "Boiling points fall when pressure falls. At 60 mbar in the flash zone, oil that would need 560 °C at atmospheric pressure vaporises at 386 °C, without cracking. Four packed beds condense it into light and heavy vacuum gas oil.",
      watch: "Flash-zone pressure and wash-bed entrainment. Deeper lift means more valuable VGO, but carried-over residue brings nickel, vanadium and carbon that poison FCC catalyst." },
    ejectors: { tag: "J-201/202/203", name: "Steam ejector set", groups: ["vac"],
      what: "Three stages of steam jets with condensers between them pull the column down to 20 mbar at the top. No moving parts, but they only work inside a narrow window of motive steam pressure and load.",
      watch: "Overload or low motive steam makes an ejector 'break': pressure jumps rather than drifting." },
    products: { tag: "Rundown", name: "Product rundown", groups: [],
      what: "Ten streams leave the unit. Each has a downstream unit waiting for it and a specification. An off-spec stream is downgraded to a cheaper destination.",
      watch: "Giveaway. A product far inside its specification is money left behind: the heavy end could have gone into a more valuable stream." },
  };

  // ---- concept cards for the Learn view
  const CONCEPTS = [
    { k: "Fundamentals", t: "A crude is a boiling curve", p: "Crude oil is thousands of compounds. Refiners describe it with a true boiling point (TBP) curve: how much of the barrel has boiled off at each temperature. Distillation slices that curve into products.", try: { label: "Show the TBP chart", act: "tab:cuts" } },
    { k: "Lever", t: "Cut points", p: "A side draw rate decides where one product ends and the next begins. Draw more kerosene and its end point rises: more jet fuel, but heavier molecules raise the freeze point.", try: { label: "Try: raise the kero draw", act: "nudge:kero:+1.5" } },
    { k: "Lever", t: "Coil outlet temperature", p: "The heater sets how much of the crude is vapour when it enters the column. More vapour means more distillate and more overflash, at the price of fuel and tube life.", try: { label: "Try: COT +8 °C", act: "nudge:cot1:+8" } },
    { k: "Constraint", t: "Overflash", p: "A little more vapour than the side draws need (2–4 % of the crude) is kept to wash the trays above the flash zone. With too little, the wash zone dries out and cokes, and the gas oil turns black.", try: { label: "Try: pull AGO harder", act: "nudge:ago:+3" } },
    { k: "Trade-off", t: "Pumparounds", p: "Heat removed in a pumparound goes to preheat the crude at a high temperature: less fuel. Heat removed at the top goes to the air. But every MW taken low in the column is reflux the upper trays never see, so separation suffers.", try: { label: "Try: shift duty to the BPA", act: "nudge:bpa:+4" } },
    { k: "Why vacuum", t: "Lower pressure, lower boiling point", p: "Above about 370 °C crude oil starts to crack. The vacuum column lowers the pressure to around 1/20 of an atmosphere so heavy gas oils boil below that limit.", try: { label: "Try: lose motive steam", act: "nudge:motive:-35" } },
    { k: "Integrity", t: "Salt becomes acid", p: "Magnesium and calcium chlorides in crude hydrolyse to HCl in the heater. In the overhead, the first water droplet to condense absorbs it at pH 1–2. The desalter and the neutraliser are the defence.", try: { label: "Try: cut wash water", act: "nudge:ww:-4" } },
    { k: "Integrity", t: "Tube metal temperature", p: "Coke on the inside of furnace tubes insulates them, so the metal gets hotter to push the same heat through. When the tube metal temperature reaches its design limit the heater must be decoked. Low throughput makes it worse.", try: { label: "Show the heater", act: "select:h101" } },
    { k: "Control", t: "Advanced process control", p: "An APC application reads the process model every minute and nudges many setpoints at once, each a little, until every product sits just inside its specification and every piece of equipment just inside its limit. The project proposes three such applications for this unit.", try: { label: "Switch APC on", act: "apc:on" } },
    { k: "AI", t: "Ask the shift advisor", p: "Claude reads the live plant, tests its own suggestions on the process model before making them, and explains the cause and effect in plain words. Ask why an alarm is on, what limits margin right now, or for a shift handover.", try: { label: "Open the advisor", act: "advisor:open" } },
    { k: "Economics", t: "Giveaway", p: "Diesel 95 % point 30 °C below its limit means barrels that could have been sold as diesel are sold as cheaper gas oil. Advanced process control earns its keep by running every product right at its limit.", try: { label: "Start mission: Squeeze the barrel", act: "mission:squeeze" } },
  ];

  // ---- guided tour: "Follow a barrel"
  const TOUR = [
    { id: "tanks", k: "1 · Feed", t: "100,000 barrels a day", p: "Arab Light arrives from tankage at 30 °C: 568 tonnes an hour. Our crude is 33.4 °API with 1.8 wt% sulfur. Nothing here is fixed: the first thing a refinery does each morning is decide which crude to run.",
      live: (o, s) => `Charge ${f1(s.act.feed)} kBPSD · ${f0(o.m_kgh / 1000)} t/h · ${f1(o.sl.api)} °API` },
    { id: "preheat", k: "2 · Heat recovery", t: "The cold preheat train", p: "Before any fuel is burnt, the crude is warmed by the products leaving the unit. The cold train takes it to the desalter at around 136 °C.",
      live: (o) => `Desalter inlet ${f1(o.Tdes)} °C` },
    { id: "desalter", k: "3 · Desalting", t: "Washing the oil", p: "Five percent wash water is mixed in and an electric field pulls the brine out. The salt that gets through will become hydrochloric acid in the column overhead.",
      live: (o, s) => `Salt ${f1(o.saltIn)} → ${s.lag.saltOut.toFixed(2)} PTB · efficiency ${f1(o.desaltEff * 100)} %` },
    { id: "hottrain", k: "4 · Heat recovery", t: "The hot preheat train", p: "Pumparounds and hot products from both columns lift the crude to the heater inlet. Every degree here is fuel saved in the furnace.",
      live: (o, s) => `CIT ${f1(s.act.CIT)} °C` },
    { id: "h101", k: "5 · Fire", t: "The charge heater", p: "Sixteen burners, eight passes. About half the crude leaves the coil as vapour. Watch the tube metal temperature: it decides when the heater must come down for decoking.",
      live: (o, s) => `COT ${f1(s.act.COT1)} °C · fired ${f1(s.act.fired1)} MW · TMT ${f0(o.TMT1)} °C` },
    { id: "c101", k: "6 · Separation", t: "Forty-one trays", p: "The two-phase feed flashes in the bottom of the column. Vapour rises and liquid falls, and every tray trades heat and molecules. The result is a smooth temperature gradient from bottom to top.",
      live: (o) => `Flash zone ${f1(o.Tfz)} °C · top ${f1(o.Ttop)} °C · vapour ${f1(o.vapLV * 100)} % of crude` },
    { id: "pa", k: "7 · Heat removal", t: "Pumparounds", p: "Three loops pull hot liquid out, cool it against crude and return it a few trays higher. They take heat out where it is worth most.",
      live: (o, s) => `TPA ${f1(s.sp.tpa)} · MPA ${f1(s.sp.mpa)} · BPA ${f1(s.sp.bpa)} MW · condenser ${f1(o.Qcond)} MW` },
    { id: "strippers", k: "8 · Polishing", t: "Side strippers", p: "Kerosene, diesel and atmospheric gas oil are drawn from the column and steam-stripped of light ends to meet flash point.",
      live: (o, s) => `Kero flash ${f1(s.q.keroFlash)} °C · diesel T95 ${f1(s.q.dieselT95)} °C` },
    { id: "overhead", k: "9 · Overhead", t: "Condense, reflux, protect", p: "Naphtha and steam condense in the air coolers. Part returns as reflux to hold the top temperature, which sets the naphtha end point.",
      live: (o, s) => `Top ${f1(o.Ttop)} °C · water dew point ${f1(o.Tdew)} °C · corrosion ${f1(s.lag.corr)} mpy` },
    { id: "h201", k: "10 · Fire again", t: "Atmospheric residue", p: "About 40 % of the crude is still liquid at the column bottom. It is too valuable to burn, so it is reheated for the vacuum column.",
      live: (o, s) => `AR ${f0(o.arKgh / 1000)} t/h · COT ${f1(s.act.COT2)} °C` },
    { id: "c201", k: "11 · Vacuum", t: "Boiling at 60 mbar", p: "Under deep vacuum the heavy gas oils vaporise without cracking. They feed the FCC and hydrocracker, where they become gasoline and diesel.",
      live: (o, s) => `Top ${f1(s.act.Ptop2)} mbar · flash zone ${f1(o.Pfz2)} mbar · cut ${f0(s.act.cutsV.cHvgo)} °C TBP` },
    { id: "products", k: "12 · Value", t: "Ten products, one margin", p: "Every barrel leaves as something worth more, or less, than the crude. The unit margin is the difference, after fuel and steam.",
      live: (o) => `Margin ${f0(o.econ.margin / 1000)} k USD/day · ${o.econ.perBbl.toFixed(2)} USD/bbl` },
  ];

  // ---- missions
  const MISSIONS = {
    sandbox: { k: "Free play", t: "Sandbox", d: "The unit at its design point on Arab Light. Every handle is yours. Nothing is scored.", dur: 0 },
    tour: { k: "Guided · 5 min", t: "Follow a barrel", d: "Twelve stops from tank to product, with the live numbers at each one. Start here.", dur: 0 },
    squeeze: { k: "Optimise · 3 plant hours", t: "Squeeze the barrel", d: "The planner wants more money from the same crude. Add at least 60,000 USD/day of margin with every product on specification.",
      dur: 3 * 3600,
      brief: ["Margin is scored on the analysers, which lag the process by about 15 minutes.", "Diesel is worth more than gas oil, and jet more than diesel. How far can you push the draws before a spec breaks?", "Pumparound duty saves fuel but costs separation. Overflash below 1 % will turn the gas oil black."],
      obj: [
        { id: "m", t: "Raise margin by 60 k USD/day over design", test: (s, M) => s.out.econ.margin - M.base >= 60000 },
        { id: "spec", t: "All products on specification at the end", test: (s) => Object.values(s.out.specLag).every(Boolean), end: true },
        { id: "nt", t: "No heater trips", test: (s) => !s.ev.h1trip && !s.ev.h2trip, keep: true },
      ] },
    switch: { k: "Disturbance · 4 plant hours", t: "Crude switch", d: "Tank 2 holds a heavy sour crude. Planning wants a 50 % blend through the unit. Keep the plant safe and the products saleable while the feed changes under you.",
      dur: 4 * 3600,
      brief: ["The blend reaches the unit gradually over about an hour.", "A heavier crude has less kerosene and diesel in it. Fixed draw rates will pull the cut points heavier.", "It also brings more residue, so the vacuum heater runs out of firing. More salt and a tighter emulsion load the desalter."],
      setup: (s) => { s.sp.crudeB = "MY"; s.sp.blend = 50; s.slateKey = ""; },
      obj: [
        { id: "nt", t: "No heater trips", test: (s) => !s.ev.h1trip && !s.ev.h2trip, keep: true },
        { id: "spec", t: "Kero, diesel and HVGO on spec at the end", test: (s) => s.out.specLag.KERO && s.out.specLag.DIESEL && s.out.specLag.HVGO, end: true },
        { id: "corr", t: "Overhead corrosion below 5 mpy at the end", test: (s) => s.lag.corr < 5, end: true },
        { id: "of", t: "Overflash above 1 % at the end", test: (s) => s.out.overflash >= 1, end: true },
      ] },
    trip: { k: "Emergency · real time", t: "Charge pump trip", d: "P-101A is vibrating badly. When it trips, H-101 loses flow and the safety system gives you seconds before it pulls the fires. Start the spare pump before SIF-101 acts.",
      dur: 900, realtime: true,
      brief: ["Low-low pass flow (SIF-101) trips the heater 15 seconds after flow falls below 35 %.", "The spare pump P-101B is in the Crude & throughput group of the operator panel.", "If the heater trips, restore feed, then reset the SIS and relight."],
      setup: (s, M) => { M.tripAt = 20 + Math.random() * 40; },
      tick: (s, M) => { if (!M.tripped && s.t - M.t0 > M.tripAt) { M.tripped = true; s.ev.p101A = false; s.log("trip", "P-101A charge pump tripped: high vibration (VSHH-1101)"); } },
      obj: [
        { id: "start", t: "Start P-101B", test: (s) => s.ev.p101B },
        { id: "nt", t: "Keep H-101 lit", test: (s) => !s.ev.h1trip, keep: true },
        { id: "cot", t: "COT back within 3 °C of setpoint at the end", test: (s) => Math.abs(s.act.COT1 - s.sp.cot1) < 3, end: true },
      ] },
    vacuum: { k: "Troubleshoot · 2 plant hours", t: "Losing vacuum", d: "Motive steam to the ejectors is sagging. The flash zone pressure is climbing and the heavy gas oil is going into the residue. Find the cause, fix it, and limit the lost margin.",
      dur: 2 * 3600,
      brief: ["The ejectors are in the Vacuum group of the operator panel.", "A broken ejector does not drift: the pressure jumps.", "Raising the vacuum heater outlet temperature to compensate makes cracked gas, which loads the ejectors further."],
      setup: (s, M) => { M.drop = true; },
      tick: (s, M) => { if (M.drop && s.sp.motive > 62 && !M.fixed) s.sp.motive = Math.max(62, s.sp.motive - 0.02 * (s.lastDt || 1)); },
      obj: [
        { id: "fix", t: "Restore motive steam (line up the HP steam bypass)", test: (s, M) => M.fixed },
        { id: "p", t: "Vacuum top pressure below 25 mbar at the end", test: (s) => s.act.Ptop2 < 25, end: true },
        { id: "c", t: "Never exceed 410 °C on H-201", test: (s) => s.act.COT2 < 410, keep: true },
      ] },
  };

  // ---- alarm definitions: cond(o, sim) -> boolean; why = cause and effect, plain words
  const ALARMS = [
    { id: "h1trip", pri: "T", tag: "H-101", msg: "H-101 tripped: fuel gas isolated", cond: (o, s) => s.ev.h1trip, why: "A safety instrumented function closed the fuel gas shut-off valves. The column loses its heat input; vaporisation and product yields collapse within minutes. Restore feed above 60 %, then reset the SIS and relight." },
    { id: "h2trip", pri: "T", tag: "H-201", msg: "H-201 tripped: fuel gas isolated", cond: (o, s) => s.ev.h2trip, why: "The vacuum heater is down. Residue goes to the vacuum column cold and nothing vaporises: VGO yield falls to zero and everything leaves as residue." },
    { id: "p101", pri: "HH", tag: "P-101A/B", msg: "No charge pump running", cond: (o, s) => !s.ev.p101A && !s.ev.p101B && !s.ev.esd, why: "Crude flow to H-101 is falling. SIF-101 will trip the heater on low-low pass flow 15 s after flow drops below 35 %. Start the spare pump." },
    { id: "tmt", pri: "H", tag: "TI-1029", msg: "H-101 tube metal temperature high", cond: (o) => o.TMT1 > 520, hh: (o) => o.TMT1 > 545, why: "Tube skin above the alarm limit. Causes: high COT, low throughput (low mass flux), coke inside the tubes. Sustained operation above design TMT shortens tube life (creep). Reduce COT or raise throughput." },
    { id: "lim1", pri: "H", tag: "TIC-1020", msg: "H-101 at maximum firing: COT below setpoint", cond: (o) => o.limited1, why: "The burners are at their heat release limit. The heater cannot reach the COT setpoint. Lower the throughput, raise CIT with more pumparound duty, or accept a lower COT." },
    { id: "co", pri: "H", tag: "AIC-1022", msg: "Flue gas CO high: incomplete combustion", cond: (o, s) => o.co > 400 && !s.ev.h1trip, why: "Not enough excess air. Fuel is leaving unburnt: efficiency falls and combustibles can ignite in the convection section (afterburning). Raise O₂ to 2–3 %." },
    { id: "o2", pri: "L", tag: "AIC-1022", msg: "Excess O₂ high: efficiency loss", cond: (o, s) => s.sp.o2 > 4.5 && !s.ev.h1trip, why: "Every extra percent of O₂ heats air that goes up the stack. About 1 % of efficiency is lost per percent of excess O₂." },
    { id: "flood", pri: "H", tag: "PDI-1084", msg: "C-101 tray loading high (flooding)", cond: (o) => o.floodMax > 90, hh: (o) => o.floodMax > 100, why: "Vapour or liquid traffic is near the hydraulic limit of the trays. Liquid gets carried up with the vapour, the products smear into each other and the column pressure drop climbs. Cause: high throughput, high COT, or too much heat removed at the top." },
    { id: "of", pri: "H", tag: "FI-1080", msg: "Overflash low: wash zone drying", cond: (o, s) => o.overflash < 1 && s.act.feed > 40, why: "The vapour leaving the flash zone is all being drawn as products. The wash trays get too little liquid and coke; metals and asphaltenes carry into the AGO. Lower the AGO draw or raise COT." },
    { id: "cond", pri: "H", tag: "TIC-1030", msg: "Overhead condensers at capacity: top temperature rising", cond: (o) => o.QcondReq > o.QcondMax, why: "The air coolers cannot condense all the overhead vapour. Top temperature and drum pressure rise and the naphtha gets heavier. Move duty to the pumparounds or lower throughput." },
    { id: "dry", pri: "H", tag: "FIC-1031", msg: "Reflux minimum: top trays drying", cond: (o) => o.QcondReq < 6, why: "Too much heat is taken out by the pumparounds. Almost no reflux reaches the top trays and the naphtha/kerosene separation collapses." },
    { id: "dew", pri: "H", tag: "TI-1030", msg: "Top temperature close to water dew point", cond: (o, s) => o.dewMargin < 14 && s.act.feed > 40, why: "If water condenses inside the top of the column, it dissolves HCl at very low pH and corrodes trays and the shell. Keep at least 14 °C of margin above the dew point." },
    { id: "corr", pri: "H", tag: "CI-1038", msg: "Overhead corrosion rate high", cond: (o, s) => s.lag.corr > 10, hh: (o, s) => s.lag.corr > 20, why: "The corrosion probe shows metal loss above 10 mpy. Causes: salt slipping through the desalter, low neutraliser, or the top running close to the dew point." },
    { id: "salt", pri: "H", tag: "AI-1009", msg: "Desalted crude salt high", cond: (o, s) => s.lag.saltOut > 3, why: "Desalter efficiency has dropped. Raise wash water, adjust mix valve dP (0.8–1.2 bar), raise demulsifier for tight emulsions." },
    { id: "bsw", pri: "H", tag: "AI-1010", msg: "Water carry-over from desalter", cond: (o) => o.bsw > 0.3, why: "An emulsion layer is building. Mixing too hard or too little demulsifier makes droplets too small to settle. Water in the hot train flashes and can upset the heater." },
    { id: "tdes", pri: "L", tag: "TIC-1004", msg: "Desalter temperature outside 125–145 °C", cond: (o) => o.Tdes < 125 || o.Tdes > 145, why: "Below the window, the oil is too viscous for droplets to settle. Above it, conductivity rises and the electrical grids can trip." },
    { id: "vac", pri: "H", tag: "PIC-2010", msg: "Vacuum column top pressure high", cond: (o, s) => s.act.Ptop2 > 30, hh: (o, s) => s.act.Ptop2 > 60, why: "Lift is being lost: HVGO is going into the residue at coker prices. Causes: low motive steam, cracked gas from a hot heater, air leaks, warm cooling water." },
    { id: "ej", pri: "H", tag: "PI-2051", msg: "Ejector J-201 broken (unstable)", cond: (o) => o.ejBroken, why: "The first-stage ejector has left its stable operating curve. It needs full motive steam pressure and a load inside its design." },
    { id: "lim2", pri: "H", tag: "TIC-2005", msg: "H-201 at maximum firing", cond: (o) => o.limited2, why: "The vacuum heater cannot reach its outlet temperature. More residue (heavier crude or a lighter cut in C-101) needs more firing." },
    { id: "crack", pri: "L", tag: "TIC-2005", msg: "H-201 outlet in cracking range", cond: (o, s) => s.act.COT2 > 408, why: "Above about 405 °C the residue starts to crack: gas loads the ejectors, coke forms in the tubes and on the wash bed." },
    { id: "kero", pri: "H", tag: "AI-1055", msg: "Kerosene off spec", cond: (o, s) => !s.out.specLag.KERO, why: "Jet A-1 needs freeze point ≤ -47 °C (heavy end too heavy: lower the kero draw) and flash point ≥ 38 °C (light end too light: more stripping steam or a heavier naphtha cut)." },
    { id: "diesel", pri: "H", tag: "AI-1065", msg: "Diesel off spec", cond: (o, s) => !s.out.specLag.DIESEL, why: "Diesel needs D86 95 % ≤ 360 °C and cloud point ≤ 0 °C. The heavy end is too heavy: lower the diesel draw, or improve fractionation below it." },
    { id: "hn", pri: "H", tag: "AI-1095", msg: "Heavy naphtha end point high", cond: (o, s) => !s.out.specLag.HN, why: "The reformer needs a naphtha end point ≤ 190 °C. Lower the top temperature." },
    { id: "ago", pri: "H", tag: "AI-1075", msg: "AGO colour dark: residue carry-over", cond: (o, s) => !s.out.specLag.AGO, why: "Overflash is too low or the flash zone is flooded, so residue droplets reach the AGO draw." },
    { id: "hvgo", pri: "H", tag: "AI-2025", msg: "HVGO metals / carbon high", cond: (o, s) => !s.out.specLag.HVGO, why: "Nickel, vanadium and Conradson carbon poison FCC catalyst. Causes: cutting too deep, high vapour velocity in the wash bed (entrainment), or a high-metals crude." },
  ];

  window.CONTENT = { EQUIP, CONCEPTS, TOUR, MISSIONS, ALARMS };
})();
