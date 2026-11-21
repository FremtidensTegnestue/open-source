# Træsamlinger

Hvorfor kan én bjælke løftes fri, mens en anden først skal skydes sidelæns og have to stifter ud? De to fagbøger følger træet fra den synlige fuge til samlingens indre. Hver bog har en indholdsfortegnelse, fire faglige dele, et alfabetisk register, studietavler og opgaver med gennemarbejdede svar.

| Anden udgave | Indhold og modeller | Læs hele bogen |
| --- | --- | --- |
| **Danske træsamlinger** · 42 sider | [25 samlinger](danske/README.md) fra remmens stød og hageblade til skråbånd, kamme og bræddeprofiler | [PDF](danske/bog.pdf?raw=true) · [HTML til offlinebrug](danske/bog.html?raw=true) |
| **Japanske træsamlinger** · 36 sider · på dansk | [20 samlinger og forbindelser](japanske/README.md) fra enkle sæder og kryds til skjulte kiler og halvblinde T-ender | [PDF](japanske/bog.pdf?raw=true) · [HTML til offlinebrug](japanske/bog.html?raw=true) |

**Tre måder at bruge bøgerne på**

- Skal du registrere et eksisterende hus, kan du begynde med [fire snit gennem en dansk rem](danske/studietavler/pl-lige-blad.md). Følg først støtten og dernæst de synlige skuldre.
- Skal du forklare en montage, kan du sammenligne [okkake-daisen-tsugi](japanske/okkake/README.md) og [kanawatsugi](japanske/kanawa/README.md). Begge har træstifter, men bjælkerne skal kunne bevæges i forskellige retninger.
- Skal du vurdere en skjult detalje, kan du gå til [studietavlen om jigokuhozo](japanske/studietavler/pl-jigoku.md). Den viser, hvorfor to separate former er nødvendige for at forklare kilernes virkning.

## Fra vidensbanken til originalen

Tegnestuens CLI søger i PDF-tekst, billeder og bibliografiske oplysninger. Søgeresultaterne blev brugt til at finde læsesteder. I bøgerne er der direkte henvisninger til de konkrete udgiveropslag, figurer eller PDF-sider. Bøgerne bruger egne modeller og gengiver originalernes principper med valgte illustrationsmål.

[Søgelog med spørgsmål og fund](kildespor.md) · [Originalkilder pr. samling](kilder.tsv)

## Modelkontrol

De 45 kapitler har 46 redigerbare SolidCraft-modeller. Jigokuhozo har to, fordi træet ændrer form. For hver model medfølger byggeopskriften samt en køreklar montagekontrol. Tabellen med resultater angiver modelmål i mm, antal legemer og antal kontrollerede stillinger. Målene gælder bogens model.

- **280 kontrollerede stillinger.** De lukkede legemer er genåbnet, målt og kontrolleret for indbyrdes overlap ved udvalgte stillinger langs den viste bevægelse. De flertrins samlinger omfatter også indføring af låsene. Ingen af de prøvede tilladte stillinger gav overlap eller ukontrollerede par.
- **Fem låseprøver.** Her er en ellers låst del bevidst flyttet i en spærret retning. Det målte overlap viser, hvor en stiv geometrisk bevægelse ville tvinge trædelene ind i hinanden. Volumenet måler hverken kraft, friktion eller brudstyrke.
- **Jigokuhozo.** Den uspredte models sidste stilling har kilerne mod hulbunden. Den udspændte models skulder ligger an, og tapspidsen har luft under sig. Overgangen mellem de to former er en forklaring af mekanismen; den er ikke en elastisk materialesimulering.

[Alle modeller og kontrolresultater](modelkontrol.tsv) · [Retning og resultat af låseprøverne](laaseproever.tsv)

### Gentag en kontrol

Kør fra denne mappe. Montageopskriften flytter delene i hukommelsen og måler interferens for hver stilling.

```sh
solidcraft-cli eval danske/hage/model.sc
solidcraft-cli run japanske/kanawa/montage.json --in japanske/kanawa/model.sc --results
solidcraft-cli run japanske/jigoku/montage-foer.json --in japanske/jigoku/model-foer.sc --results
```

Pasning i træ, fugtbevægelser, brudlast og egnethed i en bestemt bygning er ikke afprøvet for undervisningsmodellerne. Der er ikke foretaget en uafhængig håndværksfaglig bedømmelse.
