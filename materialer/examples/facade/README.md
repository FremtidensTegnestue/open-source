# Facade: ændr i SolidCraft, følg mængder, klima og overslag

Første fungerende, afgrænsede liveforløb. SolidCrafts egne parametre styrer en åben facadeprøve. En lokal Python-proces følger modelrevisionen, måler geometrien gennem den dokumenterede kontrolkanal og bruger den installerede Rust-motor til kildebaseret klima samt `pricing.py` til egne overslag. Regnskabet vises i en lokal browser ved siden af SolidCraft. Der installeres ikke et panel eller et nyt modelleringsrum.

Afprøvet på macOS med SolidCraft **0.44.1**, Python **3.9** og en versionsbundet `ft-materials` **0.3.0**. Andre værtsversioner kræver egen kontrol. Rust-programmets hash og dataudgaven fastholdes; et versionsnummer alene identificerer ikke programmet. Denne lokale prøve er ikke en uafhængig nybrugeraccept eller en færdig generel bygningsintegration.

## Opret et projekt

Kør fra `materialer/`, efter at Rust-programmet og de relevante materialedata er installeret. Erstat stier og data-ID med din installation. `--snapshot` skal være et fastholdt ID; en ny dataudgave aktiveres ikke af disse kommandoer.

```sh
python3 facade.py /sti/til/nyt-facadeprojekt \
  --engine /sti/til/ft-materials \
  --store /sti/til/datalager \
  --snapshot u2-DIN-FASTHOLDTE-DATAUDGAVE \
  --solidcraft-cli /sti/til/solidcraft-cli
python3 facade_live.py /sti/til/nyt-facadeprojekt/projekt.json
```

Første kommando skriver en selvstændig `facade.sc`, `model-script.json` og `projekt.json` i en tom mappe. Den ændrer ikke den åbne model. Åbn `facade.sc` i SolidCraft og browseradressen fra anden kommando. Proces og SolidCraft skal køre, mens du arbejder. Et statisk regnskab er ikke live, når processen er stoppet.

`model.json` i denne mappe er også en faktisk gemt, anonym eksempelmodel, som kan åbnes uden genopbygning. Dens projekt-ID er `example-facade`; brug projektoprettelsen til din egen adskilte projektidentitet.

Hvis flere SolidCraft-instanser kører, kan `projekt.json` angive `control_port` for den ønskede, dokumenterede lokale kontrolkanal. Kontrollér først, hvilken instans der har det synlige dokument. Processen fastholder porten ved start og følger ikke en senere ændring af `current.port`. Token læses i hukommelsen fra værtens beskyttede kontrolmappe og gemmes ikke i projektet eller rapporterne. En anden projektidentitet giver ingen tal. Ved genstart af appen kan forbindelse/port skulle afstemmes.

## Ret modellen

I SolidCraft: **Model → Parameters**.

- `Beklaedning`: **0** skifer, **1** træ. Config Table indeholder også de to materialevalg; ingen forberegnede resultatceller bruges.
- `Facade_bredde`: 1200–2400 mm. `Facade_hoejde`: 1800–3000 mm.
- `Trae_tykkelse`: 18–32 mm. `Krydsfiner_tykkelse`: 18–22 mm.

Prøven har fem stolpelinjer, otte skiferlægter og en fast opdeling i 32 visningssten eller16 brædder. Mål ændrer både delene og deres placering. Det er en afgrænsning af vores mængderegler, ikke dimensionering, godkendte spænd eller et valgt handelsformat. Nye åbninger, ændret opbygning, ubundne legemer og andre kildematerialer kræver en ny afstemning; systemet skal ikke gætte.

Regnskabet følger også Fortryd/Gentag og en gemt/genåbnet model. Koblingen bruger dokumentets projekt-ID og feature-ID'er, så almindelig omdøbning af et legeme bevarer den logiske gruppe. Både native volumen og uafhængige mængderegler kontrolleres. En ny ukendt del, forkert materiale, fejl eller en anden aktiv projektmodel skjuler resultatet med en forklaring. Svar fra en tidligere modelrevision vises ikke som aktuelle.

## Pris og arbejde

Alle priser starter som **ukendte**. Der følger ingen aktuelle leverandørpriser med. `-1` betyder ukendt; `0` betyder et udtrykkeligt nul. Indtast kun egne dokumenterede overslag:

- `Pris_skelet_m`, `Pris_ventlaegte_m`, `Pris_skiferlaegte_m`: DKK/m for det angivne tværsnit.
- `Pris_krydsfiner_m2`, `Pris_vindplade_m2`, `Pris_skifer_m2`, `Pris_trae_m2`: DKK/m². Træ bruger faktisk brætareal uden fugerne; skifer bruger dækket kontur efter kildens reference.
- `Pris_skruer_stk`, `Pris_clips_stk`: DKK/stk. Skruer grupperes før prisberegning, så samme køb ikke tælles to gange.
- `Timer_skifer_pr_m2`, `Timer_trae_pr_m2`: egne antagne **persontimer pr. m² facade**. Samlet arbejde følger arealet; produktiviteten er en indtastet antagelse, ikke et markedsestimat.
- `Timepris`: faktureret DKK/persontime ekskl. moms. `Levering`: samlet DKK for denne prøve, vist én gang.
- `Prisgrundlag` og `Pris_dato`: ærlig beskrivelse og dato for overslaget. Der kræves ikke en opdigtet webadresse.
- `Pris_trae_gaelder_mm`, `Pris_krydsfiner_gaelder_mm`: den tykkelse, din pris gælder. Ændret tykkelse gør posten uafklaret, indtil pris og tykkelsesgrundlag er afstemt.

Prisberegningens vurderingsdato er den indtastede `Pris_dato`; der foretages ikke automatisk markedstjek eller genberegning alene ved et datorskift. Alle beløb er **ekskl. moms**. Indkøbstillæg er eksplicitte scenarier, som kan justeres. Uoplyste beløb eller timer bevarer en uafklaret prognose. Denne forbindelse opretter kun interne skøn via en lukket kontrakt; den modtager ikke eksterne tilbud, ordredata eller aftaler. De tre dokumenterede generelle tilbuds-/ordrebegrænsninger i [reviewet](../../docs/REVIEW-2026-11-20.md) er derfor ikke løst eller aktiveret som en del af facadeforløbet.

## Klima, reference og gemning

Kilderne er fem eksplicit valgte BR-referenceposter fra det fastholdte datalager. Hvert nyt relevant mængdeinput sendes til Rust; samme gyldige input kan genbruge sit kilde-/versionsbundne resultat i hukommelsen. Ingen interpolation mellem skifer og træ bruges. Kilder, mængdeenheder og kildebaseret densitet følger rækkerne. D vises særskilt under kildedetaljerne.

Overblikket er en **kendt materialedelsum A1–A3+C3+C4**, ikke fuld LCA. A4/A5, behandling, vedligehold, udskiftninger, energi og indkøbstillæggets klimafølger er åbne. Stålplade er proxy for fastgørelser, og konstruktionstræ er proxy for ubehandlet træbeklædning. Skiferens CAD-masse bruges ikke til at erstatte kildens dækningsareal. Fælles skrueantal og fastgørelsesmasser er tydeligt antagne prøveværdier. Der er ikke beregnet brand, fugt, statik eller et opvarmet rums ventilation.

Første gyldige aflæsning fastholdes som reference. **Brug dette som reference** erstatter den eksplicit. Et ændret areal markeres som ændret omfang, og ny prisdækning behandles særskilt fra en besparelse. **Gem modelkopi og regnskab** skriver `gemt-model.json` og `gemt-regnskab.json` særskilt. Modelkopien kan åbnes i SolidCraft og genberegnes; den ændrer ikke den aktive model. Brug også SolidCrafts egen **Gem** til din arbejdsfil.

Referencefiler er bundet til programkode og projektkonfiguration. Ændret kode, motor, manifest eller projektgrundlag kræver afstemning/genstart frem for skjult fallback. En sessionrevision er ikke en gemt fils kontrolsum. Browseren kontrollerer den aktive modelrevision, før et resultat kaldes aktuelt, og en forældet gemmeanmodning afvises. Visningen er én lokal brugers forløb, ikke flerbrugerredigering.

## Overblik, sammenligning og projektgrundlag

Visningen har tre indgange: **Overblik**, **Sammenlign** og **Mål og grundlag**. Den starter med den kendte klimadelsum, bidrag pr. m², prisstatus og højst tre næste handlinger. Kilder og øvrige mangler foldes ud efter behov. Sammenlign viser reference, aktuelt omfang og bidrag pr. m²; ændret areal er fortsat en ændret opgave.

Under Mål og grundlag kan du gemme et budget ekskl. moms og et mål for **den viste materialedelsum**. Et ukendt prisoverslag giver ingen påstand om overholdt budget. Antal prissatte poster er ikke økonomisk dækning. Et klimamål er ikke en dokumenteret bygningsgrænse eller overholdelse af klimakrav.

Betragtningsperiode og levetid pr. aktiv materialepost kræver eget kilde-/antagelsesgrundlag. Visningen beregner mulige udskiftningsår inden for perioden, uden automatisk hændelse ved slutøjeblikket. Eksempel: 50 år/25 års levetid giver år 25. **Udskiftningernes klima, pris, adgang og følgearbejde beregnes endnu ikke.** Levetid er ikke garanti. Tom periode eller levetid forbliver ukendt; der medfølger ingen standardperiode.

Grundlaget indeholder 16 områder med konkrete afklaringer, blandt andet arkitektur/brug/adgang, sted/fundering, produkter, transport/spild, levetid, energi, bæring, brand, fugt, lyd, ventilation, dagslys, installationer, bevaring/genbrug, leverancer og drift. DfD vises kun ved udtrykkeligt tilvalg. Status **grundlag registreret** eller **ikke relevant med begrundelse** kræver et notat/en reference; ingen af dem betyder teknisk godkendelse. Kun relevante faglige beregninger og dokumentation kan eftervise et forhold.

Indtastninger gemmes separat i `maal-og-grundlag.json`, med revision og uden ændring af CAD eller materialernes klimatal. Skift af valgt post i formularen er ikke et beregningsinput. Formularen skal gemmes eller fortrydes, før samlet model-/regnskabssnapshot gemmes. En forældet formularrevision eller ekstern filændring afvises frem for at overskrive ubemærket. Genstart indlæser den gemte fil; afstem ændrede data før videre brug. Projektfiler kan indeholde private notater og priser og skal ikke automatisk publiceres med kodeeksemplet.

Pris-/arbejdsfelterne har læsbare forklaringer her, men indtastes fortsat i SolidCrafts Parameters. De kan endnu ikke ændres direkte i ledsagervisningen. Se [gennemgangen og næste forbedringer](../../docs/DESIGN-TOOL-REVIEW-2026-11-21.md).

## Kontrol

```sh
python3 -m unittest discover -s tests -p 'test_facade*.py' -v
python3 -m unittest discover -s tests -p 'test_pricing*.py'
```

Native geometritests kræver den afprøvede CLI; `SOLIDCRAFT_CLI` kan vælge den eksplicit. På macOS foretrækkes appens CLI frem for en ældre terminalinstallation. En manglende CLI gør de native tests sprunget over, ikke bestået. Testfaktorerne i enhedstests er ikke klimadata; den faktiske liveprøve skal desuden køres med den fastholdte Rust-motor og dokumenteres i det konkrete projekt.
