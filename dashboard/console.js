const M = JSON.parse(document.getElementById("module-metrics").textContent);
const ML = JSON.parse(document.getElementById("ml-results").textContent);
const RW = JSON.parse(document.getElementById("real-world-benchmarks").textContent);
const EXT = JSON.parse(document.getElementById("external-context").textContent);
const CATS = ["var(--accent)","var(--accent-2)","var(--cat-3)","var(--cat-4)","var(--cat-5)","var(--cat-6)"];

function fmtNum(n, d=0){ return Number(n).toLocaleString(undefined, {maximumFractionDigits:d, minimumFractionDigits:d}); }
function fmtMoney(n){
  if(Math.abs(n) >= 1e9) return "$" + (n/1e9).toFixed(2) + "B";
  if(Math.abs(n) >= 1e6) return "$" + (n/1e6).toFixed(2) + "M";
  if(Math.abs(n) >= 1e3) return "$" + (n/1e3).toFixed(1) + "K";
  return "$" + fmtNum(n);
}
function el(tag, cls, html){ const e = document.createElement(tag); if(cls) e.className = cls; if(html!==undefined) e.innerHTML = html; return e; }

function kpiTile(label, value, sub){
  return `<div class="kpi"><div class="lbl">${label}</div><div class="val">${value}${sub ? `<small>${sub}</small>` : ""}</div></div>`;
}

function hBarChart(items, {labelKey="label", valueKey="value", fmt=v=>fmtNum(v), color="var(--accent)"}={}){
  const max = Math.max(...items.map(i => i[valueKey]));
  return items.map(i => `
    <div class="bar-row">
      <div class="lbl" title="${i[labelKey]}">${i[labelKey]}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${(i[valueKey]/max*100).toFixed(1)}%; background:${color};"></div></div>
      <div class="bar-val">${fmt(i[valueKey])}</div>
    </div>`).join("");
}

function segBar(items, {labelKey="label", valueKey="value", fmt=v=>fmtNum(v)}={}){
  const total = items.reduce((s,i)=>s+i[valueKey],0);
  const bars = items.map((i,idx) => `<div style="width:${(i[valueKey]/total*100).toFixed(2)}%; background:${CATS[idx%CATS.length]};"></div>`).join("");
  const legend = items.map((i,idx) => `
    <div class="seg-legend-item"><span class="sw" style="background:${CATS[idx%CATS.length]}"></span>${i[labelKey]} — ${fmt(i[valueKey])} (${(i[valueKey]/total*100).toFixed(1)}%)</div>`).join("");
  return `<div class="seg-bar">${bars}</div><div class="seg-legend">${legend}</div>`;
}

function stackedBarChart(data, keys, {height=140}={}){
  const totals = data.map(d => keys.reduce((s,k)=>s+d[k],0));
  const max = Math.max(...totals);
  const n = data.length;
  const gap = 6, barW = 100/n;
  let bars = data.map((d,i) => {
    let yOff = 0;
    const segs = keys.map((k,ki) => {
      const h = (d[k]/max)*height;
      const rect = `<rect x="${(i*barW)}%" width="${barW-1.2}%" y="${height-yOff-h}" height="${h}" fill="${CATS[ki%CATS.length]}" />`;
      yOff += h;
      return rect;
    }).join("");
    return segs;
  }).join("");
  return `<svg viewBox="0 0 1000 ${height+26}" preserveAspectRatio="none" style="width:100%; height:${height+26}px;" role="img" aria-label="Stacked bar chart">
    <g transform="scale(10,1)">${bars.replace(/%/g,"")}</g>
    ${data.map((d,i)=>`<text x="${(i*barW/100*1000)+ (barW/100*1000)/2}" y="${height+18}" font-size="10" text-anchor="middle" fill="var(--text-dim)" font-family="JetBrains Mono">${(d.label||"").slice(0,3)}</text>`).join("")}
  </svg>`;
}

function lineChart(data, key, {height=160, color="var(--accent)", fmt=v=>fmtNum(v)}={}){
  const W = 1000;
  const vals = data.map(d => d[key]);
  const min = Math.min(...vals), max = Math.max(...vals);
  const pad = (max-min)*0.12 || 1;
  const yMin = min-pad, yMax = max+pad;
  const pts = data.map((d,i) => {
    const x = (i/(data.length-1))*W;
    const y = height - ((d[key]-yMin)/(yMax-yMin))*height;
    return [x,y];
  });
  const line = pts.map((p,i)=> (i===0?"M":"L")+p[0].toFixed(1)+","+p[1].toFixed(1)).join(" ");
  const area = line + ` L${W},${height} L0,${height} Z`;
  const last = pts[pts.length-1];
  return `<svg viewBox="0 0 ${W} ${height+4}" preserveAspectRatio="none" style="width:100%; height:${height+4}px; overflow:visible;" role="img" aria-label="Trend line chart">
    <path d="${area}" fill="${color}" opacity="0.12" stroke="none"/>
    <path d="${line}" fill="none" stroke="${color}" stroke-width="2"/>
    <circle cx="${last[0]}" cy="${last[1]}" r="3.5" fill="${color}"/>
  </svg>
  <div style="display:flex; justify-content:space-between; font-size:0.7rem; color:var(--text-dim); font-family:'JetBrains Mono'; margin-top:2px;">
    <span>${data[0].period}</span><span>${fmt(vals[vals.length-1])} latest</span><span>${data[data.length-1].period}</span>
  </div>`;
}

function cmpBars(rows){
  // rows: [{label, platform, real, fmt}]
  return rows.map(r => {
    const max = Math.max(r.platform, r.real) * 1.08;
    const fmt = r.fmt || (v=>fmtNum(v,1));
    return `
    <div style="margin-bottom:20px;">
      <div style="display:flex; justify-content:space-between; font-size:0.84rem; font-weight:600; margin-bottom:8px;">
        <span>${r.label}</span>
        ${r.badge ? `<span class="pill ${r.badgeClass||'medium'}">${r.badge}</span>` : ""}
      </div>
      <div class="bar-row" style="grid-template-columns:86px 1fr 80px;">
        <div class="lbl">Platform</div>
        <div class="bar-track"><div class="bar-fill" style="width:${(r.platform/max*100).toFixed(1)}%; background:var(--accent);"></div></div>
        <div class="bar-val">${fmt(r.platform)}</div>
      </div>
      <div class="bar-row" style="grid-template-columns:86px 1fr 80px;">
        <div class="lbl">Real-world</div>
        <div class="bar-track"><div class="bar-fill" style="width:${(r.real/max*100).toFixed(1)}%; background:var(--accent-2);"></div></div>
        <div class="bar-val">${fmt(r.real)}</div>
      </div>
    </div>`;
  }).join("");
}

function genTable(columns, rows){
  return `<div class="table-wrap"><table>
    <thead><tr>${columns.map(c=>`<th style="${c.align==='num'?'text-align:right':''}">${c.label}</th>`).join("")}</tr></thead>
    <tbody>${rows.map(r => `<tr>${columns.map(c => `<td class="${c.align==='num'?'num':''}">${c.fmt ? c.fmt(r[c.key]) : r[c.key]}</td>`).join("")}</tr>`).join("")}</tbody>
  </table></div>`;
}

/* ============================================================ TAB DEFINITIONS */
const TABS = [
  {id:"exec", label:"Executive Overview", render: renderExec},
  {id:"hosp", label:"Hospital Performance", render: renderHospital},
  {id:"fin", label:"Financial Intelligence", render: renderFinancial},
  {id:"ins", label:"Insurance Intelligence", render: renderInsurance},
  {id:"doc", label:"Doctor Analytics", render: renderDoctor},
  {id:"pat", label:"Patient Intelligence", render: renderPatient},
  {id:"res", label:"Resource Planning", render: renderResource},
  {id:"ml", label:"Predictive Analytics", render: renderPredictive},
  {id:"reco", label:"Executive Recommendations", render: renderRecommendations},
  {id:"reality", label:"Reality Check", render: renderReality},
  {id:"global", label:"Global Context", render: renderGlobal},
];

function renderExec(){
  const k = M.executive.kpis;
  const trend = M.executive.admission_trend.slice(0,-1); // drop partial final month
  const rev = M.executive.revenue_trend.slice(0,-1);
  return `
    <div class="kpi-strip">
      ${kpiTile("Total Patients", fmtNum(k.total_patients))}
      ${kpiTile("Total Billing", fmtMoney(k.total_billing))}
      ${kpiTile("Avg Billing / Admission", fmtMoney(k.avg_billing))}
      ${kpiTile("Avg Length of Stay", k.avg_length_of_stay.toFixed(1), "days")}
    </div>
    <div class="kpi-strip">
      ${kpiTile("Emergency Admissions", k.emergency_admission_pct+"%")}
      ${kpiTile("Abnormal Test Results", k.abnormal_test_pct+"%")}
      ${kpiTile("Hospitals on Record", fmtNum(k.n_hospitals))}
      ${kpiTile("Doctors on Record", fmtNum(k.n_doctors))}
    </div>
    <div class="grid g2">
      <div class="card"><h3>Admission Trend</h3><div class="card-sub">Monthly volume, May 2019 – Apr 2024 (partial final month excluded)</div>${lineChart(trend,"count",{color:"var(--accent)"})}</div>
      <div class="card"><h3>Revenue Trend</h3><div class="card-sub">Monthly billed amount</div>${lineChart(rev,"revenue",{color:"var(--accent-2)", fmt:fmtMoney})}</div>
    </div>
    <div class="grid g3" style="margin-top:16px;">
      <div class="card"><h3>Top Medical Conditions</h3><div class="card-sub">By admission count</div>${hBarChart(M.executive.top_conditions)}</div>
      <div class="card"><h3>Billing Category Mix</h3><div class="card-sub">Low / Medium / High tercile split</div>${segBar(M.executive.billing_distribution)}</div>
      <div class="card"><h3>Test Result Mix</h3><div class="card-sub">Near-balanced by design</div>${segBar(M.executive.test_result_distribution, {color:"cat"})}</div>
    </div>`;
}

function renderHospital(){
  const h = M.hospital_performance;
  return `
    <div class="banner"><span class="ic">i</span><div>${h.note}</div></div>
    <div class="grid g2">
      <div class="card"><h3>Top Hospitals by Volume</h3><div class="card-sub">Admissions handled</div>${hBarChart(h.top_by_volume,{labelKey:"Hospital",valueKey:"patient_volume"})}</div>
      <div class="card"><h3>Top Hospitals by Revenue</h3><div class="card-sub">Total billing</div>${hBarChart(h.top_by_billing,{labelKey:"Hospital",valueKey:"total_billing",fmt:fmtMoney,color:"var(--accent-2)"})}</div>
    </div>
    <div class="grid g2" style="margin-top:16px;">
      <div class="card"><h3>Longest Average Stay</h3><div class="card-sub">Hospitals with ≥2 admissions, all hit the 30-day dataset cap</div>
        ${genTable([{key:"Hospital",label:"Hospital"},{key:"patient_volume",label:"Vol.",align:"num"},{key:"avg_los",label:"Avg LOS",align:"num",fmt:v=>v.toFixed(1)},{key:"avg_billing",label:"Avg Billing",align:"num",fmt:fmtMoney}], h.top_by_los)}
      </div>
      <div class="card"><h3>Highest Emergency-Admission Share</h3><div class="card-sub">Among hospitals with ≥5 admissions</div>
        ${genTable([{key:"Hospital",label:"Hospital"},{key:"patient_volume",label:"Vol.",align:"num"},{key:"emergency_pct",label:"Emergency %",align:"num",fmt:v=>v.toFixed(1)+"%"},{key:"abnormal_pct",label:"Abnormal %",align:"num",fmt:v=>v.toFixed(1)+"%"}], h.top_by_emergency_pct)}
      </div>
    </div>`;
}

function renderFinancial(){
  const f = M.financial;
  return `
    <div class="kpi-strip">
      ${kpiTile("Total Billing", fmtMoney(f.total_billing))}
      ${kpiTile("Avg Billing / Stay Day", fmtMoney(f.avg_billing_per_stay_day))}
      ${kpiTile("High-Billing Cases", fmtNum(f.high_billing_case_count), f.high_billing_case_pct+"%")}
      ${kpiTile("LOS ↔ Billing Correlation", f.los_billing_correlation.toFixed(3))}
    </div>
    <div class="grid g2">
      <div class="card"><h3>Revenue by Medical Condition</h3><div class="card-sub">Total billed, all 6 conditions within ~3% of each other</div>${hBarChart(f.revenue_by_disease,{labelKey:"Medical Condition",valueKey:"total",fmt:fmtMoney})}</div>
      <div class="card"><h3>Revenue by Insurance Provider</h3>${hBarChart(f.revenue_by_insurance,{labelKey:"Insurance Provider",valueKey:"total",fmt:fmtMoney,color:"var(--accent-2)"})}</div>
    </div>
    <div class="grid g2" style="margin-top:16px;">
      <div class="card"><h3>Revenue by Admission Type</h3>${segBar(f.revenue_by_admission_type,{labelKey:"Admission Type",valueKey:"total",fmt:fmtMoney})}</div>
      <div class="card"><h3>Top Revenue Hospitals</h3>${hBarChart(f.top_revenue_hospitals,{labelKey:"Hospital",valueKey:"total_billing",fmt:fmtMoney,color:"var(--cat-3)"})}</div>
    </div>`;
}

function renderInsurance(){
  const i = M.insurance;
  return `
    <div class="banner"><span class="ic">i</span><div>${i.disclaimer}</div></div>
    <div class="grid g2">
      <div class="card"><h3>Provider Volume</h3>${hBarChart(i.provider_summary,{labelKey:"Insurance Provider",valueKey:"patient_volume"})}</div>
      <div class="card"><h3>Provider Avg Billing</h3>${hBarChart(i.provider_summary,{labelKey:"Insurance Provider",valueKey:"avg_billing",fmt:fmtMoney,color:"var(--accent-2)"})}</div>
    </div>
    <div class="grid g2" style="margin-top:16px;">
      <div class="card"><h3>Top Condition by Provider (revenue)</h3>
        ${genTable([{key:"Insurance Provider",label:"Provider"},{key:"Medical Condition",label:"Top Condition"},{key:"billing_amount",label:"Billing",align:"num",fmt:fmtMoney}], i.top_disease_by_provider)}
      </div>
      <div class="card"><h3>Admission Type Mix by Provider</h3>
        ${genTable([{key:"Insurance Provider",label:"Provider"},{key:"Admission Type",label:"Type"},{key:"count",label:"Count",align:"num",fmt:v=>fmtNum(v)}], i.admission_type_mix_by_provider)}
      </div>
    </div>`;
}

function renderDoctor(){
  const d = M.doctor_performance;
  const w = d.workload_distribution;
  return `
    <div class="banner"><span class="ic">i</span><div>${d.note}</div></div>
    <div class="kpi-strip" style="grid-template-columns:repeat(3,1fr);">
      ${kpiTile("Single-Case Doctors", fmtNum(w.single_case_doctors))}
      ${kpiTile("Repeat-Case Doctors", fmtNum(w.repeat_case_doctors))}
      ${kpiTile("Max Cases, One Doctor", fmtNum(w.max_cases_by_one_doctor))}
    </div>
    <div class="grid g3">
      <div class="card"><h3>Top by Case Volume</h3>${hBarChart(d.top_by_volume,{labelKey:"Doctor",valueKey:"patients_treated"})}</div>
      <div class="card"><h3>Top by Avg Billing</h3><div class="card-sub">≥3 cases</div>${hBarChart(d.top_by_avg_billing,{labelKey:"Doctor",valueKey:"avg_billing",fmt:fmtMoney,color:"var(--accent-2)"})}</div>
      <div class="card"><h3>Top by Avg Stay</h3><div class="card-sub">≥3 cases</div>${hBarChart(d.top_by_avg_los,{labelKey:"Doctor",valueKey:"avg_los",fmt:v=>v.toFixed(1)+"d",color:"var(--cat-3)"})}</div>
    </div>`;
}

function renderPatient(){
  const p = M.patient_analytics;
  return `
    <div class="grid g3">
      <div class="card"><h3>Disease Prevalence</h3>${hBarChart(p.disease_prevalence)}</div>
      <div class="card"><h3>Admissions by Age Group</h3>${hBarChart(p.admissions_by_age_group,{color:"var(--accent-2)"})}</div>
      <div class="card"><h3>Gender Split</h3>${segBar(p.gender_distribution)}</div>
    </div>
    <div class="grid g2" style="margin-top:16px;">
      <div class="card"><h3>Blood Type Distribution</h3>${hBarChart(p.blood_type_distribution,{color:"var(--cat-3)"})}</div>
      <div class="card"><h3>Avg Length of Stay by Condition</h3>${hBarChart(p.avg_los_by_condition,{fmt:v=>v.toFixed(1)+"d",color:"var(--cat-4)"})}</div>
    </div>
    <div class="grid g2" style="margin-top:16px;">
      <div class="card"><h3>Top Medication by Condition</h3>
        ${genTable([{key:"condition",label:"Condition"},{key:"top_medication",label:"Top Medication"},{key:"count",label:"Count",align:"num",fmt:v=>fmtNum(v)}], p.top_medication_by_condition)}
      </div>
      <div class="card"><h3>Test Results by Condition</h3>
        ${genTable([{key:"Medical Condition",label:"Condition"},{key:"Abnormal",label:"Abnormal",align:"num"},{key:"Normal",label:"Normal",align:"num"},{key:"Inconclusive",label:"Inconclusive",align:"num"}], p.test_result_by_condition)}
      </div>
    </div>`;
}

function renderResource(){
  const r = M.resource_planning;
  const los = r.length_of_stay_distribution;
  return `
    <div class="banner"><span class="ic">i</span><div>${r.disclaimer}</div></div>
    <div class="kpi-strip">
      ${kpiTile("Peak Months", r.peak_months.join(" / "))}
      ${kpiTile("Long-Stay Cases", fmtNum(r.long_stay_case_count), r.long_stay_case_pct+"%")}
      ${kpiTile("Median Length of Stay", los["50%"]+"d")}
      ${kpiTile("Room Number Range", r.room_number_range.min+"–"+r.room_number_range.max)}
    </div>
    <div class="grid g2">
      <div class="card"><h3>Admissions by Month</h3>${hBarChart(r.admissions_by_month,{color:"var(--accent)"})}</div>
      <div class="card"><h3>Admissions by Weekday</h3>${hBarChart(r.admissions_by_weekday,{color:"var(--accent-2)"})}</div>
    </div>
    <div class="grid g2" style="margin-top:16px;">
      <div class="card"><h3>Length-of-Stay Distribution</h3><div class="card-sub">Days, 1–30 range (dataset cap)</div>
        <div class="grid g4" style="gap:10px;">
          ${kpiTile("P25", los["25%"]+"d")}${kpiTile("Median", los["50%"]+"d")}${kpiTile("P75", los["75%"]+"d")}${kpiTile("Mean", los.mean+"d")}
        </div>
      </div>
      <div class="card"><h3>Admission Type by Month</h3><div class="card-sub">Elective / Emergency / Urgent</div>
        ${stackedBarChart(r.admission_type_by_month.map(x=>({label:x["Admission Month"], Elective:x.Elective, Emergency:x.Emergency, Urgent:x.Urgent})), ["Elective","Emergency","Urgent"])}
      </div>
    </div>`;
}

function renderPredictive(){
  const CLASSES = ["Abnormal","Inconclusive","Normal"];
  const cm = ML.error_analysis.confusion_matrix;
  const maxCell = Math.max(...cm.flat());
  const finalName = ML.final_model_name;
  const ablationRows = Object.entries(ML.ablation.results).map(([cfg,v]) => ({label:cfg, value:v.cv_f1_macro_mean, desc:v.description}));
  const zooRows = Object.entries(ML.zoo).map(([name,v]) => ({name, cv_accuracy_mean:v.cv_accuracy_mean, cv_f1_macro_mean:v.cv_f1_macro_mean, tuned:false}));
  const tunedRows = Object.entries(ML.tuned_cv5).map(([name,v]) => ({name:name+" (tuned)", cv_accuracy_mean:v.cv_accuracy_mean, cv_f1_macro_mean:v.cv_f1_macro_mean, tuned:true}));
  const allModelRows = [...zooRows, ...tunedRows];

  return `
    <div class="banner"><span class="ic">i</span><div>Research/analytics prototype trained on a <strong>synthetic</strong> dataset. NOT a medical diagnostic system — see full methodology in <code>reports/06_advanced_ml_pipeline.md</code>.</div></div>

    <div class="kpi-strip">
      ${kpiTile("Final Model", finalName)}
      ${kpiTile("Test Accuracy", (ML.final_test.test_accuracy*100).toFixed(1)+"%", "vs "+(ML.baseline_test.test_accuracy*100).toFixed(1)+"% incumbent")}
      ${kpiTile("Improvement", (ML.mcnemar.improvement_points>=0?"+":"")+ML.mcnemar.improvement_points.toFixed(2)+" pts", "McNemar p="+ML.mcnemar.p_value.toExponential(2))}
      ${kpiTile("ROC-AUC (macro)", ML.final_test.test_roc_auc_macro.toFixed(3))}
    </div>

    <div class="banner" style="background:var(--warn-soft); border-color:var(--warn);">
      <span class="ic" style="color:var(--warn);">!</span>
      <div>${ML.predictability_final_verdict}</div>
    </div>

    <div class="card">
      <h3>Feature Ablation</h3><div class="card-sub">6 feature configurations, probed with Random Forest, 5-fold CV — winner: <strong>${ML.ablation.winning_config}</strong></div>
      ${hBarChart(ablationRows,{fmt:v=>v.toFixed(4)})}
    </div>

    <div class="card" style="margin-top:16px;">
      <h3>Full Model Comparison</h3><div class="card-sub">Winning feature set, 5-fold CV — top 2 tuned via RandomizedSearchCV (n_iter=25, cv=3)</div>
      ${genTable(
        [{key:"name",label:"Model"},
         {key:"cv_accuracy_mean",label:"CV Accuracy",align:"num",fmt:v=>v.toFixed(4)},
         {key:"cv_f1_macro_mean",label:"CV F1 (macro)",align:"num",fmt:v=>v.toFixed(4)},
         {key:"name",label:"",fmt:v=>v.replace(" (tuned)","")===finalName && v.includes("tuned")?'<span class="pill best">final</span>':""}],
        allModelRows)}
    </div>

    <div class="grid g2" style="margin-top:16px;">
      <div class="card">
        <h3>Confusion Matrix — ${finalName} (final, test set)</h3><div class="card-sub">Rows = actual, columns = predicted</div>
        <div style="display:grid; grid-template-columns:90px repeat(3,1fr); gap:6px; align-items:center;">
          <div></div>${CLASSES.map(c=>`<div class="foot-note" style="text-align:center;">${c}</div>`).join("")}
          ${cm.map((row,ri)=>`
            <div class="foot-note">${CLASSES[ri]}</div>
            ${row.map(v=>`<div class="heat-cell" style="background:color-mix(in srgb, var(--accent) ${(v/maxCell*80).toFixed(0)}%, var(--surface-2)); color:${v/maxCell>0.45?'white':'var(--text)'};">${v}</div>`).join("")}
          `).join("")}
        </div>
        <p class="foot-note" style="margin-top:10px;">Most confused: ${ML.error_analysis.most_confused_pairs[0].true} → predicted ${ML.error_analysis.most_confused_pairs[0].predicted} (${ML.error_analysis.most_confused_pairs[0].count} cases)</p>
      </div>
      <div class="card">
        <h3>Feature Importance</h3><div class="card-sub">Native (impurity) vs. permutation — compare rank, not just magnitude</div>
        <p style="font-size:0.78rem; color:var(--text-dim); margin:0 0 10px;"><strong>Native top 5:</strong> ${ML.interpretability.native_importance.slice(0,5).map(d=>d.feature.replace(/^(num|cat)__/,"")).join(", ")}</p>
        ${hBarChart(ML.interpretability.permutation_importance,{labelKey:"feature",valueKey:"importance_mean",fmt:v=>v.toFixed(4),color:"var(--cat-5)"})}
        <p class="foot-note" style="margin-top:10px;">${ML.interpretability.room_number_artifact_check.verdict}</p>
      </div>
    </div>

    <div class="grid g2" style="margin-top:16px;">
      <div class="card"><h3>Old vs. New — Test Set (touched exactly twice)</h3>
        ${genTable(
          [{key:"metric",label:"Metric"},{key:"old",label:"Incumbent RF",align:"num"},{key:"new",label:finalName+" (final)",align:"num"}],
          [{metric:"Test Accuracy", old:ML.baseline_test.test_accuracy.toFixed(4), new:ML.final_test.test_accuracy.toFixed(4)},
           {metric:"Test Macro F1", old:ML.baseline_test.test_f1_macro.toFixed(4), new:ML.final_test.test_f1_macro.toFixed(4)},
           {metric:"Test ROC-AUC", old:ML.baseline_test.test_roc_auc_macro.toFixed(4), new:ML.final_test.test_roc_auc_macro.toFixed(4)}])}
        <p class="foot-note" style="margin-top:10px;">${ML.mcnemar.verdict}</p>
      </div>
      <div class="card"><h3>Class Imbalance Check</h3><div class="card-sub">Ratio ${ML.imbalance.imbalance_ratio}x — near-perfectly balanced</div>
        <p style="font-size:0.83rem; color:var(--text-dim); line-height:1.55; margin:0;">${ML.imbalance.justification}</p>
      </div>
    </div>`;
}

function renderRecommendations(){
  const recos = [
    {f:"Average billing per condition is nearly identical ($25.2K–$25.9K across all 6 conditions).", i:"Diagnosis alone can't be used to target cost containment.", r:"Investigate cost drivers beyond diagnosis code — LOS tail, room/admission-type combinations.", p:"medium"},
    {f:"10% of admissions (5,486 cases) are High-Billing (≥$45,168), a disproportionate share of $1.40B billed.", i:"A small case tail carries outsized revenue/cost exposure.", r:"Route High-Billing Flag cases into finance's case-review queue for coding and collections audit.", p:"high"},
    {f:"Admissions peak in August, July, and January (~3–4% above the monthly average).", i:"Real, if modest, seasonal demand pressure.", r:"Bias elective scheduling and staffing rosters away from Jul / Aug / Jan.", p:"high"},
    {f:"10% of admissions (5,520 cases) are Long-Stay (≥28 of a 1–30 day range).", i:"Long-stay cases are the primary capacity-demand lever.", r:"Run a discharge-bottleneck review specifically for the Long-Stay cohort.", p:"high"},
    {f:"77% of doctors and most hospitals appear only once in the data.", i:"Aggregate workload rankings outside the repeat-volume subset are meaningless.", r:"Restrict benchmarking to entities with ≥3–5 cases; label singles as non-comparable.", p:"medium"},
    {f:"Insurance-provider billing is nearly uniform ($25.46K–$25.68K average).", i:"No provider shows a distinct cost or utilization profile here.", r:"Don't build payer strategy on this billing pattern; source real claims data if needed.", p:"low"},
    {f:"Length of Stay and Billing Amount are statistically uncorrelated (r = -0.005).", i:"Billing isn't simply a function of stay length.", r:"Forecast billing and LOS as separate targets rather than deriving one from the other.", p:"medium"},
    {f:"After a full ablation + tuning pass across 9 model families, best model (Random Forest) reaches 43.2% test accuracy vs. a 33.3% baseline — a statistically significant lift (McNemar p=8.7e-08) but still led by numerically-driven fields (Room Number, Billing Amount), and pre-modeling independence tests found near-zero association between every feature and the target.", i:"Real but modest signal — not strong enough to support a clinical claim, and the dataset has a low theoretical ceiling with these columns.", r:"Keep as a research prototype; genuine further improvement would need real clinical inputs (labs, vitals, ICD codes), not more rows of this distribution.", p:"medium"},
  ];
  return `<div class="card">
    ${genTable(
      [{key:"f",label:"Finding"},{key:"i",label:"Business Impact"},{key:"r",label:"Recommendation"},{key:"p",label:"Priority",fmt:v=>`<span class="pill ${v}">${v}</span>`}],
      recos)}
  </div>
  <p class="foot-note" style="margin-top:12px;">Full write-up: <code>reports/03_business_recommendations.md</code>. Every row traces to a computed figure in <code>data/model/module_metrics.json</code> or <code>data/model/ml_results.json</code>.</p>`;
}

function renderReality(){
  const c = RW.comparison;
  const dz = c.disease_admission_mix_vs_population_prevalence;
  const insMix = c.insurance_market_structure.platform_mix_pct;
  const diseaseRows = Object.keys(dz.real_world_prevalence_pct)
    .sort((a,b) => dz.real_world_prevalence_pct[b] - dz.real_world_prevalence_pct[a])
    .map(k => ({label:k, platform: dz.platform_admission_mix_pct[k], real: dz.real_world_prevalence_pct[k]}));

  return `
    <div class="banner"><span class="ic">i</span><div>Every figure on this tab is a published statistic from a named public source (CDC/NCHS, AHRQ/HCUP, KFF, US Census, NCI SEER) — not an estimate. See <code>reports/04_reality_check.md</code> for full citations and <code>data/model/real_world_benchmarks.json</code> for the machine-readable version.</div></div>

    <div class="grid g2">
      <div class="card">
        <h3>Length of Stay</h3><div class="card-sub">Days per admission — directly comparable</div>
        ${cmpBars([{label:"Average length of stay (days)", platform:c.length_of_stay.platform_days, real:c.length_of_stay.real_world_days, fmt:v=>v.toFixed(1)+"d", badge:c.length_of_stay.ratio.toFixed(1)+"x longer", badgeClass:"high"}])}
        <p class="foot-note">${c.length_of_stay.interpretation} Source: <a href="https://www.definitivehc.com/resources/healthcare-insights/average-length-stay-hospital" target="_blank" rel="noopener">Definitive Healthcare, 2023</a>.</p>
      </div>
      <div class="card">
        <h3>Cost per Stay-Day</h3><div class="card-sub">USD per day — directly comparable, with a unit caveat</div>
        ${cmpBars([{label:"Billing / expense per stay-day ($)", platform:c.cost_per_stay_day.platform_usd, real:c.cost_per_stay_day.real_world_usd, fmt:v=>fmtMoney(v), badge:c.cost_per_stay_day.ratio.toFixed(2)+"x", badgeClass:"low"}])}
        <p class="foot-note">${c.cost_per_stay_day.interpretation} Source: <a href="https://www.kff.org/health-costs/state-indicator/expenses-per-inpatient-day/" target="_blank" rel="noopener">KFF, 2023 AHA Annual Survey</a>.</p>
      </div>
    </div>

    <div class="grid g2" style="margin-top:16px;">
      <div class="card">
        <h3>Admission Channel</h3><div class="card-sub">Share of admissions arriving via Emergency / ED</div>
        ${cmpBars([{label:"Emergency-channel share of admissions (%)", platform:c.admission_channel_mix.platform_emergency_pct, real:c.admission_channel_mix.real_world_ed_share_of_admissions_pct, fmt:v=>v.toFixed(1)+"%", badge:"biggest gap", badgeClass:"high"}])}
        <p class="foot-note">${c.admission_channel_mix.interpretation} Source: <a href="https://www.acepnow.com/article/latest-data-reveal-the-eds-role-as-hospital-admission-gatekeeper/2/" target="_blank" rel="noopener">ACEP Now / NHAMCS trend analysis</a>.</p>
      </div>
      <div class="card">
        <h3>Insurance Market Structure</h3><div class="card-sub">Platform payer mix (real market share is far less even)</div>
        ${segBar(Object.entries(insMix).map(([label,value])=>({label,value})))}
        <p class="foot-note" style="margin-top:10px;">${c.insurance_market_structure.real_world_note} Source: <a href="https://www.census.gov/library/publications/2024/demo/p60-284.html" target="_blank" rel="noopener">US Census Bureau, 2023</a> / <a href="https://www.kff.org/tag/employer-sponsored-health-insurance/" target="_blank" rel="noopener">KFF</a>.</p>
      </div>
    </div>

    <div class="card" style="margin-top:16px;">
      <h3>Disease Admission Mix vs. Population Prevalence</h3>
      <div class="card-sub">${dz.note}</div>
      ${genTable(
        [{key:"label",label:"Condition"},
         {key:"platform",label:"Platform admission share",align:"num",fmt:v=>v.toFixed(2)+"%"},
         {key:"real",label:"Real US prevalence",align:"num",fmt:v=>v.toFixed(1)+"%"}],
        diseaseRows)}
      <p class="foot-note" style="margin-top:10px;">Real prevalence spans a 6x range (7.7% asthma to 47.7% hypertension); the platform's spans 0.24 points. Sources: CDC/NCHS Data Briefs 508, 511, 516; CDC MMWR Vital Signs; NCI SEER; CDC FastStats — full links in <code>reports/04_reality_check.md</code>.</p>
    </div>

    <div class="card" style="margin-top:16px; background:var(--accent-soft); border-color:var(--accent);">
      <h3>Reading this tab</h3>
      <p style="font-size:0.85rem; line-height:1.6; margin:0;">
        None of this invalidates Modules 1-8 — those correctly describe what this dataset contains.
        This tab adds what they can't: how far the dataset sits from the real system it represents.
        Length of Stay and admission channel are the two clearest synthetic-data signatures; cost-per-day
        is coincidentally close but measures a different concept (expense vs. charge) than it appears to.
      </p>
    </div>`;
}

function renderGlobal(){
  const snap = EXT.latest_snapshot_by_country;
  const countries = Object.keys(snap);
  const indicators = [
    "Hospital beds (per 1,000 people)",
    "Physicians (per 1,000 people)",
    "Health expenditure per capita (current US$)",
    "Health expenditure (% of GDP)",
    "Life expectancy at birth (years)",
  ];
  const us = snap["United States"];
  const bedsRows = countries.map(c => ({label:c, value: snap[c]["Hospital beds (per 1,000 people)"]?.value ?? 0}))
    .sort((a,b)=>b.value-a.value);
  const spendRows = countries.map(c => ({label:c, value: snap[c]["Health expenditure (% of GDP)"]?.value ?? 0}))
    .sort((a,b)=>b.value-a.value);
  const physRows = countries.map(c => ({label:c, value: snap[c]["Physicians (per 1,000 people)"]?.value ?? 0}))
    .sort((a,b)=>b.value-a.value);

  return `
    <div class="banner"><span class="ic">i</span><div>This tab is a genuine external <strong>dataset</strong>, not just a cited statistic — fetched live from the <a href="https://data.worldbank.org/indicator" target="_blank" rel="noopener">World Bank Open Data API</a> (CC BY 4.0, no key required) by <code>scripts/07_external_worldbank_data.py</code> and cached at <code>data/external/worldbank_health_indicators.csv</code> (692 real observations, 2000–2024, 6 countries). See <code>reports/05_external_data_sources.md</code> for full detail.</div></div>

    <div class="kpi-strip">
      ${kpiTile("US Hospital Beds /1,000", us["Hospital beds (per 1,000 people)"].value.toFixed(2), "yr "+us["Hospital beds (per 1,000 people)"].year)}
      ${kpiTile("US Physicians /1,000", us["Physicians (per 1,000 people)"].value.toFixed(2), "yr "+us["Physicians (per 1,000 people)"].year)}
      ${kpiTile("US Health Spend / Capita", fmtMoney(us["Health expenditure per capita (current US$)"].value), "yr "+us["Health expenditure per capita (current US$)"].year)}
      ${kpiTile("US Health Spend (% GDP)", us["Health expenditure (% of GDP)"].value.toFixed(1)+"%", "highest of any country here")}
    </div>

    <div class="grid g3">
      <div class="card"><h3>Hospital Beds per 1,000</h3><div class="card-sub">US has less than a quarter of Japan's supply</div>${hBarChart(bedsRows,{fmt:v=>v.toFixed(2)})}</div>
      <div class="card"><h3>Health Spend (% of GDP)</h3><div class="card-sub">US spends far more of its economy on health than peers</div>${hBarChart(spendRows,{fmt:v=>v.toFixed(1)+"%",color:"var(--accent-2)"})}</div>
      <div class="card"><h3>Physicians per 1,000</h3><div class="card-sub">Germany leads; Japan is lowest despite most beds</div>${hBarChart(physRows,{fmt:v=>v.toFixed(2),color:"var(--cat-3)"})}</div>
    </div>

    <div class="card" style="margin-top:16px;">
      <h3>Full Country Comparison</h3><div class="card-sub">Latest year available per country per indicator (years differ by reporting cycle)</div>
      ${genTable(
        [{key:"country",label:"Country"},
         ...indicators.map(ind => ({key:ind, label:ind.replace(" (per 1,000 people)","/1k").replace(" (current US$)","").replace(" (% of GDP)"," %GDP").replace(" at birth (years)",""), align:"num",
            fmt:v=> v ? (typeof v.value==="number" ? v.value.toFixed(2) : "—") + ` <span class="foot-note">(${v.year})</span>` : "—"}))],
        countries.map(c => ({country:c, ...Object.fromEntries(indicators.map(ind=>[ind, snap[c][ind]]))})))}
    </div>

    <div class="card" style="margin-top:16px; background:var(--accent-soft); border-color:var(--accent);">
      <h3>Reading this tab</h3>
      <p style="font-size:0.85rem; line-height:1.6; margin:0;">
        This is national-level, aggregate data — it can't be joined row-by-row to the platform's synthetic
        admissions (no country/state field exists there). It's real context for Resource Planning and Financial
        Analytics, not a merged dimension. A single admission in this dataset ($25,594 avg. billing) costs
        roughly <strong>1.9x the entire annual per-capita US health spend</strong> ($13,473) — a scale check
        worth keeping in mind when reading the Financial Intelligence tab.
      </p>
    </div>`;
}

/* ============================================================ WIRE UP */
const tabsEl = document.getElementById("tabs");
const panelsEl = document.getElementById("panels");
TABS.forEach((t,i) => {
  const btn = el("button","tab-btn"+(i===0?" active":""), `<span class="n">${String(i+1).padStart(2,"0")}</span>${t.label}`);
  btn.dataset.id = t.id;
  btn.addEventListener("click", () => selectTab(t.id));
  tabsEl.appendChild(btn);
  const panel = el("div","panel"+(i===0?" active":""));
  panel.id = "panel-"+t.id;
  panelsEl.appendChild(panel);
});
function selectTab(id){
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b.dataset.id===id));
  document.querySelectorAll(".panel").forEach(p => p.classList.toggle("active", p.id==="panel-"+id));
}
TABS.forEach(t => { document.getElementById("panel-"+t.id).innerHTML = t.render(); });
