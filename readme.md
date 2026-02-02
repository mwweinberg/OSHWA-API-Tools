# script info

* `all_data_to_dict_and_csv.py` grabs all of the data to a dictionary and outputs as a csv
* `documentation_platform_counter.py` is for generating stats on which platforms people use to host their OSHWA documentation
* `how_many_stars.py` counts the number of stars and watchers for each entry that is hosted on github, outputs .csv and .md files

# troubleshooting info 

source oshwa_api_tools/bin/activate


if you get a error: 'total_number_of_certified_hardware = json_data['total']', that just  means your API token has expired

documentation_platform_counter.py has a block of text that will put all of the data from the API into a list called "all_data".  It ends at `######END GETTING DATA SECTION#####`



# how_many_stars TODO:



o analysis and visualization (https://pypi.org/project/py-markdown-table/ as a start?)

X make API call with user and project (https://api.github.com/repos/getpelican/pelican)
X count stars and watchers and add it to the project list item 
X do some sort of output
X parse out the user and project from the github url
X access github api via authentication so you can hit the endpoint enough to pull the data (https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api?apiVersion=2022-11-28)
X remove the limitation on 'for i in all_data[:20]:' so that it will pull all of the data
X rename github_stars.csv to github_stars_all_data.csv
X create a new list that just has relevant columns (github_projects_list_simplified)
X save it as github_stars_simplified.csv 
X add "directoryUrl" field in github_projects_list_simplified