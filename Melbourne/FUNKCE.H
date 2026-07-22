////////////////////////////////////////////////////
// deklarace a definice funkci
///////////////////////////////////////////////////
#include <math.h>
#define PI 3.1415926535
#define D_PARA 1e-4


/////////////////////////////////////////////////////
// deklarace funkci

void f_get_name(char *s_in,  char *s_txt, char *s_AB,
                char *s_sim, char *s_out, int argc, char *argv[]);
char *FileName (int FID, int CODE, int n, int argc, char *argv[]) ;
void f_read1(FILE *f_in, float *L, float *f, int *geom_CODE, float *D, float *gama, float *s_b, 
             int *N, int *NF, float **PoleF, 
             float *HFill, float *GamaFill, float *AlfaFill, 
             int *Q_CODE, float *KFill, int *d_CODE, float *d_sigma, char *s_inter);
void geom1(double L, double F, double D, int N, 
           float **intrados, float **extrados);
void geom2(double L, double F, double D, int N, 
           float **intrados, float **extrados);
void cal_dead_load(double gama, int N, float **intrados, float **extrados, 
           float **centrums, float *dead_load);
void cal_live_load(int N, float **extrados, int NF, float **PoleF, 
           float **actingpoints, float *live_load, int Q_CODE, float AlfaFill, float nivel);
void geom_polar(int N, float **intrados, float **extrados, float **ge2);
float distance (float x1, float y1, float x2, float y2);
float angle (float x1, float y1, float x2, float y2);
void cal_pq2(int N, float **intrados, float **extrados, float **centrums, 
             float *dead_load, float **p2);
void cal_AB(int N, float s_b, float **ge2, FILE *ff);
void cal_object_fce(int N, float **p2, float **fill2, FILE *fAB, FILE *ff, float s_b);
void cal_norm_con(int N, float **q2, FILE *fAB, FILE *ff, float s_b);
void cal_Nplus1_con(int N, int Com, FILE *fAB, FILE *ff, float s_b);
void read_simplex_tab(FILE *ff, float **a, int m, int n, int CODE,
                     int *m1, int *m2, int *m3);
void a_modif(float **a, int m, int n);
void simpl_icase(int icase);
void simpl_results(float **a, int m, int n, int *izrov, int *iposv, 
                   float *X, float *W);
void fprintf_matrix(float **a, int ml, int mh, int nl, int nh, FILE *ff);
void fprintf_vector(float *a, int nl, int nh, FILE *ff);
void iprintf_vector(int *a, int nl, int nh, FILE *ff);
void write_output(FILE *ff, int *icase, float W, int N, int n, 
                  float *X, float **N_e);
void write_simplex_tab(FILE *ff, const char *s_AB, int N, float s_b, 
                    float **p2, float **q2, float **fill2); 
void f_remove_files(char *s_txt, char *s_AB, char *s_sim);
void object_fce(float **a, float *aa, int n);
void cal_N_e(float **a, int *izrov, int n, float **N_e, int N, float D);
void cal_T(float **a, int *izrov, int n, int N, float *T);
void write_output_T(FILE *ff, float *T, int N); 
void cal_fill_load(float GamaFill, int N, float **extrados, float HFill, 
         float D, float f, float **fill_load);   
void write_f_to_f(FILE *f, FILE *ff);
void cal_fill2(int N, float **intrados, float **extrados, float *KFill, 
         float **fill_load, float **fill2);
void modif_d_CODE3(int N, float **ge2);
void modif2_d_CODE3(int N, float **N_e, float D);
void jump(FILE *f);
void modif_lateral_soil_pressure(int N, float *X, float *KFill, 
         float **fill2, char *s_AB, float s_b, float **ge2, float **q2);
float signum(float A);
void modif_q2(int N, float **q2, float **ge2, float *KFill);



///////////////////////////////////////////////////////
// definice funkci

void f_get_name(char *s_in,  char *s_txt, char *s_AB,
                char *s_sim, char *s_out, int argc, char *argv[])
/*
zepta se na jmeno vstupniho souboru a priradi jmena dalsich pomocnych souboru
*/ 
  {
  int i;
  char *spom, *spom2;
  spom = (char *)malloc(13);  
  spom2 = (char *)malloc(13); 
  spom = FileName(1, 1, 1, argc, argv);
  for(i=0; i<9; i++)
    {
    if ( spom[i] == '.') break;
    };
  strcpy(spom2, spom);
  strcpy(s_in, spom2);  
  strncpy(spom, spom2, i+1);
  spom[i+1] = '\0';  
  strcpy(s_txt, spom);
  strcpy(s_AB, spom);
  strcpy(s_sim, spom);
  strcpy(s_out, spom);
  strcat(s_txt, "txt");
  strcat(s_AB, "AB");
  strcat(s_sim, "sim");
  strcat(s_out, "out");    
  return;
  }


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


void f_read1(FILE *f_in, float *L, float *f, int *geom_CODE, float *D, float *gama, float *s_b, 
            int *N, int *NF, float **PoleF, 
            float *HFill, float *GamaFill, float *AlfaFill,
            int *Q_CODE, float *KFill, int *d_CODE, float *d_sigma, char *s_inter)
  {
  /*
  Precte ze souboru f_in prvni vstupni parametry
  */
  int i, c;
  jump(f_in);//prvni radek preskoci, je rezervovan na poznamky
  fscanf(f_in, "%f", L);//rozpeti
  fscanf(f_in, "%f", f);//vzepeti
  fscanf(f_in, "%d", geom_CODE); //kod geometrie (1 - kruhovy segment, 2 - parabolicky oblouk)
  fscanf(f_in, "%f", D);//tloustka klenby
  fscanf(f_in, "%f", gama);//objem. tiha klenby
  fscanf(f_in, "%f", s_b);//koeficient separace mezi bloky
  fscanf(f_in, "%d", N);//pocet bloku v klenbe
  fscanf(f_in, "%d", NF);//pocet sil vnejsiho zatizeni
  if (*NF > MAX_NF) nrerror(" Prilis mnoho vnejsich sil!");
  for( i=1; i<= *NF; i++)
    {
    fscanf(f_in, "%f", (*(PoleF + 0) + i)); // souradnice x pusobiste F
    fscanf(f_in, "%f", (*(PoleF + 1) + i)); // velikost sily F
    fscanf(f_in, "%f", (*(PoleF + 2) + i)); // sirka pusobeni sily F
    }  
  fscanf(f_in, "%f", HFill);//vyska nadnasypu nad korunou klenby
  fscanf(f_in, "%f", GamaFill);//objem tiha nadnasypu
  fscanf(f_in, "%d", Q_CODE); //zpusob roznaseni zatizeni nasypem
  fscanf(f_in, "%f", AlfaFill);//uhel roznaseni
  *AlfaFill = *AlfaFill * PI / 180.;//prevedeni na radiany
  for(i=0; i<=4; i++)
  {
      fscanf(f_in, "%f", KFill + i);//parametry zemniho tlaku
  }  
  fscanf(f_in, "%d", d_CODE);//parametry vypoctu kloubu
  fscanf(f_in, "%f", d_sigma);//normalove napeti  
  // cteni souboru s interakcnim diagramem
  i=0;
  while(i==0)
  {
      c=getc(f_in);
      if (c!=' ' && c!='\n' && c!='\t')
      {
          ungetc(c, f_in);
          i=1;
      }    
  }  
  fgets (s_inter, 12, f_in); //soubor s interakcnim diagramem
  for ( i=0; i<13; i++)
  {
      if (*(s_inter + i) == '\t') *(s_inter + i) = '\0';
      if (*(s_inter + i) == '\n') *(s_inter + i) = '\0';
      if (*(s_inter + i) == ' ') *(s_inter + i) = '\0';
  };
  *(s_inter + 12) = '\0';          
  return;
  }


void geom1(double L, double F, double D, 
           int N, float **intrados, float **extrados)
//pocita souradnice bodu na odlouku - rezy jsou normalami ke strednici
//oblouk je kruhovy segment
  {
  //lokalni promenne
  double fin, R, POMX, POMY;
  int i;
  
  //vypocet polomeru stredoveho uhlu a prirustoveko uhlu
  R = L * L / 8 / F + F / 2;
  fin = 2./N * asin(L/2/R);  
  
  //vypocet v pomocnem souradnem systemu
  for (i=0; i<=N; i++)
    {
    intrados[i][1] = R * cos (i * fin);
    intrados[i][2] = - R * sin (i * fin);
    extrados[i][1] = (R + D) * cos (i * fin);
    extrados[i][2] = - (R + D) * sin (i * fin);
    };
  
  //transformace souradnic - posun(translace)
  for (i=N; i>=0; i--)
    {
    //pocatek s.s. se posouva do bodu intrados[0][1]; intrados[0][2]
    //proto je cyklus pozpatku
    extrados[i][1] = extrados[i][1] - intrados[0][1];
    extrados[i][2] = extrados[i][2] - intrados[0][2];  
    intrados[i][1] = intrados[i][1] - intrados[0][1];
    intrados[i][2] = intrados[i][2] - intrados[0][2];  
    };
    
  //transformace souradnic - rotace(pootoceni)
  fin = (PI - N * fin) / 2 + PI;
  for (i=0; i<=N; i++)
    {
    POMX = intrados[i][1];
    POMY = intrados[i][2];
    intrados[i][1] = POMX * cos(fin) + POMY * sin(fin);
    intrados[i][2] = - POMX * sin(fin) + POMY * cos(fin);  
    POMX = extrados[i][1];
    POMY = extrados[i][2];
    extrados[i][1] = POMX * cos(fin) + POMY * sin(fin);
    extrados[i][2] = - POMX * sin(fin) + POMY * cos(fin);   
    };
  //konec funkce
  }
  
void geom2(double L, double F, double D, int N, 
           float **intrados, float **extrados)
{
    /*
    Pocita body bloku pro parabolicky oblouk
    */
    //lokalni promenne
    double a, b; //koeficienty funkce paraboly - intrados
    double dd; //delka paraboly - intrados
    double ddi, POM, X;
    int i;    
    //rovnice paraboly intrados v globalnim systemu y=a.x^2 + b.x
    a = - F * 4. / L / L;
    b = F * 4. / L;
    //delka paraboly / vzorec prevzaty z PUM od Rektoryse
    POM = pow( (L * L + 16 * F * F), 1./2.);
    dd = 1. / 2. * POM + L * L / 8. / F * log(4 * F / L + 1. / L * POM);
    
    //urceni x souradnic intrados v globalnim systemu
    POM = 0.;
    X = 0.;
    intrados[0][1] = 0.;
    for(i=1; i<=N; i++)
    {
        ddi = i * 1. / N * dd;
        while(POM < ddi)
        {
            //ji o 1 krok definovany D_PARA
            POM = POM + pow(pow(D_PARA, 2) + 
                            pow(a * (X + D_PARA) * (X + D_PARA) + b * (X + D_PARA) - a * X * X - b * X, 2),
                            1./2.);
            X = X + D_PARA;
        }    
        intrados[i][1] = X;
    }
    //urceni y souradnic v globalnim systemu
    for (i=0; i<=N; i++)
    {
      intrados[i][2] = a * intrados[i][1] * intrados[i][1] + b * intrados[i][1];
    }         
    //urceni souradnic extrados
    for (i=0; i<=N; i++)
    {
        //smernice tecny je z derivace k = 2ax + b => smerovy uhel pro normalu je
        POM = atan(2. * a * intrados[i][1] + b) + PI / 2.;
        //x souradnice 
        extrados[i][1] = intrados[i][1] + D * cos(POM);
        extrados[i][2] = intrados[i][2] + D * sin(POM);
    }    
}    
  
  
void cal_dead_load(double gama, int N, float **intrados, float **extrados, 
           float **centrums, float *dead_load)
//procedura pro vypocet souradnic tezist jednotlivych segmentu a 
//sil od vlastni tihy
  {
  //lokali promenne
  int i;
  float A, A1, A2, A3, A4;    
  for (i=1; i<=N; i++)
    {  
    //vypocet ploch
    A1 = 1./2. * (intrados[i-1][1] * intrados[i  ][2] - intrados[i  ][1] * intrados[i-1][2]);
    A2 = 1./2. * (intrados[i  ][1] * extrados[i  ][2] - extrados[i  ][1] * intrados[i  ][2]);
    A3 = 1./2. * (extrados[i  ][1] * extrados[i-1][2] - extrados[i-1][1] * extrados[i  ][2]);
    A4 = 1./2. * (extrados[i-1][1] * intrados[i-1][2] - intrados[i-1][1] * extrados[i-1][2]);
    A = A1 + A2 + A3 + A4;
    //vlastni tiha
    dead_load[i] = gama * A;
    //teziste
    centrums[i][1] = (
                     A1 * (intrados[i-1][1] + intrados[i  ][1]) / 3 +
                     A2 * (intrados[i  ][1] + extrados[i  ][1]) / 3 +
                     A3 * (extrados[i  ][1] + extrados[i-1][1]) / 3 +
                     A4 * (extrados[i-1][1] + intrados[i-1][1]) / 3 
                     )/A;
    centrums[i][2] = (
                     A1 * (intrados[i-1][2] + intrados[i  ][2]) / 3 +
                     A2 * (intrados[i  ][2] + extrados[i  ][2]) / 3 +
                     A3 * (extrados[i  ][2] + extrados[i-1][2]) / 3 +
                     A4 * (extrados[i-1][2] + intrados[i-1][2]) / 3 
                     )/A;
    };
  //konec funkce
  }

void cal_live_load(int N, float **extrados, int NF, float **PoleF, 
           float **actingpoints, float *live_load, int Q_CODE, float AlfaFill, float nivel)
{
  /*
  Vypocte pusobiste od vnejsich sil a jejich hodnoty 
  v ortogonalnich souradnicich - ze vstupnich dat
  
  Vypocte roznaseni zatizeni podle daneho kodu Q_CODE
  a urci vyslednice pusobici na jednotlive bloky
  */
  
  //lokalni parametry
  int i, j, t;
  float HBQ, TQ; //vyska nadnasypu pod silou/roznasesi sirka/ a T-parametr
  float q;       //intenzita rozneseneho zatizeni, resp. pasoveho zatizeni u Boussinuesq-a
  float **Bouss, **Bouss1; //hodnoty delta sigma podle Boussinuesq-a (na kazdem bloku urceno 5 hodnot - v 1/4) 
  float alfa, beta; //pomocne parametry pro Boussinusq-a
  float LHS, RHS; //hodnota zatizeni, ktere u Boussinesq-a nenese klenba - roznese se za klenbu
  float Xo;//pomocne hodnoty pro LHS a RHS / souradnice kam preteklo
  int  nb = 100; //pomocne hodnoty pro LHS a RHS / pocet bodu integrace 
  Bouss = matrix(1, N, 1, 5);//alokace matice Bouss
  Bouss1 = matrix(1, N, 1, 5);//od jednotkoveho zatizeni
  
  switch(Q_CODE)
  {
      
  case 0:  //bez roznaseni zatizeni a bez zohledneni sirky, na ktere vnejsi sila pusobi
  
    for (i=1; i<=N; i++)
    {
      // pro kazdy blok
      live_load [i] = 0.; //nastaveni pocatecnich hodnot
      actingpoints [i][1] = extrados [i-1][1];
      actingpoints [i][2] = extrados [i-1][2];
      for (j=1; j<=NF; j++)
      {
        // pro kazdou vnejsi silu
        if ( PoleF[0][j] >= extrados[i-1][1] && PoleF[0][j] < extrados[i][1] )
        {
            //sila pusobi na dany blok - je treba pripocitat
            actingpoints [i][1] = ( live_load [i] * actingpoints [i][1] + 
                                PoleF[1][j] * PoleF[0][j] )
                                / ( live_load [i] + PoleF[1][j] ) ;//momentova podminka
            if ( (actingpoints [i][1] - extrados [i-1][1]) == 0.) 
                  actingpoints [i][2] = extrados [i-1][2]; //nelze pouzit interpolace
            else actingpoints [i][2] = extrados [i-1][2] + 
                              ( extrados [i][2] - extrados [i-1][2])
                              * (extrados [i][1] - extrados [i-1][1])
                              / (actingpoints [i][1] - extrados [i-1][1]);//interpolace
            live_load [i] = live_load [i] + PoleF[1][j] ;//pripocteni sily
        }
      }    
    }
    break;
    
  case 1:  //roznaseni rovnomerne na vysku nadnasypu pod stredem pusobiste sily
  
    //inicializace pocatecnich hodnot
    for(i=1; i<=N; i++)
    {
        live_load [i] = 0.; //nastaveni pocatecnich hodnot
        actingpoints [i][1] = extrados [i-1][1];
        actingpoints [i][2] = extrados [i-1][2];
    }    
    for (i=1; i<=NF; i++)//pro kazdou zadanou silu je treba pocitat zvlast
    {
        //je treba nejprve provest nekolik testu
        if(PoleF[0][i] < extrados[0][1] || PoleF[0][i] >= extrados[N][1])//sila musi byt nad klenbou!!!
               nrerror(" Q_CODE = 1 => Vnejsi zatizeni musi byt nad klenbou...");
        if(PoleF[2][i] == 0. && AlfaFill == 0.)//roznaseci sirka nesmi byt nulova(deleni nulou)!!!
               nrerror(" Neuplne parametry pro roznaseni zatizeni\n Q_CODE = 1 && PoleF[2][i] = 0.0 && AlfaFill = 0.0\n");
        //je treba najit vysku nasypu, roznaseci sirku a vypocitat roznesene zatizeni q
        for(j=1; j<=N; j++)//pro kazdy blok
        {
            if(PoleF[0][i] >= extrados[j-1][1] && PoleF[0][i] < extrados[j][1])//sila je nad timto blokem
            {
                TQ = (PoleF[0][i] - extrados[j-1][1])/(extrados[j][1] - extrados[j-1][1]);//T-parametr (nasobek smeroveho vektoru daneho bodu extradosu)
                HBQ = TQ * (extrados[j][2] - extrados[j-1][2]) + extrados [j-1][2]; // souradnice y 
                HBQ = nivel - HBQ; //roznaseci vyska
                HBQ = 2 * HBQ * tan(AlfaFill) + PoleF[2][i];//roznaseci sirka
                q = PoleF[1][i] / HBQ;//rovnomerne spojite zatizeni od sily "i" - roznesene na rub klenby                
            }           
        } 
        //prirustky od sily "i" na jednotlive bloky "j"
        for(j=1; j<=N; j++)
        {
            //blok na kraji rozneseneho zatizeni vlevo
            if( (PoleF[0][i] - HBQ/2.) >= extrados[j-1][1] && (PoleF[0][i] - HBQ/2.) < extrados[j][1])
            {
                actingpoints [j][1] = ( 
                                live_load [j] * actingpoints [j][1] + 
                                q * (extrados[j][1] - (PoleF[0][i] - HBQ/2.)) * 0.5*(extrados[j][1] + (PoleF[0][i] - HBQ/2.))
                                )/( live_load [j] + q * (extrados[j][1] - (PoleF[0][i] - HBQ/2.)) ) ;//momentova podminka
                if ( (actingpoints [j][1] - extrados [j-1][1]) == 0.) 
                     actingpoints [j][2] = extrados [j-1][2]; //nelze pouzit interpolace
                else actingpoints [j][2] = extrados [j-1][2] + 
                              ( extrados [j][2] - extrados [j-1][2])
                              * (extrados [j][1] - extrados [j-1][1])
                              / (actingpoints [j][1] - extrados [j-1][1]);//interpolace
                live_load [j] = live_load [j] + q * (extrados[j][1] - (PoleF[0][i] - HBQ/2.)) ;//pripocteni sily 
            } 
            //blok uprostred rozneseneho zatizeni
            if ( (PoleF[0][i] - HBQ/2.) <= extrados[j-1][1] && (PoleF[0][i] + HBQ/2.) > extrados[j][1])
            {
                actingpoints [j][1] = ( 
                                live_load [j] * actingpoints [j][1] + 
                                q * 0.5 *(extrados[j][1] + extrados[j-1][1])* (extrados[j][1] - extrados[j-1][1])
                                )/( live_load [j] + q * (extrados[j][1] - extrados[j-1][1]) ) ;//momentova podminka
                if ( (actingpoints [j][1] - extrados [j-1][1]) == 0.) 
                     actingpoints [j][2] = extrados [j-1][2]; //nelze pouzit interpolace
                else actingpoints [j][2] = extrados [j-1][2] + 
                              ( extrados [j][2] - extrados [j-1][2])
                              * (extrados [j][1] - extrados [j-1][1])
                              / (actingpoints [j][1] - extrados [j-1][1]);//interpolace
                live_load [j] = live_load [j] + q * (extrados[j][1] - extrados[j-1][1]) ;//pripocteni sily                 
            }
            //blok na kraji rozneseneho zatizeni vpravo
            if( (PoleF[0][i] + HBQ/2.) >= extrados[j-1][1] && (PoleF[0][i] + HBQ/2.) < extrados[j][1])   
            {
                actingpoints [j][1] = ( 
                                live_load [j] * actingpoints [j][1] + 
                                q * ((PoleF[0][i] + HBQ/2.) - extrados[j-1][1]) * 0.5*((PoleF[0][i] + HBQ/2.) + extrados[j-1][1])
                                )/( live_load [j] + q * ((PoleF[0][i] + HBQ/2.) - extrados[j-1][1]) ) ;//momentova podminka
                if ( (actingpoints [j][1] - extrados [j-1][1]) == 0.) 
                     actingpoints [j][2] = extrados [j-1][2]; //nelze pouzit interpolace
                else actingpoints [j][2] = extrados [j-1][2] + 
                              ( extrados [j][2] - extrados [j-1][2])
                              * (extrados [j][1] - extrados [j-1][1])
                              / (actingpoints [j][1] - extrados [j-1][1]);//interpolace
                live_load [j] = live_load [j] + q * ((PoleF[0][i] + HBQ/2.) - extrados[j-1][1]) ;//pripocteni sily              
            }
        }                
    }    
    break;
    
  case 2: //Roznaseni zatizeni podle Boussinesq-a
    
    //nastaveni pocatecnich hodnot
    for(i=1; i<=N; i++)
    {
        live_load [i] = 0.; //nastaveni pocatecnich hodnot
        actingpoints [i][1] = extrados [i-1][1];
        actingpoints [i][2] = extrados [i-1][2];
        for(j=1; j<=5; j++)
        {
            Bouss[i][j] = 0.;
        }    
    }
    //rozpocitani jednotlivych sil do hodnot na rubu klenby
    for(i=1; i<=NF; i++)
    {
        //uvazuje se jednotkove pasove zatizeni o hodnote q = 1.
        q = 1.; LHS = 0.; RHS = 0.;
        //vypocet tlaku na jednotlive bloky
        for (j=1; j<=N; j++)
        {
            //na kazdem bloku se urcuje 5 hodnoty
            for (t=0; t<=4; t++)
            {
                //vodorovna x souradnice bodu
                TQ = t / 4. * (extrados[j][1] - extrados[j-1][1]) + extrados[j-1][1];
                //svisla y souradnice bodu
                HBQ = t / 4. * (extrados[j][2] - extrados[j-1][2]) + extrados[j-1][2];
                //vodorovna vzdalenost od pusobiste sily
                TQ = fabsf(PoleF[0][i] - TQ);
                //hloubka pod pusobistem sily
                HBQ = nivel - HBQ;
                if (HBQ == 0.) nrerror(" Boussinesq ERROR - deleni nulou...");
                //parametr beta
                beta = atanf( (TQ - 0.5 * PoleF[2][i]) / HBQ) ;
                if (beta <= AlfaFill) //musi byt v roznasecim uhlu
                {
                    //parametr alfa
                    alfa = atanf( (TQ + 0.5 * PoleF[2][i]) / HBQ) - beta;                
                    //tlak na rub klenby
                    Bouss1[j][t+1] = q / PI * (alfa + sinf(alfa) * cosf(alfa + 2 * beta));
                    //test krajnich bodu - roznasi se zatizeni za klenbu???
                    if(j==1 && t==0 && beta < AlfaFill) LHS = -1.;
                    if(j==N && t==4 && beta < AlfaFill) RHS = -1.;
                }
                else Bouss1[j][t+1] = 0.;  
            }    
        } 
        //zatizeni roznesene za klenbu vlevo a vpravo
        if (LHS != 0.)
        {
           //roznesene zatizeni je i za operou vlevo
           LHS = 0.;
           HBQ = nivel;
           //bod vlevo, kde protina uhel roznaseni zakladnu
           Xo = PoleF[0][i] - 0.5 * PoleF[2][i] - nivel * tan(AlfaFill);
           //numericka integrace ondelnikovou metodou
           for(j=0; j<=nb; j++)
           {
               TQ = Xo + j * 1. / nb * (extrados[0][1] - Xo);
               TQ = fabsf(PoleF[0][i] - TQ);
               beta = atanf( (TQ - 0.5 * PoleF[2][i]) / HBQ) ;
               alfa = atanf( (TQ + 0.5 * PoleF[2][i]) / HBQ) - beta; 
               if (j == 0 || j ==  nb) t = 1;
               else t = 2;
               LHS = LHS + t *  q / PI * (alfa + sinf(alfa) * cosf(alfa + 2 * beta));
           }
           LHS = LHS * 0.5 * (extrados[0][1] - Xo) / nb;
        }
        if (RHS != 0.)
        {
           //roznesene zatizeni je i za operou vpravo
           RHS = 0.;
           HBQ = nivel;
           //bod vpravo od opery
           Xo = PoleF[0][i] + 0.5 * PoleF[2][i] + nivel * tan(AlfaFill);
           //numericka integrace
           for(j=0; j<=nb; j++)
           {
               TQ = Xo - j/nb * (Xo - extrados[N][1]);
               TQ = fabsf(PoleF[0][i] - TQ);
               beta = atanf( (TQ - 0.5 * PoleF[2][i]) / HBQ) ;
               alfa = atanf( (TQ + 0.5 * PoleF[2][i]) / HBQ) - beta; 
               if (j == 0 || j ==  nb) t = 1;
               else t = 2;
               RHS = RHS + t *  q / PI * (alfa + sinf(alfa) * cosf(alfa + 2 * beta));
           }
           RHS = RHS * 0.5 * (Xo - extrados[N][1]) / nb;
        }
           
        
        //integrace rozneseneho zatizeni od jednotkove hodnoty q = 1.
        TQ = 0.;
        for (j=1; j<=N; j++)
        {
            //vodorovny prumet extrados
            HBQ = extrados[j][1] - extrados[j-1][1];
            //numericky vypocteny integral zatizeni na bloku "j"
            HBQ = HBQ / 4. * (0.5*Bouss1[j][1] + Bouss1[j][2] + Bouss1[j][3] + Bouss1[j][4] + 0.5*Bouss1[j][5]); 
            //pripocteno k ostatnimu zatizeni
            TQ = TQ + HBQ;
        }
        //vypocet odpovidajiciho nasobku pro skutecnou silu
        HBQ = PoleF[1][i] / (TQ + LHS + RHS);//LHS a RHS je to co preteklo doleva nebo doprava
        #ifdef BOUSSINESQ
        //kontrolni tisk
        FILE *ff;
        ff = fopen("boussin.txt", "w");
        fprintf(ff, " i=%d LHS=%f RHS=%f\n", i, LHS, RHS);
        fclose(ff);
        #endif          
        //pripocteni k ostatnim silam
        for (j=1; j<=N; j++)
        {
            for (t=1; t<=5; t++)
            {
                Bouss[j][t] = Bouss1[j][t] * HBQ;
            }
        }             
    }
    #ifdef BOUSSINESQ
    FILE *ff;
    //kontrolni tisk
    ff = fopen("boussin.txt", "a");
    fprintf_matrix(Bouss, 1, N, 1, 5, ff);
    fclose(ff);
    #endif    
    //vypocet vyslednic na bloky 
    for(i=1; i<=N; i++)
    {
        //vodorovny prumet extradosu
        HBQ = extrados[i][1] - extrados[i-1][1];
        //integrace svisle sily
        alfa = HBQ / 4. * (0.5*Bouss[i][1] + Bouss[i][2] + Bouss[i][3] + Bouss[i][4] + 0.5*Bouss[i][5]); 
        //integrace momentu k bodu [0,0]
        beta = 0.;
        for(t=0; t<=3; t++)
        {
              TQ =   (
                     ((t * HBQ / 4.) + extrados[i-1][1]) * Bouss[i][t+1] 
                     +
                     (((t+1) * HBQ /4.) + extrados[i-1][1]) * Bouss[i][t+2]
                     ) * 0.5;
              beta = beta + HBQ / 4. * TQ;
        }         
        if (alfa != 0.)
        {
           //x souradnice 
           actingpoints [i][1] = ( live_load [i] * actingpoints [i][1] + 
                                beta )
                                / ( live_load [i] + alfa ) ;//momentova podminka
           //y souradnice
           if ( (actingpoints [i][1] - extrados [i-1][1]) == 0.) 
                  actingpoints [i][2] = extrados [i-1][2]; //nelze pouzit interpolace
           else actingpoints [i][2] = extrados [i-1][2] + 
                              ( extrados [i][2] - extrados [i-1][2])
                              * (extrados [i][1] - extrados [i-1][1])
                              / (actingpoints [i][1] - extrados [i-1][1]);//interpolace
           //vysledna sila
           live_load [i] = live_load [i] + alfa ;//pripocteni sily  
        }    
    }    
    break;
    
  default: //Dasi Q_CODE jsou chybne
    nrerror(" Chybny parametr Q_CODE...");
  }  
//konec funkce roznaseni zatizeni
return;
}






void geom_polar(int N, float **intrados, float **extrados, float **ge2)
  {
  /*
  Prevede ortogonalni souradnice uzlovych bodu jednotlivych bloku
  na polarni souradnice
  matice ge2 se sklada
  ge2[i][1] - usecka a i
  ge2[i][2] - uhel alfa i
  ge2[i][3] - usecka b i
  ge2[i][4] - uhel beta i  
  */
  int i;
  for (i=0; i<=N; i++)
    {
    ge2[i][1] = 0.5 * distance(intrados[i][1], intrados[i][2], extrados[i][1], extrados[i][2]);
    ge2[i][2] = angle(intrados[i][1], intrados[i][2], extrados[i][1], extrados[i][2]);
    if (N!=i)
      {
      ge2[i][3] = distance((intrados[i][1] + extrados[i][1])/2., 
                           (intrados[i][2] + extrados[i][2])/2., 
                           (intrados[i+1][1] + extrados[i+1][1])/2., 
                           (intrados[i+1][2] + extrados[i+1][2])/2.);
      ge2[i][4] = angle((intrados[i][1] + extrados[i][1])/2., 
                           (intrados[i][2] + extrados[i][2])/2., 
                           (intrados[i+1][1] + extrados[i+1][1])/2., 
                           (intrados[i+1][2] + extrados[i+1][2])/2.);
      } 
    else 
      {
      ge2[i][3] = 1. ;
      ge2[i][4] = ge2[i][2] - PI / 2. ;
      }     
    }
  }  
  
float distance (float x1, float y1, float x2, float y2)
  {
  /*
  Vypocte vzdalenost dvou bodu
  */
  float result;
  result = sqrt( (x2-x1)*(x2-x1) + (y2-y1)*(y2-y1) );
  return result;
  }
  
float angle (float x1, float y1, float x2, float y2)
  {
  /*
  vypocte uhel v rovine od osy x
  */
  float result;
  result = atan2( (y2-y1), (x2-x1) );  
  return result;
  }
  
void cal_pq2(int N, float **intrados, float **extrados, float **centrums, 
             float *dead_load, float **p2)
  {
  /*
  Urci ekvivalentni zatizeni k bodu "0" bloku
  matice p2 ma slozky
  p2[i][1] - Px x-sova slozka sily
  p2[i][2] - Py y-sova slozka sily
  p2[i][3] - Mp moment sily k bodu "0" 
  */
  int i;
  for (i=1; i<=N; i++)
    {// pro kazdy blok    
    p2[i][1] = 0.;
    p2[i][2] = dead_load[i];
    p2[i][3] = (centrums[i][1] - 0.5 * (intrados[i-1][1] + extrados[i-1][1]))
                * dead_load[i];
    }
  //sily pro n+1 blok
  p2[N+1][1] = 0.;
  p2[N+1][2] = 0.;
  p2[N+1][3] = 0.;
  }
  
void cal_AB(int N, float s_b, float **ge2, FILE *ff)
  {
  /*
  Pocita a zapisuje transformacni matice A a B do souboru ff
  v teto verzi jen matici A - posun bloku se neuvazuje
  */
  int i, j, k;
  float X;
  //transformacni submatice Aj
  for (k=0; k<=N; k++) 
    {
    //radek 2k
    for (j=0; j<=N; j=j++) //pro matici Aj
      {      
      //1. sloupec
      X=0.;
      if ( k <= j) X = X + ge2[k][1] * sin(ge2[k][2]);
      if ( k <  j) 
        for (i=k; i<=j-1; i++) X = X + ge2[i][3] * sin(ge2[i][4]);
      fwrite(&X, sizeof(X), 1, ff);
      //2. sloupec
      X=0.;
      if ( k <= j) X = X + ge2[k][1] * cos(ge2[k][2]);
      if ( k <  j) 
        for (i=k; i<=j-1; i++) X = X + ge2[i][3] * cos(ge2[i][4]);
      fwrite(&X, sizeof(X), 1, ff);
      //3. sloupec
      if ( k <= j) X=1.;
      else X=0.;
      fwrite(&X, sizeof(X), 1, ff);
      }
    //radek 2k+1  
    for (j=0; j<=N; j=j++) //pro matici Aj
      {      
      //1. sloupec
      X=0.;
      if ( k <= j) X = X + ge2[k][1] * sin(ge2[k][2]);
      if ( k <  j) 
        for (i=k; i<=j-1; i++) X = X - ge2[i][3] * sin(ge2[i][4]);
      fwrite(&X, sizeof(X), 1, ff);
      //2. sloupec
      X=0.;
      if ( k <= j) X = X + ge2[k][1] * cos(ge2[k][2]);
      if ( k <  j) 
        for (i=k; i<=j-1; i++) X = X - ge2[i][3] * cos(ge2[i][4]);
      fwrite(&X, sizeof(X), 1, ff);
      //3. sloupec
      if ( k <= j) X = -1.;
      else X = 0.;
      fwrite(&X, sizeof(X), 1, ff);
      }
    }
  //  POSUN SE NEUVAZUJE  pro s_b <= 0
  if (s_b > 0.)
    {
    for (k=0; k<=N; k++) //transformacni submatice Bj
      {
      //radek 2k
      for (j=0; j<=N; j=j++) //pro matici Bj
        {      
        //1. sloupec      
        if ( k <= j) X = cos(ge2[k][2]) + s_b * sin(ge2[k][2]);   
        else X=0.;   
        fwrite(&X, sizeof(X), 1, ff);
        //2. sloupec
        if ( k <= j) X =  -sin(ge2[k][2]) + s_b * cos(ge2[k][2]);   
        else X=0.;   
        fwrite(&X, sizeof(X), 1, ff);
        //3. sloupec
        X = 0.;
        fwrite(&X, sizeof(X), 1, ff);
        }
      //radek 2k+1  
      for (j=0; j<=N; j=j++) //pro matici Bj
        {
        //1. sloupec      
        if ( k <= j) X = - cos(ge2[k][2]) + s_b * sin(ge2[k][2]);   
        else X=0.;   
        fwrite(&X, sizeof(X), 1, ff);
        //2. sloupec
        if ( k <= j) X = + sin(ge2[k][2]) + s_b * cos(ge2[k][2]);   
        else X=0.;   
        fwrite(&X, sizeof(X), 1, ff);
        //3. sloupec
        X = 0.;
        fwrite(&X, sizeof(X), 1, ff);
        }
      } 
    } 
  }
  
  
void cal_object_fce(int N, float **p2, float **fill2, FILE *fAB, FILE *ff, float s_b)
  {
  /*
  Pocita cilovou funkci pro simplexovou metodu
  */
  int i, j;
  float AB, Ai;
  // pootoceni fi-int a fi-ext
  for (i=1; i<=2*N+2; i++)
    {
    Ai = 0.;
    for (j=1; j<=N+1; j++)
      {
      //posun x
      fread(&AB, sizeof(AB), 1, fAB);
      Ai = Ai + AB * (p2[j][1] + fill2[j][1]);
      //posun y
      fread(&AB, sizeof(AB), 1, fAB);
      Ai = Ai + AB * (p2[j][2] + fill2[j][2]);
      //pootoceni FI
      fread(&AB, sizeof(AB), 1, fAB);
      Ai = Ai + AB * (p2[j][3] + fill2[j][3]);
      } 
    Ai = -Ai;    
    fwrite(&Ai, sizeof(Ai), 1, ff);
    }
  // POSUN SE NEUVAZUJE pro s_b<=0 
  if (s_b > 0.)
    {
    // posun y+ a y-
    for (i=1; i<=2*N+2; i++)
      {
      Ai = 0.;
      for (j=1; j<=N+1; j++)
        {
        //posun x
        fread(&AB, sizeof(AB), 1, fAB);
        Ai = Ai + AB * (p2[j][1] + fill2[j][1]);
        //posun y
        fread(&AB, sizeof(AB), 1, fAB);
        Ai = Ai + AB * (p2[j][2] + fill2[j][2]);
        //pootoceni FI
        fread(&AB, sizeof(AB), 1, fAB);
        Ai = Ai + AB * (p2[j][3] + fill2[j][3]);
        } 
      Ai = -Ai;      
      fwrite(&Ai, sizeof(Ai), 1, ff);   
      }
    }
  }
  
void cal_norm_con(int N, float **q2, FILE *fAB, FILE *ff, float s_b)
  {
  /*
  Posita podminku normy
  */
  int i, j;
  float AB, Ai;   
  //jednotlive koeficienty
  // pootoceni fi-int a fi-ext
  for (i=1; i<=2*N+2; i++)
    {
    Ai = 0.;
    for (j=1; j<=N+1; j++)
      {
      //posun x
      fread(&AB, sizeof(AB), 1, fAB);
      Ai = Ai + AB * q2[j][1];
      //posun y
      fread(&AB, sizeof(AB), 1, fAB);
      Ai = Ai + AB * q2[j][2];
      //pootoceni FI
      fread(&AB, sizeof(AB), 1, fAB);
      Ai = Ai + AB * q2[j][3];
      }
    fwrite(&Ai, sizeof(Ai), 1, ff);      
    }
  // POSUN SE NEUVAZUJE  pro s_b <= 0
  if (s_b > 0.)
    {
    // posun y+ a y-
    for (i=1; i<=2*N+2; i++)
      {
      Ai = 0.;
      for (j=1; j<=N+1; j++)
        {
        //posun x
        fread(&AB, sizeof(AB), 1, fAB);
        Ai = Ai + AB * q2[j][1];
        //posun y
        fread(&AB, sizeof(AB), 1, fAB);
        Ai = Ai + AB * q2[j][2];
        //pootoceni FI
        fread(&AB, sizeof(AB), 1, fAB);
        Ai = Ai + AB * q2[j][3];
        }
      fwrite(&Ai, sizeof(Ai), 1, ff);     
      }
    }
  //ma byt rovno 1 - je treba pridat "1" a kod pro rovnost "3"
  Ai = 1.;
  fwrite(&Ai, sizeof(Ai), 1, ff);
  i = 3;
  fwrite(&i, sizeof(i), 1, ff); 
  }
  
void cal_Nplus1_con(int N, int Com, FILE *fAB, FILE *ff, float s_b)
  {
  /*
  Pocita podminky posunu bloku N+1
  Com - je slozka 1 pro posun x, 2 pro posun y, a 3 pro natoceni
  */
  int i, j, radek, last_radek;
  float Ai;
  if (s_b <= 0.) last_radek = 2*(N+1);
  else last_radek = 4*(N+1);
  for (radek=1; radek <= last_radek; radek++)
    {
    for (i=1; i<=N+1; i++)
      {
      for (j=1; j<=3; j++)
        {
        fread(&Ai, sizeof(Ai), 1, fAB);
        if (i == N+1 && j == Com) fwrite(&Ai, sizeof(Ai), 1, ff);
        }
      }
    }
  //ma byt rovno 0 - je treba pridat "0" a kod pro rovnost "3"
  Ai = 0.;
  fwrite(&Ai, sizeof(Ai), 1, ff);
  i = 3;
  fwrite(&i, sizeof(i), 1, ff); 
  }
   
  
  
void read_simplex_tab(FILE *ff, float **a, int m, int n, int CODE,
                     int *m1, int *m2, int *m3)
{
  /*
  Cte simplexovou tabulku ze souboru *.sim do matice a[1;m+2][1;n+1]
  Je treba, aby simplexova matice v souboru byla tvaru:
  vstup je v binarnim souboru!!!    
  
  a01 a02 ... a0N 
  a11 a12 ... a1N b1 XID1
  ...
  aM1 aM2 ... aMN bM XID2
  
   
  A0i - koeficiemty u cilove funkce
  Aji (j=1..M, i=1..N) - koeficienty v podminkach
  bj - prave strany podminek
  XIDj = 1 pro podminky typu aj1*X1 + aj2*X2 + ... ajN*XN <= bj
  XIDj = 2 pro podminky typu aj1*X1 + aj2*X2 + ... ajN*XN >= bj
  XIDj = 3 pro podminky typu aj1*X1 + aj2*X2 + ... ajN*XN = bj    
  */
  //lokalni promenne
  int i, j;
  int *XID;
  int count = 1;
  //alokace vektoru XID
  XID = ivector(2, m+2);
  //cteni cilove funkce
  a[1][1] = 0. ; //vyhrazeno pro hodnotu funkce  
  for(j=2; j<=n+1; j++)  //koeficienty v cilove funkci
  {
      fread(*(a+1)+j, sizeof(float), 1, ff);
      a[1][j] = a[1][j] * CODE;
  }
  //cteni omezujicich podminek  
  for (i=2; i<=m+1; i++)//podminka i-1
  {
      for(j=2; j<=n+1; j++)//koeficienty podminky
      {
          fread(*(a+i)+j, sizeof(float), 1, ff); 
          a[i][j] = - a[i][j]; //prevod na druhou stranu rovnice
      } ;
      fread(*(a+i)+1, sizeof(float), 1, ff);//hodnota prave strany
      fread(XID + i, sizeof(int), 1, ff);//znamenko rovnosti/nerovnostid
  }    
  
  //prave strany musi byt kladne - jinak je potrena je upravit
  for (i=2; i<= m+1; i++)
    {
    if ( a[i][1] < 0.)
      {
      // prenasoneni clenu -1
      for(j=1; j<= n+1; j++)
        {
        a[i][j] = - a[i][j];
        };
      // uprava XID - je treba otocit znamenko nerovnosti po prenasobeni -1
      if (XID[i] == 1) XID[i] = 2;
      if (XID[i] == 2) XID[i] = 1;
      }
    }; 
    
  //urceni poctu m1, m2, m3
  *m1=0; *m2=0; *m3=0;
  for (i=2; i<=m+1; i++)
  {
    if (XID[i] == 1) *m1=*m1 + 1;
    if (XID[i] == 2) *m2=*m2 + 1;
    if (XID[i] == 3) *m3=*m3 + 1;
  }
  
  //seradeni podminek v poradi XID=1, XID=2, XID=3
  while (count == 0)
  {
      count = 0;
      for (i=2; i<=m; i++)
      {
          if(XID[i]>XID[i+1])
          {
              count++;//registruj vymenu
              //vymena XID
              XID[m+2] = XID[i];
              XID[i] = XID [i+1];
              XID[i+1] = XID [m+2];
              //vymena radku matice a
              for (j=1; j<=n+1; j++)
              {
                  a[m+2][j]=a[i][j];
                  a[i][j]=a[i+1][j];
                  a[i+1][j]=a[m+2][j];
              }
          }
      }
  }
  
  //nulovani posleniho radku
  for(j=1;j<=n+1; j++)
  {
      a[m+2][j] = 0.;
  };  
    
  free_ivector(XID, 2, m+2);
  return;
}                  
                   

  
void a_modif(float **a, int m, int n)
  {
  int i;
  /*
  Algoritmus simplex. metody je napsan pro maximalizaci, proto se simpl.tabulka
  prevadi z minimalizace na maximalizace 
  a nyni zpet z maximalizace na minimalizaci
  
  ...puvodne jsem myslel, ze je nutno prevadet daleko sloziteji,
     ale nakonec je to velmi primitivni funkce
  
  */
  for (i=1;i<=n+1;i++)
  {
      a[1][i] = - a[1][i];
  }    
  return;
  }
  
  
  
void simpl_icase(int icase)
  {
  //kontrola vypoctu simplexovou metodou - existence reseni
  if (icase == -1) nrerror(" Nelze splnit stanovene deformacni podminky.");
  if (icase == +1) nrerror(" Cilova funkce neni na danem polyedru omezena.");
  return;
  }

void simpl_results(float **a, int m, int n, int *izrov, int *iposv, 
                   float *X, float *W)
  {
  int i,j;
  /*
  Urceni vysledku ze siplexove tabulky
  */  
  *W = a[1][1];
  //vektor promennych X
  for(i=1; i<=m; i++)
    {
    if (iposv[i]<=n) X[iposv[i]] = a[i+1][1];    //nenulove hodnoty
    };
  for(i=1; i<=n; i++)
    {
    if (izrov[i]<=n) X[izrov[i]] = 0.;    //nulove hodnoty
    };    
  return;
  }
  
void fprintf_matrix(float **a, int ml, int mh, int nl, int nh, FILE *ff)
  {
  // tisk submatice float **a[ml..mh][nl..nh] do souboru FILE *ff
  
  //lokalni promenne
  int i, j;
  //tisk
  for (i=ml; i<=mh; i++)
    {
    for (j=nl; j<=nh; j++)
      {
      fprintf(ff, "%f\t", a[i][j]);
      }
    //odradkovani na konci radku matice
    fprintf(ff, "\n");
    }      
  return;
  }

void fprintf_vector(float *a, int nl, int nh, FILE *ff)
  {
  // tisk vektoru float *a[nl..nh] do souboru FILE *ff
  
  //lokalni promenne
  int i;
  //tisk
  for (i=nl; i<=nh; i++)
    {    
    fprintf(ff, "%f\t", a[i]);
    } 
  //odradkovani na konci radku 
  fprintf(ff, "\n");    
  return;
  } 
 
void iprintf_vector(int *a, int nl, int nh, FILE *ff)
  {
  // tisk vektoru int *a[nl..nh] do souboru FILE *ff
  
  //lokalni promenne
  int i;
  //tisk
  for (i=nl; i<=nh; i++)
    {    
    fprintf(ff, "%d\t", a[i]);
    } 
  //odradkovani na konci radku 
  fprintf(ff, "\n");    
  return;
  } 
  
void write_output(FILE *ff, int *icase, float W, int N, int n, 
                  float *X, float **N_e)
  {
  /*
  Vypise vysledky do souboru ff
  *icase - kod urcujici uspesnost simplexove metody
  W - lambda - load factor
  N - pocet bloku
  n - pocet neznamych - lokalni deformace
  *X - vektor lokalnich neznamych  
  */
  // lokalni promenne
  int i;
  //zacatek zapisu vysledku do souboru
  fprintf (ff, " icase = %d\n", *icase); 
  fprintf (ff, "         0 -> O.K.,\n");
  fprintf (ff, "        -1 -> nelze splnit omezujici podminky,\n"); 
  fprintf (ff, "        +1 -> cilova funkce je na polyedru neomezena.\n");
  fprintf (ff, " lambda = %f\n", W );
  fprintf (ff, " pocet bloku N = %d\n", N );
  fprintf (ff, " Vektor lokalnich deformaci:\n");
  for (i=1; i<=n; i=i+2)
    {
    if (i < 2*N+2)
      {
      if (X[i] != 0)
      fprintf( ff, " %3d: fi %02d int = %f\n", i, i/2, X[i]);
      if (X[i+1] != 0)
      fprintf( ff, " %3d: fi %02d ext = %f\n", i+1, i/2, X[i+1]);
      }
    else
      {
      if (X[i] != 0)
      fprintf( ff, " %3d:  y %02d (+) = %f\n", i, (i-2*N-2)/2, X[i]);
      if (X[i+1] != 0)
      fprintf( ff, " %3d:  y %02d (-) = %f\n", i+1, (i-2*N-2)/2, X[i+1]);
      }
    }; 
  fprintf (ff, " Vektor indexu spary mezi bloky:\n"); 
  for (i=0; i<=N; i++)
  {
      fprintf(ff, "%d\t\t", i);
      if(i==N) fprintf(ff, "\n");
  }    
  fprintf (ff, " Vektor normalovych sil ve sparach (+ znaci tlak):\n");
  fprintf_matrix(N_e, 1, 1, 0, N, ff);
  fprintf (ff, " Vektor vzdalenosti N od hornoho povrchu klenby:\n");
  fprintf_matrix(N_e, 2, 2, 0, N, ff);  
  //konec zapisu vysledku do souboru
  return;
  }
  
  
void write_simplex_tab(FILE *ff, const char *s_AB, int N, float s_b, 
                    float **p2, float **q2, float **fill2)
  {
  /*
  sestavi zadani pro simplexovou metodu do souboru ff
  jeho fomat je nasledujici>\:
  ZAPISUJE SE BINARNE!!!    
  
  N
  M
  CODE
  a01 a02 ... a0N 
  a11 a12 ... a1N b1 XID1
  ...
  aM1 aM2 ... aMN bM XID2
  
  kde CODE=1 pro maximalizaci a CODE = -1 pro minimalizaci
  N je pocet promennych Xi (Xi>=0)
  M je pocet podminek (rovnic a nerovnic)
  A0i - koeficiemty u cilove funkce
  Aji (j=1..M, i=1..N) - koeficienty v podminkach
  bj - prave strany podminek
  XIDj = 1 pro podminky typu aj1*X1 + aj2*X2 + ... ajN*XN <= bj
  XIDj = 2 pro podminky typu aj1*X1 + aj2*X2 + ... ajN*XN >= bj
  XIDj = 3 pro podminky typu aj1*X1 + aj2*X2 + ... ajN*XN = bj
  */ 
   
  //lokalni promenne
  FILE *fAB;
  int number;
  //zapis tabulky
  //pocet "lokalnich" promennych - neuvazuje se sliding
  if (s_b <= 0) number = 2*(N+1); 
  //pocet "lokalnich" promennych - uvazuje se sliding
  else number = 4*(N+1); 
  fwrite(&number, sizeof(number), 1, ff);
  // pocet podminek (podm. normy + 3 deformacni podm.
  number = 4;
  fwrite(&number, sizeof(number), 1, ff); 
  //CODE
  number = -1;  //je treba minimalizovat funkci
  fwrite(&number, sizeof(number), 1, ff); 
  //1. cilova funkce
  fAB = fopen(s_AB, "rb");
  cal_object_fce(N, p2, fill2, fAB, ff, s_b); 
  fclose(fAB);
  //2. podminka normy
  fAB = fopen(s_AB, "rb");
  cal_norm_con(N, q2, fAB, ff, s_b); 
  fclose(fAB);
  //3. podminky posunu
  fAB = fopen(s_AB, "rb");
  cal_Nplus1_con(N, 1, fAB, ff, s_b);
  fclose(fAB);
  fAB = fopen(s_AB, "rb");
  cal_Nplus1_con(N, 2, fAB, ff, s_b);
  fclose(fAB);
  fAB = fopen(s_AB, "rb");
  cal_Nplus1_con(N, 3, fAB, ff, s_b);
  fclose(fAB);
  return;
}  


void f_remove_files(char *s_txt, char *s_AB, char *s_sim)
{
    /*
    Vymaze vsechny pracovni binarni soubory i kontrolni textove soubry
    */
    
    remove(s_txt);
    remove(s_AB);
    remove(s_sim);
    
    return;
}    


void object_fce(float **a, float *aa, int n)
{
    /*
    Zalohuje z matice float **a prvni radek, coz jsou argumenty cilove funkce
    */    
    
    //lokalni promenne
    int i;    
    //zalohovani
    for (i=1; i<=n+1; i++)
    {
        aa[i] = a[1][i];
    }    
    //konec funkce   
    return;
} 

void cal_N_e(float **a, int *izrov, int n, float **N_e, int N, float D)
{
    /*
    z finalni simplexove tabulky a tloustky klenby vypocte normalove sily
    a jejich excentricity
    
    parametry:
    float **a[1..m+2][1..n+1] - finalni simplexova tabulka
    float **N_e[1..2][0..N] - matice s normal. silami a excentricitami
    int **izrov[1..n] - vektor urcujici indexi nulovych promennych
    int n - pocet promennych v simplexove cilove funkci
    int N - pocet bloku
    double D - tlouska klenby
    */   
    //lokalni parametry
    int k; //cislo spary od 0 do N
    int i, j; // sloupce, kde je umisten M-int a M-ext
    int ii; //pomocna promenna
    float Mint, Mext;  //momenty k bodu int a ext
    //vypocet
    for (k=0; k<=N; k++)
    {
        //je treba najit sloupec pro M_k_int
        i=0; j=0;
        for (ii=1; ii<=n; ii++)
        {
            if( (2*k+1) == izrov[ii] ) i=ii;
            if( (2*k+2) == izrov[ii] ) j=ii;
        }   
        //hodnoty momentu 
        if (i!=0) Mint = a[1][i+1];
        else Mint = 0.;
        if (j!=0) Mext = a[1][j+1];
        else Mext = 0.;
        
        //vypocet N a e
        N_e[1][k] = (Mext + Mint) / D;
        N_e[2][k] = Mext * D / ( Mext + Mint );
        
    }
    return; 
} 

void cal_T(float **a, int *izrov, int n, int N, float *T)
{
    /*
    Pocita ze simplexove tabulky smykove sily ve sparach.
    Zle spocitat jen v pripade, ze se uvazuje smyk ve sparach
    
    Parametry:
    float **a[1..m+2][1..n+1] - finalni simplexova tabulka
    float *T[0..N] - vektor s posouvajicimi silami ve sparach
    int *izrov[1..n] - vektor urcujici indexi nulovych promennych
    int n - pocet promennych v simplexove cilove funkci
    int N - pocet bloku
    */   
    
    //lokalni promenne
    int k; //cislo spary od 0 do N
    int i, j; // sloupce, kde je umistena sila Uplus a Uminis
    int ii; //pomocna promenna
    float Uplus, Uminus;  //sily potrebne k vyvolani jednotkoveho posunu u+ a u- ze simplex. tab. 
    //vypocet 
    //vypocet
    for (k=0; k<=N; k++)
    {
        //je treba najit sloupec pro Uplus a Uminus
        i=0; j=0;
        for (ii=1; ii<=n; ii++)
        {
            if( (2*k+1 + 2*N+2) == izrov[ii] ) i=ii;
            if( (2*k+2 + 2*N+2) == izrov[ii] ) j=ii;
        }   
        //hodnoty sil od jednotkoveho posunu 
        if (i!=0) Uplus = a[1][i+1];
        else Uplus = 0.;
        if (j!=0) Uminus = a[1][j+1];
        else Uminus = 0.;
        //vypocet 
        T[k] = (Uplus - Uminus) / 2.;   
    }        
    //konec funkce
    return;
}  

void write_output_T(FILE *ff, float *T, int N)
{
    /*
    Vypisedo vystupniho souboru vektor posouvajicich sil
    */
    fprintf (ff, " Vektor posouvajicich sil ve sparach:\n");
    fprintf_vector(T, 0, N, ff); 
    //konec
    return;
}  


void cal_fill_load(float GamaFill, int N, float **extrados, float HFill, 
         float D, float f, float **fill_load)
{
    /*
    Vypocte zatizeni z nadnasypu do matice fill_load[1..N][1..4],
    kde i=1..N je blok klenby
    a druhy j index znaci 1 - svisla slozka zatizeni
                          2 - vodorovny prumet extrados bloku i
                          3 - souradnice x pusobiste
                          4 - souradnice y pusobiste
                        
    GamaFill - objemova tiha nadnasypu
    N - pocet bloku klenby
    extrados - souradnice extrados
    HFill - vyska nadnasypu nad korunou klenby
    D - tloustka klenby
    f - vzepeti klenby (intrados)
    */         
    
    //lokalni promenne
    int i;
    float nivel; //y souradnice nivelety
    float A, A1, A2, A3, A4; //pomocne plochy
    //vypocet
    nivel = f + D + HFill;
    //pocatek cyklu
    for (i=1; i<=N; i++)
    {
        //vypocet plochy lichobezniku
        A1 = 1./2. * (extrados[i-1][1] * extrados[i  ][2] - extrados[i  ][1] * extrados[i-1][2]);
        A2 = 1./2. * (extrados[i  ][1] * nivel            - extrados[i  ][1] * extrados[i  ][2]);
        A3 = 1./2. * (extrados[i  ][1] * nivel            - extrados[i-1][1] * nivel           );
        A4 = 1./2. * (extrados[i-1][1] * extrados[i-1][2] - extrados[i-1][1] * nivel           );
        A = A1 + A2 + A3 + A4;
        //vlastni tiha nadnasypu
        fill_load[i][1] = GamaFill * A;
        //svisly prumet extrados bloku i (+ roste, - klesa)
        fill_load[i][2] = - extrados[i-1][2] + extrados[i][2];
        //X souradnice teziste, tj. vodorovna souradnice na rubu klenby
        fill_load[i][3] = (
             A1 * (extrados[i-1][1] + extrados[i  ][1]) / 3 +
             A2 * (extrados[i  ][1] + extrados[i  ][1]) / 3 +        
             A3 * (extrados[i  ][1] + extrados[i-1][1]) / 3 +
             A4 * (extrados[i-1][1] + extrados[i-1][1]) / 3 
             )/A;
        //fill_load[i][3] = 0.5 * (extrados[i-1][1] + extrados[i][1]);//kontrola - takto by mel pocitat RING.exe
        //svisla souradnice pusobiste na rubu klenby
        A = (extrados[i-1][1] - fill_load[i][3]) / 
            (extrados[i-1][1] - extrados [i][1]); //pomocna konstanta
        fill_load[i][4] = extrados[i-1][2] -
            A * (extrados[i-1][2] - extrados[i][2]);
    }
    //konec funkce
    return;
}        
        
        
void write_f_to_f(FILE *f, FILE *ff)
{
    /*
    Prekopiruje obsah txt souboru f do txt souboru ff
    
    Pouzije se pro prekopirovani parametru ve vstupnim souboru
    */   
    //lokalni promenne
    int c;
    // pokud nenajde konec souboru, kopiruje vsechny znaky
    while ( (c=getc(f)) != EOF)
    {
        putc(c, ff);
    }
    putc('\n', ff);        
    //konec fce
    return;
} 

void cal_fill2(int N, float **intrados, float **extrados, float *KFill, 
         float **fill_load, float **fill2)
{
    /*
    Vypocitava zatizeni z nadnasypu a transformuje ho k bodu "0" daneho bloku
    Parametry:
    int N - pocet bloku
    float **intrados, float **extrados - souradnice intrados a extrados
    float *KFill[0..5] - soucinitele zemniho tlaku a K_code
    float **fill_load[1..N][1..4] - svisle zatizeni nadnasypu, svisly prumet extrados a souradnice pusobiste sily
    float **fill2 - transformovane zatizeni
    */  
    
    //lokalni promenne
    int i; 
    //zacatek cyklu
    for (i=1; i<=N; i++)
    {// pro kazdy blok  
        //vodorovna slozka  X
        if (KFill[0] == 0.) fill2[i][1] = 0.;//bez uvazovani vodorovneho zem. tlaku
        else fill2[i][1] = fill_load[i][1] * fill_load[i][2] * KFill[1];//s uvazovanim zem. tlaku (na zacatku se uvazuje jen v kliku)
        //svisla slozka Y
        fill2[i][2] = fill_load[i][1];
        //momentova slozka M - od svisle i vodorovne sily
        fill2[i][3] =  fill2[i][2] *
              (fill_load[i][3] - 0.5 * (intrados[i-1][1] + extrados[i-1][1]))
              +
              fill2[i][1] *
              (fill_load[i][4] - 0.5 * (intrados[i-1][2] + extrados[i-1][2]));
    }
    //sily pro n+1 blok
    fill2[N+1][1] = 0.;
    fill2[N+1][2] = 0.;
    fill2[N+1][3] = 0.;
         
    //konec funkce
    return;
}


void modif_d_CODE3(int N, float **ge2)
{
    /*
    Modifikace geometrie oblouku v polarnich souradnicich tak, aby tlakova cara
    probihala jen jadrem prurezu
    
    Legenda:
        N - pocet bloku
        ge2[0..N][1..4] - geometrie bloku v polarnich souradnicich
    */
    //lokalni promenne
    int i;
    //modifikace
    for (i=0; i<=N; i++)
    {
        ge2[i][1] = ge2[i][1] / 3.;
    }
    return;
}

void modif2_d_CODE3(int N, float **N_e, float D)
{
    /*
    Prepocet pusobiste normalove sily v pripade, ze je pouzit d_CODE = 3
    a tlakova cara prochazi jen jadrem prurezu
    Legenda:
        N - pocet bloku
        N_e [0..N][1..2] - matice s normalovymi silami N a pusobistemi e
        D - tloustka klenby
    */
    //lokalni promenne
    int i;
    //modifikace
    for (i=0; i<=N; i++)
    {
        N_e[2][i] = N_e[2][i] + D / 3.;
    }
    return;
}    

void jump(FILE *f)
{
//jump - preskoci vse do konce radky nebo konce souboru
  int KONEC = -1;
  int c; 
  while (KONEC == -1)
    // vrati 1 (nasel se konec radky) nebo 0 (nasel se konec souboru)
    {
    if ( (c=getc(f)) == EOF) KONEC = 0;
    if (c == '\n') KONEC = 1; 
    };
  if (KONEC == 0) nrerror( " Funkce jump nenasla konec radky!"); 
  return;
}  

#define EPSILON 1E-3
void modif_lateral_soil_pressure(int N, float *X, float *KFill, float **fill2,
                                 char *s_AB, float s_b, float **ge2, float **q2)
{
     /*
     Modifikace zemniho tlaku pro vypocteny tvar deformace podle prviho kroku
     
     Legenda:
     N - pocet bloku
     X - vektor tvaru deformaci
     Kfill - soucinitele zemniho tlaku
     fill2 - zatizeni z nadnasypu
     */
     
     //lokalni promenne
     int i, j, k; 
     long jump;
     FILE *f;
     float **d; 
     float **u_ex;
     float max_u_ex;
     float POM;
     float n, yF;
     
     //otevreni souboru s transformacnimi maticemi
     f = fopen(s_AB, "rb");
     
     //alokace poli
     d = matrix(1, N, 1, 3);
     u_ex = matrix(1, N, 1, 3);
     
     //urceni velikosti skoku
     jump = sizeof(float)*((N+1) * 3 - 1);
     
     //vypopcet globalnich deformaci
     for (i=0; i<N; i++) //index bloku
     {
         for(j=0; j<3; j++)  //index souradnice x, y nebo fi
         {
            //nastavit nulu
            d[i+1][j+1] = 0;
            //prvni cteny znak
            fseek(f, sizeof(float)*(i*3 + j), SEEK_SET);
            for (k=1; k<=(N+1)*2; k++)
            {
                fread(&POM, sizeof(POM), 1, f);
                d[i+1][j+1] = d[i+1][j+1]+ POM * X[k];
                fseek(f, jump, SEEK_CUR);
            }
            if (s_b > 0.) //pri zahrnuti usmyknuti ve spare
            {
                for(k=(N+1)*2+1; k<=(N+1)*4; k++)
                {
                  fread(&POM, sizeof(POM), 1, f);
                  d[i+1][j+1] = d[i+1][j+1]+ POM * X[k];
                  fseek(f, jump, SEEK_CUR);
                }  
            }      
         }
     } 
     fclose(f);
          
     //urceni vodorovnych posunu bodu extrados
     for(i=1; i<=N; i++)
     {
         u_ex[i][1] = d[i][1]*EPSILON + 
                      ge2[i-1][1] * cos(ge2[i-1][2] - d[i][3]*EPSILON) -
                      ge2[i-1][1] * cos(ge2[i-1][2]);
         u_ex[i][2] = d[i][1]*EPSILON + 
                      ge2[i-1][3] * cos(ge2[i-1][4] - d[i][3]*EPSILON) -
                      ge2[i-1][3] * cos(ge2[i-1][4])+
                      ge2[i][1] * cos(ge2[i][2] - d[i][3]*EPSILON) -
                      ge2[i][1] * cos(ge2[i][2]);
         u_ex[i][3] = 0.5 * (u_ex[i][1] + u_ex[i][2]) 
                      * signum( -sin(ge2[i-1][4]) );
                      //zaporne znamenko - aktivni tlak; kladne - pasivni tlak
     }
                           
     //urceni maximalniho posunu smeren do nasypu - tam pusobi plny aktivni tlak
     max_u_ex = 0.;
     for(i=1; i<=N; i++)
     {
         if (max_u_ex < u_ex[i][1]* signum( -sin(ge2[i-1][4]) )) 
                  max_u_ex = u_ex[i][1]* signum( -sin(ge2[i-1][4]) );
         if (max_u_ex < u_ex[i][2]* signum( -sin(ge2[i-1][4]) )) 
                  max_u_ex = u_ex[i][2]* signum( -sin(ge2[i-1][4]) );
     }
     
     //prepocet bocniho zemniho tlaku                            
     for (i=1; i<=N; i++)
     {   
         //je potreba upravit vodorovnou silu i ohybovy moment !!!!!
         
         //A] bocni tlak od nasypu
         //urceni psobiste sily jako nasobek n
         n = (fill2[i][3] - ge2[i-1][1]*
             (fill2[i][2]*cos(ge2[i-1][2])+fill2[i][1]*sin(ge2[i-1][2]))
             )/(
             ge2[i-1][3]*
             (fill2[i][2]*cos(ge2[i-1][4])+fill2[i][1]*sin(ge2[i-1][4]))
             );
         //svisla osuradnice vosorovne sily
         //k bodu "0" bloku je yF=a*sin(alfa) + n*b*sin(beta)
         yF = ge2[i-1][1]*sin(ge2[i-1][2])+n*ge2[i-1][3]*sin(ge2[i-1][4]);
         //odecteni stare sily od momentu
         fill2[i][3] = fill2[i][3] - fill2[i][1] * yF;
         //uprava vodorovne sily
         if (u_ex[i][3] < 0.) fill2[i][1] = fill2[i][1] * KFill[2] / KFill[1];
         if (u_ex[i][3] > 0.) fill2[i][1] = fill2[i][1] *
                  (KFill[1] + (KFill[3] - KFill[1]) / max_u_ex * u_ex[i][3])
                  / KFill[1];
         //zapocteni do momentu
         fill2[i][3] = fill2[i][3] + fill2[i][1] * yF;
         
         //B] bocni tlak od sil z dopravy - je-li pozadovano (KFill[4] == 1.)
         if (KFill[4] == 1.)
         {
           if(q2[i][2] != 0.)
           {    
             //urceni psobiste sily jako nasobek n
             n = (q2[i][3] - ge2[i-1][1]*
                (q2[i][2]*cos(ge2[i-1][2])+q2[i][1]*sin(ge2[i-1][2]))
                )/(
                ge2[i-1][3]*
                (q2[i][2]*cos(ge2[i-1][4])+q2[i][1]*sin(ge2[i-1][4]))
                );
             //svisla osuradnice vosorovne sily
             //k bodu "0" bloku je yF=a*sin(alfa) + n*b*sin(beta)
             yF = ge2[i-1][1]*sin(ge2[i-1][2])+n*ge2[i-1][3]*sin(ge2[i-1][4]);
             //odecteni stare sily od momentu
             q2[i][3] = q2[i][3] - q2[i][1] * yF;
             //uprava vodorovne sily
             if (u_ex[i][3] < 0.) q2[i][1] = q2[i][1] * KFill[2] / KFill[1];
             if (u_ex[i][3] > 0.) q2[i][1] = q2[i][1] *
                  (KFill[1] + (KFill[3] - KFill[1]) / max_u_ex * u_ex[i][3])
                  / KFill[1];
             //zapocteni do momentu
             q2[i][3] = q2[i][3] + q2[i][1] * yF;
           }    
         }    
     }
     return;
}

float signum(float A)
{
    /*
    vrati znamenko cisla A nebo nulu
    */
    if (A == 0.) return 0.;
    if (A < 0.) return -1.;
    if (A > 0.) return 1.;
}
     
void modif_q2(int N, float **q2, float **ge2, float *KFill)
{
    /*
    Aplikuje soucintel zemniho tlaku na sily od dopravy
    */
    
    //lokalni promenne
    int i;
    float yF, xF, n;
    
    //vypocet
    for(i=1; i<=N; i++)
    {
      if(q2[i][2] != 0.)
      {  
        //pusobiste sily - v momentu je jen svisla slozka - vodorovna dosud nulova
        xF = q2[i][3] / q2[i][2];
        n = (xF - ge2[i-1][1] * cos(ge2[i-1][2]))/(ge2[i-1][3]*cos(ge2[i-1][4]));
        yF = ge2[i-1][1] * sin(ge2[i-1][2]) + n * ge2[i-1][3] * sin(ge2[i-1][4]);
        //vodorovna sila 
        q2[i][1] = q2[i][2] * KFill[1] 
                   * ge2[i-1][3] * cos(ge2[i-1][4]) * signum(ge2[i-1][4]);
        //novy moment sily
        q2[i][3] = q2[i][3] + q2[i][1] * yF;
      }    
    }       
    return;
}                       
