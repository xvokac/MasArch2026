////////////////////
// definice globalnich parametru a promennych
///////////////////////



//////////////////////////
// globalni promenne

//vstupni parametry - ze vstupniho souboru
float L, f, D, gama, s_b;  //svetla vyska, vzepeti, tloustka klenby, objem. tiha, coefficient of separation between blocks
int N;           //pocet bloku klenby
int NF;          //pocet vnejsich sil
float **PoleF;      //pole vnejsich sil
float HFill ;        //vyska nadnasypu nad korunou klenby
float GamaFill;      //objemova tiha nadnasypu
float AlfaFill;      //uhel roznaseni nadnasypem (ve vstupnim soiboru ve stupnich, potom se preposte na radiany)
int geom_CODE ;    //typ geometrie (1 - kruhovy segment, 2 - parabolicky oblouk)
int Q_CODE;       //typ roznaseni (0 - bez roznaseni, 1 - rovnomerne, 2 - nerovnomerne)
float *KFill;        //soucinitele tykajici se zemniho tlaku
float d_sigma;     //omezeni normaloveho napeti
int d_CODE;      //0-infinitni napeti, 1-Livesley 2-Crishfield & Packham 


//parametry vypoctene
float **extrados, **intrados;      //ortogonalni souradnice uzlu bloku
float **centrums, *dead_load;      //vlastni tiha klenby
float **actingpoints, *live_load;  //vnejsi zatizeni
float **ge2;  //geometrie v polarnich souradnicich
float **p2;   //vlatsni tiha k bodu "0" bloku
float **q2;   //vnejsi zatizeni k bodu "0" bloku
float **fill_load; //zatizeni z nadnasypu
float **fill2; //transformovane zatizeni z nadnasypu

//pole pro simplexovou metodu
int m, n, m1, m2, m3;
int CODE;  //+1 pro maximalizaci, -1 pro minimalizaci
float **a;
#ifdef FINTAB
float *aa, **tab;
#endif
float *X;
int *iposv, *izrov, *icase;
float W;

//pole pro vnitrni sily
float **N_e;   //normalove sily ve sparach a jejich excentririta
float *T;      //posouvajici sily (positaji se, jestlize s_b>0

//promenne pro iteracni vypocet
float *d_crush;  //tloustka tlacene casti prurezu - plasticka teorie
float W_;        //predchozi vysledek - load factor
float **ge3;      //fiktivni tloustky pro iteracni vypocet
float *dis;     //matice s disipovanymi silami
int ItNo = 0;         //pocet iterace

//pomocne promenne
int i, j;

//nazvy souboru
char *s_in;   //vstupni soubor
char *s_txt;  //podrobny textovy vyis
char *s_AB;   //transformacni matice AB             
char *s_sim;  //matice pro simplexovou metodu
char *s_out;  //vystupni soubor
char *s_inter; //soubor s interakcnim diagramem

//promenne typu FILE *
FILE *f_in, *f_out;
FILE *ff;
FILE *fAB;

////////////////////////////////
// alokovani pameti
s_in = (char *)malloc(13);
s_txt = (char *)malloc(13);
s_AB = (char *)malloc(13);
s_sim = (char *)malloc(13);
s_out = (char *)malloc(13);
s_inter = (char *)malloc(13);
PoleF = matrix(0,2,1,MAX_NF);
KFill = vector(0, 4); //soucinitele zemniho tlaku 


