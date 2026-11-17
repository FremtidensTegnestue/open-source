# Lisbjerg Bakke: materialedata og beregningsparathed

Kilder: faktiske BIMcraft-udtræk fra de arkiverede ARK- og KON-IFC-filer, original IFC-materialetilknytning sammenholdt via GlobalId/UUID og den lokale materialedatabase. Audit-skriptet `audit.py` læser alt uden at ændre projekt eller database. Resultatet ligger i `material-candidates.json`. Tallene beskriver udtrækket, ikke validerede mængder i det opførte byggeri.

## Hvor langt er vi?

| Udtræk | Fysiske kandidater (rum/projekt/åbninger frasorteret) | Positivt rapporteret volumen | Entydigt normaliseret materialenavn | Både volumen og navn |
|---|---:|---:|---:|---:|
| ARK | 2.555 | 100 | 427 | 14 |
| KON | 2.206 | 97 | 270 | 97 |

I denne optælling er eksempelvis en dør eller samlingskomponent en fysisk kandidat, selv om den indeholder flere materialer. Der er ingen påstand om, at alle kandidater har enkel eller komplet geometri. De 334 rum, ét projektobjekt og 17 åbninger (`shaft`/IfcOpeningElement) i ARK samt ét projektobjekt og 7 åbninger i KON er udeladt. Pladsholderne `<Unnamed>` og `Default Wall` tæller ikke som entydige materialer. ARK-rummenes rapporterede volumen på 1.277,35m³ er ikke en materialemængde.

De normaliserede navne er mere tilbageholdende end originalens materialetilknytninger: flere bjælker/søjler har materialer i original IFC, som ikke følger med til BIMcrafts typeoplysninger. Det er således også en adapter-/importbegrænsning; ikke alt er et hul i arkitektens kilde.

## De direkte identificerede delmængder

| Model og materiale | Antal | Importeret volumen m³ | Vurdering |
|---|---:|---:|---|
| ARK `_gulv_beton (200mm)` | 10 | 19,099 | Betonfamilie; klasse/produkt mangler |
| ARK `_gulv_beton (100mm)` | 4 | 13,929 | Betonfamilie; klasse/produkt mangler |
| KON `Wood - C35` | 75 | 354,568 | Original IFC bekræfter ét lag træ, 140mm massivtrædæk; produkt/arts-/densitetsgrundlag mangler |
| KON `Beton In Situ - Dæk` | 20 | 209,709 | Ét betonlag; styrke-/eksponeringsklasse, blanding, armering og EPD mangler |
| KON `Plywood, Sheathing` | 2 | 0,096 | Krydsfinerfamilie; behandling, lim, træart og produkt mangler |

De 100 ARK-gulve har samlet rapporteret volumen 952,058m³. De resterende 86 gulve er ikke automatisk opløst i materialer. Man må hverken give alle lag hele gulvvolumen eller forudsætte, at den generiske lagtykkelse er et færdigt netto-materialeregnskab. KON-gulvenes samlede rapporterede volumen er 564,373m³ fordelt på de tre familier ovenfor. ARK og KON holdes separat; de må ikke summeres uden kontrol af overlap.

For alle 75 KON-trædæk matcher UUID med originale IfcSlab-poster med materialet `Wood - C35` og en 140mm lagtykkelse. Et eksempel er original `KON-model.ifc STEP #21589`, GlobalId `1pr34A6_b3sQpn9BHYDXuq`, import-UUID `73d4310a-1be9-43d9-acf1-24b462361e34`. BIMcraft angiver 11,850m³ og 84,64m² for dette dæk. Areal og volumen er programafledte, ikke originale Qto-felter. Det oprindelige navngivningsgrundlag siger ikke CLT; det kan derfor ikke stiltiende bindes til en CLT-reference. Der bør kontrolleres mod tegningsgrundlag og faktisk leveret produkt.

## Værdier, der kræver særlig omtanke

- `C35`, `C30`, `C18` og `C24` er træets styrkeklasse. De giver ikke alene træart, densitet ved en given fugt, fugtbevægelse eller EPD. Fugtsvulmning kræver desuden fiber-/åreringsretning og start- og slutfugt. CLT/krydsfiner skal behandles som sammensatte produkter, ikke automatisk med massivtræs radial-/tangentialkoefficient.
- `Betonelement - Væg - 2% Steel` og `Beton In Situ - Fundament - 2% Steel` er sammensatte etiketter. Procentens betydning skal dokumenteres, før den bruges. Et helt betonvolumen må ikke både få en armeret-betonreference og separat armering uden at kontrollere dobbelttælling.
- Stålets styrkeangivelse er ikke en klimafaktor. Valsede profiler, rør, plade og opsvejste profiler har forskellige generiske referencer. Fremstillingsrute, belægning og faktisk produktion er yderligere valg.
- KON har 620 importerede bjælker: 395 med originalt stålmateriale `Metal - Steel - 345 MPa` og 225 med `Wood - C35`. Kun 80 af stålbjælkerne har feltet `weight_kg` i BIMcrafts rå elementdata. Summen er 18.648,97kg. Det er en appafledt referencevægt; ikke vejet masse eller en original IFC-mængde. Deres sektionsareal × længde × 7.850kg/m³ giver 18.648,839kg, og største forskel på en enkelt bjælke er 0,0131kg ved de afrundede sektionsarealer. Det stemmer med en generisk ståldensitet, men dokumenterer ikke densitetsproveniens eller komplet stålvægt.
- Original IFC bekræfter også søjlematerialer: 364 træ C30, 166 stål 345MPa, 21 `S-X-Column-Steel-355`, 5 `Steel, S 460`. Normaliseringen har ikke bevaret entydigt materiale eller volumen for disse. Dette er et konkret forbedringspunkt i integrationen.
- Isoleringsreference `br18:t7:D1534:row76` har reference **1m² med R=1m²K/W**. Den er ikke pr. almindelig kvadratmeter. Den nuværende simple arealskaleringsfunktion afviser korrekt dette referencegrundlag; der kræves en særskilt valideret metode, der bruger isoleringstykkelse/lambda og den valgte reference.
- Gipsreference `br18:t7:D1515:row57` har arealvægt 9,1kg/m², ikke en densitet i kg/m³. Lagantal, type og nettoareal mangler før et gipsregnskab.
- Databasen har Cembrit Cover, Solid og Transparent, men ingen navnepræcis Classic-post. `Cembrit Classic 9mm` kan derfor ikke automatisk få miljøtal fra et andet Cembrit-produkt.

## Et brugbart, manuelt referencescenarie

Der er endnu ingen verificerede produkt-/EPD-bindinger for projektets materialer. Vi kan dog vise beregninger med et klart valg: **Hvis** de 209,709m³ `Beton In Situ - Dæk` i KON antages at svare til BR18-referencen Fabriksbeton C25/30, X0/XC1, post `br18:t7:B1433:row25`, bliver resultatet:

| Enkeltberegning | Referenceværdi | Resultat |
|---|---:|---:|
| Masse | 2.246kg/m³ | 471.006,414kg |
| A1–A3 | 241kgCO₂e/m³ | 50.539,869kgCO₂e |
| C3 | 6,73kgCO₂e/m³ | 1.411,34157kgCO₂e |
| C4 | 4,97kgCO₂e/m³ | 1.042,25373kgCO₂e |
| D | −4,6kgCO₂e/m³ | −964,6614kgCO₂e |

Alle fem er kørt gennem den faktiske `materials.py calculate`-kommando med gemte requests og svar. Referencegrundlaget ligger lokalt i den registrerede BR18-xlsx, række25, kildeobservationer E25/F25/G25/H25 og K25:L25. JSON-svarene indeholder kilde-URL, originalfil, hash og lokation.

Dette er et regneeksempel for en delmængde med en **ikke dokumenteret projektklasse**. Det er ikke bygningens faktiske masse, komplette klimaaftryk eller BR18-dokumentation. Der er ikke lagt moduler sammen, ikke lagt stål til og ikke korrigeret for mængdeoverlap, spild, transport eller andet scope. Brugerfladen bør altid vise disse antagelser sammen med tallene.

## Kan databasen hjælpe videre?

Ja. Der er gode familie-referencer til beton, konstruktionstræ, CLT, krydsfiner, profiler, mineraluld og gips. De gør scenarier og sammenligninger mulige, når valg af reference er dokumenteret. Familiematch er endnu ikke et verificeret produktmatch. Databaseposternes dataår, geografiske og tekniske forhold samt slutscenarier skal vurderes; et aktuelt referencetal beskriver ikke automatisk produktionen af et ældre byggeri.

Den vigtigste praktiske rækkefølge er: (1) afklar ARK/KON-overlap og kildestatus; (2) bevar originale materialetilknytninger og få kontrollerede mængder ud for de vigtigste materialer; (3) lav en eksplicit materialeliste med produkt/alternativ generisk reference og begrundelse; (4) tilføj kildebaseret densitet og individuelle miljømoduler; (5) følg op med fugt, varme, brand, akustik og bæreevne, hvor både beregningsmetode og nødvendige randbetingelser foreligger. En enkelt lambda-værdi er for eksempel ikke en fuld U-værdi, og en brandklasse er ikke dokumentation for en hel samlings brandmodstand.
