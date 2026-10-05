import cv2,numpy as np,json
def G(f): return cv2.cvtColor(cv2.imread(f's4f/f{f:03d}.png'),cv2.COLOR_BGR2GRAY).astype(np.float32)
ref=G(192); H,W=ref.shape
# head ROI mask in frame 192 (eyes+nose+cheeks, exclude mouth rows and background): rectangle
mask=np.zeros((H,W),np.uint8); cv2.rectangle(mask,(215,185),(345,262),255,-1)   # eyes to nose base, inside face
C192=np.array([[245,268],[315,266]],np.float32)   # left, right mouth corners at 192 (my reading)
out={}
prev=np.eye(2,3,dtype=np.float32)
for f in range(192,150,-1):
    g=G(f)
    w=prev.copy()
    try:
        cc,w=cv2.findTransformECC(ref,g,w,cv2.MOTION_AFFINE,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,200,1e-6),mask,5)
    except cv2.error as e:
        print(f,'ECC fail'); w=prev
    prev=w.copy()
    p=(w@np.vstack([C192.T,np.ones((1,2))])).T
    out[f]={'M':w.tolist(),'corners':p.tolist(),'cc':float(cc)}
    if f%6==0 or f==193: print(f,round(float(cc),3),np.round(p,1).tolist())
json.dump(out,open('mouth_track.json','w'))
# overlay check
ims=[]
for f in (192,186,180,174,168,162):
    im=cv2.imread(f's4f/f{f:03d}.png'); c=np.array(out[f]['corners'])
    for q in c: cv2.circle(im,(int(round(q[0])),int(round(q[1]))),1,(0,0,255),-1)
    crop=cv2.resize(im[240:310,225:340],None,fx=5,fy=5,interpolation=cv2.INTER_CUBIC)
    # recompute marker positions on upscaled
    for q in c: cv2.circle(crop,(int((q[0]-225)*5),int((q[1]-240)*5)),5,(0,0,255),2)
    cv2.putText(crop,str(f),(5,22),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,255,255),2); ims.append(crop)
cv2.imwrite('mtrack.jpg',np.vstack([np.hstack(ims[i:i+2]) for i in range(0,6,2)]))
