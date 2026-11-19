# Pris, budget og leverandørdata

Pris og budget skal være tilgængeligt under designarbejdet. Det behøver ikke stå ved siden af CO₂. Begge beregninger kan bruge de samme modelmængder, mens priskilder og miljøkilder bevares hver for sig. Arkitekten vælger løsningen; laveste enhedspris eller klimatal vælger ikke automatisk konstruktionen.

**Status:** Dette er et fælles udviklingsgrundlag. Repoets Rust-CLI har ikke en automatisk leverandørprisforbindelse eller en færdig budgetprognose. En lokal projektprøve har afprøvet daterede prisreferencer, indkøbspakker og et særskilt regnskab. Den projektspecifikke prøve og dens kundedata/modeller er ikke med i dette repo. Den er ikke en generel, installerbar produktfunktion.

## Hold budget og prognose adskilt

- **Budgetramme:** den valgte reference, som kun ændres ved en eksplicit budgetrevision.
- **Forventet slutpris:** faktiske omkostninger + resterende aftalte omkostninger + forventede ikke-aftalte omkostninger + særskilt begrundet risiko/reserve.
- **Afvigelse:** forskellen til budgettet på samme omfang og momsgrundlag. Ved ufuldstændige poster vises en kendt delsum og konkrete mangler, ikke en fuld projektpris.

En faktureret del af en ordre skal trækkes fra den resterende ordreforpligtelse. Betaling, fakturering, levering og bestilling er forskellige hændelser. Historiske faktiske udgifter og aftalevilkår må ikke overskrives af en nyere webshoppris. En accepteret aftale er kun prisfast i det omfang, dens vilkår gør den fast.

Prisændringer skal kunne forklares som design-/mængdeændring, markeds-/aftaleprisændring, ændret omfang eller bedre datadækning. Flere prissatte poster er ikke automatisk et dyrere design. Gem mængdegrundlag og prisudgave, så ændringen kan efterprøves.

## Beregn køb i de rigtige enheder

Netto → eksplicit spildtillæg → pakker/mindstekøb → valgt leverance → pris. Ubrugte pakkerester er ikke automatisk affald eller ekstra indbygget materiale i klimaberegningen.

Hver pris skal fastholde vare-ID/variant, fysisk enhed, referenceindhold, oprindelse (eksisterende/genbrug/nyt), valuta, momsgrundlag, kilde, prisdato og gyldighed. Klimaets funktionelle R-referenceareal er ikke et købsareal. En pris pr. 100 styk er ikke en stykpris, og en nettopris skal ikke have den allerede anvendte rabat trukket igen.

Afklar om prisen omfatter montage, materiel, spild, transport, emballage, gebyrer, overhead og avance. Samlede systemtilbud og deres indeholdte komponenter må ikke tælles dobbelt. Genbrug kan have udgifter til undersøgelse, reparation og tilpasning; det antages ikke gratis. En webshopvare er ikke automatisk produktet bag en generisk miljøreference.

DfD er et frivilligt tilvalg. Særlige beslag, DfD-prøver og montagefølger medtages kun i det valgte omfang. Almindelig materiale-, pris- og budgetberegning kræver ikke DfD. Læs [adskillelsesfunktionens afgrænsning](DISASSEMBLY.md).

## Første leverandørspor: STARK

Undersøgt 19.11.2026. [STARKs offentlige beskrivelse](https://www.stark.dk/services/digitale-muligheder) angiver kundeprisfiler, manuel CSV, typisk ugentlig levering og ét abonnementsmodtagersystem. Nogle varer har to enheder/priser. Siden beskriver særskilt Punch Out med OCI/cXML. FTP/SFTP og INVOIC optræder under e-faktura og beviser ikke en prisfilkanal til vores værktøj.

[Erhvervsbetingelsernes afsnit 4](https://www.stark.dk/Om-STARK/Salgs-og-leveringsbetingelser) beskriver et prisgrundlag eksklusive bl.a. moms og fragt. Den konkrete fil og kundeaftale skal afstemmes før normalisering; en rå erhvervspris må ikke kopieres ind som en pris inklusive moms.

**Anbefaling:** start med én kunderelevant prisfil og en dokumenteret modtagerrute. Punch Out er et andet brugerforløb og er ikke i sig selv dokumentation for ubetjent genprissætning af hele projektlisten. Der er ikke fundet en offentlig read-only pris-API-kontrakt i det gennemgåede materiale. Det udelukker ikke en særskilt aftale med leverandøren.

Ingen faktisk kundekonto, eksempelfil, feltkontrakt, pris-API eller automatisk levering er afprøvet i undersøgelsen. Ingen STARK-priser er aktiveret i repoet. Automatisk leverandørlevering, modtagelse, import, anvendelse i projekt og handel er fem forskellige trin.

## Afklar før en import bygges

1. Hvilken købende kunde/entreprenør, aftale og eventuelt projekt gælder priserne for? Kundernes private aftaler skal være adskilt.
2. Hvilken filvariant leveres, og hvad betyder kolonner, pris-/salgs-/pakkeenheder, rabatter og referenceindhold?
3. Er filen fuldt katalog eller ændringer? Hvordan beskrives gyldighed, ophørte varer, tomme/0-værdier og genlevering?
4. Hvilken tilladt transport og opdateringsfrekvens kan bruges af et selvudviklet program? Et eksisterende ERP-abonnement må ikke flyttes stiltiende.
5. Hvad omfatter prisen, og hvilke vilkår gælder for opbevaring, historik og brug i et værktøj for flere firmaer?

Først en virkelig eksempelfil og tre kendte varer i forskellige enheder. Byg derefter den mindste import, som passer til den bekræftede kontrakt. Der er ikke valgt mailmodtagelse, SFTP eller API alene ud fra en offentlig produktbeskrivelse.

## Kontroller før automatisk anvendelse

Dette er acceptkrav til en fremtidig import, ikke påstande om beståede feedtests:

- Afstem tre faktiske varer mod samme kundes priser og mængder.
- Genimport af samme observation må ikke skabe dubletter eller en ny påstået prisdato.
- Forkert kunde, ukendt enhed, ændret format og ophørt vare skal give konkret afklaringsstatus.
- Hentefejl må ikke erstatte det gyldige grundlag med et tomt katalog eller skabe en falsk besparelse.
- Nye observationer skal kunne undersøges før aktivering. De må ikke ændre CAD, EPD-valg, faktiske udgifter eller aftalevilkår automatisk.

Registrér prisens observationstid, gyldighed, modtagelse og seneste vellykkede kontrol særskilt. Daglig kontrol gør ikke en ugentlig kilde til dagsdata. Genbrug gyldige modelmængder ved en ren prisændring og bevar budgetrammen.

Drift, vedligehold, udskiftning, rente, prisudvikling og restværdi kræver yderligere grundlag, før resultatet kaldes en levetidsomkostningsberegning (LCC).
