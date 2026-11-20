# Hvilke oplysninger vil vi have om et byggemateriale?

Vi vil kunne følge et materialevalg fra den første skitse til den dag, en bygningsdel skal vedligeholdes, udskiftes eller genbruges. Målet er, at en arkitekt kan slå et produkt op og få svar på *hvad det kan, under hvilke forhold, og hvor vi ved det fra*. SolidCraft, BIMCraft og en agent skal kunne bruge de samme oplysninger.

[Feltkataloget som tabel](MATERIALEFELTER.tsv) definerer **169 felter og gentagelige feltgrupper inden for 19 områder**. Hver række angiver felt-ID, dansk navn, hvad det gælder for, værdiform, enhed eller referencegrundlag samt definition og betingelser. Tabellen kan åbnes som en tabulatorsepareret UTF-8-fil i et regneark.

## Mål og efterprøvning

Målet er, at arkitekten kan vælge et materiale eller en modeldel, få de dokumenterede værdier, finde originalen og se, hvilke oplysninger der stadig skal fremskaffes. Rust-CLI’et indlæser tabellens 169 rækker som den fælles feltordbog. Der kan være mange observationer for ét felt. En families egenskaber, en produkttest, et projekteret valg og en registrering af det faktisk monterede produkt har forskellige anvendelsesområder.

| Hvad skal være opfyldt? | Sådan kan det kontrolleres i mekanikudgaven |
| --- | --- |
| Alle felter har en dansk definition og et oplyst niveau, værdiform og grundlag | `ft-materials fields` giver 169 definitioner fordelt på 19 områder. |
| Hvert udsagn kan følges til et bestemt emne og en præcis kilde | `facts ID --field FELT` viser posterne. `source KILDE_ID` viser originalens adresse, kontrolsum og rettigheder. Ukendte felt-, materiale- og kilde-ID’er afvises ved import. |
| Mangler og konkurrerende tal er synlige | `coverage --material ID` viser feltdækningen for den enkelte post. En målt nulværdi og en udokumenteret egenskab har forskellige statusser. |
| Levetid og vedligehold kan bruges i praksis | Der findes tal fra både produktdeklarationer, producentvejledninger, forsøg og generiske scenarier. Handling og hyppighed forbindes via opgavens ID og komponent i dens betingelser. |
| Begge modelprogrammer kan finde den samme dokumentation | LinCrete-eksemplet kontrollerer to levetidsudsagn fra den samme kildeversion på en faktisk SolidCraft-krop og dens tilsvarende BIMCraft-element. |

[Offentlig dækning felt for felt](../data/releases/coverage-public-mechanics-2026-11-20.json) · [Udvidet lokal dækning](../data/releases/coverage-local-mechanics-2026-11-20.json) · [Modeltesten](../examples/model-fields/README.md)

## Hvad skal en ny post som minimum fortælle?

- **Hvad taler vi om?** Identitet, navn, type og omfang. Stilkeg er en træart. En bestemt lakeret egeplanke er en produktvariant, og et gulv med underlag og bjælker er en opbygning. En prøve eller et bestemt parti kan have egne målinger.
- **Hvad siger kilden?** Hver observation peger på én præcis egenskab på én post. Gem original værdi, enhed eller klassifikationsskala, mængdegrundlag og relevante betingelser. Bevar flere målinger og modstridende kilder side om side. Ukendt, ikke deklareret og målt nul har hver deres betydning.
- **Hvor kan vi kontrollere det?** Udgiver, originaldokument, udgave, konkret side, tabel, celle eller datapunkt samt kildefilens kontrolsum, når originalen er tilgængelig. Registrer brugsret, tilgængelighed og datastatus. Ved beregninger gemmes også de valgte observationer, dataudgave, formel og modelrevision.

En ny materialefamilie kan tilføje flere egenskaber med egen definition og enhed. Udfyld det, som er relevant og dokumenteret. Familien kan bruges til at finde kandidater. Overførsel af en egenskab fra en prøve til et produkt eller fra en komponent til en hel konstruktion kræver et dokumenteret grundlag. Eksterne ordbøger kan give fælles identifikatorer for præcist definerede egenskaber. [buildingSMART Data Dictionary](https://www.buildingsmart.org/users/services/buildingsmart-data-dictionary/)

## Hvad vil vi vide?

| Område | Hvad skal en arkitekt kunne slå op? |
| --- | --- |
| Identitet, sammensætning og relationer | Materiale, producent, variant, oprindelse, behandling, bestanddele, lag og den præcise vare eller prøve. |
| Kilder og dokumentation | Hvem der har oplyst tallet, hvordan det er bestemt, gyldighed, rettigheder, usikkerhed, produktblad, prøvning og eventuelle certifikater. |
| Geometri og mængder | Formater, tolerancer, dækmål, stykvægt, masse pr. meter eller m², densitet, porøsitet og forskellen mellem indkøbt og indbygget mængde. |
| Fugt, vand, varme og luft | Vandoptagelse, tørring, dampmodstand, tæthed, fugtbevægelser, varmeledning, varmekapacitet, varmeudvidelse og varmetab gennem en opbygning. |
| Mekanik og holdbarhed | Styrke og stivhed i relevante retninger, fastgørelser, bevægelse over tid, slid, frost, korrosion og biologisk nedbrydning. |
| Brand, lyd, lys og overflade | Brandreaktion, en opbygnings brandmodstand, lydisolering, absorption, trinlyd, dagslys, solvarme, farve, glans, tekstur og skridsikkerhed. |
| Sundhed, kemi og indeklima | Stofindhold, emissioner, udvaskning, arbejdsmiljø og analyser af problemstoffer ved renovering. |
| Tekniske installationer | Flow, tryktab, kapacitet, effekt, virkningsgrad, elektriske egenskaber, installationsstøj samt energi- og vandforbrug ved et givent driftspunkt. |
| Klima, miljø og ressourcer | For hver deklareret enhed og livscyklusfase vil vi bevare hver publiceret indikator, dens enhed, scenarie og metode, herunder klima, vand, energi, råstoffer, affald og udgående materialestrømme. |
| Indkøb, udførelse og økonomi | Leverandør, sted og dato for priser, handelsformat, leveringstid, transport, montage, underlag, spild, arbejdstid samt omkostninger til drift og udskiftning. |
| Levetid, drift og reparation | Hvilken del der holder hvor længe, hvad der begrænser dens brug, hvilke opgaver der følger med, hvornår de udløses, og hvilke ressourcer de kræver. |
| Demontering og genbrug | Hvordan delene skilles ad, hvad der kan reddes, hvilket udbytte der forventes, og hvad en konkret genbrugsvare har af dokumenteret tilstand og restlevetid. |
| SolidCraft, BIMCraft og det udførte byggeri | Hvilket legeme, element eller lag materialet er valgt til, hvor mængden kommer fra, hvilket produkt der faktisk blev monteret, og hvilke kildeværdier den aktuelle beregning bruger. |

## Hvad betyder »levetid og vedligehold« i praksis?

Der kan være flere levetider for den samme bygningsdel. En træbeklædning, dens maling og dens beslag kan hver have forskellige perioder, betingelser og opgaver. Derfor skal en post kunne have flere levetidsudsagn og flere driftsopgaver.

| Post | Det vil vi registrere |
| --- | --- |
| Levetidsudsagn | Del og funktion, type af levetid, antal år eller brugscyklusser, interval/usikkerhed, referenceforhold, forudsat vedligehold og kriterium for endt brug. Garantiperiode og dokumentets gyldighed har selvstændige felter. |
| Driftsopgave | Hvilken del, hvilken handling, grundlag, første forfald, gentagelse eller tilstandsudløser, metode, adgang, kompetence og forbrug pr. gang. |
| Reparation eller udskiftning | Hvad kan skiftes separat, hvor stor en andel, hvilke nabodele berøres, hvad kræver adgangen, og hvilke mængder, udgifter og miljøbidrag følger af indgrebet? |
| Installeret eksemplar | Parti, monteringsdato, placering, faktisk tilstand, udført vedligehold, observerede skader og dato for vurdering af restlevetid. Dette hører til projektet. |

**Eksempel fra en rigtig glasdør.** DEKO DG-deklarationen anvender en referencelevetid på 30 år, rengøring tre gange om året og smøring af hængsler én gang om året. I kataloget hører det hjemme som ét levetidsudsagn og to opgaver med hver sin frekvens. Alle tre får kildearten *EPD-scenarie*. Klimatallet for vedligehold registreres særskilt med modul og deklareret mængde. En eventuel driftsvejledning kan føjes til med sin egen udgave og egne anvisninger. [DEKO, side 10](https://www.epddanmark.dk/media/5rpm3ale/md-24069-en.pdf#page=10)

## Hvordan bruges felterne i en model?

Når SolidCraft måler et bræts bredde, kommer bredden fra geometrien. Til beregning af fugtbevægelse skal vi desuden kende træart, retning i forhold til årringene, start- og slutfugt og en koefficient, der gælder i det interval. Analogt kan BIMCraft finde alle døre af en bestemt type i et projekt. Før agenten kan opstille en driftsplan, skal den kende valgt produkt, opgaverne, ibrugtagningstidspunktet og projektets beslutning om, hvilke anvisninger der gælder. Et manglende input skal kunne fremgå af svaret.

Driftsopslagene omfatter blandt andet DEKO-døre og RotationVent. En EPD kan opstille en fast intervalantagelse, mens en driftsvejledning angiver vedligehold efter behov. Begge kan læses i deres oprindelige sammenhæng. [Kilder, konkrete ID’er og kommandoer](sources/operations.md)
