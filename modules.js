/* ═══════════════════════════════════════════
   MATRIX OS — MODULES.JS v2
   Agent Cards, Dept Heads, Factories,
   Nexus Graph, Neural Brain, Dream Module
═══════════════════════════════════════════ */

/* ── CARD FLIP + EXPAND ── */
function _flipCard(wrap) {
  var isFlipped = wrap.classList.contains('mx-flipped');
  if (isFlipped) {
    wrap.classList.remove('mx-flipped');
    wrap.style.width  = '100px';
    wrap.style.height = '148px';
    wrap.style.zIndex = '';
    wrap.style.position = 'relative';
    var inn = wrap.querySelector('.mx-inner');
    if (inn) inn.style.transform = '';
  } else {
    wrap.classList.add('mx-flipped');
    wrap.style.width  = '280px';
    wrap.style.height = '340px';
    wrap.style.zIndex = '100';
    wrap.style.position = 'relative';
    var inn = wrap.querySelector('.mx-inner');
    if (inn) inn.style.transform = 'rotateY(180deg)';
  }
}

/* ── CARD BUILDER ── */
function _mkCard(a, isDept) {
  var color = a.color  || '#00e5ff';
  var icon  = a.icon   || (isDept ? 'D' : 'A');
  var stat  = a.status || 'IDLE';
  var dot   = (stat==='ONLINE'||stat==='active') ? '#00ff88'
              : stat==='IDLE' ? '#ffd700'
              : 'rgba(255,255,255,0.2)';
  var mdl   = (a.model||'').split('-')[0] || '';
  var name  = a.name || a.id || 'Agent';
  var role  = a.role || '';

  var wrap  = document.createElement('div');
  wrap.style.cssText = 'flex-shrink:0;width:100px;height:148px;perspective:1200px;cursor:pointer;'
    + 'position:relative;transition:width .35s,height .35s;';

  var inner = document.createElement('div');
  inner.className = 'mx-inner';
  inner.style.cssText = 'width:100%;height:100%;position:relative;transform-style:preserve-3d;transition:transform 0.5s;';

  /* ── FRONT ── */
  var front = document.createElement('div');
  front.style.cssText = 'position:absolute;inset:0;backface-visibility:hidden;border-radius:6px;overflow:hidden;'
    + 'display:flex;flex-direction:column;'
    + 'background:linear-gradient(160deg,rgba(4,8,24,.99),rgba(8,3,22,.99));'
    + 'border:1px solid '+color+'44;';

  /* avatar area */
  var av = document.createElement('div');
  av.style.cssText = 'flex:1;display:flex;align-items:center;justify-content:center;position:relative;'
    + 'background:radial-gradient(circle at 50% 40%,'+color+'20,rgba(0,0,0,.9));overflow:hidden;';

  /* uploaded avatar image or icon */
  var avImg = document.createElement('div');
  avImg.className = 'mx-av-display';
  avImg.style.cssText = 'display:flex;align-items:center;justify-content:center;width:100%;height:100%;';
  if (a._avatarSrc) {
    var img = document.createElement('img');
    img.src = a._avatarSrc;
    img.style.cssText = 'width:70%;height:70%;object-fit:cover;border-radius:50%;border:2px solid '+color+'55;';
    avImg.appendChild(img);
  } else {
    var iconEl = document.createElement('div');
    iconEl.style.cssText = 'font-size:30px;filter:drop-shadow(0 0 8px '+color+'66);';
    iconEl.textContent = icon;
    avImg.appendChild(iconEl);
  }

  var dotEl = document.createElement('div');
  dotEl.style.cssText = 'position:absolute;top:5px;right:5px;width:6px;height:6px;border-radius:50%;'
    + 'background:'+dot+';box-shadow:0 0 6px '+dot+';';

  /* glow line at bottom of avatar */
  var glowLine = document.createElement('div');
  glowLine.style.cssText = 'position:absolute;bottom:0;left:0;right:0;height:1px;background:'+color+';opacity:0.3;';

  av.appendChild(dotEl); av.appendChild(avImg); av.appendChild(glowLine);

  var foot = document.createElement('div');
  foot.style.cssText = 'padding:4px 6px;background:rgba(0,0,0,.85);border-top:1px solid rgba(255,255,255,.06);flex-shrink:0;';
  var nEl = document.createElement('div');
  nEl.style.cssText = 'font-size:6.5px;font-weight:bold;color:'+color+';overflow:hidden;text-overflow:ellipsis;white-space:nowrap;letter-spacing:.5px;';
  nEl.textContent = name;
  var rEl = document.createElement('div');
  rEl.style.cssText = 'font-size:5px;color:rgba(255,255,255,.3);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-top:1px;';
  rEl.textContent = role;
  var srow = document.createElement('div');
  srow.style.cssText = 'display:flex;justify-content:space-between;margin-top:2px;';
  var sl = document.createElement('span'); sl.style.cssText='font-size:5px;color:'+dot+';'; sl.textContent=stat;
  var sm = document.createElement('span'); sm.style.cssText='font-size:5px;color:rgba(255,255,255,.25);'; sm.textContent=mdl;
  srow.appendChild(sl); srow.appendChild(sm);
  foot.appendChild(nEl); foot.appendChild(rEl); foot.appendChild(srow);
  front.appendChild(av); front.appendChild(foot);

  /* ── BACK (expanded, scrollable) ── */
  var back = document.createElement('div');
  back.style.cssText = 'position:absolute;inset:0;backface-visibility:hidden;border-radius:6px;'
    + 'overflow-y:auto;transform:rotateY(180deg);'
    + 'background:linear-gradient(160deg,rgba(3,6,18,.99),rgba(2,4,14,.99));'
    + 'border:1px solid '+color+'35;display:flex;flex-direction:column;';

  /* back header */
  var bHdr = document.createElement('div');
  bHdr.style.cssText = 'display:flex;align-items:center;justify-content:space-between;padding:6px 8px;'
    + 'background:rgba(0,0,0,.6);border-bottom:1px solid '+color+'20;flex-shrink:0;';
  var bTitle = document.createElement('span');
  bTitle.style.cssText = 'font-size:7px;font-weight:bold;color:'+color+';letter-spacing:1px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;';
  bTitle.textContent = name;
  var bClose = document.createElement('button');
  bClose.style.cssText = 'background:transparent;border:1px solid rgba(255,255,255,.15);border-radius:2px;color:rgba(255,255,255,.5);font-size:8px;cursor:pointer;padding:0 5px;flex-shrink:0;';
  bClose.textContent = 'x';
  bClose.onclick = function(e){ e.stopPropagation(); _flipCard(wrap); };
  bHdr.appendChild(bTitle); bHdr.appendChild(bClose);

  /* back scroll body */
  var bBody = document.createElement('div');
  bBody.style.cssText = 'padding:8px;overflow-y:auto;flex:1;display:grid;grid-template-columns:1fr 1fr;gap:6px;';

  function lbl(t) {
    var d=document.createElement('div');
    d.style.cssText='font-size:6px;color:rgba(255,255,255,.35);letter-spacing:.8px;margin-bottom:2px;text-transform:uppercase;grid-column:1/-1;margin-top:4px;';
    d.textContent=t; return d;
  }
  function mkSel(opts, span1) {
    var s=document.createElement('select');
    s.style.cssText='width:100%;background:rgba(0,0,0,.7);border:1px solid rgba(255,255,255,.12);'
      +'border-radius:3px;padding:4px 6px;font-size:6.5px;color:rgba(255,255,255,.8);font-family:monospace;'
      +(span1?'grid-column:1/-1;':'');
    opts.forEach(function(o){var op=document.createElement('option');op.textContent=o;s.appendChild(op);});
    if(span1) s.style.gridColumn='1/-1';
    return s;
  }
  function mkInp(ph,val,span1) {
    var i=document.createElement('input');
    i.style.cssText='width:100%;background:rgba(0,0,0,.7);border:1px solid rgba(255,255,255,.12);'
      +'border-radius:3px;padding:4px 6px;font-size:6.5px;color:#fff;font-family:monospace;';
    if(span1) i.style.gridColumn='1/-1';
    i.placeholder=ph||''; i.value=val||''; return i;
  }
  function mkTa(ph,val) {
    var t=document.createElement('textarea');
    t.style.cssText='width:100%;background:rgba(0,0,0,.7);border:1px solid rgba(255,255,255,.12);'
      +'border-radius:3px;padding:4px 6px;font-size:6.5px;color:#fff;font-family:monospace;resize:none;height:52px;grid-column:1/-1;';
    t.style.gridColumn='1/-1';
    t.placeholder=ph||''; t.value=val||''; return t;
  }

  /* AVATAR UPLOAD section */
  var avSection = document.createElement('div');
  avSection.style.cssText = 'grid-column:1/-1;display:flex;gap:8px;align-items:center;padding:6px;'
    + 'background:rgba(0,0,0,.4);border:1px solid rgba(255,255,255,.08);border-radius:3px;margin-bottom:4px;';

  var avPreview = document.createElement('div');
  avPreview.style.cssText = 'width:44px;height:44px;border-radius:50%;border:2px solid '+color+'44;'
    + 'background:radial-gradient(circle,'+color+'18,rgba(0,0,0,.8));display:flex;align-items:center;'
    + 'justify-content:center;font-size:18px;flex-shrink:0;overflow:hidden;';
  avPreview.textContent = a._avatarSrc ? '' : icon;
  if (a._avatarSrc) {
    var pi = document.createElement('img');
    pi.src = a._avatarSrc; pi.style.cssText='width:100%;height:100%;object-fit:cover;';
    avPreview.textContent=''; avPreview.appendChild(pi);
  }

  var avRight = document.createElement('div');
  avRight.style.cssText = 'flex:1;display:flex;flex-direction:column;gap:4px;';

  var avUpload = document.createElement('label');
  avUpload.style.cssText = 'display:block;padding:4px 8px;background:rgba('+
    (color==='#00e5ff'?'0,229,255':'170,68,255')+',0.1);border:1px solid '+color+'35;'
    +'color:'+color+';font-size:6.5px;border-radius:3px;cursor:pointer;text-align:center;font-family:monospace;letter-spacing:.5px;';
  avUpload.textContent = 'UPLOAD AVATAR IMAGE';
  var avInput = document.createElement('input');
  avInput.type='file'; avInput.accept='image/*'; avInput.style.display='none';
  avInput.onchange = function() {
    var file = this.files[0]; if(!file) return;
    var reader = new FileReader();
    reader.onload = function(e) {
      var src = e.target.result;
      a._avatarSrc = src;
      /* update preview */
      avPreview.innerHTML='';
      var pi=document.createElement('img');pi.src=src;pi.style.cssText='width:100%;height:100%;object-fit:cover;border-radius:50%;';
      avPreview.appendChild(pi);
      /* update front avatar */
      var frontAv = wrap.querySelector('.mx-av-display');
      if(frontAv){frontAv.innerHTML='';var fi=document.createElement('img');fi.src=src;fi.style.cssText='width:70%;height:70%;object-fit:cover;border-radius:50%;border:2px solid '+color+'55;';frontAv.appendChild(fi);}
    };
    reader.readAsDataURL(file);
  };
  avUpload.appendChild(avInput);

  var avEmojis = document.createElement('div');
  avEmojis.style.cssText='display:flex;gap:3px;flex-wrap:wrap;';
  ['H','W','C','V','A','$','S','G','Z','B','M','X'].forEach(function(ic){
    var btn=document.createElement('button');
    btn.style.cssText='width:20px;height:20px;background:rgba(0,0,0,.5);border:1px solid rgba(255,255,255,.1);'
      +'border-radius:2px;color:rgba(255,255,255,.6);font-size:9px;cursor:pointer;';
    btn.textContent=ic;
    btn.onclick=function(e){
      e.stopPropagation();
      a.icon=ic; a._avatarSrc=null;
      avPreview.innerHTML=ic; avPreview.style.fontSize='18px';
      var frontAv=wrap.querySelector('.mx-av-display');
      if(frontAv){frontAv.innerHTML='';var ie=document.createElement('div');ie.style.fontSize='30px';ie.textContent=ic;frontAv.appendChild(ie);}
    };
    avEmojis.appendChild(btn);
  });

  avRight.appendChild(avUpload); avRight.appendChild(avEmojis);
  avSection.appendChild(avPreview); avSection.appendChild(avRight);

  /* Build back fields */
  bBody.appendChild(avSection);
  bBody.appendChild(lbl('AGENT STATUS'));
  bBody.appendChild(mkSel([stat,'ONLINE','IDLE','OFFLINE'], true));
  bBody.appendChild(lbl('LLM MODEL'));
  bBody.appendChild(mkSel([a.model||'hermes3:8b','qwen2.5-72b (vLLM)','hermes3:8b (Ollama)','claude-sonnet-4','gpt-4o','mistral-large'], true));
  bBody.appendChild(lbl('PROVIDER'));
  bBody.appendChild(mkSel(['vLLM (local)','Ollama (local)','OpenRouter','Anthropic','OpenAI'], false));
  bBody.appendChild(mkSel(['Auto-detect','Force local','Force cloud'], false));
  bBody.appendChild(lbl('VOICE ENGINE'));
  bBody.appendChild(mkSel([a.voice||'Piper Jenny UK','Piper Jenny (UK)','Piper Amy (US)','Kokoro TTS','ElevenLabs','None'], false));
  bBody.appendChild(lbl('VOICE PERSONA'));
  bBody.appendChild(mkSel([a.persona||'lara-croft.md','lara-croft.md','tony-stark.md','hal-9000.md','samantha.md','Custom...'], false));
  bBody.appendChild(lbl('KNOWLEDGE VAULT'));
  bBody.appendChild(mkSel(['New-matrix-vault/knowledge','Matrix-Production/kb','Matrix-Production/projects/cfo'], true));
  bBody.appendChild(lbl('SKILLS PATH'));
  bBody.appendChild(mkSel(['New-matrix-vault/skills','Matrix-Production/skills'], false));
  bBody.appendChild(lbl('CONTENT OUTPUT'));
  bBody.appendChild(mkSel(['Matrix-Production/content','Matrix-Production/products','Matrix-Production/campaigns'], false));
  bBody.appendChild(lbl('SPECIALTIES'));
  bBody.appendChild(mkInp('VAPI, RAG, n8n, LangGraph...', (a.specialties||[]).join(', '), true));
  bBody.appendChild(lbl('SYSTEM PROMPT SNIPPET'));
  bBody.appendChild(mkTa('You are '+name+'. Your role is...', a.soul||''));
  bBody.appendChild(lbl('ASSIGN TASK'));
  bBody.appendChild(mkTa('Assign a new task...', a.task||''));
  bBody.appendChild(lbl('ACTIVE / PENDING / DONE'));
  var pd=document.createElement('div');
  pd.style.cssText='grid-column:1/-1;font-size:6.5px;color:rgba(255,255,255,.45);background:rgba(0,0,0,.4);'
    +'border-radius:3px;padding:5px;line-height:1.6;min-height:28px;';
  pd.textContent=a.task||'No active task assigned';
  bBody.appendChild(pd);

  /* Save button */
  var saveRow = document.createElement('div');
  saveRow.style.cssText = 'grid-column:1/-1;display:flex;gap:6px;margin-top:4px;';
  var sv=document.createElement('button');
  sv.style.cssText='flex:2;padding:5px;border-radius:3px;font-size:7px;font-family:monospace;cursor:pointer;'
    +'background:'+color+'15;border:1px solid '+color+'45;color:'+color+';letter-spacing:1px;';
  sv.textContent='SAVE AGENT';
  sv.onclick=function(e){e.stopPropagation();sv.textContent='SAVED';setTimeout(function(){sv.textContent='SAVE AGENT';},1500);};
  var cl=document.createElement('button');
  cl.style.cssText='flex:1;padding:5px;border-radius:3px;font-size:7px;font-family:monospace;cursor:pointer;'
    +'background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.12);color:rgba(255,255,255,.4);';
  cl.textContent='CLOSE';
  cl.onclick=function(e){e.stopPropagation();_flipCard(wrap);};
  saveRow.appendChild(sv); saveRow.appendChild(cl);
  bBody.appendChild(saveRow);

  back.appendChild(bHdr);
  back.appendChild(bBody);

  inner.appendChild(front); inner.appendChild(back); wrap.appendChild(inner);
  wrap.onclick = function(e) {
    if(e.target.tagName==='SELECT'||e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA'||e.target.tagName==='BUTTON'||e.target.tagName==='LABEL') return;
    _flipCard(this);
  };
  return wrap;
}

/* ── DEPT HEADS ── */
var _DEPTS = [
  {name:'HERMES CEO',   role:'Master Orchestrator',  icon:'H', color:'#00e5ff',status:'ONLINE',model:'qwen2.5-72b',task:'Orchestrating S15 Iris Vault'},
  {name:'WEBSITE ARCH', role:'AI Smart Websites',    icon:'W', color:'#00a8ff',status:'ONLINE',model:'qwen2.5-72b',task:'Law firm landing page'},
  {name:'CHATBOT ENG',  role:'AI Chatbots & RAG',    icon:'C', color:'#ff00ff',status:'ONLINE',model:'qwen2.5-72b',task:'Dental clinic bot flow'},
  {name:'VOICE ENG',    role:'Voice Bots & IVR',     icon:'V', color:'#aa44ff',status:'ONLINE',model:'qwen2.5-72b',task:'Medical IVR system'},
  {name:'AGENT ARCH',   role:'AI Agent Design',      icon:'A', color:'#00ff88',status:'IDLE',  model:'qwen2.5-72b',task:'Multi-agent blueprint'},
  {name:'AUTO ENG',     role:'AI Workflows & n8n',   icon:'X', color:'#0088ff',status:'ONLINE',model:'qwen2.5-72b',task:'n8n pipeline build'},
  {name:'CONSULTANT',   role:'ROI & Strategy',       icon:'$', color:'#ffd700',status:'IDLE',  model:'claude-sonnet-4',task:'Law firm AI audit'},
  {name:'SOCIAL HEAD',  role:'Social Media & Content',icon:'S',color:'#ff4488',status:'ONLINE',model:'qwen2.5-72b',task:'Content calendar Q2'},
  {name:'CRM HEAD',     role:'AI CRM & Funnels',     icon:'G', color:'#ff8800',status:'IDLE',  model:'qwen2.5-72b',task:'Funnel optimization'},
  {name:'SECURITY HEAD',role:'Cybersecurity',         icon:'Z', color:'#ff3355',status:'ONLINE',model:'claude-sonnet-4',task:'Zero trust audit'},
  {name:'CFO AGENT',    role:'Income Factories',     icon:'B', color:'#ffd700',status:'ONLINE',model:'claude-sonnet-4',task:'Factory Alpha revenue push'},
  {name:'MARKETING',    role:'AI Campaigns & Ads',   icon:'M', color:'#ff6600',status:'IDLE',  model:'qwen2.5-72b',task:'Q2 campaign design'}
];

function renderDeptHeadCards() {
  var c = document.getElementById('dept-head-cards');
  if (!c) { console.warn('[Matrix] dept-head-cards not found'); return; }
  c.innerHTML = '';
  _DEPTS.forEach(function(a){ c.appendChild(_mkCard(a, true)); });
  console.log('[Matrix] Dept heads rendered:', _DEPTS.length);
}

function renderAgentRosterCards(agents) {
  var c = document.getElementById('agent-roster-cards');
  if (!c) { console.warn('[Matrix] agent-roster-cards not found'); return; }
  var addBtn = document.getElementById('roster-add-btn');
  c.querySelectorAll('[style*="perspective"]').forEach(function(el){ el.remove(); });
  agents.forEach(function(a) {
    var card = _mkCard(a, false);
    if (addBtn) c.insertBefore(card, addBtn);
    else c.appendChild(card);
  });
  var ct = document.getElementById('roster-count');
  if (ct) ct.textContent = agents.length + ' AGENTS';
  console.log('[Matrix] Roster rendered:', agents.length);
}

function _mkFactoryCard(f) {
  f.spend = f.spend || 0;
  f.net   = f.revenue_month - f.spend;
  var color = f.status==='LIVE' ? '#00ff88' : f.status==='PROD' ? '#00e5ff' : '#ffd700';
  var colorHex = f.status==='LIVE' ? 0x00ff88 : f.status==='PROD' ? 0x00e5ff : 0xffd700;
  var prog  = Math.min(100,(f.revenue_month/10000)*100);
  var isLive = f.status==='LIVE'||f.status==='PROD';

  var card = document.createElement('div');
  card.style.cssText = 'flex-shrink:0;width:250px;background:linear-gradient(135deg,rgba(1,3,10,.96),rgba(3,6,18,.98));'
    +'border:1px solid '+color+'30;border-radius:7px;display:flex;flex-direction:column;overflow:hidden;cursor:pointer;'
    +'box-shadow:0 0 14px '+color+'12,inset 0 1px 0 '+color+'15;transition:box-shadow .2s;';
  card.onmouseenter = function(){ this.style.boxShadow='0 0 24px '+color+'35,inset 0 1px 0 '+color+'25'; };
  card.onmouseleave = function(){ this.style.boxShadow='0 0 14px '+color+'12,inset 0 1px 0 '+color+'15'; };

  /* header */
  var hdr = document.createElement('div');
  hdr.style.cssText = 'display:flex;justify-content:space-between;align-items:flex-start;padding:12px 14px 8px;';
  hdr.innerHTML = '<div>'
    +'<div style="font-size:13px;font-weight:bold;color:'+color+';letter-spacing:.5px">'+f.name+'</div>'
    +'<div style="font-size:9px;color:rgba(255,255,255,.4);margin-top:3px">'+f.notes+'</div>'
    +'</div>'
    +'<span style="font-size:9px;padding:3px 9px;border:1px solid '+color+'45;border-radius:3px;color:'+color+';font-weight:bold">'+f.status+'</span>';

  /* metrics grid - today/week/month */
  var metrics = document.createElement('div');
  metrics.style.cssText = 'display:grid;grid-template-columns:1fr 1fr 1fr;border-top:1px solid rgba(255,255,255,.07);border-bottom:1px solid rgba(255,255,255,.07);';
  [
    ['TODAY', '$'+f.revenue_today.toFixed(0), '#00ff88'],
    ['WEEK',  '$'+f.revenue_week.toFixed(0),  '#00e5ff'],
    ['MONTH', '$'+f.revenue_month.toFixed(0), color]
  ].forEach(function(m,i){
    var cell = document.createElement('div');
    cell.style.cssText = 'padding:8px 10px;text-align:center;'+(i<2?'border-right:1px solid rgba(255,255,255,.06);':'');
    cell.innerHTML = '<div style="font-size:8px;color:rgba(255,255,255,.38);letter-spacing:.5px;margin-bottom:3px">'+m[0]+'</div>'
      +'<div style="font-size:17px;font-weight:300;color:'+m[2]+'">'+m[1]+'</div>';
    metrics.appendChild(cell);
  });

  /* sales + products row */
  var sp = document.createElement('div');
  sp.style.cssText = 'display:grid;grid-template-columns:1fr 1fr 1fr;border-bottom:1px solid rgba(255,255,255,.06);';
  [
    ['SALES',    f.sales,    '#ffd700'],
    ['PRODUCTS', f.products, '#aa44ff'],
    ['NET',      '$'+f.net.toFixed(0), '#00ff88']
  ].forEach(function(m,i){
    var cell=document.createElement('div');
    cell.style.cssText='padding:7px 8px;text-align:center;'+(i<2?'border-right:1px solid rgba(255,255,255,.05);':'');
    cell.innerHTML='<div style="font-size:7.5px;color:rgba(255,255,255,.35);letter-spacing:.5px;margin-bottom:2px">'+m[0]+'</div>'
      +'<div style="font-size:13px;font-weight:300;color:'+m[2]+'">'+m[1]+'</div>';
    sp.appendChild(cell);
  });

  /* progress bar */
  var progDiv = document.createElement('div');
  progDiv.style.cssText = 'padding:8px 12px;border-bottom:1px solid rgba(255,255,255,.05);';
  progDiv.innerHTML = '<div style="display:flex;justify-content:space-between;font-size:9px;margin-bottom:5px">'
    +'<span style="color:rgba(255,255,255,.4)">'+prog.toFixed(1)+'% of $10K goal</span>'
    +'<span style="color:'+color+'">$'+f.revenue_month.toFixed(0)+' earned</span>'
    +'</div>'
    +'<div style="height:5px;background:rgba(255,255,255,.07);border-radius:3px;overflow:hidden">'
    +'<div style="height:100%;width:'+prog+'%;background:linear-gradient(90deg,'+color+'44,'+color+');border-radius:3px;transition:width 1s"></div>'
    +'</div>';

  /* active task */
  var taskDiv = document.createElement('div');
  taskDiv.style.cssText = 'padding:8px 12px 10px;';
  taskDiv.innerHTML = '<div style="font-size:7.5px;color:rgba(255,255,255,.32);letter-spacing:.5px;margin-bottom:4px">ACTIVE TASK</div>'
    +'<div style="font-size:10px;color:rgba(255,255,255,.75);background:rgba(0,0,0,.4);border-radius:3px;padding:6px 9px;'
    +'border-left:2px solid '+color+';line-height:1.5;">'
    +(isLive ? 'Printify pipeline ACTIVE — batch generation running' : 'Awaiting activation command')
    +'</div>';

  /* click hint */
  var hint = document.createElement('div');
  hint.style.cssText = 'padding:0 12px 9px;font-size:8px;color:rgba(255,255,255,.22);text-align:center;letter-spacing:1px;';
  hint.textContent = 'CLICK — EXPAND  ·  DOUBLE-CLICK — 3D OFFICE';

  card.appendChild(hdr); card.appendChild(metrics); card.appendChild(sp);
  card.appendChild(progDiv); card.appendChild(taskDiv); card.appendChild(hint);

  /* expanded detail panel (toggled on single click) */
  var detail = document.createElement('div');
  detail.style.cssText = 'display:none;border-top:1px solid '+color+'20;';
  var isLiveLocal = isLive;
  var runTasks  = isLiveLocal ? ['Generating product batch','Uploading to Printify API','Publishing to Etsy marketplace'] : [];
  var waitTasks = isLiveLocal
    ? ['Gothic Techwear Hoodie v2','Cyber Aesthetic Tote Bag','Matrix OS Sticker Pack','Neon Noir Phone Case','Dark Academia Notebook']
    : ['Awaiting activation','Configure product templates','Set up Printify blueprint','Define niche & keywords'];
  var doneTasks = Array.from({length:Math.min(f.sales,8)},function(_,i){
    return 'Product '+(i+1)+' published · $'+(f.revenue_month/Math.max(f.sales,1)).toFixed(2)+' avg';
  });

  var taskGrid = document.createElement('div');
  taskGrid.style.cssText = 'display:grid;grid-template-columns:1fr 1fr 1fr;';
  [{label:'RUNNING',color:'#ffd700',tasks:runTasks},
   {label:'QUEUED', color:'#00e5ff',tasks:waitTasks},
   {label:'DONE',   color:'#00ff88',tasks:doneTasks}].forEach(function(col,ci){
    var cell=document.createElement('div');
    cell.style.cssText='padding:10px;'+(ci<2?'border-right:1px solid rgba(255,255,255,.05);':'');
    var hd=document.createElement('div');
    hd.style.cssText='display:flex;align-items:center;gap:5px;margin-bottom:7px;';
    hd.innerHTML='<span style="font-size:10px;font-weight:bold;color:'+col.color+'">'+col.label+'</span>'
      +'<span style="font-size:9px;color:rgba(255,255,255,.35);background:rgba(0,0,0,.4);border-radius:2px;padding:0 5px;margin-left:auto">'+col.tasks.length+'</span>';
    cell.appendChild(hd);
    if(!col.tasks.length){
      var e=document.createElement('div');e.style.cssText='font-size:9px;color:rgba(255,255,255,.22);font-style:italic;';e.textContent='No tasks';cell.appendChild(e);
    } else {
      col.tasks.forEach(function(t){
        var item=document.createElement('div');
        item.style.cssText='font-size:9px;color:rgba(255,255,255,.72);padding:4px 7px;margin-bottom:3px;'
          +'background:rgba(0,0,0,.3);border-radius:3px;border-left:2px solid '+col.color+'44;'
          +'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;';
        item.textContent=t;cell.appendChild(item);
      });
    }
    taskGrid.appendChild(cell);
  });
  detail.appendChild(taskGrid);
  card.appendChild(detail);

  /* click = expand/collapse, double-click = 3D office */
  var _t = null;
  card.onclick = function(e) {
    if(e.target.tagName==='BUTTON') return;
    if(_t){ clearTimeout(_t); _t=null; open3DFactory(f, colorHex); return; }
    _t = setTimeout(function(){
      _t = null;
      var open = detail.style.display==='block';
      detail.style.display = open ? 'none' : 'block';
      hint.textContent = open ? 'CLICK — EXPAND  ·  DOUBLE-CLICK — 3D OFFICE' : 'DOUBLE-CLICK — OPEN 3D OFFICE  ·  CLICK — COLLAPSE';
    }, 270);
  };
  return card;
}

function renderFactoryCards() {
  var c = document.getElementById('factory-cards-row');
  if (!c) return;
  fetch('/factory/status').then(function(r){ return r.json(); }).then(function(d) {
    c.innerHTML = '';
    var badge = document.getElementById('factory-total-badge');
    if (badge && d.totals) badge.textContent = '$'+d.totals.month.toFixed(2)+' MONTHLY · '+d.totals.progress_pct+'% OF GOAL';
    (d.factories||[]).forEach(function(f){ c.appendChild(_mkFactoryCard(f)); });
    /* blank launch card */
    var blank = document.createElement('div');
    blank.style.cssText = 'flex-shrink:0;width:220px;border:1px dashed rgba(255,215,0,.28);border-radius:7px;'
      +'background:rgba(0,4,0,.4);display:flex;flex-direction:column;align-items:center;justify-content:center;'
      +'gap:8px;cursor:pointer;transition:border-color .2s;min-height:220px;';
    blank.onmouseenter=function(){this.style.borderColor='rgba(255,215,0,.55)';};
    blank.onmouseleave=function(){this.style.borderColor='rgba(255,215,0,.28)';};
    blank.innerHTML='<div style="font-size:30px;color:rgba(255,215,0,.35)">+</div>'
      +'<div style="font-size:11px;color:rgba(255,215,0,.5);letter-spacing:1px;text-align:center;font-family:JetBrains Mono,monospace;line-height:1.6">LAUNCH NEW FACTORY</div>'
      +'<div style="font-size:9px;color:rgba(255,255,255,.22);font-family:JetBrains Mono,monospace">CLICK TO CONFIGURE</div>';
    blank.onclick=function(){if(typeof addMsg==='function')addMsg('system','// New factory configuration — use CFO Agent to set up a new income factory.');};
    c.appendChild(blank);
    console.log('[Matrix] Factories rendered:', (d.factories||[]).length);
  }).catch(function(e){ console.warn('[Matrix] Factory error:', e); });
}

/* ── NEXUS GRAPH ── */
var _NX = {z:1,dx:0,dy:0,nodes:[],edges:[],drag:false,sx:0,sy:0,started:false};

function initNexusBottom() {
  if (_NX.started) return;
  var wrap   = document.getElementById('nexus-bottom-wrap');
  var canvas = document.getElementById('nexus-bottom-canvas');
  if (!wrap||!canvas) return;
  canvas.width  = wrap.offsetWidth  || 340;
  canvas.height = wrap.offsetHeight || 210;
  _NX.started = true;
  var W=canvas.width, H=canvas.height;
  var cols=['#00e5ff','#00ff88','#ff00ff','#ffd700','#aa44ff','#ff6600'];

  function buildFallback(){
    _NX.nodes = Array.from({length:28},function(_,i){
      var a=i/28*Math.PI*2, r=(0.2+Math.random()*0.32)*Math.min(W,H);
      return {x:W/2+Math.cos(a)*r+(Math.random()-.5)*25,y:H/2+Math.sin(a)*r+(Math.random()-.5)*25,
        vx:(Math.random()-.5)*.2,vy:(Math.random()-.5)*.2,r:1.5+Math.random()*2,c:cols[i%cols.length],label:'node'+i};
    });
    _NX.edges = Array.from({length:20},function(){return {s:Math.floor(Math.random()*28),t:Math.floor(Math.random()*28)};});
    var el=document.getElementById('nexus-bottom-count'); if(el) el.textContent='28 nodes';
  }

  fetch('/nexus/graph').then(function(r){return r.json();}).then(function(d){
    _NX.nodes = (d.nodes||[]).slice(0,35).map(function(n,i){
      var a=i/Math.min(d.nodes.length,35)*Math.PI*2;
      var r=(0.2+Math.random()*0.32)*Math.min(W,H);
      return {x:W/2+Math.cos(a)*r+(Math.random()-.5)*25,y:H/2+Math.sin(a)*r+(Math.random()-.5)*25,
        vx:(Math.random()-.5)*.2,vy:(Math.random()-.5)*.2,
        r:n.type==='core'?4:n.type==='python'?2.5:1.8,c:cols[i%cols.length],label:n.label||('node'+i)};
    });
    _NX.edges=(d.edges||[]).map(function(e){return{s:e.source,t:e.target};});
    var el=document.getElementById('nexus-bottom-count');
    if(el) el.textContent=(d.total_files||_NX.nodes.length)+' nodes';
  }).catch(buildFallback);
  buildFallback();

  wrap.addEventListener('mousedown',function(e){_NX.drag=true;_NX.sx=e.clientX-_NX.dx;_NX.sy=e.clientY-_NX.dy;});
  wrap.addEventListener('mousemove',function(e){if(_NX.drag){_NX.dx=e.clientX-_NX.sx;_NX.dy=e.clientY-_NX.sy;}});
  wrap.addEventListener('mouseup',function(){_NX.drag=false;});
  wrap.addEventListener('mouseleave',function(){_NX.drag=false;});
  wrap.addEventListener('wheel',function(e){e.preventDefault();_NX.z=Math.max(.2,Math.min(8,_NX.z*(e.deltaY>0?.9:1.1)));},{passive:false});
  _animNexus();
}

function nexusBotZoom(f){ _NX.z=Math.max(.2,Math.min(8,_NX.z*f)); }

function _animNexus(){
  var canvas=document.getElementById('nexus-bottom-canvas');
  if(!canvas) return;
  var ctx=canvas.getContext('2d'),W=canvas.width,H=canvas.height;
  ctx.clearRect(0,0,W,H);
  ctx.save();ctx.translate(_NX.dx,_NX.dy);ctx.scale(_NX.z,_NX.z);
  _NX.edges.forEach(function(e){
    var a=_NX.nodes[e.s],b=_NX.nodes[e.t]; if(!a||!b) return;
    ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);
    ctx.strokeStyle='rgba(0,229,255,0.1)';ctx.lineWidth=.5/_NX.z;ctx.stroke();
  });
  _NX.nodes.forEach(function(n){
    ctx.beginPath();ctx.arc(n.x,n.y,n.r,0,Math.PI*2);
    ctx.fillStyle=n.c;ctx.shadowBlur=4/_NX.z;ctx.shadowColor=n.c;ctx.fill();ctx.shadowBlur=0;
    n.x+=n.vx;n.y+=n.vy;
    if(n.x<5||n.x>W/_NX.z)n.vx*=-1;
    if(n.y<5||n.y>H/_NX.z)n.vy*=-1;
  });
  ctx.restore();
  requestAnimationFrame(_animNexus);
}

/* ── NEURAL BRAIN ── */
var _BR={z:1,dx:0,dy:0,nodes:[],drag:false,sx:0,sy:0,started:false};
var _BR_R=[
  {cx:.5,cy:.2,c:'#00e5ff',n:12},{cx:.28,cy:.38,c:'#ffd700',n:10},
  {cx:.72,cy:.38,c:'#ffffff',n:10},{cx:.5,cy:.5,c:'#00ff88',n:14},
  {cx:.5,cy:.75,c:'#0088ff',n:8},{cx:.22,cy:.62,c:'#ff3355',n:6},
  {cx:.78,cy:.62,c:'#ff00ff',n:8},{cx:.38,cy:.7,c:'#aa44ff',n:10}
];

function initBrainBottom(){
  if(_BR.started) return;
  var wrap=document.getElementById('brain-bottom-wrap');
  var canvas=document.getElementById('brain-bottom-canvas');
  if(!wrap||!canvas) return;
  canvas.width=wrap.offsetWidth||340; canvas.height=wrap.offsetHeight||210;
  _BR.started=true;
  var W=canvas.width,H=canvas.height;

  function build(){
    _BR.nodes=[];
    _BR_R.forEach(function(reg){
      for(var i=0;i<reg.n;i++){
        var a=Math.random()*Math.PI*2,r=Math.random()*36;
        _BR.nodes.push({x:reg.cx*W+Math.cos(a)*r,y:reg.cy*H+Math.sin(a)*r,
          cx:reg.cx*W,cy:reg.cy*H,vx:(Math.random()-.5)*.2,vy:(Math.random()-.5)*.2,
          r:1+Math.random()*2.2,c:reg.c,pulse:Math.random()*Math.PI*2,firing:.2+Math.random()*.8});
      }
    });
    var el=document.getElementById('brain-bottom-nodes'); if(el) el.textContent=_BR.nodes.length;
  }
  build();

  wrap.addEventListener('mousedown',function(e){_BR.drag=true;_BR.sx=e.clientX-_BR.dx;_BR.sy=e.clientY-_BR.dy;});
  wrap.addEventListener('mousemove',function(e){if(_BR.drag){_BR.dx=e.clientX-_BR.sx;_BR.dy=e.clientY-_BR.sy;}});
  wrap.addEventListener('mouseup',function(){_BR.drag=false;});
  wrap.addEventListener('mouseleave',function(){_BR.drag=false;});
  wrap.addEventListener('wheel',function(e){e.preventDefault();_BR.z=Math.max(.2,Math.min(8,_BR.z*(e.deltaY>0?.9:1.1)));},{passive:false});
  _animBrain();
}

function _animBrain(){
  var canvas=document.getElementById('brain-bottom-canvas'); if(!canvas) return;
  var ctx=canvas.getContext('2d'),W=canvas.width,H=canvas.height;
  ctx.clearRect(0,0,W,H);
  ctx.save();ctx.translate(_BR.dx,_BR.dy);ctx.scale(_BR.z,_BR.z);
  _BR.nodes.forEach(function(n){
    n.pulse+=.025;
    var a=.3+.7*Math.abs(Math.sin(n.pulse))*n.firing;
    var hex=Math.floor(a*255).toString(16).padStart(2,'0');
    ctx.beginPath();ctx.arc(n.x,n.y,n.r,0,Math.PI*2);
    ctx.fillStyle=n.c+hex;ctx.shadowBlur=3/_BR.z;ctx.shadowColor=n.c;ctx.fill();ctx.shadowBlur=0;
    n.vx+=(n.cx-n.x)*.001;n.vy+=(n.cy-n.y)*.001;n.vx*=.98;n.vy*=.98;n.x+=n.vx;n.y+=n.vy;
  });
  ctx.restore();
  requestAnimationFrame(_animBrain);
}

/* ── DREAM MODULE ── */
var _dreamActive=false,_dreamCount=0;
var _DREAM_PROMPTS=[
  'Analyze our agent roster and propose one new specialist agent that fills a critical capability gap.',
  'Review Factory Alpha performance and propose 2 new Printify product niches with high conversion potential.',
  'Design an improved CEO routing logic for voice bot and IVR client requests.',
  'Propose 3 n8n automation improvements that would save the most time in the current workflow.',
  'Propose a new income factory concept based on AI market trends targeting $2000/month.',
  'Design an Etsy SEO optimization agent to improve product visibility and conversions.',
  'Identify the top 3 bottlenecks in Matrix OS and propose specific technical fixes.',
  'Propose voice persona improvements to make agent interactions more natural and effective.'
];

function triggerDream(){
  if(_dreamActive) return;
  _dreamActive=true;
  var badge=document.getElementById('dream-status-badge');
  var statTxt=document.getElementById('dream-state-txt');
  var bar=document.getElementById('dream-progress-bar');
  var txt=document.getElementById('dream-progress-txt');
  if(badge) badge.textContent='DREAMING';
  if(statTxt) statTxt.textContent='DREAMING - SYNTHESIZING KNOWLEDGE...';
  var pct=0;
  var iv=setInterval(function(){
    pct=Math.min(92,pct+Math.random()*8);
    if(bar) bar.style.width=pct+'%';
    if(txt) txt.textContent=pct.toFixed(0)+'% - synthesizing...';
  },350);
  var prompt=_DREAM_PROMPTS[_dreamCount%_DREAM_PROMPTS.length];
  fetch('http://localhost:8000/v1/chat/completions',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({model:'qwen2.5-72b',messages:[
      {role:'system',content:'You are the Matrix OS Dream Engine. Generate one specific, actionable improvement proposal for the Architect to review. Be creative and concrete.'},
      {role:'user',content:prompt}
    ],stream:false,temperature:0.9,max_tokens:300})
  }).then(function(r){return r.json();}).then(function(d){
    clearInterval(iv);
    var idea=d.choices&&d.choices[0]&&d.choices[0].message&&d.choices[0].message.content;
    _finishDream(idea||'No response from dream engine.',prompt);
  }).catch(function(){
    clearInterval(iv);
    _finishDream('INSIGHT: Add a dedicated Etsy SEO Agent monitoring trending keywords daily and auto-updating product tags. Estimated impact: +20% organic traffic in 30 days. Tools: EtsyAPI, pgvector, n8n scheduler.',prompt);
  });
}

function _finishDream(idea,prompt){
  _dreamCount++;
  var bar=document.getElementById('dream-progress-bar');
  var txt=document.getElementById('dream-progress-txt');
  var cnt=document.getElementById('dream-count');
  var badge=document.getElementById('dream-status-badge');
  var statTxt=document.getElementById('dream-state-txt');
  if(bar) bar.style.width='100%';
  if(txt) txt.textContent='100% - dream complete';
  if(cnt) cnt.textContent=_dreamCount+' dreams generated';
  if(badge) badge.textContent='STANDBY';
  if(statTxt) statTxt.textContent='DREAM COMPLETE - AWAITING REVIEW';
  var list=document.getElementById('dream-ideas-list');
  if(list){
    var empty=list.querySelector('[style*="NO DREAMS"]'); if(empty) empty.remove();
    var div=document.createElement('div');
    div.style.cssText='background:rgba(170,68,255,0.06);border:1px solid rgba(170,68,255,0.2);border-radius:3px;padding:6px 8px;margin-bottom:5px;';
    var title=document.createElement('div');
    title.style.cssText='font-size:7px;color:#aa44ff;font-weight:bold;margin-bottom:3px;font-family:monospace;';
    title.textContent='DREAM #'+_dreamCount+' - '+new Date().toLocaleTimeString();
    var body=document.createElement('div');
    body.style.cssText='font-size:6.5px;color:rgba(255,255,255,.65);line-height:1.6;margin-bottom:5px;';
    body.textContent=idea.substring(0,280)+(idea.length>280?'...':'');
    var btns=document.createElement('div');
    btns.style.cssText='display:flex;gap:5px;';
    var ap=document.createElement('button');
    ap.style.cssText='padding:3px 8px;background:rgba(0,255,136,.1);border:1px solid rgba(0,255,136,.3);color:#00ff88;font-size:6.5px;border-radius:2px;cursor:pointer;font-family:monospace;';
    ap.textContent='APPROVE & BUILD';
    ap.onclick=function(){this.textContent='APPROVED';this.style.background='rgba(0,255,136,.2)';this.onclick=null;if(typeof addMsg==='function')addMsg('system','Dream approved: '+idea.substring(0,80)+'...');};
    var dm=document.createElement('button');
    dm.style.cssText='padding:3px 8px;background:rgba(255,51,85,.08);border:1px solid rgba(255,51,85,.25);color:#ff3355;font-size:6.5px;border-radius:2px;cursor:pointer;font-family:monospace;';
    dm.textContent='DISMISS';
    dm.onclick=function(){div.remove();};
    btns.appendChild(ap);btns.appendChild(dm);
    div.appendChild(title);div.appendChild(body);div.appendChild(btns);
    list.insertBefore(div,list.firstChild);
  }
  if(typeof addMsg==='function') addMsg('system','Dream Engine: New insight ready.');
  setTimeout(function(){_dreamActive=false;if(bar)bar.style.width='0%';if(txt)txt.textContent='Ready for next cycle';},3000);
}

function openNewAgentForm(){
  if(typeof addMsg==='function') addMsg('system','// Use /agent command to open Agent Commander and deploy a new agent.');
}

/* ── BOOT: POLL UNTIL HUD VISIBLE ── */
var _modDone=false;
var _modPoll=setInterval(function(){
  var hud=document.getElementById('hud');
  if(!hud||hud.style.display!=='grid') return;
  clearInterval(_modPoll);
  if(_modDone) return;
  _modDone=true;
  console.log('[Matrix] modules.js booting...');
  setTimeout(function(){
    renderDeptHeadCards();
    fetch('/agents/registry').then(function(r){return r.json();}).then(function(d){
      var list=d.agents||d||[];
      if(!Array.isArray(list)) list=Object.values(list);
      renderAgentRosterCards(list);
    }).catch(function(){renderAgentRosterCards([]);});
    renderFactoryCards();
    setInterval(renderFactoryCards,30000);
  },600);
  setTimeout(function(){
    initNexusBottom();
    initBrainBottom();
  },1000);
},500);

/* ── KNOWLEDGE INGESTOR ── */
function _ingestLog(msg, color) {
  var el = document.getElementById('ingest-log');
  var st = document.getElementById('ingest-status');
  if (el) { el.style.color = color || 'rgba(0,255,136,0.7)'; el.textContent = msg; }
  if (st) st.textContent = color === '#ff3355' ? 'ERROR' : 'READY';
}

function ingestUrl() {
  var url = (document.getElementById('ingest-url-input') || {}).value;
  var vault = (document.getElementById('ingest-vault-sel') || {}).value || 'New-matrix-vault/knowledge';
  if (!url || !url.startsWith('http')) { _ingestLog('Enter a valid URL starting with http', '#ff3355'); return; }
  _ingestLog('Fetching and ingesting: ' + url + '...', '#ffd700');
  fetch('/ingest/url', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url: url, vault: vault})
  }).then(function(r){ return r.json(); }).then(function(d) {
    if (d.ok) {
      _ingestLog('Ingested: ' + (d.title || url) + ' → ' + vault, 'rgba(0,255,136,0.8)');
      document.getElementById('ingest-url-input').value = '';
      if (typeof addMsg === 'function') addMsg('system', 'Ingested URL → ' + vault + ': ' + (d.title || url));
    } else { _ingestLog('Error: ' + (d.error || 'Unknown error'), '#ff3355'); }
  }).catch(function(e) { _ingestLog('Error: ' + e.message, '#ff3355'); });
}

function ingestText() {
  var text = (document.getElementById('ingest-text-input') || {}).value;
  var vault = (document.getElementById('ingest-vault-sel') || {}).value || 'New-matrix-vault/knowledge';
  if (!text || !text.trim()) { _ingestLog('Enter some text to ingest', '#ff3355'); return; }
  _ingestLog('Saving to vault: ' + vault + '...', '#ffd700');
  fetch('/ingest/text', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: text, vault: vault, topic: text.substring(0,40).replace(/[^a-zA-Z0-9 ]/g,'').trim()||'note'})
  }).then(function(r){ return r.json(); }).then(function(d) {
    if (d.ok) {
      _ingestLog('Saved ' + text.length + ' chars → ' + vault, 'rgba(0,255,136,0.8)');
      document.getElementById('ingest-text-input').value = '';
      if (typeof addMsg === 'function') addMsg('system', 'Text ingested → ' + vault + ' (' + text.length + ' chars)');
    } else { _ingestLog('Error: ' + (d.error || 'Unknown error'), '#ff3355'); }
  }).catch(function(e) { _ingestLog('Error: ' + e.message, '#ff3355'); });
}

function ingestFile(input) {
  var vault = (document.getElementById('ingest-vault-sel') || {}).value || 'New-matrix-vault/knowledge';
  var files = input.files;
  if (!files || !files.length) return;
  var file = files[0];
  _ingestLog('Reading file: ' + file.name + '...', '#ffd700');
  var reader = new FileReader();
  reader.onload = function(e) {
    var content = e.target.result;
    fetch('/ingest/text', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text: content, vault: vault, topic: file.name.replace(/\.[^.]+$/,''), filename: file.name})
    }).then(function(r){ return r.json(); }).then(function(d) {
      if (d.ok) {
        _ingestLog('File ingested: ' + file.name + ' → ' + vault, 'rgba(0,255,136,0.8)');
        if (typeof addMsg === 'function') addMsg('system', 'File ingested → ' + vault + ': ' + file.name);
      } else { _ingestLog('Error: ' + (d.error || 'Unknown error'), '#ff3355'); }
    }).catch(function(e) { _ingestLog('Error: ' + e.message, '#ff3355'); });
  };
  reader.readAsText(file);
  input.value = '';
}

/* ── SYNC FOOTER METRICS TO LLM TILE ── */
function _syncLlmMetrics() {
  var map = [
    ['tel-model-badge', 'llm-model-badge-2'],
    ['tel-tokens',      'llm-tokens-2'],
    ['tel-msg-cost',    'llm-msg-cost-2'],
    ['tel-today-paid',  'llm-today-paid-2'],
    ['tel-saved',       'llm-saved-2'],
    ['tel-limit',       'llm-limit-2'],
    ['tel-budget-pct',  'llm-budget-pct-2']
  ];
  map.forEach(function(pair) {
    var src = document.getElementById(pair[0]);
    var dst = document.getElementById(pair[1]);
    if (src && dst) dst.textContent = src.textContent;
  });
  /* sync budget bar width */
  var srcBar = document.getElementById('tel-budget-bar');
  var dstBar = document.getElementById('llm-budget-bar-2');
  if (srcBar && dstBar) dstBar.style.width = srcBar.style.width;
  /* sync budget bar color */
  if (srcBar && dstBar) dstBar.style.background = srcBar.style.background || '#00ff88';
}
setInterval(_syncLlmMetrics, 1000);

/* ── 2D FACTORY OFFICE MODAL ── */
var _officeModal = null;
var _officeAnim  = null;

function open3DFactory(factory, colorHex) {
  if (_officeAnim)  { cancelAnimationFrame(_officeAnim); _officeAnim = null; }
  if (_officeModal) { document.body.removeChild(_officeModal); _officeModal = null; }

  var col   = factory.status==='LIVE' ? '#00ff88' : factory.status==='PROD' ? '#00e5ff' : '#ffd700';
  var isLive = factory.status==='LIVE' || factory.status==='PROD';

  /* ── MODAL SHELL ── */
  var modal = document.createElement('div');
  modal.style.cssText = 'position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,0.96);display:flex;flex-direction:column;font-family:JetBrains Mono,monospace;';
  _officeModal = modal;

  /* header */
  var hdr = document.createElement('div');
  hdr.style.cssText = 'display:flex;align-items:center;justify-content:space-between;padding:12px 20px;background:rgba(0,0,0,0.85);border-bottom:1px solid '+col+'40;flex-shrink:0;';
  hdr.innerHTML = '<div>'
    +'<div style="font-size:16px;font-weight:bold;color:'+col+';letter-spacing:1px">⚡ '+factory.name.toUpperCase()+' — LIVE OFFICE VIEW</div>'
    +'<div style="font-size:10px;color:rgba(255,255,255,0.4);margin-top:3px">'+factory.notes+' · '+factory.status+' · $'+factory.revenue_month.toFixed(2)+'/mo · '+factory.sales+' sales · '+factory.products+' products</div>'
    +'</div>';
  var xBtn = document.createElement('button');
  xBtn.style.cssText = 'background:rgba(255,51,85,0.12);border:1px solid rgba(255,51,85,0.4);color:#ff3355;font-size:12px;padding:6px 18px;border-radius:4px;cursor:pointer;font-family:inherit;letter-spacing:1px;';
  xBtn.textContent = 'CLOSE';
  xBtn.onclick = function() {
    if (_officeAnim) cancelAnimationFrame(_officeAnim);
    document.body.removeChild(modal); _officeModal = null;
  };
  hdr.appendChild(xBtn);

  /* stats strip */
  var stats = document.createElement('div');
  stats.style.cssText = 'display:flex;border-bottom:1px solid '+col+'20;flex-shrink:0;background:rgba(0,0,0,0.6);';
  [['TODAY','$'+factory.revenue_today.toFixed(2),'#00ff88'],
   ['THIS WEEK','$'+factory.revenue_week.toFixed(2),'#00e5ff'],
   ['MONTH','$'+factory.revenue_month.toFixed(2),col],
   ['SALES',String(factory.sales),'#ffd700'],
   ['PRODUCTS',String(factory.products),'#aa44ff'],
   ['STATUS',factory.status,col]
  ].forEach(function(s){
    var seg=document.createElement('div');
    seg.style.cssText='flex:1;text-align:center;padding:8px 12px;border-right:1px solid rgba(255,255,255,0.06);';
    seg.innerHTML='<div style="font-size:8px;color:rgba(255,255,255,0.35);letter-spacing:.5px;margin-bottom:3px">'+s[0]+'</div>'
      +'<div style="font-size:14px;font-weight:300;color:'+s[2]+'">'+s[1]+'</div>';
    stats.appendChild(seg);
  });

  /* canvas */
  var canvasWrap = document.createElement('div');
  canvasWrap.style.cssText = 'flex:1;position:relative;overflow:hidden;';
  var canvas = document.createElement('canvas');
  canvas.style.cssText = 'width:100%;height:100%;display:block;';
  canvasWrap.appendChild(canvas);

  /* task panel */
  var taskPanel = document.createElement('div');
  taskPanel.style.cssText = 'flex-shrink:0;display:grid;grid-template-columns:1fr 1fr 1fr;border-top:1px solid '+col+'20;background:rgba(0,0,0,0.7);max-height:140px;';
  var runTasks  = isLive ? ['Generating product batch','Uploading to Printify','Publishing to Etsy','Monitoring sales metrics'] : ['Awaiting activation'];
  var waitTasks = isLive ? ['Gothic Hoodie v2','Cyber Tote Bag','Matrix Sticker Pack','Neon Phone Case','Dark Academia Notebook'] : ['Configure templates','Set up blueprint','Define niche & keywords'];
  var doneTasks = Array.from({length:Math.min(factory.sales,8)},function(_,i){return 'Product '+(i+1)+' published · $'+(factory.revenue_month/Math.max(factory.sales,1)).toFixed(2)+' avg';});
  [{label:'RUNNING',col:'#ffd700',tasks:runTasks},
   {label:'QUEUED', col:'#00e5ff',tasks:waitTasks},
   {label:'DONE',   col:'#00ff88',tasks:doneTasks}].forEach(function(c2,ci){
    var cell=document.createElement('div');
    cell.style.cssText='padding:10px 14px;overflow-y:auto;border-right:1px solid rgba(255,255,255,0.06);scrollbar-width:thin;';
    var hd2=document.createElement('div');
    hd2.style.cssText='font-size:10px;font-weight:bold;color:'+c2.col+';letter-spacing:.5px;margin-bottom:7px;display:flex;justify-content:space-between;';
    hd2.innerHTML='<span>'+c2.label+'</span><span style="font-weight:normal;color:rgba(255,255,255,0.35)">'+c2.tasks.length+'</span>';
    cell.appendChild(hd2);
    c2.tasks.forEach(function(t){
      var item=document.createElement('div');
      item.style.cssText='font-size:9px;color:rgba(255,255,255,0.72);padding:4px 8px;margin-bottom:3px;background:rgba(0,0,0,0.3);border-radius:3px;border-left:2px solid '+c2.col+'55;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;';
      item.textContent=t; cell.appendChild(item);
    });
    taskPanel.appendChild(cell);
  });

  modal.appendChild(hdr); modal.appendChild(stats); modal.appendChild(canvasWrap); modal.appendChild(taskPanel);
  document.body.appendChild(modal);

  /* wait one frame for layout */
  requestAnimationFrame(function(){
    _buildOffice2D(canvas, factory, col, isLive);
  });
}

function _buildOffice2D(canvas, factory, accentCol, isLive) {
  var W = canvas.parentElement.offsetWidth  || 1200;
  var H = canvas.parentElement.offsetHeight || 580;
  canvas.width  = W;
  canvas.height = H;
  var ctx = canvas.getContext('2d');

  /* ── ROOM LAYOUT CONSTANTS ── */
  var FLOOR_Y   = H * 0.82;
  var CEILING_Y = H * 0.08;
  var LEFT_X    = W * 0.04;
  var RIGHT_X   = W * 0.96;
  var ROOM_W    = RIGHT_X - LEFT_X;

  /* accent color as rgb */
  var accR = parseInt(accentCol.slice(1,3),16);
  var accG = parseInt(accentCol.slice(3,5),16);
  var accB = parseInt(accentCol.slice(5,7),16);
  function accAlpha(a){ return 'rgba('+accR+','+accG+','+accB+','+a+')'; }

  /* ── AGENT DEFINITIONS ── */
  var AGENTS = [
    {name:'HERMES',  col:'#00e5ff', task:'Orchestrating',   zone:'server'},
    {name:'WEBSITE', col:'#00a8ff', task:'Building LP',     zone:'desk'},
    {name:'CHATBOT', col:'#ff00ff', task:'Training bot',    zone:'desk'},
    {name:'VOICE',   col:'#aa44ff', task:'IVR config',      zone:'desk'},
    {name:'CFO',     col:'#ffd700', task:'Revenue push',    zone:'pipeline'},
    {name:'AUTO',    col:'#0088ff', task:'n8n pipeline',    zone:'desk'},
    {name:'SOCIAL',  col:'#ff4488', task:'Content plan',    zone:'desk'},
    {name:'SECURITY',col:'#ff3355', task:'Audit',           zone:'server'},
    {name:'AGENT',   col:'#00ff88', task:'Blueprint',       zone:'board'},
  ];

  /* ── ZONES ── */
  var zones = {
    server:   {x: LEFT_X + ROOM_W*0.07,  y: FLOOR_Y - H*0.38, w: ROOM_W*0.18, h: H*0.38, label:'SERVER ROOM'},
    desk:     {x: LEFT_X + ROOM_W*0.28,  y: FLOOR_Y - H*0.30, w: ROOM_W*0.32, h: H*0.30, label:'WORKSTATION AREA'},
    pipeline: {x: LEFT_X + ROOM_W*0.62,  y: FLOOR_Y - H*0.22, w: ROOM_W*0.22, h: H*0.22, label:'PRINTIFY PIPELINE'},
    board:    {x: LEFT_X + ROOM_W*0.62,  y: FLOOR_Y - H*0.44, w: ROOM_W*0.22, h: H*0.20, label:'STRATEGY BOARD'},
    ceo:      {x: LEFT_X + ROOM_W*0.87,  y: FLOOR_Y - H*0.44, w: ROOM_W*0.09, h: H*0.44, label:'CEO OFFICE'},
  };

  /* ── ANIMATE AGENTS ── */
  var agentStates = AGENTS.map(function(a, i){
    var zone = zones[a.zone] || zones.desk;
    return {
      agent: a,
      x: zone.x + zone.w * (0.2 + Math.random()*0.6),
      y: FLOOR_Y - 20,
      tx: zone.x + zone.w * (0.2 + Math.random()*0.6),
      ty: FLOOR_Y - 20,
      zone: zone,
      moveTimer: Math.random()*120,
      taskTimer: 0,
      action: 'idle',
      pulse: Math.random()*Math.PI*2,
      size: 14 + Math.random()*4,
    };
  });

  /* products on belt */
  var beltProds = Array.from({length:Math.max(Math.min(factory.products,6),2)},function(_,i){
    return {x: zones.pipeline.x + i*(zones.pipeline.w/6), speed: 0.6+Math.random()*0.4};
  });

  /* data particles */
  var dataParticles = [];
  for(var i=0;i<(isLive?60:20);i++){
    dataParticles.push({
      x: LEFT_X + Math.random()*ROOM_W,
      y: CEILING_Y + Math.random()*(FLOOR_Y-CEILING_Y),
      vx: (Math.random()-0.5)*1.2,
      vy: (Math.random()-0.5)*0.6,
      size: 1.5+Math.random()*2,
      col: [accentCol,'#00e5ff','#ff00ff','#00ff88'][Math.floor(Math.random()*4)],
      pulse: Math.random()*Math.PI*2,
      alpha: 0.3+Math.random()*0.6,
    });
  }

  /* blinking lights */
  var blinkLights = [];
  for(var bi=0;bi<8;bi++){
    blinkLights.push({
      x: zones.server.x + 12 + bi*12,
      y: zones.server.y + 20 + Math.floor(bi/4)*15,
      phase: Math.random()*Math.PI*2,
      col: isLive ? accentCol : '#ff3355',
    });
  }

  var frame = 0;

  function draw() {
    _officeAnim = requestAnimationFrame(draw);
    frame++;
    ctx.clearRect(0,0,W,H);

    /* ── BACKGROUND ── */
    var bgGrad = ctx.createLinearGradient(0,0,0,H);
    bgGrad.addColorStop(0,'#010510');
    bgGrad.addColorStop(1,'#020814');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0,0,W,H);

    /* ceiling glow */
    var cgGrad = ctx.createLinearGradient(0,CEILING_Y,0,CEILING_Y+60);
    cgGrad.addColorStop(0, accAlpha(0.15));
    cgGrad.addColorStop(1,'transparent');
    ctx.fillStyle = cgGrad;
    ctx.fillRect(LEFT_X, CEILING_Y, ROOM_W, 60);

    /* ── WALLS / FLOOR / CEILING ── */
    ctx.strokeStyle = accAlpha(0.4);
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(LEFT_X, CEILING_Y); ctx.lineTo(RIGHT_X, CEILING_Y);
    ctx.moveTo(LEFT_X, FLOOR_Y);   ctx.lineTo(RIGHT_X, FLOOR_Y);
    ctx.moveTo(LEFT_X, CEILING_Y); ctx.lineTo(LEFT_X, FLOOR_Y);
    ctx.moveTo(RIGHT_X,CEILING_Y); ctx.lineTo(RIGHT_X, FLOOR_Y);
    ctx.stroke();

    /* grid lines on floor */
    ctx.strokeStyle = accAlpha(0.06);
    ctx.lineWidth = 1;
    for(var gx=LEFT_X;gx<RIGHT_X;gx+=40){
      ctx.beginPath(); ctx.moveTo(gx,FLOOR_Y); ctx.lineTo(gx,CEILING_Y); ctx.stroke();
    }
    for(var gy=CEILING_Y;gy<FLOOR_Y;gy+=40){
      ctx.beginPath(); ctx.moveTo(LEFT_X,gy); ctx.lineTo(RIGHT_X,gy); ctx.stroke();
    }

    /* ceiling strip lights */
    [0.2,0.4,0.6,0.8].forEach(function(pct){
      var lx = LEFT_X + ROOM_W*pct;
      var lg = ctx.createLinearGradient(lx-2,CEILING_Y,lx+2,CEILING_Y+120);
      lg.addColorStop(0,accAlpha(isLive?0.9:0.3));
      lg.addColorStop(1,'transparent');
      ctx.fillStyle=lg;
      ctx.fillRect(lx-1,CEILING_Y,2,120);
      /* cone */
      var cg=ctx.createRadialGradient(lx,CEILING_Y,0,lx,CEILING_Y,80);
      cg.addColorStop(0,accAlpha(isLive?0.08:0.02));
      cg.addColorStop(1,'transparent');
      ctx.fillStyle=cg; ctx.fillRect(lx-80,CEILING_Y,160,120);
    });

    /* ── ZONES ── */
    Object.keys(zones).forEach(function(zk){
      var z = zones[zk];
      /* zone background */
      ctx.fillStyle = 'rgba(10,20,40,0.5)';
      ctx.fillRect(z.x, z.y, z.w, z.h);
      /* zone border */
      ctx.strokeStyle = accAlpha(0.25);
      ctx.lineWidth = 1;
      ctx.strokeRect(z.x, z.y, z.w, z.h);
      /* corner accents */
      ctx.strokeStyle = accentCol;
      ctx.lineWidth = 2;
      var cs=8;
      [[z.x,z.y,cs,0,0,cs],[z.x+z.w,z.y,-cs,0,0,cs],[z.x,z.y+z.h,cs,0,0,-cs],[z.x+z.w,z.y+z.h,-cs,0,0,-cs]].forEach(function(c){
        ctx.beginPath();ctx.moveTo(c[0]+c[2],c[1]);ctx.lineTo(c[0],c[1]);ctx.lineTo(c[0],c[1]+c[5]);ctx.stroke();
      });
      /* zone label */
      ctx.fillStyle=accAlpha(0.5);
      ctx.font='bold 9px JetBrains Mono,monospace';
      ctx.letterSpacing='1px';
      ctx.textAlign='center';
      ctx.fillText(z.label, z.x+z.w/2, z.y+12);
    });

    /* ── SERVER RACKS ── */
    var svz = zones.server;
    var rackW=18, rackH=svz.h*0.7, rackSpacing=26;
    for(var ri=0;ri<5;ri++){
      var rx=svz.x+10+ri*rackSpacing;
      var ry=svz.y+svz.h-rackH-10;
      ctx.fillStyle='#0d1a2e'; ctx.fillRect(rx,ry,rackW,rackH);
      ctx.strokeStyle=accAlpha(0.4); ctx.lineWidth=1; ctx.strokeRect(rx,ry,rackW,rackH);
      /* rack lights */
      for(var rli=0;rli<6;rli++){
        var blink=blinkLights[ri*1]||{phase:ri*0.5};
        var lit = isLive&&(Math.sin(frame*0.08+blink.phase+rli*0.3)>0.3);
        ctx.fillStyle=lit?accentCol:'#330a0a';
        ctx.beginPath();ctx.arc(rx+rackW/2, ry+8+rli*12, 3, 0, Math.PI*2);ctx.fill();
        if(lit){ctx.shadowColor=accentCol;ctx.shadowBlur=6;ctx.beginPath();ctx.arc(rx+rackW/2,ry+8+rli*12,3,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;}
      }
    }
    /* big screen on server room wall */
    var scrX=svz.x+3, scrY=svz.y+svz.h*0.05, scrW=svz.w-6, scrH=svz.h*0.28;
    var scrGrd=ctx.createLinearGradient(scrX,scrY,scrX,scrY+scrH);
    scrGrd.addColorStop(0,accAlpha(isLive?0.35:0.08)); scrGrd.addColorStop(1,accAlpha(0.02));
    ctx.fillStyle=scrGrd; ctx.fillRect(scrX,scrY,scrW,scrH);
    ctx.strokeStyle=accentCol; ctx.lineWidth=1.5; ctx.strokeRect(scrX,scrY,scrW,scrH);
    ctx.fillStyle=accentCol; ctx.font='bold 8px monospace'; ctx.textAlign='center';
    ctx.fillText(isLive?'LIVE':'IDLE',scrX+scrW/2,scrY+scrH*0.38);
    ctx.fillStyle='rgba(255,255,255,0.6)'; ctx.font='7px monospace';
    ctx.fillText('$'+factory.revenue_month.toFixed(0),scrX+scrW/2,scrY+scrH*0.65);
    ctx.fillText(factory.sales+' sales',scrX+scrW/2,scrY+scrH*0.85);

    /* ── WORKSTATION DESKS ── */
    var dsk=zones.desk;
    var cols2=3, rows=2, dW=(dsk.w-20)/(cols2), dH=(dsk.h-15)/rows;
    for(var dr=0;dr<rows;dr++){
      for(var dc=0;dc<cols2;dc++){
        var dx=dsk.x+10+dc*dW, dy=dsk.y+8+dr*dH;
        /* desk surface */
        ctx.fillStyle='#1a2640'; ctx.fillRect(dx+2,dy+dH*0.55,dW-8,8);
        ctx.strokeStyle='#223344'; ctx.lineWidth=1; ctx.strokeRect(dx+2,dy+dH*0.55,dW-8,8);
        /* monitor */
        var mCol=aColors2[dr*cols2+dc]||accentCol;
        ctx.fillStyle='#050d18'; ctx.fillRect(dx+8,dy+dH*0.15,dW-20,dH*0.38);
        ctx.strokeStyle=mCol; ctx.lineWidth=1.5; ctx.strokeRect(dx+8,dy+dH*0.15,dW-20,dH*0.38);
        /* monitor glow */
        var mg=ctx.createRadialGradient(dx+dW/2,dy+dH*0.34,0,dx+dW/2,dy+dH*0.34,30);
        var mr2=parseInt(mCol.slice(1,3),16),mg2=parseInt(mCol.slice(3,5),16),mb2=parseInt(mCol.slice(5,7),16);
        mg.addColorStop(0,'rgba('+mr2+','+mg2+','+mb2+','+(isLive?0.18:0.04)+')');
        mg.addColorStop(1,'transparent');
        ctx.fillStyle=mg; ctx.fillRect(dx,dy,dW,dH*0.6);
        /* monitor scanline flicker */
        if(isLive&&frame%3===0){
          var scanY=dy+dH*0.15+((frame*2)%(dH*0.38));
          ctx.strokeStyle='rgba('+mr2+','+mg2+','+mb2+',0.3)';
          ctx.lineWidth=1;
          ctx.beginPath();ctx.moveTo(dx+8,scanY);ctx.lineTo(dx+dW-12,scanY);ctx.stroke();
        }
      }
    }

    /* ── PRINTIFY PIPELINE ── */
    var plz=zones.pipeline;
    /* belt */
    ctx.fillStyle='#0d1a2e'; ctx.fillRect(plz.x+5,plz.y+plz.h*0.5,plz.w-10,12);
    ctx.strokeStyle=accAlpha(0.4); ctx.lineWidth=1; ctx.strokeRect(plz.x+5,plz.y+plz.h*0.5,plz.w-10,12);
    /* belt motion lines */
    if(isLive){
      ctx.strokeStyle=accAlpha(0.2); ctx.lineWidth=1;
      for(var bi2=0;bi2<5;bi2++){
        var bx=(plz.x+5+(frame*2+bi2*20)%(plz.w-10));
        ctx.beginPath();ctx.moveTo(bx,plz.y+plz.h*0.5+1);ctx.lineTo(bx,plz.y+plz.h*0.5+11);ctx.stroke();
      }
    }
    /* moving products */
    beltProds.forEach(function(p){
      if(isLive) p.x+=p.speed;
      if(p.x>plz.x+plz.w-10) p.x=plz.x+5;
      ctx.fillStyle=accentCol;
      ctx.shadowColor=accentCol; ctx.shadowBlur=6;
      ctx.fillRect(p.x,plz.y+plz.h*0.38,14,14);
      ctx.shadowBlur=0;
      ctx.strokeStyle='rgba(255,255,255,0.4)'; ctx.lineWidth=1; ctx.strokeRect(p.x,plz.y+plz.h*0.38,14,14);
    });
    /* label */
    ctx.fillStyle=accAlpha(0.6); ctx.font='bold 8px monospace'; ctx.textAlign='center';
    ctx.fillText('PRINTIFY',plz.x+plz.w/2,plz.y+plz.h*0.25);
    ctx.fillStyle='rgba(255,255,255,0.5)'; ctx.font='7px monospace';
    ctx.fillText(factory.products+' products',plz.x+plz.w/2,plz.y+plz.h*0.38);

    /* ── STRATEGY BOARD ── */
    var brd=zones.board;
    ctx.fillStyle='#0a1828'; ctx.fillRect(brd.x+4,brd.y+20,brd.w-8,brd.h-25);
    ctx.strokeStyle=accAlpha(0.3); ctx.lineWidth=1; ctx.strokeRect(brd.x+4,brd.y+20,brd.w-8,brd.h-25);
    /* board items */
    var items=[['Q2 PLAN','#00ff88'],['ETSY SEO','#00e5ff'],['NEW FAC','#ffd700'],['AGENTS','#aa44ff']];
    items.forEach(function(it,i){
      var ix=brd.x+8+i*((brd.w-12)/4), iy=brd.y+32;
      var ir2=parseInt(it[1].slice(1,3),16),ig2=parseInt(it[1].slice(3,5),16),ib2=parseInt(it[1].slice(5,7),16);
      ctx.fillStyle='rgba('+ir2+','+ig2+','+ib2+',0.12)'; ctx.fillRect(ix,iy,(brd.w-16)/4-2,brd.h-40);
      ctx.strokeStyle=it[1]; ctx.lineWidth=1; ctx.strokeRect(ix,iy,(brd.w-16)/4-2,brd.h-40);
      ctx.fillStyle=it[1]; ctx.font='bold 7px monospace'; ctx.textAlign='center';
      ctx.fillText(it[0],ix+(brd.w-16)/8,iy+12);
    });

    /* ── CEO OFFICE ── */
    var ceo=zones.ceo;
    var deskX=ceo.x+8, deskY=ceo.y+ceo.h*0.55;
    ctx.fillStyle='#1a2640'; ctx.fillRect(deskX,deskY,ceo.w-16,10);
    ctx.strokeStyle='#223344'; ctx.lineWidth=1; ctx.strokeRect(deskX,deskY,ceo.w-16,10);
    ctx.fillStyle='#050d18'; ctx.fillRect(deskX+4,deskY-ceo.h*0.32,ceo.w-24,ceo.h*0.3);
    ctx.strokeStyle=accentCol; ctx.lineWidth=1.5; ctx.strokeRect(deskX+4,deskY-ceo.h*0.32,ceo.w-24,ceo.h*0.3);

    /* ── DATA PARTICLES ── */
    dataParticles.forEach(function(p){
      p.pulse+=0.04; p.x+=p.vx; p.y+=p.vy;
      var pr2=parseInt(p.col.slice(1,3),16),pg2=parseInt(p.col.slice(3,5),16),pb2=parseInt(p.col.slice(5,7),16);
      var pa=p.alpha*Math.abs(Math.sin(p.pulse));
      if(p.x<LEFT_X||p.x>RIGHT_X)p.vx*=-1;
      if(p.y<CEILING_Y||p.y>FLOOR_Y)p.vy*=-1;
      ctx.fillStyle='rgba('+pr2+','+pg2+','+pb2+','+pa+')';
      ctx.shadowColor=p.col; ctx.shadowBlur=4;
      ctx.beginPath();ctx.arc(p.x,p.y,p.size,0,Math.PI*2);ctx.fill();
      ctx.shadowBlur=0;
    });

    /* ── AGENTS ── */
    agentStates.forEach(function(s){
      s.pulse+=0.06;
      /* movement */
      s.moveTimer--;
      if(s.moveTimer<=0){
        s.moveTimer=80+Math.random()*150;
        var margin=20;
        s.tx=s.zone.x+margin+Math.random()*(s.zone.w-margin*2);
        s.ty=FLOOR_Y-s.size-4;
        s.action=isLive?['typing','walking','thinking','reading'][Math.floor(Math.random()*4)]:'idle';
      }
      var spd=1.2;
      var dx2=s.tx-s.x, dy2=s.ty-s.y, dist=Math.sqrt(dx2*dx2+dy2*dy2);
      if(dist>spd){s.x+=dx2/dist*spd;s.y+=dy2/dist*spd;}

      /* shadow */
      ctx.fillStyle='rgba(0,0,0,0.25)';
      ctx.beginPath();ctx.ellipse(s.x,FLOOR_Y-2,s.size*0.6,3,0,0,Math.PI*2);ctx.fill();

      /* body */
      var ar2=parseInt(s.agent.col.slice(1,3),16),ag2=parseInt(s.agent.col.slice(3,5),16),ab2=parseInt(s.agent.col.slice(5,7),16);
      /* legs */
      if(dist>2&&s.action==='walking'){
        var legSwing=Math.sin(frame*0.2)*5;
        ctx.strokeStyle='rgba('+ar2+','+ag2+','+ab2+',0.7)';ctx.lineWidth=3;
        ctx.beginPath();ctx.moveTo(s.x,s.y);ctx.lineTo(s.x-4+legSwing,s.y+s.size*0.6);ctx.stroke();
        ctx.beginPath();ctx.moveTo(s.x,s.y);ctx.lineTo(s.x+4-legSwing,s.y+s.size*0.6);ctx.stroke();
      } else {
        ctx.strokeStyle='rgba('+ar2+','+ag2+','+ab2+',0.7)';ctx.lineWidth=3;
        ctx.beginPath();ctx.moveTo(s.x,s.y);ctx.lineTo(s.x-4,s.y+s.size*0.6);ctx.stroke();
        ctx.beginPath();ctx.moveTo(s.x,s.y);ctx.lineTo(s.x+4,s.y+s.size*0.6);ctx.stroke();
      }
      /* body */
      var bodyGrad=ctx.createLinearGradient(s.x-s.size*0.5,s.y-s.size*0.7,s.x+s.size*0.5,s.y);
      bodyGrad.addColorStop(0,'rgba('+ar2+','+ag2+','+ab2+',0.9)');
      bodyGrad.addColorStop(1,'rgba('+ar2+','+ag2+','+ab2+',0.5)');
      ctx.fillStyle=bodyGrad;
      ctx.beginPath();ctx.ellipse(s.x,s.y-s.size*0.35,s.size*0.45,s.size*0.55,0,0,Math.PI*2);ctx.fill();
      /* head glow */
      var glow=0.5+0.5*Math.sin(s.pulse);
      ctx.shadowColor=s.agent.col; ctx.shadowBlur=8*glow;
      ctx.fillStyle='rgba('+ar2+','+ag2+','+ab2+',0.95)';
      ctx.beginPath();ctx.arc(s.x,s.y-s.size,s.size*0.45,0,Math.PI*2);ctx.fill();
      ctx.shadowBlur=0;
      /* head border */
      ctx.strokeStyle=s.agent.col;ctx.lineWidth=1.5;
      ctx.beginPath();ctx.arc(s.x,s.y-s.size,s.size*0.45,0,Math.PI*2);ctx.stroke();
      /* face dot */
      ctx.fillStyle='rgba('+ar2+','+ag2+','+ab2+',0.4)';
      ctx.fillRect(s.x-s.size*0.25,s.y-s.size-1,s.size*0.5,2);
      /* arms based on action */
      if(s.action==='typing'){
        var arm=Math.sin(frame*0.3)*4;
        ctx.strokeStyle='rgba('+ar2+','+ag2+','+ab2+',0.7)';ctx.lineWidth=2.5;
        ctx.beginPath();ctx.moveTo(s.x-s.size*0.4,s.y-s.size*0.6);ctx.lineTo(s.x-s.size*0.7,s.y-s.size*0.3+arm);ctx.stroke();
        ctx.beginPath();ctx.moveTo(s.x+s.size*0.4,s.y-s.size*0.6);ctx.lineTo(s.x+s.size*0.7,s.y-s.size*0.3-arm);ctx.stroke();
        /* typing dots */
        for(var td=0;td<3;td++){
          var tpulse=Math.sin(frame*0.15+td*0.8)>0;
          if(tpulse){ctx.fillStyle=s.agent.col;ctx.beginPath();ctx.arc(s.x-4+td*4,s.y-s.size*0.1,1.5,0,Math.PI*2);ctx.fill();}
        }
      } else if(s.action==='thinking'){
        ctx.strokeStyle='rgba('+ar2+','+ag2+','+ab2+',0.7)';ctx.lineWidth=2.5;
        ctx.beginPath();ctx.moveTo(s.x-s.size*0.4,s.y-s.size*0.6);ctx.lineTo(s.x-s.size*0.3,s.y-s.size*1.3);ctx.stroke();
        /* thought bubble */
        ctx.fillStyle='rgba('+ar2+','+ag2+','+ab2+',0.15)';
        ctx.beginPath();ctx.arc(s.x+s.size*0.5,s.y-s.size*1.6,s.size*0.5,0,Math.PI*2);ctx.fill();
        ctx.strokeStyle=s.agent.col;ctx.lineWidth=1;ctx.stroke();
        ctx.fillStyle=s.agent.col;ctx.font='bold 8px monospace';ctx.textAlign='center';
        ctx.fillText('?',s.x+s.size*0.5,s.y-s.size*1.55);
      } else {
        ctx.strokeStyle='rgba('+ar2+','+ag2+','+ab2+',0.7)';ctx.lineWidth=2.5;
        ctx.beginPath();ctx.moveTo(s.x-s.size*0.4,s.y-s.size*0.6);ctx.lineTo(s.x-s.size*0.8,s.y-s.size*0.2);ctx.stroke();
        ctx.beginPath();ctx.moveTo(s.x+s.size*0.4,s.y-s.size*0.6);ctx.lineTo(s.x+s.size*0.8,s.y-s.size*0.2);ctx.stroke();
      }
      /* name tag */
      ctx.fillStyle='rgba(0,0,0,0.7)';
      var tw2=ctx.measureText(s.agent.name).width+6;
      ctx.fillRect(s.x-tw2/2,s.y-s.size*2.2,tw2,13);
      ctx.strokeStyle=s.agent.col;ctx.lineWidth=0.5;ctx.strokeRect(s.x-tw2/2,s.y-s.size*2.2,tw2,13);
      ctx.fillStyle=s.agent.col;ctx.font='bold 7px monospace';ctx.textAlign='center';
      ctx.fillText(s.agent.name,s.x,s.y-s.size*2.2+10);
      /* task bubble when active */
      if(isLive&&s.action!=='idle'&&s.action!=='walking'){
        s.taskTimer++;
        if(s.taskTimer<120){
          ctx.fillStyle='rgba(0,0,0,0.8)';
          var tw3=ctx.measureText(s.agent.task).width+8;
          ctx.fillRect(s.x-tw3/2,s.y-s.size*3.1,tw3,13);
          ctx.strokeStyle=s.agent.col;ctx.lineWidth=0.5;ctx.strokeRect(s.x-tw3/2,s.y-s.size*3.1,tw3,13);
          ctx.fillStyle='rgba(255,255,255,0.8)';ctx.font='6px monospace';ctx.textAlign='center';
          ctx.fillText(s.agent.task,s.x,s.y-s.size*3.1+9);
        } else {
          s.taskTimer=0;
        }
      }
    });

    /* ── FACTORY NAME OVERLAY ── */
    ctx.textAlign='center';
    ctx.fillStyle=accAlpha(0.08);
    ctx.font='bold '+(W*0.06)+'px monospace';
    ctx.fillText(factory.name.toUpperCase(), W/2, H*0.55);

    /* ── STATUS INDICATOR ── */
    var statusX=W-80, statusY=CEILING_Y+30;
    var statusPulse=isLive?(0.5+0.5*Math.sin(frame*0.1)):0.3;
    ctx.fillStyle=isLive?'rgba(0,255,136,'+statusPulse+')':'rgba(255,215,0,0.3)';
    ctx.shadowColor=isLive?'#00ff88':'#ffd700'; ctx.shadowBlur=isLive?12:4;
    ctx.beginPath();ctx.arc(statusX,statusY,8,0,Math.PI*2);ctx.fill();
    ctx.shadowBlur=0;
    ctx.fillStyle='rgba(255,255,255,0.5)';ctx.font='bold 9px monospace';ctx.textAlign='left';
    ctx.fillText(factory.status,statusX+14,statusY+4);

    /* frame counter (shows activity) */
    ctx.fillStyle=accAlpha(0.2);ctx.font='7px monospace';ctx.textAlign='right';
    ctx.fillText('FRAME '+frame+' · '+new Date().toLocaleTimeString(),RIGHT_X-4,FLOOR_Y+14);

    ctx.textAlign='left';
  }

  var aColors2 = [accentCol,'#00e5ff','#ff00ff','#ffd700','#aa44ff','#00ff88'];
  draw();
}


/* ── IRIS VAULT STATUS ── */
async function checkIrisStatus() {
  try {
    var r = await fetch('/iris/health');
    var d = await r.json();
    var el = document.getElementById('iris-status-badge');
    var am = document.getElementById('iris-memories');
    var vn = document.getElementById('iris-notes');
    if (el) {
      el.textContent = d.status || 'UNKNOWN';
      el.style.color = d.ok ? '#00ff88' : '#ff3355';
    }
    if (am) am.textContent = d.agent_memories + ' memories';
    if (vn) vn.textContent = d.vault_notes + ' notes';
  } catch(e) {}
}

document.addEventListener('DOMContentLoaded', function() {
  setTimeout(function() {
    checkIrisStatus();
    setInterval(checkIrisStatus, 15000);
  }, 5000);
});
