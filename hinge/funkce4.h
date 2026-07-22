// deklarace a definice funkci pro HINGE.exe
// vypocitava interakcni diagram pro kloub ve zdene konstrukci

/*
podle predpokladu z clanku:
B.T.Rosson, T.E. Boothby: Hardening and shakedown of masonry arch joints
In: Arch Bridges, Sinopoli (ed.), 1998 Balkema, Rotterdam, ISBN 90 5809 012 4

- je vybran elasticky stav
*/

#ifndef MATH
  #include <math.h>
  #define MATH
#endif


//////////////////////////////////////////////////////////////
//deklarace funkci

//maxM - maximalni ohybovy moment
double fce4_maxM(double b, double h, double sigma);

//maxP - maximalni osova sila
double fce4_maxP(double b, double h, double sigma);

//MproP - vypocte ohybovy moment pro zvolenou osovou silu
double fce4_MproP(double P, double maxP, double maxM);

//fce2 - vypocet interakcniho diagramu
int fce4(FILE *f, int N, double P[], double M[]);

//////////////////////////////////////////////////////////////
//definice funkci

//maxM - maximalni ohybovy moment
/*
b - sirka prurezu
h - vyska prurezu
sigma - max. normalove napeti
*/
double fce4_maxM(double b, double h, double sigma)
  {
  double M;
  M = 0.09375 * b * h * h * sigma;
  return M;
  }
  
//maxP - maximalni osova sila
/*
b - sirka prurezu
h - vyska prurezu
sigma - max. normalove napeti
*/
double fce4_maxP(double b, double h, double sigma)
  {
  double P;
  P = b * h * sigma;
  return P;
  }

//MproP - vypocte ohybovy moment pro zvolenou osovou silu
/*
P - zvolena osova sila
maxP - maximalni osova sila
maxM - maximalni ohybovy moment
*/
double fce4_MproP(double P, double maxP, double maxM)
  {
  if ( P > maxP || P < 0 ) return 0.0;
  else 
    {
    double M;
    /*
    interaction aquation:
    (i)  f1(P,M)=(9/16)*(M/maxM)+(P/maxP)-1<=0
    (ii) f2(P,M)=(9/16)*(M/maxM)+4*(P/maxP)^2-3*(P/maxP)<=0
    Je treba royhodnout, kteremu dat prednost.
    Pro dane P lze vyjadrit M=f(P) takto:
    (i) M(i) = 16/9 * maxM * (1 - P / maxP)
    (ii) M(ii) = 16/9 * maxM * ( 3 * P/maxP - 4 * (P /maxP)^2)
    Pro vsechna P z intervalu <0; maxP> plati, ze M(i)<=M(ii).
    Krivky maji jeden spolecny bod P', ktery lze spocitat z rovnosti M(i)=M(ii):
    (1 - P' / maxP) = ( 3 * P'/maxP - 4 * (P' /maxP)^2)
    provedeme substituci x = P/maxP a potom lze sestavit rovnici:
    1 - x = 3x - 4x^2
    4x^2 - 4x + 1 = 0
    (2x - 1)^2 = 0
    resenim je tedy x = 1/2
    a hledanym bodem je P' = maxP / 2
    
    Je-li P >  P' rozhoduje M(i),
    je-li P <=  P' rozhoduje M(ii).    
    */    
    if (P > maxP/2)
      {
      M = 16./9. * maxM * ( 1 - P / maxP );
      }
    else
      {
      M = 16./9. * maxM * ( 3 * P / maxP - 4 * pow (P / maxP,2));
      };                         
    return M;
    };
  }
  
//fce4 - vypocet interakcniho diagramu
int fce4(FILE *f, int N, double P[], double M[])
  {
  // deklarace lok prom
  int i;
  double b, h, sigma, maxP, maxM;
  double DeltaP;
  // cteni ze souboru
  fscanf(f, "%lf", &b);
  fscanf(f, "%lf", &h);
  fscanf(f, "%lf", &sigma);
  // urceni max hodnot P a M
  maxM = fce4_maxM(b, h, sigma);
  maxP = fce4_maxP(b, h, sigma);
  // urceni kroku DeltaP
  DeltaP = maxP / N;
  // interakcni diagram
  for(i=0; i<=N; i++)
    {
    *(P + i) = DeltaP * i;
    *(M + i) = fce4_MproP( *(P + i), maxP, maxM);
    };
  return 0;
  }
  
