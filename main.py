from components.App import Application

def main():
    Application()
    
if __name__=="__main__":
    main()


## taiga
# projects ['id', 'project_name', 'project_owner', 'is_selected']
# members ['id', 'username']
# sprints ['id', 'sprint_name', 'sprint_start', 'sprint_end']
# us ['id', 'us_num', 'is_complete', 'sprint_id', 'points']
# task ['id', 'task_num', 'is_complete', 'us_id', 'assignee_id', 'task_subject']
