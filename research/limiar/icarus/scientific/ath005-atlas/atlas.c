/* MOTION: resident, prefiltered real IMU windows; no external dependencies. */
#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stddef.h>
#include <math.h>
#include <time.h>
#define NCHAN 6
#define NS 128
#define NF 30
#define NC 6
#define MAX_BATCH 64
typedef struct {uint64_t cpu_ns,wall_ns,correct,expanded,features,over;} Result;
static uint64_t stamp(clockid_t id){struct timespec t;clock_gettime(id,&t);return (uint64_t)t.tv_sec*1000000000u+(uint64_t)t.tv_nsec;}
static void cheap(const double *x,double *f){
    for(int j=0;j<NCHAN;j++){double s=0;for(int i=0;i<NS;i++)s+=x[j*NS+i];f[j]=s/NS;}
}
static void tail(const double *x,double *f){
    for(int j=0;j<NCHAN;j++){
        const double *v=x+j*NS;double a=0,b=0,c=0,d=0;
        for(int i=0;i<NS;i++){
            double z=v[i]-f[j];a+=z*z;
            if(i>=1){z=v[i]-v[i-1];b+=z*z;}
            if(i>=8){z=v[i]-v[i-8];c+=z*z;}
            if(i>=32){z=v[i]-v[i-32];d+=z*z;}
        }
        f[6+j*4]=a/NS;f[7+j*4]=b/(NS-1);
        f[8+j*4]=c/(NS-8);f[9+j*4]=d/(NS-32);
    }
}
int atlas_features(const double *x,double *f){if(!x||!f)return -1;cheap(x,f);tail(x,f);return 0;}
static int predict(const double *d,double *margin){
    int best=0;double first=INFINITY,second=INFINITY;
    for(int k=0;k<NC;k++){if(d[k]<first){second=first;first=d[k];best=k;}else if(d[k]<second)second=d[k];}
    *margin=second-first;return best+1;
}
static void accumulate(const double *f,const double *cent,const double *scale,double *d,int start,int end){
    for(int k=0;k<NC;k++)for(int j=start;j<end;j++){double z=(f[j]-cent[k*NF+j])*scale[j];d[k]+=z*z;}
}
/* mode 0 FULL,1 LITE,2 STATIC,3 CAUSAL. Budget is fraction q/4 of expansions.
   Cheap scores are causal, batch length is known. Exact quota and prefix. */
int atlas_run(const double *x,const uint8_t *y,size_t n,int q,int mode,double th,
              const double *cent,const double *scale,Result *out,uint8_t *pred,uint8_t *mask,double *margins){
    if(!x||!y||!cent||!scale||!out||!pred||!mask||!margins||!n||n>MAX_BATCH||
       q<1||q>4||mode<0||mode>3||!isfinite(th)||th<0)return -1;
    Result r={0};size_t k=n*(size_t)q/4,count=0;
    uint64_t wall=stamp(CLOCK_MONOTONIC),cpu=stamp(CLOCK_PROCESS_CPUTIME_ID);
    for(size_t i=0;i<n;i++){
        double f[NF],d[NC]={0},margin,ignored;
        const double *v=x+i*NCHAN*NS;
        cheap(v,f);accumulate(f,cent,scale,d,0,6);
        int p=predict(d,&margin);margins[i]=margin;
        size_t quota=(i+1)*(size_t)q/4;
        int expand=mode==0||(mode==2&&quota>i*(size_t)q/4)||
                   (mode==3&&count<quota&&(margin<th||k-count==n-i));
        if(expand){tail(v,f);accumulate(f,cent,scale,d,6,NF);p=predict(d,&ignored);count++;}
        pred[i]=(uint8_t)p;mask[i]=(uint8_t)expand;
        r.correct+=p==y[i];r.expanded+=expand;r.features+=6+24*(uint64_t)expand;
        size_t bound=mode==0?i+1:mode==1?0:quota;
        if(count>bound&&count-bound>r.over)r.over=count-bound;
    }
    r.cpu_ns=stamp(CLOCK_PROCESS_CPUTIME_ID)-cpu;r.wall_ns=stamp(CLOCK_MONOTONIC)-wall;*out=r;return 0;
}
