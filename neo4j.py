# -*- coding:utf-8 -*-
import os, json, random
from dotenv import load_dotenv
import py2neo
from py2neo import Node, Relationship, Graph, Path, Subgraph

from extractor import *
from utils import *
import CKIP

load_dotenv()
db_server = os.getenv("NEO4J_SERVER")
db_name = os.getenv("NEO4J_NAME")
db_user, db_pass = os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASS")

graph = Graph(db_server, name=db_name, auth=(db_user, db_pass))

def genKey():
	seed = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
	return ''.join(random.sample(seed,3))

def extract(title, text, laws=[]):
	text = re.sub('[ 　  \r\n]', '', text)

	ckip_res = CKIP.request(text)

	maintext = extract_maintext(text)
	persons = extract_person_ckip(ckip_res)
	bad_words = extract_insult(text, ckip_res)
	fine = regexp_match(maintext,'.*[處科]罰金([^，。]+).*' , None)
	days = regexp_match(maintext,'.*處拘役([^，。]+).*' , None)
	judge_result = extract_result(text, maintext)
	features = extract_feature(text, ckip_res)
	data = {'title': title,
			'maintext': maintext,
			'persons': persons,
			'location': list(set(features['loca']+features['addr'])),
			'date': list(set(features['date'])),
			'bad_words': bad_words,
			'fine': fine, #罰金
			'days': days, #拘役X日
			'laws': list(set(laws)),
			'result': judge_result,
			'text': text,
	}
	return data

def commit(data, skip_existed=False):
	title = data['title']
	cypher = f"MATCH (n:裁判書) WHERE n.name = '{title}' RETURN n"
	result = graph.run(cypher).data()

	if len(result) > 0:
		if skip_existed:
			return data['title']
		else:
			data['title'] = f"{data['title']}_{genKey()}"
			return commit(data)

	tx = graph.begin()
	temp = {}
	judge = Node("裁判書", name=data['title'], text=data['text'])
	for person in data['persons']:
		if person not in temp:
			node = Node(person[0], name=person[1])
			temp[person] = node
		else:
			node = temp[person]
		relation = Relationship(node, "屬於", judge)
		if person[0] == '被告' and data['bad_words']:
			for bad_word in data['bad_words']:
				if bad_word not in temp:
					temp[bad_word] = Node("語詞", name=bad_word)
				relation_bad = Relationship(node, "罵", temp[bad_word])
				relation_bad_con = Relationship(temp[bad_word], "屬於", judge)
				tx.create(relation_bad)
				tx.create(relation_bad_con)
		if person[0] == '被告' and data['fine']:
			if ('罰金', data['fine']) not in temp:
				temp[('罰金', data['fine'])] = Node('罰金', size=data['fine'])
			relation_money = Relationship(node, "遭判", temp[('罰金', data['fine'])])
			relation_money_j = Relationship(temp[('罰金', data['fine'])], "屬於", judge)
			tx.create(relation_money)
			tx.create(relation_money_j)
		if person[0] == '被告' and data['days']:
			if ('拘役', data['days']) not in temp:
				temp[('拘役', data['days'])] = Node('拘役', size=data['days'])
			relation_day = Relationship(node, "遭判", temp[('拘役', data['days'])])
			relation_day_j = Relationship(temp[('拘役', data['days'])], "屬於", judge)
			tx.create(relation_day)
			tx.create(relation_day_j)
		tx.create(relation)
	if data['laws']:
		node = Node("法條", name="相關法律", data=data['laws'])
		relation = Relationship(node, "屬於", judge)
		for issue in data['laws']:
			node_issue = Node("法條", name=issue)
			relation_issue = Relationship(node_issue, "屬於", node)
			tx.create(relation_issue)
		tx.create(relation)
	if data['result']:
		node_result = Node("結果", name=data['result'])
		relation_result = Relationship(node_result, "屬於", judge)
		tx.create(relation_result)
	if data['location']:
		if len(data['location']) > 1:
			node = Node("地點", name="地點", data=data['location'])
			relation = Relationship(node, "屬於", judge)
			for location in data['location']:
				node_loca = Node("地點", name=location)
				rela_loca = Relationship(node_loca, "屬於", node)
				tx.create(rela_loca)
			tx.create(relation)
		else:
			node_loca = Node("地點", name=data['location'][0])
			rel_loca = Relationship(node_loca, "屬於", judge)
			tx.create(rel_loca)
	if data['date']:
		node = Node("日期", name="日期", data=data['date'])
		relation = Relationship(node, "屬於", judge)
		for date in data['date']:
			node_date = Node("日期", name=date)
			relation_date = Relationship(node_date, "屬於", node)
			tx.create(relation_date)
		tx.create(relation)
	graph.commit(tx)

	return data['title']

def getAllNodes(target="語詞"):
	cypher = f"MATCH (n:{target}) RETURN n"
	results = graph.run(cypher).data()
	return [result['n']['name'] for result in results if len(result['n']['name']) < 15]

def getJudgement(title):
	cypher = f"MATCH (n:裁判書) WHERE n.name = '{title}' RETURN n"
	result = graph.run(cypher).data()
	if len(result) > 0:
		return dict(result[0]['n'])
	else:
		return False

def getRelatedNode(title):
	cypher = f"MATCH (n:裁判書)-[r:屬於]-(k) WHERE n.name = '{title}' RETURN k"
	nodes = graph.run(cypher).data()
	res = {}
	for node in nodes:
		label = list(node['k'].labels)[0]
		if label not in res:
			res[label] = []
		if node['k']['data']:
			for data in list(node['k']['data']):
				res[label] += [data]
		else:
			res[label] += [node['k']['name'] if node['k']['name'] else node['k']['size']]
	#if res['法條']:
	#	res['法條'] = [law.replace("中華民國", "") for law in res['法條']]

	for label in res:
		res[label] = sorted(res[label], key=len, reverse=True)
	targets = ["結果", "被告", "原告", "證人", "法官", "檢察官", "書記官", "語詞", "拘役", "罰金", "日期", "時間", "法條"]
	res = dict(sorted(res.items(), key=lambda item: targets.index(item[0]) if item[0] in targets else 999))
	return res

def getgraph(title="臺灣高等法院 臺中分院刑事103,上易,480"):
	cypher = f"MATCH (n:裁判書)-[r:屬於]-(k) WHERE n.name = '{title}' RETURN *"
	result = graph.run(cypher).to_subgraph()

	nodes, rels = [], []
	for node in result.nodes:
		label = list(node.labels)[0]
		nodes += [{'name':node['name'] if node['name'] else node['size'],
					'label':label, 'color': getColor(label),
				}]
		if node['data']:
			for data in list(node['data']):
				nodes += [{'name':data, 'label':label, 'color': getColor(label)}]

	targets = ["結果", "被告", "原告", "證人", "法官", "檢察官", "書記官", "語詞", "拘役", "罰金", "日期", "時間", "法條"]
	nodes = sorted(nodes, key=lambda node: targets.index(node['label']) if node['label'] in targets else 999)
	names = [node['name'] for node in nodes]
	for rel in result.relationships:
		walks = list(py2neo.data.walk(rel))
		src = walks[0]['name'] if walks[0]['name'] else walks[0]['size']
		dst = walks[2]['name'] if walks[2]['name'] else walks[2]['size']
		rels += [{'source':names.index(src), 'target':names.index(dst)}]
		if walks[0]['data']:
			for data in list(walks[0]['data']):
				rels += [{'source':names.index(data), 'target':names.index(src)}]

	return {"nodes":nodes, "links":rels}

if __name__ == '__main__':
	#MATCH (n:裁判書) WHERE n.name = 'TEST' RETURN n
	#MATCH (n:裁判書) WHERE n.name = 'TEST' detach delete n

	with open(f"./data/臺灣臺南地方法院 112 年度訴字第 345 號刑事判決.json", 'r', encoding='utf-8') as f:
		judge = json.load(f)
	data = extract(judge["裁判字號"], judge["主文"], judge['相關法條'])
	with open(f"./result/{judge['裁判字號']}.json", "w", encoding='utf-8') as f:
		json.dump(data, f, indent=4, ensure_ascii=False)

	exit()
	test = "臺灣屏東地方法院 112 年度易字第 260 號刑事判決"
	print(getRelatedNode(test))
	print(getgraph(test))
