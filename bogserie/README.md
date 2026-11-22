# Fremtidens Tegnestues bogserie

| Bog | Læseudgave | Trykfil |
| --- | --- | --- |
| Byggeriets illustrerede fagordbog · 80 sider | [Læs](../transformation-og-genbrug/fagordbog/fagordbog.pdf?raw=true) | [Tryk](../transformation-og-genbrug/fagordbog/tryk.pdf?raw=true) |
| Danske træsamlinger · 76 sider | [Læs](../transformation-og-genbrug/traesamlinger/danske/bog.pdf?raw=true) | [Tryk](../transformation-og-genbrug/traesamlinger/danske/tryk.pdf?raw=true) |
| Japanske træsamlinger · 64 sider | [Læs](../transformation-og-genbrug/traesamlinger/japanske/bog.pdf?raw=true) | [Tryk](../transformation-og-genbrug/traesamlinger/japanske/tryk.pdf?raw=true) |
| Læs et hus · 36 sider | [Læs](../transformation-og-genbrug/boeger/laes-et-hus/bog.pdf?raw=true) | [Tryk](../transformation-og-genbrug/boeger/laes-et-hus/tryk.pdf?raw=true) |
| Byg videre på huset · 36 sider | [Læs](../transformation-og-genbrug/boeger/byg-videre/bog.pdf?raw=true) | [Tryk](../transformation-og-genbrug/boeger/byg-videre/tryk.pdf?raw=true) |
| Vinduet der blev siddende · 36 sider | [Læs](../transformation-og-genbrug/boeger/vinduet/bog.pdf?raw=true) | [Tryk](../transformation-og-genbrug/boeger/vinduet/tryk.pdf?raw=true) |
| Vandets vej gennem huset · 32 sider | [Læs](../transformation-og-genbrug/boeger/vandets-vej/bog.pdf?raw=true) | [Tryk](../transformation-og-genbrug/boeger/vandets-vej/tryk.pdf?raw=true) |
| En dør får et nyt liv · 32 sider | [Læs](../transformation-og-genbrug/boeger/doerens-liv/bog.pdf?raw=true) | [Tryk](../transformation-og-genbrug/boeger/doerens-liv/tryk.pdf?raw=true) |

Se [hvilket hus og hvilke spørgsmål de fem nye bøger følger](../transformation-og-genbrug/boeger/README.md).

## Sådan hænger bindene sammen

Omslaget bærer tegnestuens navn, bogens titel, én tegning fra bogen og en kort undertitel. Hvert bind har en farve, der går igen i overskrifter og tavler. Fagordbogen er bladgrøn, det danske træbind er kastanjebrunt, og det japanske er blågrønt.

Playfair Display bruges til titler, Lora til læsetekst og Inter til tavlenumre, billedtekster og kilder. Typografien og grundpaletten tager udgangspunkt i pdfcn Elegant. Alle bind bruger den samme sats, de samme omslagsfunktioner og samme udskrift. [Seriens typografi og farver](pdfcn.css) · [Sidernes sats](bog.css) · [Omslag, sidefod og sidetal](serie.js)

Et fagligt opslag har forklaring på venstresiden og en tavle på højresiden. I fagordbogen forbinder tal på tegningen hver bygningsdel med sit navn. I træbøgerne viser en billedfølge, hvordan delene mødes. Brug de redigerede originaltegninger og behold henvisningen til originalkilden ved forklaringen.

De fem fortællende bind bruger en fælles [opslagsskabelon](fagbog.js) med kapitel til venstre og tavle til højre. Tegningerne ledsages af en billedtekst, og kilderne står på samme opslag som den faglige forklaring. På papir kan læseren bruge arbejdsbladene sidst i bogen eller scanne kolofonens QR-kode for at hente modellerne.

## Udgiv et bind

1. Tilføj bogen til [kataloget](boeger.json) med dens kildemappe, HTML-manuskript, navn på læse-PDF og script til opslagene. To bøger med samme indholdsstruktur kan bruge samme script. En bog kan også have sin egen emnefarve og tavlesats i et ekstra stilark.
2. Brug funktionerne i `window.bogserie` til forside, indholdssider og bagside. Sæt den første venstreside på et lige sidetal. Angiv sidetal i det trykte register og klikbare destinationer i skærmudgaven. Slut med et sidetal deleligt med fire, inklusive omslaget.
3. Kør bygningen fra repositoryets rod. Den bruger Node.js med `playwright-core`, Chromium, Python 3 med `pikepdf` samt skrifterne Inter og Noto Serif/Sans CJK JP. De versionsbestemte fontfiler til Playfair Display og Lora hentes ved bygning.

```sh
CHROMIUM=/sti/til/chromium node bogserie/byg.cjs fagordbog
CHROMIUM=/sti/til/chromium node bogserie/byg.cjs
```

Den første kommando bygger fagordbogen. Den anden bygger hele kataloget. Bygningen kontrollerer, at satsen holder sig inden for siden, og skriver to filer fra de samme sider. Læseudgaven beskæres til 170 × 240 mm. Trykfilen leveres i læserækkefølge med 3 mm udfald hele vejen rundt. Se et opslag og omslaget som prøvetryk på det valgte papir. Ved et separat limbundet omslag afhænger rygbredden af papiret og sidetallet.
