/* Research-only test shim: include exact original implementation, infer selected
   membership by toggling a single label. No production code modifications. */
#include "../../experiments/exp00x-icaro/icaro.c"
int euclid_mask(const double *weights,size_t n,int b,int cap,uint8_t *mask){
    if(!weights||!mask||!n||n>MAX_N)return -1;
    double x[MAX_N*32]={0};uint8_t y[MAX_N];Result base={0},r={0};
    for(size_t i=0;i<n;i++){
        if(!isfinite(weights[i])||weights[i]<0||weights[i]>10)return -2;
        x[32*i]=weights[i];y[i]=1;
        for(size_t j=4;j<32;j++)x[32*i+j]=-100.;
    }
    if(rank_batch(x,y,n,b,cap,&base)||base.over)return -3;
    for(size_t i=0;i<n;i++){
        y[i]=0;
        int rc=rank_batch(x,y,n,b,cap,&r);y[i]=1;
        if(rc||r.over||r.terms!=base.terms)return -4;
        if(r.correct==base.correct+1)mask[i]=1;
        else if(r.correct+1==base.correct)mask[i]=0;
        else return -5;
    }
    return 0;
}
