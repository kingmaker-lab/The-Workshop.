/* LEVER: matched resident aggregation; unchanged original heap. */
#include "../ath003-archimedes/arch.c"
/* 0 full, 1 lite, 2 static, 3 rank, 4 causal, 5 rank with full fast path.
   Diagnostic mode 6 margin-only and 7 margin+heap, no tail or labels. */
int lever_run(const double *x,const uint8_t *y,size_t n,int b,int w,int mode,
              double threshold,ArchResult *out,uint8_t *mask){
    if(!x||!y||!out||!mask||!n||n>MAX_N||!valid_budget(b)||w<1||w>64||
       mode<0||mode>7||!isfinite(threshold)||threshold<0)return -1;
    size_t stride=4+28*(size_t)w,k=n*(b-4)/28,len=0,count=0;
    double margins[MAX_N];Choice heap[MAX_N];uint8_t chosen[MAX_N]={0};
    ArchResult r={0};
    uint64_t wall=ns(CLOCK_MONOTONIC),cpu=ns(CLOCK_PROCESS_CPUTIME_ID);
    double scale=1./sqrt((double)w);
    /* Causal arm processes each sample immediately, no future margins. */
    if(mode==4){
        for(size_t i=0;i<n;i++){
            double score=0.;for(int j=0;j<4;j++)score+=x[i*stride+j];
            size_t q=(i+1)*(b-4)/28;
            if(count<q&&(fabs(score)<threshold||k-count==n-i)){
                chosen[i]=1;count++;score+=arch_tail(x+i*stride,w,scale);
            }
            r.correct+=(score>=0)==y[i];r.checksum+=score;
            r.expanded+=chosen[i];r.terms+=chosen[i]?32:4;
            r.raw_reads+=4+(chosen[i]?28*(uint64_t)w:0);
            uint64_t bound=(i+1)*(uint64_t)b;
            if(r.terms>bound&&r.terms-bound>r.over)r.over=r.terms-bound;
        }
    }else{
        for(size_t i=0;i<n;i++){
            double score=0.;for(int j=0;j<4;j++)score+=x[i*stride+j];margins[i]=score;
        }
        if(mode==0||(mode==5&&b==32)){for(size_t i=0;i<n;i++)chosen[i]=1;}
        else if(mode==2){for(size_t i=0;i<n;i++)chosen[i]=((i+1)*(b-4)/28>i*(b-4)/28);}
        else if(mode==3||mode==5||mode==7){
            for(size_t i=0;i<n;i++){
                size_t q=(i+1)*(b-4)/28;
                push(heap,&len,(Choice){margins[i],i});if(len>q)pop(heap,&len);
            }
            for(size_t i=0;i<len;i++)chosen[heap[i].index]=1;
        }
        for(size_t i=0;i<n;i++){
            double score=margins[i];
            if(chosen[i]&&mode<6)score+=arch_tail(x+i*stride,w,scale);
            if(mode<6)r.correct+=(score>=0)==y[i];
            r.checksum+=score;r.expanded+=chosen[i];
            r.terms+=4+(mode<6&&chosen[i]?28:0);
            r.raw_reads+=4+(mode<6&&chosen[i]?28*(uint64_t)w:0);
            uint64_t bound=(i+1)*(uint64_t)(mode==0?32:mode==1||mode>=6?4:b);
            if(r.terms>bound&&r.terms-bound>r.over)r.over=r.terms-bound;
        }
    }
    memcpy(mask,chosen,n);
    r.cpu_ns=ns(CLOCK_PROCESS_CPUTIME_ID)-cpu;r.wall_ns=ns(CLOCK_MONOTONIC)-wall;
    *out=r;return 0;
}
