***************************************
Zakladni informace o programu MArch.exe
***********************************************
Posledni aktualizace: 26.07.04 15:39

 M. Vokac
***********************************************

Program slouzi k vypoctu zdenych kleneb. Jedna se o priblizne reseni.
Zakladni algoritmus vypoctu vychazi z knihy J. Heymana: THE MASONRY ARCH,
kde se hledaji plasticke klouby a tvar poruseni klenby.  

Ke kolapsu klenby dochazi, jestlize vzniknou 4 kouby (k pohybu podpor se 
neprihlizi, proto 3 klouby neznamenaji kolaps konstrukce). V plastickych
kloubech musi prochazet vyslednicova cara (funicular polygon) bodem 
ve vzdalenosti D/2 od teziste. Tyto body se pouzivaji pri vypostu k momentove
podmince rovnovaze.

Heyman dale zavadi "geometrical safety factor", ktery by mel byt min. 2.
Jestlize chceme vyloucit tahove trhliny tak min. 3.
Jedna se o tzv. "middle half rule" a "middle third rule".

Program nejprve natipuje nejaky tvar poruseni. Sestavi podminky rovnovahy ke 
3 bodum klenby, velikost a polohu vypocte reakci a potom take tlakovou caru.
Podle tvaru tlakove cary opravi predpoklad o poloze plastickych kloubu a vypocet
se opakuje.

Jedna se o iteracni zpusob vypoctu. Prvni tvar poruseni je nahodne generovan.
Dale se voli tavr poruseni takovy, aby nejlepe odpovidal tvaru vyslednicove cary
z predchoziho iteracniho kroku. 


Pro vypocteny tvar tvakove cary se urci pravdepodobna poloha plastickych kloubu.
V plastickzch kloubech je predem dan bod, kterym musi vyslednicova cara 
prochazet a ke kterym se stanovuji podminky rovnovahy, z kterych se spoctou
hledane veliciny. 

Hlenane veliciny jsou:
a)svisle a vodorovne reakce, 
b)pusobiste reakci, 
c)vyska klenby (MODE1) nebo max. velikost nahodileho zatizeni (MODE2).

Program ma 2 zakladni MODEs
MODE1 - pro dane zatizeni spocte nutnou tloustku klenby podle pravidla
        "middle-half rule"
MODE2 - pro danou tloustku klenby vypocte maximalni velikost 
        nahodileho zatizeni jako nasobek zadanych danych hodnot (rovnez
        podle pravidla "middle-half rule")



Konvergence reseni:
*******************        
Iteracni proces muze zkolabovat pri nekolika udalostech:
1) nageneruje (vypocte) se pro dalsi krok tvar poruseni, ktery vede na rovnici 
   s linearne zavyslymi radky (iteracni vypocet se ukonci a oznami se ERROR),
2) vysledny tvar poruseni osciluje mezi dvema tvary (iteracni vypocet se ukonci 
   a oznami se ERROR),
3) pri testovani programu v MODE 2 bylo odhaleno, ze muze nastat oscilace nejen 
   mezi dvemi tvary poruseni, ale opakuje se sekvence tri tvaru (iteracni 
   vypocet se ukonci a oznami se ERROR). 
Je-li to v programu zadano parametrem [err], tak pri vypisu na obrazovku 
se vypise, jesti chyba byla zpusobena oscilaci reseni nebo linearne 
zavyslymi radky v matici soustavy rovnic.   
   
Pri testovani programu podle prikladu v knize J. Heymana byl pri testovani 
v MODE 1 nalezen jen jeden pripad oscilace reseni v 12 x 100 = 1200 nahodne 
generovanych tvarech poruseni. Oscilace uzce souvisi s mnozstvim bodu pri 
diskreditaci klenby. Mensi mnozstvi bodu zpusobi vetsi pravdepodobnot vyskytu 
oscilace pri iteracnim resni.

Pri testovani programu v MODE 2 byla oscilace daleko castejsi a vyskytlo se 
opakovani sekvence 3 tvaru poruseni, coz se pri testovani v MODE 1 nevyskytlo.
Testy ukazaly, ze oscilace je pri reseni v MODE 2 nekolikanasobne castejsi.

Pokud nenastane pripad 1) ani pripad 2) resp. 3), tak vypocet konverguje 
k nejakemu konkretnimu reseni tvaru poruseni. Rozhodujici je takove reseni, 
kdy:
a) v MODE1 je minimalni tloustka klenby,
b) v MODE2 je maximalni velikost zatizeni.

Pri testovani programu podel prikladu v knize J.Heymana bylo generovano
nekolik sad, kazda se 100 tvary poruseni a s odlisnou hodnotou NumRand,
coz je argument pro generator pseudo-nahodnych cisel. 
Vysledky byly nasledujici:

A) Testovani probihalo v MODE1:
NumRand ERRORS  OK      OTHERS
50      24      16      60
500     17      10      73
7500    21      12      67
333     15      7       78
250     20      12      68
750     17      6       77
1000    11+1*)  13      75
1001    25      5       70
2500    17      16      67
25      17      16      67
75      20      10      70
5000    20      13      67

B) Testovani probihalo v MODE2:
NumRand ERRORS  OK      OTHERS
50      38+5    12      45
500     34+5    12      49
7500    36+4    21      39
333     38+4    21      37
250     41+4    17      38
750     43+2    17      38
1000    32+5    22      41
1001    36+4    23      37
2500    40+2    14      44
25      40+2    15      43
75      47+6    14      33
5000    55+2    14      29

Legenda:
NumRand - argument pro generator pseudo-nahodnych cisel,
ERRORS - linearne zavisle radky soustavy rovnic + oscilace reseni,
OK - hledany vysledek (minimalni tloustka klenby),
OTHERS - ostatni vysledky.  
*) jediny nalezeny pripad oscilace iteracniho reseni v MODE1


Priklad vstupniho souboru pro MArch.exe:
****************************************
Soubor je textovy bez jakychkoli poznamek - tedy jen cisla. 
V tomto souboru ma text vysvetlujici formu. 
Proto se tento soubor bez vymazani vysvetlujiciho textu 
neda jako vstupni soubor pouzit.

//Diskretizace oblouku 
13                              // pocet bodu
0     0     2.638               // hodnoty X[m], Y[m], 1/D[-] (resp. D[m])
0.6	  1.03	1.618                
1.2	  1.65	1.313               // kde:  X[m] x-souradnice bodu "intrados"
1.8	  2.08	1.161                        Y[m] y-souradnice bodu "intrados"
2.4	  2.37	1.077                        1/D[-] revativni tloustka klenby
3	  2.56	1.028                        D[m] tloustka kleny
3.6	  2.66	1.004                        ("tloustka" ve svislem smeru!!!)
4.2	  2.56	1.028
4.8	  2.37	1.077
5.4	  2.08	1.161
6	  1.65	1.313
6.6	  1.03	1.618
7.2	  0	    2.638

//Stale zatizeni
11                              // pocet sil reprezentujici stale zatizeni
0.6   25.3                      // X[m], W[kN]
1.2   19.3
1.8   15.2                      // kde  X[m] je x-souradnice pusobiste sily
2.4   12.5                              W[kN] je sila staleho zatizeni
3     10.8
3.6   10.0
4.2   10.8
4.8   12.5
5.4   15.2
6     19.3
6.6   25.3

//Vnejsi - nahodile zatizeni
1                               // pocet sil nahodileho zatizeni
1.8   40.0                      // kde  X[m] je x-souradnice pusobiste sily
                                        P[kN] je sila staleho zatizeni

100000                          // paraametr pseudo-nahodneho generatoru  

      
1                             // MODE - 1 pocita tloustku klenby
                                      - 2 pocita max. nasobek vnejsiho zatizeni

100                              // pocet generovanych tvaru poruseni        
 

**************** END OF input FILE *******************


Start programu
**************

Spusti se z prikazove radky prikazem "march".
Lze sputit i nekolika parametry, ktere nejsou povine:

march [inputfile [outputfile [err [list]]]]

march - nazev programu
inputfile - nazev vstupniho souboru (textovy soubor)
outputfile - nazev vystupniho souboru (textovy soubor)
err - parametr, ktery zapina nebo vypina zapis chybovych hlaseni na 
      obrazovku. Pismeno "Y" zapina a "N" vypina vypis.
list - parametr, ktery zapina nebo vypina zapis generovanych tvaru poruseni
      klenby do vystupniho souboru. Pismeno "Y" zapina a "N" vypina vypis.
      
Pokud nektery parametr neni uveden, program jeho hodnotu bude vyzadovat po
jeho spusteni.


Vystup programu:
****************
Vystupem jsou body poruseni - cisla bodu diskretovaneho oblouku od 1 do n
Tvar poruseni v kloubu - 0 jestlize je tlak na dolnim lici
                       - 1 jeslize je tlak u horniho lice klenby
D - tloustka klenby - pri vypoctu v MODE 1
alfa - nasobek zatizeni - pri vypoctu v MODE 2
H - vodorovna slozka sily v bode n
V - svisla slozka sily v dobe n
EpsH - svisla vzdalenost vodorovne slozky sily v bode n od dolniho lice klenby


