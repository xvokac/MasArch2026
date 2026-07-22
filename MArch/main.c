/*
  Name: MArch.exe                                     ver. 1.0
  Copyright: Miroslav Vokac, 2003
  Author: Miroslav Vok·Ë
  Date: 27.10.03 17:11
  Description: ONLY CZECH VERSION

Program pro vypocet tvaru poruseni zdene klenby podle literatury:
Jacques Heyman: THE MASONRY ARCH

Metoda je zalozena na vyhledani tvaru poruseni plastickymi klouby. 


Program je nazvan "MArch.exe"

Pracuje ve dvou MODEs:
MODE1 - k zvojenemu zatizeni vypocita nasobek udane tloustky klenby
MODE2 - k zvolene tloustce klenby vypocte nasobek zadaneho zatizeni
*/

#include <stdio.h>
#include <stdlib.h>
#include <time.h>


#include "define.h"
#include "def_fce.h"

int main(int argc, char *argv[])
{ 
  // zacatek programu
  printf("\n");
  printf(" *******************\n");
  printf(" ***  MArch 1.0  ***\n");
  printf(" *******************\n");
  printf("\n");
  printf(" ***  START  ***\n");
  printf("\n");
  
  //jmeno vstupniho souboru
  c_file_in = (char *) malloc (13); //alokace pameti
  if (c_file_in == NULL)
    {
    printf(" *** ERROR *** Neni dostatek volne pameti!\n\n");
    system("PAUSE");
    exit(0);
    };
  printf(" *** INPUT FILE ***\n");
  if (argc < 2)
    {
    printf("\n Zadej jmeno vstupniho souboru: ");
    fgets (c_file_in, 12, stdin);
    for ( i=0; i<13; i++)
      {
      if (*(c_file_in + i) == '\n') *(c_file_in + i) = '\0';
      };
    *(c_file_in + 12) = '\0';
    }
  else strcpy(c_file_in, argv[1]);
  
  //otevreni vstupniho souboru
  printf("\n Otevirani vstupniho souboru \"%s\": ...", c_file_in);
  finput = fopen (c_file_in, "r"); 
  if (finput == NULL) 
    {
    printf("\n *** ERROR *** Vstupni soubor \"%s\" nebyl nalezen!", c_file_in);
    system("PAUSE");
    exit(0);
    }
  else printf(" OK\n");
        
  // cteni vstupnich dat
  fscanf(finput, "%d",&Npoints);  
  if (Npoints > MAXPOINTS) 
    {
    printf("\n *** ERROR *** Program podporuje maximalne %d bodu! (NW > %d)", 
            MAXPOINTS, 
            MAXPOINTS);
    return 0;
    };
  for (i=0; i<Npoints; i++) 
    {
    fscanf(finput, "%lf %lf %lf", &X[i], &Y[i], &NasD[i]);
    };
  fscanf(finput, "%d", &NW);
  if (NW > MAXPOINTS) 
    {
    printf("\n *** ERROR *** Program podporuje maximalne %d bodu! (NW > %d)", 
            MAXPOINTS, 
            MAXPOINTS);
    return 0;
    };
  for (i=0; i<NW; i++) 
    {
    fscanf(finput, "%lf %lf", &XW[i], &W[i]);
    };
  fscanf(finput, "%d", &NP);
  if (NP > MAXNP) 
    {
    printf("\n *** ERROR *** Program podporuje maximalne %d bodu! (NP > %d)", 
            MAXNP, 
            MAXNP);
    return 0;
    };
  for (i=0; i<NP; i++) 
    {
    fscanf(finput, "%lf %lf", &XP[i], &P[i]);
    };
  fscanf(finput, "%d", &NumRand);
  fscanf(finput, "%d", &MODE);
  fscanf(finput, "%d", &Ngen);
  // konec - cteni vstupnich dat  
  
  // uzavreni vstupniho souboru
  fclose(finput);
  
  // testovani nactenych dat
  #ifdef TEST
  foutput = fopen("output1.txt", "w");
  if (MODE == 1)
    {
    fprintf(foutput, 
            "\n Geometrie oblouku (Npoints = %d):\n X[m] Y[m] 1/D[-]", 
            Npoints);
    }
  else
    {
    fprintf(foutput, 
            "\n Geometrie oblouku (Npoints = %d):\n X[m] Y[m] D[m]", 
            Npoints);
    };
  for (i=0; i<Npoints; i++) 
    {
    fprintf(foutput, "\n %f %f %f", X[i], Y[i], NasD[i]);
    };
  fprintf(foutput, "\n Stale zatizeni (NW = %d):\n XW[m] W[kN]", NW);
  for (i=0; i<NW; i++) 
    {
    fprintf(foutput, "\n %f %f", XW[i], W[i]);
    };
  fprintf(foutput, "\n Vnejsi zatizeni (NP = %d):\n XP[m] P[kN]", NP);
  for (i=0; i<NP; i++) 
    {
    fprintf(foutput, "\n %f %f", XP[i], P[i]);
    };
  fprintf(foutput, "\n Argument pro funkci srand() je: %d", NumRand);
  fprintf(foutput, "\n Vypocet v rezimu: MODE%d", MODE);
  fprintf(foutput, 
          "\n Pocet generovanych tvaru poruseni v 1 generaci: %d", Ngen);
  fclose(foutput);
  #endif  
  // konec - testovani vstupnich dat
  
  // pro testovani MODE2 podle knihy J.Heymana
  #ifdef HEYMAN_MODE2
  if (MODE != 1)
    {
    for (i=0; i<Npoints; i++)
      {
      NasD[i] =  NasD[i] * 0.252982;
      };
    };
  #endif
  
  // Generovani bodu poruseni 
  srand(NumRand);
  
  // ZAlozeni vystupniho souboru
  #ifdef TEST_GEN
  //alokace pameti
  c_file_out = (char *) malloc (13); //alokace pameti
  if (c_file_out == NULL)
    {
    printf(" *** ERROR *** Neni dostatek volne pameti!\n\n");
    system("PAUSE");
    exit(0);
    };
  printf("\n *** OUTPUT FILE ***\n");
  if (argc < 3)
    {
    printf("\n Zadej jmeno vystupniho souboru (existujici bude prepsan): ");
    fgets (c_file_out, 12, stdin);
    for ( i=0; i<13; i++)
      {
      if (*(c_file_out + i) == '\n') *(c_file_out + i) = '\0';
      };
    *(c_file_out + 12) = '\0';
    }
  else strcpy(c_file_out, argv[2]);  
  
  
  //zapnuti/vypnuti vypisu chybovych hlaseni na obrazovku
  if (argc >= 4) err = *(argv[3]);   
  while(err!= 'Y' && err!= 'N')
    {
    printf("\n Zapnou vypis chyb na obrazovku? <Y/N>: ");
    err = getchar();
    getchar();    
    }; 
  //zapnuti/vypnuti vypisu generovanych tvaru poruseni na obrazovku
  if (argc >= 5) list = *(argv[4]);   
  while(list!= 'Y' && list!= 'N')
    {
    printf("\n Zapnou vypis generovanych tvaru do souboru? <Y/N>: ");
    list = getchar();
    getchar();    
    }; 
  
  //oterreni vystupniho souboru  
  printf("\n Otevirani vystupniho souboru \"%s\": ...", c_file_out);
  fout2 = fopen(c_file_out,"w");
  if (fout2 == NULL) 
    {
    printf("\n *** ERROR *** Vystupni soubor \"%s\" nebyl vytvoren!", fout2);
    system("PAUSE");
    exit(0);
    }
  else printf(" OK\n");  
  //hlavicka vystupniho souboru
  fprintf(fout2, " Input file: %s\n", c_file_in);
  time (&cas);
  fprintf(fout2, " Start of computation: %s\n\n", ctime(&cas));
  if (list == 'Y')
    {
    fprintf(fout2, "# No. |");
    fprintf(fout2, " Generovane_body_poruseni Tvar_poruseni |");
    fprintf(fout2, " Result |");
    fprintf(fout2, " Vysledne_body_poruseni Vysledny_tvar_poruseni |");
    fprintf(fout2, " D[m] alfa[-] H[kN] V[kN] EpsH[m]"); 
    };  
  fclose(fout2);
  #endif
  
    
  
  
  //Start vypoctu
  printf("\n *** COMPUTATION ***\n");
  if (err = 'N') printf ("\n Probiha vypocet... ");
  Tstart = clock();  //zahajeni vypoctu
  
#ifdef GENEROVAT  
for (igen=0; igen<Ngen; igen++)
{
#endif  

  // nastaveni Gauss_testu na 0 - nenastal ERROR
  Gauss_test = 0;
  // NASTAVENI Oscil_testu na 0 - nenastala oscilace (ERROR)
  Oscil_test = 0;
  // nastaveni historie pro kontrolu konvergence
  for (i=0; i<NPINS; i++)
    {
    H1Pins[i]=0;
    H2Pins[i]=0;
    H3Pins[i]=0;
    H1ID[i]=0;
    H2ID[i]=0;
    H3ID[i]=0;
    };    
  // Generovani prvniho bodu
  Pins [0] = rand()*(Npoints)/RAND_MAX ;    
  // Generovani ostatnich bodu
  for (i=1; i<NPINS; i++) 
    {
    test = 1;                            // 1 jestlize se bod opakuje                              
    while (test != 0) 
      {
      Pins [i] = rand()*(Npoints)/RAND_MAX;     
      test = 0;
      for (j=0; j<i; j++)
        {
        if (Pins[i] == Pins[j]) test = 1;
        };
      };
    };    
  // body je potreba seradit vzestupne
  test = 1;
  while (test != 0)
    {
    test = 0;    
    for (i=0; i<(NPINS-1); i++) 
      {   
      if (Pins[i] > Pins [i+1])
        {
        pom = Pins[i];
        Pins[i] = Pins[i+1];
        Pins[i+1] = pom ;
        test = 1;
        };
      };
    };
  // konec generovani bodu poruseni
  // generovani orientace poruseni v koubu
  for (i=0; i<NPINS; i++)
    {
    IDPins[i] = (rand()% 2) ;
    };
  
  #ifdef TEST
  //testovani tvaru poruseni
  foutput = fopen("output1.txt", "a");
  fprintf(foutput, "\n Generovane body pro tvar poruseni:\n ");
  for (i=0; i<NPINS; i++)
    {
    fprintf(foutput, " %d", Pins [i]);
    };
  fprintf(foutput, "\n Generovana orientace pootoceni v kloubech:\n ");
  for (i=0; i<NPINS; i++)
    {
    fprintf(foutput, " %d", IDPins [i]);
    };
  fclose(foutput);
  #endif
  
  #ifdef TEST_GEN
  if (list == 'Y')
    {
    fout2 = fopen(c_file_out,"a");
    fprintf(fout2, "\n# %d |", igen);  
    for (i=0; i<NPINS; i++)
      {
      fprintf(fout2, " %d", Pins [i]);
      };  
    for (i=0; i<NPINS; i++)
      {
      fprintf(fout2, " %d", IDPins [i]);
      };
    fprintf(fout2, " |");
    fclose(fout2);
    };
  #endif
  
  // test podle knihy J.Heymana
  // definuje klouby podle knihy
  #ifdef HEYMAN
  Pins[0] =0;
  Pins[1] =5;
  Pins[2] =6;
  Pins[3] =11;
  IDPins[0] =0;
  IDPins[1] =0;
  IDPins[2] =0;
  IDPins[3] =1; 
  printf("\n * Nastaven testovaci tvar poruseni podle J.Heymana! *");
  #endif

  
#ifdef ITEROVAT  
test = 1;  
while (test == 1)  
{
#endif    
  // sestaveni rovnic a reseni soustavy rovnic
  if (MODE == 1)
    {
    // sestaveni soustavy rovnic MODE1
    for (i=0; i<(NPINS-1)*(NPINS-1); i++)
      {      
      A[i] = 0;  //nulovani pole A        
      };
    mode1A1(A, X, Pins, NPINS);
    mode1A2(A, X, Pins, NPINS, P, XP, NP);
    mode1A2(A, X, Pins, NPINS, W, XW, NW);
    mode1A3(A, Pins, NPINS, IDPins, NasD);
    mode1B(B, Y, Pins, NPINS);
    #ifdef TEST
    // kontrolni vystup soustavy rovnic
    foutput = fopen("output1.txt", "a");
    fprintf(foutput, "\n Soustava rovnic [A]*{C}={B} ve tvaru [A|B]:");
    for (i=0; i<(NPINS-1); i++)
      {
      fprintf(foutput, "\n %f %f %f | %f", 
                  A[(NPINS-1)*i], 
                  A[(NPINS-1)*i+1], 
                  A[(NPINS-1)*i+2], 
                  B[i]);
      };
    fclose(foutput);
    #endif
    // reseni soustavy rovnic
    if (GaussElim(A, B, C, (NPINS-1)) == 1)
      {
      if (err == 'Y')
        {
        printf("\n *** ERROR *** Gaussova eliminace - lin. zavisle radky!!! ");
        printf("\n               #%d. generovany tvar", igen);
        };
      Gauss_test = 1;
      test = 0;
      SUM_Gauss_Error = SUM_Gauss_Error + 1;
      };
    if (Gauss_test != 1) 
      {
      // vypocet hlavich neznamych
      D = C[2];
      H =  1 / C[1];
      V = C[0] * H ;
      #ifdef TEST
      // kontrolni vystup hlavnich neznamych
      foutput = fopen("output1.txt", "a");
      fprintf(foutput, "\n Neznamy vektor {C}:");    
      fprintf(foutput, "\n %f %f %f", C[0], C[1], C[2]);    
      fprintf(foutput, "\n Hlavni nezname:\n D[m] H[kN] V[kN]\n");    
      fprintf(foutput, " %f %f %f", D, H, V);
      fclose(foutput);
      #endif
      };
    }
  else 
    {
    // sestaveni soustavy rovnic MODE2
    mode2A1(A, X, Pins, NPINS);
    mode2A2(A, Y, NasD, Pins, NPINS, IDPins);
    mode2A3(A, X, Pins, NPINS, P, XP, NP);
    mode2B(B, X, Pins, NPINS, W, XW, NW);    
    #ifdef TEST
    // kontrolni vystup soustavy rovnic
    foutput = fopen("output1.txt", "a");
    fprintf(foutput, "\n Soustava rovnic [A]*{C}={B} ve tvaru [A|B]:");
    for (i=0; i<(NPINS-1); i++)
      {
      fprintf(foutput, "\n %f %f %f | %f", 
                  A[(NPINS-1)*i], 
                  A[(NPINS-1)*i+1], 
                  A[(NPINS-1)*i+2], 
                  B[i]);
      };
    fclose(foutput);
    #endif
    // reseni soustavy rovnic
    if (GaussElim(A, B, C, (NPINS-1)) == 1)
      {
      if (err == 'Y')
        {
        printf("\n *** ERROR *** Gaussova eliminace - lin. zavisle radky!!! ");
        printf("\n               #%d. generovany tvar", igen);
        };
      Gauss_test = 1;
      test = 0;
      SUM_Gauss_Error = SUM_Gauss_Error + 1;
      };
    if (Gauss_test !=1)
      {
      // vypocet hlavich neznamych
      alfa = C[2];
      H = C[1];
      V = C[0];
      #ifdef TEST
      // kontrolni vystup hlavnich neznamych
      foutput = fopen("output1.txt", "a");
      fprintf(foutput, "\n Neznamy vektor {C}:");    
      fprintf(foutput, "\n %f %f %f", C[0], C[1], C[2]);    
      fprintf(foutput, "\n Hlavni nezname:\n alfa[-] H[kN] V[kN]\n");    
      fprintf(foutput, " %f %f %f", alfa, H, V);
      fclose(foutput);
      #endif
      };
    };
  if (Gauss_test != 1)
    {
    // Vypocet V, H, EpsH na pravem konci klenby
    V = V + alfa * SumF(P, XP, NP, X[Pins[NPINS-1]], X[Npoints - 1]) 
        + SumF(W, XW, NW, X[Pins[NPINS-1]], X[Npoints - 1]);
    EpsH = ( alfa * SumM(P, XP, NP, X[Pins[NPINS-1]], X[Npoints - 1])
        + SumM(W, XW, NW, X[Pins[NPINS-1]], X[Npoints - 1]) 
        - V * (X[Npoints - 1] - X[Pins[NPINS-1]]) ) / H
        + Y[Pins[NPINS-1]] - Y[Npoints - 1] 
        + IDPins[NPINS-1] * NasD[Pins[NPINS-1]] * D ;
    // H svoji hodnotu nemeni
  
    // Tvar tlakove cary e[i] - odchylky od strednice klenby
    for (i=0; i<Npoints; i++)
      {
      e[i] = 1/H * ( - alfa * SumM(P, XP, NP, X[i], X[Npoints - 1])
                   - SumM(W, XW, NW, X[i], X[Npoints - 1]) 
                   + V * (X[Npoints - 1] - X[i]) )
           - (Y[i] -  Y[Npoints - 1] - EpsH);
      e[i] = e[i] - (NasD[i] * D) / 2  ;    
      };
    #ifdef TEST
    // kontrolni vystup tvaru tlakove cary
    foutput = fopen("output1.txt", "a");
    fprintf(foutput, "\n Tvar tlakove cary:");  
    fprintf(foutput, "\n X[m] e[m] D/2[m]");
    for (i=0; i<Npoints; i++)
      {  
      fprintf(foutput, "\n %f %f %f", X[i], e[i], NasD[i] * D/2);    
      };
    fclose(foutput);
    #endif    
    
    // Testovani tvaru tlakove cary
    test = 0;
    for (i=0; i<Npoints; i++)
      {
      if ( fabs(e[i]) > TOLERANCE * (NasD[i] * D/2) ) 
        {
        test = 1;
        };
      };
    if (D<0 || alfa<0) test = 1;
    if (test != 0)
      {    
      #ifdef TEST  
      foutput = fopen("output1.txt", "a");
      fprintf(foutput, "\n Tvar tlakove cary nesplnuje predpoklady!");  
      fclose(foutput);
      #endif    
      };  
      
    // Ulozeni stareho tvaru do historie
    for (i=0; i<NPINS; i++)
      {
      H1Pins[i]= H2Pins[i];
      H2Pins[i]= H3Pins[i];
      H3Pins[i]= Pins[i];
      H1ID[i]=H2ID[i];
      H2ID[i]=H3ID[i];
      H3ID[i]=IDPins[i];
      };
  
    // Novi kandidati plastickych kloubu  
    for (i=0; i<Npoints; i++)
      {
      eDIV[i] = e[i] / (NasD[i] * D/2);
      };  
    finder(eDIV, Npoints, Pins, IDPins, NPINS);
    if (D < 0 || alfa < 0)
      {
      for (i=0; i<NPINS; i++)
        {
        if (IDPins[i] == 0) IDPins[i] = 1;
        else IDPins[i] = 0;
        };
      };  
    #ifdef TEST  
    //testovani noveho tvaru poruseni
    foutput = fopen("output1.txt", "a");
    fprintf(foutput, "\n Novy tvar poruseni:\n ");
    for (i=0; i<NPINS; i++)
      {
      fprintf(foutput, " %d", Pins [i]);
      };
    fprintf(foutput, 
           "\n Orientace pootoceni v kloubech pro novy tvar poruseni:\n ");
    for (i=0; i<NPINS; i++)
      {
      fprintf(foutput, " %d", IDPins [i]);
      };
    fclose(foutput);
    #endif
    
    //testovani konvergence nebo oscilace iteracniho vypoctu
    Oscil_test=1;
    for(i=0; i<NPINS; i++)  //test pred-minuleho tvaru poruseni
      {
      if (H2Pins[i] != Pins [i]) Oscil_test = 0;
      else if ( H2ID[i] != IDPins[i]) Oscil_test = 0;
      };
    if (Oscil_test == 0)   //pred-minuly tvar neni totozny
      {
      Oscil_test=1;
      for(i=0; i<NPINS; i++) //test pred-pred-minuleho tvaru
        {
        if (H1Pins[i] != Pins [i]) Oscil_test = 0;
        else if ( H1ID[i] != IDPins[i]) Oscil_test = 0;
        };
      }
    if (Oscil_test == 1)
      {
      test = 0;
      if (err == 'Y')
        {
        printf("\n *** ERROR *** Reseni osciluje!!! ");
        printf("\n               #%d. generovany tvar", igen);
        };
      SUM_Oscil_Error = SUM_Oscil_Error + 1;
      };
    
    };
  
#ifdef ITEROVAT
} ;
#endif
  
  // vystup do souboru    
  #ifdef TEST_GEN
  if (list == 'Y')
    {
    fout2 = fopen(c_file_out,"a");
    if (Gauss_test != 1 && Oscil_test != 1)
      { 
      fprintf(fout2, " OK |");    
      for (i=0; i<NPINS; i++)
        {
        fprintf(fout2, " %d", Pins [i]);
        };
      for (i=0; i<NPINS; i++)
        {
        fprintf(fout2, " %d", IDPins [i]);
        };    
      fprintf(fout2, " | %f %f %f %f %f", D, alfa, H, V, EpsH);
      }
    else
      {
      fprintf(fout2, " ERROR");
      };
    fclose(fout2);
    };
  #endif
  // vyhodnoceni konecneho vysledku
  if (Gauss_test != 1 && Oscil_test != 1)
    {
    if (SUM_OK == 0) 
      {
      SUM_OK = 1;
      for (i=0; i<NPINS; i++)
        {
        Result_Pins[i] = Pins[i];
        Result_ID[i] = IDPins[i];
        };
      Result_D = D;
      Result_alfa = alfa;
      Result_H = H;
      Result_V = V;
      Result_EpsH = EpsH;
      }
    else
      {
      if ( (MODE == 1 && Result_D > D) || (MODE == 2 && Result_alfa < alfa) )
        {
        SUM_OK = 1;
        for (i=0; i<NPINS; i++)
          {
          Result_Pins[i] = Pins[i];
          Result_ID[i] = IDPins[i];
          };
        Result_D = D;
        Result_alfa = alfa;
        Result_H = H;
        Result_V = V;
        Result_EpsH = EpsH;
        };
      if ( (MODE == 1 && Result_D == D) || (MODE == 2 && Result_alfa == alfa) )
        {
        SUM_OK = SUM_OK + 1;
        };      
      };
    };
  
#ifdef GENEROVAT
} ;
#endif  

Tstop = clock();  //konec vypoctu

  #ifdef TEST_GEN  
  // Vypis vysledku vypoctu na obrazovku  
  printf("\n\n");
  printf(" ***  RESULTS  ***\n");
  printf("\n");
  printf(" Cas vypoctu: %6.2f sec\n", 
            (Tstop - Tstart) / (double) CLOCKS_PER_SEC);
  printf(" Vypocet probehl v MODE %d\n", MODE);
  printf(" Parametr generatoru: %d\n", NumRand);  
  printf("\n");
  printf(" Pocet generovanych tvaru poruseni: %d\n", Ngen);
  printf(" - pocet vysledku OK:        %3d\n", SUM_OK);
  printf(" - pocet ERROR_GaussElim:    %3d\n", SUM_Gauss_Error);
  printf(" - pocet ERROR_Oscilace:     %3d\n", SUM_Oscil_Error);
  printf(" - pocet ostatnich vysledku: %3d\n", 
            Ngen - SUM_OK - SUM_Gauss_Error - SUM_Oscil_Error);
  printf("\n");
  printf(" | Vysledne_body_poruseni | Vysledny_tvar_poruseni |\n |");
  for (i=0; i<NPINS; i++)
      {
      printf(" %d", Result_Pins[i]);
      };  
  printf(" |");   
  for (i=0; i<NPINS; i++)
      {
      printf(" %d", Result_ID[i]);
      }; 
  printf(" |\n\n");    
  printf(" D[m] alfa[-] H[kN] V[kN] EpsH[m]\n"); 
  printf(" %f %f %f %f %f\n", 
          Result_D, Result_alfa, Result_H, Result_V, Result_EpsH); 
  #endif
  
  // Vypis vysledku do souboru  
  fout2 = fopen(c_file_out,"a");
  fprintf(fout2, "\n\n");
  fprintf(fout2, " ***  RESULTS  ***\n");
  fprintf(fout2, "\n");
  fprintf(fout2, " Cas vypoctu: %6.2f sec\n", 
                 (Tstop - Tstart) / (double) CLOCKS_PER_SEC);
  fprintf(fout2, " Vypocet probehl v MODE %d\n", MODE);
  fprintf(fout2, " Parametr generatoru: %d\n", NumRand);  
  fprintf(fout2, "\n");
  fprintf(fout2, " Pocet generovanych tvaru poruseni: %d\n", Ngen);
  fprintf(fout2, " - pocet vysledku OK:        %3d\n", SUM_OK);
  fprintf(fout2, " - pocet ERROR_GaussElim:    %3d\n", SUM_Gauss_Error);
  fprintf(fout2, " - pocet ERROR_Oscilace:     %3d\n", SUM_Oscil_Error);
  fprintf(fout2, " - pocet ostatnich vysledku: %3d\n", 
            Ngen - SUM_OK - SUM_Gauss_Error - SUM_Oscil_Error);
  fprintf(fout2, "\n");
  fprintf(fout2, " | Vysledne_body_poruseni | Vysledny_tvar_poruseni |\n |");
  for (i=0; i<NPINS; i++)
      {
      fprintf(fout2, " %d", Result_Pins[i]);
      };  
  fprintf(fout2, " |");   
  for (i=0; i<NPINS; i++)
      {
      fprintf(fout2, " %d", Result_ID[i]);
      }; 
  fprintf(fout2, " |\n\n");    
  fprintf(fout2, " D[m] alfa[-] H[kN] V[kN] EpsH[m]\n"); 
  fprintf(fout2, " %f %f %f %f %f\n", 
          Result_D, Result_alfa, Result_H, Result_V, Result_EpsH);   
  // konecny Tvar tlakove cary e[i] - odchylky od strednice klenby
  D = Result_D;
  alfa = Result_alfa;
  H = Result_H;
  V = Result_V;
  EpsH = Result_EpsH;
  for (i=0; i<Npoints; i++)
    {
    e[i] = 1/H * ( - alfa * SumM(P, XP, NP, X[i], X[Npoints - 1])
                   - SumM(W, XW, NW, X[i], X[Npoints - 1]) 
                   + V * (X[Npoints - 1] - X[i]) )
           - (Y[i] -  Y[Npoints - 1] - EpsH);
    e[i] = e[i] - (NasD[i] * D) / 2  ;    
    };
  // hodnoty vnitrnich sil
  printf("\n\n");
  printf(" ***  Internal forces ***\n\n");
  printf(" Program pocita vysledne vnitrni sily... ");  
  fprintf(fout2, "\n\n Internal forces:\n");
  fprintf(fout2, " Point H[kN] V[kN] e[m] e/D[-] M[kNm]\n");
  for (i=0; i<Npoints; i++)
    {
    fprintf(fout2, " %d %f %f %f %f %f\n", i , H, 
          (V - alfa * SumF(P, XP, NP, X[i], X[Npoints-1]) 
             - SumF(W, XW, NW, X[i], X[Npoints - 1])),
          e[i],
          e[i] / NasD[i] * D,
          H * e[i]
          ); 
    };
  fclose(fout2);  
  printf("OK\n");
  
  // graficky vystup pro program AutoCAD
  printf("\n\n");
  printf(" ***  AutoCAD  Commands ***\n\n");
  printf(" Program generuje prikazy pro AutoCAD... ");
  fout2 = fopen(c_file_out,"a");
  fprintf(fout2, "\n\n AutoCAD commands:\n\n");
  for (i=0; i<(Npoints-1); i++)
    {    
    fprintf(fout2, "line %f,%f %f,%f \n\n", X[i], Y[i], X[i+1], Y[i+1]);
    fprintf(fout2, "line %f,%f %f,%f \n\n", X[i], (Y[i] + NasD[i] * D), 
                                         X[i+1], (Y[i+1] + NasD[i+1] * D));
    fprintf(fout2, "line %f,%f %f,%f \n\n", X[i], (Y[i] + NasD[i] * D / 2 + e[i]), 
                                    X[i+1], (Y[i+1] + NasD[i+1] * D / 2 + e[i+1]));
    };
  fclose(fout2);  
  printf("OK\n");
  
  

  // ukonceni programu
  printf("\n");
  printf(" ***  END  ***\n");
  printf("\n");
  
  printf("\n");
  system("PAUSE");
  return 0;
}
