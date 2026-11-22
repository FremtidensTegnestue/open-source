# Vinduet der blev siddende

Den gennemgående byggesag er istandsættelsen af vinduerne i Det Harboeske Enkefruekloster i Stormgade. Teksterne er skrevet ud fra originalpublikationerne. Illustrationerne er nye konstruktionsprincipper. Bogens øvelsesvindue, beslag og profil har egne mål. [Ordlyd, tegninger og sidereferencer](bog.html) · [Kilder ved hvert opslag](kildespor.tsv)

## Fra vidensbanken til huset

Søgningen blev foretaget 22. november 2026 med tegnestuens videns-CLI.

```sh
vidensbank-soeg --tekst --json 'Taarbæk vinduesistandsættelse originalt vindue forsatsramme linoliekit vindue eksempel renovering slidt bundramme'
```

Søgningen gav blandt andet Realeas udgivelse om Det Harboeske Enkefruekloster på PDF-side 120 og 121 samt Raadvads anvisning om total istandsættelse på PDF-side 14. Første fund blev valgt som husets fortælling. Originalens PDF-sider 117–121 blev læst i sammenhæng og kontrolleret mod fotografier og billedtekster. I bogens henvisninger er PDF-sidetallet én højere end det trykte sidetal i Realeas bog. [Realea, 2008 · Det Harboeske Enkefruekloster](https://realdaniabyogbygklubben.dk/media/1398/det-harboeske-enkefruekloster.pdf#page=117)

I restaureringsberetningen er tolv særskilte forsatsrammer med diagonal skævhed over seks centimeter og 28 modelstørrelser to forskellige oplysninger. De beskriver arbejdet i husets forskellige åbninger. En diagonaltegning af en bestemt karm eller et opmålt profilsnit kan ikke udledes af disse oplysninger. [Realea · PDF-side 121](https://realdaniabyogbygklubben.dk/media/1398/det-harboeske-enkefruekloster.pdf#page=121)

Siderne i Raadvads tre anvisninger, *Bedre vinduer* og Slots- og Kulturstyrelsens *Forsatsvinduer* blev slået op direkte i originalernes PDF-filer. Sagsoplysninger fra Stormgade står for sig i prosaen, mens de øvrige kilder underbygger faglige observationer, værkstedsprincipper og de nye tegnede eksempler. Sidetalslinkene til de seks originalværker står ved hvert opslag.

## Fra model til tavle

I [cad](cad) ligger 14 redigerbare SolidCraft-modeller, én for hver [vektortavle](figurer). Profilerne er lukkede konturer, ekstruderet som separate legemer efter de afbildede snit. Tavlerne er ortografiske projektioner af de eksporterede modellegemer. Stiplede sigtelinjer, mål og tekst er tegningspåskrifter. Der er foretaget visuel kontrol af alle 14 tavler og sammenligning med kilderne ved de enkelte opslag. Modellerne er genindlæst og kontrolleret med `solidcraft-cli eval`. Der blev kontrolleret lukkede legemer, volumener og arealer for de projicerede konturer.

På [profilprøven](figurer/14-maal.svg) er SVG-visningsfeltet 126 × 104 enheder, svarende til 126 × 104 mm. Kontrollinjen går fra x = 37 til x = 87. Den måler 50 mm ved tryk i fuld størrelse. De to profilsnit bruger samme træ-, glas- og underkitgeometri med udvendig kit vist på den højre prøve. De øvrige tavler er uden fast målestok.
