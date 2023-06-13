
def getColor(label):
	if label == "裁判書":
		return "Black"
	elif label == "結果":
		return "MediumVioletRed"
	elif label == "被告":
		return "#008080" #Teal
	elif label == "原告":
		return "MediumAquamarine"
	elif label == "證人":
		return "SteelBlue"
	elif label == "法官":
		return "MediumBlue"
	elif label == "檢察官":
		return "CornflowerBlue"
	elif label == "書記官":
		return "DodgerBlue"
	elif label == "語詞":
		return "Purple"
	elif label == "拘役":
		return "OrangeRed"
	elif label == "罰金":
		return "DarkOrange"
	elif label == "日期":
		return "MediumSeaGreen"
	elif label == "地點":
		return "SaddleBrown"
	elif label == "法條":
		return "IndianRed"
	else:
		return "#2F4F4F" #DarkSlateGray


# 有期徒刑