/*
Definovani globalnich promennych pro program MArch.exe
*/

// definování konstant
#define MAXPOINTS 100         // maximalni pocet bodu pro diskreditaci
#define NPINS 4               // pocet plastickych kloubu
#define MAXNP 10              // maximalni pocet vnejsich sil
#define TOLERANCE 1.0001      // tolerance pri testovani tavru poruseni

// podmineny preklad
//#define TEST                // pro testovani programu(podrobny vystup vypoctu)
#define ITEROVAT              // iteruje vypocet  
#define GENEROVAT             // generuje urcity pocet tvaru poruseni
#define TEST_GEN              // pro vystup generace do souboru
//#define HEYMAN              // nastavi pocatecni klouby podle knihy J.Heymana
//#define HEYMAN_MODE2        // test Heyman pro MODE2

// promenne pro geometrii konstrukce
double X [MAXPOINTS];      // X-sove souradnice bodu
double Y [MAXPOINTS];      // Y-one souradnice bodu
double NasD [MAXPOINTS];   // D - vyska prurezu v pode i
int Npoints;               // pocet bodu pro diskreditaci

// promenne pro vlastni tihu
int NW   ;                 // pocet sil pro vlastni tihu
double W [MAXPOINTS];      // pole sil pro vlastni tihu
double XW [MAXPOINTS];     // x-sove souradnice pro vlastni tihu

// promenne pro vnejsi sily
int NP;                    // poset sil pri vnejsi zatizeni
double P [MAXNP];          // pole sil pro vnejsi zatizeni
double XP [MAXNP];         // x-sove souradnice pro vnejsi zatizeni

// vektor ID pro tvar poruseni
int Pins [NPINS];          // vektor s rezy poruseni  
int IDPins [NPINS];        // vektor s 1-kladny moment v koubu, 0-zaporny 

// matice pro soustavu rovnic [A]*{C}={B}
double A [(NPINS-1)*(NPINS-1)] ;
double B [NPINS-1] ;
double C [NPINS-1] ;   

// hlavni vystupni promenne
double D = 1;           // nasobek tloustky klenby
double alfa = 1;        // nasobek vnejsiho zatizeni
double H, V;            // reakce klenby 
double EpsH;            // svisla souradnice H na pravem konci klenby
double e[MAXPOINTS];    // odchylky tlakove cary od strednice
double eDIV[MAXPOINTS]; // eDIV = e / (nasD * D/2)

// promenne typu FILE* pro vstup a vystup
FILE *finput;               // vstupni soubor
#ifdef TEST
FILE *foutput;              // vystupni soubor
#endif
#ifdef TEST_GEN
FILE *fout2;
#endif

// pomocne promenne 
int i;                      // pomocna promenna pro cykly
int j;                      // pomocna promenna pro cykly
int Ngen;                   // pocet generovanych tvaru
int igen ;                  // pro cykl generovani
int pom ;                   // pomocna promenna 
int test ;                  // testovaci promenna
int NumRand ;               // argument pro generovani RAND()
int MODE ;                  // MODE vypoctu MODE=1 - hleda k zatizeni nasobek D
                            //            MODE=2 - hleda pro D nasobek zatizeni
int err = 0;                // vypis chyb na obrazovku ('Y'==ON, 'N'==0FF)
int list = 0;               // vypis generovanych tvaru poruseni do souboru
                            // ('Y'==ON, 'N'==0FF)
int Gauss_test  ;           // "1" - lin. zavisle, soustava nema reseni
int Oscil_test  ;           // "1" - reseni osciluje => nekonverguje
int H1Pins[NPINS];          // historicke body poruseni
int H2Pins[NPINS];          // historicke body poruseni
int H3Pins[NPINS];          // historicke body poruseni
int H1ID[NPINS];            // historicke ID
int H2ID[NPINS];            // historicke ID
int H3ID[NPINS];            // historicke ID

// promenne pro konecne vysledky
int SUM_Gauss_Error = 0;  // pocet gen. tvaru, kde byly lin. zavisle radky
int SUM_Oscil_Error = 0;  // pocet tvaru, kde reseni oscilovalo
int SUM_OK = 0;           // pocet vysledku odpovidajici konecnym hodnotam  
int Result_Pins[NPINS];// vysledne body poruseni
int Result_ID[NPINS];  // vysledne ID
double Result_D;
double Result_alfa;
double Result_H;
double Result_V;
double Result_EpsH;

// jmena souboru
char *c_file_in;        //jmeno vstupniho souboru
char *c_file_out;       //jmeno vystupniho souboru

//promenne casu 
time_t cas;
clock_t Tstart, Tstop;


    





