(() => {
  'use strict';
  const W=1920,H=1080,DURATION=30,starts=[0,3.5,8.5,14,22,26,30];
  const PINK='#ff4b96', PURPLE='#c4a7fa', CYAN='#7bdde3', WHITE='#edf0f7', DIM='#8192a5', GREEN='#7fe2ba';
  const canvas=document.querySelector('#field'),ctx=canvas.getContext('2d',{alpha:false});
  const toggle=document.querySelector('#toggle');
  const soundButton=document.querySelector('#sound');
  const soundtrack=new Audio('assets/sound.mp3');soundtrack.preload='none';
  let soundOn=false;
  if(!ctx){document.querySelector('.fallback').style.display='flex';return}
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  let t=reduced.matches?DURATION:0,playing=!reduced.matches,last=0,ready=false,rose=null,elephant=null;
  // Fixed seed: repeatable visual field and repeatable exported captures.
  let seed=216;const rnd=()=>((seed=(seed*1664525+1013904223)>>>0)/4294967296);
  const columns=Array.from({length:82},()=>({x:Math.floor(rnd()*W/21)*21,y:Math.floor(rnd()*H*2-H),speed:34+rnd()*76,count:6+Math.floor(rnd()*12)}));
  const stars=Array.from({length:135},()=>({x:rnd()*W,y:rnd()*H,r:rnd()<.8?1:2}));
  const clamp=x=>Math.max(0,Math.min(1,x));const ease=x=>{x=clamp(x);return x*x*(3-2*x)};
  const font=(size=20,bold=false)=>`${bold?'700':'400'} ${size}px ui-monospace,Consolas,monospace`;
  function text(s,x,y,size=20,color=WHITE,bold=false,align='left'){
    ctx.font=font(size,bold);ctx.textAlign=align;ctx.textBaseline='top';ctx.fillStyle=color;ctx.fillText(s,x,y);
  }
  function line(x1,y1,x2,y2,color='#344052',width=1){ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke()}
  function box(x,y,w,h,color='#101b26',edge='#3b5368'){ctx.fillStyle=color;ctx.fillRect(x,y,w,h);ctx.strokeStyle=edge;ctx.lineWidth=1;ctx.strokeRect(x,y,w,h)}
  function brackets(x,y,w,h,color){for(const [xx,yy,sx,sy] of [[x,y,1,1],[x+w,y,-1,1],[x,y+h,1,-1],[x+w,y+h,-1,-1]]){line(xx,yy,xx+sx*30,yy,color,2);line(xx,yy,xx,yy+sy*30,color,2)}}
  function ring(cx,cy,r,color,angle){ctx.beginPath();ctx.arc(cx,cy,r,angle,angle+2.15);ctx.strokeStyle=color;ctx.lineWidth=2;ctx.stroke()}
  function load(src){return new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>reject(new Error(`Could not load ${src}`));im.src=src})}
  function binaryArt(image,kind){
    // Source PNG is a sampling template only. The output contains binary glyphs exclusively.
    const columns=128,rows=144,cellW=5,cellH=5;
    const sample=document.createElement('canvas');sample.width=columns;sample.height=rows;
    const s=sample.getContext('2d',{willReadFrequently:true});
    const factor=Math.min(columns/image.width,rows/image.height),iw=image.width*factor,ih=image.height*factor;
    s.drawImage(image,(columns-iw)/2,(rows-ih)/2,iw,ih);
    const px=s.getImageData(0,0,columns,rows).data;
    const out=document.createElement('canvas');out.width=columns*cellW;out.height=rows*cellH;
    const o=out.getContext('2d');o.textBaseline='top';o.font='700 7px ui-monospace,Consolas,monospace';
    for(let y=0;y<rows;y++)for(let x=0;x<columns;x++){
      const i=(y*columns+x)*4,a=px[i+3];if(a<22)continue;
      const r=kind==='rose'?Math.max(56,Math.min(255,px[i]*1.14+20)):Math.min(255,px[i]*1.13+7);
      const g=kind==='rose'?Math.max(24,Math.min(255,px[i+1]*1.08+5)):Math.min(255,px[i+1]*1.13+7);
      const b=kind==='rose'?Math.max(50,Math.min(255,px[i+2]*1.14+12)):Math.min(255,px[i+2]*1.13+7);
      o.fillStyle=`rgba(${r|0},${g|0},${b|0},${Math.min(1,a/196)})`;
      o.fillText((((r*3+g*4+b)/8+x*7+y*11)|0)%3?'1':'0',x*cellW,y*cellH-2);
    }
    return out;
  }
  function art(asset,x,y,p,color,vertical=true){
    if(!asset||p<=0)return;const amount=ease(p),ww=asset.width,hh=asset.height;
    ctx.save();ctx.beginPath();ctx.rect(x,y,vertical?ww:ww*amount,vertical?hh*amount:hh);ctx.clip();
    ctx.shadowColor=color;ctx.shadowBlur=16;ctx.drawImage(asset,x,y);ctx.restore();
    if(amount<.999){if(vertical)line(x-15,y+hh*amount,x+ww+15,y+hh*amount,CYAN,2);else line(x+ww*amount,y-15,x+ww*amount,y+hh+15,PINK,2)}
    const scan=y+(t*105%hh);if(scan<y+hh*amount)line(x+24,scan,x+ww-24,scan,'#516e85');
  }
  function base(){
    ctx.fillStyle='#040810';ctx.fillRect(0,0,W,H);
    ctx.strokeStyle='#0c1825';ctx.lineWidth=1;ctx.beginPath();for(let x=0;x<W;x+=40){ctx.moveTo(x,0);ctx.lineTo(x,H)}for(let y=0;y<H;y+=40){ctx.moveTo(0,y);ctx.lineTo(W,y)}ctx.stroke();
    for(const c of columns)for(let j=0;j<c.count;j++){
      const yy=((c.y+t*c.speed+j*20)%(H+300)+H+300)%(H+300)-150;
      if(yy>112&&yy<953)text(((Math.floor(t*4)+j+c.x/21)&1)?'1':'0',c.x,yy,12,j<c.count-2?'#15333e':'#4a5675',true);
    }
    ctx.fillStyle='#23364c';for(const st of stars)ctx.fillRect(st.x,st.y,st.r,st.r);
  }
  function chrome(phase){
    line(60,84,1860,84,'#365268');text('GENTLEMAN // EXPERIMENT 001',63,38,18,CYAN,true);
    text(`CANVAS 1920×1080  /  PHASE ${String(phase).padStart(2,'0')}`,1854,38,17,DIM,false,'right');
    line(60,985,1860,985,'#365268');line(60,985,60+1800*t/DURATION,985,PINK,3);
    text('GENTLE AI × ENGRAM  //  BINARY MEMORY FIELD',62,1007,16,DIM);
    text(`${String(Math.floor(t)).padStart(2,'0')}:00 / 30:00`,1852,1007,16,DIM,false,'right');
  }
  function render(){
    if(!ready)return;base();let phase=1;
    if(t<3.5){
      text('// CONNECTION INITIALIZING',92,151,20,PINK);
      text('EVERY SESSION LEAVES A TRACE.',92,239,47,WHITE,true);
      text('WHAT IF THE NEXT ONE COULD READ IT?',92,326,34,CYAN,true);
      ['agent environment online','skill network linked','persistent memory attached'].forEach((v,j)=>{if(t>.55+j*.42)text(`[0${j+1}] ${v}`,102,484+j*52,24,j===2?GREEN:DIM)});
      art(rose,1155,160,(t-.35)/2.2,PINK);brackets(1135,144,680,755,PINK);
    }else if(t<8.5){
      phase=2;const q=t-3.5;
      text('01 / THE ORCHESTRATOR',92,148,21,PINK);text('GENTLE AI',92,250,82,WHITE,true);text('STRUCTURE THE WORK.',98,365,39,PINK,true);
      [['SKILLS','know what to use'],['FLOW','know when to act'],['EVIDENCE','know what worked']].forEach(([k,v],j)=>{const y=488+j*103;box(89,y,821,81);text(`0${j+1}  ${k}`,110,y+15,24,CYAN,true);text(v,386,y+18,22,DIM);line(97,y+79,97+804*ease((q-j*.4)/1.3),y+79,PINK,3)});
      ring(1480,527,432,PINK,t*.6);ring(1480,527,405,'#6a3456',-t*.8);ring(1480,527,379,'#3b3650',t*.5);
      art(rose,1150,174,q/2.1,PINK);brackets(1130,155,690,750,PINK);text('ROSE / GENTLE AI',1490,934,17,PINK,false,'center');
    }else if(t<14){
      phase=3;const q=t-8.5;
      text('02 / THE MEMORY',1125,148,21,PURPLE);text('ENGRAM',1125,250,82,WHITE,true);text('REMEMBER WHAT MATTERS.',1129,365,32,PURPLE,true);
      [['DECISION','architecture saved'],['DISCOVERY','finding retained'],['CONTEXT','ready for next session']].forEach(([k,v],j)=>{const y=485+j*105;box(1117,y,698,81,'#161828','#514969');text(k,1143,y+12,23,PURPLE,true);text(v,1143,y+43,19,DIM);if(q>j*.48)text('[ OK ]',1760,y+20,18,GREEN)});
      ring(435,525,424,PURPLE,-t*.5);ring(435,525,394,'#684d89',t*.7);ring(435,525,365,'#3f405d',-t*.45);
      art(elephant,120,170,q/2.3,PURPLE);brackets(98,153,690,748,PURPLE);text('ELEPHANT / ENGRAM',449,934,17,PURPLE,false,'center');
    }else if(t<22){
      phase=4;const q=t-14;
      text('03 / A SHARED CURRENT',96,150,21,CYAN);text('GUIDE  →  BUILD  →  REMEMBER  →  CONTINUE',960,192,29,WHITE,true,'center');
      art(rose,124,240,q/1.5,PINK);art(elephant,1153,240,(q-.3)/1.5,PURPLE);
      brackets(110,227,667,661,PINK);brackets(1142,227,667,661,PURPLE);line(786,522,1136,522,'#406473',3);
      for(let j=0;j<4;j++){ctx.beginPath();ctx.arc(786+(q*100+j*90)%350,522,8,0,Math.PI*2);ctx.fillStyle=j%2?PINK:CYAN;ctx.fill()}
      ring(960,522,143,'#4d8b99',t*.4);
      for(let j=0;j<8;j++)text(((j+Math.floor(t*3))&1)?'1':'0',775+(q*140+j*108)%365,442+(j%3)*34,12,j%2?CYAN:'#795789',true);
      [['intent','agent'],['execution','tools'],['memory','context']].forEach(([a,b],j)=>{text(a,825,366+j*75,17,DIM);text(b,995,366+j*75,17,CYAN)});
      text('GENTLE AI',444,929,24,PINK,true,'center');text('ENGRAM',1480,929,24,PURPLE,true,'center');
    }else if(t<26){
      phase=5;const q=t-22;
      text('04 / THE NEXT SESSION',93,153,21,GREEN);text('$ pi --resume',93,239,52,WHITE,true);
      box(89,338,1741,447,'#0a1520','#3d7076');text('~/workspace  /  engram://project',126,368,20,DIM);line(90,414,1830,414,'#335766');
      ['connecting memory provider','reading decisions','reconstructing context','resuming from last checkpoint'].forEach((v,j)=>{if(q>.25+j*.46)text(`> ${v.padEnd(32,' ')} [OK]`,144,467+j*62,25,j%2?GREEN:WHITE)});
      if(q>2.5)text('> Ready. The work continues._',144,733,27,PINK,true);
      text('NO RESET. JUST CONTINUITY.',95,846,51,WHITE,true);
    }else{
      phase=6;const q=t-26;
      art(rose,170,154,q/1.1,PINK);art(elephant,1130,154,(q-.2)/1.1,PURPLE);
      brackets(161,143,651,754,PINK);brackets(1118,143,651,754,PURPLE);
      text('×',960,390,105,CYAN,true,'center');box(515,852,895,108,'#07101a','#07101a');
      text('GENTLE AI × ENGRAM',960,870,57,WHITE,true,'center');text('BUILD WITH PURPOSE. REMEMBER WHAT MATTERS.',960,928,24,PINK,false,'center');
    }
    chrome(phase);
  }
  function frame(now){if(!last)last=now;if(playing){t=Math.min(DURATION,t+Math.min(.08,(now-last)/1000));if(t===DURATION){playing=false;soundtrack.pause()}}last=now;render();requestAnimationFrame(frame)}
  function labels(){toggle.textContent=playing?'Ⅱ':'▶';toggle.setAttribute('aria-label',playing?'Pause animation':'Play animation')}
  function syncSound(){if(soundOn){soundtrack.currentTime=Math.min(t,29.99);if(playing)soundtrack.play().catch(()=>{});else soundtrack.pause()}}
  toggle.onclick=()=>{if(t>=DURATION)t=0;playing=!playing;last=performance.now();labels();syncSound();render()};
  document.querySelector('#replay').onclick=()=>{t=0;playing=true;last=performance.now();labels();syncSound();render()};
  document.querySelector('#skip').onclick=()=>{t=DURATION;playing=false;labels();syncSound();render()};
  soundButton.onclick=()=>{soundOn=!soundOn;soundButton.textContent=soundOn?'♫':'♪';soundButton.setAttribute('aria-label',soundOn?'Disable sound':'Enable sound');if(soundOn)syncSound();else soundtrack.pause()};
  document.addEventListener('keydown',e=>{if(e.key===' '){e.preventDefault();toggle.click()}if(e.key==='ArrowRight'){t=starts.find(x=>x>t+.05)??DURATION;syncSound();render()}if(e.key==='ArrowLeft'){t=[...starts].reverse().find(x=>x<t-.05)??0;syncSound();render()}});
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&playing){playing=false;soundtrack.pause();labels()}});
  Promise.all([load('assets/rose.png'),load('assets/engram-elephant.png')]).then(([a,b])=>{rose=binaryArt(a,'rose');elephant=binaryArt(b,'elephant');ready=true;labels();render();document.documentElement.classList.add('ready');requestAnimationFrame(frame)}).catch(error=>{document.querySelector('.fallback').style.display='flex';console.error(error)});
})();
