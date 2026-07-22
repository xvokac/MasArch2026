/*
Program HINGE.exe

poèítá interakèní diagram podle celkem 4 metod
detaily viz INFO.TXT
*/



#include <iostream>
#include <stdlib.h>

using namespace std;

// definice funkcí
#include "funkce1.h"
#include "funkce2.h"
#include "funkce3.h"
#include "funkce4.h"
#include "fce_prg.h"


int main(int argc, char *argv[])
{

  //deklarace globalnich promennych
  #include "global.h"
  
  //uvod
  printf("\n");
  printf("\n *********************************************");
  printf("\n ************    HINGE.exe 1.0    ************");
  printf("\n *********************************************");
  printf("\n");
  printf("\n (c) 2004, Miroslav Vokac (xvokac@centrum.cz)");
  printf("\n");
  printf("\n *** START ***");
  printf("\n");
  
  //otevreni vstupniho souboru
  fin = fopen(FileName(1, 1, 1, argc, argv), "r");
  fout = fopen(FileName(0, 1, 2, argc, argv), "w");

  
  //cteni dat ze vstupniho souboru
  if (jump(fin) == 0)    //preskoceni 1. radky - je rezervovana na poznamky
    {
    printf("\n *** ERROR *** Spatny format vstupniho souboru!\n");
    system("PAUSE");
    exit(0);
    };
  fscanf(fin, "%d", &METHOD); //cteni zpusobu vypoctu
  fscanf(fin, "%d", &N);       //cteni - pocet bodu diagramu
  if  ( N>NN || N<=0 )
    {
    printf("\n *** ERROR *** Neplatna hodnota N = %d! (0 < N <= %d)\n", N, NN);
    system("PAUSE");
    exit(0);
    };
  
  //urceni metody vypoctu
  switch(METHOD)
    {
    case 1:         
        fce1(fin, N, P, M);        
        break;
    case 2:         
        fce2(fin, N, P, M);        
        break;
    case 3:         
        fce3(fin, N, P, M);        
        break;
    case 4:         
        fce4(fin, N, P, M);        
        break;    
    default:         
        printf("\n *** ERROR *** Neplatna hodnota METHOD = %d!\n", METHOD);
        printf("\n * d musi byt z mnoziny (1, 2, 3, 4) *\n");
        system("PAUSE");
        exit(0);
        break;
    };
  //tisk vysledku do souboru
  fprintf(fout, " Interakcni diagram - METHOD=%d\n", METHOD);
  print_results(fout, N, P, M);
  //uzavreni souboru
  fclose(fin);
  fclose(fout);
  
  //konec
  printf("\n");
  printf("\n *** END ***");
  printf("\n");
  
  system("PAUSE");	
  return 0;
}
