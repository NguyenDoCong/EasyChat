from langchain_core.documents import Document
from datetime import datetime

def get_all_tasks():
    """Get all tasks."""

    results = []
    for response in responses:
        assignees = " and ".join(response["assignees"])
        comments  = " and ".join(response["comments"])
        try:
            date_obj = datetime.strptime(response['start_date'], "%Y-%m-%d")
            start_date = date_obj.timestamp()
        except Exception as e:
            # print(e)
            start_date = None
        try:
            date_obj = datetime.strptime(response['target_date'], "%Y-%m-%d")
            target_date = date_obj.timestamp()
        except Exception as e:
            # print(e)
            target_date = None
        try:
            completed_at = date_obj.timestamp()
        except Exception as e:
            # print(e)
            completed_at = None
        content = f"This is a task that has name: {response['name']}, assignees: {assignees}, \
            'comments': {comments}, 'start date': {response['start_date']}, 'target date': {response['target_date']}, \
            'description': {response['description']}, \
            'priority': {response['priority']}, 'state': {response['state']}."
        metadata = {"task id": str(response['id']),
                    "priority": str(response['priority']), 
                    "state": str(response['state']), 
                    "start date": start_date, 
                    "target date": target_date, 
                    "completed at": completed_at,
                    "project name": str(response['project_name'])
                    }
        document = Document(page_content=content, metadata=metadata)
        results.append(document)

    # pprint.pprint(results)
    return results