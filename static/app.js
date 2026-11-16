'use strict';
let initialData = null;
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = (x,dec=2) => Number(x).toLocaleString('es-CO',{minimumFractionDigits:dec,maximumFractionDigits:dec});
const message = (txt, bad=false) => { $('message').textContent=txt; $('message').className=bad?'error':''; };

function populate(data){
  $('cap1').value=data.capacities[0]; $('cap2').value=data.capacities[1];
  $('producerTable').innerHTML=data.producers.map(p=>`<tr data-id="${esc(p.id)}"><td><b>${esc(p.id)}</b></td><td><input class="name" data-key="name" value="${esc(p.name)}" aria-label="Nombre de ${esc(p.id)}"></td><td><input class="city" data-key="municipio" value="${esc(p.municipio)}" aria-label="Municipio de ${esc(p.id)}"></td><td><input data-key="weight" type="number" min="1" step="1" value="${p.weight}" aria-label="Carga de ${esc(p.id)}"></td><td><select data-key="priority" aria-label="Prioridad de ${esc(p.id)}"><option ${p.priority==='Alta'?'selected':''}>Alta</option><option ${p.priority==='Media'?'selected':''}>Media</option><option ${p.priority==='Baja'?'selected':''}>Baja</option></select></td><td><input data-key="x" type="number" step="any" value="${p.x}" aria-label="Coordenada X de ${esc(p.id)}"></td><td><input data-key="y" type="number" step="any" value="${p.y}" aria-label="Coordenada Y de ${esc(p.id)}"></td></tr>`).join('');
  updateSummary();
}
function readData(){
 const producers=Array.from($('producerTable').querySelectorAll('tr')).map(row=>{
    const obj={id:row.dataset.id};
    row.querySelectorAll('[data-key]').forEach(el=>{obj[el.dataset.key]=['weight','x','y'].includes(el.dataset.key)?Number(el.value):el.value;});
    return obj;
 });
 return {producers,capacities:[Number($('cap1').value),Number($('cap2').value)]};
}
function updateSummary(){
  const {producers,capacities}=readData();
  const weight=producers.reduce((s,p)=>s+(Number.isFinite(p.weight)?p.weight:0),0);
  $('count').textContent=producers.length;
  $('totalWeight').textContent=`${fmt(weight,0)} kg`;
  $('totalCapacity').textContent=`${fmt(capacities[0]+capacities[1],0)} kg`;
  $('freeCapacity').textContent=`${fmt(capacities[0]+capacities[1]-weight,0)} kg`;
}
function renderMap(solution,producers){
 const colors=['#2878cf','#e89438']; const lookup={D:{id:'D',name:'Depósito',x:0,y:0}};
 producers.forEach(p=>lookup[p.id]=p);
 const pts=Object.values(lookup), xs=pts.map(p=>p.x),ys=pts.map(p=>p.y);
 const minX=Math.min(...xs)-1,maxX=Math.max(...xs)+1,minY=Math.min(...ys)-1,maxY=Math.max(...ys)+1;
 const x=p=>45+(p.x-minX)/(maxX-minX||1)*590;
 const y=p=>402-(p.y-minY)/(maxY-minY||1)*355;
 let svg='';
 for(let k=0;k<=10;k++){
  const xx=45+k*59, yy=47+k*35.5;
  svg+=`<line x1="${xx}" y1="47" x2="${xx}" y2="402" stroke="#e2ebef"/><line x1="45" y1="${yy}" x2="635" y2="${yy}" stroke="#e2ebef"/>`;
 }
 svg+='<rect x="45" y="47" width="590" height="355" fill="none" stroke="#b8ccd8"/>';
 solution.trucks.forEach((t,i)=>{
  const path=t.route.map(id=>`${x(lookup[id])},${y(lookup[id])}`).join(' ');
  svg+=`<polyline points="${path}" fill="none" stroke="${colors[i]}" stroke-width="3.6" stroke-linejoin="round" stroke-linecap="round" opacity=".85"/>`;
 });
 pts.forEach(p=>{
  const depot=p.id==='D'; const cx=x(p),cy=y(p);
  svg+=`<circle cx="${cx}" cy="${cy}" r="${depot?11:9}" fill="${depot?'#0e7760':'#ffffff'}" stroke="${depot?'#0e7760':'#246f7e'}" stroke-width="3"/>`;
  svg+=`<text x="${cx}" y="${cy-18}" text-anchor="middle" font-size="13" font-weight="bold" fill="#1b3449">${esc(p.id)}</text>`;
 });
 svg+='<text x="340" y="437" text-anchor="middle" font-size="12" fill="#687d8d">Coordenada X (simulada)</text><text x="15" y="225" transform="rotate(-90 15 225)" text-anchor="middle" font-size="12" fill="#687d8d">Coordenada Y (simulada)</text>';
 $('routeMap').innerHTML=svg;
}
function display(result){
 const exact=result.exact,greedy=result.greedy,stats=result.stats;
 renderMap(exact,result.producers);
 $('routeDetails').innerHTML=exact.trucks.map((t,i)=>`<article class="truck ${i?'orange-border':'blue-border'}"><h3>🚚 Camión ${t.truck}</h3><div class="path">${t.route.map(esc).join(' → ')}</div><p><b>Carga:</b> ${fmt(t.load,0)} / ${fmt(t.capacity,0)} kg</p><p><b>Distancia:</b> ${fmt(t.distance)} unidades</p></article>`).join('')+`<article class="truck"><h3>Distancia conjunta</h3><strong style="font-size:27px;color:#0c7457">${fmt(exact.total_distance)} unidades</strong></article>`;
 $('greedyDist').textContent=fmt(greedy.total_distance);
 $('exactDist').textContent=fmt(exact.total_distance);
 $('improvement').textContent=`${fmt((greedy.total_distance-exact.total_distance)/greedy.total_distance*100)} %`;
 $('runTime').textContent=`${fmt(stats.elapsed_ms)} ms`;
 const max=Math.max(greedy.total_distance,exact.total_distance,0.01);
 $('comparisonBars').innerHTML=[['Greedy',greedy.total_distance,'greedy'],['Backtracking',exact.total_distance,'exact']].map(([name,num,cls])=>`<div class="bar-row"><b>${name}</b><div class="track"><div class="fill ${cls}" style="width:${num/max*100}%"></div></div><strong>${fmt(num)}</strong></div>`).join('');
 $('dpResult').textContent=result.dp.trucks.map(t=>`Camión ${t.truck}: ${t.route.slice(1,-1).join(', ')||'sin carga'} (${t.load} kg)`).join(' · ')+'. Distancia de esa distribución con rutas voraces: '+fmt(result.dp.total_distance)+'.';
 $('mergeResult').textContent='Orden por distancia al depósito: '+result.ordered_ids.join(' → ')+'.';
 $('nodesResult').textContent=`${stats.assignment_nodes} nodos de asignación, ${stats.route_nodes} nodos de rutas; ${stats.partitions} particiones evaluadas y ${stats.route_subsets_evaluated} subconjuntos optimizados.`;
 $('pruneResult').textContent=`${stats.assignment_prunes_capacity} podas por capacidad/factibilidad y ${stats.route_prunes_distance} podas por cotas de distancia.`;
}
async function calculate(){
 const btn=$('solveBtn');btn.disabled=true;btn.textContent='Calculando…';message('');
 try{
  const response=await fetch('/api/solve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(readData())});
  const result=await response.json();
  if(!response.ok)throw Error(result.error||'Error inesperado.');
  if(!result.feasible){message(result.message,true);return;}
  display(result);message(`Solución exacta encontrada: ${fmt(result.exact.total_distance)} unidades. Se respetan las capacidades y todos los productores se visitan una vez.`);
 }catch(err){message(err.message,true)}finally{btn.disabled=false;btn.textContent='▶ Calcular rutas'}
}
async function benchmark(){
 const btn=$('benchmarkBtn');btn.disabled=true;btn.textContent='Ejecutando…';
 try{
  const response=await fetch('/api/benchmark',{method:'POST'});const result=await response.json();
  if(!response.ok)throw Error(result.error||'Error en pruebas.');
  $('benchmarkResult').innerHTML=`<div class="table-wrapper"><table><thead><tr><th>N</th><th>Greedy</th><th>Backtracking</th><th>Tiempo (ms)</th><th>Nodos</th><th>Podas</th></tr></thead><tbody>${result.rows.map(r=>r.error?`<tr><td>${r.n}</td><td colspan="5">${esc(r.error)}</td></tr>`:`<tr><td>${r.n}</td><td>${fmt(r.greedy)}</td><td>${fmt(r.backtracking)}</td><td>${fmt(r.ms,3)}</td><td>${r.nodes}</td><td>${r.prunes}</td></tr>`).join('')}</tbody></table></div><p class="hint">${esc(result.note)} Los tiempos dependen del computador. No se utilizan datos de rutas reales.</p>`;
 }catch(err){message(err.message,true)}finally{btn.disabled=false;btn.textContent='▶ Ejecutar pruebas'}
}
async function init(){
 try{
  const response=await fetch('/api/defaults');initialData=await response.json();populate(initialData);
  $('solveBtn').addEventListener('click',calculate);
  $('resetBtn').addEventListener('click',()=>{populate(initialData);message('Escenario original restaurado.');});
  $('benchmarkBtn').addEventListener('click',benchmark);
  $('producerTable').addEventListener('input',updateSummary);
  $('cap1').addEventListener('input',updateSummary);
  $('cap2').addEventListener('input',updateSummary);
  await calculate();
 }catch(err){message('No se pudo cargar la aplicación: '+err.message,true)}
}
init();
