// Turn the linked atlas into facing text and plate pages without redrawing its details.
(() => {
  const {sheets,page,front,back,text,markup,title,label,series} = window.bogserie;
  const book = document.title;
  const chapters = [...document.querySelectorAll('section[id]')];
  const contents = [...document.querySelectorAll('ol li a')];
  const entries = [...document.querySelectorAll('.words a')];
  const folios = new Map();
  const coverArt = document.querySelector('#vindue-snit-0 svg').cloneNode(true);
  coverArt.querySelectorAll('a,defs,:scope > rect').forEach(el=>el.remove());
  const motif = coverArt.outerHTML;
  front('Byggeriets<br>illustrerede<br>fagordbog','Fra husets form til håndværkets ord',motif);
  const toc = page('toc','indhold',book,title('Indhold'));
  page('essay','indledning',book,label('Indledning')+title('Det lille svaj ved tagfoden')+
    '<p class="lede">Stil dig på fortovet og følg tagets linje ned mod muren. Lige inden kanten flader taget ud. Det lille svaj kan du se fra gaden. Men hvad har tømreren lagt under taget for at give det den form?</p>'+
    '<p>På den første tavle er huset skåret igennem. Ved punkt 3 ligger en trækile oven på spæret. Den er tyk ved kanten og bliver tyndere op ad taget. Kilen hedder en skalk. Næste gang du får øje på svajet, har du både ordet og en forestilling om det træ, der ligger gemt.</p>'+
    '<p>Du kan gå begge veje gennem bogen. Begynd med et nummer på en tegning, og læs forklaringen på siden overfor. Eller begynd med et ord i det alfabetiske register, og følg sidetallet tilbage til den del af huset, du leder efter.</p>');
  function spread(topic,heading,plateId,drawing,terms,chapter) {
    const left=sheets.length+1;
    for(const t of terms) folios.set(t.id,left);
    folios.set(plateId,left+1);
    const caption = label('Emneblad '+String(chapter).padStart(2,'0'));
    page('definitions','',topic,caption+title(topic)+terms.map(t=>
      '<article id="'+t.id+'"><h3><a href="#'+plateId+'">'+t.name+'</a></h3>'+t.prose+'<div class="citation">'+t.sources+'</div></article>').join(''));
    page('drawing',plateId,topic,label('Tavle')+title(heading)+'<figure>'+drawing+'</figure>'+
      '<div class="platekey">'+terms.map(t=>'<a href="#'+t.id+'">'+t.name+'</a>').join('')+'</div>');
  }
  const roof = document.querySelector('.front');
  const roofTerms=[...document.querySelectorAll('.terms article')].map(a=>({
    id:a.querySelector('h3').id,name:text(a.querySelector('h3')).replace(/^(\d+)\s+/,'$1 · '),
    prose:markup(a.querySelector('.def p')),sources:a.querySelector('.sources').innerHTML
  }));
  // Two enlarged halves of the source plate. Keep its numbered geometry and link hit areas.
  for (const [i,nums] of [[1,2,6],[3,4,5]].entries()) {
    const img=roof.querySelector('img'), svg=new DOMParser().parseFromString(
      new TextDecoder().decode(Uint8Array.from(atob(img.src.split(',')[1]),c=>c.charCodeAt(0))),'image/svg+xml').documentElement;
    svg.setAttribute('viewBox',(480*i)+' 0 480 480');
    for(const t of svg.querySelectorAll('text')) if (/^[AB] · /.test(t.textContent)) t.remove();
    svg.removeAttribute('width');svg.removeAttribute('height');
    const box='<div class="roofart">'+ '<img alt="'+(i?'Tagets kant':'Muren over gulvet')+'" src="data:image/svg+xml;charset=utf-8,'+encodeURIComponent(new XMLSerializer().serializeToString(svg))+'">'+
      nums.map(n=>{const a=roof.querySelector('.spot[href="#tagfod-ord-'+n+'"]').cloneNode(true);a.style.left=(2*parseFloat(a.style.left)-100*i)+'%';a.style.width='10%';return a.outerHTML}).join('')+'</div>';
    spread(text(roof.querySelector('h1')),i?'B · Tagets kant':'A · Muren over gulvet',i?'tagfod-kant':'tagfod-tegning',box,nums.map(n=>roofTerms[n-1]),1);
  }
  for(const sec of chapters) {
    const topic=text(sec.querySelector('h1'));
    const chapter=contents.findIndex(a=>text(a)===topic)+1;
    if(!chapter) throw Error('Ukendt emneblad '+topic);
    const terms=[...sec.querySelectorAll('p[id]')].map(p=>{
      const clone=p.cloneNode(true);
      const name=text(clone.querySelector('b'));
      const links=[...clone.querySelectorAll('a[href^="http"]')].map(markup);
      clone.querySelectorAll('a').forEach(a=>a.remove());
      return {id:p.id,name,prose:'<p>'+clone.innerHTML.trim()+'</p>',sources:links.join(' · ')};
    });
    spread(topic,text(sec.querySelector('h2')),sec.id,markup(sec.querySelector('svg')),terms,chapter);
  }
  const row=(id,name)=>'<a href="#'+id+'"><span>'+name+'</span><b>'+folios.get(id)+'</b></a>';
  folios.set('register',sheets.length+1);
  toc.querySelector('main').insertAdjacentHTML('beforeend','<div class="catalogrows">'+contents.map(a=>row(a.hash.slice(1),text(a))).join('')+row('register','Alfabetisk register')+'</div>');
  const perPage=Math.ceil(entries.length/3);
  for(let i=0;i<entries.length;i+=perPage){
    const slice=entries.slice(i,i+perPage);
    page('wordindex',i?'':'register',book,label('Alfabetisk register')+title(text(slice[0])+' – '+text(slice.at(-1)))+
      '<div class="indexcols">'+slice.map(a=>row(a.hash.slice(1),a.parentNode.textContent.trim())).join('')+'</div>');
  }
  page('colophon','',book,label(series)+title('Om bogen')+
    '<p>'+text(document.querySelector('section.index > p:last-child'))+'</p><div class="qr">'+window.bookQR+'</div><p><a href="'+roof.querySelector('footer a').href+'">Åbn fagordbogen og de redigerbare tegninger på GitHub</a></p><p class="imprint">Bogformat 170 × 240 mm<br>Sats i Playfair Display og Lora</p>');
  back('En mursten springer frem, et vindue deles af en sprosse, og ved tagfoden ligger en skalk. Hvad kan du få øje på, næste gang du går forbi et hus?',motif);
  document.body.replaceChildren(...sheets);
  document.body.className='ordbog';
})();
