import requests
import math
import pprint
import time
import json
import os

from bs4 import BeautifulSoup


forkortelser = {" f.eks. ": "_#=#==",
								" b.la. " : "==_##=",
								" d. "    : "#_==##",
								" ca. "   : "__##__",
								" dvs. "  : "-##-##",
								"0. " : "0_###",
								"1. " : "1_###",
								"2. " : "2_###",
								"3. " : "3_###",
								"4. " : "4_###",
								"5. " : "5_###",
								"6. " : "6_###",
								"7. " : "7_###",
								"8. " : "8_###",
								"9. " : "9_###",
}

def current_time():
	t = time.localtime()
	current_time = time.strftime("%H:%M:%S", t)
	return current_time


class Results():
	#Handles outputting of web hit results in a readable json-format


	def __init__(self, url_per = 2):
		self.url_per = url_per
		
	def get_json(self, file="results.json"):

		if not os.path.exists(file):
			with open(file, "w") as f:
				f.write("{}")

		with open(file, "r") as f:
			return json.load(f)

	def get_url_list(self):
		url_list = []
		for entryno, result in self.get_json().items():
			url_list += result["Results"]

		return url_list

	def get_hits(self):
		hits = {}
		for entryno, result in self.get_json().items():
			if not result["Results"] == [""]:
				hits[entryno] = result
		return hits

	def save_hits(self, file="hits.json"):
		hits = self.get_hits()
		with open(file, "w") as f:
			json.dump(hits, f, indent=4, sort_keys=True)
		return len(hits)

	def get_duplicate_urls(self, dist = 4):
		'''
		Return urls which were repeated within a certain threshhold/distance
		'''
		dup_urls = []

		listsize = 2 * dist * self.url_per + 1
		circ_buffer = [None]*listsize
		for url in self.get_url_list():
			circ_buffer.append(url)

			mid_url = circ_buffer[dist * self.url_per + 1]
			if circ_buffer.count(mid_url) > 1:
 			# If middle url duplicate

 				if not mid_url in dup_urls: dup_urls.append(mid_url)

			circ_buffer.pop(0)

		return dup_urls

	def get_entry_keys(self):
		data = self.get_json()
		return [key for key in data]

	def update_json(self, append_dict, file="results.json"):

		with open(file, "r") as f:
			data = json.load(f)

		for key in append_dict:
			data[str(key).zfill(5)] = append_dict[key]

		with open(file, "w") as f:
			json.dump(data, f, indent=4, sort_keys = True)



class Text():
	# Class responsible for i/o of text string to plagiarize-detect onto,
	# as well as rudimentary string formatting

	def __init__(self,txtpath="metoo.txt"):

		with open(txtpath, "r", encoding="utf-8", errors="ignore") as f:
			txt = f.read()

		self.txt = txt 
		#Adds self.sen_list


	def get_sentences_list(self, truncate = -1, remove_thresh=0):
		return self.sen_list


	def change_sentencences_list(self, truncate = -1, remove_thresh = 0):
		#Umbrella function for formatting string for better hits
		#TODO: Distribute functionality

		encoded = self.txt
		for key, value in forkortelser.items():
			#Encode expressions that we don't want to split on "."
			encoded = encoded.replace(key,value)

		encoded = encoded.replace(".\n", ". ")
		encoded = encoded.replace('."', ". ")	
		encoded = encoded.replace(":\n", ". ")
		encoded = encoded.replace(": ", ". ")
		encoded = encoded.replace("? ", ". ")		
		code_list = encoded.split(". ")

		sen_list = code_list
		for key, value in forkortelser.items():
			#Decode back
			for i, code in enumerate(sen_list):
				sen_list[i] = sen_list[i].replace(value, key)


		sen_list = [sen.strip() for sen in sen_list]

		#Remove Under size threshold
		sen_list = [sen for sen in sen_list if len(sen)>remove_thresh]
		#[print(len(sen)) for sen in sen_list]

		#Truncate
		sen_list = [sen[:truncate] for sen in sen_list]

		self.sen_list = sen_list





class TextWalker():
	'''
	High level object handling the web request work
	TODO: Add functionality for other web searches
	DuckDuckGO is only supported at the moment.
	TODO: Add proxy functionality for faster traversal
	TODO: Traverse string in bins / binary-tree instead
	of only sequentially/linearily 
	'''

	def __init__(self, resultsobject, textobject):

		self.results = resultsobject
		self.textobject = textobject

		self.textobject.change_sentencences_list()


	def get_ddg_results(self, query):

		response = requests.get(f'https://html.duckduckgo.com/html/?q="{query}"', headers={'User-Agent': 'Mozilla/5.0'})
		if not response.ok:
			raise Exception("Request Denied :(")
		soup = BeautifulSoup(response.text, "html.parser")

		urls = [url.text.replace(" ", "").replace("\n", "") for url in soup.findAll("a", class_="result__url")][0:2]

		return urls

	def get_already_done(self):
		return [int(x) for x in self.results.get_entry_keys()]

	def walk_through_senlist(self, sleeptime=3, start=0, end=-1, skip=True):
		already_done = self.get_already_done()

		sen_list = self.textobject.get_sentences_list()

		for n, sen in enumerate(sen_list[start:end]):

			if skip: #Skip over known entries
				if n+start in already_done:
					print(f"{n+start} Already done")
					continue

			query = sen
			print(query)
			results = self.get_ddg_results(query)
			print(n+start, results)
			self.results.update_json({(n+start):{"Sentence":sen,"Results":results}})
			time.sleep(sleeptime)

	def half_hour_walk(self, sleeptime=3, start=0, end=-1, skip=True):
		while True:
			#try:
				self.walk_through_senlist(sleeptime, start, end, skip)
			#except Exception as e:
			#	print (e)
			#	print(f"Sleeping for 30min. at {current_time()}")
			#	time.sleep(60*30)



def main():

	r = Results()
	tx = Text(txtpath="metoo.txt")
	t = TextWalker(r, tx)
	tx.change_sentencences_list(truncate=200, remove_thresh=50)
	t.half_hour_walk()

main()

