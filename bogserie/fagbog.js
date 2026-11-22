// Book-length narratives with a text page facing a single illustrated plate.
(() => {
  const {sheets, page, front, back, text, markup, label, title, series} = window.bogserie;
  const header = document.querySelector('header');
  const book = text(header.querySelector('h1'));
  const intro = document.querySelector('aside.intro');
  const articles = [...document.querySelectorAll('article[id]')];
  const id = location.pathname.split('/').at(-2);
  const digital = 'https://github.com/FremtidensTegnestue/open-source/tree/main/transformation-og-genbrug/boeger/' + id;
  const fieldwork = {
    'laes-et-hus':[
      ['Læs facaden fra gaden','Vælg ét vindue. Skitsér muren ved siden af og under vinduet. Hvilke mål ville vise, om de to steder er bygget ens?','Sted i facaden','Det kan ses fra gaden','Det vil jeg måle inde'],
      ['Tegn det skjulte leje','Tegn et lodret snit ved gulvet ud mod muren. Sæt et lille kryds ved det sted, hvor du ville forvente at finde enden af en bjælke.','Tegn det synlige','Tegn din antagelse','Et fund der kan afgøre det']
    ],
    'byg-videre':[
      ['Hvilken dør bruger I?','Følg en beboers vej fra gangen til det bageste rum. Skriv, hvad der sker ved hver dør, og hvem der er i rummet, når man går igennem.','Ruten i dag','Ruten efter ændringen','Det vil beboeren savne'],
      ['Regn indgrebene efter','Læg prøveplanerne ved siden af hinanden. Tæl åbningerne og skriv særskilt, hvad der sker med karm og blad. Hvilket forslag ville du tage med til en opmåling?','Forslag A','Forslag B','Forslag C']
    ],
    vinduet:[
      ['Et vindue ved næste eftersyn','Giv vinduet et navn, som en kollega kan finde igen fra gården. Skitsér begge rammer. Sæt en ring om det sted, du vil se nærmere på ved næste besøg.','Hus, etage og fag','Det så jeg ved glasset','Det så jeg ved træet og beslaget'],
      ['Følg de to rammer','Se på vinduet fra stuen. Tegn den bane, hver ramme følger, når den åbnes. Hvor kan et greb, en urtepotte eller den anden ramme komme i vejen?','Den ydre rammes vej','Den indre rammes vej','Det skal prøves i åbningen']
    ],
    'vandets-vej':[
      ['Begynd ved pletten','Markér etagen og placér det synlige spor på en skitse. Sæt tidspunkt på observationen. Brug en anden streg til den mulige vej, vandet kan have fulgt.','Sted og tidspunkt','Det synlige spor','Den del af vejen er skjult'],
      ['Hvad skilte sporene ad?','Skriv to mulige forklaringer på samme plet. Hvilket fund ville gøre den ene mere sandsynlig? Lad det stå åbent, hvis begge stadig passer.','Første forklaring','Anden forklaring','Det næste spørgsmål til undersøgeren']
    ],
    'doerens-liv':[
      ['Giv dørbladet en adresse','Markér, fra hvilken side du ser døren. Tegn hængselsiden og falsen. Giv karm og blad samme mærke, når de er et sæt.','Sted og mærke','Blad, fals og hængsler','Delene der følger med'],
      ['Prøv den nye åbning på papir','Sammenlign to døre med samme udvendige bladmål. Læg skitserne af fals, hængsling og karm oven på hinanden. Hvor viser den første forskel sig?','Blad A og karm','Blad B og karm','Prøven der mangler']
    ]
  }[id] || [];
  const images = articles.map(a=>a.querySelector('figure img'));
  const motif = markup(header.querySelector('img') || images[0]);
  front(book, text(header.querySelector('h2')), motif);
  const toc = page('toc','indhold',book,label(series)+title('Indhold'));
  page('essay','indledning',book,label('Indledning')+intro.innerHTML);
  const rows = [];
  const refs = new Map();
  for (const [i,a] of articles.entries()) {
    const h = a.querySelector('h2');
    const fig = a.querySelector('figure');
    const sources = [...a.querySelectorAll('.sources a')];
    if (!fig || !sources.length || !images[i]) throw Error('Manglende tavle eller kilde i '+a.id);
    const folio = sheets.length+1;
    rows.push('<a href="#'+a.id+'"><span>'+text(h)+'</span><b>'+folio+'</b></a>');
    for (const link of sources) {
      const base = link.href.split('#')[0];
      if (!refs.has(base)) {
        const citation = link.cloneNode(true);
        citation.href = base;
        citation.textContent = link.dataset.title || text(link).replace(/\s*·\s*PDF-s\..*$/i,'');
        refs.set(base, {link:citation, pages:[]});
      }
      const entry=refs.get(base);
      if(!entry.pages.includes(folio)) entry.pages.push(folio);
    }
    const paragraphs=[...a.children].filter(el=>el!==h && el!==fig && !el.matches('.sources'));
    page('chapter',a.id,book,label('Kapitel '+String(i+1).padStart(2,'0'))+markup(h)+paragraphs.map(markup).join('')+
      '<div class="sources">'+sources.map(markup).join(' · ')+'</div>');
    const plate = page('faceplate','tavle-'+a.id, text(h),label('Tavle '+String(i+1).padStart(2,'0'))+markup(fig));
    const image = plate.querySelector('img[data-bredde-mm]');
    if (image) {
      const width=Number(image.dataset.breddeMm), height=Number(image.dataset.hoejdeMm);
      if (!(width>0 && width<=130 && height>0 && height<=150)) throw Error('Profilen passer ikke i 1:1');
      image.style.cssText='flex:none;align-self:center;margin:auto;width:'+width+'mm;height:'+height+'mm';
    }
  }
  toc.querySelector('main').insertAdjacentHTML('beforeend','<div class="bookrows">'+rows.join('')+'<a href="#kilder"><span>Kilder og videre læsning</span><b>'+ (sheets.length+1) +'</b></a></div>');
  const list=[...refs.values()];
  for(let i=0;i<list.length;i+=6) {
    const items=list.slice(i,i+6).map(e=>'<p>'+markup(e.link)+'<small>Læs med på side '+e.pages.join(', ')+'</small></p>');
    page('refpage',i?'':'kilder',book,label('Bibliografi')+title('Kilder og videre læsning')+'<div class="bookrefs">'+items.join('')+'</div>');
  }
  // The final signature includes a field exercise when the bibliography leaves a spare leaf.
  for(let i=0;(sheets.length+2)%4;i++){
    const [t,p,...fields]=fieldwork[i] || ['Fra skitse til opmåling','Tag en kopi af din skitse med til bygningen og skriv dine iagttagelser ved den del, de hører til.','Sted og dato','På tegningen','På stedet'];
    page('fieldnote','',book,label('Arbejdsblad')+title(t)+'<p>'+p+'</p>'+
      fields.map(f=>'<div class="notefield"><b>'+f+'</b></div>').join(''));
  }
  page('colophon','',book,label(series)+title('Om bogen')+'<p>Tegningerne, de redigerbare SolidCraft-modeller og kildesporet følger med bogudgaven. På tegnestuens åbne boghylde kan du hente materialet til din egen læsning og undervisning.</p><div class="qr">'+window.bookQR+'</div><p><a href="'+digital+'">Åbn bogens tegninger og kilder</a></p><p class="imprint">Fremtidens Tegnestue · Bogformat 170 × 240 mm<br>Sats i Playfair Display og Lora</p>');
  back(text(header.querySelector('p')),markup(header.querySelector('img')||images.at(-1)));
  document.body.replaceChildren(...sheets);
  document.body.className='fagbog '+id;
})();
