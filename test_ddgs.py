from ddgs import DDGS
import pprint

results = DDGS().text("bóng đèn rạng đông 60w site:https://rangdong.com.vn/", max_results=10)
for result in results:
    print("--------------------------------")
    pprint.pprint(result['title'])