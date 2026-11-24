/* ICARO: research-only bounded batch selector; original SOLARIS unchanged. */
#include "../exp006-solaris/solaris.c"
typedef struct {double margin;size_t index;} Choice;
static int worse(Choice a,Choice b){
    double x=fabs(a.margin),y=fabs(b.margin);
    return x>y||(x==y&&a.index>b.index);
}
static void push(Choice *heap,size_t *len,Choice c){
    size_t i=(*len)++;heap[i]=c;
    while(i){size_t p=(i-1)/2;if(!worse(heap[i],heap[p]))break;
        Choice t=heap[i];heap[i]=heap[p];heap[p]=t;i=p;}
}
static void pop(Choice *heap,size_t *len){
    if(!*len)return;
    heap[0]=heap[--(*len)];
    size_t i=0;
    while(2*i+1<*len){
        size_t j=2*i+1;
        if(j+1<*len&&worse(heap[j+1],heap[j]))j++;
        if(!worse(heap[j],heap[i]))break;
        Choice t=heap[i];heap[i]=heap[j];heap[j]=t;i=j;
    }
}
static int valid_budget(int b){return b==8||b==16||b==24||b==32;}
/* cap=-1: maximize feasible expansions. Otherwise match an observed count.
   Select globally low absolute margins subject to every logical prefix quota.
   The heap removes worst selected member when a nested prefix cap is exceeded. */
static int rank_batch(const double *x,const uint8_t *y,size_t n,int b,int cap,Result *out){
    if(!x||!y||!out||!n||n>MAX_N||!valid_budget(b)||cap< -1||cap>(int)(n*(b-4)/28))return -10;
    Choice heap[MAX_N];double margins[MAX_N];unsigned char chosen[MAX_N]={0};size_t len=0;
    for(size_t i=0;i<n;i++){
        double m=0;for(int j=0;j<4;j++)m+=x[32*i+j];margins[i]=m;
        if(!isfinite(m))return -11;
        size_t quota=(i+1)*(b-4)/28;
        if(cap>=0&&quota>(size_t)cap)quota=(size_t)cap;
        push(heap,&len,(Choice){m,i});
        if(len>quota)pop(heap,&len);
    }
    for(size_t i=0;i<len;i++)chosen[heap[i].index]=1;
    Result r={0};
    for(size_t i=0;i<n;i++){
        double score=margins[i];
        if(chosen[i]){double tail=0;for(int j=4;j<32;j++)tail+=x[32*i+j]*.15;score+=tail;}
        r.correct+=(score>=0)==y[i];r.terms+=chosen[i]?32:4;
        uint64_t limit=(i+1)*(uint64_t)b;if(r.terms>limit&&r.terms-limit>r.over)r.over=r.terms-limit;
    }
    *out=r;return 0;
}
static int read_batch(Solar *s,const void *data,size_t bytes,size_t n){
    if(!s||!data||!n||n>MAX_N||bytes!=n*(32*sizeof(double)+1))return -10;
    memcpy(s->x,data,n*32*sizeof(double));memcpy(s->y,(const unsigned char*)data+n*32*sizeof(double),n);
    for(size_t i=0;i<n*32;i++)if(!isfinite(s->x[i])||fabs(s->x[i])>1e6)return -11;
    for(size_t i=0;i<n;i++)if(s->y[i]>1)return -11;
    return 0;
}
/* Native live candidate. Safety/policy identical to SOLARIS. No integral threshold. */
int icaro_step(Solar *s,const void *data,size_t bytes,size_t n,SolarResult *out){
    if(!s||!out)return -10;
    uint64_t w=ns(CLOCK_MONOTONIC),c=ns(CLOCK_PROCESS_CPUTIME_ID);
    SolarResult r={0};int status=observe_native(s,&r,1);
    if(status)return status;
    r.observer_cpu_ns=ns(CLOCK_PROCESS_CPUTIME_ID)-c;
    if((status=read_batch(s,data,bytes,n)))return status;
    r.budget=s->budget;
    Result a={0};if((status=rank_batch(s->x,s->y,n,r.budget,-1,&a)))return status;
    r.correct=a.correct;r.terms=a.terms;r.over=a.over;
    r.cpu_ns=ns(CLOCK_PROCESS_CPUTIME_ID)-c;r.wall_ns=ns(CLOCK_MONOTONIC)-w;
    *out=r;return 0;
}
/* Offline replay state, bounded input, no hardware reads. Caller checks safety.
   Modes: 0 original reset, 1 original persistent, 2 rank at identical budget,
   3 rank capped to exact expansion count achieved by baseline. */
Solar *icaro_replay_new(const double *th){
    if(!th)return NULL;
    Solar *s=calloc(1,sizeof *s);if(!s)return NULL;
    for(int i=0;i<4;i++){if(!isfinite(th[i])||th[i]<0||th[i]>12){solar_free(s);return NULL;}s->thresholds[i]=th[i];}
    return s;
}
int icaro_replay(Solar *s,const void *data,size_t bytes,size_t n,int b,int mode,int cap,Result *out){
    if(!out||!valid_budget(b)||mode<0||mode>3)return -10;
    int status=read_batch(s,data,bytes,n);if(status)return status;
    if(mode==0)return asc_run(s->x,s->y,n,b,s->thresholds[b/8-1],5,out);
    if(mode>=2)return rank_batch(s->x,s->y,n,b,mode==3?cap:-1,out);
    if(s->previous_budget!=b){s->ticks=(int)llround(s->thresholds[b/8-1]*700);s->err=0;s->steps=0;s->previous_budget=b;}
    int credit=0;Result r={0};
    for(size_t i=0;i<n;i++){
        const double *v=s->x+32*i;double score=0,tail=0;
        for(int j=0;j<4;j++)score+=v[j];
        credit+=b-4;int wants=b==32||fabs(score)*700<s->ticks;int expand=wants&&credit>=28;
        if(expand){credit-=28;for(int j=4;j<32;j++)tail+=v[j]*.15;score+=tail;}
        else if(wants)r.forced++;
        int cost=expand?32:4;r.terms+=cost;r.correct+=(score>=0)==s->y[i];
        if(b!=32){s->err+=3*(b-cost);if(++s->steps==16){s->ticks+=s->err;if(s->ticks<0)s->ticks=0;if(s->ticks>8400)s->ticks=8400;s->steps=0;s->err=0;}}
        if(r.terms>(i+1)*(uint64_t)b){uint64_t over=r.terms-(i+1)*(uint64_t)b;if(over>r.over)r.over=over;}
    }
    *out=r;return 0;
}
#ifdef ICARO_CLI
/* Local trusted fixture, same format as SOLARIS. */
int main(int argc,char **argv){
    if(argc!=3)return 2;
    char *end=NULL;long n=strtol(argv[1],&end,10);
    if(!end||*end||n<1||n>MAX_N)return 2;
    FILE *f=fopen(argv[2],"rb");if(!f)return 2;
    double th[4];if(fread(th,sizeof(double),4,f)!=4){fclose(f);return 2;}
    Solar *s=solar_new(th);if(!s){fclose(f);return 3;}
    unsigned char data[MAX_N*257];size_t bytes=(size_t)n*257;int rc=0;
    puts("correct,terms,budget,over,cpu_ns,wall_ns,observer_cpu_ns,available_kib,temp_milli");
    for(;;){
        size_t got=fread(data,1,bytes,f);if(!got){if(ferror(f))rc=4;break;}if(got!=bytes){rc=4;break;}
        SolarResult r;int status=icaro_step(s,data,bytes,(size_t)n,&r);
        if(status){fprintf(stderr,"ICARO stop %d\n",status);rc=3;break;}
        printf("%llu,%llu,%d,%llu,%llu,%llu,%llu,%lld,%lld\n",(unsigned long long)r.correct,(unsigned long long)r.terms,r.budget,(unsigned long long)r.over,(unsigned long long)r.cpu_ns,(unsigned long long)r.wall_ns,(unsigned long long)r.observer_cpu_ns,(long long)r.available_kib,(long long)r.temp_milli);
        struct timespec wait={0,100000000};nanosleep(&wait,NULL);
    }
    solar_free(s);fclose(f);return rc;
}
#endif
