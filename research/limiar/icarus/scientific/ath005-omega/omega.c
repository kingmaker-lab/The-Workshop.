/* ICARUS OMEGA: Linux x86_64, native streaming executable. */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <sys/resource.h>
#include <glob.h>
#include <errno.h>
#define MAX 256
#define D 768
#define F 30
typedef struct {double c[180],scale[30],coarse[24],benefit[14];} Model;
typedef struct {uint64_t cpu,wall;unsigned correct,expanded,over;unsigned char p[MAX],mask[MAX],group[MAX];double margin[MAX];} Result;
static uint64_t ns(clockid_t id){struct timespec t;if(clock_gettime(id,&t))exit(2);return (uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec;}
/* Welford is stable but expensive; centered first-sample moments avoid catastrophic cancellation.
   Identical in all arms, fallback to two-pass if cancellation is substantial. */
static void cheap(const double *x,double *f){
 for(int j=0;j<6;j++){
  const double *v=x+128*j;double o=v[0],s=0,z=0;
  for(int i=0;i<128;i++){double a=v[i]-o;s+=a;z+=a*a;}
  double m=s/128.,u=z/128.;f[j]=o+m;f[6+j]=u-m*m;
  if(f[6+j]<1e-10*u){double a=0;for(int i=0;i<128;i++){double b=v[i]-f[j];a+=b*b;}f[6+j]=a/128.;}
 }
}
static void tail(const double *x,double *f){
 for(int j=0;j<6;j++){
  const double *v=x+128*j;double a=0,b=0,c=0;
  for(int i=1;i<128;i++){double z=v[i]-v[i-1];a+=z*z;if(i>=8){z=v[i]-v[i-8];b+=z*z;}if(i>=32){z=v[i]-v[i-32];c+=z*z;}}
  f[12+3*j]=a/127.;f[13+3*j]=b/120.;f[14+3*j]=c/96.;
 }
}
int omega_features(const double *x,double *f){if(!x||!f)return -1;cheap(x,f);tail(x,f);return 0;}
/* Affine squared-distance scores, with common feature-square term removed.
   Model coefficients stored as standardized centroids and scales.
   Full and adaptive expansions evaluate precisely the same score function. */
static double distance(const double *f,const double *c,const double *scale,int lo,int hi){
 double d=0;for(int j=lo;j<hi;j++){double z=(f[j]-c[j])*scale[j];d+=z*z;}return d;
}
static int pick(const double *d,int lo,int hi,double *margin){
 int p=lo;double a=INFINITY,b=INFINITY;
 for(int k=lo;k<hi;k++){if(d[k]<a){b=a;a=d[k];p=k;}else if(d[k]<b)b=d[k];}
 *margin=(b-a)/(1.+a+b);return p;
}
static int bin(double m){const double e[]={.02,.05,.10,.20,.40,.60};int i=0;while(i<6&&m>=e[i])i++;return i;}
/* 0 FULL,1 OMEGA,2 LITE,3 STATIC. Group 0 dynamic classes 0..3, group 1 static 4..5. */
static void run(const double *x,const unsigned char *y,unsigned n,int mode,int q,double th,const Model *m,Result *r){
 memset(r,0,sizeof(*r));uint64_t w=ns(CLOCK_MONOTONIC),c=ns(CLOCK_PROCESS_CPUTIME_ID);
 for(unsigned i=0;i<n;i++){
  double f[F],d[6]={0},margin=0,ignored;const double *v=x+i*D;unsigned cap=(i+1)*(unsigned)q/4;
  cheap(v,f);int p,g=255,expand=mode==0;
  if(mode!=0){
   g=distance(f,m->coarse+12,m->scale,0,12)<distance(f,m->coarse,m->scale,0,12);
   int lo=g?4:0,hi=g?6:4;
   for(int k=lo;k<hi;k++)d[k]=distance(f,m->c+k*F,m->scale,0,12);
   p=pick(d,lo,hi,&margin);
   expand=mode==3?cap>i*(unsigned)q/4:mode==1&&r->expanded<cap&&m->benefit[g*7+bin(margin)]>th;
  }else p=0;
  if(expand){
   tail(v,f);
   for(int k=0;k<6;k++){
    if(mode==0||k<(g?4:0)||k>=(g?6:4))d[k]=distance(f,m->c+k*F,m->scale,0,12);
    d[k]+=distance(f,m->c+k*F,m->scale,12,30);
   }
   p=pick(d,0,6,&ignored);r->expanded++;
  }
  r->p[i]=(unsigned char)(p+1);r->mask[i]=(unsigned char)expand;r->group[i]=(unsigned char)g;r->margin[i]=margin;r->correct+=r->p[i]==y[i];
  unsigned bound=mode==0?i+1:mode==2?0:cap;
  if(r->expanded>bound&&r->expanded-bound>r->over)r->over=r->expanded-bound;
 }
 r->cpu=ns(CLOCK_PROCESS_CPUTIME_ID)-c;r->wall=ns(CLOCK_MONOTONIC)-w;
}
static int read_exact(FILE *f,void *p,size_t n){return fread(p,1,n,f)==n;}
static int guard(void){
 FILE *f=fopen("/proc/meminfo","r");if(!f)return 0;
 char line[256];unsigned long kb=0;while(fgets(line,sizeof(line),f))if(sscanf(line,"MemAvailable: %lu kB",&kb)==1)break;fclose(f);
 if(kb<262144)return 0;
 const char *patterns[]={"/sys/class/thermal/thermal_zone*/temp","/sys/class/hwmon/hwmon*/temp*_input"};
 for(int k=0;k<2;k++){glob_t g={0};int rc=glob(patterns[k],0,NULL,&g);if(rc==0)for(size_t i=0;i<g.gl_pathc;i++){
  FILE *t=fopen(g.gl_pathv[i],"r");long v;if(t){int ok=fscanf(t,"%ld",&v);fclose(t);if(ok==1&&v>=80000){globfree(&g);return 0;}}
 }globfree(&g);}
 return 1;
}
static unsigned rng(unsigned *s){*s^=*s<<13;*s^=*s>>17;*s^=*s<<5;return *s;}
static void print_result(unsigned subject,unsigned trial,unsigned batch,unsigned n,int rep,int mode,const unsigned char *y,const Result *r){
 printf("B,%u,%u,%u,%u,%d,%d,%llu,%llu,%u,%u,%u,",subject,trial,batch,n,rep,mode,(unsigned long long)r->cpu,(unsigned long long)r->wall,r->correct,r->expanded,r->over);
 for(unsigned i=0;i<n;i++)printf("%u",y[i]);
 putchar(',');for(unsigned i=0;i<n;i++)printf("%u",r->p[i]);
 putchar(',');for(unsigned i=0;i<n;i++)printf("%u",r->mask[i]);
 putchar(',');for(unsigned i=0;i<n;i++)printf("%u",r->group[i]==255?2:r->group[i]);
 for(unsigned i=0;i<n;i++)printf(",%.17g",r->margin[i]);
 putchar('\n');
}
int main(int argc,char **argv){
 if(argc!=9){fprintf(stderr,"usage: omega model.bin data.bin batch q threshold reps mode(-1 paired,0..3 single) cap_seconds(0 unlimited)\n");return 2;}
 int size=atoi(argv[3]),q=atoi(argv[4]),reps=atoi(argv[6]),mode=atoi(argv[7]),cap=atoi(argv[8]);double th=strtod(argv[5],NULL);
 if(size<1||size>MAX||q<1||q>3||reps<1||reps>7||mode< -1||mode>3||cap<0||!isfinite(th))return 2;
 if(!guard()){fprintf(stderr,"SAFETY STOP\n");return 3;}
 FILE *mf=fopen(argv[1],"rb"),*f=fopen(argv[2],"rb");Model m;
 if(!mf||!f||!read_exact(mf,&m,sizeof(m))||fgetc(mf)!=EOF)return 2;
 fclose(mf);char magic[8];if(!read_exact(f,magic,8)||memcmp(magic,"OMEGA001",8))return 2;
 double *x=malloc((size_t)size*D*sizeof(double));if(!x)return 2;
 unsigned char y[MAX];unsigned batch=0;uint64_t start=ns(CLOCK_MONOTONIC);int truncated=0;
 for(;;){
  uint32_t h[4];size_t got=fread(h,sizeof(uint32_t),4,f);if(got==0&&feof(f))break;
  if(got!=4||h[0]<1||h[0]>24||h[2]<1||h[3]<1||h[3]>6)return 2;
  unsigned left=h[2];
  while(left){
   if(cap&&ns(CLOCK_MONOTONIC)-start>=(uint64_t)cap*1000000000ULL){truncated=1;goto finish;}
   if(!guard()){fprintf(stderr,"SAFETY STOP batch=%u\n",batch);return 3;}
   unsigned n=left<(unsigned)size?left:(unsigned)size;
   for(unsigned i=0;i<n;i++){if(!read_exact(f,x+i*D,D*sizeof(double)))return 2;y[i]=(unsigned char)h[3];}
   Result r;int lo=mode<0?0:mode,hi=mode<0?4:mode+1;
   for(int a=lo;a<hi;a++)run(x,y,n,a,q,th,&m,&r);
   unsigned seed=0x9e3779b9u^batch^((unsigned)q<<24);
   for(int rep=0;rep<reps;rep++){
    int order[4]={0,1,2,3};
    if(mode<0)for(int j=3;j>0;j--){int k=(int)(rng(&seed)%(unsigned)(j+1));int z=order[j];order[j]=order[k];order[k]=z;}
    for(int a=lo;a<hi;a++){
     int arm=mode<0?order[a]:a;run(x,y,n,arm,q,th,&m,&r);
     print_result(h[0],h[1],batch,n,rep,arm,y,&r);
    }
   }
   if(fflush(stdout))return 2;
   left-=n;batch++;
  }
 }
 finish:
 {struct rusage u;if(getrusage(RUSAGE_SELF,&u))return 2;
 printf("END,%u,%d,%ld,%llu\n",batch,truncated,u.ru_maxrss,(unsigned long long)(ns(CLOCK_MONOTONIC)-start));}
 free(x);fclose(f);return ferror(stdout)?2:0;
}
