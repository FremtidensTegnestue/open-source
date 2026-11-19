# Miljødata: ÖKOBAUDAT

## Indsamlet primærkilde

Dette datasæt arkiverer det offentlige ÖKOBAUDAT soda4LCA-register og de tilhørende **originale udvidede JSON-datasæt**. JSON er leverandørens publicerede maskinlæsbare primærformat; filerne er gemt uden ændringer, med HTTP-metadata, hentetid og SHA-256.

- Register: <https://oekobaudat.de/OEKOBAU.DAT/resource/processes?format=json>
- Individuel kilde: `.../processes/<UUID>?format=json&view=extended&version=<version>`
- Officiel dokumentation og vilkår: <https://oekobaudat.de/en/guidance/data-users.html>
- Originalfiler: `data/raw/environmental/oekobaudat/`.
- Registrerede datakilder og udtræk: `data/staging/environmental/`.

Der hentes hele den tilgængelige procesoversigt via sider af 500 poster, og alle forskellige `(UUID, version)` hentes. Der vælges ikke kun træ, facader eller et lille udvalg af materialer. Processer kan omfatte produkter, generiske materialer, konstruktioner, energiforsyning, transport og affaldsbehandling; antallet af datasæt er derfor **ikke** antallet af unikke rene materialer eller danske produkter. Geografisk anvendelighed fremgår af hvert datasæt og skal vurderes konkret.

Databasen er levende. Registerets rapporterede total er antal rækker på hentetidspunktet, mens det lokale antal er forskellige `(UUID, version)` fra de faktisk hentede registerfiler. Eventuelle dubletter eller ændringer under paginering må ikke fortolkes som yderligere materialer. Alle rå registersider er bevaret, så dækningen kan efterprøves.

## Hvilke værdier udtrækkes?

1. Alle numeriske, modulopdelte LCIA-indikatorer fra `LCIAResults/LCIAResult`: klima, forsuring, eutrofiering, ozon, ressourcepåvirkning, vand og andre indikatorer, når kilden indeholder dem.
2. Alle numeriske modulopdelte resource-/affalds-/energiudvekslinger fra `exchanges/exchange/.../other/anies`.
3. Eksplicit strukturerede `materialProperties` såsom densitet, når de findes.
4. Referenceflowets rapporterede flowegenskaber og måleenheder.

Hver observation har en præcis **JSON Pointer** til den originale værdi, original tekst, numerisk værdi, kilde-ID, enhed, metode-/flow-ID, livscyklusmodul, deklareret grundlag og betingelser. JSON Pointer bruger nulbaserede arrayindekser. Negative værdier bevares. Eksplicitte nulværdier er nul; `MND`, manglende værdier og andre markører bliver ikke nul og registreres i `unparsed-values.jsonl`.

LCIA-metodernes UUID'er bevares, så ældre GWP-metoder og nyere GWP-total/fossil/biogenic ikke automatisk sidestilles. Egenskabsnavnet er en søgevenlig etiket, ikke en erklæring om metodisk sammenlignelighed.

## Deklareret enhed og beregningsgrundlag

Et EPD-resultat gælder kildens deklarerede mængde. Denne kan eksempelvis være **1.000 kg**, selv om referenceflowets `meanAmount` er `1`. Udtrækket bruger den eksplicitte referenceflowegenskabs `meanValue` og `referenceUnit` og bevarer desuden alle underliggende referenceoplysninger i `conditions.declared_references`. Hvis referencegrundlaget ikke kan aflæses entydigt, forbliver det uafklaret frem for at blive opfundet.

`unit` er tælleren i det rapporterede resultat, eksempelvis kg CO2-eq. `declared_unit` og `conditions.declared_amount` beskriver nævneren/grundlaget. Der foretages ingen omregning til “pr. kg”, “pr. m²” eller dansk bygningsresultat. Rå enheder som `qm`, `pcs.` og `kg/m^3` bevares i stedet for at blive stiltiende normaliseret.

A1-A3, A1, A2 og A3 bevares som særskilte kildeangivelser og lægges aldrig ukritisk sammen. Modul D holdes særskilt. Scenarieattributter fra den enkelte værdi bevares. Der beregnes ingen totalsummer eller sammenlignende miljøkonklusioner i dette udtræk.

## Rettigheder og kildeangivelse

ÖKOBAUDATs officielle brugerinformation tillader gratis videreformidling af uændrede data med kildeangivelse. Den originale vilkårsside er gemt i `data/raw/environmental/terms/oekobaudat-data-users.html`. Originale procesfiler er derfor bevaret særskilt fra de afledte databaseposter.

Den enkelte kildes `licenseType`, `copyright`, `accessRestrictions`, ejer og programoperatør registreres også. Status `verified` betyder her, at en kildeangivet licenstekst er fundet og bevaret; den er ikke en ny juridisk vurdering. Ukendte og andre licensangivelser markeres særskilt. Datamængden tildeles ikke automatisk MIT eller en anden fælles licens.

ECO SMDP/ECO Portal blev undersøgt, men er **ikke** bulk-importeret: de aktuelle ECO-vilkår kræver API-licens og begrænser videreformidling/dekonstruktion til nye dataprodukter. At et endpoint svarer uden login fastslår ikke rettigheder til videreudgivelse. Se den bevarede `eco-platform-terms.html` og <https://www.eco-platform.org/terms-conditions.html>.

## PDF'er og øvrig dokumentation

De publicerede JSON-datasæt er originale kilder til de importerede tal. Refererede EPD-PDF'er og andre bilag er registreret med adresse og præcis kildehenvisning i `attachments.jsonl`, men er **ikke alle downloadet**. Det gælder også tekniske egenskaber, der kun står i prosa eller billeder. Datasættet må derfor ikke beskrives som et fuldt PDF-arkiv eller en komplet teknisk produktdatabase.

## Reproduktion

Kør kommandoerne fra mappen `materialer`.

```sh
python3 collectors/environmental.py --provider oekobaudat
```

Kommandoen genbruger det eksisterende kildesnapshot. For at hente nye registerversioner:

```sh
python3 collectors/environmental.py --provider oekobaudat --refresh-index
```

Versionsbestemte procesfiler genbruges. Et helt nyt snapshot bør arkiveres separat, hvis tidligere registerversioner skal bevares. Genudtræk uden nye procesdownloads:

```sh
python3 collectors/environmental.py --provider oekobaudat --offline
```

Collectorens kildekode bruger Python-standardbiblioteket, fire samtidige hentninger som udgangspunkt, timeout og retries. Stagefilerne skrives fra bunden ved genkørsel. Kør ikke samme collector samtidigt mod samme mappe.

## Kontroller og kendte begrænsninger

- Originalfiler har SHA-256 og præcise URL'er; root-databasebyggeren kan kontrollere dem igen.
- En referencekontrol på en EPD med 1.000 kg deklareret enhed sammenholder samtlige 299 observationer med deres originale JSON-værdier.
- Kontrollen efterprøver også bevarelse af negativt modul D og skelnen mellem nul og `MND`.
- Udløbne historiske datasæt bevares sammen med `reference_year` og `valid_until`; dette er ikke et register kun over aktuelt gyldige EPD'er.
- Materialefamilie er en navigationsklassifikation udledt af registertekst, ikke en ny certificeret produkttaksonomi.
- Duplikater på tværs af registre/versioner må ikke sammenlægges uden identitets- og metodekontrol.
- Udtrækket udfører ingen bygnings-LCA, dokumenterer ikke automatisk BR18-overholdelse og opfinder ingen manglende materialetal.

Se `data/staging/environmental/summary.json` for faktiske antal, dækning, egenskaber, livscyklusmoduler og fejl.
