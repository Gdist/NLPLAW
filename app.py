import os, json
from flask import Flask, request, render_template, redirect, url_for, escape, Response

from neo4j import *
from utils import *
from crawler import *

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
	return render_template('index.html')

@app.route('/hello')
def hello():
	return 'Hello World'

# 查詢資料庫現有資料
@app.route('/query', methods=['GET'])
def query():
	title = request.args.get('title')
	judge = getJudgement(title)
	nodes = getRelatedNode(title)
	graph = True #getgraph(title)
	text = judge['text']
	html = str(escape(text)) #?
	html_nodes = nodes.copy()

	for label in nodes:
		color = getColor(label)
		for node in nodes[label]:
			html = html.replace(node, f"<font color=\"{color}\"><b>{node}</b></font>")
		new_label = f"<font color=\"{color}\">{label}</font>"
		html_nodes[new_label] = html_nodes.pop(label)
	return render_template('index.html', title=title, text=text, html=html, nodes=html_nodes, graph=graph)


@app.route('/submit', methods=['POST'])
def submit():
	title  = request.form['title']
	mytext = request.form['mytext']
	data = extract(title, mytext)
	mytitle = commit(data)
	return redirect(url_for('query', title=mytitle))

@app.route('/search', methods=['POST'])
def search():
	keyword  = request.form['keyword'].strip()

	node = getJudgement(keyword) # 1. keyword是判決書名稱，且在database中
	if node: return redirect(url_for('query', title=node['name']))
	app.logger.info(keyword)
	if (os.path.exists(f"./data/{keyword}.json")): # 2. keyword是判決書名稱，且在local disk
		filepath = f"./data/{keyword}.json"
	else:
		result = crawlJudge(keyword, num=1, page=1)
		filepath = result[0]

	with open(filepath, 'r', encoding='utf-8') as f:
		judge = json.load(f)

	node = getJudgement(judge["裁判字號"])
	if node:
		return redirect(url_for('query', title=node['name']))

	data = extract(judge["裁判字號"], judge["主文"], judge['相關法條'])
	mytitle = commit(data)
	return redirect(url_for('query', title=mytitle))

@app.route('/graph', methods=['GET'])
def graph():
	title = request.args.get('title')
	
	res = getgraph(title)
	return Response(json.dumps(res), mimetype="application/json")

if __name__ == '__main__':
	app.run(host="0.0.0.0", port=11616, debug=True)