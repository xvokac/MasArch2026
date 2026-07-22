// funkce pro program HINGE.exe

#ifndef STDARG
  #include <stdarg.h>
  #define STDARG
#endif


///////////////////////////////////////////////////////////////////////////
//deklarace funkci

//FileName - input file NEBO output file
/*
vrati jmeno jsouboru, ktere precte z klavesnice nebo vezme n-ty argument z prikazove radky
FID = 1 - vstupni soubor (je testovano, jestli existuje)
FID != 1 - vystupni soubor
FID = 2 - vystupni soubor - jestlize existuje jiz nejaky stejneho jmena, hlasi ERROR
CODE = 1 - cte argument z prikazove radky, jestlize v prikazove radce zadan, pak cte jmeno z klavesnice
CODE != 1 - cte jen z klavesnice
argc, argv - argumenty z prikazove radky
*/
char *FileName (int FID, int CODE, int n, int argc, char *argv[]) ;

//jump - preskoci vse do konce radky
int jump(FILE *f);

//print_results - tiskne zaverecne vysledky do souboru
void print_results(FILE *f, int N, double P[], double M[]);

//read_input - cte data ze vstupniho souboru *** NEFUNGUJE!!! ***
/*
cte jako scanf(), ale jestlize po "bilem" znaku 
nasleduje @ - tak zbytek do konce radku preskoci - t.j. bere jako poznamku
*/
void read_input(FILE *stream, const char *format, ...);




/////////////////////////////////////////////////////////////////////////
// DEFINICE

//FileName - input file NEBO output file
//cte jmeno z klavesnice nebo n-ty argument z prikazove radky
//FID = 1 - vstupni soubor, jinak vystupni
//FID = 2 - vystupni soubor - jestlize existuje jiz nejaky stejneho jmena, hlasi ERROR
//CODE = 1 cte argument z prikazove radky, 
//jestlize nebyl zadan, pak cte z klavesnice
//CODE != 1 cte jen z klavesnice
char *FileName (int FID, int CODE, int n, int argc, char *argv[]) 
  {
  // deklarace promennych
  int i;  
  FILE *f;
  char *c_file;
  // promenna pro jmeno souboru
  c_file = (char *) malloc (13); //alokace pameti
  if (c_file == NULL)
    {
    printf(" *** ERROR *** Neni dostatek volne pameti!\n\n");
    system("PAUSE");
    exit(0);
    };
  // nacteni jmena souboru  
  if (FID == 1) printf("\n *** INPUT FILE ***\n");
  else printf("\n *** OUTPUT FILE ***\n"); 
  if (FID != 1 && FID != 2) printf("\n Existujici vystupni soubor bude prepsan!");  
  if (CODE == 1 && argc >= n+1) 
    {
    strcpy(c_file, argv[n]);
    }    
  else 
    {    
    if (FID == 1) printf("\n Zadej jmeno vstupniho souboru: ");
    else printf("\n Zadej jmeno vystupniho souboru: ");
    fgets (c_file, 12, stdin);
    for ( i=0; i<13; i++)
      {
      if (*(c_file + i) == '\n') *(c_file + i) = '\0';
      };
    *(c_file + 12) = '\0';
    };
  // testovani jmena souboru - existence
  if (FID == 1)
    {
    f = fopen (c_file, "r"); 
    if (f == NULL) 
        {
        printf("\n *** ERROR *** Vstupni soubor \"%s\" nebyl nalezen!\n", c_file);
        system("PAUSE");
        exit(0);
        }
    else printf("\n OK\n");
    fclose(f);
    };
  if (FID != 2 && FID != 1)
    {
    f = fopen (c_file, "a"); 
    if (f != NULL) 
        {
        printf("\n Vystupni soubor \"%s\" jiz existuje a bude prepsan!\n", c_file); 
        printf("\n\n OK\n");      
        }
    else printf("\n OK\n");
    fclose(f);
    };
  if (FID == 2)
    {
    f = fopen (c_file, "a"); 
    if (f != NULL) 
        {
        printf("\n *** ERROR *** Vystupni soubor \"%s\" jiz existuje!\n", c_file);
        system("PAUSE");
        exit(0);
        }
    else printf("\n OK\n");
    fclose(f);
    };      
  return c_file;
  }
  
  
//jump - preskoci vse do konce radky nebo konce souboru
// vrati 1 (nasel se konec radky) nebo 0 (nasel se konec souboru)
int jump(FILE *f)
  {
  int KONEC = -1;
  int c; 
  while (KONEC == -1)
    {
    if ( (c=getc(f)) == EOF) KONEC = 0;
    if (c == '\n') KONEC = 1; 
    };
  return KONEC;
  }


//print_results - tiskne zaverecne vysledky do souboru
void print_results(FILE *f, int N, double P[], double M[])
  {
  int i;
  fprintf(f, " %d\n %f\n\n", N, *(P + N));
  for (i=0; i<=N; i++)
    {
    fprintf(f, " %f %f\n", *(P + i), *(M + i));
    };    
  }
  
  
//read_input - cte data ze vstupniho souboru *** NEFUNGUJE!!!!! ***
/*
cte jako fscanf(), ale jestlize po "bilem" znaku 
nasleduje @ - tak zbytek do konce radku preskoci - t.j. jedna se o poznamku
*/
void read_input(FILE *stream, const char *format, ...)
  {
  //deklarace pomocnych promennych
  int KONEC = 0;
  int redy = 0;
  int c;
  va_list argumenty;
  
  //lze cist max 1 parametr!!! jinak mohou byt komplikace
  
  //cteni ze souboru - testovani dat
  while (redy == 0)
    {
    c = getc(stream);
    putchar(c);
    switch (c)
      {
      case '@':
        {  
        while (KONEC == 0)
          {
          if (getc(stream) == '\n') KONEC = 1;
          };
        KONEC = 0;
        redy = 0;
        };
      case 32:      //space - mezera
      case 2:        //TAB - tabel8tor
      case 10:     redy = 0; //odradkovani '\n'
      default: 
        {
        redy = 1;      // na zacatku platneho cteni
        ungetc(c, stream);
        };
      };
    };
    
  // cteni   ze souboru - od mista platneho cteni
  va_start(argumenty, format);
  fscanf(stream, format, argumenty);
  }
  
  
    

