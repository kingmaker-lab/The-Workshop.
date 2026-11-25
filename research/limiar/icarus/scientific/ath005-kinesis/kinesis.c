/* KINESIS: new experimental kernel, MOTION source unchanged. */
#include "../ath005-atlas/atlas.c"
#define KC 12
#define KB 7
static void kin_cheap(const double *x,double *f){
    for(int j=0;j<6;j++){
        const double *v=x+j*NS;double s=0,a=0;
        for(int i=0;i<NS;i++)s+=v[i];
        f[j]=s/NS;
        for(int i=0;i<NS;i++){double z=v[i]-f[j];a+=z*z;}
        f[6+j]=a/NS;
    }
}
static void kin_tail(const double *x,double *f){
    for(int j=0;j<6;j++){
        const double *v=x+j*NS;double a=0,b=0,c=0;
        for(int i=1;i<NS;i++){
            double z=v[i]-v[i-1];a+=z*z;
            if(i>=8){z=v[i]-v[i-8];b+=z*z;}
            if(i>=32){z=v[i]-v[i-32];c+=z*z;}
        }
        f[12+3*j]=a/(NS-1);f[13+3*j]=b/(NS-8);f[14+3*j]=c/(NS-32);
    }
}
int kin_features(const double *x,double *f){
    if(!x||!f)return -1;
    kin_cheap(x,f);kin_tail(x,f);return 0;
}
static int kin_group(const double *f,const double *coarse,const double *scale){
    double d[2]={0,0};
    for(int k=0;k<2;k++)for(int j=0;j<KC;j++){
        double z=(f[j]-coarse[k*KC+j])*scale[j];d[k]+=z*z;
    }
    return d[1]<d[0];
}
static void kin_acc(const double *f,const double *cent,const double *scale,double *d,int g,int lo,int hi){
    for(int k=0;k<3;k++)for(int j=lo;j<hi;j++){
        double z=(f[j]-cent[(g*3+k)*NF+j])*scale[j];d[k]+=z*z;
    }
}
static int kin_pred(const double *d,int g,double *margin){
    int best=0;double first=INFINITY,second=INFINITY;
    for(int k=0;k<3;k++){if(d[k]<first){second=first;first=d[k];best=k;}else if(d[k]<second)second=d[k];}
    *margin=(second-first)/(1.+second+first);return g*3+best+1;
}
static int kin_bin(double v){
    const double edges[6]={.02,.05,.10,.20,.40,.60};
    int b=0;while(b<6&&v>=edges[b])b++;return b;
}
/* 0 FLAT_FULL,1 HIER_FULL,2 HIER_LITE,3 STATIC,4 MARGIN,5 BENEFIT.
 * Both adaptive selectors exact-count and prefix constrained; no lookahead.
 */
int kin_run(const double *x,const uint8_t *y,size_t n,int q,int mode,double th,
 const double *cent,const double *scale,const double *coarse,const double *benefit,
 Result *out,uint8_t *pred,uint8_t *mask,double *margins,uint8_t *groups){
    if(!x||!y||!cent||!scale||!coarse||!benefit||!out||!pred||!mask||!margins||!groups||
       !n||n>MAX_BATCH||q<1||q>3||mode<0||mode>5||!isfinite(th))return -1;
    Result r={0};size_t count=0,k=n*(size_t)q/4;
    uint64_t wall=stamp(CLOCK_MONOTONIC),cpu=stamp(CLOCK_PROCESS_CPUTIME_ID);
    for(size_t i=0;i<n;i++){
        const double *v=x+i*NCHAN*NS;double f[NF],margin=0,ignored;int p,expand=0;
        kin_cheap(v,f);
        size_t quota=(i+1)*(size_t)q/4;
        if(mode==0){
            double d[NC]={0};kin_tail(v,f);accumulate(f,cent,scale,d,0,NF);
            p=predict(d,&ignored);expand=1;groups[i]=255;
        }else{
            int g=kin_group(f,coarse,scale);double d[3]={0};
            kin_acc(f,cent,scale,d,g,0,KC);p=kin_pred(d,g,&margin);groups[i]=(uint8_t)g;
            int wants=mode==4?margin<th:mode==5?benefit[g*KB+kin_bin(margin)]>th:0;
            expand=mode==1||(mode==3&&quota>i*(size_t)q/4)||
                   ((mode==4||mode==5)&&count<quota&&(wants||k-count==n-i));
            if(expand){kin_tail(v,f);kin_acc(f,cent,scale,d,g,KC,NF);p=kin_pred(d,g,&ignored);}
        }
        count+=(size_t)expand;pred[i]=(uint8_t)p;mask[i]=(uint8_t)expand;margins[i]=margin;
        r.correct+=p==y[i];r.expanded+=expand;r.features+=12+18*(uint64_t)expand;
        size_t bound=mode<=1?i+1:mode==2?0:quota;
        if(count>bound&&count-bound>r.over)r.over=count-bound;
    }
    r.cpu_ns=stamp(CLOCK_PROCESS_CPUTIME_ID)-cpu;r.wall_ns=stamp(CLOCK_MONOTONIC)-wall;*out=r;return 0;
}
