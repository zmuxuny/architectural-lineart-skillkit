'use strict';
(()=>{
const $=id=>document.getElementById(id);
const W=3840,H=2160,PW=1440,PH=810;
const state={color:'#aeb0b2',intensity:1.15,detail:1.65,bg:'white'};
const PRESETS={
 whiteGray:{color:'#aeb0b2',intensity:1.15,detail:1.65,bg:'white'},
 gentleGray:{color:'#929ba4',intensity:2.8,detail:.9,bg:'white'},
 charcoal:{color:'#454b55',intensity:3.9,detail:1.12,bg:'white'},
 blueGray:{color:'#61778a',intensity:3.2,detail:1,bg:'white'},
 blackFine:{color:'#b4bdc5',intensity:1.5,detail:1.02,bg:'black'},
 original:{color:'#ffffff',intensity:1,detail:1,bg:'black'}
};
let sourceImage=null,svgSource=null,svgCached=null,sourceName='内置精细线稿',renderQueued=false,zoom=1;
let previewSource=null;
function msg(s,error){$('statusText').textContent=s;$('statusDot').className='dot'+(error?' err':'');}
function clamp(n,a,b){return Math.max(a,Math.min(b,n));}
function hexNorm(s){s=String(s).trim();if(/^#[0-9a-fA-F]{6}$/.test(s))return s.toLowerCase();if(/^[0-9a-fA-F]{6}$/.test(s))return '#'+s.toLowerCase();if(/^#[0-9a-fA-F]{3}$/.test(s))return '#'+s.slice(1).split('').map(x=>x+x).join('').toLowerCase();return null;}
function colorRgb(h){return [parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16)];}
function updateBg(){const b=$('artboard');b.classList.toggle('checker',state.bg==='transparent');b.style.backgroundColor=state.bg==='black'?'#000':state.bg==='white'?'#fff':'';$('bgLabel').textContent=state.bg==='white'?'白色':state.bg==='black'?'黑色':'透明';document.querySelectorAll('[data-bg]').forEach(x=>x.classList.toggle('active',x.dataset.bg===state.bg));}
function repaint(){renderQueued=false;if(!previewSource)return;const [r,g,b]=colorRgb(state.color),old=previewSource.data;
 let out=new Uint8ClampedArray(old.length);
 for(let i=0;i<old.length;i+=4){const oa=old[i+3];if(oa===0)continue;out[i]=r;out[i+1]=g;out[i+2]=b;out[i+3]=Math.round(255*clamp(Math.pow(oa/255,state.detail)*state.intensity,0,1));}
 $('previewCanvas').getContext('2d').putImageData(new ImageData(out,PW,PH),0,0);
}
function queueRepaint(){if(renderQueued||!previewSource)return;renderQueued=true;requestAnimationFrame(repaint);}
function apply(){updateBg();$('color').value=state.color;$('hex').value=state.color.toUpperCase();$('hexReadout').textContent=state.color.toUpperCase();$('intensity').value=String(state.intensity);$('intensityReadout').textContent=state.intensity.toFixed(2)+'×';$('detail').value=String(state.detail);$('detailReadout').textContent=state.detail<.9?'细节丰富':state.detail>1.1?'主线突出':'平衡';queueRepaint();}
function setPreset(key){Object.assign(state,PRESETS[key]);document.querySelectorAll('[data-preset]').forEach(x=>x.classList.toggle('active',x.dataset.preset===key));apply();msg('已应用配色。可继续微调线条颜色与可见度。');}
function markCustom(){document.querySelectorAll('[data-preset]').forEach(x=>x.classList.remove('active'));}
async function loadEmbedded(){try{
  const b64=$('embeddedPng').textContent.trim();const im=new Image();await new Promise((res,rej)=>{im.onload=res;im.onerror=()=>rej(new Error('无法读取内置线稿 PNG'));im.src='data:image/png;base64,'+b64;});
  loadImage(im,'__ARTWORK_TITLE__');
 }catch(e){msg('内置图片载入失败：'+e.message,true);$('loading').textContent='载入失败，可通过“载入其他 SVG”选择原始文件。';}
}
function loadImage(im,name){sourceImage=im;sourceName=name;
 const c=document.createElement('canvas');c.width=PW;c.height=PH;const ctx=c.getContext('2d',{willReadFrequently:true});ctx.clearRect(0,0,PW,PH);ctx.drawImage(im,0,0,PW,PH);previewSource=ctx.getImageData(0,0,PW,PH);
 $('svgHolder').innerHTML='<canvas id="previewCanvas" width="1440" height="810" role="img" aria-label="实时调色的建筑线稿"></canvas>';
 $('loading').style.display='none';$('sourceNote').textContent='已载入：'+sourceName;$('svgStats').textContent='4K 原画预览 · SVG 真正矢量导出';apply();msg('准备就绪。请选择配色并导出。');
}
function safeParseSvg(text){let parsed=new DOMParser().parseFromString(text,'image/svg+xml');if(parsed.querySelector('parsererror'))throw Error('SVG 内容无法解析');let svg=parsed.documentElement;if(svg.localName!=='svg')throw Error('不是有效 SVG');
 svg.querySelectorAll('script,style,foreignObject,image,iframe,object,embed,animate,animateMotion,animateTransform,set,filter,feImage,audio,video').forEach(el=>el.remove());
 for(const el of [svg,...svg.querySelectorAll('*')])for(const a of Array.from(el.attributes||[])){
 const k=a.name.toLowerCase(),v=a.value;
 if(k.startsWith('on')||((k==='href'||k==='xlink:href')&&!v.startsWith('#'))||((k==='style'||k==='filter'||k==='fill'||k==='stroke')&&/url\s*\(/i.test(v))) el.removeAttribute(a.name);
 }
 svg.setAttribute('xmlns','http://www.w3.org/2000/svg');return svg;
}
async function loadCustomSVG(file){try{
 msg('正在处理所选 SVG…');if(file.size>35*1024*1024)throw Error('SVG 超过 35MB，请精简图层后导入');let text=await file.text();let parsed=safeParseSvg(text);
 const code=new XMLSerializer().serializeToString(parsed);const url=URL.createObjectURL(new Blob([code],{type:'image/svg+xml'}));
 const im=new Image();try{await new Promise((resolve,reject)=>{im.onload=resolve;im.onerror=()=>reject(Error('无法将 SVG 渲染为预览'));im.src=url;});}
 finally{URL.revokeObjectURL(url)}
 svgSource=text;svgCached=null;loadImage(im,file.name);msg('已载入自定义 SVG。');
 }catch(e){msg('自定义 SVG 导入失败：'+e.message,true);window.alert(e.message);}}
async function getRawSvg(){if(svgSource!==null)return svgSource;if(svgCached!==null)return svgCached;
 if(!('DecompressionStream' in window))throw Error('浏览器缺少 SVG 解压功能，请升级 Chrome/Edge，或载入自己的 SVG 文件。');
 const encoded=$('embeddedSvg').textContent.trim();const bytes=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0));
 const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
 svgCached=await new Response(stream).text();return svgCached;
}
async function exportSVG(withBg){const text=await getRawSvg();const svg=safeParseSvg(text);
 for(const el of svg.querySelectorAll('path,rect,line,polyline,polygon,circle,ellipse,text')){
  let fill=el.getAttribute('fill'),stroke=el.getAttribute('stroke');
  if(fill!=='none'&&(fill!==null||(stroke===null&&el.localName!=='line')))el.setAttribute('fill',state.color);
  if(stroke!==null&&stroke!=='none')el.setAttribute('stroke',state.color);
  const op=parseFloat(el.getAttribute('opacity')||'1');el.setAttribute('opacity',clamp(Math.pow(op,state.detail)*state.intensity,0,1).toFixed(5));
 }
 svg.setAttribute('width',String(W));svg.setAttribute('height',String(H));
 if(withBg&&state.bg!=='transparent'){
  const vals=(svg.getAttribute('viewBox')||`0 0 ${W} ${H}`).split(/[ ,]+/).map(Number);
  const n=svg.ownerDocument.createElementNS('http://www.w3.org/2000/svg','rect');
  n.setAttribute('x',String(vals[0]));n.setAttribute('y',String(vals[1]));n.setAttribute('width',String(vals[2]));n.setAttribute('height',String(vals[3]));n.setAttribute('fill',state.bg==='black'?'#000000':'#ffffff');n.setAttribute('data-background','true');
  svg.insertBefore(n,svg.firstChild);
 }
 return '<?xml version="1.0" encoding="UTF-8"?>\n'+new XMLSerializer().serializeToString(svg);
}
function filename(ext,withBg){const clr=state.color.slice(1).toUpperCase(),b=withBg&&state.bg!=='transparent'?state.bg==='black'?'黑底':'白底':'透明底';return `__FILE_STEM___${clr}_${b}_3840x2160.${ext}`;}
function download(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),15000);}
async function exportPNG(withBg){if(!sourceImage)throw Error('图形尚未载入');const scratch=document.createElement('canvas');scratch.width=W;scratch.height=H;
 const srcCtx=scratch.getContext('2d',{willReadFrequently:true});srcCtx.drawImage(sourceImage,0,0,W,H);const im=srcCtx.getImageData(0,0,W,H);
 const arr=im.data,[r,g,b]=colorRgb(state.color),strength=state.intensity,pow=state.detail;
 for(let i=0;i<arr.length;i+=4){let alpha=arr[i+3];if(alpha===0)continue;arr[i]=r;arr[i+1]=g;arr[i+2]=b;arr[i+3]=Math.round(255*clamp(Math.pow(alpha/255,pow)*strength,0,1));}
 srcCtx.putImageData(im,0,0);
 let outCanvas=scratch;
 if(withBg&&state.bg!=='transparent'){
  outCanvas=document.createElement('canvas');outCanvas.width=W;outCanvas.height=H;
  const c=outCanvas.getContext('2d',{alpha:false});c.fillStyle=state.bg==='black'?'black':'white';c.fillRect(0,0,W,H);c.drawImage(scratch,0,0);
 }
 const png=await new Promise(resolve=>outCanvas.toBlob(resolve,'image/png'));if(!png)throw Error('无法生成 PNG。');
 download(png,filename('png',withBg));scratch.width=1;scratch.height=1;if(outCanvas!==scratch){outCanvas.width=1;outCanvas.height=1;}
}
let busy=false;
async function doExport(type,bg,button){if(busy)return;busy=true;const old=button.textContent;button.textContent='生成中，请稍候…';document.querySelectorAll('.export').forEach(x=>x.disabled=true);
 try{await new Promise(r=>requestAnimationFrame(r));if(type==='svg'){const svg=await exportSVG(bg);download(new Blob([svg],{type:'image/svg+xml;charset=utf-8'}),filename('svg',bg));msg('已导出真实矢量 SVG（保留建筑路径和色阶）。');}else{await exportPNG(bg);msg('已导出 3840×2160 PNG。');}}
 catch(e){msg('导出失败：'+e.message,true);window.alert('导出失败：'+e.message);}finally{button.textContent=old;busy=false;document.querySelectorAll('.export').forEach(x=>x.disabled=false);}
}
function applyZoom(){zoom=clamp(zoom,.5,3);$('artboard').style.width=(100*zoom)+'%';$('zoomLabel').textContent=Math.round(zoom*100)+'%';}
$('zoomIn').onclick=()=>{zoom+=.25;applyZoom()};$('zoomOut').onclick=()=>{zoom-=.25;applyZoom()};$('zoomFit').onclick=()=>{zoom=1;applyZoom()};
$('openFile').onclick=()=>$('fileInput').click();$('fileInput').onchange=async e=>{const f=e.target.files[0];if(f)await loadCustomSVG(f);e.target.value='';};
$('resetBtn').onclick=()=>setPreset('whiteGray');document.querySelectorAll('[data-preset]').forEach(x=>x.onclick=()=>setPreset(x.dataset.preset));
$('color').oninput=e=>{state.color=e.target.value;markCustom();apply()};
$('hex').onchange=e=>{const val=hexNorm(e.target.value);if(!val){$('hex').value=state.color.toUpperCase();msg('颜色格式应为 #RRGGBB。',true);}else{state.color=val;markCustom();apply();}};
$('intensity').oninput=e=>{state.intensity=Number(e.target.value);markCustom();apply()};
$('detail').oninput=e=>{state.detail=Number(e.target.value);markCustom();apply()};
document.querySelectorAll('[data-bg]').forEach(x=>x.onclick=()=>{state.bg=x.dataset.bg;markCustom();updateBg()});
$('pngTransparent').onclick=e=>doExport('png',false,e.currentTarget);$('pngBackground').onclick=e=>doExport('png',true,e.currentTarget);
$('svgTransparent').onclick=e=>doExport('svg',false,e.currentTarget);$('svgBackground').onclick=e=>doExport('svg',true,e.currentTarget);
window.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='o'){e.preventDefault();$('fileInput').click();}});
updateBg();loadEmbedded();
})();
