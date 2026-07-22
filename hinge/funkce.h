// deklarace a definice funkci pro HINGE.exe
// vypocitava interakcni diagram pro kloub ve zdene konstrukci

#ifndef MATH
  #include <math.h>
  #define MATH
#endif

//////////////////////////////////////////////////////////////////////////////
// DEKLARACE

//napeti jako funkce pretvoreni
double sigma(   double eps,         // dana hodnota pretvoreni
                double sigma_m,     // maximalni napeti
                double eps_m,       // odpovidajici pretvoreni
                int k);             // konstanta
                
//napeti jako funkce y - uncrack
double sigma_y_uncrack(
                    double eps1,    //pretvoreni hornich vlaken
                    double eps2,    //pretvoreni dolnich vlaken
                    double eps_m,   //pretvoreni pro sigma_m
                    double sigma_m, //maximalni tlakove napeti                    
                    double d,       //vyska prurezu - d
                    double y,       //souradnice y
                    int k);         //konstanta
                    
//napeti jako funkce y - crack
double sigma_y_crack(
                    double eps1,    //pretvoreni hornich vlaken                    
                    double eps_m,   //pretvoreni pro sigma_m
                    double sigma_m, //maximalni tlakove napeti
                    double d_ef,    //ucinna vyska prurezu - d'
                    double d,       //vyska prurezu                    
                    double y,       //souradnice y
                    int k);         //konstanta

// dP_uncrack               
double dP_uncrack(  double eps1,    //pretvoreni hornich vlaken
                    double eps2,    //pretvoreni dolnich vlaken
                    double eps_m,   //pretvoreni pro sigma_m
                    double sigma_m, //maximalni tlakove napeti
                    double b,       //sirska prurezu
                    double d,       //vyska prurezu
                    int k);         //konstanta
                    
// dM_uncrack
double dM_uncrack(  double eps1,    //pretvoreni hornich vlaken
                    double eps2,    //pretvoreni dolnich vlaken
                    double eps_m,   //pretvoreni pro sigma_m
                    double sigma_m, //maximalni tlakove napeti
                    double b,       //sirska prurezu
                    double d,       //vyska prurezu
                    int k);         //konstanta
                    
// dP_crack
double dP_crack  (  double eps1,    //pretvoreni hornich vlaken               
                    double eps_m,   //pretvoreni pro sigma_m
                    double sigma_m, //maximalni tlakove napeti
                    double b,       //sirska prurezu
                    double d_ef,    //ucinna vyska prurezu - d'
                    double d,       //vyska prurezu
                    int k);         //konstanta

// dM_crack
double dM_crack  (  double eps1,    //pretvoreni hornich vlaken               
                    double eps_m,   //pretvoreni pro sigma_m
                    double sigma_m, //maximalni tlakove napeti
                    double b,       //sirska prurezu
                    double d_ef,    //ucinna vyska prurezu - d'
                    double d,       //vyska prurezu
                    int k);         //konstanta
                        


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
                        (2*(k+1) * (eps1-eps2) * pow(eps_m, k-1))
        + ( pow(eps1, k+2) - pow(eps2, k+2)) /
                        ((k+1)*(k+2) * pow(eps1-eps2, 2) * pow(eps_m, k-1))
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
       (k * (3*d-2*d_ef)/6-(d-2*d_ef/(k+2))/((k+1)*pow(eps_m,k-1)))/
       (2*(k-1)*pow(eps_m, k-1));
 return dM;
 }
  

  
                
