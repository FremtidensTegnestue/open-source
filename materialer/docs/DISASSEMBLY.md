# Reparation og adskillelse

`ft-materials disassembly` vurderer konkrete indgreb på bygningsdele. Kommandoen kan bruges ved nybyggeri, renovering og transformation. Kommandoen kan bygges fra `main`. Den udgivne v0.3.0-binærfil er fra før funktionen blev tilføjet.

Du beskriver delene, deres forbindelser og det ønskede indgreb. Programmet udvider adgangsplanen med berørte dele, viser nødvendige erstatninger og beregner tilførte produkter med den eksisterende Rust-beregner. Det ændrer ikke CAD-modellen og udsteder ikke teknisk godkendelse.

## Prøv et eksempel

Byg fra denne checkout i `materialer/` og brug et allerede installeret datalager eller kør den normale `build` én gang. Eksemplerne fastholder mekanikudgaven af de offentlige data fra 20. november 2026. Et andet lager skal indeholde samme udgave. Kommandoerne her bruger standardlageret. Et eksisterende eksternt lager vælges med `--store STI`.

```sh
cargo build --locked
target/debug/ft-materials disassembly examples/disassembly/existing-window.json --text
target/debug/ft-materials disassembly examples/disassembly/new-build-window.json --text
```

Eksemplerne returnerer **statuskode 2**, fordi deres fysiske grundlag og materialeregistrering er ufuldstændige. Rapporten er gyldig som en delvis scenarievurdering. Kode 1 betyder fejl; kode 0 betyder, at kommandoen ikke fandt åbne punkter i de indsendte oplysninger. Ingen af koderne dokumenterer en fysisk bygningsdels egnethed.

- **Eksisterende vindue:** bevaring, liste/beslag og selektivt rudeskift. En ny liste er et antaget forbrug på 0,100 kg med generisk SBR-reference, ikke en valgt EPDM-profil.
- **Nybyggeri:** to foreslåede forbindelsesprincipper ved et senere rudeskift. Begge registrerer fornyelse af glasbånd. I det ene kan glaslisten foreslås genmonteret; i det andet bliver tabet af listen en ekstra, ukvantificeret erstatningspost. Begge bruger nutidige kildereferencer, ikke en prognose for fremtidig produktion.

Vindueskernen er et afgrænset forsøg. Karm-væg-forbindelse, retablering, arbejde, spild, transport, driftsenergi og fremtidige produktgenerationer er ikke fuldt beregnet. Manglende poster står i `unknowns`. Intet af eksemplerne er en komplet vindues- eller bygnings-LCA.

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

`actions` forbinder del-ID'er med `retain`, `repair_in_place`, `temporarily_remove`, `remove`, `replace` eller `install`. Ikke nævnte, tilstedeværende dele foreslås bevaret. En ikke-tilstedeværende del kræver en eksplicit installation. Reparation på stedet åbner ikke automatisk alle delens forbindelser. Hvis andre arbejder kræver, at den samme del tages af eller erstattes, viser rapporten den oprindelige bestilling, den foreslåede handling og den konflikt, der skal afklares.

`deliveries` er tilførte produkter med ID, navn, `covers_parts`, eksplicit `material_id`, mængde/enhed/evidens og valgte GWP-observations-ID'er. En manglende mængde er `null`. Forkert enhed, materialekobling eller indikator giver fejl fra den eksisterende beregner uden fallback. Samme del må ikke dækkes af både et komplet produkt og en ekstra produktberegning; overlappende `covers_parts` afvises. Separate slid-/overfladelag registreres som selvstændige dele, når de tilføres særskilt.

`supplied_inventory_complete` er brugerens eksplicitte erklæring om produktregistreringen, ikke programverificeret produktindhold. En install-/erstatningspost uden levering gør produktresultatet ufuldstændigt. Reparation kan også kræve materialer, som programmet ikke kan gætte; registrér dem eller hold erklæringen falsk og beskriv manglen.

## Resultat og afgrænsning

Standardoutput er JSON med foreslåede handlinger, følgearbejder, adgangsafhængigheder, kildeberegninger og konkrete mangler. `--text` viser samme vurdering på dansk.

- Manglende masse for en oprindelig del giver status `partial` og en ukendt bevaret masseprocent. En beregnet andel er et scenarie ud fra de angivne masser, ikke en eftervist genbrugsprocent.
- `known_totals_by_module` viser kun den kendte produktdelsum og ledsages af leverancedækning. Et modul uden beregnede leverancer er `null`; et kendt nul fra kilden bevares som nul. En fuldt erklæret situation uden nye produkter kan have nul produktbidrag uden at være en nul-LCA.
- Samlet produktreference kræver alle ønskede moduler og tilstrækkelig registrering. Et samlet C1–C4-tal fordeles ikke til C3/C4. Overlappende moduler afvises.
- Modul D vises særskilt. `D_separate` er den kendte delsum for de leverancer, der har D. `D_coverage` angiver antal oplyste og registrerede leverancer, og om hele inventaret har D-dækning. Negative kildetal ændres ikke til nul.
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
