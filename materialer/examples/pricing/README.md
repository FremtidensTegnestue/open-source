# Prøv vores pris- og budgetsystem

Første genbrugelige version af import, sammenligning og budgetberegning. Python 3.9+ og standardbiblioteket er tilstrækkeligt. Kør fra `materialer/`. Det er en separat Python-del; den udgivne Rust-binær og SolidCraft er ikke ændret.

**Alle leverandører, priser, aftaler og budgetter i denne mappe er TESTDATA.** Der er ingen forbindelse til et byggemarked. `example.invalid` er en bevidst uvirkelig adresse. Virkelige kundeprisfiler og projektregnskaber skal opbevares uden for Git.

```sh
python3 pricing.py import examples/pricing/supplier-a.csv --format csv --store /tmp/ft-price-test/store.json
python3 pricing.py import examples/pricing/supplier-b.csv --format csv --store /tmp/ft-price-test/store.json
python3 pricing.py import examples/pricing/supplier-c.json --format json --store /tmp/ft-price-test/store.json
python3 pricing.py report examples/pricing/project.json --store /tmp/ft-price-test/store.json --as-of 2026-11-19 --out /tmp/ft-price-test/report.json --allow-test-data
python3 pricing.py check /tmp/ft-price-test/report.json --as-of 2026-11-19
```

Åbn `/tmp/ft-price-test/report.html`. Den bruger ingen eksterne ressourcer. Testtilbud kræver det udtrykkelige `--allow-test-data`; en almindelig projektberegning ignorerer dem. Eksemplets dato er fastholdt for at gøre resultatet gentageligt. Brug en faktisk vurderingsdato ved rigtige priser og genberegn ved ændret kilde eller dato.

## Fra overslag til tilbud

Formålet er at danne et internt prisoverblik og et ensartet grundlag for at indhente og sammenligne leverandørtilbud. Skeln overslag, faktisk tilbud og accepteret aftale; vores beregning fastlægger ikke leverandørens pris. Brug [forespørgselsskabelonen](quote-request-template.txt). Den er generel og kræver afstemte mængder/krav; der er ingen automatisk afsendelse eller modelbaseret tilbudseksport. Priser, datoer og leverandører i eksemplet er fortsat testdata. En lavere postpris skal afstemmes med pakker, samlet levering, mangler og produktets egnethed, før den bruges i forhandling.

## Hvad bliver afprøvet?

**Nye kontraktgrænser fundet ved review:** Kør `python3 examples/pricing/probe_quote_limits.py` fra `materialer/` for fire isolerede reproduktioner af tilbudskontekst, flere selvstændige tilbud, produktændring med gammel ordre og priskildetyper. Der skrives kun til terminalen. Alle data er fiktive; assertions dokumenterer de aktuelle begrænsninger, ikke en bestået tilbudsfunktion. Se [fund, nødvendige afstemninger og næste acceptopgave](../../docs/REVIEW-2026-11-20.md). Projektspecifikke/mængdebetingede tilbud og genbrug af ordrer efter produktændring må ikke behandles automatisk som afklarede.

150 m² af samme fiktive folie, uden spildtillæg:

| Testleverandør | Købsregel | Varebeløb ekskl. moms | Levering | Samlet ekskl. moms |
| --- | --- | ---: | ---: | ---: |
| A, valgt i eksemplet | To ruller à 100 m², 400 kr./rulle ekskl. moms | 800 | 100 | 900 |
| B | Én pakke à 150 m², 700 kr./pakke | 700 | 400 | 1.100 |
| C | Mindstekøb 250 m², trin à 125 m²; listepris 625 kr./125 m² inkl. 25% moms og 10% dokumenteret testrabat | 900 | 100 | 1.000 |

B har laveste varebeløb og højere samlet beløb end A. Rapporten sorterer varealternativer, men vælger ikke automatisk leverandør. Skift `selection` eksplicit og genberegn for at sammenligne den samlede leverance. Ingen påstand om en automatisk global indkøbsoptimering.

## Importkontrakt, version 1

CSV bruger komma som separator, punktum som decimaltegn og UTF-8, eventuelt BOM. Kolonnenavnene følger testfilerne. JSON har `schema: 1`, `mode: "observations"` og `offers` med de samme felter. Dette er **vores udvekslingsformat**, ikke en påstået STARK-, BD- eller anden leverandørstandard. En faktisk leverandørfil kræver en konkret afprøvet konvertering til formatet.

- Identitet: `supplier_id`, `supplier_name`, `account_id`, `sku`, `product_id`, `mapping_reference`. `product_id` er en eksplicit afstemt produktvariant; navn eller samme miljøreference er ikke et match. `public` betyder offentlig pris, øvrige konto-ID'er er kundebundne. Ingen hemmeligheder i filerne.
- Fysik: `unit` (`m2`, `m3`, `m`, `stk`, `kg`, `L`, `job`), `origin` (`nyt`, `genbrug`, `eksisterende`), `price_quantity`, `purchase_step`, `minimum_quantity`. Pris pr. 100 stk kan kombineres med køb i 50 stk; referenceindhold er ikke nødvendigvis pakkestørrelse.
- Beløb: `amount`, `currency: DKK`, `tax_basis: incl_vat/excl_vat`. Ved inkl. moms kræves eksplicit `vat_rate`, fx `0.25`; den antages aldrig ud fra land eller leverandør. Systemets resultat er altid ekskl. moms.
- Prisgrundlag: `price_basis: net/list`. Listepris kræver `discount_percent` og `discount_reference`. Nettopris må ikke få rabat igen. Brug dokumenteret relevant rabataftale, ikke en antaget generel rabat.
- Kilde: `source_url` (HTTPS), `observed_on`, `review_on`, valgfri `valid_until`, `kind: budget_reference/quote/test`. Kontroldato er vores kontrolpolitik, ikke tilbudsgaranti. `availability: available/unknown/unavailable/quote_required` afspejler kilden, ikke en afprøvet lagerreservation.

Originale importbytes arkiveres ved lageret med SHA256; rå observation og normaliseret pris gemmes sammen. Gentagen fil giver ingen dublet eller ny prisdato. Historik bevares. Seneste observationsdato bruges først, derefter modtagelsestid ved samme dato. Filen skal derfor angive det faktiske observationstidspunkt på dagsniveau; den er ikke en intradagshistorik. Producent-/variantmapping og korrekt kontokontekst skal afstemmes før import.

Alle rækker valideres før lageret ændres. Import er tilføjelse af prisobservationer. Manglende rækker sletter aldrig varer. `mode: delta` afvises; leverandørens total-/ændringsfiler kræver særskilt dokumenteret konvertering, især ophørte varer. Ingen omgåelse af login eller automatisk HTML-scraping.

## Hent fra en aftalt filadresse

```sh
python3 pricing.py fetch 'https://leverandoer.example/aftalt-prisfil.csv' --format csv --store /sti/uden-for-git/leverandoerpriser.json
```

Adressen er et eksempel, ikke et eksisterende feed. Kommandoen henter version 1-formatet over HTTPS, med 20 sekunders timeout og højst 10 MiB. URL må ikke indeholde brugernavn/password. Login, API-nøgler, SFTP, mail, planlagte baggrundsjob og leverandørspecifikke adaptere er ikke implementeret. Hentefejl returnerer fejl og bevarer det tidligere lager; den gør ikke det gamle grundlag nyere. Hentning er teknisk afprøvet med en kontrolleret HTTP-respons i testen, ikke mod en virkelig leverandørs kundekonto.

Import/hentning ændrer kun lageret. Den ændrer ikke projektvalg, CAD, EPD eller budgetramme. Genberegn rapporten efter import og kør `check`. Rapporten er gemt med vurderingsdato og input-/program-/originalfilhash, ikke en live kontrol ved HTML-åbning. Ved fejl er en gammel gemt rapport historisk og må kun bruges efter en bestået aktualitetskontrol.

## Budget og bestillinger

Projektfilen har et eksplicit `scope_id`, `account_id`, DKK/ekskl. moms, `lines`, `delivery`, valgfri `budget` og `unresolved_scope`.

- Postens netto og `waste_rate` giver behovet. Modellerede materialemængder må ikke erstattes med klimaets funktionelle referenceareal.
- Valg angives som `selection: {supplier_id, account_id, sku}`. Kun samme `product_id`, fysisk enhed og oprindelse sammenlignes. Kundepriser fra en anden konto afvises fra sammenligningen. Offentlige referencer er tilladt men mærket.
- Samme leverandørvare skal samles i én købspost før pakker/mindstekøb. Dublerede valgte SKU'er afvises i denne version. Komplekse mængderabattrin, flere afsendelser og rabat-/leveringsoptimering er endnu ikke implementeret.
- Ordresnapshots angives i `orders`: unikt `id`, `supplier_id`, `reference`, `price_fixed: true`, `quantity`, `invoiced_quantity`, `invoiced_excl_vat`, `remaining_excl_vat`. De er afstemte summer, ikke en fakturaimport eller et bogføringssystem. Faktureret mængde må ikke overstige ordremængden. Betaling og modtagelse er ikke lig fakturering; disse hændelser er ikke modelleret her.
- Faktureret + eksplicit resterende aftalt beløb tælles én gang. Ordremængden fratrækkes behovet; kun den endnu ikke bestilte rest prissættes fra tilbuddene. Prisvariable aftaler kræver afklaring og afvises som fast pris. Overskydende ordremængde markeres til afstemning.
- `delivery` er samlede projektspecifikke leverings-/gebyrbeløb pr. valgt leverandør, ekskl. moms, med reference. Ikke en automatisk universel fragtsats eller et beløb pr. post. Manglende levering er ukendt; nul skal være et eksplicit begrundet scenarie.
- En fast budgetramme kræver beløb, revision og dato. `null` betyder ikke fastlagt. Den ændres ikke ved prisopdatering. Kendt delsum vises altid; fuld prognose og afvigelse vises kun, når alle poster og erklærede følgeomkostninger er dækket. En overskridelse af budgettet kan allerede påvises, hvis den kendte delsum er større end rammen.

Dækningen gælder det **erklærede** omfang, ikke automatisk hele byggeriet. Montage, materiel, transport, manglende materialer og andre kendte huller skal stå som poster eller i `unresolved_scope`. Ukendt er ikke nul. Et tilbud er ikke en accepteret ordre. DfD er frivilligt, og der tilføjes ingen standard-DfD-omkostning.

```sh
python3 -m unittest discover -s tests -p test_pricing.py -v
```

## Samlet indkøb, håndværkerrabat og CO₂

Brug `examples/pricing/project-basket.json` i reportkommandoen for at afprøve folie og skruer samlet. A og B har pris på 2 af 2 testposter, C på 1 af 2. A giver 1.000 kr. med levering og det fiktive transportscenarie 6 kg CO₂e. B giver 1.190 kr. og det fiktive transportscenarie 3 kg CO₂e. C kræver supplerende indkøb og får ingen fuld sum. Ingen af disse værdier vedrører rigtige produkter, ruter eller leverandører.

Brugerens prioritet er at samle så mange egnede varer som muligt ét sted og vurdere samlet pris og CO₂. `supplier_baskets` viser derfor samlet prisreferencedækning pr. leverandør og manglende poster, uden automatisk at erstatte det valgte indkøb. Antal prissatte poster er ikke værdidækning eller bekræftet lager-/leveringsevne. Der er ingen skjult vægtning mellem kroner, CO₂ og arkitektur.

Håndværkerrabat behandles som en konkret aftale for den faktisk indkøbende kunde/entreprenør, leverandør og varegruppe/produkt. Indlæs listepris med den relevante rabatreference og korrekt `account_id`, eller en allerede beregnet nettopris. Rabatprocent antages ikke ud fra leverandørnavn eller kundetype. Private aftaler må ikke genbruges som offentlige priser, og en nettopris rabatteres ikke igen. Adgang, vareafgrænsning, gyldighed og eventuelle rabattrin skal afklares ved rigtig dataimport; komplekse rabattrin er endnu ikke modelleret.

`delivery[supplier_id]` kan have et eksplicit `transport_kg_co2e` med `climate_reference`. Det er et samlet afstemt transportscenarie i det angivne projektomfang, ikke et generisk CO₂tal pr. leverandør eller en antagelse om én bil. Ukendt pris og ukendt CO₂ er forskellige mangler. Et kendt leveringsbeløb kan have ukendt CO₂ og omvendt. Færre indkøbssteder er ikke automatisk færre afsendelser eller lavere klimaaftryk; lagersteder, rute, mængder, køretøj og samlastning kan ændre resultatet.

Materialernes produktbidrag følger det faktiske produktvalg og de afstemte materialemængder i klimamotoren. Prisimport ændrer dem ikke. Emballage, faktisk spild, returer og supplerende leverancer skal afstemmes, hvis indkøbsplanen ændrer dem. Genbrug ikke ubrugt pakkeindhold som automatisk affald. Leverandørens transportscenarie skal erstatte det relevante eksisterende projekt-A4-bidrag efter afstemning, ikke lægges oveni. Transporttallet alene er ikke bygnings-LCA eller dokumentation for lavest samlet klimaaftryk.

## Justér arbejdstimer og timepriser som budgetvarianter

`project-labor.json` udvider det fiktive eksempel med to arbejdsposter. Referencen er 6.200 kr. inklusive eksempelmaterialer/levering, alt ekskl. moms; den fiktive budgetramme er 7.000 kr. Ingen af timesatserne er markedsdata.

```sh
python3 pricing_editor.py examples/pricing/project-labor.json --store /tmp/ft-price-test/store.json --variant /tmp/ft-price-test/budgetvariant.json --as-of 2026-11-19 --allow-test-data
```

Åbn den udskrevne adresse på `127.0.0.1`. Visningen kører lokalt og genberegner gennem Python-kernen, når timer, timepriser eller leverandørvalg ændres. Der er ingen parallel JavaScript-beregning af budgettet. Den faste budgetramme ændres ikke. Forsinkede svar ignoreres, og en ændret indtastning markeres som afventende. Referencen er skrivebeskyttet; **Gem særskilt variant** skriver kun den angivne variantfil. **Fortryd ændringer** gendanner de værdier, filen blev åbnet med.

En gemt variant kan åbnes som projektfil i samme kommando med en ny `--variant`-destination. Den oprindelige references checksum kontrolleres, og sammenligningen fortsætter mod den. Ændret model-/pris-/programgrundlag afbryder visningen og kræver genstart. Budgetramme, model og leverandørprisarkiv bliver ikke ændret af en afprøvning. Serveren binder kun loopback, kræver den tilfældige adresse og afviser POST fra andre origins. Den er en lokal afprøvningsvisning, ikke en hostet flerbrugerapp eller SolidCraft-plugin.

Arbejdsposter ligger i projektets `labor`:

- `id`, `label`, `hours`, `hourly_rate`, `rate_basis`, `reference` og eventuelle `linked_line_ids`.
- `hours` er **persontimer**: to personer i fire timer giver otte persontimer. Timer er ikke i sig selv varighed eller en eftervist tidsplan.
- `contractor_rate`: entreprenørens fakturerede timepris ekskl. moms. Løntillæg må ikke lægges oveni igen.
- `employer_cost`: virksomhedens samlede omkostning pr. persontime, med indhold dokumenteret i referencen.
- `gross_wage`: selve bruttotimelønnen. Beregning kræver særskilt afstemt `employer_addon_percent`; manglende ferie-/pensions-/øvrige omkostninger er ukendte, ikke nul. Ingen lovbestemt eller universel procentsats er indkodet. Løn er ikke en momsbelagt leverandørpris; det er projektets omkostning, som vises på samme ekskl. moms-regnskabsgrundlag.
- Ukendte timer/priser angives som `null`, ikke nul. Den kendte delsum kan vises, men fuld prognose forbliver uafklaret.
- Hvis arbejde indgår i en samlet materialeleverance/entreprise, kan en eksplicit dokumenteret `included_in_line_id` markere dette. Arbejdet får da ikke et ekstra tillæg til regnskabet. Parentpostens omfang/pris skal være afstemt; det er ikke en gratis arbejdsydelse.

Timer og satser er endnu et **planlægningsoverslag**. Individuel lønkørsel, løn-/tidsregistrering, fakturaafstemning af arbejdsposter, holdplan og automatisk montageproduktivitet er ikke implementeret. Materialeposternes eksisterende ordresnapshots er særskilte; arbejdsposternes priser skal ikke omtales som faktisk afholdte eller låste udgifter.

`compare_reports` viser reference, variant og forskel på sammenlignelige poster; ny prisdækning og tabt prisdækning vises separat. En fuld forskel vises kun, når begge beregninger har dækket det erklærede omfang. Et nyt kendt arbejdsbeløb er ikke automatisk et fordyrende design. Der er ingen automatisk ændring af CO₂tal ud fra arbejdstimer. Ændret montage kan påvirke materialer, beslag, spild, transport og byggepladsenergi; disse følger skal afstemmes separat.

```sh
python3 -m unittest discover -s tests -p 'test_pricing*.py' -v
```


## Gentag den afgrænsede leveranceundersøgelse

```sh
python3 examples/pricing/probe_delivery_limits.py
```

Kør fra `materialer/`. Scriptet bruger eksisterende `pricing.py` og fiktive vinduesbeløb/hændelser. Det skriver et JSON-resultat til terminalen og ændrer ingen projektfil, ordre eller model. Seks grænseprøver viser, at nettobudget kan beregnes, mens fysisk modtagelse/skade/montage, kreditforløb og slutaccept ikke håndteres som leverancehistorik. Entydige linjenøgler skal afstemmes, før flere linjer fra samme eksterne ordre kan indlæses. Det er et gentageligt researchredskab, ikke et nyt leverancesystem eller en brugeraccepttest. Produkt-/fragt-/arbejds-/klimadata er ikke dokumenteret af eksemplet.
