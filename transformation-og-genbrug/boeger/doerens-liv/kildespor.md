# En dør får et nyt liv

Bogen tager udgangspunkt i den indvendige dør mellem værelse og stue på foto 41 i Øllgaards tilstandsvurdering. Det andet fotografi på samme side viser døren til badeværelset. Egne prøveblade følger i de efterfølgende opslag. Se [manuskriptet](bog.html) og [oversigten over kilder, modeller og tegninger for hvert opslag](kildespor.tsv).

## Besigtigelsen i Odense

Vidensbankens søgning pegede direkte på side 22 i tilstandsvurderingen. Derefter blev udgiverens PDF hentet, teksten læst i sammenhæng og dørens fyldninger og greb sammenholdt med fotografierne på samme side.

```sh
vidensbank-soeg --tekst --json 'Genbrugshuset Odense fyldningsdøre karme indvendige døre genbrug beslag hængsler sammenfatning'
```

- Huset blev opført 1991–1993 og rummer 14 lejligheder. [Tilstandsvurderingen, PDF-s. 4](https://www.wsp.com/-/media/campaign/denmark/documents/c-det-genanvendte-hus--odense.pdf#page=4)
- I de indvendige døre er både fyldningsblad og karm genbrug. Husets beslag, låsekasser og greb på disse døre er nye. Ved eftersynet i 2021 var dørene generelt i pæn stand, og flere bandt. Årsagen til, at et bestemt blad bandt, blev ikke fastslået. [Fotos 40–41 og materialeoversigt, PDF-s. 22](https://www.wsp.com/-/media/campaign/denmark/documents/c-det-genanvendte-hus--odense.pdf#page=22) · [Undersøgernes vurdering, PDF-s. 29](https://www.wsp.com/-/media/campaign/denmark/documents/c-det-genanvendte-hus--odense.pdf#page=29)
- Sammenfatningen beskriver istandsættelsen af dørpartierne. Trykt side 18 står på PDF-side 10. [De genanvendte huse 30 år efter](https://www.tre-ing.dk/wp-content/uploads/Sammenfatningsrapport-De-Genanvendte-huse-30-aar-efter.pdf#page=10)

## De to prøver

Prøven med de ens blade isolerer hængselplaceringen. Begge blade har i CAD bredden 825 mm, højden 2.040 mm og tykkelsen 40 mm. Øverste hængselmidte ligger 200 mm under bladets overkant på A og 240 mm under overkanten på B. Nederste hængselmidte ligger i begge tilfælde 1.740 mm fra toppen. Samme lodrette forskydning kan ikke bringe begge beslag på B til at passe til de faste positioner for A. Geometrien af hængslernes blade er forenklet til placeringen af beslagene.

I prøven med gulvet står bladets underkant i snittets y-koordinat 47 mm. Gulvets overside ligger ved 52 mm før og 45 mm efter et nyt lag på 7 mm. Derved skifter den frie afstand fra +5 mm til et geometrisk overlap på 2 mm. Tallene og de to prøveblade er konstruerede eksempler. De angiver hverken et opmålingsresultat fra Odense eller en monteringsanvisning.

Modellerne blev oprettet i SolidCraft med lukkede profilsnit og ekstruderede legemer. Hver gemt .sc blev kontrolleret med `solidcraft-cli eval` og eksporteret. SVG-tavlerne er ortografiske projektioner af de eksporterede overflader. Antal legemer, lukning, profilareal og volumen er sammenholdt med prøvegeometrien. Samme rammetræ går igen på tavle 1, 2, 3, 5, 8 og 13. Modellerne har lang fyldning øverst og kort nederst, i overensstemmelse med foto 41. Hængselmarkører, bevægelsesbue og målpile er forklarende påskrifter. Der er ikke udført en fysisk prøve.

## Ord, beregning og brand

Kochs fagordbog er grundlag for beskrivelsen af dørblad, indfatning, overfals, slagliste og slutblik. [Dørblad, PDF-s. 10](https://danskbyggeskik.dk/publikationer/ordbog_fagudtryk_fra_det_traditionelle_byggeri.pdf#page=10) · [Gerigt, PDF-s. 19](https://danskbyggeskik.dk/publikationer/ordbog_fagudtryk_fra_det_traditionelle_byggeri.pdf#page=19) · [Overfalse, PDF-s. 36](https://danskbyggeskik.dk/publikationer/ordbog_fagudtryk_fra_det_traditionelle_byggeri.pdf#page=36) · [Slagliste og slutblik, PDF-s. 44](https://danskbyggeskik.dk/publikationer/ordbog_fagudtryk_fra_det_traditionelle_byggeri.pdf#page=44)

Birgisdottir m.fl. sammenligner et scenarie med en ny dør og et med en genbrugt dør. De angiver en klimabesparelse på 80 procent i deres eksempel og fremhæver metalbeslagenes rolle. Odenses nye metaldele gør det forkert at overføre procenten direkte til den undersøgte bygning. [Dialogværktøj, trykt s. 73 / PDF-s. 74](https://vbn.aau.dk/ws/files/312319822/Dialogv_rkt_j_samlet_20190917.pdf#page=74)

DBI skelner mellem tre demonstrationsdøre i projekt TRÆ og færdige produkter med dokumenterede egenskaber. Bogens principsnit gennem blad og karm er en illustration af komponenterne. [DBI · GenDør](https://brandogsikring.dk/forskning-og-udvikling/brandsikre-biobaserede-byggevarer/gendoer/)
