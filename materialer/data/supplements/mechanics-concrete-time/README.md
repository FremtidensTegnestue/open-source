# Krybning, svind og udmattelse i beton og andre cementbaserede materialer

Denne samling giver adgang til målte tidsforløb og til den blanding, prøvegeometri og publikation, som hvert forsøg bygger på. Det meste af materialet er beton. Den store forsøgsdatabase omfatter også mørtel og cementpasta. Et forsøgs-id eller blandings-id identificerer en kildepost. Flere forsøg kan bruge den samme blanding. [Šmilauer m.fl., database og manual](https://doi.org/10.5281/zenodo.8150177)

| Mængde | Hvad den beskriver |
|---:|---|
| 1.411 krybekurver med 28.519 målepunkter | Registreret krybefunktion pr. spændingsenhed over tid |
| 3.512 svindkurver med 69.267 målepunkter | Længdeændring pr. længdeenhed over tid |
| 1.482 trykstyrker | Gennemsnitlig cylinder- eller kubestyrke ved 28 døgn, med prøveform i feltet `basis` |
| 632 elasticitetsmoduler | Blandingens oplyste E-modul ved 28 døgn, i MPa |
| 16 cykliske forsøg | Frekvens, belastning og antal cyklusser for hver HPC-prøve |

De 7.053 poster repræsenterer 6.328 forsøgs- eller blandings-id’er. Kurverne er observationsdata til sammenligning og modelafprøvning. Danmark, en betonstyrkeklasse eller et produkt kan først knyttes til en kurve, hvis der er belæg for det i den enkelte posts oplysninger.

## Læs en kurve

`conditions.test` rummer forsøgsalder, temperatur, fugtforhold, spænding og oprindelige kvalitetsmarkeringer, når kilden angiver dem. `conditions.specimen` giver prøvegeometri og forbehandling. `conditions.mix` beskriver sammensætningen. Kildeartikler, årstal og tilgængelige DOI’er ligger i `conditions.literature`, hentet ved opslag fra prøve til blanding og fra blanding til litteratur. [Originalarbejdsbog](https://zenodo.org/api/records/8150177/files/CreepShrinkage-2023-07-15-xlsx.xlsx/content)

**Krybning.** `creep` har y-enheden µstrain/MPa. Én µstrain er en milliontedel tøjning. Den rapporterede funktion `CD_Jcreep` angiver deformation pr. spænding. I en samlet compliance indgår den øjeblikkelige elastiske tøjning sammen med den efterfølgende deformation. Feltet `CT_elastic_strain` fortæller, om starttøjningen blev målt. Hvis der mangler et målt nulpunkt, kræver brug som ren krybetøjning eller som dimensionsløs krybefaktor yderligere oplysninger. Basiskrybning og samlet krybning bruger tid i døgn siden belastning. Tørringskrybning bruger døgn siden eksponering. Feltet `CT_sigma` har positivt fortegn ved tryk. Kildens foreslåede tids- og complianceforskydninger ligger som særskilte oplysninger. [Forskergruppens artikel, især afsnit 3 og 4](https://doi.org/10.3390/ma16206751)

**Svind.** `shrinkage_strain_time` har y-enheden µstrain. Negative værdier angiver sammentrækning og positive udvidelse. For totalt svind og udtørringssvind tæller x-aksen døgn fra starten af udtørring. Ved autogent svind er nulpunktet det registrerede `ST_t_dryingFrom`. Værdier under `Water storage` eller uden type beholder kildens tidsværdier og får eksplicit ukendt reference. Databasen indeholder også målinger før det valgte nulpunkt og gentagelser på samme tidspunkt. Alle målte fortegn og disse gentagelser er bevaret. [Feltbeskrivelser i originalarbejdsbogen](https://zenodo.org/api/records/8150177/files/CreepShrinkage-2023-07-15-xlsx.xlsx/content)

**Fugt.** Kildens fugtfelter benytter også talkoder. Ved krybeforsøg kan for eksempel 99 betyde en forseglet prøve, 100 opbevaring i vand, 101 damp og 85 fugtig opbevaring. Slå det konkrete feltnavn op før brug som procent. Alle originale kolonnebeskrivelser for de anvendte tabeller står i [source-columns.json](source-columns.json).

**Udmattelse.** I arket `Sample details` under `Fatigue` står 16 prøver af højtydende beton, alle ved 10 Hz. `Pmax`, `Pmin`, `Pa` og `Pmean` bevarer enheden kN. `Stress` er kildens egen spændingskolonne i MPa. `N` spænder fra 5 til 2.001.945 cyklusser. Arket identificerer ikke observationens afslutning som brud eller afbrudt forsøg for hver prøve. En afledning af levetid eller en S–N-kurve kræver afklaring af det udfald. [Miarka, forsøgsdata, version 2](https://doi.org/10.5281/zenodo.19844638) · [Publikationen om forsøgene](https://doi.org/10.1016/j.cemconcomp.2025.106394)

## Kvalitet og fravalg

Hele kildearket ligger i `originals/`. Importen gennemgår 30.509 rækker med krybedata og 69.947 med svinddata. Først fjernes punkter fra forsøg med `ERROR` i kildens CTU-kvalitetskolonne. Derefter fjernes punkter med `elimData` slået til og rækker uden et numerisk par. Rækkefølgen giver ét fravalg pr. række.

| Status | Krybning | Svind |
|---|---:|---:|
| Rækker på forsøg med `ERROR` | 1.509 | 478 |
| Enkeltpunkter med aktivt `elimData` | 481 | 198 |
| Mangler tidspunkt eller måleværdi | 0 | 4 |
| Med i kataloget | 28.519 | 69.267 |

Kildens spørgsmålstegn angiver problematiske forsøg. De er søgbare med eget mærke i `conditions.source_quality_class`. Af de beholdte krybekurver er 369 klassificeret som plausible og 1.042 som problematiske. For svind er det 1.623 plausible, 1.631 problematiske og 258 uden anvendelig klassifikation. En plausibilitetsvurdering på ét forsøg giver ingen fælles måleusikkerhed for punkterne eller karakteristisk projekteringsværdi for et produkt. [Forfatternes beskrivelse af klassifikationen](https://doi.org/10.3390/ma16206751)

Hvert par af x- og y-værdier henviser i samme rækkefølge til `source_point_ids`. Tilhørende kildenoter, kontroller, flag og registreret massetab ligger under punktets id i `point_attributes_by_id`. Dobbeltregistrerede tidspunkter bevares som individuelle punkter, sorteret på tidspunkt og oprindeligt id. De udleverede tal er bevaret uden udglatning, interpolation eller efterkorrektion. Hvor et felt var tomt i arket, kan nøglen mangle i JSON.

## Kilder og genskabelse

Bogfiler og dokumentation er bevaret byte-for-byte. `sources.jsonl` angiver navne, udgivelsesversion, direkte download, licens, filstørrelse, SHA-256 og udgiverens MD5. De gemte Zenodo-metadata registrerer udgivernes CC BY 4.0-licenser. Regnearket indeholder hele den anvendte krybe- og svinddatabase. Ved udmattelsesforsøg er stikprøvens testark og README arkiveret. Forfatterens øvrige billeder og rå maskinlogger kan hentes hos udgiveren. [Krybning og svind, version 2023-07-15](https://zenodo.org/records/8150177) · [Udmattelse, version 2](https://zenodo.org/records/19844638) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

Kør fra `mechanics-concrete-time/`. Den lille Rust-importør kontrollerer de fire originalers SHA-256 og genopbygger tabellerne, kolonneordbogen og optællingen fra regnearkene. Med en midlertidig byggemappe kan kompilatets cache fjernes efter kørslen.

```sh
build_dir=$(mktemp -d)
CARGO_TARGET_DIR="$build_dir" cargo run --locked --manifest-path collector/Cargo.toml -- .
rm -r -- "$build_dir"
```
