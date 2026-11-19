# Et sammenhængende designredskab

Undersøgelsesgrundlag fra 18. november 2026, samlet til publicering 19. november. Produktarbejdet er afgrænset til **SolidCraft**, med et generelt mål om brug på flere projekter. De [visuelle udkast](../examples/design-ui/README.md) er afprøvning med fiktive data; en produktintegration eller samlet faglig beregningsplatform er ikke bygget.

## Styrende behov

LCA skal indgå som et almindeligt projekteringsredskab sammen med relevante øvrige beregninger. Model, materialevalg, variantgrundlag og dokumentation skal hænge sammen, så brugeren kan undersøge konsekvenser under arbejdet og danne en rapport fra det samme fastholdte grundlag.

Arkitekten skal kunne markere en del, afprøve materialer eller komplette opbygninger, forstå delens og projektets forskel og beholde eller gå tilbage uden selv at genmodellere hvert materialealternativ. Systemet skal aflede passende mængder og følgeposter for de løsninger, det faktisk understøtter. Et nyt emissionsfaktorvalg på gamle, forkerte mængder opfylder ikke behovet.

Arkitektonisk frihed består. Brugeren kan frivilligt fastholde udtryk, åbninger eller andre kvaliteter og genåbne dem. Tekniske krav og uafklarede eftervisninger skal være konkrete; et materialevalg eller en købt vare er ingen faglig godkendelse. Søgning skal kunne undersøge kombinationer og forklare sit omfang, forudsætninger og laveste fundne resultat. Ingen generel søgekerne eller matematisk minimum er påvist i disse udkast.

## Videre funktioner til undersøgelse

| Mulighed | Hvad skal afprøves? |
| --- | --- |
| Arkitektoniske fastholdelser og hele skiftets følger | Kan udtryk, lag, lysninger og følgeposter forstås sammen? |
| Klimabudget og robusthed | Kan alternative kombinationer undersøges på samme funktion og datadækning, med synlige mangler og realistiske scenarier? |
| Standardmål, partier og afskær | Kan passende indkøbsmængder og mindre spild afledes uden at overtage arkitektens valg? |
| Klima, pris og levering | Kan sammenlignelige løsninger vises med prisdato, kendte følgearbejder og faktisk tilgængelighed? |
| Vedligehold, reparation og adskillelse | Kan adgang, retablering, restlevetid og relevante livscyklusfølger undersøges? |
| Erfaring fra faktisk indbygning og brug | Kan leverancer, spild, drift og brugererfaring afstemmes med designets forudsætninger under passende adgang og samtykke? |

Et bedre bygningsdesign omfatter også menneskers aktiviteter og tilgængelighed, rumforløb og proportioner, dagslys og udsyn, temperatur og energi, luftkvalitet og naturlige luftveje, lyd, sted og landskab samt bygbarhed og fremtidig anvendelse. Det er et undersøgelseskatalog, ikke en bestilling om alle fagmotorer eller ti permanente paneler.

En valgt anvendelse og stedets forhold skal ligge bag undersøgelserne. Projektvalgte principper, eksempelvis dokumenterbar naturlig ventilation, bevares særskilt fra universelle lovkrav. En illustration af lys eller luft er ikke en beregning. Metode, kilde, omfang, revision og fagligt ansvar skal følge hvert resultat. Arkitektonisk kvalitet reduceres ikke til en skjult samlet score.

Et relevant første eksempel er ét vinduesvalg: rum/udsyn, lys, sommerkomfort, luftveje, bæring/samlinger, LCA og økonomi omkring samme beslutning. Det visuelle udkast undersøger denne sammenhæng, mens selve fagberegningerne er åbne. EU's [Level(s)](https://green-forum.ec.europa.eu/green-business/levels/quick-introduction-levels_en) og RIBAs [evaluering af bygninger i brug](https://www.riba.org/work/business-tools/post-occupancy-evaluation-guidance/) giver inspiration til helhed og læring; de er ikke dokumentation for vores produkts effekt eller et projekts efterlevelse.

## Lignende løsninger — deskresearch, 18. november 2026

Integreret klimavisning, produktforslag, genbrug og varianter har nære eksisterende paralleller. Vores mulige værdi skal efterprøves i det konkrete arbejdsforløb; nedenstående er ikke en fuld markedsanalyse eller en selvafprøvet produktsammenligning.

| Reference | Dokumenteret relevans og afgrænsning |
| --- | --- |
| [C.Scale Product Recommendations](https://docs.cscale.io/users-guide/reduce-emissions/carbon-reduction-measures/product-recommendations) | Sidepanel med op til tre kategori-/egenskabsmatchede produktforslag, EPD og A1–A3-forskel. Dette er ikke i sig selv laveste hele-projekt-bidrag. |
| [Tally 2.0](https://docs.cscale.io/tally-2-0-users-guide/modeling-in-tally) | Løbende Revitresultater, materialedefinitioner, designvarianter og eksisterende/genbrug-status. Den læste guide/FAQ mærker 2.0 som **beta, ikke til rapportering/compliance**. C.Scale-synk er en særskilt, eksplicit handling. |
| [Autodesk Simulation Factors](https://help.autodesk.com/cloudhelp/2025/ENU/Revit-CarbonInsights/files/carbon_insights/ci_flexible_platform/ci_simulation/Simulation_Factors.html) | Afprøv alternative vægge, tage og åbninger uden at foretage ændringerne i Revit. Nye simulationsværdier kræver beregning, før resultaterne vises. |
| [One Click LCA Carbon Designer 3D](https://help.oneclicklca.com/en/articles/275669-carbon-designer-3d-getting-started) | Materiale-/konstruktionsskift og op til fire designs side om side. IFCimport er beta og laver en forenklet model. Modulomfang afhænger af det valgte værktøj. |
| [LCAlive](https://lcalive.lcabyg.dk/) | Genereret tidlig model, konstruktionsbibliotek, liveemissioner og eksport til LCAbyg. Siden beskriver tre boligtyper i første version. |
| [CAALA](https://www.caala.de/faq) | Klima/energi/livscyklusøkonomi; FAQ skelner plugins til Rhino/SketchUp fra gbXMLimport fra Revit/Archicad. |
| [Concular](https://concular.de/concular-plattform/) | Materialepas, matching, genbrugshandel, lager og logistik på fælles grundlag. En [AI-/Revitpilotside](https://www.green-ai-hub.de/pilotprojekte/pilotprojekt-concular) beviser ikke nutidig generel tilgængelighed af hele anbefalingsforløbet. |
| [EC3 2.0](https://www.buildingtransparency.org/ec3-2-0-modernizing-open-infrastructure-for-embodied-carbon/) | Den læste udgave beskriver Find & Compare i beta; Project Planner og mere helhedsvisning følger senere. En deklarations faser er ikke automatisk projektets beregnede dækning. |

Statusudsagnene er fastholdt til den angivne læsedato. Ingen programmer er installeret eller afprøvet her. Pris, licens, dansk metodedækning og en identisk brugeropgave skal undersøges konkret, før en teknisk forbindelse eller et produkt vælges.

## Praktiske kontroller for videre udvikling

- Samme funktion, relevante følgeposter, periode og modulafgrænsning i sammenligninger. Manglende data er ikke nul; D holdes særskilt.
- Adskil markering/visningskontekst fra geometri, kilder, mængder og scenarier. Vis ikke sene eller gamle resultater som aktuelle.
- Afprøv sammenligning, fortrydelse, gem/genåbn og rapport; få klik er ikke alene bevis for intuitiv betjening.
- Test kombinationssøgning mod et lille udtømmeligt sæt før hurtigere metoder. En delsum er ikke automatisk en sikker nedre grænse, hvis resterende bidrag kan være negative eller koblede.
- Bevar netto, indkøb, overlap, spild og fælles systemdele særskilt. Skeln transport fra montage og produktdata fra projektets brug.
- Et fremtidigt genbrugsvareforløb skal bevare vare-/parti-ID, antal, kilde, dato og dokumentation fra fund til indbygning. Modelvalg, bekræftet reservation, køb og levering er forskellige tilstande. Ingen handel er implementeret eller autoriseret af et modelvalg.

Næste undersøgelse bør følge én reel beslutning og observere forståelse, afbrydelser, mængde-/omfangsfejl, datamangler og arkitektens kontrol. Teknisk virkende forbindelse, markedsføringsudsagn og dokumenteret brugerfordel er forskellige evidensniveauer.
