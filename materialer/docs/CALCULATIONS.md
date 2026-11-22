# Fra model til materialeberegning

Den leverede arbejdsgang læser faktiske modeller i Solidcraft eller BIMcraft, foreslår navnematches og udfører beregninger på eksplicit valgte kildeobservationer. Originalmodeller og materialedatabase ændres ikke. JSON-rapporter kan bruges direkte af AI-agenter.

## Brug

```sh
python3 materials.py extract examples/models/solidcraft/solid-wood.sc --software solidcraft --out /tmp/model-extract.json
python3 materials.py suggest examples/models/solidcraft/solid-wood.sc --software solidcraft --out /tmp/material-candidates.json
python3 materials.py assess examples/models/solidcraft/solid-wood.sc --software solidcraft --bindings examples/bindings/solidcraft-solid-wood.json --out /tmp/wood-assessment.json
python3 materials.py assess examples/models/bimcraft/controls.bimc --software bimcraft --bindings examples/bindings/bimcraft-controls.json --out /tmp/building-assessment.json
python3 materials.py calculate examples/requests/environmental-1000kg.json --out /tmp/epd-scaling.json
python3 materials.py normalize --value 1 --unit 'lb/ft^3' --dimension density
```

Alle svar og rapporter er JSON. `--db` er et globalt argument før subkommandoen. Exit0 er en gennemført operation; exit1 er en fejl; exit2 fra `assess` betyder, at noget er uafklaret eller kun delvist beregnet. Ved `--out` skrives rapporten atomisk til en `.json`-fil; stdout angiver filsti og status. Kilde-, input- og databasefiler må ikke bruges som output.

Agentvejledning: [material-model-assessment](../.agents/skills/material-model-assessment/SKILL.md). Skillen leveres i repositoryet og er ikke installeret globalt i andre agentklienter.

## Modellernes mængder og materialer

`adapters/solidcraft.py` kalder `solidcraft-cli eval` og læser målte, lukkede kroppes volumen i mm³. Volumen konverteres med1e-9 til m³. Appens standardmateriale bliver ukendt; appens densitet bruges ikke til databaseberegning. Total overflade er en særskilt oplysning, og `area_m2` for referenceareal er ukendt. X/Y/Z-mål er verdensakse-justerede boundingbox-udstrækninger, ikke fiberretning eller nødvendigvis dimensionerne på et roteret emne. Projekt-, STEP- og STP-filer understøttes; kommandoscript-JSON accepteres ikke som en inert model.

`adapters/bimcraft.py` åbner modellen uden at gemme og kalder `inspect` samt pagineret `elements`. Den er verificeret mod CLI0.12.0. Native `.bimc`/`.bimcraft` og en kontrolleret IFC-import er afprøvet. Kun eksplicit homogen materialetildeling opløses. Forskellige materialer i lag bliver uafklarede frem for at få tildelt hele elementets volumen hver især.

BIMcraft0.12.0 rapporterer gulvvolumen med trin0,001m³. Den observerede regression viser0,0048m³ som0,005m³. Adapteren bevarer den rapporterede værdi og trinnet. Beregningsrapporten angiver en afrundingsgrænse på±0,0005m³ omsat til masse og klima, når disse skalerer med volumen. Det er kun modelafrundingens bidrag og ikke et samlet statistisk usikkerhedsinterval for materialedata. Andre kategorier eller filer kan have yderligere mængde-/importbegrænsninger; se advarsler og kilden til mængden.

Mængderne er programafledte. En præcis mængde beviser ikke, at modellen eller materialevalget svarer til det faktisk byggede. Importadvarsler og udeladt indhold gør det samlede resultat delvist. Afrundingsmeddelelser er notices med eksplicit talmæssig grænse.

IFC-importens særskilte oversigt bevares i `extraction.import_summary`, inklusive `skipped`, `generic` og `moved`. Udeladte eller generisk importerede entiteter giver selvstændige advarsler; en tom `inspect.warnings` er ikke bevis for en komplet import. Afprøvningen på [Lisbjerg Bakke](../reports/lisbjerg-bakke/README.md) viser også, at den undersøgte CLI ikke udstiller nettovolumen for alle kategorier. Rumvolumen og åbninger er ikke materialemængder. Manglende volumen i CLI’en må ikke sidestilles med manglende original IFC-geometri.

### Overførsel fra Solidcraft til BIMcraft

[Det samlede eksempel](../examples/integrated-workflow/README.md) er afprøvet med Solidcraft GLB-eksport, BIMcraft `import_mesh`, materialeberegninger og en geometrisk returkontrol. To modelversioner med tre dele er kontrolleret mod analytiske mål og original Excel. Geometrien bliver ikke genskabt i BIMcraft; mængderne beregnes fra BIMcrafts faktiske familietrekanter.

`extract`, `suggest` og `assess` accepterer nu `--mesh-quantities` for BIMcraft. Standardadfærden er uændret. Tilvalget læser de refererede familiedefinitioner i batches og kan beregne volumen for manglende mængder på en snæver, verificeret type af generisk mesh-komponent. Én uparameteriseret meshform i standardreferenceplanet kræves. Trekanterne kontrolleres for endelige koordinater, degenererede flader, sammenhæng, lukning og konsistent fladeretning før volumenintegration i SI-enheder. Ikke-understøttede forhold giver `unsupported_mesh_quantity` og manglende volumen. `area_m2` udledes ikke af total overflade.

Mængdens `source_ref` angiver meshmetode, kildeformens GUID, trekantsantal, svejsetolerance og grænser. Selvskæring kontrolleres ikke generelt, og tessellering er ikke den oprindelige CAD-geometri. Materialet læses kun fra formens eksplicitte tildeling; en beregning kræver stadig en særskilt databasebinding. GLB-materialenavne kan være visuelle etiketter og beviser ikke et bestemt produkt eller egenskabssæt.

Eksemplet bruger et nyt BIM-projekt for hver CAD-revision, da gentagen `import_mesh` tilføjer nye komponenter. GLB-returen bevarer den målte geometri i forsøget, mens CAD-parametre og historik forbliver i `.sc`-originalen; fysiske standardmaterialer på returmodellen bruges ikke som datagrundlag.

## Eksplicit binding mellem model og database

Forslag fra `suggest` er tekstmatches, ikke godkendte produkter. Brug `show MATERIAL-ID`, `observations --material MATERIAL-ID` og `sources --id SOURCE-ID` til at undersøge kilderne.

Et bindingsdokument følger denne struktur; erstat pladsholderne med faktiske værdier:

```json
{
  "schema_version": 1,
  "model_sha256": "CHECKSUM-FRA-EXTRACT",
  "elements": {
    "ELEMENT-ID": {
      "material_id": "DATABASE-MATERIAL-ID",
      "model_material_name": "PRÆCIST-NAVN-FRA-MODELLEN",
      "selection_note": "Begrund valg af konkret kilde og eventuelle scenarieantagelser",
      "operations": ["mass", "climate"],
      "density_observation_id": "DENSITETSOBSERVATION-ID",
      "gwp_observation_ids": ["KLIMAOBSERVATION-ID"]
    }
  }
}
```

Modelhash og materialenavn kontrolleres ved brug. Kildeobservationerne skal tilhøre den valgte databasepost. Hvis der bruges arealbaseret klima, skal `area_basis_note` desuden dokumentere, hvorfor modellens rapporterede areal svarer til kildens referenceareal. Et ændret eller manglende materiale og manglende bindingsgrundlag giver ingen opdigtet beregning.

Bindingsdokumentet er et eksplicit datavalg. Værktøjet kræver en begrundelse, men certificerer ikke brugerens produktækvivalens eller kildeværdiernes faglige anvendelighed. De leverede kontrolbindinger er tydeligt mærkede referencescenarier.

## Leverede metoder

### Masse

`mass_kg = volume_m3 × density_kg_m3`.

Densitet skal være egenskaben `density` og have en kendt enhed. Arealvægt eller uklar enhed kan ikke bruges som densitet. Resultatet indeholder både originalværdi, SI-konvertering og kildelokation.

### Klimabidrag

`bidrag = kildeværdi × enhedsfaktor × faktisk_mængde / deklareret_mængde`.

Metoden gælder én valgt GWP-indikator og ét kildeangivet livscyklusmodul ad gangen. Den understøtter eksplicitte referencegrundlag i masse, volumen eller areal. “1ton” er1000kg efter den dokumenterede metriske konvention. ILCD-felter som `declared_unit=kg` og `conditions.declared_amount=1000` understøttes, når kildehenvisningerne er entydige; udvekslingens `meanAmount=1` bruges ikke som erstatning.

Alle angivne referencebeløb og -enheder skal stemme overens efter enhedsomregning. Hvis `declared_unit` siger `1 kg`, mens kildekonteksten siger `1000 kg`, afvises beregningen. Programmet vælger ikke automatisk den ene oplysning. `1 ton` og `1000 kg` kan derimod beskrive samme reference. Sammenligningen tillader kun en relativ forskel på 1e-12 for numerisk afrunding ved omregning. Et normaliseret referencebeløb skal være endeligt og større end nul; en tom eller blank modulangivelse giver ingen klimaberegning.

Python og Rust afprøves mod de samme [48 testtilfælde](../tests/fixtures/climate-scaling.json): masse, volumen og areal, CO₂-enheder i gram/kg/ton, 1000kg-referencen, negative produktions-/D-værdier og afvisning af modstridende, manglende eller uegnede input. Numerisk over-/underløb giver en fejl; en meget lille, ikke-nul påvirkning må ikke blive et falsk nul. En udtrykkelig nulværdi eller nulmængde kan fortsat give nul. Testenes tal er særskilte regne- og afvisningskontroller, ikke dokumentation for produktækvivalens eller en fuld bygnings-LCA.

Der dannes ingen global sum, som blander produktionsfase, delmoduler, modul D, forskellige indikatorer eller metoder. EPD-betingelser som R-værdi eller år accepteres ikke som et simpelt arealgrundlag. Installationsfaktorer kræver deres egen metode og kan ikke anvendes som en produktdeklaration.

### Træets fugtbevægelse

USDA Wood Handbook2021, kapitel13, trykt side13–16, ligning13–3:

`ΔD = D_initial × C_retning × (MC_slut − MC_start)`.

Kilden ligger i `data/raw/wood/chapter_13.pdf`; koefficientens citation og originalfilhash følger rapporten. `1/%MC` er pr. procentpoint træfugt og beholder talværdien ved konvertering. Begge fugttilstande skal ligge inden for observationens gyldighedsinterval, i de anvendte tabel13–5-værdier6–14%. Metoden er et kildebeskrevet overslag, ikke en måling af det konkrete emne.

Vælg `operations=["moisture"]` og et `moisture`-objekt med `coefficient_observation_id`, `dimension_axis` (`x`/`y`/`z`), `direction` (`radial`/`tangential`), `initial_moisture_percent`, `final_moisture_percent` og en eksplicit `orientation_note`. Se det kørende eksempel i `examples/bindings/solidcraft-moisture.json`. Dimensionen i dette eksempel er en kendt, akseret brætbredde. Adapteren udleder ikke fiberretning, og CLT antages ikke at have egenskaberne for en råtræsart.

## Enhedskonvertering

`material_units.normalize` bruger eksplicitte aliaser og faktorer. Understøttede dimensioner er masse, længde, areal, volumen, densitet, varmeledningsevne, specifik varmekapacitet, arealbaseret varmemodstand, dimensionsløs værdi og fugtkoefficient. Ukendte/tvetydige enheder og dimensionsfejl afvises. Originaldatabasen er uændret; konverteringerne fremgår af resultaterne.

Btu betyder International Table Btu. Ton betyder metrisk ton i dette danske interface. Termisk resistivitet i m K/W er ikke arealbaseret varmemodstand i m²K/W. Fulde faktorvalg og NIST-kildehenvisninger findes i `material_units.py`.

## Verifikation og eksempler

```sh
python3 examples/run_controls.py
python3 -m unittest discover -s tests -v
```

`examples/reports/validation-summary.json` dokumenterer10 reelle modelcases: fem fra hver app med træ, beton, stål, glas og isolering. Den uafhængige reference beregner rektangulære kontrolvolumener fra de forfattede mål og læser densitet/GWP direkte i den originale BR18-Excel-fil. Der kontrolleres10 vægtresultater og40 separate modulresultater.

Derudover testes en faktisk Solidcraft-hvidædelgransmodel mod USDA-eksemplet:232mm,8→11% træfugt og tangentielt C0,00245 giver1,7052mm ændring. En original ÖKOBAUDAT-observation kontrollerer deklareret grundlag på1000kg. Manglende og blandede materialer, kildefilsændring, tvetydige enheder og andre fejltilfælde har egne kontroller.

Kontrolmodellerne er homogene mængdeprøver med eksplicit valgte referencedatasæt. De repræsenterer ikke en fuldt projekteret bygning eller verificeret udførelse af glasbyggesten, valsede profiler eller andre produkter. Den brede materialedækning fortsætter; kontrolcases fastlægger ikke en permanent afgrænsning.
