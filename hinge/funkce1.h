// deklarace a definice funkci pro HINGE.exe
// vypocitava interakcni diagram pro kloub ve zdene konstrukci
/*
podle predpokladu z clanku:
N.Taylor, P.Mallinder: The brittle hinge in masonry arch mechanisms. 
The Structural Engineer/Volume 71/ No 20/19 October 1993/pp.359-366
*/

#ifndef MATH
  #include <math.h>
  #define MATH
#endif


//definovani konstant pro iteracni vypocet
#ifndef CHYBY
  #define CHYBA   0.1      //maximalni odchylka P pri vypoctu d_ef resp. eps2
  #define KROK_D_EF 0.000001       //delka kroku pri vypoctu d_ef
  #define KROK_EPS_2 0.000001      //delka kroku pri vypoctu eps2
  #define CHYBY
#endif


////////////////////////////////////////////////////////////////////////////
// DEKLARACE

//napeti jako funkce pretvoreni
double sigma(   double eps,         
                double sigma_m,     
                double eps_m,       
                int k);             
                
//napeti jako funkce y - uncrack
double sigma_y_uncrack(
                    double eps1,    
                    double eps2,    
                    double eps_m,   
                    double sigma_m,                     
                    double d,       
                    double y,       
                    int k);         
                    
//napeti jako funkce y - crack
double sigma_y_crack(
                    double eps1,                        
                    double eps_m,   
                    double sigma_m, 
                    double d_ef,    
                    double d,                          
                    double y,       
                    int k);         

// dP_uncrack               
double dP_uncrack(  double eps1,    
                    double eps2,    
                    double eps_m,   
                    double sigma_m, 
                    double b,       
                    double d,       
                    int k);         
                    
// dM_uncrack
double dM_uncrack(  double eps1,    
                    double eps2,    
                    double eps_m,   
                    double sigma_m, 
                    double b,       
                    double d,       
                    int k);         
                    
// dP_crack
double dP_crack  (  double eps1,                   
                    double eps_m,   
                    double sigma_m, 
                    double b,       
                    double d_ef,    
                    double d,       
                    int k);         

// dM_crack
double dM_crack  (  double eps1,                   
                    double eps_m,   
                    double sigma_m, 
                    double b,       
                    double d_ef,    
                    double d,       
                    int k);         
                    
// fce1 - výpoèet interakèního diagramu
int fce1(FILE *f, int N, double P[], double M[]);


                        


/////////////////////////////////////////////////////////////////////////////
// DEFINICE

//napeti jako funkce pretvoreni
double sigma(   double eps,         // dana hodnota pretvoreni
                double sigma_m,     // maximalni napeti
                double eps_m,       // odpovidajici pretvoreni
                int k)              // konstanta
  {
  double sig;
  sig = (k/(k-1)) * (eps/eps_m - (eps/eps_m)*k/k);
  return sig;
  }
  
//napeti jako funkce y - uncrack
double sigma_y_uncrack(
                    double eps1,    //pretvoreni hornich vlaken
                    double eps2,    //pretvoreni dolnich vlaken
                    double eps_m,   //pretvoreni pro sigma_m
                    double sigma_m, //maximalni tlakove napeti                    
                    double d,       //vyska prurezu - d
                    double y,       //souradnice y
                    int k)          //konstanta
  {
  double sigma;
  sigma = (((eps1+eps2)/2+y*(eps1-eps2)/d)/((k-1)*eps_m))*
          (k-pow(((eps1+eps2)/2+y*(eps1-eps2)/d)/eps_m, k-1));
  return sigma;
  }
  
//napeti jako funkce y - crack
double sigma_y_crack(
                    double eps1,    //pretvoreni hornich vlaken                    
                    double eps_m,   //pretvoreni pro sigma_m
                    double sigma_m, //maximalni tlakove napeti
                    double d_ef,    //ucinna vyska prurezu - d'
                    double d,       //vyska prurezu
                    double y,       //souradnice y
                    int k)          //konstanta
  {
  double sigma;
  sigma = (eps1*(1+y/d_ef-d/(2*d_ef))/
          ((k-1)*eps_m))*(k-pow(1+y/d_ef-d/(2*d_ef), k-1)
          *pow(eps1, k-1)/pow(eps_m,k-1));
  return sigma;
  }
  
  
// dP_uncrack               
double dP_uncrack(  double eps1,    //pretvoreni hornich vlaken
                    double eps2,    //pretvoreni dolnich vlaken
                    double eps_m,   //pretvoreni pro sigma_m
                    double sigma_m, //maximalni tlakove napeti
                    double b,       //sirska prurezu
                    double d,       //vyska prurezu
                    int k)          //konstanta
  {
  double dP;
  dP = sigma_m * b * d *(k * (eps1 + eps2)/2 + 
        (pow(eps2, k+1) - pow(eps1, k+1))/((k+1) * 
        (eps1-eps2) * pow(eps_m, k-1)))/((k - 1)*eps_m);
  return dP;
  }
  
// dM_uncrack
double dM_uncrack(  double eps1,    //pretvoreni hornich vlaken
                    double eps2,    //pretvoreni dolnich vlaken
                    double eps_m,   //pretvoreni pro sigma_m
                    double sigma_m, //maximalni tlakove napeti
                    double b,       //sirska prurezu
                    double d,       //vyska prurezu
                    int k)         //konstanta
  {
  double dM;
  dM = sigma_m * b * d * d *
        (
        k * (eps1 - eps2) / 12 
        - ( pow(eps1, k+1) + pow(eps2, k+1)) /
                        (2 * (k+1) * (eps1 - eps2) * pow(eps_m, k-1))
        + ( pow(eps1, k+2) - pow(eps2, k+2)) /
                        ((k+1) * (k+2) * pow(eps1-eps2, 2) * pow(eps_m, k-1))
        )/((k-1) * eps_m);
  return dM;
  }
  
// dP_crack
double dP_crack  (  double eps1,    //pretvoreni hornich vlaken               
                    double eps_m,   //pretvoreni pro sigma_m
                    double sigma_m, //maximalni tlakove napeti
                    double b,       //sirska prurezu
                    double d_ef,    //ucinna vyska prurezu - d'
                    double d,       //vyska prurezu
                    int k)          //konstanta
  {
  double dP;
  dP = sigma_m * b * eps1 * d_ef * 
        (k/2 - pow(eps1/eps_m, k-1)/(k+1)) / ((k-1)*eps_m);
  return dP;
  }
  
// dM_crack
double dM_crack  (  double eps1,    //pretvoreni hornich vlaken               
                    double eps_m,   //pretvoreni pro sigma_m
                    double sigma_m, //maximalni tlakove napeti
                    double b,       //sirska prurezu
                    double d_ef,    //ucinna vyska prurezu - d'
                    double d,       //vyska prurezu
                    int k)          //konstanta
 {
 double dM;
 dM = sigma_m * b * eps1 * d_ef *
       (
       k * (3 * d - 2 * d_ef)/6 
       - pow(eps1, k-1) * (d - 2 * d_ef /(k+2))/((k+1) * pow(eps_m, k-1))
       ) /
       (2 * (k-1) * eps_m);
 return dM;
 }
  
// fce1 - výpoèet interakèního diagramu
int fce1(FILE *f, int N, double P[], double M[])
  {
  // deklarace lok. prom.
  int i, j;
  double b, h, sigma_m, eps_m, lam, maxP;
  int k;
  int crack = 1;
  double DeltaP, eps1;
  double PP [2], d_ef[2], eps2[2], MM; //pomocne hodnoty pro iteraci
   
  // cteni ze souboru
  fscanf(f, "%lf", &b);
  fscanf(f, "%lf", &h);
  fscanf(f, "%lf", &sigma_m);
  fscanf(f, "%lf", &eps_m);
  fscanf(f, "%lf", &lam);
  fscanf(f, "%d", &k);
  // urceni max hodnoty P   
  maxP = b * h * sigma_m;
  // urceni kroku DeltaP
  DeltaP = maxP / N;
  
  // interakcni diagram
  *(P + 0) = 0.0;
  *(M + 0) = 0.0;
  *(P + N) = maxP;
  *(M + N) = 0.0;
  for(i=1; i<N; i++)
    {
    if (crack == 1)  // prurez s trhlinou
      {
      // nastaveni eps1
      eps1 = lam * eps_m;
      // odhad d_ef a prvni hodnota PP
      if (i==1) d_ef[0] = 2 * DeltaP * i / sigma_m / b; // jinak vysledek z predchoziho vypoctu
      PP[0] = dP_crack  ( eps1,    //pretvoreni hornich vlaken               
                          eps_m,   //pretvoreni pro sigma_m
                          sigma_m, //maximalni tlakove napeti
                          b,       //sirska prurezu
                          d_ef[0],    //ucinna vyska prurezu - d'
                          h,       //vyska prurezu
                          k);          //konstanta
      // iteracni vypocet velikosti d_ef
      while( fabs(PP[0] - DeltaP * i) > CHYBA)
        {
        d_ef[1] = d_ef[0] + KROK_D_EF;
        PP[1] = dP_crack  ( eps1,    //pretvoreni hornich vlaken               
                          eps_m,   //pretvoreni pro sigma_m
                          sigma_m, //maximalni tlakove napeti
                          b,       //sirska prurezu
                          d_ef[1],    //ucinna vyska prurezu - d'
                          h,       //vyska prurezu
                          k);          //konstanta
        d_ef[0] = d_ef[0] + 
                  (                        
                  (d_ef[1] - d_ef[0]) / (PP[1] - PP[0]) * (DeltaP * i - PP[0])
                  );
        PP[0] = dP_crack  ( eps1,    //pretvoreni hornich vlaken               
                          eps_m,   //pretvoreni pro sigma_m
                          sigma_m, //maximalni tlakove napeti
                          b,       //sirska prurezu
                          d_ef[0],    //ucinna vyska prurezu - d'
                          h,       //vyska prurezu
                          k);          //konstanta
        };
      // vypocet momentu MM pro danou hodnotu d_ef
      MM = dM_crack  (eps1,    //pretvoreni hornich vlaken               
                    eps_m,   //pretvoreni pro sigma_m
                    sigma_m, //maximalni tlakove napeti
                    b,       //sirska prurezu
                    d_ef[0],    //ucinna vyska prurezu - d'
                    h,       //vyska prurezu
                    k);          //konstanta
      // kontrola d_ef
      if (d_ef[0] > h) crack = -1;  //je treba opravit vypocet
      };
    if (crack != 1) //prurez bez trhliny
      {
      // odhad eps2, eps1 a prvni hodnota PP
      if (crack == -1)  //poprve pouzit vypocet bez trhliny
        {
        eps2[0] = 0;    //nastaveno jen poprve, jinak z predchoziho vypoctu
        crack = 0;
        };
      eps1 = lam * eps_m - (lam - 1) * eps2[0];
      PP[0] = dP_uncrack(  eps1,    //pretvoreni hornich vlaken
                    eps2[0],    //pretvoreni dolnich vlaken
                    eps_m,   //pretvoreni pro sigma_m
                    sigma_m, //maximalni tlakove napeti
                    b,       //sirska prurezu
                    h,       //vyska prurezu
                    k)  ;        //konstanta
      // iteracni vypocet eps2
      while( fabs(PP[0] - DeltaP * i) > CHYBA)
        {
        eps2[1] = eps2[0] + KROK_EPS_2;
        eps1 = lam * eps_m - (lam - 1) * eps2[0];
        PP[1] = dP_uncrack(  eps1,    //pretvoreni hornich vlaken
                    eps2[1],    //pretvoreni dolnich vlaken
                    eps_m,   //pretvoreni pro sigma_m
                    sigma_m, //maximalni tlakove napeti
                    b,       //sirska prurezu
                    h,       //vyska prurezu
                    k)  ;        //konstanta
        eps2[0] = eps2[0] + 
                  (                        
                  (eps2[1] - eps2[0]) / (PP[1] - PP[0]) * (DeltaP * i - PP[0])
                  );
        PP[0] = dP_uncrack(  eps1,    //pretvoreni hornich vlaken
                    eps2[0],    //pretvoreni dolnich vlaken
                    eps_m,   //pretvoreni pro sigma_m
                    sigma_m, //maximalni tlakove napeti
                    b,       //sirska prurezu
                    h,       //vyska prurezu
                    k)  ;        //konstanta
        };
      // vypocet momentu MM pro danou hodnotu eps2
      MM = dM_uncrack(  eps1,    //pretvoreni hornich vlaken
                    eps2[0],    //pretvoreni dolnich vlaken
                    eps_m,   //pretvoreni pro sigma_m
                    sigma_m, //maximalni tlakove napeti
                    b,       //sirska prurezu
                    h,       //vyska prurezu
                    k)     ;    //konstanta          
      
      };
    *(P + i) = PP[0];
    *(M + i) = MM;   
    };
  return 0;
  }
  

