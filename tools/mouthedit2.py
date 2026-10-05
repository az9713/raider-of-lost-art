import cv2,numpy as np,json,os,sys
tr=json.load(open('mouth_track.json'))
H,W=480,854
DROP=float(sys.argv[1]) if len(sys.argv)>1 else 6.0     # extra jaw opening in px at frame-192 scale
CON=float(sys.argv[2]) if len(sys.argv)>2 else 1.0
os.makedirs('s4out',exist_ok=True)
def smooth(x): x=np.clip(x,0,1); return x*x*(3-2*x)
X,Y=np.meshgrid(np.arange(W,dtype=np.float32),np.arange(H,dtype=np.float32))
cx,half=280.0,36.0
t=(X-cx)/half; q=np.clip(1-t*t,0,1)
yc=268.0
yu=yc+q*3.5                     # upper edge of the teeth band
yl=yc+q*13.0                    # lower lip line
def edit192(im,s):
    d=DROP*s*q                  # jaw opening
    yl2=yl+d
    # remap: inside opening stretch; below, shift down with falloff
    src_y=Y.copy()
    inside=(Y>=yu)&(Y<=yl2)&(q>0)
    ratio=np.where(yl2-yu>0.5,(yl-yu)/np.maximum(yl2-yu,0.5),1.0)
    src_y=np.where(inside,yu+(Y-yu)*ratio,src_y)
    below=(Y>yl2)&(Y<=yl2+14)&(q>0)
    fall=np.clip(1-(Y-yl2)/14.0,0,1)
    src_y=np.where(below,Y-d*fall,src_y)
    out=cv2.remap(im,X,src_y.astype(np.float32),cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
    # teeth contrast inside the opening
    lab=cv2.cvtColor(out,cv2.COLOR_BGR2LAB).astype(np.float32)
    L=lab[:,:,0]; reg=((Y>yu)&(Y<yl2-1.5)&(q>0.1)).astype(np.float32)
    reg=cv2.GaussianBlur(reg,(0,0),1.0)
    mean=cv2.GaussianBlur(L,(0,0),3.0)
    L2=mean+(L-mean)*(1+1.6*CON*s)           # amplify tooth gaps vs tooth faces
    L2=L2-18*s*CON*(1-np.clip((L-mean)*0.05+0.5,0,1))*0   # no global darken
    lab[:,:,0]=np.clip(L*(1-reg)+L2*reg,0,255)
    return cv2.cvtColor(lab.astype(np.uint8),cv2.COLOR_LAB2BGR)
for f in range(193):
    im=cv2.imread(f's4f/f{f:03d}.png')
    s=smooth((f-168)/14.0) if f>=168 else 0.0
    if s<=0: cv2.imwrite(f's4out/f{f:03d}.png',im); continue
    M=np.array(tr[str(f)]['M'],np.float32)             # 192 -> f
    al=cv2.warpAffine(im,M,(W,H),flags=cv2.INTER_CUBIC|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REPLICATE)   # f aligned to 192
    ed=edit192(al,s)
    mask=np.zeros((H,W),np.float32); cv2.ellipse(mask,(280,278),(44,22),0,0,360,1.0,-1); mask=cv2.GaussianBlur(mask,(0,0),2.5)
    back=cv2.warpAffine(ed,M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
    mb=cv2.warpAffine(mask,M,(W,H),flags=cv2.INTER_LINEAR)[...,None]
    out=np.clip(im.astype(np.float32)*(1-mb)+back.astype(np.float32)*mb,0,255).astype(np.uint8)
    cv2.imwrite(f's4out/f{f:03d}.png',out)
ims=[]
for f in (168,174,180,186,192):
    o=cv2.imread(f's4f/f{f:03d}.png')[235:310,215:345]; n=cv2.imread(f's4out/f{f:03d}.png')[235:310,215:345]
    r=np.hstack([cv2.resize(o,None,fx=4,fy=4,interpolation=cv2.INTER_CUBIC),cv2.resize(n,None,fx=4,fy=4,interpolation=cv2.INTER_CUBIC)])
    cv2.putText(r,str(f),(5,22),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,255,255),2); ims.append(r)
cv2.imwrite('mcmp2.jpg',np.vstack(ims))
