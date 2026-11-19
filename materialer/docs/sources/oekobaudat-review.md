# Hvem har gennemgået miljødataene?

For 5.012 materiale- og procesposter kan du slå op, hvilken gennemgang udgiveren har registreret for det konkrete miljø­datasæt. En designer, der har valgt LinCrete til en facade, kan eksempelvis se, at den valgte version har en akkrediteret tredjepartsgennemgang med en reference til Institut Bauen und Umwelt. Kontrollen gælder miljødataene. Brandklasse, akustik og andre produktegenskaber har deres egne dokumenter og betingelser. [LinCretes originale procespost](https://oekobaudat.de/OEKOBAU.DAT/resource/processes/c54c16f6-4295-4749-bff0-ba7ed4bc9117?format=json&view=extended&version=00.01.000)

```sh
ft-materials build
ft-materials facts environmental:material:oekobaudat:c54c16f6-4295-4749-bff0-ba7ed4bc9117@00.01.000 --field verification
```

## Hvad dækker udtrækket?

De 5.554 undersøgte kildedokumenter har en kendt version, en SHA-256-kontrolsum og den frie brugslicens i grundudgaven. Hver af de 6.141 registrerede gennemgange har sit eget udsagn. Flere bedømmelser af samme datasæt kan derfor læses hver for sig.

| Udgiverens angivelse | Dansk betydning | Antal |
| --- | --- | ---: |
| Independent external review | Uafhængig ekstern gennemgang | 3.472 |
| Accredited third party review | Akkrediteret tredjepartsgennemgang | 1.533 |
| Dependent internal review | Intern gennemgang | 1.133 |
| Independent review panel | Uafhængigt bedømmerpanel | 3 |

538 registreringer har en kontaktreference uden angivelse af reviewtype. To angiver udtrykkeligt, at gennemgang ikke er foretaget. To kildedokumenter har ingen reviewpost. De tre grupper fremgår af dækningsregnskabet. En tegnestue kan gå tilbage til originalen for at undersøge et hul. [Optælling og kontrolsum over kildelisten](../../data/supplements/oekobaudat-review/summary.json)

Hvert udsagn bruger originalens ordlyd for reviewtypen og rækkefølgen af dens kontaktreferencer. Institutioner med genkendte navne vises direkte. En kontakt kan også stå med sit originale ID og eventuelle versionsnummer. `source_locator` er en JSON Pointer, som peger på den præcise reviewpost i udgiverens JSON, eksempelvis `/modellingAndValidation/validation/review/0`. Det er her, man kan finde yderligere oplysninger om den enkelte bedømmelse og bedømmer. [Baggrund og vilkår for ÖKOBAUDAT](https://www.oekobaudat.de/en/guidance/data-users.html)

## Genskab og kontroller

Den færdige faktastrøm følger med Git og kan læses offline med en bygget udgave. De 5.554 originalers adresser, individuelle rettigheder, kontrolsummer og materialebindinger følger allerede med grundudgaven fra Parquet. Genindsamlingen bruger de kvitteringer fra den installerede udgave, også når den indeholder yderligere lokale tillæg.

```sh
ft-materials collect-reviews --fetch
ft-materials collect-reviews
```

Første kommando henter manglende originaler fra udgiverens versionsadresser og gemmer hver godkendt fil under `data/raw/environmental/oekobaudat/processes`. Hvis en netforbindelse afbrydes, kan man gentage kommandoen, så den genbruger de færdige filer. Anden kommando kører helt offline. Den kræver alle de låste originaler og kontrollerer deres SHA-256, proces-ID, versionsnummer og kildeangivne licens, før den skriver den komprimerede faktastrøm. En opdateret udgiverfil med en ny kontrolsum kræver en ny kildeudgave. [Beskrivelse af grunddata, rettigheder og kildekvitteringer](environmental.md)
