# Brug projektet og byg videre

[Ny på GitHub? Start med læsning og download](START-HER.md). Du kan bruge indholdet uden at oprette en konto. En GitHub-konto er nødvendig, når du vil oprette en fejlmelding eller sende en ændring tilbage.

Alle er velkomne til at bruge og videreudvikle vores egen kode. Den og vores egne tekster er udgivet under [MIT](LICENSE). Kildedata og tredjepartsmateriale beholder deres egne vilkår; se [kilder og rettigheder](materialer/THIRD_PARTY.md).

| Du vil … | Start her |
| --- | --- |
| Se et eksempel og prøve et materialeopslag | [Den korte startvejledning](materialer/docs/KOM-GODT-I-GANG.md) |
| Fortælle, hvor du gik i stå, eller foreslå en forbedring | [Opret et issue](https://github.com/FremtidensTegnestue/open-source/issues). Skriv, hvad du ville gøre, og hvad der skete. |
| Udvikle programmet eller bidrage med en kilde | [Bidragsguiden med Python- og Rust-tests](materialer/CONTRIBUTING.md) |

Du kan læse eksemplerne i browseren uden installation. Brug af materialeopslag og beregninger kræver de værktøjer, startvejledningen angiver; der kræves ingen betalt AI-tjeneste.

Du kan eksperimentere i din egen kopi. Vil du sende en ændring tilbage, så lav en **fork** (din kopi på GitHub), arbejd i en **gren** (en særskilt udgave af ændringen), og åbn en **pull request** (et forslag om at tage ændringen ind i den fælles version). Beskriv problemet, ændringen og hvordan du har kontrolleret den. Bidrag gennemgås, før de bliver del af den fælles version. Du kan også begynde med den [danske formular til hjælp, fejl og forslag](https://github.com/FremtidensTegnestue/open-source/issues/new/choose), uden at ændre nogen filer.

Vil du drøfte, hvordan en eksisterende bygning kan ombygges, eller dele erfaringer med genbrug? [Tilføj dit spørgsmål eller din erfaring til debatten](transformation-og-genbrug/debat.md). Du kan også [oprette et issue](https://github.com/FremtidensTegnestue/open-source/issues).

Når du ændrer læsesider, kan du kontrollere alle lokale dokumenthenvisninger fra mappen `materialer` med `python scripts/check_public_docs.py`. Kontrollen kræver Python 3.11+ og en Git-kopi, men ingen ekstra Python-pakker. Den kører også automatisk på GitHub. Den kontrollerer statiske filstier og Markdown-overskrifter; eksterne kilder, dynamiske HTML-links og den faktiske læsbarhed kræver særskilt kontrol.
