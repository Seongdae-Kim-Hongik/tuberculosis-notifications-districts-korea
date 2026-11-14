# 52T — TBNW 보조 결과: 호흡기 결핵 사망(TBD, A15-A16, 성×연령 간접표준화 TBD_Estd3r 2011-2024)을 같은 주모형 사양(강제 5 + 가설 S1 7, NB, BYM2 593 + RW1 + 연도 iid)으로 2013-2024에 적합.
#  비교용으로 TBNW도 2013-2024 같은 사양으로 다시 적합. 공변량 z는 panel_TBNW_<VER>.csv 값 그대로.  산출: 04_분석/TBNW/results_<VER>/S52T_tbd_aux.csv
#  주의: inla()의 E= 인자는 데이터 환경에서 평가된다 → 오프셋은 데이터 열(offE) 이름으로 넘긴다(11/14 첫 실행 버그: E=d[[E]]가 패널 E 열로 해석됨).
suppressPackageStartupMessages({library(INLA);library(jsonlite);library(sf)})
inla.setOption(num.threads="1:1")
VER<-Sys.getenv("ST_VER","std3");D<-file.path("..","04_분석","TBNW");OUT<-file.path(D,paste0("results_",VER))
S<-fromJSON(file.path(D,paste0("config_TBNW_",VER,".json")))
DD<-read.csv(file.path(D,paste0("panel_TBNW_",VER,".csv")),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE);DD$fbd_region<-enc2utf8(DD$fbd_region)
TB<-read.csv(file.path("..","02_패널","TBD_Estd3r.csv"),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE);TB$fbd_region<-enc2utf8(TB$fbd_region)
TB<-TB[TB$year>=2013&TB$year<=2024,c("year","fbd_region","cases","E_std")];names(TB)[3:4]<-c("tbd_cases","tbd_E")
DD<-DD[DD$year<=2024,];n0<-nrow(DD);DD<-merge(DD,TB,by=c("year","fbd_region"));stopifnot(nrow(DD)==n0,nrow(DD)==229*12)
g<-inla.read.graph(file.path(D,"graph_593.graph"))
G<-st_read(paste0(Sys.getenv("ST_DATA_ROOT"), "/기타/R_Studio/FBD_DATA_ZIP/final.shp",quiet=TRUE);G$region<-enc2utf8(G$region)
DD<-DD[order(DD$year,match(DD$fbd_region,G$region)),];DD$area<-match(DD$fbd_region,G$region);DD$time<-DD$year-min(DD$year)+1;DD$yiid<-DD$time
HYP<-S$sets_after_vif$S1_narrative_full;COV<-unique(c(S$forced,HYP))
pc<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)),phi=list(prior="pc",param=c(0.5,2/3)));pcp<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)))
rhs<-paste(paste(sprintf("`%s`",COV),collapse="+"),"+ f(area,model='bym2',graph=g,scale.model=TRUE,constr=TRUE,hyper=pc) + f(time,model='rw1',scale.model=TRUE,hyper=pcp) + f(yiid,model='iid',hyper=pcp)")
fit<-function(y,ecol,lab){d<-DD;d$y<-d[[y]];d$offE<-d[[ecol]];m<-inla(as.formula(paste("y ~ 1 +",rhs)),family="nbinomial",data=d,E=offE,control.fixed=list(mean=0,prec=4,mean.intercept=0,prec.intercept=0.001),
  control.compute=list(waic=TRUE),control.inla=list(control.vb=list(emergency=50)))
  fx<-m$summary.fixed[COV,];data.frame(outcome=lab,variable=COV,role=ifelse(COV%in%HYP,"hypothesis","forced"),IRR=exp(fx$mean),lo=exp(fx$`0.025quant`),hi=exp(fx$`0.975quant`),
   credible=(fx$`0.025quant`>0|fx$`0.975quant`<0),WAIC=round(m$waic$waic,1),phi=m$summary.hyperpar[grep("Phi",rownames(m$summary.hyperpar)),"mean"],n=nrow(d),cases=sum(d$y),years="2013-2024")}
R<-rbind(fit("tbd_cases","tbd_E","TBD (respiratory TB deaths)"),fit("cases","E","TBNW (new notifications), 2013-2024"))
write.csv(R,file.path(OUT,"S52T_tbd_aux.csv"),row.names=FALSE);print(R[R$role=="hypothesis",c("outcome","variable","IRR","lo","hi","credible")])
