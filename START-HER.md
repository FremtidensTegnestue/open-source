# Ny her? Begynd med din egen designopgave

**Forstå, hvad dine designvalg betyder.** Her finder du åben viden og værktøjer til at undersøge, hvordan det, vi bevarer, forandrer og bygger, påvirker mennesker, ressourcer og klima.

Begynd med tre spørgsmål:

1. Hvad vil du skabe eller forandre?
2. Hvilke valg står du med?
3. Hvilke konsekvenser har du brug for at forstå?

Brug bøger, materialetal og de afgrænsede beregningseksempler, når de er relevante for din opgave. Kilder, antagelser og åbne spørgsmål er en del af grundlaget. Du kan læse og hente materialet **uden en GitHub-konto** og begynde uden installation.

[Åbn værktøjerne på websiden](https://fremtidenstegnestue.github.io/open-source/) · [Se alle bøger](https://fremtidenstegnestue.github.io/open-source/#boeger)

Websiden er indgangen for arkitekter, konstruktører, ingeniører, bygherrer, håndværkere og andre med en byggeopgave. Her kan du finde viden om din opgave, undersøge materialetal eller vælge et eksempel til fordybelse. Vejledningen nedenfor hjælper dig også, hvis du vil bruge filerne her på GitHub.

## Brug materialerne med det samme

**[Åbn materialeopslaget i browseren](https://fremtidenstegnestue.github.io/open-source/#materialer).** Søg fx på egetræ eller isolering, vælg et materiale og se tal, referenceenhed og kilde. Du behøver ikke installere Python eller kende GitHub. Browserudgaven viser de 507 referencer fra den danske tabel 7 fra 2025. For 447 af dem kan du skrive din mængde i feltet **Se bidraget for din mængde** og se fasebidragene med det samme. **Gem beregning** henter mængde, resultat og kilder som én fil. De øvrige referencer forklarer, hvorfor deres særlige enheder kræver en anden metode. Dette er et afgrænset materialebidrag; flere poster og livscyklusfaser kræves til en hel bygnings LCA.

## Vælg en relevant fordybelse

- **Undersøg isoleringsvalg:** [Sammenlign to muligheder i browseren](https://fremtidenstegnestue.github.io/open-source/#isolering). Vælg form og to referencer, og angiv areal og ønsket isoleringsevne R. Du ser klimafaserne og forskellen med det samme og kan gemme input, resultater og kilder. Der beregnes ikke en hel konstruktion eller en fuld LCA. [Materialekortene](https://fremtidenstegnestue.github.io/open-source/#materialevalg) hjælper dig med spørgsmål om anvendelse, montage og vedligehold.
- **Få skruer og tætning med:** [Åbn det særskilte forløb](https://fremtidenstegnestue.github.io/open-source/#fastgoerelser). Vælg skruetype og nettovægt i kg. Resultatet viser de oplyste faser og kan gemmes med kilder. Beslag og tætningsprodukter har foreløbig kildekort; deres klimatal er endnu ikke i browserberegningen.
- **Find navnet på en bygningsdel:** [Åbn det illustrerede vindue på websiden](https://fremtidenstegnestue.github.io/open-source/vinduet.html). Se tegningen, vælg en del, og følg henvisningen til forklaringen og originalkilden.
- **Læs en bog:** [Åbn bøgerne på websiden](https://fremtidenstegnestue.github.io/open-source/#boeger), og læs den korte beskrivelse ved hver titel. Vælg den, der hjælper med din egen opgave. PDF'en åbnes eller bliver hentet til din computer eller telefon. Skal bogen til trykkeriet, findes særskilte **Tryk**-filer i [den fulde bogoversigt](bogserie/README.md).
- **Forstå et klimaregnestykke:** [Læs eksemplet med betonpladen på websiden](https://fremtidenstegnestue.github.io/open-source/regneeksempel.html). Du kan se, hvad ændret tykkelse gør ved masse og produktionsklima, uden at køre beregningen selv.

Brug browserens tilbageknap, når du vil tilbage. Links i teksten viser videre til næste emne eller til den kilde, forklaringen bygger på.

## Når du vil regne videre på egne modeller

Den enkle mængdeberegning ovenfor virker uden installation. Vil du hente mængder fra CAD/BIM eller bruge det større datagrundlag, kræver det lokale programmer og en terminal. Den aktuelle Rust-beregner kræver Rust/Cargo og cirka 9 GB til grundbasen, plus yderligere plads. [Se den lokale opsætning og dens forudsætninger](materialer/docs/KOM-GODT-I-GANG.md#vælg-dit-næste-trin). Du behøver kun denne vej, når din opgave kræver den.

## Tag din egen AI med

Du kan bruge materialet direkte eller få din egen AI til at hjælpe med at læse, forklare og stille spørgsmål. [Åbn AI-vejledningen på websiden](https://fremtidenstegnestue.github.io/open-source/#brug-ai), og tilpas opgaven til den byggesag og de valg, du står med.

Giv din AI et link til læsesiden, relevant kopieret tekst eller en hentet PDF/materialefil. Det afhænger af din AIs muligheder, hvad den kan læse; en chat har ikke automatisk adgang til lokale filer eller beregningsværktøjer. Bed den vise kilder og sige, hvis grundlaget mangler. Kontrollér svaret mod materialet.

## Hvad er GitHub, og hvad ser du på skærmen?

GitHub er det sted, hvor vi opbevarer og deler filerne. En samling som denne kaldes et **repository** — tænk på den som en fælles projektmappe.

På forsiden står filnavnene øverst. Rul ned til teksten med overskriften **Fremtidens Tegnestue**, og vælg en af indgangene. Du behøver ikke åbne tilfældige filer i listen.

Når du åbner en tekstside, kan filnavnet slutte på **.md**. Det er en almindelig læseside. Vælg **Preview**, hvis GitHub viser rå tekst i stedet for den formaterede side. Du kan læse siden uden at bruge knapperne **Code**, **Blame** eller redigering.

## Find det rigtige sted

- **Bygninger, genbrug og detaljer:** [Håndbogen](transformation-og-genbrug/haandbog/README.md), [fagordbogen](transformation-og-genbrug/fagordbog/OVERSIGT.md) og [træsamlingerne](transformation-og-genbrug/traesamlinger/README.md).
- **Materialetal og beregninger:** [Browseropslaget](https://fremtidenstegnestue.github.io/open-source/#materialer) virker uden installation. [Den korte materialeguide](materialer/docs/KOM-GODT-I-GANG.md) viser derudover opsætning og forudsætninger for det større lokale datagrundlag og beregningsværktøjerne.
- **Alle bøger samlet:** [Bogoversigten](bogserie/README.md) indeholder læseudgaver og trykfiler.
- **Kode og forbedringer:** [Bidragsguiden](CONTRIBUTING.md) viser, hvordan du deler en erfaring, melder en fejl eller udvikler videre.

På en lang side kan du søge i teksten med **⌘F** på Mac eller **Ctrl+F** på Windows. På en telefon findes funktionen normalt som **Find på siden** i browserens menu. Fagordbogen har også sit eget [alfabetiske register](transformation-og-genbrug/fagordbog/OVERSIGT.md#fra-ord-til-detalje).

## Hent en fil eller hele pakken

Vil du kun læse en bog, så vælg dens PDF-link. Du behøver ikke hente alle data og modeller.

Vil du gemme hele projektet, så [hent pakken som ZIP](https://github.com/FremtidensTegnestue/open-source/archive/refs/heads/main.zip). Pak ZIP-filen ud, og åbn mappen **open-source-main**. Bøger og modeller ligger i undermapperne. At hente pakken installerer ikke programmerne og opdaterer ikke automatisk din kopi senere.

En **HTML-udgave** er en side til browseren. Hent filen, gem den med endelsen **.html**, og åbn den i browseren. Nogle udgaver kræver, at deres tilhørende mapper følger med; den enkelte vejledning fortæller, hvad der er selvstændigt. På GitHub kan et klik på en HTML-fil vise dens kode frem for den færdige side.

En **model** med endelsen **.sc** eller **.bimc** åbnes i henholdsvis SolidCraft eller BIMCraft. Du behøver kun disse programmer, hvis du vil undersøge eller ændre modellerne. [Programguide](materialer/docs/PROGRAMMER.md). Datafiler som **.parquet** og programkode som **.py** og **.rs** er til egne analyser og udvikling; begynd med den relevante guide frem for at åbne dem som en bog.

## Hvis du går i stå

Find gerne linket til siden og beskriv, hvad du ville gøre, og hvad der skete.

- Har du en GitHub-konto, kan du [melde en fejl eller stille et spørgsmål](https://github.com/FremtidensTegnestue/open-source/issues/new/choose).
- Foretrækker du at kontakte os direkte, så [skriv til Fremtidens Tegnestue](https://fremtidenstegnestue.dk/kontakt-os).

Undlad private modeller, kundedata og adgangsnøgler i en offentlig fejlmelding. [Brug og rettigheder](CONTRIBUTING.md) forklarer, hvad du kan bygge videre på. Kildedata og andres materiale har deres egne vilkår.

Materialeopslag, beregningseksempler og undervisningsmodeller har hvert deres kontrolomfang. [Se, hvad der er afprøvet](README.md#hvad-er-afprøvet), før du bruger et resultat som grundlag for en beslutning i et byggeri.

[Tilbage til forsiden](README.md)
