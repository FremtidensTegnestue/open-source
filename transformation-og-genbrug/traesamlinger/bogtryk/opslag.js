// Executed in the offline book's DOM before printing. Keep links and vector geometry intact.
(() => {
  const sections = [...document.querySelectorAll('section')];
  const cover = sections[0];
  const book = cover.querySelector('h1').textContent;
  const jp = book.startsWith('Japanske');
  const {sheets,page,front,back,text,markup,figures,title,label,series} = window.bogserie;
  const body = sec => [...sec.querySelectorAll(':scope > p:not(.sources)')].map(markup).join('');
  const sources = sec => markup(sec.querySelector('.sources'));
  const art = id => markup(document.getElementById(id).parentElement.querySelector('.grid figure svg'));
  const motif = art(jp ? 'kanawa' : 'fransk');
  front(book.replace(' ', '<br>'), text(cover.querySelector('h2')), motif);
  const toc = page('toc', 'indhold', book, title('Indhold'));
  const intro = sections[2];
  page('essay', '', book, label('Indledning') + title(text(intro.querySelector('h2'))) + body(intro) + sources(intro));
  let family = '', joint = 0;
  for (const sec of sections.slice(3)) {
    const h = sec.querySelector('h2'), id = h.id, name = text(h);
    if (id.startsWith('del-')) {
      family = name;
      const figs = figures(sec.querySelector('.route'));
      page('part', id, book, label('Del ' + ['I','II','III','IV'][Number(id.slice(4))-1]) +
        title(name) + body(sec) + sources(sec));
      page('familyplate', '', family, '<div class="triptych">' + figs.join('') + '</div>');
    } else if (sec.querySelector('.where')) {
      const seq = figures(sec.querySelector('.grid'));
      const idx = String(++joint).padStart(2,'0');
      page('joint', id, family, label('Samling ' + idx) + title(name) +
        '<div class="first">' + markup(sec.querySelector('.where p')) + '</div>' +
        body(sec) + markup(sec.querySelector('.where figure')) + sources(sec));
      page('sequence', '', name, label('Tavle ' + idx) + '<div class="steps count'+seq.length+'">' + seq.join('') + '</div>');
    } else if (id === 'register') {
      page('index', id, book, label('Opslag') + title(name) + markup(sec.querySelector('.contents')) +
        markup(sec.querySelector(':scope > h3')) + body(sec));
    } else {
      const content = [...sec.children].filter(x => !['HEADER','H2'].includes(x.tagName)).map(markup).join('');
      page(id.startsWith('pl-') ? 'study' : id.startsWith('kilder-') ? 'refs' : 'essay', id, book,
        label(id.startsWith('pl-') ? 'Studietavle' : id.startsWith('kilder-') ? 'Bibliografi' : 'Fordybelse') + title(name) + content);
    }
  }
  const digital = 'https://github.com/FremtidensTegnestue/open-source/tree/main/transformation-og-genbrug/traesamlinger/' + (jp?'japanske':'danske');
  // Complete a four-page signature with full-size study details.
  let i = 0;
  const endplates = jp ? ['jigoku','okkake','kanawa'] : ['dobbelt','skraatap','fransk'];
  while ((sheets.length + 2) % 4) {
    const id = endplates[i++], sec = document.getElementById(id).parentElement;
    page('endplate','',book,label('Detalje') + title(text(sec.querySelector('h2'))) + markup(sec.querySelector('.grid figure:last-child')));
  }
  page('colophon','',book,label(series) + title('Om bogen') +
    '<p>Tekster, snittegninger og redigerbare SolidCraft-modeller udgives samlet af Fremtidens Tegnestue. I den digitale udgave kan du følge henvisningerne helt ind på de historiske tavler.</p>' +
    '<div class="qr">'+window.bookQR+'</div><p><a href="'+digital+'">Åbn bogen og modellerne på GitHub</a></p><p class="imprint">Bogformat 170 × 240 mm<br>Sats i Playfair Display og Lora<br>Japanske skrifttegn i Noto Serif CJK JP</p>');
  back(text(cover.querySelector('.lede')), motif);
  const destinations = new Map(sheets.map((s,i)=>[s.id,i+1]));
  const contents = sections[1];
  const rows = [...contents.querySelectorAll('a[href^="#"]')].map(a=>{
    const dest=a.hash.slice(1);
    return '<a class="'+(dest.startsWith('del-')?'major':'')+'" href="'+a.hash+'"><span>'+
      text(a).replace(/^\d+[　 ]+/,'')+'</span><b>'+destinations.get(dest)+'</b></a>';
  });
  const split = rows.findIndex(r=>r.includes('href="#del-3"'));
  toc.querySelector('main').insertAdjacentHTML('beforeend','<div class="toccols"><div>'+rows.slice(0,split).join('')+'</div><div>'+rows.slice(split).join('')+'</div></div>');
  for (const a of sheets.find(p=>p.id==='register').querySelectorAll('.contents a'))
    a.insertAdjacentHTML('beforeend','<b>'+destinations.get(a.hash.slice(1))+'</b>');
  document.body.replaceChildren(...sheets);
  document.documentElement.lang='da';
  document.body.className=jp?'jp':'dk';
})();
