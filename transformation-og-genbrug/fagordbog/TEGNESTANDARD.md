# Tegnestandard for den illustrerede fagordbog

## Fremtidens Tegnestues udtryk

Vi bruger den lyse palette og typografi fra [fremtidenstegnestue.dk](https://fremtidenstegnestue.dk/). På fagarkene er baggrunden knækket hvid (#FAFBF9), snitkanter og overskrifter kulfarvede (#20211E), hjælpelinjer grå (#555950) og det fremhævede stof brunligt (#806747). Nummerfelter bruger en mørkere brun (#695437) med hvid skrift. Skriftfamilien er Arial, Helvetica og derefter sans-serif. Behold baggrundsfladen i SVG-filen, så tegningen også er læselig på en mørk skærm.

[Fælles typografi og layout til skærm og udskrift](fagark.css) kan genbruges til det næste ark. Browserudgaven indeholder en kopi af stilarket og tegningen, så arket også virker offline.

## Tegningens grammatik

- Brug samme nummer i tegning, ordliste og PDF. Giv en ny bygningsvariant sit eget bogstav. Angiv ude og inde eller anden nødvendig orientering.
- En fuld snitkant viser materiale. En tynd leder med prik peger på én del. En klamme angiver en udstrækning. En stiplet afgrænsning angiver et område. Murforbandt og skravering skal også kunne skelnes på et sort-hvidt print.
- Markér ét fagligt spørgsmål ad gangen. Kald en principskitse »uden mål«. Ved en opmåling skal kilde, målestok, enhed og måleusikkerhed stå på bladet.
- Skriv en billedbeskrivelse og en nummerliste, der også fungerer uden farver eller mus. Originalerne skal kunne åbnes hos udgiveren.

## Sådan er de første snit bygget og kontrolleret

[Tegneopskriften](cad/tagsnit.json) opbygger to selvstændige profilsnit i SolidCraft. Hver del har en lukket skitse i XZ-planet, eget navn og 100 mm ekstrudering. Dybden og profilernes mål er illustrative. A viser en muret trempel, B en opskalket tagfod. [Åbn den redigerbare SolidCraft-model](cad/tagsnit.sc).

Fra fagordbogens mappe kan du gentage kørslen med SolidCraft CLI 0.45.0:

```sh
solidcraft-cli run cad/tagsnit.json --param-check strict --save /tmp/fagordbog.sc --out /tmp/fagordbog.glb
solidcraft-cli eval /tmp/fagordbog.sc
solidcraft-cli run cad/kollision.json --in /tmp/fagordbog.sc --results
```

SVG'ens materialeflader er ortogonale projektioner af de eksporterede legemer. Tekst, ledelinjer, skravering og nummerfelter ligger ovenpå. Ved ændringer skal CAD-projektionen og PDF'en eksporteres på ny. Kontrollér samtidig, at hver leder stadig ender på den rigtige del.

**Kontrol af den udgivne model.** SolidCraft rapporterede 11 lukkede legemer. Interferenskontrollen fandt 0 overlap og 0 ukontrollerede par. For hvert legeme er projektionsareal gange dybde sammenholdt med CAD-volumen. Alle par er kontrolleret for arealoverlap i snittet. Der er målt fælles kontaktkant ved blandt andet remmens leje på ydermuren, bjælkens leje i muren og skalkens møde med spær og tagflade. Tagfladen bliver fladere ud mod gesimsen. Tagfoden er markeret som et område omkring samlingen.

**Faglig status.** Snittene er sammenholdt med Kochs og Brüels originaler i de [seks opslag](README.md). De viser placering og form i de valgte eksempler. En uafhængig fagpersons gennemgang af snittene udestår. Bæreevne, fastgørelser og fugtteknisk funktion kræver en konkret konstruktion og egne beregninger.
