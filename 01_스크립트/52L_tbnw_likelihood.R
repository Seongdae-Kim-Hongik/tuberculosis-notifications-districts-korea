# 52L — TBNW 우도 5종 비교(2026-11-13). 47K_sknd_likelihood.R 복제·확장: 주모형 사양(강제통제 5 + 가설 S1 7) + BYM2(593) + RW1 + 연도 iid, offset = E(성×8연령).
#  Poisson · NB · ZIP(type 1) · ZINB(type 1) · Poisson+관측 iid 5종: WAIC·DIC·−Σlog CPO, 사후 평균으로 기대 0칸 수(관측 대조), 가설 변수 IRR(우도별).
#  사용(01_스크립트/에서): Rscript 52L_lept_likelihood.R [ST_VER=std3]   산출: 04_분석/LEPT/results_<VER>/S52L_likelihood.csv, S52L_likelihood_IRR.csv
suppressPackageStartupMessages({library(INLA);library(jsonlite);library(sf)})
inla.setOption(num.threads="1:1")
VER<-Sys.getenv("ST_VER","std3");D<-file.path("..","04_분석","TBNW");OUT<-file.path(D,paste0("results_",VER));dir.create(OUT,showWarnings=FALSE)
S<-fromJSON(file.path(D,paste0("config_TBNW_",VER,".json")))
DD<-read.csv(file.path(D,paste0("panel_TBNW_",VER,".csv")),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE)
g<-inla.read.graph(file.path(D,"graph_593.graph"))
SHP<-Sys.getenv("ST_SHP",file.path(normalizePath(file.path(dirname(sub("--file=","",grep("--file=",commandArgs(),value=TRUE))),"..")),"data","boundary","final.shp"))
G<-st_read(SHP,quiet=TRUE);G$region<-enc2utf8(G$region);DD$fbd_region<-enc2utf8(DD$fbd_region);stopifnot(g$n==nrow(G),all(DD$fbd_region%in%G$region))
DD$area<-match(DD$fbd_region,G$region);DD$time<-DD$year-min(DD$year)+1;DD$yiid<-DD$time;DD$obs<-seq_len(nrow(DD))
HYP<-S$sets_after_vif$S1_narrative_full;COV<-unique(c(S$forced,HYP))
pc<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)),phi=list(prior="pc",param=c(0.5,2/3)));pcp<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)))
base<-paste("cases ~ 1 +",paste(sprintf("`%s`",COV),collapse="+"),
  "+ f(area,model='bym2',graph=g,scale.model=TRUE,constr=TRUE,hyper=pc) + f(time,model='rw1',scale.model=TRUE,hyper=pcp) + f(yiid,model='iid',hyper=pcp)")
IRR<-list()
fit<-function(fam,extra=""){f<-as.formula(paste(base,extra));t0<-Sys.time();lab<-paste0(fam,ifelse(extra=="","","+obs_iid"))
  m<-inla(f,family=fam,data=DD,E=DD$E,control.fixed=list(mean=0,prec=4,mean.intercept=0,prec.intercept=0.001),
    control.compute=list(waic=TRUE,dic=TRUE,cpo=TRUE,config=FALSE),control.predictor=list(compute=TRUE,link=1),
    control.inla=list(control.vb=list(emergency=50)))
  mu<-m$summary.fitted.values$mean*DD$E;hp<-m$summary.hyperpar
  p0<-switch(fam,poisson=exp(-mu),
    nbinomial={k<-hp[grep("size",rownames(hp)),"mean"];(k/(k+mu))^k},
    zeroinflatedpoisson1={p<-hp[grep("zero-probability",rownames(hp)),"mean"];p+(1-p)*exp(-mu/(1-p))},
    zeroinflatednbinomial1={k<-hp[grep("size",rownames(hp)),"mean"];p<-hp[grep("zero-probability",rownames(hp)),"mean"];m1<-mu/(1-p);p+(1-p)*(k/(k+m1))^k})
  fx<-m$summary.fixed[COV,];IRR[[lab]]<<-data.frame(likelihood=lab,variable=COV,IRR=exp(fx$mean),lo=exp(fx$`0.025quant`),hi=exp(fx$`0.975quant`),credible=(fx$`0.025quant`>0|fx$`0.975quant`<0))
  cpo<-m$cpo$cpo;nf<-sum(m$cpo$failure>0,na.rm=TRUE)
  data.frame(likelihood=lab,WAIC=round(m$waic$waic,1),DIC=round(m$dic$dic,1),neg_logscore=round(-sum(log(cpo),na.rm=TRUE),1),cpo_fail=nf,
    zero_prob=ifelse(grepl("zeroinflated",fam),round(hp[grep("zero-probability",rownames(hp)),"mean"],4),NA),
    size=ifelse(grepl("nbinomial",fam),round(hp[grep("size",rownames(hp)),"mean"],2),NA),
    expected_zeros=round(sum(p0),1),observed_zeros=sum(DD$cases==0),minutes=round(as.numeric(difftime(Sys.time(),t0,units="mins")),2))}
R<-rbind(fit("poisson"),fit("nbinomial"),fit("zeroinflatedpoisson1"),fit("zeroinflatednbinomial1"),fit("poisson","+ f(obs,model='iid',hyper=pcp)"))
R$expected_zeros[R$likelihood=="poisson+obs_iid"]<-NA
write.csv(R,file.path(OUT,"S52L_likelihood.csv"),row.names=FALSE);print(R)
I<-do.call(rbind,IRR);write.csv(I,file.path(OUT,"S52L_likelihood_IRR.csv"),row.names=FALSE);print(I[I$variable%in%HYP,])
