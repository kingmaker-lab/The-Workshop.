/* ARCHIMEDES-01: synthetic raw-signal aggregation, original ICARO heap. */
#include "../../experiments/exp00x-icaro/icaro.c"
typedef struct {
    uint64_t cpu_ns,wall_ns,terms,raw_reads,over,correct,expanded;
    double checksum;
} ArchResult;
static double arch_tail(const double *v,int w,double scale){
    double tail=0.;
    for(int j=0;j<28;j++){
        double sum=0.;
        for(int z=0;z<w;z++)sum+=v[4+j*w+z];
        tail+=.15*(sum*scale);
    }
    return tail;
}
/* modes: full, lite, static prefix schedule, ICARO rank, random prefix rank,
   global top-k (diagnostic, allowed to violate prefix only). */
int arch_run(const double *x,const uint8_t *y,size_t n,int b,int w,int mode,
             uint64_t seed,ArchResult *out,uint8_t *chosen_out){
    if(!x||!y||!out||!chosen_out||!n||n>MAX_N||!valid_budget(b)||
       !(w==1||w==4||w==16||w==64||w==256)||mode<0||mode>5)return -1;
    size_t stride=4+28*(size_t)w,k=n*(b-4)/28,len=0;
    double margins[MAX_N];Choice heap[MAX_N];uint8_t chosen[MAX_N]={0};
    ArchResult r={0};
    uint64_t wall=ns(CLOCK_MONOTONIC),cpu=ns(CLOCK_PROCESS_CPUTIME_ID);
    double scale=1./sqrt((double)w);
    for(size_t i=0;i<n;i++){
        double v=0.;for(int j=0;j<4;j++)v+=x[i*stride+j];
        margins[i]=v;
    }
    if(mode==0){for(size_t i=0;i<n;i++)chosen[i]=1;}
    else if(mode==2){for(size_t i=0;i<n;i++)chosen[i]=((i+1)*(b-4)/28>i*(b-4)/28);}
    else if(mode>=3){
        if(!seed)seed=1;
        for(size_t i=0;i<n;i++){
            double p=margins[i];
            if(mode==4){seed^=seed<<13;seed^=seed>>7;seed^=seed<<17;p=(double)(seed>>11)*0x1p-53;}
            size_t quota=mode==5?k:(i+1)*(b-4)/28;
            push(heap,&len,(Choice){p,i});if(len>quota)pop(heap,&len);
        }
        for(size_t i=0;i<len;i++)chosen[heap[i].index]=1;
    }
    for(size_t i=0;i<n;i++){
        double score=margins[i];
        if(chosen[i])score+=arch_tail(x+i*stride,w,scale);
        r.correct+=(score>=0)==y[i];r.checksum+=score;
        r.expanded+=chosen[i];r.terms+=chosen[i]?32:4;
        r.raw_reads+=4+(chosen[i]?28*(uint64_t)w:0);
        uint64_t bound=(i+1)*(uint64_t)(mode==0?32:mode==1?4:b);
        if(r.terms>bound&&r.terms-bound>r.over)r.over=r.terms-bound;
    }
    memcpy(chosen_out,chosen,n);
    r.cpu_ns=ns(CLOCK_PROCESS_CPUTIME_ID)-cpu;
    r.wall_ns=ns(CLOCK_MONOTONIC)-wall;
    *out=r;return 0;
}
