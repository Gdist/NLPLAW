import os, json, requests
from dotenv import load_dotenv

load_dotenv()
server = os.getenv("CKIP_SERVER")
TOKEN = os.getenv("CKIP_TOKEN")

def request(sent):
    res = requests.post("http://140.116.245.157:2001", data={"data":sent, "token":TOKEN})
    if res.status_code == 200:
        return json.loads(res.text)
    else:
        return None 

def printJSON(data):
    if isinstance(data, str) or isinstance(data, int): print(data)
    else: print(json.dumps(data, ensure_ascii=False, indent=4))

def getExample(sent):
    res = requests.post("http://140.116.245.151/NER_news_fe/extractor.php", data={"sentence":sent})
    if res.status_code == 200:
        return res.json()
    else:
        return None

def NER(sent):
    r = request(sent, TOKEN)

    nameList, timeList, locList, objList,  = [], [], [], []
    eventList, simpleList, tmpSimList = [], [], []
    tmpSim, tmpEvt= [], []

    for word, tag in zip(r["ws"][0], r["pos"][0]):
        # 人時地物
        if tag == "Nb": nameList += [word]
        elif tag == "Nd": timeList += [word]
        elif tag == "Nc": locList += [word]
        elif tag == "Na": objList += [word]
        # 事件
        if tag in ["COMMACATEGORY", "PERIODCATEGORY", "SEMICOLONCATEGORY"] and tmpEvt:
            simpleList.append(tmpSim)
            eventList.append("".join(tmpEvt))
            tmpSim = ""
            tmpEvt = []
        elif tag in ["VC", "VJ", "VCL"]:
            tmpSim = word if not tmpEvt else tmpEvt[0] + word
            tmpEvt += [word]
        elif tag in ["Caa", "Cba", "Cbb", "VA", "VE", "D", "P"] and tmpEvt:
            tmpEvt += [word]
            tmpSim = tmpEvt[0] + tmpEvt[-1]
        elif tag == "DE" and tmpEvt and preType in ["VC", "VJ", "VCL"]:
            tmpEvt += [word]
            tmpSim = tmpEvt[0] + tmpEvt[-1]
        elif tag[0] == "N" and tmpEvt:
            tmpEvt += [word]
            tmpSim = tmpEvt[0] + tmpEvt[-1]
        elif tag in ["PAUSECATEGORY", "PARENTHESISCATEGORY"] and tmpEvt:
            tmpEvt += [word]
            tmpSim = tmpEvt[0] + tmpEvt[-2]
        preType = tag # 用於DE，檢查前一個字是不是及物動詞
    #for ner in r["ner"][0]:


    res1 = {"pnList": nameList, "tList":timeList, "locList":locList, "objList":objList,
            "simpleEventList":simpleList, "fullEventList":eventList}
    return res1