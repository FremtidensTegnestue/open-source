# Materialedata til statiske analyser

En arkitekt kan spørge, hvor meget et bestemt materiale giver efter, om det opfører sig forskelligt på langs og på tværs, eller hvordan det ændrer sig under en last over tid. Materialekataloget giver adgang til målinger, kurver og kildebelagte referenceværdier, som kan bruges, når man vælger eller kontrollerer input til en beregning.

## Hvad kan jeg slå op?

| Område | Hvilke forskelle kan jeg undersøge? | Data og originalkilder |
| --- | --- | --- |
| Beton, cementpasta og mørtel | Krybning under last, svind over tid, 28-døgns styrker, E og cykliske trykforsøg. Kurverne fastholder blanding, prøve, tidsakse, fortegn, kvalitetsvurdering og den tilhørende litteratur | [Katalog og fravalg](../../data/supplements/mechanics-concrete-time/README.md) · [Original database](https://zenodo.org/records/8150177) · [Udmattelsesforsøg](https://zenodo.org/records/19844638) |
| Træ og træbaserede plader | Retningsafhængig stivhed, Poissons tal og forskydning, limtræ- og pladeoplysninger hvor tabellerne dækker dem, samt udvalgte krybe- og udmattelsesdata. Beregnede moduler har særskilt status | [Katalog og tabeller](../../data/supplements/mechanics-wood/README.md) · [USDA om træ](https://research.fs.usda.gov/download/treesearch/37427.pdf) · [USDA om trækompositter](https://research.fs.usda.gov/download/treesearch/62260.pdf) |
| Skruer og træsamlinger | 31 udtræksforsøg på enkeltskruer i gran og 48 lastforsøg på træsamlinger med CLT. Den målte kraft gælder den prøvede skrue eller hele samlingen med angivet antal skruer og vinkel | [Katalog og forsøgsdata](../../data/supplements/mechanics-connections/README.md) · [Udtræksforsøg](https://doi.org/10.1007/s00107-025-02205-3) · [Træ–CLT-samlinger](https://doi.org/10.3390/buildings12071018) |
| Konstruktionsmetaller og glas | Referenceværdier for angivne stålkvaliteter, rustfrit stål, aluminium, titanium og glastyper. Dynamiske målinger for flere legeringer, sten og andre prøver kan findes efter forsøgsretning | [Katalog og studier](../../data/supplements/mechanics-metals-glass/README.md) · [FieldCrafts kort](https://github.com/tangency-labs/fieldcraft/blob/v0.8.1/docs/manual/structural/material-library.md) · [JRC om konstruktionsglas](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2021-12/ReqNo_JRC86637_lbna26439enn.pdf) |
| Murværk, porebeton, natursten, jord og hamp | Densitet, stivhed, tryk, spaltetræk og forskydning hvor de er prøvet. Man kan vælge den enkelte mur, prøvegruppe, tørretid eller mørtelfuge | [Katalog med seks originalartikler](../../data/supplements/mechanics-minerals/README.md) · [Historisk murværk](https://doi.org/10.3390/heritage4010014) · [Stampet jord](https://doi.org/10.3390/buildings10030057) |
| Gips, stenuld og sandwichplader | Styrke og brudenergi for de prøvede materialer og plader, kompressionsmodul i to retninger for stenuld og bøjningsmodul for sandwichpladen | [Tabel 3, 4 og 6 i primærartiklen](https://doi.org/10.3989/mc.2013.01412) |
| Polymerer, kompositter, skum, halm, lim og silikone | Printretning, korttidskrybning, cyklisk last, hele spændings-tøjningskurver, tryk ved en angiven deformation og modelkoefficienter. Se forsøgsbeskrivelsen for lastretning og målemetode | [Katalog med ti primærstudier](../../data/supplements/mechanics-polymers/README.md) · [DTU’s glasfiberforsøg](https://zenodo.org/records/15665325) · [Forsøg på epoxylim](https://doi.org/10.1186/s40563-015-0056-y) |

For armeringsstål kan man f.eks. slå `mechanics-metals-glass:material:s500-b-jrc` op. JRC’s regneeksempel angiver 500 MPa som karakteristisk flydespænding og 200 GPa som elasticitetsmodul. Rapportens dimensioneringsværdi 435 MPa hører til eksemplets lastsituation og partialkoefficient. Ved arbejde med en leverance kan man også søge et certifikat for værk, fremstillingsproces, klasse og diameter. [JRC, afsnit 1.4.2.1](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/1110_WS_EC2.pdf) · [Eksempel på dansk produktcertifikat for B500B](https://forcecertification.com/wp-content/uploads/2023/04/DK-FC-041-10080-004-version-2-OSB-B500B-6-16-mm.pdf)

## Hvad er blevet dækket?

Tabellen tæller materiale- og prøveposter med mindst én registreret værdi for egenskaben. Flere målinger på samme prøve giver stadig kun én post i denne optælling. En enkelt kurve kan indeholde mange målepunkter.

| Egenskab | Tidligere offentlig udgave | Mekanikudgaven |
| --- | ---: | ---: |
| Elasticitetsmodul E | 274 | 1.219 |
| Trykstyrke | 317 | 1.739 |
| Trækstyrke | 170 | 354 |
| Poissons tal | 39 | 124 |
| Forskydningsmodul G | Feltet var ikke defineret | 26 |
| Fastgørelsens kapacitet | 4 | 83 |
| Krybning under last | 0 | 1.420 |
| Udmattelse og gentagen brug | 0 | 48 |
| Spændings-tøjningskurve | Feltet var ikke defineret | 92 |
| Svindtøjning over tid | Feltet var ikke defineret | 3.512 |

## Dansk murværk på tegnestuens server

Det lokale tillæg `mechanics-dk` giver 74 værdier fra Teknologisk Institut for navngivne vægge, mursten og mørtler. Et eksempel er serie »9,0 %« i 2022-rapporten. Dens eksperimentelt bestemte E-modul var 1.232 MPa efter 90 døgn og 900 MPa efter 370 døgn. Det er murværkets respons med netop denne mørtel og disse sten. Rapporten oplyser også, at seriens faktiske kalkindhold var 9,1 %. Begge procentangivelser er gemt. PDF-filer og udtræk findes i tegnestuens lokale samling. Adgang til rapporterne hos udgiveren følger her. [Forsøgsvægge og mørtelprismer fra 2015](https://www.mur-tag.dk/fileadmin/user_upload/Editor/filer/Rapporter/Bilag_2_-_Test_report_-_Masonry_based_on_lime_mortar_v6.pdf) · [Murværksforsøg fra 2022, tabel 6](https://www.mur-tag.dk/fileadmin/user_upload/Editor/filer/Rapporter/P2008487-2_Optimized_strength_measurement_of_old_masonry_-_Evaluation_report.pdf)

## Fra en modeldel til en kildeværdi

Kør fra `materialer/`. Det første opslag finder middeltrykstyrken for stampet jord med angivet lagtykkelse og tørretid. Det andet giver feltets dækning blandt træposterne. Det tredje gælder tegnestuens lokale udgave.

```sh
ft-materials facts mechanics-minerals:material:shrestha-2020-120-1 --field compressive_strength
ft-materials coverage --dataset mechanics-wood --field shear_modulus
ft-materials facts mechanics-dk:material:dti-2022-wall-9.0 --field elastic_modulus
```

En agent kan knytte modeldelens ID til den valgte forsøgs- eller produktpost. Gem dataudgaven, feltets ID, det valgte fakta- eller observations-ID, enhed, retning og kildested sammen med valget. For en kurve skal agenten også læse akserne. I betondataene er en typisk enhed for krybning mikrotøjning pr. MPa. Arkivet skelner bl.a. mellem undersøgelser vurderet som plausible og som problematiske. Begge kan findes ved opslag. [Datamodellen og opslagene](../RUST.md) · [Forskergruppens kvalitetsvurdering](https://doi.org/10.3390/ma16206751)

Til en konkret bæreevneberegning skal rådgiveren udpege en passende materialemodel og dokumentere kvalitet, tilstand, laster, understøtninger, forbindelser og de relevante sikkerhedsfaktorer. For genbrugte dele kan sortering, skader og prøvning af det faktiske parti være afgørende. I kataloget kan en teknisk reference, en forsøgsmiddelværdi og en producenterklæring have samme enhed og forskelligt anvendelsesområde. Kildestatus, prøvebetingelser og mangler kan læses for hver post.

[Dækning pr. felt i den offentlige udgave](../../data/releases/coverage-public-mechanics-2026-11-20.json) · [Dækning i den lokale udgave](../../data/releases/coverage-local-mechanics-2026-11-20.json)
