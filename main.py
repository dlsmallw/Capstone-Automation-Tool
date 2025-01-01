from backend import TaigaCSVParser, GitHubCommitParser
import pandas as pd

# from components import dialog

# from nicegui import ui

# ui.button('Test General Dialog', on_click=dialog.gen_dialog('TEST DIALOG').open)
# ui.button('Test Error Dialog', on_click=dialog.err_dialog('TEST ERR', 'TEST ERROR MSG').open)

# ui.run(native=True)

task_report_url = 'https://api.taiga.io/api/v1/tasks/csv?uuid=a368e32c271a4e0b94918762640de1a1'
us_report_url = 'https://api.taiga.io/api/v1/userstories/csv?uuid=3182e43aa3b045f484d842d74cff2d86'

# tpc = TaigaCSVParser.TaigaParsingController()

# tpc.set_task_report_url(task_report_url)
# tpc.set_us_report_url(us_report_url)

# tpc.retrieve_data_by_api()
# df = tpc.get_master_df()

# print(df)

ghp = GitHubCommitParser.GitHubParsingController()

ghp.retrieve_and_parse_commit_data()

# contributors = ghp.get_contributors()
# all_commits = ghp.get_all_commit_data()
# commits_by_member = ghp.get_commits_by_committer_data()

# print('Contributors:')
# print(contributors)

# print('All Commit Data:')
# print(all_commits)

# print('Commits by Committer:')
# print(commits_by_member)

ghp.write_to_excel()
