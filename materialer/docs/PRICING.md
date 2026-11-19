# Pris, budget og leverandørdata

Pris og budget skal være tilgængeligt under designarbejdet. Det behøver ikke stå ved siden af CO₂. Begge beregninger kan bruge de samme modelmængder, mens priskilder og miljøkilder bevares hver for sig. Arkitekten vælger løsningen; laveste enhedspris eller klimatal vælger ikke automatisk konstruktionen.

**Status 19.11.2026:** En første genbrugelig Python-del er implementeret i [pricing.py](../pricing.py): CSV/JSON-import i vores eget format, HTTPS-hentning af dette format, kildehistorik, sammenligning af eksplicit samme produkt og budgetopfølgning ekskl. moms. [Kør det adskilte testeksempel](../examples/pricing/README.md). Ingen faktiske kundeprisfiler er modtaget, og ingen byggemarkedsforbindelse er aktiveret. Rust-binæren og SolidCrafts modelleringsrum er uændrede. Lokale projektspecifikke modeller/kundepriser er ikke med i repoet.

**Styrende valg, 19.11.2026:** Vi udvikler vores eget pris- og budgetsystem. Leverandørernes ERP-/ordrestyringsintegrationer er dokumentation for mulige datakilder, ikke et valg om at bruge de systemer. Systemets priser, budgetter og sammenligninger er **eksklusive moms**. Bevar leverandørens oprindelige beløb/momsgrundlag og dokumentér omregning med den relevante sats én gang. Ukendt momsgrundlag må ikke gættes. Referencer skal være på samme grundlag; ændret momsvisning er ikke en besparelse. Den første afgrænsede prisfunktion er en separat Python-del; den er ikke installeret som en ny Rust-kommando.

## Hold budget og prognose adskilt

- **Budgetramme:** den valgte reference, som kun ændres ved en eksplicit budgetrevision.
- **Forventet slutpris:** faktiske omkostninger + resterende aftalte omkostninger + forventede ikke-aftalte omkostninger + særskilt begrundet risiko/reserve.
- **Afvigelse:** forskellen til budgettet på samme omfang og momsgrundlag. Ved ufuldstændige poster vises en kendt delsum og konkrete mangler, ikke en fuld projektpris.

En faktureret del af en ordre skal trækkes fra den resterende ordreforpligtelse. Betaling, fakturering, levering og bestilling er forskellige hændelser. Historiske faktiske udgifter og aftalevilkår må ikke overskrives af en nyere webshoppris. En accepteret aftale er kun prisfast i det omfang, dens vilkår gør den fast.

Prisændringer skal kunne forklares som design-/mængdeændring, markeds-/aftaleprisændring, ændret omfang eller bedre datadækning. Flere prissatte poster er ikke automatisk et dyrere design. Gem mængdegrundlag og prisudgave, så ændringen kan efterprøves.

## Beregn køb i de rigtige enheder

Netto → eksplicit spildtillæg → pakker/mindstekøb → valgt leverance → pris. Ubrugte pakkerester er ikke automatisk affald eller ekstra indbygget materiale i klimaberegningen.

Hver pris skal fastholde vare-ID/variant, fysisk enhed, referenceindhold, oprindelse (eksisterende/genbrug/nyt), valuta, momsgrundlag, kilde, prisdato og gyldighed. Klimaets funktionelle R-referenceareal er ikke et købsareal. En pris pr. 100 styk er ikke en stykpris, og en nettopris skal ikke have den allerede anvendte rabat trukket igen.

Afklar om prisen omfatter montage, materiel, spild, transport, emballage, gebyrer, overhead og avance. Samlede systemtilbud og deres indeholdte komponenter må ikke tælles dobbelt. Genbrug kan have udgifter til undersøgelse, reparation og tilpasning; det antages ikke gratis. En webshopvare er ikke automatisk produktet bag en generisk miljøreference.

DfD er et frivilligt tilvalg. Særlige beslag, DfD-prøver og montagefølger medtages kun i det valgte omfang. Almindelig materiale-, pris- og budgetberegning kræver ikke DfD. Læs [adskillelsesfunktionens afgrænsning](DISASSEMBLY.md).

## Første leverandørspor: STARK

Undersøgt 19.11.2026. [STARKs offentlige beskrivelse](https://www.stark.dk/services/digitale-muligheder) angiver kundeprisfiler, manuel CSV, typisk ugentlig levering og ét abonnementsmodtagersystem. Nogle varer har to enheder/priser. Siden beskriver særskilt Punch Out med OCI/cXML. FTP/SFTP og INVOIC optræder under e-faktura og beviser ikke en prisfilkanal til vores værktøj.

[Erhvervsbetingelsernes afsnit 4](https://www.stark.dk/Om-STARK/Salgs-og-leveringsbetingelser) beskriver et prisgrundlag eksklusive bl.a. moms og fragt. Den konkrete fil og kundeaftale skal afstemmes før normalisering; en rå erhvervspris må ikke kopieres ind som en pris inklusive moms.

**Anbefaling:** start med én kunderelevant prisfil og en dokumenteret modtagerrute. Punch Out er et andet brugerforløb og er ikke i sig selv dokumentation for ubetjent genprissætning af hele projektlisten. Der er ikke fundet en offentlig read-only pris-API-kontrakt i det gennemgåede materiale. Det udelukker ikke en særskilt aftale med leverandøren.

Ingen faktisk kundekonto, eksempelfil, feltkontrakt, pris-API eller automatisk levering er afprøvet i undersøgelsen. Ingen STARK-priser er aktiveret i repoet. Automatisk leverandørlevering, modtagelse, import, anvendelse i projekt og handel er fem forskellige trin.

## Flere leverandører, forskellige prisgrundlag

Undersøgt 19.11.2026. STARK er første eksempel, ikke en leverandørbinding. Ét prisoverblik skal kunne samle flere dokumenterede indgange uden at love samme format eller opdateringsfrekvens:

| Leverandør | Offentligt beskrevet mulighed | Hvad mangler før vores import? |
| --- | --- | --- |
| [Davidsen](https://www.davidsen.dk/webshop/hjaelp-til-erhvervswebshop/priser/modtag-automatiske-prisfiler-til-din-prisbog) | Automatiske elektroniske prisfiler til navngivne ordrestyringsprogrammer. | Eksempelfil, prisbasis, interval og eget modtagersystem. |
| [Bygma](https://www.bygma.dk/bygma-proff-services/) | Aftalepriser i ProffShop. [KeyBalance](https://www.keybalance.dk/edi/bygma) beskriver håndtering af Bygma-filer. | Leverandørens bekræftelse af filkontrakt/adgang; partnerens integration er ikke vores. |
| [XL-PRO](https://www.xl-byg.dk/xl-pro/om-xl-pro-dk) | Prislister med/uden aftale; [Jens Schultz](https://www.xl-byg.dk/artikel/proff-login) beskriver download til eget IT-system. | Lokal forretning, format og interval; ikke antaget ens i hele kæden. |
| [Brødrene Dahl](https://www.bd.dk/kontakt/spoergsmaal-og-svar/filer) | Månedlig listeprisfil plus særskilt kundens rabatfil; først totalfil, siden ændringsfiler. | Begge grundlag, korrekt aftale og afprøvet format/modtagelse. |
| [Silvan](https://www.silvan.dk/kundeservice/handelsbetingelser) | Offentlig webshoppris inkl. moms og indregnet rabat, ekskl. fragt/gebyrer. | Aftalt dataadgang; ingen prisfeed-kontrakt identificeret i læste sider. |
| [Havnens Hænder](https://havnens-h.dk/) | Udvalgt webshop samt tilbudsbestilling; fragt/håndtering særskilt. | Konkret variant, købspakke, prisbasis og aftalt dataadgang. |

Ingen af disse feedforbindelser er afprøvet her. Manglende offentlig API-dokumentation beviser ikke, at en aftale er umulig. En offentlig webshop eller kendt handelsplatform er heller ikke i sig selv en understøttet kommerciel API-kontrakt.

Hos Havnens Hænder viser [græsisolering](https://havnens-h.dk/products/graes-isolering) hele pakker med tykkelsesafhængigt areal og mail-/telefonbestilling. [Hampeisolering](https://havnens-h.dk/products/hamp-isolering) har ligeledes variantafhængige pakker. Webprodukters visning inklusive skatter må ikke stiltiende overføres til skriftlige tilbud: de [linkede betingelser](https://cdn.shopify.com/s/files/1/0754/5684/0023/files/Salgs-og-leveringsbetingelser_2024.pdf?v=1711375873) beskriver disse eksklusive moms. Registrér kildetypen og afklar den konkrete handel. En fra-pris er ikke tilstrækkeligt grundlag for valgt tykkelse/enhed; et EPD-link er ikke en eftervist klimaberegning.

Bevar produktidentitet adskilt fra leverandørens tilbud. Flere tilbud kan høre til samme dokumenterede producentvare/variant; et andet produkt er et materialevalg. Sammenlign samlet køb, pakker, montage og levering. Flere leverandører kan betyde flere leveringsgebyrer. Listepris og rabatgrundlag skal begge fastholdes, når nettoprisen afledes; træk ikke rabatten to gange. Fravær i en ændringsfil betyder ikke i sig selv ophørt vare. Byg en lille import efter en virkelig filkontrakt frem for en uprøvet adapter til hver leverandør.

## Afklar før en import bygges

1. Hvilken købende kunde/entreprenør, aftale og eventuelt projekt gælder priserne for? Kundernes private aftaler skal være adskilt.
2. Hvilken filvariant leveres, og hvad betyder kolonner, pris-/salgs-/pakkeenheder, rabatter og referenceindhold?
3. Er filen fuldt katalog eller ændringer? Hvordan beskrives gyldighed, ophørte varer, tomme/0-værdier og genlevering?
4. Hvilken tilladt transport og opdateringsfrekvens kan bruges af et selvudviklet program? Et eksisterende ERP-abonnement må ikke flyttes stiltiende.
5. Hvad omfatter prisen, og hvilke vilkår gælder for opbevaring, historik og brug i et værktøj for flere firmaer?

Først en virkelig eksempelfil og tre kendte varer i forskellige enheder. Byg derefter den mindste import, som passer til den bekræftede kontrakt. Der er ikke valgt mailmodtagelse, SFTP eller API alene ud fra en offentlig produktbeskrivelse.

## Kontroller før automatisk anvendelse

Disse krav er delvist afprøvet i den nye import med mærkede testdata. Virkelige leverandørfiler, adgangskontrakter og faktiske kundepriser er fortsat ikke afprøvet:

- Afstem tre faktiske varer mod samme kundes priser og mængder.
- Genimport af samme observation må ikke skabe dubletter eller en ny påstået prisdato.
- Forkert kunde, ukendt enhed, ændret format og ophørt vare skal give konkret afklaringsstatus.
- Hentefejl må ikke erstatte det gyldige grundlag med et tomt katalog eller skabe en falsk besparelse.
- Nye observationer skal kunne undersøges før aktivering. De må ikke ændre CAD, EPD-valg, faktiske udgifter eller aftalevilkår automatisk.

Registrér prisens observationstid, gyldighed, modtagelse og seneste vellykkede kontrol særskilt. Daglig kontrol gør ikke en ugentlig kilde til dagsdata. Genbrug gyldige modelmængder ved en ren prisændring og bevar budgetrammen.

Drift, vedligehold, udskiftning, rente, prisudvikling og restværdi kræver yderligere grundlag, før resultatet kaldes en levetidsomkostningsberegning (LCC).

## Læring fra den første implementering

Ingen leverandørfiler var til rådighed. Derfor er tre syntetiske leverandører isoleret fra rigtige projekter, og almindelige rapporter ignorerer testtilbud. En teknisk fungerende import af vores format er ikke dokumentation for, at en bestemt leverandørs fil kan læses. Afprøv den konkrete leverandørkontrakt før en adapter bygges.

Kontrollerne dækker blandt andet momsomregning og rabat én gang, indkøbspakker, mindstekøb, kundeadskillelse, kildehistorik, idempotent import, fejl uden sletning, tilbagekaldt/udløbet pris uden genoplivning af ældre pris, delvis fakturering uden dobbeltregning og uændrede aftalte omkostninger ved ændret markedspris. Ukendte leveringsomkostninger blokerer en fuld prognose. Laveste varebeløb må ikke præsenteres som billigste samlede leverance. Der er endnu ingen automatisk kombinationssøgning eller indkøbs-/fakturaintegration.

## Saml indkøbet med klima og den faktiske rabataftale

Brugerens seneste prioritet er at købe så mange passende varer som muligt ét sted, med både pris og CO₂ i vurderingen. `supplier_baskets` viser leverandørernes prisreferencedækning af de ikke-bestilte poster og hvilke poster der kræver supplering. Det er ikke automatisk leverandørvalg, faktisk lagerdækning, global indkøbsoptimering eller en skjult kr./CO₂score. Samlet levering/gebyrer holdes på leveranceplanen, ikke ganget på hver vare.

Håndværkerrabat hører til den konkrete købende virksomheds aftale og dens produkt-/varegruppeomfang. Den må ikke antages universelt, videregives mellem kunder eller trækkes igen fra en nettopris. Importen understøtter en eksplicit listepris/rabataftale og separat kontokontekst; afprøv faktisk aftale og rabattrin mod leverandørens egne priser.

Transport-CO₂ er et særskilt dokumenteret scenarie med kilde, ikke afledt af antal leverandørnavne. Ukendt leverandørtransport forbliver ukendt. Produktbidrag, emballage, faktisk spild og returer skal følge den konkrete indkøbsplan og materialemotoren. Nyt leverandør-A4 afstemmes som erstatning for relevant tidligere transportscenarie; det må ikke dobbelttælles. En enkelt leverandør kan sende fra flere lagre. [Testeksemplet](../examples/pricing/README.md) viser et bevidst pris-/transportklimatradeoff, uden en automatisk vinder.

## Budget som justerbare beslutninger, med arbejdstid og løn

Brugeren skal kunne afprøve enkelte poster ligesom ved klimavarianter: fasthold en reference, ændr forudsætninger og se forskellen, fortryd eller gem særskilt. `pricing_editor.py` er en første lokal budgetvisning med den samme Python-beregning bag redigeringen; [afprøv arbejdstimer og leverandørvalg](../examples/pricing/README.md). Dette ændrer ikke modelleringsrummet eller bygger et nyt CAD-interface. Den gemte variant aktiverer ikke automatisk et projektbudget, et materialevalg eller en EPD.

Arbejde beregnes i persontimer, med særskilt prisgrundlag for faktureret timepris, samlet lønomkostning og bruttotimeløn med dokumenterede tillæg. Manglende lønfølgeomkostninger må ikke blive nul, og en entreprenørs allerede sammensatte timepris skal ikke få løntillæg igen. Medregn ikke montage både i en samlet entreprise og som en særskilt timepost. Fag, afgrænsning, produktivitetsantagelser og kilder skal afstemmes før timer/satser bliver faktiske projektforudsætninger. Denne version håndterer planlægningsoverslag for arbejde, ikke lønbogføring eller tids-/fakturaafstemning.

Variantens faste budgetramme og dens kildepriser bevares. Forskelle mellem to fuldt sammenlignelige, kendte poster adskilles fra nye prissatte eller udeladte poster. En fuld projektforskel kræver fuld passende dækning i begge scenarier. Arbejdstimer er ikke en CO₂referenceenhed: materialefølger, byggepladsenergi, arbejders transport og affald skal have deres egne grundlag.
