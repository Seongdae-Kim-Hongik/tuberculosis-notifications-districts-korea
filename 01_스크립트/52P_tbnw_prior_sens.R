# 52P — TBNW 사전분포 민감도(2026-11-13). 주모형 사양(강제통제 5 + 가설 S1 7, NB, BYM2 593 + RW1 + 연도 iid, offset E 성×8연령)을 사전분포만 바꿔 다시 적합.
#  P0 기준: 고정효과 N(0, prec 4) · BYM2 PC prec(0.5,0.01) phi PC(0.5,2/3) · RW1/iid PC prec(0.5,0.01)
#  P1 고정효과 약한 사전 N(0, prec 0.01) / P2 고정효과 강한 수축 N(0, prec 25) / P3 BYM2 PC prec(1,0.01)·phi PC(0.5,0.5) / P4 시간 PC prec(1,0.01) / P5 BYM2 phi PC(0.5,0.9)(구조 쪽 사전)
#  산출: 04_분석/LEPT/results_<VER>/S52P_prior_sensitivity.csv (사양별 가설 변수 IRR·95% CrI·WAIC·phi)
suppressPackageStartupMessages({library(INLA);library(jsonlite);library(sf)})
inla.setOption(num.threads="1:1")
VER<-Sys.getenv("ST_VER","std3");D<-file.path("..","04_분석","TBNW");OUT<-file.path(D,paste0("results_",VER))
S<-fromJSON(file.path(D,paste0("config_TBNW_",VER,".json")))
DD<-read.csv(file.path(D,paste0("panel_TBNW_",VER,".csv")),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE)
g<-inla.read.graph(file.path(D,"graph_593.graph"))
SHP<-Sys.getenv("ST_SHP",file.path(normalizePath(file.path(dirname(sub("--file=","",grep("--file=",commandArgs(),value=TRUE))),"..")),"data","boundary","final.shp"))
G<-st_read(SHP,quiet=TRUE);G$region<-enc2utf8(G$region);DD$fbd_region<-enc2utf8(DD$fbd_region)
DD$area<-match(DD$fbd_region,G$region);DD$time<-DD$year-min(DD$year)+1;DD$yiid<-DD$time
HYP<-S$sets_after_vif$S1_narrative_full;COV<-unique(c(S$forced,HYP))
FAM<-if(file.exists(file.path(D,paste0("HM_best_TBNW_",VER,".txt")))&&grepl("poisson",readLines(file.path(D,paste0("HM_best_TBNW_",VER,".txt")))[1],ignore.case=TRUE)) "poisson" else "nbinomial"
spec<-list(P0_reference=list(fp=4,bp=c(0.5,0.01),ph=c(0.5,2/3),tp=c(0.5,0.01)),P1_vague_fixed=list(fp=0.01,bp=c(0.5,0.01),ph=c(0.5,2/3),tp=c(0.5,0.01)),
  P2_shrink_fixed=list(fp=25,bp=c(0.5,0.01),ph=c(0.5,2/3),tp=c(0.5,0.01)),P3_wider_spatial=list(fp=4,bp=c(1,0.01),ph=c(0.5,0.5),tp=c(0.5,0.01)),
  P4_wider_time=list(fp=4,bp=c(0.5,0.01),ph=c(0.5,2/3),tp=c(1,0.01)),P5_structured_phi=list(fp=4,bp=c(0.5,0.01),ph=c(0.5,0.9),tp=c(0.5,0.01)))
R<-list()
for(nm in names(spec)){s<-spec[[nm]];pc<-list(prec=list(prior="pc.prec",param=s$bp),phi=list(prior="pc",param=s$ph));pcp<-list(prec=list(prior="pc.prec",param=s$tp))
  f<-as.formula(paste("cases ~ 1 +",paste(sprintf("`%s`",COV),collapse="+"),"+ f(area,model='bym2',graph=g,scale.model=TRUE,constr=TRUE,hyper=pc) + f(time,model='rw1',scale.model=TRUE,hyper=pcp) + f(yiid,model='iid',hyper=pcp)"))
  m<-inla(f,family=FAM,data=DD,E=DD$E,control.fixed=list(mean=0,prec=s$fp,mean.intercept=0,prec.intercept=0.001),control.compute=list(waic=TRUE,dic=TRUE),control.inla=list(control.vb=list(emergency=50)))
  fx<-m$summary.fixed[HYP,];hp<-m$summary.hyperpar
  R[[nm]]<-data.frame(spec=nm,family=FAM,variable=HYP,IRR=exp(fx$mean),lo=exp(fx$`0.025quant`),hi=exp(fx$`0.975quant`),credible=(fx$`0.025quant`>0|fx$`0.975quant`<0),
    WAIC=round(m$waic$waic,1),phi=round(hp[grep("Phi",rownames(hp)),"mean"],3));print(R[[nm]])}
write.csv(do.call(rbind,R),file.path(OUT,"S52P_prior_sensitivity.csv"),row.names=FALSE)
