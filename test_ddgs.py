from ddgs import DDGS
import pprint

results = DDGS().text("đèn bàn site:https://rangdong.com.vn/", max_results=10)
for result in results:
    print("--------------------------------")
    pprint.pprint(result)