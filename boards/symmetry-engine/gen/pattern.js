const PAL=['#db2945','#f27a0d','#d9a800','#29a13d','#00999e','#1a66d9','#6b3dd1','#cc2e9e'];
const {FRIEZES,WALLPAPERS,apply}=window.SYM;
const MOTIF=[{pts:[[.08,.1],[.2,.12],[.3,.22],[.34,.36]],col:PAL[0],w:4},{pts:[[.12,.3],[.16,.4],[.12,.46]],col:PAL[5],w:4},{pts:[[.3,.08],[.36,.08]],col:PAL[3],w:6}];
const FMOTIF=[{pts:[[.1,.25],[.18,.3],[.28,.5],[.3,.7]],col:PAL[5],w:4},{pts:[[.14,.6],[.2,.62]],col:PAL[0],w:6}];
function sized(cv){const d=Math.min(2,devicePixelRatio||1),b=cv.getBoundingClientRect();cv.width=Math.max(1,Math.round(b.width*d));cv.height=Math.max(1,Math.round(b.height*d));const c=cv.getContext('2d');c.setTransform(d,0,0,d,0,0);return {c,w:b.width,h:b.height};}
function line(c,pts){c.beginPath();pts.forEach((p,i)=>i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1]));c.stroke();}
function wall(cv,id,cell,scaleDiv){const {c,w,h}=sized(cv),g=WALLPAPERS.find(x=>x.id===id),{A,B}=g.lattice,s=w/(scaleDiv||3.2),cx=w/2,cy=h/2;
 const toS=([u,v])=>[cx+s*(u*A[0]+v*B[0]),cy-s*(u*A[1]+v*B[1])];const R=Math.ceil(Math.max(w,h)/s/0.6)+2;
 c.fillStyle=getComputedStyle(document.documentElement).getPropertyValue('--sheet');c.fillRect(0,0,w,h);
 if(cell){c.beginPath();[[0,0],[1,0],[1,1],[0,1]].forEach((p,i)=>{const q=toS(p);i?c.lineTo(...q):c.moveTo(...q)});c.closePath();c.strokeStyle='#9aa1b2';c.setLineDash([4,5]);c.lineWidth=1;c.stroke();c.setLineDash([]);}
 c.lineCap=c.lineJoin='round';for(const st of MOTIF){c.strokeStyle=st.col;c.lineWidth=st.w*w/600+1;for(const o of g.ops){const b=st.pts.map(p=>apply(o,p[0],p[1]));for(let i=-R;i<=R;i++)for(let j=-R;j<=R;j++)line(c,b.map(([u,v])=>toS([u+i,v+j])));}}}
function frieze(cv,id){const {c,w,h}=sized(cv),g=FRIEZES.find(x=>x.id===id),cw=Math.min(h*.55,w/5),toS=([x,y])=>[x*cw,h/2-y*cw];
 c.fillStyle=getComputedStyle(document.documentElement).getPropertyValue('--sheet');c.fillRect(0,0,w,h);c.strokeStyle='#dfe2ea';c.beginPath();c.moveTo(0,h/2);c.lineTo(w,h/2);c.stroke();
 c.lineCap=c.lineJoin='round';for(const st of FMOTIF){c.strokeStyle=st.col;c.lineWidth=st.w*h/300+1;for(const o of g.ops)for(let k=-2;k<=Math.ceil(w/cw)+2;k++)line(c,st.pts.map(p=>{const q=apply(o,p[0],p[1]);return toS([q[0]+k,q[1]]);}));}}
function renderWallpaper(id){const cv=document.getElementById('cv');const go=()=>wall(cv,id,true);go();addEventListener('resize',go);}
function renderFrieze(id){const cv=document.getElementById('cv');const go=()=>frieze(cv,id);go();addEventListener('resize',go);}
function renderTiles(){const go=()=>{document.querySelectorAll('canvas[data-wp]').forEach(cv=>wall(cv,cv.dataset.wp,false,cv.dataset.ws?2.4:1.6));document.querySelectorAll('canvas[data-fr]').forEach(cv=>frieze(cv,cv.dataset.fr));};go();addEventListener('resize',go);}
