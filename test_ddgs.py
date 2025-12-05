from ddgs import DDGS
import pprint

results = DDGS().text("đèn bàn site:https://rangdongstore.vn/", max_results=5)
for result in results:
    print("--------------------------------")
    pprint.pprint(result)