# Sammenlign en bjælke — mængder, nedbøjning og følsomhed

Første genbrugelige FieldCraft-forløb i `beam_study.py`. Ét rektangulært, simpelt understøttet træreferenceemne uden udkragning, med fuld nedadrettet jævnt fordelt last. Tre eksempelvalg og en eksplicit svækkelse af stivheden vises med materialemængder, kendt klimadelsum og prisstatus. Koden bruger standardbiblioteket og den eksisterende priskerne; ingen ny Python-afhængighed.

## Hvad sker der?

1. SolidCraft bygger hver kandidat som et lukket legeme i en separat fil. Målte volumener sammenholdes med beregningsgeometrien.
2. FieldCraft løser et 2D plane-stress quad8-net med træets fiberretning langs bjælken. To net sammenholdes for hver variant, også følsomhedstilfældet.
3. Reaktioner og momentbalance kontrolleres. Midtnedbøjningen sammenholdes med en særskilt Timoshenko-bjælkereference: bøjning plus rektangulært forskydningsbidrag med kappa=5/6.
4. Rust-motoren beregner kildebaseret masse og klimamoduler for det faktisk målte CAD-volumen. Statiske densiteter og klimakildens referencevægt holdes adskilt.
5. En kandidatbundet meterpris kan give et internt netto-materialeoverslag. Prisens tværsnit og grundlag skal passe. Ukendt pris bliver ikke nul.
6. HTML og JSON gemmes med input, native filer og versions-/kildebinding. En friskhedskontrol afviser ændret grundlag.

Dette er en fysisk sammenligning og en kontrol af en afgrænset opskrift. Ingen kandidat bliver samlet godkendt. Styrke, kombinationer, stabilitet/kipning, krybning, vibrationer, anlæg, samlinger, brand, fundering og produktvalg skal undersøges særskilt. Den smalleste bjælke eller den laveste delsum er ikke automatisk et konstruktionsvalg. Der foretages ingen generel optimering af en bygning.

## Input og eksempel

[study.json](study.json) indeholder tre illustrative kandidater, et testspænd på 5600 mm og en ekstern testlast på 4,6 N/mm. N/mm og kN/m har samme talværdi. Egenlasten vælges udtrykkeligt og beregnes af den statiske densitet, ikke klimakildens referencevægt. Den indgår én gang. Den eksterne last må derfor ikke allerede indeholde den samme bjælkes egenvægt, når tilvalget bruges.

GL24h-værdierne er en elastisk reference fra en tidligere kildekontrol, ikke et bestilt produkt eller en styrkeeftervisning. Poisson-tal er en antagelse; de ubrugte ud-af-plan-egenskaber er beskrevet i input. Input med spænd/højde under 8 afvises som uden for referencekontrollens afgrænsning. Andre lasttyper, udkragning, kontinuitet, huller eller samvirke er ikke understøttet.

**10 mm, 450 mm og stivhedsfaktor 0,8 er eksplicitte TEST-valg.** De er ikke normative grænser, målt usikkerhed, erklæret levetid eller krav til en konkret bygning. Udskift med begrundede projektspecifikke input. Et tomt nedbøjnings-/højdekrav forbliver ukendt. En følsomhedsgrænse er ikke en statistisk sikkerhedsvurdering.

Et prisfelt kan være `null`, eller eksempelvis følgende **testskøn**:

```json
{"amount_excl_vat_per_m":100,"section_mm":[115,405],"observed_on":"2026-11-22","reference":"TEST: internt skøn, ikke tilbud"}
```

Skønnet gælder kun bjælkens nettolængde i m med det nævnte tværsnit. Handelslængde, afskær, transport, montage og følgekomponenter er åbne. Der medfølger ingen faktiske priser.

## Runtime og kørsel

Installeret FieldCraft, SolidCraft CLI og `ft-materials` skal være til rådighed. Runtime er en separat lokal JSON-fil; lokale stier, priser og projekter publiceres ikke automatisk.

```json
{
  "fieldcraft_cli":"/sti/til/fieldcraft-cli",
  "solidcraft_cli":"/sti/til/solidcraft-cli",
  "engine":{"binary":"/sti/til/ft-materials","root":"/sti/til/materialer","store":"/sti/til/data","snapshot":"FASTHOLDT-DATA-ID"},
  "climate_source":{
    "material_id":"VALGT-KILDE-ID",
    "density_observation_id":"VALGT-DENSITET-ID",
    "gwp_observations":{"A1-A3":"VALGT-ID","C3":"VALGT-ID","C4":"VALGT-ID","D":"VALGT-ID"},
    "reference":"Begrund hvorfor denne reference passer til sammenligningen"
  },
  "bound_files":{
    "/sti/til/fieldcraft-cli":"SHA256",
    "/sti/til/solidcraft-cli":"SHA256",
    "/sti/til/ft-materials":"SHA256",
    "/sti/til/data/FASTHOLDT-DATA-ID/manifest.json":"SHA256"
  }
}
```

Kilde-ID'er vælges fra den installerede udgave. Denne første opskrift kræver klimakilder med volumenbasis; andre referenceenheder afvises indtil en dokumenteret omregning er bygget. Modul, indikator og materialekilde kontrolleres i Rust-svaret. Et ukendt klimamodul kan angives som `null`; ukendte moduler fremgår og må ikke fortolkes som nul. Klimatallet er en kendt bjælkedelsum af tilgængelige A1–A3/C3/C4-moduler, D særskilt. Det er ikke fuld LCA eller en metode til automatisk nulbelastning for genbrug.

Kør fra `materialer/`:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 beam_study.py examples/beam-study/study.json --runtime /sti/til/runtime.json --out /sti/til/nyt-forloeb
PYTHONDONTWRITEBYTECODE=1 python3 beam_study.py --out /sti/til/nyt-forloeb --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_beam_study.py'
```

Åbn `rapport.html` for overblik, `kandidater.sc` for geometrierne og de gemte `.fieldcraft`-filer for de enkelte analyser. Resultaterne er gemte rapporter, ikke et nyt livepanel eller automatisk tilbageskrivning til et aktivt SolidCraft-dokument. Ny kørsel til samme mappe kræver samme projekt-ID; brug en særskilt mappe til et andet projekt. Ved fejl markeres rapporten som fejlet; ingen skjult fallback til gamle tal.

Friskhedskontrollen binder input, kode, runtimeprogrammer, datamanifest og de gemte artefakter. Gem og kontrollér en rapport før brug; en statisk HTML-fil kan ikke selv opdage senere eksterne filændringer. Funktionens native forløb er afprøvet med SolidCraft 0.44.1, FieldCraft 0.8.1 og en konkret fastholdt `ft-materials`-motor/dataudgave. Andre kombinationer kræver egen kontrol.

Se også [hvad en ingeniør normalt leverer i Danmark](../../docs/ENGINEERING-SCOPE-DK.md). Fagansvar og formel dokumentationskontrol følger projektets faktiske aftaler og klassifikation.
