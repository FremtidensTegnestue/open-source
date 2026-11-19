# Facademontage: prøv adgang før du vælger samlingen

Kør fra `materialer/` med en kildebygget DfD-version og den dataudgave, eksemplet angiver:

```sh
ft-materials disassembly examples/disassembly/facade-mounting.json --text
```

Eksemplet giver statuskode2: et gyldigt, delvist resultat. Det er to egne montagehypoteser for samme begrænsede prøvefelt, ikke en bestemt producents system eller en vurdering af alle traditionelle facader.

| Indgreb | Åbning af nabodel | Planlagt lokal adgang |
| --- | --- | --- |
| Udskift én beklædningsdel | Nabodel tages midlertidigt af; låsedel antages skåret fri og skal erstattes | Adgangsafdækning og låsedel tages midlertidigt af; nabodel foreslås bevaret |
| Indre lag | Foreslås bevaret | Foreslås bevaret |
| Fysisk adgang, skade og genmontage | Ikke eftervist | Ikke eftervist |
| Samlet klima og vinder | Ukendt | Ukendt |

Det lokale forløb er en designhypotese, ikke en DfD-godkendelse. Inputtets afhængigheder er angivet af os; programmet udleder dem ikke fra en CAD-model. En lukket adgangsafhængighed viser, at denne plan ikke hænger sammen. Den beviser ikke, at enhver anden udtagningsmetode er umulig.

## Udvikl monteringen som en samlet opgave

1. Vælg enhed: enkeltsten/plade, felt eller hel kassette. Skeln forbindelser inde i enheden fra dens ophæng på bygningen. En aftagelig kassette er ikke automatisk adskillelig indvendigt.
2. Vis hvordan egenvægt og vind føres til underlaget, hvordan enheden låses, og hvad der holder den, mens låsen løsnes. Kapaciteter skal eftervises for den faktiske løsning.
3. Tegn adgang, værktøj, udtagningsretning, plads, tolerancer og materialebevægelse. Afprøv midterfelt, hjørne, tagfod og åbning. Et overlap eller en inddækning kan ændre hele rækkefølgen.
4. Adskil bæring/låsning fra regnafledning og lufttæthed, hvor det er teknisk muligt. Beskriv tætninger, genmontage og nødvendige forbrugsdele. En vandret ophængsskinne må ikke utilsigtet stoppe afvanding eller hulrummets luftvej.
5. Registrér første montage og gentagen udtagning/genmontage: tid, værktøj, antal nabodele, skader, forbrugsdele og retablering. Indtil en prøve er gennemført er resultatet antaget eller ukendt.
6. Medregn første opførelses samlede materialer og senere følgearbejde. Antal beslag, mængde skruer, underlag, indkøb/spild, tætninger og tilstødende lag er endnu åbne i dette eksempel. Ingen klimaoptimeret vinder kan udledes.

Facadehulrumsventilation er ikke rumventilation. Projektets naturlige ventilation og øvrige tekniske funktioner afstemmes ved faktisk facade-/åbningsændring. Arkitekten vælger form og udtryk; fx modularitet og retvinklede dele er muligheder, ikke obligatoriske arkitekturkrav.

## Kilde og vores anvendelse

Vandkunsten m.fl., *Rebeauty — Nordic Built Component Reuse* (2017), viser bl.a. et tilpasset tagstensbeslag (trykt21/PDF23), kilefastholdelse i en indvendig glasvæg (trykt29/PDF31) og beslag til metalplader uden nye huller i pladen (trykt33/PDF35). Designreglerne findes trykt15/PDF17. [Rapport](https://vandkunsten.com/content/2019/03/NBCR-20170201-sml.pdf). Udvalgte sider er gennemgået visuelt og i tekst19.11.2026; der er ikke foretaget fuld standard-/produktafprøvning.

Vores eksempelforløb er ikke en digital kopi eller teknisk validering af prototyperne. Rapportens historiske LCA, tids-/tabsantagelser og produktvalg er ikke importeret som nutidige standarddata. Dens principper bruges til at undersøge konkret montage, herunder alternative enhedsstørrelser, adgang og materialefølge. [CLI og implementeringsgrænse](../../docs/DISASSEMBLY.md).
