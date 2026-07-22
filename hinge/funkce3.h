// deklarace a definice funkci pro HINGE.exe
// vypocitava interakcni diagram pro kloub ve zdene konstrukci
/*
podle predpokladu:
bilinearni pracovni diagram
sig_m - max. tlakove napeti
eps_m - pretvoreni odpovidajici sig_m
lam - udava mezni pretvoreni eps_max = lam * eps_m
pracovni diagram sig = f(eps) je potom dan dvema primkami takto:    
  (i)  pro  eps <= eps_m   plati     sig = sig_m * eps / eps_m
  (ii) pro  eps > eps_m    plati     sig = sig_m
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

////////////////////////////////////////////////////////////////
// deklarace funkci

//BiLin_P_crack - vypocte normalovou silu, prurez s tazenou oblasti
double BiLin_P_crack(double sig_m, 
                      double d_ef, 
                      double lam, 
                      double b);   
                      
//BiLin_M_crack - vypocte ohybovy moment, prurez s tazenou oblasti
double BiLin_M_crack(double sig_m,   
                      double h,      
                      double d_ef,   
                      double lam,    
                      double b) ;    
                      
//BiLin_P_uncrack - vypocte normalovou silu, prurez bez tazene oblasti
double BiLin_P_uncrack(double sig_m, 
                      double eps_m,   
                      double eps1,    
                      double h, 
                      double lam, 
                      double b) ;  
                      
//BiLin_M_uncrack - vypocte ohybovy moment, prurez bez tazene oblasti
double BiLin_M_uncrack(double sig_m, 
                      double eps_m,   
                      double eps1,    
                      double h, 
                      double lam, 
                      double b) ;  

//fce3 - vypocet interakcniho diagramu
int fce3(FILE *f, 
        int N,    
        double P[], 
        double M[]);        

/////////////////////////////////////////////////////////////////
// definice funkci

//BiLin_P_crack - vypocte normalovou silu, prurez s tazenou oblasti
double BiLin_P_crack(double sig_m, //max. tlakove napeti
                      double d_ef, //efektivni vyska prurezu (tlacena vyska)
                      double lam, //koeficient lambda - udava mezni pretvoreni
                      double b)   //sirska prurezu
  {
  double P;
  P = sig_m * d_ef * b * (1. - 1. /(2. * lam));
  return P;
  }
  
//BiLin_M_crack - vypocte ohybovy moment, prurez s tazenou oblasti
double BiLin_M_crack( double sig_m,  
                      double h,     
                      double d_ef,  
                      double lam, 
                      double b)   
                      /*
                      double sig_m,  //max. tlakove napeti
                      double h,     //vyska prurezu
                      double d_ef,  //efektivni vyska prurezu (tlacena vyska)
                      double lam, //koeficient lambda - udava mezni pretvoreni
                      double b)   //sirska prurezu
                      */                      
  {
  double M ;
  M = sig_m * b * (
        1. / 2. * (d_ef - d_ef / lam) * (h - d_ef + d_ef / lam)
        + 1. / 2. * d_ef / lam * ( h / 2. - d_ef + 2. / 3. * d_ef / lam)
                      );  
  return M;
  }
  
//BiLin_P_uncrack - vypocte normalovou silu, prurez bez tazene oblasti
double BiLin_P_uncrack(double sig_m, //max. tlakove napeti
                      double eps_m,   //pretvoreni odpovidajici sig_m
                      double eps1,    //pretvoreni dolnich vlaken
                      double h, //celkova vyska prurezu
                      double lam, //koeficient lambda - udava mezni pretvoreni
                      double b)   //sirska prurezu
  {
  double P;
  P = sig_m * b *(
                 h - 1./2. * h * (eps_m - eps1)/(lam * eps_m - eps1)
                 * (1. - eps1/eps_m)
               );
  return P;
  }
                      
//BiLin_M_uncrack - vypocte ohybovy moment, prurez bez tazene oblasti
double BiLin_M_uncrack(double sig_m,   //max. tlakove napeti
                      double eps_m,    //pretvoreni odpovidajici sig_m
                      double eps1,     //pretvoreni dolnich vlaken
                      double h,        //celkova vyska prurezu
                      double lam,      //koeficient lambda - udava mezni pretvoreni
                      double b)        //sirska prurezu
  {
  double M;
  M = 1./2. * sig_m * b * ( h * (eps_m - eps1)/(lam * eps_m - eps1)) 
      * (1 - eps1 / eps_m) * 
      (h /2 - 1./3 * ( h * (eps_m - eps1)/(lam * eps_m - eps1)));
  return M;
  }


//fce3 - vypocet interakcniho diagramu
int fce3(FILE *f,       //vstupni soubor
        int N,          //pocet intervalu na interakcnim diagramu
        double P[],     //pole normalovych sil
        double M[])     //pole ohybiovych momentu
  {
  // deklarace lok. prom.
  int i;
  double b, h, sig_m, eps_m, lam, maxP;  
  //pomocne hodnoty pro iteraci
  int crack = 1;
  double DeltaP;
  double P_ [2]; 
  double d_ef[2]; 
  double eps1[2]; 
  double M_; 
   
  // cteni ze souboru
  fscanf(f, "%lf", &b);
  fscanf(f, "%lf", &h);
  fscanf(f, "%lf", &sig_m);
  fscanf(f, "%lf", &eps_m);
  fscanf(f, "%lf", &lam);  
  // urceni max hodnoty P   
  maxP = b * h * sig_m;
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
      // odhad d_ef a prvni hodnota PP
      if (i==1) d_ef[0] = 2. * DeltaP * i / sig_m / b; // jinak vysledek z predchoziho vypoctu
      P_[0] = BiLin_P_crack(sig_m, //max. tlakove napeti
                      d_ef[0], //efektivni vyska prurezu (tlacena vyska)
                      lam, b); 
      // iteracni vypocet velikosti d_ef
      while( fabs(P_[0] - DeltaP * i) > CHYBA)
        {
        d_ef[1] = d_ef[0] + KROK_D_EF;
        P_[1] = BiLin_P_crack(sig_m, //max. tlakove napeti
                      d_ef[1], //efektivni vyska prurezu (tlacena vyska)
                      lam, b); 
        d_ef[0] = d_ef[0] + 
                  (                        
                  (d_ef[1] - d_ef[0]) / (P_[1] - P_[0]) * (DeltaP * i - P_[0])
                  );
        P_[0] = BiLin_P_crack(sig_m, //max. tlakove napeti
                      d_ef[0], //efektivni vyska prurezu (tlacena vyska)
                      lam, b); //koeficient lambda - udava mezni pretvoreni
        };
      // vypocet momentu MM pro danou hodnotu d_ef      
      M_ = BiLin_M_crack(sig_m,  
                      h,     
                      d_ef[0],  
                      lam ,     
                      b) ;        
      // kontrola d_ef
      if (d_ef[0] > h) crack = -1;  //je treba opravit vypocet
      };
    if (crack != 1) //prurez bez trhliny
      {
      // odhad eps1 a prvni hodnota PP
      if (crack == -1)  //poprve pouzit vypocet bez trhliny
        {
        eps1[0] = 0;    //nastaveno jen poprve, jinak z predchoziho vypoctu
        crack = 0;
        };      
      P_[0] = BiLin_P_uncrack(sig_m, //max. tlakove napeti
                      eps_m,   //pretvoreni odpovidajici sig_m
                      eps1[0],    //pretvoreni dolnich vlaken
                      h, //celkova vyska prurezu
                      lam, b); //koeficient lambda - udava mezni pretvoreni   
      // iteracni vypocet eps1
      while( fabs(P_[0] - DeltaP * i) > CHYBA)
        {
        eps1[1] = eps1[0] + KROK_EPS_2;        
        P_[1] = BiLin_P_uncrack(sig_m, //max. tlakove napeti
                      eps_m,   //pretvoreni odpovidajici sig_m
                      eps1[1],    //pretvoreni dolnich vlaken
                      h, //celkova vyska prurezu
                      lam, b); //koeficient lambda - udava mezni pretvoreni
        eps1[0] = eps1[0] + 
                  (                        
                  (eps1[1] - eps1[0]) / (P_[1] - P_[0]) * (DeltaP * i - P_[0])
                  );
        P_[0] = BiLin_P_uncrack(sig_m, //max. tlakove napeti
                      eps_m,   //pretvoreni odpovidajici sig_m
                      eps1[0],    //pretvoreni dolnich vlaken
                      h, //celkova vyska prurezu
                      lam, b); //koeficient lambda - udava mezni pretvoreni
        };
      // vypocet momentu MM pro danou hodnotu eps2
      M_ = BiLin_M_uncrack(sig_m, //max. tlakove napeti
                      eps_m,   //pretvoreni odpovidajici sig_m
                      eps1[0],    //pretvoreni dolnich vlaken
                      h, //celkova vyska prurezu
                      lam, b); //koeficient lambda - udava mezni pretvoreni  
      };
    *(P + i) = P_[0];
    *(M + i) = M_;   
    };
  return 0;
  }

