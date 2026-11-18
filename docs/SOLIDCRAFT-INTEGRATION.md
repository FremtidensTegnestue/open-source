# Materialevalg og klimaregnskab under tegnearbejdet

Undersøgelsesnotat, 18. november 2026. **Ingen ny integration er implementeret.**

Målet er at markere en bygningsdel i SolidCraft, afprøve alternative løsninger og se virkningen på klimaregnskabet samtidig. Arkitekten vælger frit mellem blandt andet bevaring, reparation, genbrug og nye produkter. Kilder, antagelser og datamangler skal kunne undersøges uden at fylde hele arbejdsfladen.

## Hvad er undersøgt?

Den installerede SolidCraft CLI rapporterer **0.44.1**. Dokumentationen er læst på tagget [v0.44.1](https://github.com/tangency-labs/solidcraft/tree/v0.44.1), commit `e151d5ea6866fb055e011379153fb1cae0566f22`. Der er desuden foretaget læseopslag i en kørende desktop-app. Der er ikke installeret plugins, ændret materialer, åbnet/flyttet paneler eller udløst modelændringer.

| Behov | Fund | Afgrænsning |
| --- | --- | --- |
| Læs det markerede element | `ui.selection` svarede i den åbne app | Aktuel markering kan læses; automatisk besked ved et nyt klik er ikke eftervist |
| Følg modelrevisionen | `document.revision` og `control.subscribe` svarede | Abonnementets oprettelse er prøvet; levering af en hændelse efter en modelændring er ikke afprøvet |
| Læs modeldele | `document.inspect` svarede | Mængdeudtræk og beregning findes allerede i repoets adaptere; den løbende kæde er ikke bygget |
| Fysisk materialevalg | Appen oplyser `material.assign`, `material.create` og `material.inspect` | Kommandofund er ikke afprøvning af ændringer; fysisk densitet er ikke et klimakildevalg |
| Gem egne projektoplysninger | `document.metadata.set` har et dokumenteret navngivet objekt; komponenter har også metadata | Skema og kommandoer er undersøgt; ny persistens og genåbning er ikke afprøvet |
| Brug paneler | `panel.list` svarede med ni registrerede paneltyper | Ingen af de registrerede typer er et eksternt materiale-/klimapanel; layoutstyring er ikke registrering af nyt indhold |

## To vigtige skel

[Kontrolprotokollen](https://github.com/tangency-labs/solidcraft/blob/v0.44.1/docs/control-protocol.md#following-the-design) skelner modelrevision fra markering. At markere noget ændrer ikke modelrevisionen. Et fremtidigt værktøj har derfor brug for både modelopdatering og en forbindelse til markeringen. En intern UI-kobling eller let læsning af markeringen er mulige undersøgelsesspor.

[Plugin-dokumentationen](https://github.com/tangency-labs/solidcraft/blob/v0.44.1/docs/plugins.md) beskriver kommandodialoger med valg af geometri og formularfelter. Pluginet leverer ikke egen UI-kode. Geometrisk forhåndsvisning bruger en midlertidig model og begrænsede rettigheder; den er ikke dokumentation for et vedvarende klimaregnskab. De særskilte `ui`- og `storage`-kapabiliteter beskrives som fremtidige. Den dokumenterede Wasm-flade giver heller ikke en almindelig proces-/netværksbro til Rust-CLI'et.

Et flytbart panel i appens layoutsystem beviser således ikke, at et installeret plugin kan levere vores ønskede panel. Panelindhold og forbindelsen til beregningsmotoren skal afklares særskilt.

## Mulige veje

| Vej | Oplevelse under tegning | Hvad skal afklares? |
| --- | --- | --- |
| Udvidelse af SolidCrafts egen brugerflade | Et vedvarende område følger markeringen og viser alternativer samt reference/variant/forskel | Registrering af indhold, markeringskobling, revisionsbundet beregningsbro og vedligeholdelse på tværs af appversioner |
| Plugin med kommandodialog | Valg kan begynde ved en markeret del | Dokumenteret formularflade dækker ikke alene et løbende parallelt regnskab eller kald til den eksisterende motor |
| Lokal ledsagende visning | Kan bruge kontrolforbindelsen og den eksisterende Rust-motor | Er en særskilt visning; brugbarhed og sammenhæng med SolidCraft skal vurderes i praksis |

Den første vej ligger nærmest målet om direkte integration. Det er en vurdering af målopfyldelse, ikke et valg om nu at ændre eller distribuere SolidCraft. En officiel udvidelsesmulighed bør undersøges, før en særskilt appvariant vælges. Ingen udviklerkontakt er foretaget.

## Et sammenhængende beregningsforløb

En mulig fremtidig kæde er:

1. Markeringen identificerer en bygningsdel eller en udtrykkelig gruppe af legemer.
2. Projektets valg forbinder den med materiale, tilstand og kildegrundlag.
3. En relevant ændring opdaterer mængder og berørte følgeposter.
4. Beregningen knyttes til præcis den model- og valgrevision, den bygger på.
5. Visningen viser elementets og projektets bidrag samt forskellen til referencen. Et resultat fra en ældre revision erstatter ikke det aktuelle.

Tegnearbejdet skal kunne fortsætte under beregning. Tilbagemelding efter et afsluttet greb eller en kort pause kan undersøges sammen med eventuel forhåndsvisning. Respons og belastning af UI-tråden er ikke målt.

Et vindue kan bestå af flere legemer. Valg af en rude må ikke utilsigtet skifte hele facaden eller kun beregne glasset, når kilden dækker et helt vindue. Projektets identitet og mængdesemantik skal følge deling, kopiering, omdøbning og sletning. En standardmaterialeetiket i CAD er ikke i sig selv et tilstrækkeligt kildevalg.

`ft-materials` kan allerede beregne på udtrykkeligt valgte observationer og fastholde dataudgaven. Det eksisterende modelbaserede forløb læser filer; et liveforløb kræver en yderligere bro til den åbne models tilstand. Særlige referenceenheder, transport, drift, udskiftninger og øvrige projektscenarier skal fortsat have passende metoder.

## Spørgsmål før et løsningsvalg

- Kan vi få en understøttet, vedvarende UI-udvidelse i SolidCraft frem for at vedligeholde en separat appvariant?
- Hvordan følger markering og mængder den åbne model uden krav om manuel eksport eller gentagen indtastning?
- Hvilke oplysninger kan være foreløbige i skitsefasen, og hvordan bliver det forståeligt i regnskabet?
- Hvordan opleves valg, sammenligning og fortrydelse ved faktisk tegnearbejde?
- Hvordan følger materialevalg med kopierede eller ændrede modeldele og en genåbnet fil?

Komplette opbygninger skal sammenlignes på samme aftalte funktion, periode og datadækning. Manglende data er ikke nul, og modul D holdes særskilt. Et lavere beregnet bidrag er ikke en teknisk godkendelse. Genbrugslagre, reservation, køb og levering er mulige senere tilkoblinger til det samme vare-/modelgrundlag; de er ikke implementeret i denne undersøgelse.
