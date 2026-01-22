#!/usr/bin/env python3
import json
import time
from flask import Flask, Response, render_template_string

app = Flask(__name__)

HTML = '''<!DOCTYPE html>
<html>
<head>
<title>Streaming Test</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked@2.0.3/marked.min.js"></script>
<style>
body { font-family: system-ui; max-width: 800px; margin: 50px auto; padding: 20px; background: #1a1a2e; color: #eee; }
#output { background: #16213e; padding: 20px; border-radius: 8px; min-height: 200px; }
button { background: #4a90d9; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 10px 5px 10px 0; }
pre { background: #0f3460; padding: 12px; border-radius: 8px; overflow-x: auto; }
h1 { color: #4a90d9; }
</style>
</head>
<body>
<h1>Streaming Markdown Test</h1>
<button onclick="testStream()">Test Streaming</button>
<button onclick="testCode()">Test Code Block</button>
<button onclick="document.getElementById('output').innerHTML=''">Clear</button>
<div id="output"></div>
<script>
marked.setOptions({breaks:true, gfm:true, highlight:function(code,lang){
  try{if(lang&&hljs.getLanguage(lang))return hljs.highlight(code,{language:lang}).value;return hljs.highlightAuto(code).value;}catch(e){return code;}}});

async function testStream(){
  const out=document.getElementById('output'); out.innerHTML='<p>Streaming...</p>'; let txt='';
  const res=await fetch('/stream'); const rdr=res.body.getReader(); const dec=new TextDecoder();
  while(true){const{value,done}=await rdr.read();if(done)break;
    for(const ln of dec.decode(value).split('\\n')){if(!ln.trim())continue;
      try{const e=JSON.parse(ln);if(e.type==='chunk'){txt+=e.content;out.innerHTML=marked.parse(txt);}}catch(x){}}}}

async function testCode(){
  const out=document.getElementById('output'); out.innerHTML='<p>Streaming code...</p>'; let txt='';
  const res=await fetch('/stream-code'); const rdr=res.body.getReader(); const dec=new TextDecoder();
  while(true){const{value,done}=await rdr.read();if(done)break;
    for(const ln of dec.decode(value).split('\\n')){if(!ln.trim())continue;
      try{const e=JSON.parse(ln);if(e.type==='chunk'){txt+=e.content;out.innerHTML=marked.parse(txt);}}catch(x){}}}}
</script>
</body></html>'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/stream')
def stream():
    def gen():
        for c in ["# Hello ","World!\n\n","This is **streaming** ","markdown.\n\n","- Item 1\n","- Item 2\n"]:
            yield json.dumps({"type":"chunk","content":c})+"\n"
            time.sleep(0.15)
    return Response(gen(), mimetype='application/x-ndjson')

@app.route('/stream-code')
def stream_code():
    def gen():
        for c in ["Code example:\n\n","```python\n","def hello():\n","    print('Hi')\n","```\n"]:
            yield json.dumps({"type":"chunk","content":c})+"\n"
            time.sleep(0.12)
    return Response(gen(), mimetype='application/x-ndjson')

if __name__=='__main__':
    print("Open http://localhost:5555")
    app.run(port=5555,debug=True)
