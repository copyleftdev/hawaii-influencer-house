const { SITES, DEFAULTS, run, dcf, npv, irr } = require("./engine.js");
const ref = require("./vectors.json");
const WIN = { term180: false, prodDayRate: 6618, prodDays: 45, activationFee: 72000, activations: 10 };
const CASES = {
  oahu_base:    ["oahu", "buy",   {}, false],
  oahu_lease:   ["oahu", "lease", {}, true],
  kona_base:    ["kona", "buy",   {}, true],
  kona_lease:   ["kona", "lease", {}, true],
  kona_win:     ["kona", "buy",   WIN, true],
  kona_win_low: ["kona", "buy",   { ...WIN, activations: 4 }, true],
  kona_win_hi:  ["kona", "buy",   { ...WIN, activations: 14, residRate: 8000 }, true],
};
let worst = 0, fails = 0;
console.log("case             field        exact             js          rel.err");
for (const [name, [sk, mode, kw, shield]] of Object.entries(CASES)) {
  const o = { ...DEFAULTS, ...kw }, s = SITES[sk];
  const b = run(s, o, mode), d = dcf(s, o, mode, shield);
  const got = { gross: b.gross, noi: b.noi, dscr: b.dscr, equity: b.equity,
                irr: irr(d.flows), npv12: npv(0.12, d.flows) };
  for (const f of ["gross", "noi", "dscr", "equity", "irr", "npv12"]) {
    const exp = ref[name][f];
    if (exp === null || exp === undefined) continue;
    const err = Math.abs(got[f] - exp) / Math.max(1, Math.abs(exp));
    worst = Math.max(worst, err);
    const bad = err > 1e-6;   // float64 accumulation floor; anything above this is a logic error
    if (bad) fails++;
    if (bad || f === "irr" || f === "npv12")
      console.log(`${name.padEnd(16)} ${f.padEnd(8)} ${String(exp).slice(0,14).padStart(14)} ${String(got[f]).slice(0,14).padStart(14)}  ${err.toExponential(2)} ${bad ? "  <-- MISMATCH" : ""}`);
  }
}
console.log(`\nworst relative error across all fields: ${worst.toExponential(3)}`);
console.log(fails ? `${fails} MISMATCHES` : "PASS - browser model agrees with the exact agent-calc model to better than 1e-6 relative\n(residual is float64 rounding in the discounting chain, ~fractions of a cent on NPV)");
