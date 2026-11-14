# 52S — TBNW 민감도: 독거노인 가구 비율의 2013–2014 값이 2010 센서스–2015 사이 보간이므로 2015–2025만 같은 주모형 사양으로 적합(11/14 review 지적 반영). 공변량 z = panel 값 그대로.
#  산출: 04_분석/TBNW/results_<VER>/S52S_from2015.csv
suppressPackageStartupMessages({library(INLA);library(jsonlite);library(sf)})
inla.setOption(num.threads="1:1")
VER<-Sys.getenv("ST_VER","std3");D<-file.path("..","04_분석","TBNW");OUT<-file.path(D,paste0("results_",VER))
S<-fromJSON(file.path(D,paste0("config_TBNW_",VER,".json")))
DD<-read.csv(file.path(D,paste0("panel_TBNW_",VER,".csv")),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE);DD$fbd_region<-enc2utf8(DD$fbd_region);DD<-DD[DD$year>=2015,]
g<-inla.read.graph(file.path(D,"graph_593.graph"))
G<-st_read(paste0(Sys.getenv("ST_DATA_ROOT"), "/기타/R_Studio/FBD_DATA_ZIP/final.shp",quiet=TRUE);G$region<-enc2utf8(G$region)
DD<-DD[order(DD$year,match(DD$fbd_region,G$region)),];DD$area<-match(DD$fbd_region,G$region);DD$time<-DD$year-min(DD$year)+1;DD$yiid<-DD$time
HYP<-S$sets_after_vif$S1_narrative_full;COV<-unique(c(S$forced,HYP))
pc<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)),phi=list(prior="pc",param=c(0.5,2/3)));pcp<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)))
f<-as.formula(paste("cases ~ 1 +",paste(sprintf("`%s`",COV),collapse="+"),"+ f(area,model='bym2',graph=g,scale.model=TRUE,constr=TRUE,hyper=pc) + f(time,model='rw1',scale.model=TRUE,hyper=pcp) + f(yiid,model='iid',hyper=pcp)"))
m<-inla(f,family="nbinomial",data=DD,E=E,control.fixed=list(mean=0,prec=4,mean.intercept=0,prec.intercept=0.001),control.compute=list(waic=TRUE),control.inla=list(control.vb=list(emergency=50)))
fx<-m$summary.fixed[COV,];R<-data.frame(analysis="from2015",cov=COV,IRR=exp(fx$mean),lo=exp(fx$`0.025quant`),hi=exp(fx$`0.975quant`),cred=(fx$`0.025quant`>0|fx$`0.975quant`<0),WAIC=m$waic$waic,n=nrow(DD),years="2015-2025")
write.csv(R,file.path(OUT,"S52S_from2015.csv"),row.names=FALSE);print(R[R$cov%in%HYP,2:6])
