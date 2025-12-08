from ddgs import DDGS
import pprint

results = DDGS().text("đèn led 5W site:https://rangdongstore.vn/", max_results=10)
for result in results:
    print("--------------------------------")
    pprint.pprint(result)