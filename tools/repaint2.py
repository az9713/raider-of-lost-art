import cv2,numpy as np,os,math
N=193
F=[cv2.imread(f'fr/f{i:03d}.png') for i in range(N)]
H,W=F[0].shape[:2]
out=[f.copy() for f in F]

def gold(im):
    hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
    m=((hsv[:,:,0]>=14)&(hsv[:,:,0]<=38)&(hsv[:,:,1]>90)&(hsv[:,:,2]>95)).astype(np.uint8)*255
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
    return cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
def idol(im):
    g=gold(im); n,lab,st,_=cv2.connectedComponentsWithStats(g)
    o=np.zeros((H,W),np.uint8)
    if n<2: return o
    i=1+int(np.argmax(st[1:,cv2.CC_STAT_AREA]))
    cv2.fillConvexPoly(o,cv2.convexHull(cv2.findNonZero((lab==i).astype(np.uint8))),255); return cv2.dilate(o,np.ones((5,5),np.uint8))
def protect(im):
    hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
    skin=((hsv[:,:,0]<=22)&(hsv[:,:,2]>125)&(hsv[:,:,1]>25)).astype(np.uint8)*255
    return cv2.bitwise_or(cv2.dilate(skin,np.ones((5,5),np.uint8)),cv2.dilate(idol(im),np.ones((5,5),np.uint8)))

# ---------- lump removal (stone-weighted normalised blur) ----------
def stone_fill(im,cx,cy,rx,ry,xmin=0,xmax=None,sig=6,warm_add=True,prot=True):
    hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); h,s_,v=hsv[:,:,0],hsv[:,:,1],hsv[:,:,2]
    stone=((h>=82)&(h<=104)&(s_>=55)&(s_<=160)&(v>=58)&(v<=145)).astype(np.uint8)*255
    water=((h>=80)&(h<=108)&(v>=145)).astype(np.uint8)*255
    reg=np.zeros((H,W),np.uint8); cv2.ellipse(reg,(cx,cy),(rx+6,ry+5),0,0,360,255,-1)
    reg[:,:xmin]=0
    if xmax: reg[:,xmax:]=0
    base=((h>=85)&(h<=115)&(s_>130)&(v<75)).astype(np.uint8)*255
    base=cv2.dilate(base,np.ones((5,5),np.uint8)); base[cy-3:,:]=0   # idol base sits above the lump
    keep=cv2.bitwise_or(base,protect(im)) if prot else base
    keep=cv2.bitwise_or(keep,cv2.dilate(water,np.ones((3,3),np.uint8)))
    mask=cv2.bitwise_and(reg,cv2.bitwise_not(cv2.bitwise_or(stone,keep)))
    if warm_add:
        warm=(((h<=58)&(s_>=20)&(v>=12)&(v<=150))|((h<=25)&(s_>=90)&(v>=100))).astype(np.uint8)*255
        mask=cv2.bitwise_or(mask,cv2.bitwise_and(cv2.bitwise_and(warm,reg),cv2.bitwise_not(keep)))
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
    if warm_add:
        dark=(v<82).astype(np.uint8)*255
        wr=cv2.bitwise_and(cv2.bitwise_and(cv2.bitwise_or(warm,dark),reg),cv2.bitwise_not(keep))
        wr=cv2.morphologyEx(wr,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
        nn,ll,ss,_=cv2.connectedComponentsWithStats(wr)
        ok_=[i for i in range(1,nn) if ss[i,4]>=25]
        if ok_:
            pts=cv2.findNonZero(np.isin(ll,ok_).astype(np.uint8))
            hm=np.zeros((H,W),np.uint8); cv2.fillConvexPoly(hm,cv2.convexHull(pts),255)
            mask=cv2.bitwise_or(mask,hm)
    mask=cv2.dilate(mask,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))
    mask=cv2.bitwise_and(mask,cv2.bitwise_not(keep))
    if xmin: mask[:,:xmin]=0
    if xmax: mask[:,xmax:]=0
    wgt=(stone>0).astype(np.float32); wgt[cv2.dilate(mask,np.ones((5,5),np.uint8))>0]=0
    f=im.astype(np.float32)
    num=cv2.GaussianBlur(f*wgt[...,None],(0,0),sig); den=cv2.GaussianBlur(wgt,(0,0),sig)[...,None]
    fill=num/np.maximum(den,1e-3); ok=(den[...,0]>0.03)
    soft=cv2.GaussianBlur(mask.astype(np.float32)/255.0,(0,0),1.3)
    tel=cv2.inpaint(im,mask,7,cv2.INPAINT_TELEA).astype(np.float32)
    fill=tel
    rng=np.random.RandomState(7); nz=cv2.GaussianBlur(rng.randn(H,W).astype(np.float32),(0,0),1.0)*5.0
    fill=fill+nz[...,None]
    res=np.clip(f*(1-soft[...,None])+fill*soft[...,None],0,255).astype(np.uint8)
    sp=((h<=20)&(s_>120)&(v>100)&(reg>0)&(keep==0))
    if sp.any():
        sp=cv2.dilate(sp.astype(np.uint8)*255,np.ones((3,3),np.uint8)); res=cv2.inpaint(res,sp,3,cv2.INPAINT_TELEA)
    rest=np.zeros((H,W),bool)
    if rest.any():
        t=cv2.inpaint(res,(rest*255).astype(np.uint8),5,cv2.INPAINT_TELEA); res[rest]=t[rest]
    return res
def tfill(im,m,rad=5): return cv2.inpaint(im,m,rad,cv2.INPAINT_TELEA)

lump={113:(471,292,26,15),114:(457,292,26,15),115:(447,292,26,15),116:(442,292,26,15),
      119:(430,298,14,12,420,W),117:(432,295,24,14,418,W),118:(430,296,18,13,421,W),
      122:(350,313,16,13,0,358),123:(341,324,16,13,0,352),124:(333,331,16,13,0,346),125:(327,336,18,14,0,340)}
dome={126:(316,347),127:(308,354),128:(295,359),129:(279,365),130:(264,375),131:(248,385),132:(230,395),133:(208,403)}

# ---------- sprite from frame 113 ----------
im=F[113]; hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
warm=((hsv[:,:,0]<=58)&(hsv[:,:,1]>=25)&(hsv[:,:,2]>=40)&(hsv[:,:,2]<=150)).astype(np.uint8)*255
reg=np.zeros((H,W),np.uint8); cv2.ellipse(reg,(471,292),(26,15),0,0,360,255,-1)
wm=cv2.bitwise_and(warm,reg); wm=cv2.morphologyEx(wm,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(wm); i=1+int(np.argmax(st[1:,4]))
pts=cv2.findNonZero((lab==i).astype(np.uint8)); hull=np.zeros((H,W),np.uint8); cv2.fillConvexPoly(hull,cv2.convexHull(pts),255)
hull=cv2.erode(hull,np.ones((2,2),np.uint8))
alpha=cv2.GaussianBlur(hull.astype(np.float32),(0,0),0.9)
x,y,w,h=cv2.boundingRect(hull); SCX,SCY=x+w//2,y+h//2
SP=np.dstack([F[113].astype(np.float32),alpha])[SCY-24:SCY+24,SCX-34:SCX+34]   # 48x68 BGRA
cv2.imwrite('dbg_sprite2.png',cv2.resize(np.dstack([SP[...,:3],np.full(SP.shape[:2],255,np.float32)]).astype(np.uint8)[...,:3],None,fx=6,fy=6))
cv2.imwrite('dbg_sprite2_a.png',cv2.resize(SP[...,3].astype(np.uint8),None,fx=6,fy=6))

patch={126:(342,332),127:(332,339),128:(318,345),129:(300,352),130:(288,361),131:(272,367),132:(254,373),133:(236,377),
       134:(217,387),135:(190,396),136:(169,409),137:(149,413),138:(113,439),139:(80,455),140:(60,465),141:(40,475)}
path={113:(506,274),114:(546,277),115:(584,291),116:(618,314),117:(650,347),118:(680,388),119:(708,436),120:(734,490)}
def place(base,k):
    cx,cy=path[k]; p0=path.get(k-1,(467,282)); p1=path.get(k+1,(cx+26,cy+50))
    vx,vy=(p1[0]-p0[0])/2,(p1[1]-p0[1])/2; sp=math.hypot(vx,vy)
    ang=28.0*(k-112)
    sh,sw=SP.shape[:2]
    big=np.zeros((200,200,4),np.float32); big[100-sh//2:100-sh//2+sh,100-sw//2:100-sw//2+sw]=SP
    M=cv2.getRotationMatrix2D((100,100),-ang,1.0)
    rot=cv2.warpAffine(big,M,(200,200),flags=cv2.INTER_CUBIC)
    L=int(max(1,min(sp*0.5,24)))
    if L>2:
        ker=np.zeros((L,L),np.float32); th=math.atan2(vy,vx)
        cv2.line(ker,(L//2-int(round(math.cos(th)*(L-1)/2)),L//2-int(round(math.sin(th)*(L-1)/2))),(L//2+int(round(math.cos(th)*(L-1)/2)),L//2+int(round(math.sin(th)*(L-1)/2))),1,1)
        ker/=ker.sum(); rot=cv2.filter2D(rot,-1,ker)
    T=np.float32([[1,0,cx-100],[0,1,cy-100]])
    lay=cv2.warpAffine(rot,T,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    al=np.clip(lay[...,3:4],0,1)
    return np.clip(base.astype(np.float32)*(1-al)+lay[...,:3]*al,0,255).astype(np.uint8)

for f in range(113,142):
    base=F[f].copy()
    if f in lump:
        cx,cy,rx,ry,*bd=lump[f]; base=stone_fill(base,cx,cy,rx,ry,*bd,prot=(f<119))
    if f in dome:
        cx,cy=dome[f]; m=np.zeros((H,W),np.uint8); cv2.ellipse(m,(cx,cy),(20,13),0,0,360,255,-1)
        base=tfill(base,m,6)
    if f in patch:
        cx,cy=patch[f]; m=np.zeros((H,W),np.uint8); cv2.ellipse(m,(cx,cy+(4 if f>=134 else 0)),((34,19) if f>=134 else (26,15)),0,0,360,255,-1)
        base=tfill(base,m,7)
    if f in path: base=place(base,f)
    out[f]=base
os.makedirs('out',exist_ok=True)
for i,im in enumerate(out): cv2.imwrite(f'out/f{i:03d}.png',im)
print('done')
