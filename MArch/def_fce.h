/*
Deklarovani a Definovani funkci pro program MArch.exe
*/

//////////////////////////////////////////////////////////////////////////////
//DEKLARACE

// Reseni soustavy rovnic Gaussovou eliminaci
int GaussElim(double A[], double B[], double C[], int N);
// funkce SumF - pro souctovou podminku rovnovahy ve svislem smeru
double SumF(double P[], double XP[], int n, double XLeft, double XRight);
// funkce SumM - pro momentovou podminku rovnovahy
double SumM(double P[], double XP[], int n, double XLeft, double XRight);
// funkce finder() - hleda nove kandodaty pro vznik plastickych kloubu
void finder(double e[], int n, int P[], int ID[], int m);
// funkce pro setaveni soustavy rovnic v MODE 1
void mode1A1(double A[], double X[], int Pins[], int N);
void mode1A2(double A[], double X[], int Pins[], int N, 
             double P[],double XP[],int NP);
void mode1A3(double A[], int Pins[], int N, int ID[], double  ND[]);
void mode1B(double B[], double Y[], int Pins[], int N);
// funkce pro setaveni soustavy rovnic v MODE 2
void mode2A1(double A[], double X[], int Pins[], int N);
void mode2A2(double A[], double Y[], double ND[], int Pins[], int N, int ID[]);
void mode2A3(double A[], double X[], int Pins[], int N,
             double P[], double XP[], int NP);
void mode2B(double B[], double X[], int Pins[], int N,
             double W[], double XW[], int NW);



//////////////////////////////////////////////////////////////////////////////
//DEFINICE POUZITYCH FUNKCI

int GaussElim(double A[], double B[], double C[], int N)
  {
  /*Reseni soustavy rovnic Gaussovou eliminaci
  resi soustavu [A]*{C}={B}
  vrati hodnotu 0 - pokud bylo nalezeno reseni
  vrati hodnotu 1 - pokud jsou radky linearne zavisle
  pole A[], B[], C[] muze byt dynamicke i pevne nadeklarovane
  funkce se v hlavnim programu spousti GaussElim(A,B,C,N) 
  tj. predavaji se pouze adresy prvnich clenu pole*/  
  //#define GAUSS_TEST_ELIM  //testovani vypoctu s vystupem printf()  
  //lokalni promenne
  int i, j, k;
  double POM ;  
  // Gaussova eliminace
  #ifdef TEST_GAUSS_ELIM
  printf("\n Gaussova eliminace:");
  #endif
  for (i=0; i<(N -1); i++)
    {
    #ifdef TEST_GAUSS_ELIM
    printf("\n eliminace ve sloupci %d:", i);
    #endif    
    //je treba vyzkouset, neni-li potreba vymenit radky v pripade, ze Aii = 0
    if (*(A+N*(i)+(i))==0)
      {// je nutno vymenit radky 
       //(a pro i=0 overit, neni-li cely 1. radek nulovy)
      if (i==0)
        {
        j = 0;
        for (k=i+1; k<N; k++)
          {
          if (*(A+k)!= 0) j=1;
          };
        if (j == 0)
          {// prvni radek je plny nul - radek je zavisly!
          return 1;
          };
        };
      j = 0;
      for(k=i+1; k<N;k++)
        {
        if (*(A+N*k+i)!=0) j = k;
        };
      if (j == 0) 
        {// radky jsou zavisle, ve sloupci jsou same nuly
        return 1;
        }
      else
        {// je treba vymenit radky i a j
        //vymena v matici A
        for (k=0; k<N; k++)
          {
          POM = *(A+N*i+k);
          *(A+N*i+k) = *(A+N*j+k) ;
          *(A+N*j+k) = POM ;
          };
        //vymena v matici B
        POM = *(B+i);
        *(B+i) = *(B+j) ;
        *(B+j) = POM ;
        };    
      };
    // nasleduje eliminace ve sloupci i    
    for (j=(i+1); j<N; j++)
      {
      #ifdef TEST_GAUSS_ELIM
      printf("\n   radek %d: ", j);
      #endif       
      POM = - ( *(A+N*j+i)/ *(A+N*i+i));
      for (k=i; k<N; k++)
        {
        *(A+N*j+k) = *(A+N*j+k) + POM * *(A+N*i+k);
        #ifdef TEST_GAUSS_ELIM
        printf("%f ", *(A+N*j+k));
        #endif 
        };
      *(B+j) = *(B+j) + POM * *(B+i);
      #ifdef TEST_GAUSS_ELIM
      printf("%f ", *(B+j));
      #endif 
      };
    //je treba vyzkouset, nevznikl-li radek plny nul
    j=0;
    for (k=i+1; k<N; k++)
      {
      if (*(A+N*(i+1)+ k)!=0) j=1;
      };
    if (j==0)
      {//vznikl radek nul - linearne zavisly
      return 1;
      };       
    };
  #ifdef TEST_GAUSS_ELIM
  //matice po eliminaci - kontrolni tisk
  printf("\n Soustava rovnic po eliminaci:\n ");
  for (i=0; i<N; i++)
    {
    for (j=0; j<N; j++)
      {
      printf("%f ", *(A+N*i+j));
      }
    printf("| %f\n ", *(B+i));
    };
  #endif
  // Vypocet neznamych ve vektoru {C}
  for (i=0; i<N; i++)
    {
    for (j=0; j<i; j++)
      {
      *(B+(N-1)-i) = *(B+(N-1)-i) - *(A+(N*N-1) - N*i-j) * *(C+(N-1)-j);
      };    
    *(C+(N-1)-i) = *(B+(N-1)-i) / *(A+(N*N-1) - N*i - i);
    };
  #ifdef TEST_GAUSS_ELIM
  // kontrolni tisk na obrazovku
  printf("\n Vysledny vektor neznamych cisel:\n ");
  for(i=0; i<N; i++)
    {
    printf("%f ", *(C+i));
    };
  #endif  
  return 0;
  }
  
  
// funkce SumF - pro souctovou podminku rovnovahy ve svislem smeru
/* Secte vsechny sily ve vektoru P[i] (i<n), 
   pokud pro souradnici sily XP[i] plati
   XLeft <= XP[i] < XRight
*/
double SumF(double P[], double XP[], int n, double XLeft, double XRight)
{
double SUM = 0;
int i;
for (i=0; i<n; i++)
  {
  if ( XLeft <= *(XP+i) && *(XP+i) < XRight)
    {
    SUM = SUM + *(P+i);
    };
  };
return (SUM);
}

// funkce SumM - pro momentovou podminku rovnovahy
/* Secte vsechny momenty sil P[i] (i<n), pokud pro souradnici sily XP[i] plati
   XLeft <= XP[i] < XRight
   moment se pocita jako M[i] = P[i] * (XP[i]-XLeft)
*/
double SumM(double P[], double XP[], int n, double XLeft, double XRight)
{
double SUM = 0;
int i;
for (i=0; i<n; i++)
  {
  if ( XLeft <= *(XP+i) && *(XP+i) < XRight)
    {
    SUM = SUM + *(P+i) * ( *(XP+i) - XLeft);
    };
  };
return (SUM);
}


// funkce finder() - hleda nove kandodaty pro vznik plastickych kloubu
void finder(double e[], int n, int P[], int ID[], int m)
/*Funkce pro program MArch.exe
  pro dane diference od strednice klenby e[] a poctu n prvku pole
  vypocte nove kandidaty P[m] plastickych kloubu
  a orientace oh. momentu v plast. kloubu ID[m]
  hleda hlavne lokalni extremy abs(e[i])
*/
{
  int i, j;
  double k1, k2;
  double max;
  int POM;
  int pocitadlo = 0;
  int test;
    
  for (i=0; i<n; i++) 
    {
    // vypocet k1
    if (i==0) k1 = fabs( *(e+i));      
    else k1 = fabs( *(e+i)) - fabs( *(e+i-1));
    // vypocet k2
    if (i==(n-1)) k2 = - fabs( *(e+i));      
    else k2 = fabs( *(e+i+1)) - fabs( *(e+i));
    // test extremu
    if ( k1 > 0 && k1*k2 <= 0)
      {// nasel se extrem
      if (pocitadlo <= (m-1))
        {//vektor P neni naplnen
        *(P+pocitadlo) = i;
        pocitadlo = pocitadlo + 1;
        }
      else
        {// pocitadlo je naplneno => porovnani velikosti
        // nejprve se P seradi podle velikosti fabs(*(e+ *(P+j)))        
        test = 0;
        while (test == 0) 
          {
          test = 1;
          for (j=0; j<m-1; j++)
            {
            if (fabs(*(e + *(P+j)))<fabs(*(e + *(P+1+j))))
              {
              test = 0;
              POM = *(P+j);
              *(P+j) = *(P+j+1);
              *(P+j+1) = POM;
              };
            };
          };
        // porovnani velikosti extremu s jiz registrovanymi          
        if (fabs(*(e + i)) >= fabs(*(e + *P)))
          {
          *(P+3) = *(P+2);
          *(P+2) = *(P+1);
          *(P+1) = *P;
          *P = i;
          };
        if (fabs(*(e + *P)) > fabs(*(e + i)) && 
            fabs(*(e + i))>= fabs(*(e + *(P+1))))
          {
          *(P+3) = *(P+2);
          *(P+2) = *(P+1);
          *(P+1) = i;
          };
        if (fabs(*(e + *(P+1))) > fabs(*(e + i)) && 
            fabs(*(e + i))>= fabs(*(e + *(P+2))))
          {      
          *(P+3) = *(P+2);
          *(P+2) = i;
          };
        if (fabs(*(e + *(P+2))) > fabs(*(e + i)) && 
            fabs(*(e + i))>= fabs(*(e + *(P+3))))
          {
          *(P+3) = i;
          };
        };
      };
    };
  if (pocitadlo <= (m - 1))
    {// vektor P nenyl zcela lokalnimi extremy naplnen
    // je treba doplnit dalsimi body
    while (pocitadlo <= (m - 1))
      {
      max = 0;
      for (i=0; i<n; i++)
        {
        test = 0;
        for (j=0; j<pocitadlo; j++)
          {
          if ( i == *(P+j)) test = 1;
          };
        if ( test == 0 && fabs(*(e + i)) >= max)
          {
          max = fabs(*(e + i));
          POM = i;
          };
        };
      *(P+pocitadlo) = POM ;
      pocitadlo = pocitadlo + 1;
      };
    };
  // Seradit P od nejmensiho k nejvetsimu
  test = 0;
  while (test == 0) 
    {
    test = 1;
    for (i=0; i<m-1; i++)
      {
      if (*(P+i)>*(P+i+1))
        {
        test = 0;
        POM = *(P+i);
        *(P+i) = *(P+i+1);
        *(P+i+1) = POM;
        };
      };
    }; 
  // Priradit ID
  for (i=0; i<m; i++)
    {
    if ( (fabs(*(e + *(P+i)))/ *(e + *(P+i))) == -1) 
      {
      *(ID+i) = 0;
      };
    if ( (fabs(*(e + *(P+i)))/ *(e + *(P+i))) == 1)
      {
      *(ID+i) = 1;
      };
    }; 
}

// funkce mode1A1 - pro MODE1 sestavuje A[i][0]
void mode1A1(  double A[], double X[], int Pins[], int N)
  {
  // lokalni promenne
  int i;
  // vypocet prvku A[i][0]
  for (i=0; i<N-1; i++)
    {
    *(A + (N-1)*i) = *(X + *(Pins + N-1)) -  *(X + *(Pins + i));
    };
  }
  
// funkce mode1A2 - pro MODE1 sestavuje A[i][1]
void mode1A2(double A[], double X[], int Pins[], int N, 
             double P[], double XP[],int NP)
  {  
  // lokalni promenne
  int i;  
  // vypocet prvku
  for (i=0; i<N-1; i++)
    {
    *(A + 1 + (N-1)*i) = *(A + 1 + (N-1)*i) 
                       - SumM(P,XP,NP,*(X + *(Pins + i)),*(X + *(Pins + N-1)));
    };
  }

// funkce mode1A3 - pro M0DE1 sestavuje A[i][2]
void mode1A3(  double A[], int Pins[], int N, int ID[], double  ND[])
  {
  // lokalni promenne
  int i;
  // vypocet prvku matice
  for (i=0; i<N-1; i++)
    {
    *(A + 2 + (N-1)*i) = *(ID + N-1) * *(ND + *(Pins + N-1)) 
                          - *(ID + i) * *(ND + *(Pins + i));
    };
  }
  
// funkce mode1B - pro MODE1 sestavuje B[i]
void mode1B(  double B[], double Y[], int Pins[], int N)
  {
  // lokalni promenne
  int i;
  // vypocet prvku
  for (i=0; i<N-1; i++)
    {
    *(B + i) = *(Y + *(Pins + i)) - *(Y + *(Pins + N-1));
    };
  }

// funkce mode2A1 - pro MODE2 sestavuje A[i][0]  
void mode2A1(double A[], double X[], int Pins[], int N)
  {
  mode1A1(A, X, Pins, N); // totozne s MODE1
  }

// funkce mode2A2 - pro MODE2 seestavuje A[i][1]
void mode2A2(double A[], double Y[], double ND[], int Pins[], int N, int ID[])
  {
  int i;
  for (i=0; i<N-1; i++)
    {
    *(A+1+(N-1)*i) = *(ID +N-1) * *(ND + *(Pins +N-1)) 
                    - *(ID +i) * *(ND + *(Pins +i))
                    + *(Y+ *(Pins+N-1)) - *(Y+ *(Pins+i)) ;
    };
  }
                    
// funkce mode2A3 - pro MODE 2 sestavuje A[i][2]
void mode2A3(double A[], double X[], int Pins[], int N,
             double P[], double XP[], int NP)
  {
  int i;
  for (i=0; i<N-1; i++)
    {
    *(A+2+(N-1)*i) = - SumM(P, XP, NP, *(X + *(Pins+i)), *(X + *(Pins + N-1)));
    };
  }

// funkce mode2B - pro MODE 2 sestavuje B[i]             
void mode2B(double B[], double X[], int Pins[], int N,
             double W[], double XW[], int NW)
  {
  int i;
  for (i=0; i<N-1; i++)
    {
    *(B+i) = SumM(W, XW, NW, *(X + *(Pins+i)), *(X + *(Pins + N-1)));
    };
  }  
  
