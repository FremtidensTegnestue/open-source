# Miljødeklarationer fra EPD Danmark

Denne indsamling læser resultater direkte fra EPD-ejernes offentliggjorte PDF’er. I udgaven fra 18. november 2026 gav 82 deklarationer 15.313 tal og 81 udtrykkelige kildemarkeringer for eksempelvis udeblevne deklarationer. Tallene dækker 32 indikatorer, blandt andet klima, råstoffer, energi og affald. Hver værdi henviser til en bestemt PDF-side, tabelrække, modulkolonne, enhed og produktmængde. [EPD Danmarks database](https://www.epddanmark.dk/epd-databasen/)

## Hent data

Rust-kommandoen indeholder PDF-læseren og arbejder direkte fra repositoryets rod.

```sh
cargo run --locked -- collect-epd --locked
```

Kommandoen henter eller genbruger 920 identificerede originaler, i alt cirka 329 MB. Den kontrollerer hver SHA-256 og gemmer originalerne efter indhold i `data/raw/epd-danmark/objects/`. Det lokale supplement ligger derefter i `data/staging/epd-danmark/`. To kørsler med de samme originaler og samme udtræk giver samme filer. Hvis udgiveren ændrer en låst kilde, skal den oprindelige fil hentes fra et bevaret arbejdsarkiv. [Originalernes kontrolsummer og adresser](sources.lock.json) · [Kontrolsummer for udtrækket](validation.json)

For at indsamle den **aktuelle** udgave, vælg nye navne til både kildelås og resultatmappe. Eksemplet opretter en særskilt kontrolkørsel.

```sh
cargo run --locked -- collect-epd --refresh \
  --lock data/raw/epd-danmark/ny-kontrol/sources.lock.json \
  --output data/raw/epd-danmark/ny-kontrol/epd-danmark
```

## Hvordan læses cellerne?

For den kontrollerede udgave indeholder pakken en tabeloversigt med PDF-side, placering af tal, modulnavne og kontrolsum af hver resultatrække. Rust læser tegnene på de angivne positioner i originalfilen og kontrollerer hele rækken før import. Kildestederne bevarer de sidenumre og linjenumre, der tidligere blev brugt til uafhængig kontrol. Nye eller ændrede dokumenter undersøges ud fra deres overskrifter, modulet over hver kolonne og den deklarerede enhed. Resultater med tvetydige forudsætninger får en forklaring i `coverage.jsonl`. [Kontrollerede tabellokationer](pdf-layouts.json.gz)

## Hvad indgår i beregningerne?

Indsamlingen gennemgik 701 poster i udgiverens katalog. Den læste produktsider med én hoved-PDF mærket EN 15804+A2 og arkiverede 275 kandidatdeklarationer. Udtrækket kræver, at produktsiden angiver ét deklareret datasæt, og at PDF’en uafhængigt bekræfter den deklarerede mængde. Filer med gentagne resultatsæt eller tvetydige modulkolonner kræver særskilt gennemgang. En produktside svarede med HTTP 500. Den lokale `coverage.jsonl` viser udfald for hver katalogpost. [Dækning og begrundelser](validation.json)

PDF’en er grundlag for talværdien, fortegnet, enheden og modulet. Flere moduler kan være deklareret samlet, fx A1–A3 eller B1–B7. Referencegrundlaget er mængden af det deklarerede produkt. Hvis deklarationen omfatter en produktgruppe, bevares den afgrænsning. Kildemarkeringer som `ND` og `MND` har det oprindelige tekstfelt og en tom numerisk værdi. De kan søges som dokumentation.

Som eksempel angiver deklarationen for skillevægssystemet Tystø **−0,768 kg CO₂e for 1 m² i modul A1–A3**, indikatoren GWP-total. Tabellen står på PDF-side 8. Modul D og de øvrige deklarerede faser har separate observationer. Forsidens fulde gyldighedsdato opbevares sammen med beregningsgrundlaget. [Originaldeklaration MD-23055-EN](https://www.epddanmark.dk/media/3ctltuob/md-23055-en_rev1.pdf)

## Adgang til originalerne

Repositoryet distribuerer kildelås, kode og efterprøvelige kontrolsummer. Indsamlingen henter de fulde tal og originaler lokalt direkte hos EPD Danmark. Programinstruktionens afsnit 5.9 placerer ejerskabet hos den enkelte EPD-ejer. Vi har ikke fundet en samlet tilladelse til at videreudgive denne samling. Udgiverens LCAbyg-arkiv med 363 krypterede `.lb5epd`-filer registreres som original. Selve udtrækket foretages fra de offentlige tabeller i PDF’erne. [EPD Danmark, General Programme Instructions, v3](https://www.epddanmark.dk/media/ifrh2ghc/general-programme-instructions_v3.pdf) · [LCAbygs officielle filvejledning](https://guide.lcabyg.dk/da/legacy-2023/building_model/stage/import_epd/import_epd/)
