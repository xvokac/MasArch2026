///////////////////////////////////////////
// FUNKCE pro iteracni vypocty podle 
//           a] Livesleye d_CODE = 1
//           b] Crisfielda & Packhama d_CODE = 2
//           c] podle libovolne zadaneho interakcniho diagramu d_CODE = 4

//////////////////////////////////////////
//DEKLARACE FUNKCI
void cal_d_crush(int N, float d_sigma, float **N_e, float *d_crush);
void cal_d_crush2(int N, char *s_inter, float **N_e, float *d_crush, float D);
void modif_geom2(int N, float **ge2, float **ge3, float *d_crush, int d_CODE); 
void cal1_N_e(float **a, int *izrov, int n, float **N_e, 
              int N, float D, float **ge3);
void cal2_N_e(float **a, int *izrov, int n, float **N_e, 
              int N, float D, float **ge3, float *dis);
void write_sim_to_txt(char *s_sim, char *s_txt);
void cal_dis(float *dis, int N, float d_sigma, float *d_crush);  
void modif_a_dis(float **a, float *dis, int N);


/////////////////////////////////////////
//DEFINICE FUNKCI 

void cal_d_crush(int N, float d_sigma, float **N_e, float *d_crush)
{
    /*
    vypocte vektor d_crush, tery obsahuje tloustku tlacene casti
    prurezu podle plasticke teorie rozdeleni napeti v prurezu,
    tato tloustka potom redukuje tloustku klenby na fiktivni tloustku
    klenby - redukce je ruzna podle metody
    
    Legenda:
        N - pocet bloku
        d_sigma - max. hodnota normaloveho napeti
        N_e - matice s normalovymi silami a excentricitami
        d_crush - vektor, kam se zapisuji velikosti tlacene tloustky prurezu
    */
    
    //lokalni promenne
    int i;
    //vypocet
    for (i=0; i<=N; i++)
    {
        d_crush[i] = N_e[1][i] / d_sigma;
    }
    return;    
}   

void cal_d_crush2(int N, char *s_inter, float **N_e, float *d_crush, float D)
{
    /*
    pocita minimalni vzdalenost N od lice oblouku pro dany interakcni diagram
    pri d_CODE = 4
    
    Legenda:
        N - pocet bloku
        s_inter - soubor txt s interakcnim diagramem
        N_e[1..2][0..N] - aktualni normalove sily a excentricity
        d_crush[0..N] - vektor pro redikci na fiktivni tloustku
        D - tloustka klenby
    
    Format souboru s interakcnim diagramem - viz MELB.txt    
    */
    
    //lokalni promenne
    FILE *f;
    int nn, index;
    int i, j;
    float *SN, *SM;
    float dy, SN_max;
    
    //otevreni souboru s interakcnim diagramem
    f = fopen(s_inter, "r");
    if (f == NULL) 
          nrerror(" Soubor s interakcnim diagramem se nepodarilo otevrit!");    
    //cteni zakladnich udaju o interakcnim diagramu
    jump(f);//preskocen prvni radek - je rezervovan na poznamky
    fscanf(f, "%d", &nn); //pocet bodu
    fscanf(f, "%f", &SN_max); //maximalni normalova sila    
    //alokace pameti
    SN = vector(0, nn);
    SM = vector(0, nn);    
    //cteni bodu interakcniho diagramu
    for(i=0; i<=nn; i++)
    {
        fscanf(f, "%f", SN+i);
        fscanf(f, "%f", SM+i);
    }    
    //uzavreni souboru
    fclose(f);  
    
    //vypocet vektoru d_crush
    for(i=0; i<=N; i++)
    {
        //kontrola velikosti normalove sily
        if (N_e[1][i] >= SN_max) 
              nrerror(" Normalove sily jsou vetsi nez v interakcnim diagramu!");
        //hledani intervalu pro interpolaci
        index = -10;
        for(j=0; j<nn; j++)
        {
            if ( SN[j] <= N_e[1][i] && N_e[1][i] < SN[j+1] ) index = j - 1;
        }
        //uprava cisla index pro kraje diagramu 
        if (index == -10) 
          nrerror(" Nebyl nalezen interval pro interpolaci interakcniho diagramu!");
        if (index < 0) index = 0;
        if (index > nn - 3) index = nn - 3;
        //vypocet maximalniho momentu pro danou normalovou silu - zapis do d_crush[i]
        //interpolace polynomem 4. stupne
        polint(SN + index, SM + index, 4, N_e[1][i], d_crush + i, &dy);
        d_crush[i] = D / 2. - d_crush[i] / N_e[1][i];
    }        
    return;
} 

void modif_geom2(int N, float **ge2, float **ge3, float *d_crush, int d_CODE)
{
    /*
    Prepocte ge2 na fiktivni tloustku ge3
    */
    //lokalni promenne
    int i;
    //vypocet
    for (i=0; i<=N; i++)
    {
        switch (d_CODE)
        {
            case 1:
            case 2:
               ge3[i][1] = ge2[i][1] - d_crush[i] / 2. * d_CODE;
               break;
            case 4:
               ge3[i][1] = ge2[i][1] - d_crush[i];
               break; 
        }    
        ge3[i][2] = ge2[i][2];
        ge3[i][3] = ge2[i][3];
        ge3[i][4] = ge2[i][4];
    }        
    return;
}   

void cal1_N_e(float **a, int *izrov, int n, float **N_e, 
              int N, float D, float **ge3)
{
    /*
    z finalni simplexove tabulky a tloustky klenby vypocte normalove sily
    a jejich excentricity
    
    jedna se o modifikovanou funkci cal_N_e pri iteracnim vypoctu d_CODE = 1
    
    DE TO ZJEDNODUSIT A TUTO FUNKCI POUZIVAT I PRED ITEROVANIM 
    / VYZADUJE ALE DROBNE MODIFIKACE /
    
    parametry:
    float **a[1..m+2][1..n+1] - finalni simplexova tabulka
    float **N_e[1..2][0..N] - matice s normal. silami a excentricitami
    int **izrov[1..n] - vektor urcujici indexi nulovych promennych
    int n - pocet promennych v simplexove cilove funkci
    int N - pocet bloku
    float D - tlouska klenby
    float **ge3[0..N][1..4] - geometrie v pol. sour. s fikivnimi tloustkami 
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
        N_e[1][k] = (Mext + Mint) / (2. * ge3[k][1]) ;
        N_e[2][k] = Mext * (2. * ge3[k][1]) / ( Mext + Mint )
                    + (D/2. - ge3[k][1]);
        
    }
    return; 
}  

void cal2_N_e(float **a, int *izrov, int n, float **N_e, 
              int N, float D, float **ge3, float *dis)
{
    /*
    z finalni simplexove tabulky a tloustky klenby vypocte normalove sily
    a jejich excentricity
    
    jedna se o modifikovanou funkci cal_N_e pri iteracnim vypoctu d_CODE = 2
    
    parametry:
    float **a[1..m+2][1..n+1] - finalni simplexova tabulka
    float **N_e[1..2][0..N] - matice s normal. silami a excentricitami
    int **izrov[1..n] - vektor urcujici indexi nulovych promennych
    int n - pocet promennych v simplexove cilove funkci
    int N - pocet bloku
    float D - tlouska klenby
    float **ge3[0..N][1..4] - geometrie v pol. sour. s fikivnimi tloustkami 
    float d_crush - maximalni normalove napeti
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
        
        //oprava o disipovane sily - jejich odecteni
        Mint = Mint - dis[k];
        Mext = Mext - dis[k];
        
        //vypocet N a e
        N_e[1][k] = (Mext + Mint) / (2. * ge3[k][1]) ;
        N_e[2][k] = Mext * (2. * ge3[k][1]) / ( Mext + Mint )
                    + (D/2. - ge3[k][1]);
        
    }
    return; 
}  



void write_sim_to_txt(char *s_sim, char *s_txt)
{
    /*
    */
    //lokalni promenne
    int n, m, CODE;
    int i, j;
    float a;
    FILE *fb, *ft;
    //otevreni souboru
    fb = fopen(s_sim, "rb");
    ft = fopen(s_txt, "w");
    //cteni souboru a zapis
    fread(&n, sizeof(int), 1, fb);
    fprintf(ft, " %d\n", n);
    fread(&m, sizeof(int), 1, fb);
    fprintf(ft, " %d\n", m);
    fread(&CODE, sizeof(int), 1, fb);
    fprintf(ft, " %d\n", CODE);
    //cilova funkce
    for(i=1; i<=n; i++)
    {
        fread(&a, sizeof(float), 1, fb);
        fprintf(ft, " %f", a);
    }
    fprintf(ft, "\n");
    //podminky
    for (j=1; j<=m; j++)
    {
        for(i=1; i<=n; i++)
        {
             fread(&a, sizeof(float), 1, fb);
             fprintf(ft, " %f", a);   
         }
        fread(&a, sizeof(float), 1, fb);
        fprintf(ft, " %f", a);
        fread(&CODE, sizeof(int), 1, fb);
        fprintf(ft, " %d\n", CODE); 
    }
}           
    

void cal_dis(float *dis, int N, float d_sigma, float *d_crush)
{
    /*
    Pocita disipovanou praci v kloubech pro d_CODE =2
    
    Legenda:
    dis[0..N] - disipovana prace v kloubu
    N - pocet bloku
    d_sigma / maximalni napeti
    d_crush - tloustka na ktere pusobi d_crush
    */
    int i;
    for (i=0; i<=N; i++)
    {
        dis[i] = 0.5 * d_sigma * pow(d_crush[i], 2.);
    }    
    return;
}  

void modif_a_dis(float **a, float *dis, int N)
{
    /*
    Pripocte k matici a (k 1. radku, kde je cilova funkce) hodnoty
    disipovane prace v kloubech
    
    Legenda:
    a[1..m+2][1..n+1] - simplexova tabulka pro simplx()
    dis[0..N] - disipovane sily
    N - pocet bloku
    */
    int i;
    int j = 0;
    for(i=2; i<= 1 + 2*(N+1); i=i+2)
    {
        a[1][i] = a[1][i] - dis[j];
        a[1][i+1] = a[1][i+1] - dis[j];
        j++;
    }    
    return;
}         
