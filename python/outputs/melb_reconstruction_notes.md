# MELB / MasArch reconstruction notes

## Co je zatim pevne

- `MasArch.exe` byl GUI obal nad konzolovymi programy `MELB.exe` a `HINGE.exe`.
- `MELB.exe` vytvari:
  - textovy detail vypoctu `*.txt`,
  - binarni transformacni matice `*.AB`,
  - binarni zadani simplexove ulohy `*.sim`.
- V `MELB.exe` zustaly nazvy funkci:
  - `_simplx`
  - `_polint`
  - `_geom1`, `_geom2`
  - `_cal_pq2`
  - `_cal_AB`
  - `_cal_N_e`
  - `_cal_T`
- To silne ukazuje na simplex a interpolaci z Numerical Recipes.

## Pridane testy

Adresar `melb_regression` ted umi strojove cist zachovane `zlamal*.in`, vysledkove
`*.out`, podrobne textove vypisy `*.txt`, binarni transformacni matici `*.AB`
a prvni vrstvu binarniho `*.sim`.

Aktualni testy:

```text
Ran 10 tests in 0.092s
OK
```

Pro referencni pripad `zlamal0\zlamal0_1.in` se overuje:

- `lambda = 9.158882`
- aktivni lokalni deformace:
  - `1: fi 00 int = 5.000002`
  - `16: fi 07 ext = 8.384995`
  - `51: fi 25 int = 6.778130`
  - `82: fi 40 ext = 3.393136`
- hlavicka `zlamal0_1.sim`:
  - `(164, 4, -1)`
  - 828 dalsich 32bit bunek
  - pri cteni jako tabulka vychazi prirozene tvary `(5, 165)` nebo `(165, 5)`
  - trailing metadata jako int: `(0, 0, 3)`
- `zlamal0_1.AB`:
  - pro `N = 40` ma tvar `164 x 123`
  - obecne `4*(N+1)` radku a `3*(N+1)` sloupcu
  - prvnich `2*(N+1)` radku odpovida lokalnim rotacim `fi int/ext`
  - dalsich `2*(N+1)` radku odpovida posuvnym podminkam `y (+/-)`
- `zlamal0_1.txt`:
  - geometrie intrados/extrados: `41 x 4`
  - vlastni tiha klenby: `40 x 3`
  - nadnasyp a vnejsi zatizeni: `40` radku
  - transformovana zatizeni: `41 x 3`
  - vysledkove vektory ve sparach: `41` hodnot
- porovnani `AB` s `txt`:
  - `AB @ (transformovana vlastni tiha + transformovany nadnasyp)` reprodukuje
    prvni radek simplexoveho souboru `*.sim` s opacnym znamenkem
  - `AB @ transformovane vnejsi zatizeni` reprodukuje druhy radek `*.sim`,
    ale s posunem o jednu bunku, coz odpovida staremu 1-based stylu poli
    v Numerical Recipes
- interpretace `*.sim`:
  - posledni integery `(0, 0, 3)` odpovidaji NR parametrum `m1=0, m2=0, m3=3`
  - historicky vektor aktivnich lokalnich deformaci po vynasobeni cilovym
    radkem `*.sim` dava `lambda = 9.158892`, tj. shodne s textovym vypisem
    v toleranci zaokrouhleni
- SciPy/HiGHS `linprog`:
  - spravna moderna formulace je staticka/dualni: 4 primarni promenne
    (`lambda` + tri staticke/kompatibilitni konstanty) a `4*(N+1)` nerovnosti
  - pro `zlamal0_1` reprodukuje `lambda = 9.158867`
  - aktivni nerovnosti jsou `1, 16, 51, 82`
  - zaporne HiGHS marginaly aktivnich nerovnosti reprodukuji lokalni deformace
    z historickeho vypisu

## Co zatim nevychazi primo

Prime pokusy predat `*.sim` do `scipy.optimize.linprog` jako standardni LP matici
zatim nevychazeji:

- interpretace `(5, 165)` vede na neomezenou ulohu,
- interpretace `(165, 5)` vede na neproveditelnou ulohu.

To pravdepodobne znamena, ze `*.sim` neni jen cista float matice `A, b, c`, ale
obsahuje data ve formatu puvodni funkce `simplx` z Numerical Recipes, vcetne
stavovych/metadatovych polozek.

## Navrzeny dalsi krok

1. Overit SciPy/HiGHS formulaci na dalsich zachovanych `zlamal*_*.txt/.AB/.sim` pripadech.
2. Zobecnit sestaveni kompatibilitnich radku tak, aby uz nebylo nutne cist `*.sim`.
3. Az potom pouzit `*.sim` jen jako regresni kontrolu puvodniho Numerical Recipes simplex formatu.

Tato cesta je lepsi nez slepe kopirovat binarni format `*.sim`: vede k citelnemu
Python kodu a umozni pozdeji znovu postavit GUI bez zavislosti na starem MELB.exe.
