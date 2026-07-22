/*MELB.EXE

Program pro výpoèet klenbové konstrukce
pomocí øešení stability rigidních blokù /jako linearni optimalizcni problem
reseny simplexovou metodou/

M. Gilbert, Proff. C. Melbourne:
Rigid-block analysis of masonry structures
The Structure Engineer/Vol 72/No 21/1 November 1994
a dalsi literatura.....

Posrobne informace viz MELB.TXT.     
*/

//hlavickove soubory
#include <stdio.h>
#include <stdlib.h>
//globalni parametry
#define MAX_NF 10    //max pocet sil vnejsiho zatizeni (live load)
#define D_ITER_EPS 1e-2   //max. chyba pri itercnim vypoctu
#define VER 1.2      //verze programu
//#define FINTAB     //vypise puvodn tabulku i finalni vysledky simplexove 
                     //metody do kontrolniho souboru "sim_tab.txt"
//#define MATRIXAB   //vypise transformacni matice A a B(jestlize s_b>0)
                     //do kontrolniho textoveho souboru "AB.txt"
//#define BOUSSINESQ   //tiskne roznesene vnejsi zatizeni do kontrolniho souboru "Boussin.txt"

//hlavickove soubory - definovane uzivatelem
#include "nrutil.h"
#include "nrutil.c"
#include "simplex.h"
#include "polint.h"
#include "funkce.h"
#include "crush.h"


int main(int argc, char *argv[])
{ 
  //deklarace globalnich parametru a promennych
  #include "define.h"
  
  //start programu
  printf(" *** start programu MELB.exe ver. %2.1f ***\n\n", VER);
  
  //jmeno projektu
  f_get_name(s_in,  s_txt, s_AB,
             s_sim, s_out, argc, argv);
  
  //cteni parametru vstupniho souboru
  f_in = fopen (s_in, "r");
  if(!f_in) nrerror(" Vstupni soubor neexistuje!");
  f_read1(f_in, &L, &f, &geom_CODE, &D, &gama, &s_b, &N, &NF, PoleF, &HFill, 
          &GamaFill, &AlfaFill, &Q_CODE, KFill, &d_CODE, &d_sigma, s_inter);
  fclose(f_in);
  
  printf("\n *** start vypoctu ***\n");
  
  //alokovani pameti pro matice
  intrados = matrix(0, N, 1, 2);
  extrados = matrix(0, N, 1, 2);
  centrums = matrix(1, N, 1, 2);
  dead_load = vector(1, N);
  actingpoints = matrix(1, N, 1, 2);
  live_load = vector(1, N);
  fill_load = matrix(1, N, 1, 4);
  ge2 = matrix(0, N, 1, 4);
  p2 = matrix(1, N+1, 1, 3);
  q2 = matrix(1, N+1, 1, 3); 
  fill2 = matrix(1, N+1, 1, 3);   
  
  //hlavcka textoveho souboru
  ff = fopen(s_txt, "w");
  fprintf(ff, "Vstupni soubor: %s\n", s_in);
  fprintf(ff, "***kopie vstupniho souboru***\n");
  f_in = fopen(s_in, "r");
  write_f_to_f(f_in, ff);
  fclose(f_in);
  fprintf(ff, "*****************************\n");
  fclose(ff);
  
  //vypocet ortogonalnich souradnic uzlovych bodu bloku
  printf("\n Vypocet ortogonalnich souradnic...");
  switch (geom_CODE)
  {
      case 1:
          geom1(L, f, D, N, intrados, extrados);
          break;
      case 2:
          geom2(L, f, D, N, intrados, extrados);
          break;
      default:
          nrerror(" Nespravna hodnota geom_CODE - povolena 1 nebo 2");
  }    
  ff = fopen(s_txt, "a");
  fprintf(ff, "Ortoganalni souradnice intrados a extrados:\n");
  fprintf(ff, "X_int\tY_int\tX_ext\tY_ext\n");
  for (i=0; i<=N; i++)
    {
    fprintf(ff, "%f\t%f\t%f\t%f\n", intrados[i][1], intrados[i][2],
                                  extrados[i][1], extrados[i][2]);
    }
  fclose(ff);
  
  //vlastni tiha klenby
  printf("\n Vlastni tiha klenby...");
  cal_dead_load(gama, N, intrados, extrados, centrums, dead_load);
  ff = fopen(s_txt, "a");
  fprintf(ff, "Vlastni tiha klenby - jednotlive bloky:\n");
  fprintf(ff, "X_p\tY_p\tP\n");
  for (i=1; i<=N; i++)
    {
    fprintf(ff, "%f\t%f\t%f\n", centrums[i][1], centrums[i][2], dead_load[i]);
    }
  fclose(ff);
  
  //zatizeni nadnasypem
  printf("\n Zatizeni nadnasypem...");
  cal_fill_load(GamaFill, N, extrados, HFill, D, f, fill_load);
  ff = fopen(s_txt, "a"); 
  fprintf(ff, "Tiha nadnasypu pusobici na bloky:\n");
  fprintf(ff, "P\th_ver\tX_p\tY_p\n");
  for (i=1; i<=N; i++)
  {
      fprintf(ff, "%f\t%f\t%f\t%f\n", fill_load[i][1],fill_load[i][2],
                                      fill_load[i][3],fill_load[i][4]); 
  }
  fclose(ff);    
  
    
  //vnejsi zatizeni(ronaseni a rozpocitani na bloky)
  printf("\n Vnejsi sily...");
  cal_live_load(N, extrados, NF, PoleF, actingpoints, 
                live_load, Q_CODE, AlfaFill, (D + f + HFill));
  ff = fopen(s_txt, "a");
  fprintf(ff, "Vnejsi zatizeni pusobici na bloky:\n");
  fprintf(ff, "X_q\tY_q\tQ\n");
  for (i=1; i<=N; i++)
    {
    fprintf(ff, "%f\t%f\t%f\n", actingpoints[i][1], 
                               actingpoints[i][2], 
                               live_load[i]);
    }
  fclose(ff);
  
  //geometrie v polarnich souradnicich
  printf("\n Polarni souradnice...");
  geom_polar(N, intrados, extrados, ge2);
  if (d_CODE == 3) modif_d_CODE3(N, ge2);
  ff = fopen(s_txt, "a");
  fprintf(ff, "Ortogonalni lokalni souradnice jednotlivych bloku:\n");
  fprintf(ff, "a\talfa\tb\tbeta\n");
  for (i=0; i<=N; i++)
    {
    fprintf(ff, "%f\t%f\t%f\t%f\n", ge2[i][1], ge2[i][2], ge2[i][3], ge2[i][4]);
    }
  fclose(ff);
  
  //vlastni tiha - k bodu "0" bloku
  printf("\n Transformace vlastni tihy...");
  cal_pq2(N, intrados, extrados, centrums, dead_load, p2);
  ff = fopen(s_txt, "a");
  fprintf(ff, "Transformovane zatizeni vlastni tihou klenby:\n");
  fprintf(ff, "Px\tPy\tMp\n");
  for (i=1; i<=N+1; i++)
    {
    fprintf(ff, "%f\t%f\t%f\n", p2[i][1], p2[i][2], p2[i][3]);
    }
  fclose(ff);
  
  //zatizeni nadnasypem - k bodu "0" bloku 
  printf("\n Transformace zatizeni nadnasypem...");
  cal_fill2(N, intrados, extrados, KFill, fill_load, fill2);
  ff = fopen(s_txt, "a");
  fprintf(ff, "Transformovane zatizeni nadnasypem:\n");
  fprintf(ff, "Px\tPy\tMp\n");
  for (i=1; i<=N+1; i++)
    {
    fprintf(ff, "%f\t%f\t%f\n", fill2[i][1], fill2[i][2], fill2[i][3]);
    }
  fclose(ff);
  
  //vnejsi zatizeni - k bodu "0" bloku 
  printf("\n Transformace vnejsich sil...");
  cal_pq2(N, intrados, extrados, actingpoints, live_load, q2);
  if (KFill[0] != 0. && KFill[4] == 1.) modif_q2(N, q2, ge2, KFill);    //soucinitel zeniho tlaku aplikovan na sily od dopravy
  ff = fopen(s_txt, "a");
  fprintf(ff, "Transformovane zatizeni vnejsich sil:\n");
  fprintf(ff, "Qx\tQy\tMq\n");
  for (i=1; i<=N+1; i++)
    {
    fprintf(ff, "%f\t%f\t%f\n", q2[i][1], q2[i][2], q2[i][3]);
    }
  fclose(ff);
  
  //sestaveni matice transformace
  printf("\n Transformacni matice vektoru deformaci...");
  fAB = fopen(s_AB, "wb");
  cal_AB(N, s_b, ge2, fAB);
  fclose(fAB);  
  
  #ifdef MATRIXAB
  //kontrolni tisk transformacnich matic [A] [B] do souboru
  //cte binarni soubor a prepise ho do textoveho souboru "AB.txt"
  ff = fopen("AB.txt", "w");
  fAB = fopen(s_AB, "rb");
  if (s_b <= 0.) n = (N+1) * 2;
  else n = (N+1) * 4;
  float B;
  for (i=1; i<=n; i++)
  {
      for (j=1; j<=3*(N+1); j++)
      {
          fread(&B, sizeof(B), 1, fAB);
          fprintf(ff, " %f", B);
      }
      fprintf(ff, "\n");
  }        
  fclose(ff);
  fclose(fAB);
  #endif

new_soil_press:  //sem se vraci vypocet po oprave bocniho zatizeni z nasypu
  
  //sestaveni rovnic a nerovnic pro simplexovou metodu  
  printf("\n Rovnice a nerovnice pro simlexovou metodu...");
  ff = fopen(s_sim, "wb");
  write_simplex_tab(ff, s_AB, N, s_b, p2, q2, fill2);  
  fclose(ff);
  
  //uvolnìní pamìti
  free_matrix(intrados, 0, N, 1, 2);
  free_matrix(extrados,0, N, 1, 2);
  free_matrix(centrums,1, N, 1, 2);
  free_vector(dead_load,1, N);
  free_matrix(actingpoints,1, N, 1, 2);
  free_vector(live_load,1, N);
  
  
  /*Nacteni siplexove tabulky*/  
  //cteni rozmeru simplexove tabulky a CODE
  ff=fopen(s_sim, "rb");
  fread(&n, sizeof(n), 1, ff);
  fread(&m, sizeof(m), 1, ff);
  fread(&CODE, sizeof(CODE), 1, ff);
  //alokace pameti pro simplexovou metodu
  a = matrix(1, m+2, 1, n+1); 
  #ifdef FINTAB
  aa = vector(1, n+1); 
  tab = matrix(1, m+2, 1, m+n+2);
  #endif
  iposv = ivector(1, m);
  izrov = ivector(1, n);
  icase = (int *)malloc(sizeof(int));
  if (!icase) nrerror(" allocation failure!\n");
  X = vector(1, n);
  //cteni simplexove tabulky
  read_simplex_tab(ff, a, m, n, CODE, &m1, &m2, &m3);
  //uzavreni souboru
  fclose(ff);  
  
  #ifdef FINTAB
  //tisk puvodni simplexove tabulky
  ff=fopen("sim_tab.txt", "w");
  fprintf(ff, " Puvodni simplexová tabulka:\n");
  fprintf_matrix(a, 1, m+2, 1, n+1, ff);
  fclose(ff);  
  //zalohovani argumentu cilove funkce - tj. 1. radek matice float **a
  object_fce(a, aa, n);
  #endif
  
  //vypocet simplexovou metodou
  printf("\n Vypocet simplexovou metodou...");
  simplx(a, m, n, m1, m2, m3, icase, izrov, iposv);
  printf (" icase = %d", *icase); 
  
  #ifdef FINTAB
  //urceni kompletni finalni simplexove tabulky
  cal_final_tab(a, aa, iposv, izrov, tab, m, n);  
  //kontrolni tisk finální simplexove tabulky do souboru
  ff=fopen("sim_tab.txt", "a");
  fprintf(ff, " Finální simplexová tabulka:\n");
  fprintf_matrix(a, 1, m+2, 1, n+1, ff);
  fprintf(ff, " Vektor iposv:\n");
  iprintf_vector(iposv, 1, m, ff);
  fprintf(ff, " Vektor izrov:\n");
  iprintf_vector(izrov, 1, n, ff);
  fprintf(ff, " Finální simplexová taulka - celá:\n");
  fprintf_matrix(tab, 1, m+2, 1, m+n+2, ff);
  fclose(ff);
  #endif
    
  //prevod hodnot matice a z ulohy maximalizace zpet na minimalizaci
  if (CODE < 0) a_modif(a, m, n);
  
  //stanoveni vektoru lokalnich deformaci X a minimalni prace W = lambda
  simpl_results(a, m, n, izrov, iposv, X, &W);
  printf (" & lambda = %f", W); 
  
  
  //stanoveni velikosti normalovych sil a excentricity
  N_e = matrix(1, 2, 0, N);  //matice normalovych sil a excentricit
  if (d_CODE != 3) cal_N_e(a, izrov, n, N_e, N, D);
  else //tlakova cara jen v jadru prurezu 
  {
      cal_N_e(a, izrov, n, N_e, N, D/3.);
      modif2_d_CODE3(N, N_e, D);
  }    
  
  //v pripade uvazovani usmyknuti - vypocet posouvajicich sil v sparach
  if (s_b > 0.)
  {
      T = vector(0, N);
      cal_T(a, izrov, n, N, T);
  }
   
      
  //ulozeni dat do vystupniho souboru
  printf("\n Ulozeni vysledku...");
  ff = fopen(s_out, "w");
  write_output(ff, icase, W, N, n, X, N_e);
  if (s_b > 0.)  //prida se vektor posouvajicich sil
  {
      write_output_T(ff, T, N);    
  }    
  fclose(ff); 
  ff = fopen(s_txt, "a"); //ulozeni tehoz do textoveho souboru
  fprintf(ff, "\n*** vysledky vypoctu ***\n");
  write_output(ff, icase, W, N, n, X, N_e);
  if (s_b > 0.)  //prida se vektor posouvajicich sil
  {
      write_output_T(ff, T, N);    
  }    
  fclose(ff); 
  
  //Oprava bocniho zemniho tlaku - podle vypoctenych deformaci
  if (KFill[0] == 2.) 
  {
     modif_lateral_soil_pressure(N, X, KFill, fill2, s_AB, s_b, ge2, q2);
     KFill[0] = 0.;
     printf("\n Prepocet bocniho zemniho tlaku...");
     ff = fopen(s_out, "a");
     fprintf(ff, "\n*** Po prepocitani zemniho tlaku ***\n");
     fclose(ff);
     ff = fopen(s_txt, "a");
     fprintf(ff, "\n*** Po prepocitani zemniho tlaku ***\n");     
     fprintf(ff, "\nNove transformovane zatizeni nadnasypem:\n");
     for (i=1; i<=N+1; i++)
     {
         fprintf(ff, "%f\t%f\t%f\n", fill2[i][1], fill2[i][2], fill2[i][3]);
     }
     if (KFill[4] == 1.)
     {
         fprintf(ff, "\nNove transformovane zatizeni vnejsich sil:\n");
         for (i=1; i<=N+1; i++)
         {
             fprintf(ff, "%f\t%f\t%f\n", q2[i][1], q2[i][2], q2[i][3]);
         }
     }    
     fclose(ff);     
     goto new_soil_press; //opakuje nulty krok pro opravene bocni zatizeni
  }
   
  
  switch(d_CODE)
  {
      case 0:
      case 3:
          //pokud neni druhym argumentem z prikazove radky "1", potom se smazou vsechny
          //pomocne soubory
          if(argc < 3 || atoi(argv[2]) != 1) 
                     f_remove_files(s_txt, s_AB, s_sim);
          //konec programu  
          printf("\n\n *** konec programu ***\n\n");
          system("PAUSE");	
          return 0;
      case 1:
          //iterace podle Livesley-e,
          printf("\n Iterovani vypoctu podle Livesleye...");
          break;
      case 2:
          //iterace podle Crisfield-a & Packham-a
          printf("\n Iterovani vypoctu podle Crisfielda & Packhama...");
          break;
      case 4:
          //iterace podle zadaneho interakcniho diagramu
          printf("\n Iterovani vypoctu podle daneho interakcniho diagramu v souboru %s...", s_inter);
          break;
      default:
          nrerror(" nespravny d_CODE - povolene hodnoty 0, 1 nebo 2");
  }    
  
  /////////////////////////////////////////////////////////////////////////
  //ITERACNI VYPOCET
  //priprava na iteraci
  //alokovani potrebnych poli
  d_crush = vector(0, N);
  ge3 = matrix(0, N, 1, 4); 
  if (d_CODE == 2) dis = vector(0, N); //disipovana prace v kloubech
  //urceni velikosti d_crush
  if (d_CODE == 4) cal_d_crush2(N, s_inter, N_e, d_crush, D);
  else cal_d_crush(N, d_sigma, N_e, d_crush);
  ff = fopen(s_txt, "a"); //ulozeni do textoveho souboru
  switch(d_CODE)
  {
      case 1:
      case 2:
          fprintf(ff, " Vektor d_crush:\n");
          break;
      case 4:
          fprintf(ff, " Vektor e_min:\n");
          break;
  }    
  fprintf_vector(d_crush, 0, N, ff);
  fclose(ff); 
  
iterovat:  //sem se vraci vypocet pri iteracnim vypoctu

  //zalohovani predchoziho vysledku - load factor
  W_ = W;
  //pocitadlo iterace zvetsit o 1
  ItNo++;
  printf("\n * Iterace c. %d *\n", ItNo);     
  //fiktivni tloustka - uprava geom2
  modif_geom2(N, ge2, ge3, d_crush, d_CODE);    
  //nova transformacni matice
  fAB = fopen(s_AB, "wb");
  cal_AB(N, s_b, ge3, fAB);
  fclose(fAB);   
  //nove nerovnice pro simplexovou metodu
  ff = fopen(s_sim, "wb");
  write_simplex_tab(ff, s_AB, N, s_b, p2, q2, fill2);    
  fclose(ff); 
  //disipovane sily - v kloubech
  if( d_CODE == 2) cal_dis(dis, N, d_sigma, d_crush);  
  //rozmer simplexove tabulky a CODE - ty zustavaji stejne, jen posun pozice
  ff=fopen(s_sim, "rb");
  fseek(ff, 3 * sizeof(int), SEEK_CUR);  
  //cteni simplexove tabulky
  read_simplex_tab(ff, a, m, n, CODE, &m1, &m2, &m3);
  //uzavreni souboru
  fclose(ff);  
  //pripocteni disipovanych sil
  if(d_CODE == 2) modif_a_dis(a, dis, N);
  //novy vypocet simplexovou metodou   
  simplx(a, m, n, m1, m2, m3, icase, izrov, iposv);
  printf (" icase = %d", *icase);   
  //prevod hodnot matice a z ulohy maximalizace zpet na minimalizaci
  if (CODE < 0) a_modif(a, m, n);  
  //stanoveni vektoru lokalnich deformaci X a minimalni prace W = lambda
  simpl_results(a, m, n, izrov, iposv, X, &W);
  printf (" & lambda = %f", W);   
  //stanoveni velikosti normalovych sil a excentricity
  N_e = matrix(1, 2, 0, N);  //matice normalovych sil a excentricit
  switch(d_CODE)
  {
      case 1:
      case 4:
          cal1_N_e(a, izrov, n, N_e, N, D, ge3);
          break;
      case 2:
          cal2_N_e(a, izrov, n, N_e, N, D, ge3, dis);
          break;
      default:
          nrerror(" Neplatna hodnota d_CODE!");
  }    
  //v pripade uvazovani usmyknuti - vypocet posouvajicich sil v sparach
  if (s_b > 0.)
  {
      T = vector(0, N);
      cal_T(a, izrov, n, N, T);
  }
  //ulozeni dat do vystupniho souboru
  printf("\n Ulozeni vysledku...");
  ff = fopen(s_out, "a");
  fprintf(ff, "\n * Iterace c. %d * Delta = %f *\n", ItNo, W_ - W);
  write_output(ff, icase, W, N, n, X, N_e);
  if (s_b > 0.)  //prida se vektor posouvajicich sil
  {
      write_output_T(ff, T, N);    
  }    
  fclose(ff); 
  ff = fopen(s_txt, "a"); //ulozeni tehoz do textoveho souboru
  fprintf(ff, "\n * Iterace c. %d * Delta = %f *\n", ItNo, W_ - W);
  write_output(ff, icase, W, N, n, X, N_e);
  if (s_b > 0.)  //prida se vektor posouvajicich sil
  {
      write_output_T(ff, T, N);    
  }    
  fclose(ff); 
  //urceni velikosti d_crush
  if (d_CODE == 4) cal_d_crush2(N, s_inter, N_e, d_crush, D);
  else cal_d_crush(N, d_sigma, N_e, d_crush);
  ff = fopen(s_txt, "a"); //ulozeni do textoveho souboru
  switch(d_CODE)
  {
      case 1:
      case 2:
          fprintf(ff, " Vektor d_crush:\n");
          break;
      case 4:
          fprintf(ff, " Vektor e_min:\n");
          break;
  } 
  fprintf_vector(d_crush, 0, N, ff);
  fclose(ff); 
  
  //preruseni vypoctu, jestlize icase!=0
  switch(*icase)
  {
      case -1:
          nrerror(" Nelze splnit omezujici podminky - geometricky zamknuta klenba.");  
          break;
      case 1:
          nrerror(" Klenba zatizena jen stalym zatizenim je nestabilni.");
          break;
  }     
  
  //rozhodnuti o iteraci
  if ( fabs(W_ - W) > D_ITER_EPS) goto iterovat;
  
  //konec programu  
  printf("\n\n *** konec programu ***\n\n");
  system("PAUSE");	
  return 0;  
}
