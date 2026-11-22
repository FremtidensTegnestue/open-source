window.bogserie = (() => {
  const sheets = [];
  const text = el => el?.textContent.trim() || '';
  const markup = el => el?.outerHTML || '';
  const figures = selector => [...selector.querySelectorAll('figure')].map(markup);
  const title = el => '<h2>' + el + '</h2>';
  function page(kind, id, label, html) {
    const n = sheets.length + 1;
    const el = document.createElement('section');
    el.className = 'sheet ' + kind;
    if (id) el.id = id;
    el.innerHTML = '<main>' + html + '</main>' +
      '<footer><span>' + label + '</span><b>' + n + '</b></footer>';
    sheets.push(el);
    return el;
  }
  const label = t => '<div class="eyebrow">' + t + '</div>';
  const series = 'Fremtidens Tegnestue';
  function front(headline, subtitle, motif) {
    return page('cover', '', '', label(series) + '<h1>' + headline + '</h1>' +
      '<div class="coverart">' + motif + '</div><div class="subtitle"><a href="#indhold">' + subtitle + '</a></div>');
  }
  function back(blurb, motif) {
    return page('back', '', '', label(series) + '<div class="backtext">' + blurb + '</div><div class="backart">'+motif+'</div>');
  }
  return {sheets,page,front,back,text,markup,figures,title,label,series};
})();
