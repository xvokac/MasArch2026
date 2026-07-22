#include "nrutil.h"
#define EPS 5.0e-3  //mensi cisla v absolutni hodnote jsou povazovana za nulu


//Here EPS is the absolute precision, 
//which should be adjusted to the scale of your variables. 
#define FREEALL free_ivector(L3,1,m);free_ivector(L1,1,n+1);

void simplx(float **a, int m, int n, int m1, int m2, int m3, int *icase,
            int izrov[] , int iposv[])
//Simplex method for linear programming. 
//Input parameters a, m, n, mp, np, mi, m2, and m3,
//and output parameters a, icase, izrov, and iposv are described above.
  {
  void simp1(float **a, int mm, int L1[], int nL1, int iabf, int *kp, 
             float *bmax);
  void simp2(float **a, int m, int n, int *ip, int kp);
  void simp3(float **a, int i1, int k1, int ip, int kp);
  int i,ip,is,k,kh,kp,nL1; 
  int *L1,*L3;
  float q1,bmax; 

  if (m != (m1+m2+m3)) nrerror("Bad input constraint counts in simplx"); 
  L1=ivector(1 ,n+1);
  L3=ivector(1,m);
  nL1=n;
  for (k=1;k<=n;k++) L1[k]=izrov[k]=k;
  //Initialize index list of columns admissible for exchange, 
  //and make all variables initially right-hand.
  for (i=1;i<=m;i++) 
    {
    if (a[i+1] [1] < 0.0) nrerror("Bad input tableau in simplx"); 
    //Constants bi must be nonnegative.
    iposv[i]=n+i;
    //Initial left-hand variables. ml type constraints are represented 
    //by having their slack variable initially left-hand, with no artificial variable. 
    //m2 type constraints have their slack variable initially left-hand, with a minus sign, 
    //and their artificial variable handled implicitly during their first exchange. 
    //m3 type constraints have their artificial variable initially left-hand.
    }
  if (m2+m3) 
    {	
    //Origin is not a feasible starting SOlution: we must do phase one.
	for (i=1;i<=m2;i++) L3[i]=1;	
    //Initialize list of m2 constraints whose slack variables 
    //have never been exchanged out of the initial basis.
    for (k=1;k<=(n+1);k++) 
      {
      //Compute the auxiliary objective function.
      q1=0.0;
      for (i=m1+1;i<=m;i++) q1 += a[i+1] [k];
      a [m+2] [k] = -q1;      
      }
    for (;;) 
      {
	  simp1 (a ,m+1, L1 ,nL1, 0 ,&kp, &bmax) ;	
      //Find max. coeff. of auxiliary objective fN.
      if (bmax <= EPS && a[m+2] [1] < -EPS) 
        {         
        *icase = -1;
        //Auxiliary objective function is stili negative and can't be im proved, 
        //hence no feasible solution exists.
	    FREEALL return;
        } 
      else if (bmax <= EPS && a[m+2] [1] <= EPS) 
        {
        //Auxiliary objective function is zero and can't be improved; 
        //we have a feasible starting vector. Clean out the artificial variables 
        //corresponding to any remaining equatity constraints 
        //by goto ona and then move on to phase 000.
        for (ip=m1+m2+1;ip<=m;ip++) 
          {
	      if (iposv[ip] == (ip+n)) 
            { 
            //Found an artificial variable for an equality constraint.
	        simp1(a,ip,L1 ,nL1,1 ,&kp,&bmax);	
	        if (bmax > EPS)goto one;	
            //Exchange with column corresponding to maximum pivot element in row.
            }
          }
        for (i=m1+1;i<=m1+m2;i++) 
          //Change sign of row for any m2 constraints stili 
          //present from the in itial basis.
          if (L3[i-m1] == 1)
	        for (k=1;k<=n+1;k++)
	          a[i+1] [k] = -a [i+1] [k];
	    break;  //Go to phase two.
        }        
      simp2(a,m,n,&ip,kp); //Locate a pivot element (phase ona).
      if (ip == 0) 
        {
        *icase = -1; 
        FREEALL return;
        //Maximum of auxiliary objective function is unbounded, 
        //SO no feasible solution exists.
        }
one:
        simp3(a,m+1,n,ip,kp);
        //Exchange a left- and a right-hand variable (phase ona), 
        //then update lists.


//Exchanged aut an artificial variable for an equality constraint. 
//Make sure it stays aut by removing it from the L1 list.


        if (iposv[ip] >= (n+m1+m2+1)) 
          {
          //Exchanged aut an artificial variable for an equality constraint. 
          //Make sure it stays aut by removing it from the L1 list.
	      for (k=1;k<=nL1;k++)
	        if (L1[k] == kp) break;
	      --nL1 ;
	      for (is=k;is<=nL1;is++) L1 [is] =L1 [is+1] ;
	      }
        else 
          {
	      kh=iposv [ip] -m1-n;
	      if (kh >= 1 && L3[kh]) 
            {
            //Exchanged aut an m2 type constraint for the first time. 
            //Correct the pívat column for the minus sign and 
            //the implicit artificial variable.
            L3[kh]=0;
            ++a[m+2] [kp+1];
            for (i=1;i<=m+2;i++)
              a[i] [kp+1] = -a[i] [kp+1] ;
            }
          }
        is=izrov[kp];   //Update lis15 of left- and right-hand 	variables.
        izrov[kp]=iposv[ip];
        iposv[ip]=is;
	  }	//Stili in phase ona, go back to the for(; ;) .
    }	
    //End of phase ONE code for finding an initial feasible solution. 
    //Now, in phase two, optimize it.
	for (;;) 
      {
      simp1(a,0,L1,nL1,0,&kp,&bmax) ;//Test the z-row for doneness.
      if (bmax <= EPS) //Done. Solution found. Return with the good news.
        {
        *icase=0; FREEALL return;
        }
      simp2(a,m,n,&ip,kp); //Locate a pívat element (phase two).
      if (ip == 0)   //Objective function is unbounded. Report and return.
        { 
        *icase=1; 
        FREEALL return;
        }
      simp3(a,m,n,ip,kp);
      //Exchange a left- and a right-hand variable (phase two).
      is=izrov[kp] ; 
      izrov[kp]=iposv[ip]; 
      iposv[ip]=is;
    }//and return for another iteration.    
  }

///////////////////////////////////////////////////////////////////////////
//The preceding routine mak:es use of the following utility functions.

#include <math.h>

void simp1(float **a, int mm, int L1[], int nL1, int iabf, int *kp,
           float *bmax)
//Determines the maximum of these elemen15 whose index is contained 
//in the supplied list 11, either with or without taking the absolute 
//value, as flagged by iabf.
  {
  int k;
  float test;  
  
  if (nL1 <= 0) //No eligible columns.
	*bmax=0.0;
  else 
    {
    *kp=L1 [1] ;
    *bmax=a[mm+1] [*kp+1];
    for (k=2;k<=nL1;k++) 
      {
      if (iabf == 0)
	    test=a[mm+1] [L1 [k] +1] -(*bmax) ;
      else
	    test=fabs(a[mm+1] [L1[k]+1])-fabs(*bmax);
	  if (test > 0.0) 
        {
	    *bmax=a [mm+1] [L1 [k] +1] ;
	    *kp=L1[k];
        }
      }
    }
  }







void simp2(float **a, int m, int n, int *ip, int kp) 
//Locate a pívat element, taking degeneracy into account.
  {
  int k,i;
  float qp,q0,q,q1;

  *ip=0;
  for (i=1;i<=m;i++)
    if (a[i+1][kp+1] < -EPS) break;  //Any possíble pívots?
  if (i>m) return;
  q1 = -a [i+1] [1] /a[i+1] [kp+1];
  *ip=i;
  for (i=*ip+1;i<=m;i++) 
    {
    if (a[i+1] [kp+1] < -EPS) 
      {
      q = -a[i+1] [1]/a[i+1] [kp+1];
      if (q < q1) 
        {
        *ip=i;
        q1=q;
        } 
      else if (q == q1) //We have a degeneracy.
        {
        for (k=1;k<=n;k++) 
          {
          qp = -a[*ip+1] [k+1]/a[*ip+1] [kp+1]; 
          q0 = -a[i+1] [k+1] /a[i+1] [kp+1] ;
          if (q0 != qp) break;
          }
        if (q0 < qp) *ip=i;
        }
      }
    }
  }



void simp3(float **a, int i1, int k1, int ip, int kp)
//Matrix operations to exchange a left-hand and ríght-hand variable (see text). 
  {
  int kk,ii; 
  float piv;

  piv=1.0/a[ip+1] [kp+1];
  for (ii=1;ii<=i1+1;ii++)
    if (ii-1 != ip) 
      {
      a[ii][kp+1] *= piv;
      for (kk=1;kk<=k1+1;kk++)
        if (kk-1 != kp)
	    a[ii] [kk] -= a[ip+1] [kk] * a[ii] [kp+1] ;

    }
  for (kk=1;kk<=k1+1;kk++)
	if (kk-1 != kp) a[ip+1][kk] *= -piv;
  a[ip+1] [kp+1]=piv;
  }


///////////////////////////////////////////////////////////////////////
//funkce - prevede **a na **tab - kompletni finalni simplexovou tabulku
void cal_final_tab(float **a, float *aa, int *iposv, int *izrov, 
                   float **tab, int m, int n)
{  /*
    float **a[1..m+2][1..n+1] je matice pouzivana predeslymi procedurami
    float **tab[1..m+2][1..m+n+2] je cela simplexova tabulka
    float *aa[1..n+1] je prvni radek simplexove tabulky pred vypoctem
    int *izrov jsou puvodni indexi promennych, ktere jsou nulove
    int *iposv jsou puvodni indexi promennych, ktere nejsou nulove, 
            jejich hodnoty jsou ve potom ve vektoru d[i][0]
    - vektory izrov resp. iposv udavaji, v jakem poradi jsou na konci vypoctu 
    sloupce matice flouat **a resp. jeji radky
    
    Finalni tabulka ma tvar (znaceni podle Prehledu uzite matematiky od
    Karla Rektoryse a kolektivu):
        
    c[0]       z[1]........z[n+m]       XXXX
    d[1][0]    d[1][1].....d[1][n+m]    c[1]
    ....       .....                    ....
    d[m][0]    d[m][1].....d[m][n+m]    c[m]    
    XXXX       c[1]........c[m][n+m]    XXXX
    
    Oproti PUM jsou prehozeny krajni sloupce a radky
    */
    
    //lokalni promene
    int i, j;
    
    //prepis zatim znamych hodnot matice
    for(i=1; i<=m+2; i++)
    {
        for(j=1; j<=n+1; j++)
        {
            tab[i][j] = a[i][j];
        }
    }
    
    //prepis sloupcu neznamych s nenulovou hodnotou 
    for(i=2; i<=m+1; i++)
    {
        for(j=n+2; j<=n+m+1;  j++)
        {
            if ( (i-2) == (j-n-2) ) tab[i][j] = 1.; //diagonalni prvek
            else tab [i][j] = 0.;    //mimo diagonalu 
        }
    }
    
    //originalni soucinitele z cilove funkce do posledniho radku
    for (i=1; i<=n+m; i++)
    {
        if(i<=n)
        {
            if(n >= (j=izrov[i])) tab[m+2][i+1] = aa [j+1];
            else tab[m+2][i+1] = 0.;
        }
        if(i>n)
        {
            if(n >= (j=iposv[i-n])) tab[m+2][i+1] = aa [j+1];
            else tab[m+2][i+1] = 0.;     
        }
    }     
    //originalni soucinitele cilove funkce do posledniho sloupce
    for (i=1; i<=m; i++)
    {
        if(n >= (j=iposv[i])) tab[i+1][n+m+2] = aa[j+1];
        else tab[i+1][n+m+2] = 0.;   
    }    
    //prvni radek - z[i]
    for (i=1; i<=n+m; i++)
    {
        tab[1][i+1] = 0.;
        for (j=1; j<=m; j++)
        {
            tab[1][i+1] = tab[1][i+1] +  tab[j+1][n+m+2]*tab[j+1][i+1];
        }
    }
    //konec vypoctu finalni kompletni simplexove tabulky       
    return;
}    
