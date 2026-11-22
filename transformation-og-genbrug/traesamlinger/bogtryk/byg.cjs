// Run from traesamlinger with playwright-core installed and CHROMIUM pointing to Chromium.
const { chromium } = require('playwright-core');
const fs = require('node:fs/promises');
const { pathToFileURL } = require('node:url');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const os = require('node:os');

const fonts = [
  ['Lora', 400, 'lora/v37/0QI6MX1D_JOuGQbT0gvTJPa787weuyJG.ttf'],
  ['Lora', 600, 'lora/v37/0QI6MX1D_JOuGQbT0gvTJPa787zAvCJG.ttf'],
  ['Playfair Display', 600, 'playfairdisplay/v40/nuFvD-vYSZviVYUb_rj3ij__anPXJzDwcbmjWBN2PKebukDQ.ttf'],
];
async function build() {
  const faces = await Promise.all(fonts.map(async ([family, weight, file]) => {
    const res = await fetch('https://fonts.gstatic.com/s/' + file);
    if (!res.ok) throw Error('Font download failed: ' + file);
    const data = Buffer.from(await res.arrayBuffer()).toString('base64');
    return `@font-face{font-family:"${family}";font-weight:${weight};src:url(data:font/ttf;base64,${data})}`;
  }));
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'ft-bog-'));
  const browser = await chromium.launch({executablePath:process.env.CHROMIUM, headless:true, args:['--no-sandbox']});
  try {
    for (const lang of ['danske','japanske']) {
      const page = await browser.newPage();
      await page.goto(pathToFileURL(path.resolve(lang, 'bog.html')).href);
      await page.evaluate(() => document.querySelectorAll('style').forEach(el => el.remove()));
      for (const name of ['pdfcn.css','bog.css']) await page.addStyleTag({path:path.join('bogtryk', name)});
      await page.addStyleTag({content:faces.join('\n')});
      await page.evaluate(qr => window.bookQR = qr, await fs.readFile('bogtryk/'+lang+'-qr.svg','utf8'));
      await page.addScriptTag({path:'bogtryk/opslag.js'});
      await page.evaluate(() => document.fonts.ready);
      const overflow = await page.evaluate(() => [...document.querySelectorAll('main')].flatMap((m,i) => {
        const rect = m.getBoundingClientRect();
        return [...m.querySelectorAll('*:not(svg):not(svg *)')].some(el => {
          const r = el.getBoundingClientRect();
          return r.right > rect.right+1 || r.bottom > rect.bottom+1;
        }) ? [i+1] : [];
      }));
      if (overflow.length) throw Error(lang+' overflows on '+overflow.join(', '));
      const pdf = path.join(tmp,lang+'.pdf');
      await page.pdf({path:pdf,printBackground:true,preferCSSPageSize:true,tagged:true,outline:true});
      execFileSync('python3',['bogtryk/beskaer.py',pdf,lang]);
      await page.close();
    }
  } finally {
    await browser.close();
    await fs.rm(tmp,{recursive:true,force:true});
  }
}
build().catch(err => {console.error(err);process.exitCode=1});
