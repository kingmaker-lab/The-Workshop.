/* SOLARIS Linux/x86_64 research core. No artificial pressure. */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <glob.h>
#include <sched.h>
#include <sys/resource.h>
#include "../exp004-ascension/ascension.c"
#define MAX_N 256
#define MAX_SENSORS 128
typedef struct {
    uint64_t correct,terms,forced,over,observer_cpu_ns,cpu_ns,wall_ns;
    int64_t available_kib,temp_milli;
    double busy,mem_psi,cpu_psi,freq_khz,policy_age;
    int budget,refreshed,ticks;
} SolarResult;
typedef struct {
    char *paths[MAX_SENSORS]; size_t count;
    cpu_set_t affinity;
    uint64_t total,idle;
    double last,interval,busy,mp,cp,freq,diag;
    int budget,up,previous_budget,ticks,err,steps;
    double thresholds[4];
    double x[MAX_N*32]; uint8_t y[MAX_N];
} Solar;
static uint64_t ns(clockid_t clock){
    struct timespec t; if(clock_gettime(clock,&t))return 0;
    return (uint64_t)t.tv_sec*1000000000u+(uint64_t)t.tv_nsec;
}
static double monotonic(void){return ns(CLOCK_MONOTONIC)/1e9;}
static int read_word(const char *path,char *word){
    FILE *f=fopen(path,"r"); if(!f)return 0;
    int ok=fscanf(f,"%127s",word)==1; fclose(f);return ok;
}
static void add_paths(Solar *s,const char *pattern){
    glob_t g={0};
    if(glob(pattern,0,NULL,&g)==0){
        for(size_t i=0;i<g.gl_pathc&&s->count<MAX_SENSORS;i++){
            char *p=strdup(g.gl_pathv[i]);if(p)s->paths[s->count++]=p;
        }
    }
    globfree(&g);
}
static void discover(Solar *s){
    glob_t g={0};char p[4096],name[128];
    if(glob("/sys/class/hwmon/hwmon*",0,NULL,&g)==0){
        for(size_t i=0;i<g.gl_pathc;i++){
            if(snprintf(p,sizeof p,"%s/name",g.gl_pathv[i])>=(int)sizeof p)continue;
            if(!read_word(p,name))continue;
            if(strcmp(name,"coretemp")&&strcmp(name,"k10temp")&&strcmp(name,"zenpower"))continue;
            if(snprintf(p,sizeof p,"%s/temp*_input",g.gl_pathv[i])<(int)sizeof p)add_paths(s,p);
        }
    }
    globfree(&g);memset(&g,0,sizeof g);
    if(glob("/sys/class/thermal/thermal_zone*",0,NULL,&g)==0){
        for(size_t i=0;i<g.gl_pathc;i++){
            if(snprintf(p,sizeof p,"%s/type",g.gl_pathv[i])>=(int)sizeof p)continue;
            if(!read_word(p,name))continue;
            if(strcmp(name,"x86_pkg_temp")&&strcmp(name,"cpu-thermal")&&strcmp(name,"cpu_thermal"))continue;
            if(snprintf(p,sizeof p,"%s/temp",g.gl_pathv[i])<(int)sizeof p)add_paths(s,p);
        }
    }
    globfree(&g);
}
static int safety(Solar *s,int64_t *avail,int64_t *total,int64_t *temp){
    char line[256];long long v;*avail=*total=*temp=-1;
    FILE *f=fopen("/proc/meminfo","r");if(!f)return -1;
    while(fgets(line,sizeof line,f)){
        if(sscanf(line,"MemAvailable: %lld",&v)==1)*avail=v;
        if(sscanf(line,"MemTotal: %lld",&v)==1)*total=v;
    }
    fclose(f);
    if(*avail<512*1024||*total<=0)return -2;
    for(size_t i=0;i<s->count;i++){
        f=fopen(s->paths[i],"r");if(!f)return -3;
        int ok=fscanf(f,"%lld",&v)==1;fclose(f);
        if(!ok||v<=0||v>=150000)return -3;
        if(v>*temp)*temp=v;
    }
    if(*temp>=80000)return -4;
    return 0;
}
static int cpu_ticks(Solar *s,uint64_t *total,uint64_t *idle){
    char line[512];FILE *f=fopen("/proc/stat","r");if(!f)return -1;
    *total=*idle=0;int found=0;
    while(fgets(line,sizeof line,f)){
        int cpu;unsigned long long a,b,c,d,e,g,h,i;
        if(sscanf(line,"cpu%d %llu %llu %llu %llu %llu %llu %llu %llu",&cpu,&a,&b,&c,&d,&e,&g,&h,&i)!=9)continue;
        if(cpu<0||cpu>=CPU_SETSIZE||!CPU_ISSET(cpu,&s->affinity))continue;
        *total+=a+b+c+d+e+g+h+i;*idle+=d+e;found++;
    }
    fclose(f);return found?0:-1;
}
static double psi(const char *path){
    char line[256];double v=-1;FILE *f=fopen(path,"r");
    if(f){if(fgets(line,sizeof line,f)&&sscanf(line,"some avg10=%lf",&v)!=1)v=-1;fclose(f);}
    return v;
}
static double frequency(Solar *s){
    char p[256];double sum=0;int n=0;
    for(int cpu=0;cpu<CPU_SETSIZE;cpu++)if(CPU_ISSET(cpu,&s->affinity)){
        snprintf(p,sizeof p,"/sys/devices/system/cpu/cpu%d/cpufreq/scaling_cur_freq",cpu);
        FILE *f=fopen(p,"r");double v;if(f){if(fscanf(f,"%lf",&v)==1){sum+=v;n++;}fclose(f);}
    }
    return n?sum/n:-1;
}
void solar_free(Solar *s){if(s){for(size_t i=0;i<s->count;i++)free(s->paths[i]);free(s);}}
Solar *solar_new(const double *thresholds){
    if(!thresholds)return NULL;
    Solar *s=calloc(1,sizeof *s);if(!s)return NULL;
    for(int i=0;i<4;i++){if(!isfinite(thresholds[i])||thresholds[i]<0||thresholds[i]>12){solar_free(s);return NULL;}s->thresholds[i]=thresholds[i];}
    s->budget=8;s->interval=.15;s->last=s->diag=-1;s->busy=s->mp=s->cp=s->freq=-1;
    if(sched_getaffinity(0,sizeof s->affinity,&s->affinity)){solar_free(s);return NULL;}
    discover(s);
    int64_t a,t,h;
    if(safety(s,&a,&t,&h)||cpu_ticks(s,&s->total,&s->idle)){solar_free(s);return NULL;}
    return s;
}
int solar_target(double busy,int64_t avail,int64_t total,double mp){
    if(!isfinite(busy)||busy<0||total<=0||avail<0)return 8;
    int mem=(avail<256*1024||(double)avail/total<.10||mp>=5)?8:((double)avail/total<.20?16:32);
    int cpu=busy>=.75?8:busy>=.45?16:busy>=.25?24:32;
    return mem<cpu?mem:cpu;
}
static int observe_native(Solar *s,SolarResult *r,int adaptive){
    int64_t total;
    int status=safety(s,&r->available_kib,&total,&r->temp_milli);
    if(status)return status;
    double now=monotonic();
    if(adaptive&&(s->last<0||now-s->last>=s->interval)){
        uint64_t t,i;double old=s->busy;s->busy=-1;
        if(cpu_ticks(s,&t,&i)==0){
            if(t>s->total&&i>=s->idle&&i-s->idle<=t-s->total)s->busy=1.-(double)(i-s->idle)/(t-s->total);
            s->total=t;s->idle=i;
        }
        s->interval=(old>=0&&s->busy>=0&&fabs(old-s->busy)<.1)?.5:.15;
        s->mp=psi("/proc/pressure/memory");s->last=now;r->refreshed=1;
    }
    if(adaptive&&(s->diag<0||now-s->diag>=1.)){
        s->cp=psi("/proc/pressure/cpu");s->freq=frequency(s);s->diag=now;
    }
    if(adaptive){
        int target=solar_target(s->busy,r->available_kib,total,s->mp);
        if(target<s->budget){s->budget=target;s->up=0;}
        else if(target==s->budget)s->up=0;
        else if(r->refreshed&&++s->up>=2){s->budget+=8;if(s->budget>target)s->budget=target;s->up=0;}
    }
    r->busy=s->busy;r->mem_psi=s->mp;r->cpu_psi=s->cp;r->freq_khz=s->freq;
    r->policy_age=s->last<0?-1:now-s->last;
    return 0;
}
/* modes 0=full, 1=fixed16, 2=adaptive reset, 3=adaptive persistent */
int solar_step(Solar *s,const void *data,size_t bytes,size_t n,int mode,SolarResult *out){
    if(!s||!data||!out||!n||n>MAX_N||bytes!=n*(32*sizeof(double)+1)||mode<0||mode>3)return -10;
    uint64_t w=ns(CLOCK_MONOTONIC),c=ns(CLOCK_PROCESS_CPUTIME_ID);
    SolarResult r={0};int status=observe_native(s,&r,mode>=2);
    if(status)return status;
    r.observer_cpu_ns=ns(CLOCK_PROCESS_CPUTIME_ID)-c;
    memcpy(s->x,data,n*32*sizeof(double));memcpy(s->y,(const unsigned char *)data+n*32*sizeof(double),n);
    for(size_t i=0;i<n*32;i++)if(!isfinite(s->x[i]))return -11;
    for(size_t i=0;i<n;i++)if(s->y[i]>1)return -11;
    int b=mode==0?32:mode==1?16:s->budget;r.budget=b;
    Result a={0};
    if(mode!=3){
        if(asc_run(s->x,s->y,n,b,s->thresholds[b/8-1],mode==0?0:5,&a))return -12;
    }else{
        if(s->previous_budget!=b){s->ticks=(int)llround(s->thresholds[b/8-1]*700);s->err=0;s->steps=0;s->previous_budget=b;}
        int credit=0; /* credit resets each batch: stronger local prefix guarantee */
        for(size_t i=0;i<n;i++){
            const double *v=s->x+i*32;double score=0,tail=0;
            for(int j=0;j<4;j++)score+=v[j];
            credit+=b-4;int wants=b==32||fabs(score)*700<s->ticks;
            int expand=wants&&credit>=28;
            if(expand){credit-=28;for(int j=4;j<32;j++)tail+=v[j]*.15;score+=tail;}
            else if(wants)a.forced++;
            int cost=expand?32:4;a.terms+=cost;a.correct+=(score>=0)==s->y[i];
            if(b!=32){s->err+=3*(b-cost);if(++s->steps==16){s->ticks+=s->err;if(s->ticks<0)s->ticks=0;if(s->ticks>8400)s->ticks=8400;s->steps=0;s->err=0;}}
            if(a.terms>(i+1)*(uint64_t)b){uint64_t over=a.terms-(i+1)*(uint64_t)b;if(over>a.over)a.over=over;}
        }
    }
    r.correct=a.correct;r.terms=a.terms;r.forced=a.forced;r.over=a.over;r.ticks=s->ticks;
    r.cpu_ns=ns(CLOCK_PROCESS_CPUTIME_ID)-c;r.wall_ns=ns(CLOCK_MONOTONIC)-w;*out=r;return 0;
}
#ifdef SOLARIS_CLI
/* Offline local binary stream: 4 native doubles then fixed-size batches.
   Usage: solaris_cli batch_size input.bin; one CSV line per batch. */
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
        size_t got=fread(data,1,bytes,f);
        if(!got){if(ferror(f))rc=4;break;}
        if(got!=bytes){rc=4;break;}
        SolarResult r;int status=solar_step(s,data,bytes,(size_t)n,3,&r);
        if(status){fprintf(stderr,"SOLARIS stop %d\n",status);rc=3;break;}
        printf("%llu,%llu,%d,%llu,%llu,%llu,%llu,%lld,%lld\n",(unsigned long long)r.correct,(unsigned long long)r.terms,r.budget,(unsigned long long)r.over,(unsigned long long)r.cpu_ns,(unsigned long long)r.wall_ns,(unsigned long long)r.observer_cpu_ns,(long long)r.available_kib,(long long)r.temp_milli);
        struct timespec wait={0,100000000};nanosleep(&wait,NULL);
    }
    solar_free(s);fclose(f);return rc;
}
#endif
