# Fremtidens Tegnestue

**Hvad er værd at bevare, og hvad skal der til for at bygge videre på det?**

Vi er arkitekt Thais Espersen og systemudvikler Mikkel Freltoft Krogsholm. Sammen bygger vi de værktøjer, vi selv gerne vil have ved tegnebordet. Her deler vi vores materialedata, beregninger og en håndbog om transformation og genbrug. Du kan åbne en byggesag, se hvad beboerne oplevede, eller tage tallene med ind i din egen model.

**[Åbn håndbogen](transformation-og-genbrug/openwiki/quickstart.md)** · **[Gå på opdagelse i materialerne](materialer/README.md)** · **[Mød tegnestuen](https://fremtidenstegnestue.dk/om)**

![Illustration af et gammelt trævindue på arbejdsbordet med et afmonteret hjørnebeslag og en tegning af vinduesprofilet](.github/billeder/vindue-under-reparation.webp)

<!-- Forsideillustration skabt med den indbyggede ImageGen. Prompt: Ultrabred, tekstfri forsideillustration til Fremtidens Tegnestue. Vis et gammelt dansk trævindue under reparation på et arbejdsbord, med false, afskallet linoliemaling, løst hjørnebeslag og en blyantstegnet profildetalje. Arkitektfagligt linoleumstryk på varmt papir i teglrød, kulsort og gråblå. Komponér hele motivet vandret i format 3:1. -->

## Når facaden skal blive, og boligerne skal være varmere

På Ryesgade 30 A–C i København fortæller beboere, at de efter renoveringen igen kunne bruge de dele af boligen, hvor det før trak. Ude på gaden står den murede facade stadig. I håndbogen kan du følge vinduesforsøgene i prøvelejligheden, se hvad der gik galt med isoleringen og finde målingerne efter indflytning. Undervejs kan du slå op i projektets egne tegninger og rapporter. [Læs om Ryesgade](transformation-og-genbrug/praksis/etagehus.md) · [Se projektgruppens egen beskrivelse](https://renover.dk/projekt/ryesgade-30-a-c/)

Andre sager følger en villa i Gentofte, der blev til to boliger, og en almen blok i Tilst, hvor beboerne skulle beslutte, om de ville vende tilbage efter renoveringen. Skal du selv ud at se på en bygning, kan du tage vores arbejdsark med. [Følg de tre danske byggesager](transformation-og-genbrug/praksis/README.md) · [Tag arbejdsarket med på besigtigelse](transformation-og-genbrug/oplaeg/forste-besigtigelse.md)

## Fra en tegning til et tal, du kan forklare

I Vandkunstens konstruktionsmodel for **Lisbjerg Bakke** fandt vi 75 trædæk med et samlet volumen på knap **355 m³**. Modellen giver os mængden. For at regne på klimaaftrykket skal vi også vide, hvilket træprodukt der blev brugt. Rapporten giver dig mængderne og de spørgsmål, vi ville stille projektholdet, før vi satte tal på klimaaftrykket. [Læs vores rapport](materialer/reports/lisbjerg-bakke/README.md) · [Hent originalmodellen hos Vandkunsten](https://opensource.vandkunsten.com/07_FBABLisbjerg/)

I materialebanken kan du også undersøge, hvor meget træ bevæger sig, når fugten ændrer sig, og hvad en bestemt glasdør kræver af vedligehold. Den offentlige dataudgave fra november 2026 rummer **over to millioner observationer**. Tallene følger med, så du selv kan undersøge enheder, betingelser og kilder. [Hent dataene](materialer/data/README.md) · [Se eksemplet med glasdøren](materialer/docs/sources/operations.md)

### Prøv det på en hylde

En krydsfinerplade og to stålskinner er nok til at afprøve hele forløbet. I **SolidCraft** tegner vi delene. I **BIMCraft** finder vi dem igen i bygningsmodellen. Vores materialeværktøj i Rust beregner hyldens vægt til **2,277 kg** og klimaaftrykket fra produktionen til **1,238 kg CO₂e**. I **FieldCraft** undersøger vi, hvor meget en skinne bøjer, når hylden belastes. Du kan følge regnestykket direkte i browseren eller hente modellen og ændre lasten selv. [Se hylden og beregningerne](materialer/examples/hyldekonsol/README.md) · [Hent programmerne og se, hvordan de spiller sammen](materialer/docs/PROGRAMMER.md)

Bruger du en AI-agent, kan du åbne projektmappen og give den en opgave på almindeligt dansk. [Kom i gang med materialeværktøjet](materialer/docs/RUST.md)

> Gennemgå hyldeeksemplet med mig. Hvad sker der med stålskinnens nedbøjning, hvis jeg sænker lasten fra 100 til 80 newton? Vis kilden til stålets stivhed, og fortæl mig, hvad vi stadig skal vide om væggen og skruerne.

## Hvilken byggesag sidder du med?

Har du et vindue, du gerne vil redde, en model med mangelfulde materialetal eller erfaringer fra en ombygning, som andre kunne lære af? Vi vil gerne høre, hvilken beslutning I står over for på jeres tegnestue, og se på, hvordan vi kan hjælpe.

**[Tal med Thais og Mikkel om din sag](https://fremtidenstegnestue.dk/kontakt-os)** · [Del en kilde, en erfaring eller en rettelse](CONTRIBUTING.md)
