# Fremadrettet agenttest: stålmodel

Opgaven er løst ved at følge repositoryets `material-model-assessment`-skill og beregningsguide. Ingen eksisterende eksempelbindinger eller valideringsrapporter blev brugt til datavalget.

## Resultat

- Model: `solid-steel.sc`, faktisk målt lukket volumen **0,0016 m³**.
- Modelmateriale: **Konstruktionsstål, valsede profiler, lille forarbejdning**.
- Eksplicit referencescenarie: `br18:t7:D1591:row129`.
- Densitet: **7.850 kg/m³**, original `Sheet1!K129:L129`.
- Vægt: **12,56 kg**.
- A1–A3-faktor: cirka **1.639 kg CO₂-ækv. pr. metrisk ton**, original `Sheet1!E129`.
- Klimabidrag A1–A3: **20,58584 kg CO₂-ækv.** (cirka20,586).

Regning: `0,0016 × 7850 = 12,56 kg`; `12,56 / 1000 × 1639 = 20,58584 kg CO₂-ækv.` Originalfilen indeholder et lille binært flydende-tal-aftryk i klimaværdien, som er bevaret i den fulde rapport.

Dette er et brugerbestilt referencescenarie for det navngivne generiske BR18-datasæt. Det er ikke en attest for et bestemt stålprodukt, en fuld bygnings-LCA eller myndighedsoverholdelse. Kun A1–A3 er medtaget. Eksakt navnematch blev behandlet som en kandidat, ikke automatisk produktækvivalens.

## Dokumentation

`extraction.json` gemmer faktisk modelmåling, programversion, rå CLI-svar og uændret modelchecksum. `candidates.json` gemmer forslag. `material.json`, `observations.json` og `source.json` gemmer de undersøgte databaseoplysninger. `bindings.json` er skrevet til denne test. `assessment.json` er værktøjets komplette dokumenterede beregningsrapport. `independent-check.json` sammenholder beregningen med originale Excel-celler læst separat og bekræfter uændret model.

Ingen uafklarede nødvendige input eller advarsler blev rapporteret. Kilden har `license_status=unknown`, og miljøindikatorens detaljerede metodefelt er ikke angivet i databasen; rapporten bevarer disse forhold. De forhindrer ikke den eksplicit bestilte skalering af denne officielle referenceværdi.

Skillen gav en fungerende arbejdsgang; der blev ikke fundet en konkret misvisende instruktion i denne fremadrettede test.
