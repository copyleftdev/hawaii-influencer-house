// Browser model. Mirrors model.py + dcf.py. Validated against the agent-calc
// reference vectors in model/vectors.json by model/verify.js.
const GET = 0.045, TAT = 0.14, DAYS = 365;
const LAND = { Honolulu: 0.40, Hawaii: 0.30 }, COSTSEG = 0.25;
const RAMP = [0.55, 0.80, 1, 1, 1, 1, 1, 1, 1, 1];
const GROWTH = 0.03, INFLATE = 0.03, TAX_ORD = 0.40;
const TAX_1250 = 0.25 + 0.0725, TAX_LTCG = 0.20 + 0.038 + 0.0725;

const SITES = {
  oahu: { name: "Oʻahu — North Shore", county: "Honolulu", price: 4000000,
    leaseMonthly: 18000, credit: 0.22, creditUplift: 0.27, insurance: 38000,
    utilities: 42000, maintPct: 0.015,
    proptaxResid: 1000000 * 4.50 / 1000 + 3000000 * 11.40 / 1000,
    proptaxHotel: 4000000 * 13.90 / 1000 },
  kona: { name: "Hawaiʻi Island — Kona", county: "Hawaii", price: 2600000,
    leaseMonthly: 12000, credit: 0.27, creditUplift: 0.32, insurance: 30000,
    utilities: 34000, maintPct: 0.015,
    proptaxResid: 2600000 * 11.10 / 1000, proptaxHotel: 2600000 * 11.55 / 1000 },
};

function pmt(P, annualRate, n) {
  const i = annualRate / 12;
  return i === 0 ? P / n : P * i / (1 - Math.pow(1 + i, -n));
}
function balance(P, annualRate, n, m) {
  const i = annualRate / 12, p = pmt(P, annualRate, n), g = Math.pow(1 + i, m);
  return P * g - p * (g - 1) / i;
}
function yearInterest(P, annualRate, n, y) {
  const p = pmt(P, annualRate, n) * 12;
  return p - (balance(P, annualRate, n, 12 * (y - 1)) - balance(P, annualRate, n, 12 * y));
}

function engines(o) {
  const cap = o.beds * DAYS, e = {};
  e["Brand activations"] = { gross: o.activations * o.activationFee,
    direct: o.activations * o.activationFee * o.activationDirect,
    bn: o.activations * o.activationDays * o.beds };
  e["Cohort retreats"] = { gross: o.retreats * o.retreatSeats * o.retreatPrice,
    direct: o.retreats * o.retreatSeats * o.retreatPrice * o.retreatDirect,
    bn: o.retreats * o.retreatDays * o.retreatSeats };
  e["Production days"] = { gross: o.prodDays * o.prodDayRate,
    direct: o.prodDays * o.prodDayRate * o.prodDirect, bn: o.prodDays * o.beds };
  let used = 0; for (const k in e) used += e[k].bn;
  const remaining = cap - used;
  if (remaining < 0) return { oversold: -remaining };
  const residBn = remaining * o.residOcc;
  e["Creator residencies"] = { gross: residBn / (365 / 12) * o.residRate, direct: 0, bn: residBn };
  return { e, cap, used: used + residBn, oversold: 0 };
}

function fixedCosts(s, o, mode) {
  const c = {};
  if (mode === "buy") {
    c.debt = pmt(s.price * o.ltv, o.rate, o.termMonths) * 12;
    c.proptax = o.proptaxHotel ? s.proptaxHotel : s.proptaxResid;
    c.insurance = s.insurance; c.maint = s.price * s.maintPct;
  } else {
    c.lease = s.leaseMonthly * 12; c.insurance = s.insurance / 2;
    c.maint = s.price * s.maintPct / 3;
  }
  c.utilities = s.utilities; c.staff = o.staff; c.founder = o.founderComp;
  c.marketing = o.marketing; c.legal = o.legal; c.software = o.software;
  let t = 0; for (const k in c) t += c[k];
  return { total: t, parts: c };
}

function run(s, o, mode) {
  const E = engines(o);
  if (E.oversold) return { oversold: E.oversold };
  const rev = {}; let gross = 0;
  for (const k in E.e) { rev[k] = E.e[k].gross; gross += E.e[k].gross; }
  const fx = fixedCosts(s, o, mode);
  const c = {};
  if (mode === "buy") {
    c["Property tax"] = fx.parts.proptax; c["Insurance"] = fx.parts.insurance;
    c["Maintenance & reserves"] = fx.parts.maint;
  } else {
    c["Master lease"] = fx.parts.lease; c["Insurance (contents/GL)"] = fx.parts.insurance;
    c["Maintenance & reserves"] = fx.parts.maint;
  }
  c["Utilities & connectivity"] = s.utilities; c["Staff (loaded)"] = o.staff;
  c["Founder compensation"] = o.founderComp; c["Marketing & booking"] = o.marketing;
  c["Legal, GET/TAT, CPA"] = o.legal; c["Software & gear service"] = o.software;
  c["Consumables & housekeeping"] = E.used * o.consumables;
  let direct = 0; for (const k in E.e) direct += E.e[k].direct;
  c["Engine direct costs"] = direct;
  c["GET @ 4.5% of gross"] = gross * GET;
  c["TAT @ 14% of lodging"] = o.term180 ? 0 : rev["Creator residencies"] * TAT;
  c["Payment/platform fees"] = gross * o.paymentFees;
  let total = 0; for (const k in c) total += c[k];
  const debt = mode === "buy" ? fx.parts.debt : 0;
  const equity = mode === "buy" ? s.price * (1 - o.ltv) + o.capex : o.capex;
  const noi = gross - total;
  return { eng: E.e, rev, cost: c, gross, total, noi, debt, net: noi - debt,
           dscr: debt ? noi / debt : null, equity, cap: E.cap, used: E.used, oversold: 0 };
}

function dcf(s, o, mode, shieldUsable) {
  const b = run(s, o, mode);
  if (b.oversold) return { oversold: b.oversold };
  const fx = fixedCosts(s, o, mode), debt = mode === "buy" ? fx.parts.debt : 0;
  const fixedExDebt = fx.total - debt;
  const tatCost = o.term180 ? 0 : b.rev["Creator residencies"] * TAT;
  let direct = 0; for (const k in b.eng) direct += b.eng[k].direct;
  const varRate = (b.gross * (GET + o.paymentFees) + direct + b.used * o.consumables + tatCost) / b.gross;

  let bonusY1, straight;
  if (mode === "buy") {
    const bldg = s.price * (1 - LAND[s.county]);
    bonusY1 = bldg * COSTSEG + o.capex * o.capexShortLife;
    straight = (bldg * (1 - COSTSEG) + o.capex * (1 - o.capexShortLife)) / 39;
  } else {
    bonusY1 = o.capex * o.capexShortLife;
    straight = o.capex * (1 - o.capexShortLife) / 10;
  }
  const P = s.price * o.ltv, rows = [], flows = [-b.equity];
  let carry = 0, accum1250 = 0, accum1245 = mode === "buy" ? bonusY1 : 0;
  for (let y = 1; y <= o.holdYears; y++) {
    const g = Math.pow(1 + GROWTH, y - 1);
    const rev = b.gross * RAMP[y - 1] * g;
    const ebitda = rev - rev * varRate - fixedExDebt * Math.pow(1 + INFLATE, y - 1);
    const interest = mode === "buy" ? yearInterest(P, o.rate, o.termMonths, y) : 0;
    const dep = (y === 1 ? bonusY1 : 0) + straight;
    accum1250 += straight;
    const taxable = ebitda - interest - dep + carry;
    let tax;
    if (taxable < 0) { carry = shieldUsable ? 0 : taxable; tax = shieldUsable ? taxable * TAX_ORD : 0; }
    else { carry = 0; tax = taxable * TAX_ORD; }
    const cf = ebitda - debt - tax;
    flows.push(cf); rows.push({ y, rev, ebitda, debt, dep, taxable, tax, cf });
  }
  let ex = null;
  if (mode === "buy") {
    const val = s.price * Math.pow(1 + o.appreciation, o.holdYears);
    const netsale = val * (1 - o.saleCosts);
    const bal = balance(P, o.rate, o.termMonths, 12 * o.holdYears);
    const basis = s.price + o.capex - accum1250 - accum1245;
    const gain = netsale - basis;
    const t1245 = Math.min(accum1245, Math.max(0, gain)) * TAX_ORD;
    const rem = Math.max(0, gain - accum1245);
    const t1250 = Math.min(accum1250, rem) * TAX_1250;
    const tcap = Math.max(0, rem - accum1250) * TAX_LTCG;
    const proceeds = netsale - bal - t1245 - t1250 - tcap;
    flows[flows.length - 1] += proceeds;
    ex = { val, netsale, bal, basis, gain, t1245, t1250, tcap, proceeds };
  }
  return { base: b, rows, flows, ex };
}

function npv(rate, flows) {
  let v = 0; for (let t = 0; t < flows.length; t++) v += flows[t] / Math.pow(1 + rate, t);
  return v;
}
function irr(flows) {
  let lo = -0.95, hi = 10;
  const f = r => npv(r, flows);
  if (f(lo) * f(hi) > 0) return null;
  for (let i = 0; i < 200; i++) {
    const mid = (lo + hi) / 2;
    if (f(lo) * f(mid) <= 0) hi = mid; else lo = mid;
  }
  return (lo + hi) / 2;
}

const DEFAULTS = {
  beds: 10, residOcc: 0.70, residRate: 6500, term180: true,
  activations: 8, activationDays: 5, activationFee: 55000, activationDirect: 0.35,
  prodDays: 30, prodDayRate: 4500, prodDirect: 0.15,
  retreats: 4, retreatDays: 8, retreatSeats: 10, retreatPrice: 7500, retreatDirect: 0.40,
  staff: 265000, founderComp: 120000, marketing: 60000, legal: 35000, software: 24000,
  consumables: 11, paymentFees: 0.03,
  ltv: 0.70, rate: 0.0725, termMonths: 360, capex: 610000, capexShortLife: 0.85,
  appreciation: 0.03, saleCosts: 0.06, holdYears: 10, proptaxHotel: false,
};

if (typeof module !== "undefined") module.exports = { SITES, DEFAULTS, run, dcf, npv, irr, engines, fixedCosts };
