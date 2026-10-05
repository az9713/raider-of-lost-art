# Usage: python shots/run_api.py <shot_dir> <duration_s> <out_name.mp4> [resolution]
# Reads <shot_dir>/prompt.txt and <shot_dir>/api_ref_urls.json (key "image_urls"); keys from .env (never printed).
import json,sys,time,urllib.request,urllib.error
d=sys.argv[1]; dur=int(sys.argv[2]); out=sys.argv[3]; res=sys.argv[4] if len(sys.argv)>4 else '480p'
env={}
for l in open('.env',encoding='utf-8'):
    l=l.strip()
    if '=' in l and not l.startswith('#'):
        k,v=l.split('=',1); env[k.strip()]=v.strip().strip('"').strip("'")
auth='Key %s:%s'%(env['HF_API_KEY_ID'],env['HF_API_KEY_SECRET'])
body={"prompt":open(d+'/prompt.txt',encoding='utf-8').read(),"image_urls":json.load(open(d+'/api_ref_urls.json'))['image_urls'],
      "duration":dur,"resolution":res,"aspect_ratio":"16:9","generate_audio":True}
req=urllib.request.Request('https://api.higgsfield.ai/bytedance/seedance-2.0/reference-to-video',data=json.dumps(body).encode(),
      headers={'Authorization':auth,'Content-Type':'application/json','Accept':'application/json'},method='POST')
try:
    r=urllib.request.urlopen(req,timeout=120); resp=json.loads(r.read()); print('POST',r.status)
except urllib.error.HTTPError as e:
    print('POST FAILED',e.code,e.read().decode()[:600]); sys.exit(1)
json.dump(resp,open(d+'/api_submit.json','w'),indent=1); print('request_id',resp.get('request_id'))
t0=time.time(); last=None
while time.time()-t0<900:
    rq=urllib.request.Request(resp['status_url'],headers={'Authorization':auth,'Accept':'application/json'})
    try: s=json.loads(urllib.request.urlopen(rq,timeout=60).read())
    except urllib.error.HTTPError as e: print('poll error',e.code); time.sleep(10); continue
    if s.get('status')!=last: print(int(time.time()-t0),'s',s.get('status')); last=s.get('status')
    if s.get('status') in ('completed','failed','nsfw','canceled','error'): break
    time.sleep(10)
json.dump(s,open(d+'/api_result.json','w'),indent=1)
if s.get('status')=='completed':
    urllib.request.urlretrieve(s['video']['url'],d+'/'+out); print('downloaded',d+'/'+out)
