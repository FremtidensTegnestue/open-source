# Reparation og adskillelse

**DfD er et tilvalg.** Værktøjets almindelige materiale-, klima-, pris- og budgetarbejde forudsætter ikke DfD. Brugeren vælger det for et projekt eller bestemte bygningsdele. Særlige DfD-konstruktioner og deres pris-/materialefølger indføres kun i det valgte omfang. De eksisterende DfD-eksempler er forsøg, ikke standardkonstruktioner for nye projekter.

`ft-materials disassembly` vurderer konkrete indgreb på bygningsdele. Kommandoen kan bruges ved nybyggeri, renovering og transformation. Funktionen findes i kildekoden, men er ikke med i den oprindeligt udgivne v0.3.0-binærfil.

Du beskriver delene, deres forbindelser og det ønskede indgreb. Programmet udvider adgangsplanen med berørte dele, viser nødvendige erstatninger og beregner tilførte produkter med den eksisterende Rust-beregner. Det ændrer ikke CAD-modellen og udsteder ikke teknisk godkendelse.

## Når DfD er valgt: design konstruktionen til adskillelse fra starten

Design for Disassembly påvirker konstruktionsprincip, lag og samlinger allerede under projekteringen. Produktmålet omfatter derfor også alternative opbygninger med uafhængige dele og realistisk udskiftningsadgang. Traditionelle løsninger kan rumme brugbare principper; en skruet forbindelse beviser ikke alene adskillelighed.

Et konstruktionsforslag skal undersøge:

- bærende system og stabilitet under ændring, herunder nødvendig midlertidig understøtning;
- uafhængige lag med forskellig levetid, fx bæring, klimaskærm, installationer og indvendig beklædning;
- adgang til forbindelser, værktøj, udtagningsretning og fri plads;
- udskiftelige tætninger, forbrugsdele, følgearbejder og retablering;
- et konkret reparations-, ombygnings- eller demonteringsforløb med forventet skade og genbrug på del- eller enhedsniveau;
- alle materialer ved første opførelse og senere indgreb, med samme relevante tekniske funktion og synlige klimamæssige afvejninger.

En mulig træningscase er en facade med separat fastgjort beklædning, tilgængeligt underlag og udskiftelige tætninger. Den skal undersøges i snit og arbejdsrækkefølge; dette er ikke et valgt eller eftervist produktsystem. Arkitekten vælger udtrykket. Brand, fugt, bæreevne, lyd og relevante luftveje afklares for den konkrete løsning. Fremtidigt genbrug giver ingen automatisk klimakredit.

**Implementeringsgrænse:** Kommandoen vurderer et allerede beskrevet indgreb. Den genererer eller efterviser ikke alternative konstruktionssystemer. Kravet om identiske del-ID'er på tværs af varianter beskytter dette afgrænsede sammenligningsomfang. Fysisk forskellige opbygninger kræver fremover eksplicit afstemning til fælles funktion og komplet mængdegrundlag; de må ikke presses ind i et forkert identisk delinventar for at bestå kontrollen.

Fagligt grundlag: BAMB beskriver reversible bygninger gennem tilpasning, genbrug og adskillelse samt uafhængighed og udskiftelighed mellem dele med forskellige funktioner og levetider. [BAMB, Reversible Building Design Tool, FAQ](https://www.bamb2020.eu/about-bamb/faq/faq-reversible-building-design-tool/), læst 19.11.2026. Punkterne ovenfor er vores produktkrav og konkretisering, ikke en gennemført BAMB-certificering eller ny runtimefunktion.

## Prøv et eksempel

Byg fra denne checkout i `materialer/` og brug et allerede installeret datalager eller kør den normale `build` én gang. Eksemplerne fastholder den offentlige v0.3-dataudgave; et andet lager skal indeholde netop denne udgave. Kommandoerne her bruger standardlageret. Et eksisterende eksternt lager vælges med `--store STI`.

```sh
cargo build --locked
target/debug/ft-materials disassembly examples/disassembly/existing-window.json --text
target/debug/ft-materials disassembly examples/disassembly/new-build-window.json --text
```

Eksemplerne returnerer **statuskode 2**, fordi deres fysiske grundlag og materialeregistrering er ufuldstændige. Rapporten er gyldig som en delvis scenarievurdering. Kode 1 betyder fejl; kode 0 betyder, at kommandoen ikke fandt åbne punkter i de indsendte oplysninger. Ingen af koderne dokumenterer en fysisk bygningsdels egnethed.

- **Eksisterende vindue:** bevaring, liste/beslag og selektivt rudeskift. En ny liste er et antaget forbrug på 0,100 kg med generisk SBR-reference, ikke en valgt EPDM-profil.
- **Nybyggeri:** to foreslåede forbindelsesprincipper ved et senere rudeskift. Begge registrerer fornyelse af glasbånd. I det ene kan glaslisten foreslås genmonteret; i det andet bliver tabet af listen en ekstra, ukvantificeret erstatningspost. Begge bruger nutidige kildereferencer, ikke en prognose for fremtidig produktion.

Vindueskernen er et afgrænset forsøg. Karm-væg-forbindelse, retablering, arbejde, spild, transport, driftsenergi og fremtidige produktgenerationer er ikke fuldt beregnet. Manglende poster står i `unknowns`. Intet af eksemplerne er en komplet vindues- eller bygnings-LCA.

## Facadens montering

[Afprøv en lokal udskiftningsopgave](../examples/disassembly/FACADE.md) med to eksplicitte montagehypoteser. Udvikl bæring, låsning, adgang, udtagningsretning og genmontage som én opgave. Vælg både del- og enhedsniveau; en aftagelig kassette dokumenterer ikke adskillelse af dens bestanddele. Eksemplet er kørt med den eksisterende motor og indeholder åbne materialemængder; det er ingen ny konstruktionsgenerator eller fuld klimaberegning.

## Input

De to JSON-eksempler er de konkrete skabeloner. Ukendte feltnavne og ugyldige enum-værdier afvises frem for at blive ignoreret.

| Felt | Betydning |
| --- | --- |
| `schema_version` | Skal være `1`. |
| `snapshot` | Fuldt, uforanderligt data-ID. `latest` afvises. |
| `scope` | Fælles funktion, indgreb, `new_build` / `renovation` / `transformation` og valgfri modelbinding. |
| `indicator`, `modules` | Præcis GWP-egenskab og ønskede kildemoduler. D må ikke indgå i summen. |
| `variants` | Konkrete muligheder, der vurderes; ingen automatisk optimering. |
| `basis_files` | Valgfrie lokale inputfiler med `path` og SHA256, fx en tilstandsregistrering. |

Hver variant indeholder samme sæt fysiske del-ID'er og samme indledende tilstedeværelse. En variant må ikke udelade en vanskelig del og dermed se bedre ud. Programmet kan kontrollere ID'er; den fælles funktion og et tilstrækkeligt omfang kræver stadig faglig vurdering. `equivalence` angiver denne vurderings kilde eller antagelse.

### Dele og forbindelser

En del har ID, navn, `origin` (`existing`, `reused`, `new`), `initially_present`, valgfri `current_mass` og `joints`. En masse er i kg og skal have eksplicit evidens. Delene skal beskrive adskilte fysiske mængder: registrér ikke både hele vinduets masse og massen af dets indeholdte rude som uafhængige mængder. Programmet kan ikke opdage et forkert fysisk hierarki ud fra navne alene.

Hver forbindelse har en beskrivelse af metoden samt:

- `access`: `accessible`, `blocked` eller `unknown`.
- `outcome`: `reversible`, `destructive` eller `unknown`.
- `evidence`: `basis`, `note` og valgfri `reference`. Dokumenteret eller testet kræver en henvisning, men programmet har ikke selv udført prøven.
- `requires_removal`: dele, der skal tages af for at få adgang. De foreslås midlertidigt udtaget. Destruktiv udtagning udløser en foreslået erstatning.
- `sacrificial_parts`: berørte dele, der skal erstattes eller fjernes. Det er en følgevirkning, ikke i sig selv en dokumenteret udtagningsrækkefølge.

Adgangsafhængigheder udvides, indtil planen er stabil. Cykliske adgangskrav afvises. Ukendt adgang eller adskillelse forbliver et åbent punkt. Den foreslåede rækkefølge er en adgangsplan, ikke en komplet de-/genmontageplan, understøtningsplan eller sikkerhedsinstruks. Demontering af et helt system som bevaret samlet enhed skal beskrives på det relevante enhedsniveau; denne version udleder ikke automatisk assembly-grupper fra en CAD-model.

### Handlinger og materialer

`actions` forbinder del-ID'er med `retain`, `repair_in_place`, `temporarily_remove`, `remove`, `replace` eller `install`. Ikke nævnte, tilstedeværende dele foreslås bevaret. En ikke-tilstedeværende del kræver en eksplicit installation. Reparation på stedet åbner ikke automatisk alle delens forbindelser.

`deliveries` er tilførte produkter med ID, navn, `covers_parts`, eksplicit `material_id`, mængde/enhed/evidens og valgte GWP-observations-ID'er. En manglende mængde er `null`. Forkert enhed, materialekobling eller indikator giver fejl fra den eksisterende beregner uden fallback. Samme del må ikke dækkes af både et komplet produkt og en ekstra produktberegning; overlappende `covers_parts` afvises. Separate slid-/overfladelag registreres som selvstændige dele, når de tilføres særskilt.

`supplied_inventory_complete` er brugerens eksplicitte erklæring om produktregistreringen, ikke programverificeret produktindhold. En install-/erstatningspost uden levering gør produktresultatet ufuldstændigt. Reparation kan også kræve materialer, som programmet ikke kan gætte; registrér dem eller hold erklæringen falsk og beskriv manglen.

## Resultat og afgrænsning

Standardoutput er JSON med foreslåede handlinger, følgearbejder, adgangsafhængigheder, kildeberegninger og konkrete mangler. `--text` viser samme vurdering på dansk.

- Ukendt gammel masse giver ingen bevaret masseprocent. En beregnet andel er et scenarie ud fra de angivne masser, ikke en eftervist genbrugsprocent.
- `known_totals_by_module` viser kun den kendte produktdelsum og ledsages af leverancedækning. Et modul uden beregnede leverancer er `null`; et kendt nul fra kilden bevares som nul. En fuldt erklæret situation uden nye produkter kan have nul produktbidrag uden at være en nul-LCA.
- Samlet produktreference kræver alle ønskede moduler og tilstrækkelig registrering. Et samlet C1–C4-tal fordeles ikke til C3/C4. Overlappende moduler afvises.
- Modul D vises særskilt og tælles aldrig med i summen. Negative kildetal ændres ikke til nul.
- En produktdifference beregnes kun med deklareret funktionel sammenlignelighed, komplet produktdækning og ens, oplyst klimametode. Fx mangler BR-referencernes `method`-felt i den aktive dataudgave: faktorerne kan beregnes, men denne kommando laver ikke automatisk en variantdifference på det grundlag.
- `complete_lifecycle_total` og `winner` er altid `null`. Der tilføjes ingen undgået belastning, fremtidig genbrugskredit eller samlet grøn score.

## Gem, genåbn og kontrollér

Gem JSON-output som rapport. For delvise vurderinger forventes kode 2, selv om JSON er skrevet. Kontrollér den gemte rapport ved at genberegne:

```sh
target/debug/ft-materials disassembly examples/disassembly/existing-window.json --check vindue-rapport.json
```

Denne kontrol kræver samme requestbytes, beregningsprogram, dataudgave, valgte observationer og eventuelle model-/grundlagsfiler. En ændring giver fejl; der returneres ikke en gammel succes. Model- og grundlagsstier opløses relativt til requestfilen. En modelbinding kræver `path` og SHA256. Den binder en gemt fil, ikke et markeret element eller en aktiv SolidCraft-session. Eksemplerne har ingen faktisk modelbinding.

## Kontrol af implementeringen

```sh
cargo test --locked --bin ft-materials disassembly::tests
```

Testene omfatter adgang og materialefølger, cykler, manglende masser/data, skiftet sammenligningsomfang, dobbelttælling af produkt og komponent, modulgrupper, D, kilde-/enhedsfejl og ændret gemt model. Den generelle native beregner bruges også i denne kommando; der er ikke indført en parallel GWP-formel eller nye pakkeafhængigheder.
