// deklarace a definice funkci pro HINGE.exe
// vypocitava interakcni diagram pro kloub ve zdene konstrukci
/*
podle predpokladu z clanku:
Thomas E. Boothby: Elastic plactic stability of jointed masonry arches..
Engineering Structures, Vol. 19, No. 5, pp. 345-351, 1997

V pruøezu mùže v daném bodì napìtí nabývat pouze buï hodnotu NULA 
nebo hodnotu SIGMA%MAX. Takže tato formulace pøedstavuje plastický prùbìh
napìtí v prùøezu - obdobnì jako napìtí v betonu pøi plastickém návrhu ŽB

*/

#ifndef MATH
  #include <math.h>
  #define MATH
#endif


//////////////////////////////////////////////////////////////
//deklarace funkci

//maxM - maximalni ohybovy moment
double fce2_maxM(double b, double h, double sigma);

//maxP - maximalni osova sila
double fce2_maxP(double b, double h, double sigma);

//MproP - vypocte ohybovy moment pro zvolenou osovou silu
double fce2_MproP(double P, double maxP, double maxM);

//fce2 - vypocet interakcniho diagramu
int fce2(FILE *f, int N, double P[], double M[]);

//////////////////////////////////////////////////////////////
//definice funkci

//maxM - maximalni ohybovy moment
/*
b - sirka prurezu
h - vyska prurezu
sigma - max. normalove napeti
*/
double fce2_maxM(double b, double h, double sigma)
  {
  double M;
  M = 0.125 * b * h * h * sigma;
  return M;
  }
  
//maxP - maximalni osova sila
/*
b - sirka prurezu
h - vyska prurezu
sigma - max. normalove napeti
*/
double fce2_maxP(double b, double h, double sigma)
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
double fce2_MproP(double P, double maxP, double maxM)
  {
  if ( P > maxP || P < 0 ) return 0.0;
  else 
    {
    /*
    interaction aquation:
    f(P,M)=(1/4)*(M/maxM)+(P/maxP)^2-(P/maxP)<=0
    */
    double M;
    M = 4 * maxM * ( P / maxP - pow(P/maxP, 2) );
    return M;
    };
  }
  
//fce2 - vypocet interakcniho diagramu
int fce2(FILE *f, int N, double P[], double M[])
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
  maxM = fce2_maxM(b, h, sigma);
  maxP = fce2_maxP(b, h, sigma);
  // urceni kroku DeltaP
  DeltaP = maxP / N;
  // interakcni diagram
  for(i=0; i<=N; i++)
    {
    *(P + i) = DeltaP * i;
    *(M + i) = fce2_MproP( *(P + i), maxP, maxM);
    };
  return 0;
  }
  

