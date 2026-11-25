/* ASCENSION C11 kernel. Research only. */
#include <stdint.h>
#include <stddef.h>
#include <math.h>
typedef struct { uint64_t correct, terms, forced, over; } Result;
int asc_run(const double *x,const uint8_t *y,size_t n,int b,double t,int mode,Result *out){
    if(!x||!y||!out||!n||n>20000||(b!=8&&b!=16&&b!=24&&b!=32)||mode<0||mode>5||isnan(t)||t<0)return -1;
    Result r={0,0,0,0};
    int64_t credit=0;
    t=fmin(t,12.0);
    int ticks=(int)llround(t*700),err=0;
    for(size_t i=0;i<n;i++){
        const double *v=x+32*i;
        double s=0;
        for(int j=0;j<4;j++)s+=v[j];
        int expand=0;
        if(mode==0||(mode>=2&&b==32))expand=1;
        else if(mode>=2){
            credit+=b-4;
            int wants=mode<=3?fabs(s)<t:fabs(s)*700<ticks;
            expand=wants&&credit>=28;
            if(expand)credit-=28;
            else if(wants)r.forced++;
            int cost=expand?32:4;
            if(mode==3)t=fmin(12.,fmax(0.,t+.12*(b-cost)/28.));
            if(mode>=4){
                err+=3*(b-cost);
                if(mode==4||(i+1)%16==0){
                    ticks+=err;
                    if(ticks<0)ticks=0;
                    if(ticks>8400)ticks=8400;
                    err=0;
                }
            }
        }
        if(expand){double tail=0;for(int j=4;j<32;j++)tail+=v[j]*.15;s+=tail;}
        r.correct+=(uint64_t)((s>=0)==y[i]);
        r.terms+=expand?32:4;
        int64_t over=(int64_t)r.terms-(int64_t)(i+1)*b;
        if(over>0&&(uint64_t)over>r.over)r.over=(uint64_t)over;
    }
    *out=r;
    return 0;
}
