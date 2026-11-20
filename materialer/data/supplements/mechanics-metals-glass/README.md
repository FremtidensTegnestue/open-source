# Mekaniske materialedata fra metalkort, glasvejledninger og ultralydsforsøg

Samlingen indeholder 193 kildeposter og 848 tal. Den er til opslag om konkrete materialeklasser og forsøgsprøver. De samme 848 tal findes i faktastrømmen og observationsstrømmen for at understøtte begge opslag i Rust-værktøjet. Den enkelte værdi har enhed, kildested og anvendelsesbetingelser. [Optælling pr. felt og kilde](summary.json) · [Originaladresser og SHA-256](sources.jsonl)

| Kildegrundlag | Poster | Hvad værdierne beskriver |
| --- | ---: | --- |
| FieldCraft 0.8.1 | 9 | Kildespecificerede værdier ved stuetemperatur for konstruktionsstål, rustfrit stål, aluminium og titanium. |
| JRC’s Eurocode 2-regneeksempel (2014) | 1 | Karakteristisk flydespænding og elastisk stivhed for armeringsstål S500 B. |
| Glasvejledninger fra 2014 og 2026 | 7 | Ét generelt sæt referenceværdier for sodakalksilikatglas og seks referenceposter med bøjningsstyrke for bestemte glastyper. |
| To undersøgelser af Kanji Ono | 176 | Elastiske egenskaber udledt af ultralydsforsøg for prøver af bl.a. stål, støbejern, kobber, messing, aluminium, glas, sten, plast, brændt ler, mørtel, gips og komposit. Én post repræsenterer én kilderække. Retning, fugttilstand og gentagne prøver kan give flere poster med samme materialenavn. |

## Prøv fire opslag

Kør fra mappen `materialer` på en udgave, der indeholder dette supplement.

```sh
ft-materials facts mechanics-metals-glass:material:en10025-s235 --field yield_strength
ft-materials facts mechanics-metals-glass:material:s500-b-jrc --field yield_strength
ft-materials facts mechanics-metals-glass:material:soda-lime-reference --field elastic_modulus
ft-materials facts mechanics-metals-glass:material:ono-2022-a1-r04 --field dynamic_elastic_modulus
```

S235-kortet oplyser en flydegrænse på 235 MPa for den angivne produkttype og tykkelse på højst 40 mm. Det tilhørende faktaopslag opbevarer tallet som 235.000.000 Pa og giver standardudgave, tabelrække og side. I FieldCraft bruges oplysninger om flydegrænse og trækstyrke som reference. Valg af svigtkriterium og plastisk materialemodel sker særskilt. Værdier fra programkortet er kildeklassificeret som typiske værdier, minimumværdier eller projekteringskonstanter efter den enkelte oplysnings grundlag. [FieldCrafts materialebibliotek og kildebeskrivelse](https://github.com/tangency-labs/fieldcraft/blob/v0.8.1/docs/manual/structural/material-library.md)

JRC bruger armeringsstål **S500 B** (styrkeklasse 500, duktilitetsklasse B) i et regneeksempel om en pladsstøbt bygning. Side 17 angiver en karakteristisk flydespænding på mindst 500 MPa og et E-modul på 200 GPa. Kildens karakteristiske krav til duktilitet følger flydespændingen som betingelser. Med partialkoefficient 1,15 for den viste brudgrænsetilstand beregner forfatterne en regningsmæssig flydespænding på 435 MPa. Den ligger i det særskilte felt `conditions.worked_example_design`. Ved brug i en konkret bygning skal den valgte armering kunne identificeres, og beregningsforudsætningerne skal passe til projektet. [JRC’s originale regneeksempel, §1.4.2.1, trykt s. 17](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/1110_WS_EC2.pdf#page=29)

For grundmaterialet sodakalksilikatglas angiver 2026-artiklens tabel 3 et E-modul på 70 GPa og et Poissons tal på 0,2 til overslagsberegninger. For bøjningsstyrke skelner kilderne bl.a. mellem udglødet floatglas, varmeforstærket, termisk hærdet, kemisk forstærket og emaljeret glas. Overfladebeskaffenhed, lastvarighed, randforhold og partialkoefficienter har betydning ved eftervisning af en rude. De fire 2026-styrker kommer fra artiklens tabel 5, som henviser til et udkast fra 2023 og særskilte produktstandarder. JRC’s 25 MPa for mønstret glas er en dateret tysk angivelse med krav om producentbekræftelse. [Glasreview, tabel 3 og 5](https://doi.org/10.3390/buildings16030506) · [JRC’s originale vejledning, afsnit 3.3 og 3.6](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2021-12/ReqNo_JRC86637_lbna26439enn.pdf)

## Hvad et ultralydsforsøg fortæller

I 2022-artiklens tabel A1 har prøven af brændt rød mursten et dynamisk E-modul på 9,10 GPa. Forsøget bestemmer stivhed ud fra bølgehastigheder i prøven. En statisk eftervisning af en væg kræver en dokumenteret sammenhæng med langsom belastning, data for stenen og mørtlen samt oplysninger om væggen. Især fugt, porøsitet, materialeorientering og tidsskala kan ændre resultatet. Derfor har disse værdier egne felter, `dynamic_elastic_modulus`, `dynamic_shear_modulus` og `dynamic_poisson_ratio`. Retningsangivelser i kildetabellerne bevares med prøven. [Ono 2020, appendiks A](https://doi.org/10.3390/app10155265) · [Ono 2022, appendiks A](https://doi.org/10.3390/app122413026)

De 114 rækker fra 2020 kommer fra tabellerne A1–A3. De 62 rækker fra 2022 kommer fra tabellerne A1–A4. Rækker, som 2022-forfatteren henviser tilbage til 2020-artiklen som reference 44, forekommer én gang i dataudtrækket. Manglende værdier markeret med stjerne i kilden er udeladt. Hver dynamisk værdi og dens densitet kan findes i den arkiverede JATS-XML under den angivne tabel, tabelkroppens rækkenummer og kolonne. Densitet opgives i kg/m³. En originalværdi i Mg/m³ og dens enhed står i betingelserne. Vickers-værdierne fra Onos laboratorierækker føres med kildens hårdhedsnotation HN og uden omregning til brudstyrke.

I 2022-artiklen er der fem egenskaber, hvor to tabeller angiver forskellige værdier for den samme prøve. Begge værdier kan slås op med status `conflicting`. Det drejer sig om E og Poissons tal for bundet siliciumcarbid (forsøg 9) samt densiteten i de tre vandmættede mørtelprøver i tabel 6 og A2. Også forskellen mellem porøsiteten 31,3 % i tabel 6 og 31,7 % i tabel A2 følger de berørte poster som en kildenote. [Ono 2022, forsøgsdata og tabeller](https://doi.org/10.3390/app122413026)

## Originaler og genbrug

De to forsøgsartikler er skrevet af Kanji Ono. Glasreviewet er skrevet af Viviane Setti Barroso, Anísio Andrade og Paulo Providencia. PDF og JATS-XML er arkiveret uændret fra MDPI under CC BY 4.0. De to JRC-rapporter er © European Union 2014. Begge tillader gengivelse med kildeangivelse på den anden fysiske PDF-side. JSON-kortene fra FieldCraft er fastholdt til commit `c1bec5b74f666f40b2fa45db89ff2aeccbe61431` med de oprindelige licenstekster. Kortene henviser videre til deres tekniske kilder. Standardhenvisninger, dokumentudgaver og sideangivelser bevares på den enkelte observation. [Arkiverede originaler](originals/) · [Feltkortenes originale JSON](https://github.com/tangency-labs/fieldcraft/blob/c1bec5b74f666f40b2fa45db89ff2aeccbe61431/crates/model/data/materials.json) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
