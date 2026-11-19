# Opdatering af denne OpenWiki

Du kan redigere [debatloggen](debat.md) og [oplæggene](oplaeg/) direkte på GitHub. Det er kilderne til wikien. De færdige sider kan læses direkte under [openwiki](openwiki/quickstart.md).

OpenWiki arbejder med én Git-rod ad gangen. For at opdatere netop denne wiki fra en lokal klon med de seneste bidrag, begynder du i repositoryets rod med kilderne committet. Disse kommandoer opretter en midlertidig Git-arbejdsmappe for emnet.

```sh
tema=transformation-og-genbrug
arbejde=$(mktemp -d)
revision=$(git subtree split --prefix="$tema" HEAD)
git worktree add --detach "$arbejde/tema" "$revision"
```

Bed din agent opdatere den eksisterende OpenWiki på dansk med den absolutte sti til `$arbejde/tema` som Git-rod. Gennemse de opdaterede sider, indeks og kildespor. Kopiér den færdige wiki tilbage fra repositoryets rod. Git viser så ændringerne før publicering.

```sh
rsync -a --delete "$arbejde/tema/openwiki/" "$tema/openwiki/"
git status --short -- "$tema"
```

Når ændringerne er gemt og kontrolleret, kan den midlertidige arbejdsmappe fjernes. Kontrollér før oprydning, at eventuelle nye sider også er kommet med.
