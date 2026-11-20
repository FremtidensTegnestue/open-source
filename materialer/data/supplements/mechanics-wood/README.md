# Træets stivhed, krybning og udmattelse samt træbaserede pladers og bjælkers egenskaber

Udgaven indeholder 874 feltværdier om 143 arts-, prøve- og produktposter. 729 værdier er oplyst i de to amerikanske håndbogskapitler, og 145 er beregnede skøn. 841 værdier er skalarer og findes også i observationsstrømmen. 33 dokumenterede intervaller ligger i feltstrømmen med både nedre og øvre grænse. Hver feltværdi angiver original, fysisk PDF-side, tabel eller afsnit, række og egenskab. Tallene beskriver de nævnte prøver eller grupper. Dansk styrkeklasse, dimensioneringsværdi og det enkelte element kræver yderligere dokumentation.

## Massivt træ

USDA Forest Products Laboratory offentliggjorde de udvalgte tal i David E. Kretschmanns kapitel 5 i jubilæumsudgaven af *Wood Handbook* fra 2010. Tabel 5–1 giver 34 arter eller artsgrupper med relative E- og forskydningsmoduler. Tabel 5–2 giver 35 med retningsbestemte Poisson-tal. Begge tabeller omhandler cirka 12 % træfugt. L, R og T betyder henholdsvis længderetningen, radialretningen og tangentialretningen. I et Poisson-tal er første bogstav lastretning og andet bogstav retningen for tværtøjningen. Forsøgsresultaterne kan afvige fra den teoretiske reciprocitet mellem to retninger. Manglende tabelceller er bevaret som huller. [Original udgivelse](https://research.fs.usda.gov/treesearch/37427) · [Original PDF](https://research.fs.usda.gov/download/treesearch/37427.pdf)

For 25 entydigt valgte artsrækker giver skønnet i fodnote a til tabel 5–1 også mulighed for at beregne omtrentlige moduler i MPa. I udgangspunktet bruges bøjningsmodulet ved 12 % fugt fra den tilhørende amerikanske række i tabel 5–3a. Den omtrentlige aksiale stivhed beregnes som 1,1 gange dette bøjningsmodul. Dernæst multipliceres den med hver tilgængelig retningsbestemt stivhedsratio. Hver sådan værdi har status `derived`, den anvendte kildecelle, den oprindelige faktor og betingelserne. De 145 skøn er afledt af laboratoriedata for træ uden knaster og udgør hverken egne prøvninger eller styrkeklasser til byggeri. De oprindelige bøjningsdata, som allerede findes under `wood`, indgår kun som beregningsgrundlag.

Afsnittet på side 5–39 angiver omtrentlige forhold mellem ekstra krybedeformation og første elastiske deformation for almindelige anvendelsesforhold efter flere år samt for grønt træ, der tørrer under last. Tabel 5–17, side 5–41, giver 15 forsøgstilfælde med maksimal cyklisk spænding som procent af anslået statisk styrke. Lastforhold, frekvens når oplyst, lastform, fiber-/knastforhold og omtrentligt cykeltal følger hvert punkt. To punkter kan ikke uden videre forbindes til en kurve for ét produkt.

## Træbaserede produkter

I 2021-udgavens kapitel 12 har Zhiyong Cai, C. Adam Senalik og Robert J. Ross sammenstillet resultater fra forskellige undersøgelser. Disse rækker bevarer undersøgelsens navn som angivet i håndbogen, fabriksnummer, forsøgstype og retning eller fugtindhold, hvor tabellen oplyser det. Bøjningsmodulet og det aksiale trækmodul ligger i samme katalogfelt med tydelig markering af målemetoden. `internal bond` betyder trækstyrke vinkelret på pladens flade. [Original udgivelse](https://research.fs.usda.gov/treesearch/62260) · [Original PDF](https://research.fs.usda.gov/download/treesearch/62260.pdf)

| Tabel | Materialer og afgrænsning |
| --- | --- |
| 12–2 | Krydsfiner fra seks træarter. Kolonnen om proportionalitetsgrænsen er udeladt, fordi den trykte GPa-enhed strider mod kolonnen i psi. |
| 12–3 til 12–6 | OSB fra 22 fabriksrækker, industrielle spånplader, hårde træfiberplader og MDF. Træsort, fabriksnummer og fugtindhold og retning afhænger af den enkelte tabel. MDF-tabellens skruedata i kg er udeladt. |
| 12–7 og 12–8 | Limtræ og LVL med studie, træart, lamineringer og belastningstype som oplyst. Tabel 12–8, Koch (1973), angiver 0,0 som LVL-stivhed ved fladbøjning. Denne celle er udeladt som uegnet beregningsinput. |
| 12–9 og 12–10 | Polypropylenreference, træ/polypropylen-blandinger samt ekstruderede træ/plast-produkter. Forskydningsstyrke og indtrykningsstyrke under en dyvel er særskilte størrelser. Tabel 12–10 har modstridende kolonnenavne og enheder for bøjningsstyrke og bøjningsmodul. Disse to kolonner er udeladt. |
| 12–11 | Intervaller for let cementbundet træuld med oplysning om variation i blanding, partikler, fremstilling og hærdning. Skærprøverne har et snævrere interval for relativ densitet, som følger værdien. |

Oversigtstabel 12–1 er udeladt for at undgå gentagelse af data fra de mere specificerede tabeller. Arter og prøvegrupper har kildeafgrænsede ID’er i dette supplement. Projektets øvrige kilder til en lignende handelsbetegnelse beskriver ikke nødvendigvis samme træart, fugt, sortering eller plade.

## Kilder og genindlæsning

De to originale kapitel-PDF’er er gemt under `originals/`. Forfatter, årgang, udgiveradresse, filstørrelse og SHA-256 står i `sources.jsonl`. De føderale kapitler videredistribueres som hele USDA-publikationer med oprindelige krediteringer. Underliggende tredjepartskilder beholder deres egen status. Dette supplement gengiver numeriske fakta med egne feltnavne. [USDA Forest Services beskrivelse af rettigheder til myndighedspublikationer](https://research.fs.usda.gov/sites/default/files/2024-06/srs-authorsguide-2024.pdf)

Fra mappen `materialer` kan data indlæses og undersøges med Rust-værktøjet.

```sh
ft-materials build --supplement data/supplements/mechanics-wood --require-originals
ft-materials facts mechanics-wood:material:species-spruce-sitka --field shear_modulus
ft-materials facts mechanics-wood:material:t12-3-1 --field elastic_modulus
```
