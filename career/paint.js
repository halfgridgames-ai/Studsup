// World Tour (Career) zone backdrops painted in code: the stand-ins until the Midjourney pictures go in career/zoneN.webp.
// careerPaint(zone 0-5, width, height) returns a canvas. Same seed every time, so a zone always looks the same.
(function(){
function rng(s){return()=>{s=(s*16807)%2147483647;return(s-1)/2147483646;};}
function lin(c,y0,y1,stops){const g=c.createLinearGradient(0,y0,0,y1);stops.forEach((s,i)=>g.addColorStop(i/(stops.length-1),s));return g;}
function ridge(c,w,h,base,amp,col,r,n,jag){c.fillStyle=col;c.beginPath();c.moveTo(0,h);c.lineTo(0,base);const st=w/n;
  for(let i=0;i<=n;i++){const x=i*st,y=base-amp*(jag?(i%2?r():r()*.35):(.5+.5*Math.sin(i*1.3+r()*2)))*1;c.lineTo(x,y);}c.lineTo(w,h);c.closePath();c.fill();}
function stars(c,w,h,n,r,maxY){for(let i=0;i<n;i++){c.globalAlpha=.3+r()*.7;c.fillStyle='#fff';const s=r()<.08?2.2:1.1;c.fillRect(r()*w,r()*h*maxY,s,s);}c.globalAlpha=1;}
function pitch(c,x,y,s,surf,line){c.save();c.translate(x,y);c.fillStyle=surf;c.beginPath();c.moveTo(-s*.7,0);c.lineTo(s*.7,0);c.lineTo(s,s*.42);c.lineTo(-s,s*.42);c.closePath();c.fill();
  c.strokeStyle=line;c.lineWidth=Math.max(1,s*.02);c.stroke();c.beginPath();c.moveTo(0,0);c.lineTo(0,s*.42);c.stroke();c.beginPath();c.ellipse(0,s*.21,s*.12,s*.06,0,0,7);c.stroke();
  c.lineWidth=Math.max(1.5,s*.03);c.strokeStyle='#fff';[-1,1].forEach(d=>{c.beginPath();c.moveTo(d*s*.78,s*.12);c.lineTo(d*s*.78,s*.02);c.lineTo(d*s*.86,s*.02);c.lineTo(d*s*.86,s*.3);c.stroke();});c.restore();}
function paint(z,w,h){
  const cv=document.createElement('canvas');cv.width=w;cv.height=h;const c=cv.getContext('2d');const r=rng(97+z*131);const M=Math.min(w,h);
  if(z===0){c.fillStyle=lin(c,0,h*.66,['#040b1f','#0b2c4f','#2f7aa0']);c.fillRect(0,0,w,h);stars(c,w,h,160,r,.5);
    c.globalCompositeOperation='lighter';for(let k=0;k<3;k++){const y0=h*(.12+k*.07);const g=c.createLinearGradient(0,y0-h*.08,0,y0+h*.12);g.addColorStop(0,'rgba(60,255,170,0)');g.addColorStop(.5,k===1?'rgba(120,120,255,.28)':'rgba(60,255,170,.32)');g.addColorStop(1,'rgba(60,255,170,0)');c.fillStyle=g;
      c.beginPath();c.moveTo(0,y0);for(let x=0;x<=w;x+=w/24)c.lineTo(x,y0+Math.sin(x/w*7+k*2)*h*.05);for(let x=w;x>=0;x-=w/24)c.lineTo(x,y0+h*.12+Math.sin(x/w*6+k)*h*.04);c.fill();}c.globalCompositeOperation='source-over';
    ridge(c,w,h,h*.6,h*.2,lin(c,h*.38,h*.62,['#f2fbff','#8fb9d6']),r,Math.round(w/60),true);
    ridge(c,w,h,h*.68,h*.08,lin(c,h*.58,h*.7,['#e3f4ff','#9cc6e0']),r,Math.round(w/45),true);
    c.fillStyle=lin(c,h*.68,h,['#dff3ff','#a8d2ec','#7fb3d6']);c.fillRect(0,h*.68,w,h);
    c.strokeStyle='rgba(120,180,220,.6)';c.lineWidth=1.2;for(let i=0;i<18;i++){let x=r()*w,y=h*(.72+r()*.26);c.beginPath();c.moveTo(x,y);for(let j=0;j<4;j++){x+=(r()-.5)*M*.12;y+=(r()-.3)*M*.03;c.lineTo(x,y);}c.stroke();}
    for(let i=0;i<3;i++){const x=w*(.15+i*.33+r()*.1),y=h*.72,s=M*.05;c.fillStyle='#f4fbff';c.beginPath();c.arc(x,y,s,Math.PI,0);c.fill();c.fillStyle='#355a77';c.beginPath();c.arc(x+s*.45,y,s*.3,Math.PI,0);c.fill();}
    pitch(c,w*.82,h*.73,M*.16,'rgba(190,235,255,.9)','rgba(80,150,200,.9)');
    c.fillStyle='#fff';for(let i=0;i<140;i++){c.globalAlpha=.4+r()*.5;c.beginPath();c.arc(r()*w,r()*h,r()*1.8+.4,0,7);c.fill();}c.globalAlpha=1;}
  if(z===1){c.fillStyle=lin(c,0,h*.66,['#25124a','#9a2f3a','#f07a2a','#ffc27a']);c.fillRect(0,0,w,h);
    const sx=w*.68,sy=h*.56,sr=M*.13;let g=c.createRadialGradient(sx,sy,sr*.2,sx,sy,sr*3);g.addColorStop(0,'rgba(255,230,150,.9)');g.addColorStop(.3,'rgba(255,170,80,.35)');g.addColorStop(1,'rgba(255,120,60,0)');c.fillStyle=g;c.fillRect(0,0,w,h);
    c.fillStyle='#ffe2a0';c.beginPath();c.arc(sx,sy,sr,0,7);c.fill();
    c.fillStyle='#6a2412';for(let i=0;i<4;i++){const x=r()*w,ww=M*(.2+r()*.3),hh=h*(.06+r()*.06);c.beginPath();c.moveTo(x,h*.64);c.lineTo(x+ww*.15,h*.64-hh);c.lineTo(x+ww*.85,h*.64-hh);c.lineTo(x+ww,h*.64);c.fill();}
    g=c.createLinearGradient(0,h*.46,0,h*.66);g.addColorStop(0,'#d2552a');g.addColorStop(1,'#7a2510');c.fillStyle=g;const ux=w*.28,uw=M*.6;c.beginPath();c.moveTo(ux-uw*.5,h*.65);c.bezierCurveTo(ux-uw*.45,h*.5,ux-uw*.25,h*.47,ux,h*.47);c.bezierCurveTo(ux+uw*.3,h*.47,ux+uw*.45,h*.5,ux+uw*.5,h*.65);c.fill();
    c.strokeStyle='rgba(90,20,5,.45)';c.lineWidth=2;for(let i=1;i<6;i++){c.beginPath();c.moveTo(ux-uw*.5+i*uw/6,h*.49);c.quadraticCurveTo(ux-uw*.5+i*uw/6+5,h*.57,ux-uw*.5+i*uw/6,h*.65);c.stroke();}
    c.fillStyle=lin(c,h*.64,h,['#e0743a','#b8471d','#7e2b10']);c.fillRect(0,h*.64,w,h);
    for(let i=0;i<70;i++){c.fillStyle=r()<.5?'#5f6b2a':'#7a7d34';c.beginPath();c.ellipse(r()*w,h*(.66+r()*.34),M*.012+r()*M*.02,M*.008+r()*M*.01,0,0,7);c.fill();}
    for(let i=0;i<5;i++){const x=r()*w,y=h*(.62+r()*.06),s=M*(.05+r()*.04);c.strokeStyle='#3a2416';c.lineWidth=s*.12;c.beginPath();c.moveTo(x,y+s);c.quadraticCurveTo(x+s*.2,y+s*.3,x,y-s*.2);c.stroke();c.fillStyle='#3b4a22';for(let j=0;j<4;j++){c.beginPath();c.ellipse(x+(r()-.5)*s,y-s*.3+(r()-.5)*s*.3,s*.45,s*.22,0,0,7);c.fill();}}
    pitch(c,w*.8,h*.7,M*.17,'#c9873f','rgba(255,240,210,.85)');}
  if(z===2){c.fillStyle=lin(c,0,h*.7,['#07031a','#2a0c4f','#7a1a8c','#d9468f']);c.fillRect(0,0,w,h);stars(c,w,h,60,r,.3);
    c.globalCompositeOperation='lighter';[[.25,-.25],[.7,.2]].forEach(([x,a])=>{c.save();c.translate(w*x,h*.62);c.rotate(a);const g=c.createLinearGradient(0,0,0,-h*.7);g.addColorStop(0,'rgba(200,220,255,.35)');g.addColorStop(1,'rgba(200,220,255,0)');c.fillStyle=g;c.beginPath();c.moveTo(-M*.02,0);c.lineTo(-M*.12,-h*.7);c.lineTo(M*.12,-h*.7);c.lineTo(M*.02,0);c.fill();c.restore();});c.globalCompositeOperation='source-over';
    [['#251a55',.42,.5,.3],['#170f3c',.5,.38,.6],['#0c0828',.6,.3,.9]].forEach(([col,top,var_,lit])=>{let x=0;while(x<w){const bw=M*(.06+r()*.1),bh=h*(top*.35+r()*var_*.45);const y=h*.72-bh;c.fillStyle=col;c.fillRect(x,y,bw,bh+2);
      if(r()<.3){c.fillRect(x+bw*.45,y-h*.05,2,h*.05);}
      for(let wy=y+6;wy<h*.7;wy+=9)for(let wx=x+4;wx<x+bw-5;wx+=8)if(r()<lit*.35){c.fillStyle=r()<.8?'rgba(255,214,120,.85)':'rgba(120,240,255,.85)';c.fillRect(wx,wy,3,4);}
      if(r()<.2){c.fillStyle=r()<.5?'#ff3d9a':'#3cf0ff';c.shadowColor=c.fillStyle;c.shadowBlur=12;c.fillRect(x+bw*.15,y+h*.05,bw*.7,4);c.shadowBlur=0;}x+=bw+2;}});
    c.fillStyle=lin(c,h*.72,h,['#1d2235','#0f1322']);c.fillRect(0,h*.72,w,h);
    c.fillStyle='rgba(255,255,255,.06)';for(let i=0;i<12;i++)c.fillRect(r()*w,h*(.74+r()*.24),M*(.08+r()*.15),2);
    pitch(c,w*.78,h*.76,M*.17,'#2f8a4a','rgba(255,255,255,.85)');
    c.strokeStyle='#ffd24a';c.lineWidth=3;c.beginPath();c.arc(w*.2,h*.85,M*.06,0,7);c.stroke();c.fillStyle='#ffd24a';c.font='bold '+Math.round(M*.07)+'px sans-serif';c.textAlign='center';c.textBaseline='middle';c.fillText('H',w*.2,h*.852);}
  if(z===3){c.fillStyle=lin(c,0,h*.7,['#0d2a2a','#2e6a4a','#a9c77a']);c.fillRect(0,0,w,h);
    const vx=w*.66,vy=h*.3,vw=M*.5;c.fillStyle='#3a2c2c';c.beginPath();c.moveTo(vx-vw,h*.62);c.lineTo(vx-vw*.14,vy);c.lineTo(vx+vw*.14,vy);c.lineTo(vx+vw,h*.62);c.fill();
    let g=c.createRadialGradient(vx,vy,2,vx,vy,M*.2);g.addColorStop(0,'rgba(255,140,40,.95)');g.addColorStop(1,'rgba(255,80,20,0)');c.fillStyle=g;c.fillRect(vx-M*.3,vy-M*.3,M*.6,M*.6);
    c.strokeStyle='#ff6a1a';c.lineWidth=3;for(let i=0;i<3;i++){c.beginPath();c.moveTo(vx+(i-1)*vw*.08,vy+2);c.quadraticCurveTo(vx+(i-1)*vw*.3,h*.42,vx+(i-1)*vw*.4,h*.5);c.stroke();}
    for(let i=0;i<10;i++){c.fillStyle='rgba(200,200,190,'+(.15+r()*.2)+')';c.beginPath();c.arc(vx+(r()-.3)*M*.3,vy-M*(.05+i*.04),M*(.04+i*.01),0,7);c.fill();}
    [['#2b6a3c',.6,.07],['#1a5230',.7,.08],['#0d3b20',.8,.09]].forEach(([col,b,s])=>{c.fillStyle=col;for(let x=-20;x<w+40;x+=M*s*1.1){c.beginPath();c.arc(x,h*b+r()*h*.03,M*s*(.8+r()*.6),0,7);c.fill();}c.fillRect(0,h*b,w,h);});
    for(let i=0;i<5;i++){const x=r()*w,y=h*(.72+r()*.08),s=M*(.12+r()*.06);c.strokeStyle='#08250f';c.lineWidth=s*.07;c.beginPath();c.moveTo(x,y);c.quadraticCurveTo(x+s*.15,y-s*.6,x+s*.05,y-s);c.stroke();
      c.fillStyle='#0a3016';for(let a=0;a<6;a++){const an=-Math.PI+a*Math.PI/5;c.beginPath();c.ellipse(x+s*.05+Math.cos(an)*s*.3,y-s+Math.sin(an)*s*.12+s*.05,s*.32,s*.07,an,0,7);c.fill();}}
    c.fillStyle=lin(c,h*.82,h,['#3d6b1d','#284d12']);c.fillRect(0,h*.84,w,h);
    pitch(c,w*.8,h*.8,M*.16,'#5aa83a','rgba(255,255,255,.85)');
    c.strokeStyle='rgba(20,60,30,.9)';c.lineWidth=2;for(let i=0;i<8;i++){const x=r()*w;c.beginPath();c.moveTo(x,0);c.quadraticCurveTo(x+10,h*.1,x-4,h*(.1+r()*.15));c.stroke();}}
  if(z===4){c.fillStyle=lin(c,0,h,['#6fe8f5','#0f8aa8','#0a4a6e','#062a44']);c.fillRect(0,0,w,h);
    c.globalCompositeOperation='lighter';for(let i=0;i<7;i++){const x=r()*w;c.fillStyle='rgba(255,255,255,.07)';c.beginPath();c.moveTo(x,0);c.lineTo(x+M*.08,0);c.lineTo(x+M*.3,h*.85);c.lineTo(x+M*.12,h*.85);c.fill();}c.globalCompositeOperation='source-over';
    c.fillStyle='rgba(20,90,110,.85)';for(let i=0;i<4;i++){const x=w*(.1+i*.24),aw=M*.13,ah=h*.22,y=h*.66;c.beginPath();c.moveTo(x-aw,y);c.lineTo(x-aw,y-ah);c.arc(x,y-ah,aw,Math.PI,0);c.lineTo(x+aw,y);c.lineTo(x+aw*.7,y);c.lineTo(x+aw*.7,y-ah);c.arc(x,y-ah,aw*.7,0,Math.PI,true);c.lineTo(x-aw*.7,y);c.fill();}
    c.fillStyle=lin(c,h*.72,h,['#d9bf86','#a0855a']);c.beginPath();c.moveTo(0,h*.76);for(let x=0;x<=w;x+=w/12)c.lineTo(x,h*.74+Math.sin(x*.02)*h*.02);c.lineTo(w,h);c.lineTo(0,h);c.fill();
    ['#f472b6','#fb923c','#a78bfa','#facc15','#34d399'].forEach(col=>{for(let i=0;i<4;i++){const x=r()*w,y=h*(.74+r()*.12);c.fillStyle=col;for(let j=0;j<5;j++){c.beginPath();c.arc(x+(r()-.5)*M*.07,y-r()*M*.06,M*(.012+r()*.018),0,7);c.fill();}}});
    c.strokeStyle='#1f8a5a';c.lineWidth=3;for(let i=0;i<10;i++){const x=r()*w;c.beginPath();c.moveTo(x,h*.8);for(let j=1;j<6;j++)c.lineTo(x+Math.sin(j)*6,h*.8-j*h*.03);c.stroke();}
    pitch(c,w*.8,h*.77,M*.16,'rgba(90,200,170,.85)','rgba(255,255,255,.8)');
    c.strokeStyle='rgba(255,255,255,.55)';c.lineWidth=1.2;for(let i=0;i<40;i++){c.beginPath();c.arc(r()*w,r()*h*.8,r()*4+1,0,7);c.stroke();}
    for(let i=0;i<8;i++){const x=r()*w,y=h*(.2+r()*.4),s=M*.018;c.fillStyle=r()<.5?'#ffd166':'#ff8fab';c.beginPath();c.ellipse(x,y,s*1.6,s,0,0,7);c.fill();c.beginPath();c.moveTo(x-s*1.4,y);c.lineTo(x-s*2.6,y-s);c.lineTo(x-s*2.6,y+s);c.fill();}}
  if(z===5){c.fillStyle='#04030c';c.fillRect(0,0,w,h);c.globalCompositeOperation='lighter';[[.25,.3,'rgba(140,60,220,.35)'],[.7,.2,'rgba(40,160,220,.28)'],[.5,.5,'rgba(220,60,160,.18)']].forEach(([x,y,col])=>{const g=c.createRadialGradient(w*x,h*y,0,w*x,h*y,M*.7);g.addColorStop(0,col);g.addColorStop(1,'rgba(0,0,0,0)');c.fillStyle=g;c.fillRect(0,0,w,h);});c.globalCompositeOperation='source-over';
    stars(c,w,h,300,r,.75);
    const px=w*.76,py=h*.24,pr=M*.13;let g=c.createRadialGradient(px-pr*.4,py-pr*.4,pr*.1,px,py,pr);g.addColorStop(0,'#ffd8a8');g.addColorStop(1,'#a8552a');c.fillStyle=g;c.beginPath();c.arc(px,py,pr,0,7);c.fill();
    c.strokeStyle='rgba(255,220,170,.7)';c.lineWidth=M*.012;c.beginPath();c.ellipse(px,py,pr*1.8,pr*.45,-.3,0,7);c.stroke();
    g=c.createRadialGradient(w*.16,h*.2,1,w*.16,h*.2,M*.05);g.addColorStop(0,'#7ec8ff');g.addColorStop(1,'#1e4fa0');c.fillStyle=g;c.beginPath();c.arc(w*.16,h*.2,M*.045,0,7);c.fill();
    c.fillStyle=lin(c,h*.68,h,['#9aa0ab','#5b6070','#2f3340']);c.beginPath();c.moveTo(0,h);c.lineTo(0,h*.74);c.quadraticCurveTo(w*.5,h*.62,w,h*.74);c.lineTo(w,h);c.fill();
    for(let i=0;i<14;i++){const x=r()*w,y=h*(.76+r()*.22),s=M*(.015+r()*.04);c.fillStyle='rgba(40,44,55,.6)';c.beginPath();c.ellipse(x,y,s,s*.35,0,0,7);c.fill();c.strokeStyle='rgba(200,205,215,.4)';c.lineWidth=1;c.beginPath();c.ellipse(x,y-1,s,s*.35,0,Math.PI,0);c.stroke();}
    const dx=w*.8,dy=h*.74,dr=M*.17;g=c.createRadialGradient(dx,dy,dr*.2,dx,dy,dr);g.addColorStop(0,'rgba(182,255,58,.35)');g.addColorStop(1,'rgba(182,255,58,.08)');c.fillStyle=g;c.beginPath();c.ellipse(dx,dy,dr,dr*.7,0,Math.PI,0);c.fill();
    c.strokeStyle='rgba(182,255,58,.9)';c.lineWidth=2;c.shadowColor='#b6ff3a';c.shadowBlur=14;c.beginPath();c.ellipse(dx,dy,dr,dr*.7,0,Math.PI,0);c.stroke();for(let i=1;i<4;i++){c.beginPath();c.ellipse(dx,dy,dr*i/4,dr*.7,0,Math.PI,0);c.stroke();}c.shadowBlur=0;
    c.fillStyle='#4a4f60';c.fillRect(dx-dr*1.05,dy-2,dr*2.1,6);}
  return cv;}
window.careerPaint=paint;
})();
