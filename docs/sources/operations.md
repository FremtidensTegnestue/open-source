# Hvad skal vedligeholdes, og hvor længe holder det?

En arkitekt kan slå en konkret dør, et vindue eller et facadeprodukt op og se, hvilken del en oplysning gælder. En driftsleder kan følge henvisningen tilbage til en side i producentens vejledning. En rådgiver kan se, om en hyppighed er en antagelse i et miljøregnskab eller en anvisning for den dør, bygherren overtager.

## Tre opslag, der gør en forskel

| Produkt og kilde | Hvad fortæller den? | Hvad kan man bruge det til? |
| --- | --- | --- |
| DEKO DG dobbeltglasdør | Miljødeklarationen regner med 30 års referencelevetid, tre rengøringer om året, én årlig smøring og 0,94 g smøremiddel pr. m² pr. smøring. Driftsmanualen siger, at hængsler smøres efter behov og ved højdejustering. Grebets funktion og fastgørelse skal kontrolleres regelmæssigt efter brugens omfang. | Beregn det beskrevne miljøscenarie for et opmålt dørareal. Giv driftslederen den separate producentanvisning. [Miljødeklaration, fysisk PDF-side 10](https://www.epddanmark.dk/media/5rpm3ale/md-24069-en.pdf#page=10) · [DEKO DG, drift og vedligehold, side 3](https://a.storyblok.com/f/59946/x/118b6cd2e4/d_v_dg_dor-da-en_gb-c.pdf#page=3) |
| RotationVent RV2 | RSL-tabellen forudsætter årligt filterskift. B2-tabellen regner med halvandet år mellem skift og angiver også den afrundede frekvens 0,667 pr. år. Revisionsnoten forklarer ændringen til halvandet år. | Begge perioder har status `conflicting`. Vælg det konkrete B2-scenarie med kildehenvisning ved en LCA. En kalender til driften kræver en driftsanvisning. [Maico Nordic, revision 2, PDF-side 2 og 10](https://www.epddanmark.dk/media/200ljx5q/md-24123-en_rev2.pdf#page=10) |
| LinCrete-facadepladen i modeleksemplet | Producenten angiver en beregnet funktionstid over 50 år og henviser særskilt til en tabel med mindst 50 år. ØKOBAUDAT-registreringen modellerer nedtagning efter 50 år. | Slå den valgte plade op fra modellen. Oplysningens type, den åbne eller lukkede nedre grænse og kilden følger med. Ingen af værdierne er en garanti for en opført facade. [Lindners EPD, fysisk PDF-side 4](https://ibudata.lca-data.com/resource/sources/d1d9893d-2d5b-44fe-a55c-151303189a64/_LinCrete_Glass-Fibre_Reinforced_Concrete_22566.pdf?version=00.01.000#page=4) · [IBU's datasæt](https://ibudata.lca-data.com/datasetdetail/process.xhtml?uuid=c54c16f6-4295-4749-bff0-ba7ed4bc9117&version=00.01.000) |

## Hvilke data følger med?

Det offentlige tillæg giver 135 udsagn om 36 eksisterende produktposter. Det dækker blandt andet rørisolering, loftsplader, facadeplader, korkgulve, tæppefliser og keramiske fliser. For CLIMAFLEX følger levetidsantagelsen af, hvornår rørene udskiftes. For Amorim-korkgulve er støvsugning og vådrengøring to opgaver med forskellig hyppighed. For Rockpanel angiver en historisk udgave første genbehandling for én finish og et tilbagevendende interval for en anden. Rockpanel-kilden havde gyldighed til 2025. [CLIMAFLEX-datasæt](https://oekobaudat.de/OEKOBAU.DAT/resource/processes/adf13951-973f-4f8a-8267-e987d8de4fe1?format=json&view=extended&version=00.02.000) · [Amorim-kilde](https://oekobaudat.de/OEKOBAU.DAT/resource/processes/7b06ebcb-bf35-4ce0-8562-04a31cc7a315?format=json&view=extended&version=00.02.000) · [Rockpanel-kilde](https://oekobaudat.de/OEKOBAU.DAT/resource/processes/5a705462-f3ef-4451-8d47-d2be6beb6fd9?format=json&view=extended&version=00.09.001)

Samme LinCrete-post giver adgang til kildens varmeudvidelsesinterval, SVHC-grænse med kandidatlistens dato, affaldsbehandling, transport og brand- og lydegenskaber med deres konkrete opbygninger. Lydværdierne gælder en plade med 14 % åbent areal og mineraluld bagved. Brandklassen gælder den angivne opbygning med akustikvæv og mineraluld. Dokumentposten fører til den EPD, som gengiver prøvningen. [Lindners original, fysisk PDF-side 3, 4 og 6](https://ibudata.lca-data.com/resource/sources/d1d9893d-2d5b-44fe-a55c-151303189a64/_LinCrete_Glass-Fibre_Reinforced_Concrete_22566.pdf?version=00.01.000#page=3)

Det danske tillæg genskaber 109 udsagn om 28 eksisterende danske EPD-poster fra 28 deklarationer og to DEKO-manualer. Det omfatter blandt andet døre, vinduer, hampebeton, uldtekstiler, maling, fjernvarmeunits og ventilation. For Triplans måtte skelnes der mellem måttens tabellevetid og antagelsen om, at den følger stålprofilet, indtil det nedtages. For en fugtig, allerede installeret måtte kræver en restlevetidsvurdering oplysninger om det konkrete eksemplar. [Dansk kildeliste med PDF-versioner og kontrolsummer](../../data/supplements/operations/danish.lock.json)

## Prøv det på din computer

Med en klon af projektet og det kompilerede Rust-CLI kan du bygge databasen og læse de offentlige oplysninger offline fra første opslag. `ft-materials build` læser de færdige data i Git, også når mappen med hentede PDF-originaler er tom. Kompilering af CLI'et kan kræve internet til Cargo-afhængighederne første gang. Her er et opslag for LinCrete-pladen.

```sh
ft-materials build
ft-materials facts environmental:material:oekobaudat:c54c16f6-4295-4749-bff0-ba7ed4bc9117@00.01.000 --field service_life_value
```

Kør følgende fra projektets rod for at få de danske driftsopgaver med. Når man angiver tillæg manuelt, skal hvert ønsket tillæg med i byggekommandoen.

```sh
ft-materials collect-epd --locked
ft-materials collect-operations --danish
ft-materials build \
  --supplement data/supplements/tampere \
  --supplement data/supplements/operations \
  --supplement data/supplements/field-sources \
  --supplement data/staging/epd-danmark \
  --supplement data/staging/operations-dk
ft-materials facts epd-danmark:record:3746df4da119c92cf0998ed1eb0b3deb --field condition_trigger
ft-materials facts epd-danmark:record:9a0b48bb30ea8a2ac58c9a594232ead8 --field maintenance_frequency
```

Hver opgave har en komponent, et kildegrundlag og et gruppenavn i `conditions`. Forbind en opgave med dens interval, ressourceforbrug og udløsende tilstand ved samme `material_id`, `source_id` og `conditions.statement_group`. En frekvens på tre gange årligt angiver et antal. Den første dato kræver en selvstændig oplysning. En årlig opgørelse af energi til støvsugning angiver alene regnskabets periode. Databasen lader antallet af rengøringer stå åbent, når kilden gør det.

## Originaler, rettigheder og kontrol

ZIP-filen rummer 36 uændrede, versionerede procesfiler fra ÖKOBAUDAT. Hver kildepost angiver udgiverens licens og SHA-256 over den ukomprimerede original. Se også projektets registrering af ejer, adgangsvilkår og brugsret pr. kilde. De enkelte PDF'er har deres egne rettighedshavere. En generel tilladelse til at genudgive hele PDF-filerne er ikke dokumenteret. Rust-indsamleren henter dem direkte fra udgiverne, gemmer dem lokalt og kontrollerer versionen. De offentlige strukturerede udsagn henviser til de originale sider. [Offentlig kildeliste](../../data/supplements/operations/public.lock.json) · [Miljødata og vilkår](environmental.md) · [EPD Danmarks programinstruktion, §5.9](https://www.epddanmark.dk/media/ifrh2ghc/general-programme-instructions_v3.pdf)

```sh
ft-materials collect-operations
ft-materials collect-operations --offline
ft-materials collect-operations --danish --offline
cargo test --locked --release --test operations_rust
```

Ved første genkontrol udpakker `collect-operations` de 36 procesfiler fra det medfølgende arkiv og henter LinCretes ene originale PDF fra IBU. Efter en vellykket onlinekørsel kan `--offline` genskabe samtlige 135 offentlige udsagn ud fra de samme kildebytes. Den danske genkontrol kræver de danske PDF-originaler fra den første onlinekørsel med `--danish`. `--output /sti/til/mappe` skriver udtrækket separat. En afvigende SHA-256 eller et manglende tekstanker afbryder indsamlingen inden publicering af nye fakta. En ny dokumentudgave får sin egen gennemgang og kildelås. Det fastholder den version, som en tidligere beregning byggede på.
