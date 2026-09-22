(function(){
  const modules = [
    {n:"01", name:"Executive Analytics", aud:"CEO / Hospital Director", stat:"$1.40B total billing", desc:"Rapid organizational health check: KPI cards, admission &amp; revenue trend, top conditions, hospital comparison."},
    {n:"02", name:"Hospital Performance", aud:"Operations Manager", stat:"39,815 hospitals tracked", desc:"Benchmarks volume, billing, stay length, and emergency mix across the 7,789 hospitals with repeat admissions."},
    {n:"03", name:"Financial Analytics", aud:"Finance / Revenue Mgmt", stat:"10% cases are high-billing", desc:"Revenue by disease, admission type, hospital, and insurance provider; billing-per-stay-day economics."},
    {n:"04", name:"Insurance Analytics", aud:"Insurance / Revenue Cycle", stat:"5 providers, ~even split", desc:"Payer volume, billing, and admission-type mix — billed amounts only, not confirmed claim payouts."},
    {n:"05", name:"Doctor Performance", aud:"Medical Director", stat:"40,276 doctors on record", desc:"Workload distribution restricted to the 9,384 doctors with repeat cases; avoids single-case ranking noise."},
    {n:"06", name:"Patient Analytics", aud:"Clinical Management", stat:"6 conditions, near-equal split", desc:"Demographics, disease prevalence, medication patterns, and test-result distribution by condition."},
    {n:"07", name:"Resource Planning", aud:"Capacity Planning", stat:"Aug / Jul / Jan peak months", desc:"Admission-volume seasonality and the long-stay cohort as capacity-demand proxies — not real bed data."},
    {n:"08", name:"Predictive Analytics", aud:"Analytics / Clinical Support", stat:"6 models compared", desc:"Multi-class Test Results classifier — a research prototype, not a diagnostic system."},
  ];
  document.getElementById("module-grid").innerHTML = modules.map(m => `
    <div class="module-card">
      <span class="mnum">MODULE ${m.n}</span>
      <h3>${m.name}</h3>
      <span class="aud">${m.aud}</span>
      <p>${m.desc}</p>
      <span class="stat-line">${m.stat}</span>
    </div>
  `).join("");

  const wireframes = [
    {t:"Executive Overview", list:["KPI cards","Admission trend","Revenue trend","Test-result mix"]},
    {t:"Hospital Performance", list:["Hospital ranking","Patient volume","Revenue","Avg length of stay"]},
    {t:"Financial Intelligence", list:["Revenue by disease","Billing by hospital","Billing by insurance","Cost-driver view"]},
    {t:"Insurance Intelligence", list:["Provider comparison","Patient volume","Billing","Admission mix"]},
    {t:"Doctor Analytics", list:["Doctor workload","Patient volume","Billing","Case mix"]},
    {t:"Patient Intelligence", list:["Demographics","Disease distribution","Medication","Test-result patterns"]},
    {t:"Resource Planning", list:["Admission trends","Peak periods","LOS distribution","Capacity-demand proxy"]},
    {t:"Predictive Analytics", list:["Model comparison","Confusion matrix","Feature importance","Prediction mix"]},
    {t:"Executive Recommendations", list:["Observation","Business implication","Recommended action","Priority"]},
  ];
  document.getElementById("wf-grid").innerHTML = wireframes.map((w,i) => `
    <div class="wf-card">
      <div class="wf-head"><span class="wf-title">${w.t}</span><span class="wf-idx">DASH ${String(i+1).padStart(2,"0")}</span></div>
      <div class="wf-body">
        <div class="wf-kpis"><div></div><div></div><div></div><div></div></div>
        <div class="wf-chart"></div>
        <div class="wf-row"><div></div><div></div></div>
      </div>
      <ul class="wf-list">${w.list.map(x=>`<li>${x}</li>`).join("")}</ul>
    </div>
  `).join("");

  const recos = [
    {f:"Average billing per condition is nearly identical ($25.2K–$25.9K across all 6 conditions).", i:"Diagnosis alone can't be used to target cost containment.", r:"Investigate cost drivers beyond diagnosis code — LOS tail, room/admission-type combinations.", p:"medium"},
    {f:"10% of admissions (5,486 cases) are High-Billing (≥$45,168), a disproportionate share of $1.40B billed.", i:"A small case tail carries outsized revenue/cost exposure.", r:"Route High-Billing Flag cases into finance's case-review queue for coding and collections audit.", p:"high"},
    {f:"Admissions peak in August, July, and January (~3–4% above the monthly average).", i:"Real, if modest, seasonal demand pressure.", r:"Bias elective scheduling and staffing rosters away from Jul / Aug / Jan.", p:"high"},
    {f:"10% of admissions (5,520 cases) are Long-Stay (≥28 of a 1–30 day range).", i:"Long-stay cases are the primary capacity-demand lever.", r:"Run a discharge-bottleneck review specifically for the Long-Stay cohort.", p:"high"},
    {f:"77% of doctors and most hospitals appear only once in the data.", i:"Aggregate workload rankings outside the repeat-volume subset are meaningless.", r:"Restrict benchmarking to entities with ≥3–5 cases; label singles as non-comparable.", p:"medium"},
    {f:"Insurance-provider billing is nearly uniform ($25.46K–$25.68K average).", i:"No provider shows a distinct cost or utilization profile here.", r:"Don't build payer strategy on this billing pattern; source real claims data if needed.", p:"low"},
    {f:"Length of Stay and Billing Amount are statistically uncorrelated (r = -0.005).", i:"Billing isn't simply a function of stay length.", r:"Forecast billing and LOS as separate targets rather than deriving one from the other.", p:"medium"},
    {f:"Best model (Random Forest) reaches 40.7% test accuracy vs. a 33% baseline — real but modest, led by high-cardinality numeric fields (Room Number, Billing Amount).", i:"Weak, numerically-driven signal — not strong enough to support a clinical claim.", r:"Keep as a research prototype; re-run with permutation importance and real clinical inputs before any deployment claim.", p:"medium"},
  ];
  document.getElementById("reco-table").innerHTML = `
    <table>
      <thead><tr><th style="width:30%">Finding</th><th style="width:24%">Business Impact</th><th style="width:32%">Recommendation</th><th>Priority</th></tr></thead>
      <tbody>
        ${recos.map(r => `<tr><td>${r.f}</td><td>${r.i}</td><td>${r.r}</td><td><span class="pill ${r.p}">${r.p}</span></td></tr>`).join("")}
      </tbody>
    </table>
  `;

  const links = document.querySelectorAll(".rail a");
  const sections = Array.from(links).map(a => document.querySelector(a.getAttribute("href")));
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if(e.isIntersecting){
        links.forEach(l => l.classList.remove("active"));
        const idx = sections.indexOf(e.target);
        if(idx > -1) links[idx].classList.add("active");
      }
    });
  }, {rootMargin: "-20% 0px -70% 0px"});
  sections.forEach(s => s && io.observe(s));
})();
