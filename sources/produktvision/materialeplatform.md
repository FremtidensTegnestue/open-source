# Brugerens produktretning: åben materialedataplatform

Denne projektbrief fastholder brugerens idé og præcisering fra samtalen den 17. november 2026. Det er en vision og krav til videre planlægning, ikke dokumentation for implementerede funktioner.

## Formål

Saml så mange relevante og dokumenterede datapunkter om byggematerialer som muligt i et åbent, maskinlæsbart datagrundlag til danske arkitekter og deres AI-agenter.

## Ambition og dækning

- Gå bredt på tværs af materialefamilier, produkter, bygningsdele og relevante egenskaber.
- Indsaml materialeegenskaber, klimaaftryk/CO2, fugt- og temperaturbevægelse samt øvrige tekniske, miljømæssige og anvendelsesrelevante data.
- Dæk både generiske materialeoplysninger, konkrete produkter og dokumenterede konstruktioner.
- Facadebeklædning, træ eller én bestemt bygningsdel må ikke være projektets vedtagne afgrænsning.
- Vandkunstens materiale er et udgangspunkt blandt potentielt mange kilder.

## Produktets dele

- En søgbar database med kildehenvisninger, enheder, betingelser, versioner og kvalitet for hvert datapunkt.
- Beregningsværktøjer, der bruger de dokumenterede data og eksplicitte metoder.
- Et CLI, så agenter og andre programmer kan søge, hente, sammenligne og beregne.
- Agent-skills, som forklarer korrekt brug, datavalg og arbejdsgange.
- Integration med BIMcraft og Solidcraft til at hente oplysninger og mængder fra modeller og forbinde dem med materialedata.
- Mulighed for, at AI-agenten kan samle arbejdsgangen og forklare resultater og manglende oplysninger.

## Fagligt grundprincip

AI-agenten finder og betjener værktøjerne. Efterprøvbar programkode udfører beregningerne. Materialematch, kilde, måleenhed, metode og anvendelsesbetingelser skal kunne følges. Manglende data registreres frem for at blive opfundet.

## Status

Den oprindelige bestilling var at skrive visionen i wiki og fastholde den brede ambition. Brugeren har siden udtrykkeligt bestilt, at indsamling og opbygning af databasen påbegyndes, at originalkilder downloades, og at dækning og dokumentation prioriteres bredt. Den faktiske leverance dokumenteres i docs/DATABASE.md og data/catalog.json.
